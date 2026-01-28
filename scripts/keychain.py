#!/usr/bin/env python3
"""
Secure keychain storage for QR Coin wallet.

Supports:
- macOS Keychain (via security CLI)
- Linux libsecret (via secret-tool CLI)
- Fallback: encrypted file with password

Usage:
  keychain.py store <private_key>   Store key in keychain
  keychain.py retrieve              Retrieve key from keychain
  keychain.py delete                Remove key from keychain
  keychain.py status                Check if key is stored
"""

import sys
import os
import subprocess
import platform
import json
import hashlib
from pathlib import Path
from getpass import getpass

SERVICE_NAME = "qrcoin-wallet"
ACCOUNT_NAME = "agent-wallet"
CONFIG_DIR = Path.home() / ".clawdbot" / "skills" / "qrcoin"
ENCRYPTED_FILE = CONFIG_DIR / ".wallet.enc"

def get_platform():
    """Detect platform and available keychain."""
    system = platform.system()
    
    if system == "Darwin":
        # macOS - use security CLI
        if subprocess.run(["which", "security"], capture_output=True).returncode == 0:
            return "macos"
    
    elif system == "Linux":
        # Linux - check for secret-tool
        if subprocess.run(["which", "secret-tool"], capture_output=True).returncode == 0:
            return "linux"
    
    # Fallback to encrypted file
    return "file"

def macos_store(private_key: str) -> bool:
    """Store in macOS Keychain."""
    try:
        # Delete existing entry first (ignore errors)
        subprocess.run([
            "security", "delete-generic-password",
            "-s", SERVICE_NAME,
            "-a", ACCOUNT_NAME
        ], capture_output=True)
        
        # Add new entry
        result = subprocess.run([
            "security", "add-generic-password",
            "-s", SERVICE_NAME,
            "-a", ACCOUNT_NAME,
            "-w", private_key,
            "-U"  # Update if exists
        ], capture_output=True, text=True)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Keychain error: {e}")
        return False

def macos_retrieve() -> str:
    """Retrieve from macOS Keychain."""
    try:
        result = subprocess.run([
            "security", "find-generic-password",
            "-s", SERVICE_NAME,
            "-a", ACCOUNT_NAME,
            "-w"  # Output password only
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception:
        return None

def macos_delete() -> bool:
    """Delete from macOS Keychain."""
    try:
        result = subprocess.run([
            "security", "delete-generic-password",
            "-s", SERVICE_NAME,
            "-a", ACCOUNT_NAME
        ], capture_output=True)
        return result.returncode == 0
    except Exception:
        return False

def linux_store(private_key: str) -> bool:
    """Store in Linux secret-service (GNOME Keyring, KWallet, etc.)."""
    try:
        result = subprocess.run([
            "secret-tool", "store",
            "--label", "QR Coin Agent Wallet",
            "service", SERVICE_NAME,
            "account", ACCOUNT_NAME
        ], input=private_key.encode(), capture_output=True)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Secret service error: {e}")
        return False

def linux_retrieve() -> str:
    """Retrieve from Linux secret-service."""
    try:
        result = subprocess.run([
            "secret-tool", "lookup",
            "service", SERVICE_NAME,
            "account", ACCOUNT_NAME
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception:
        return None

def linux_delete() -> bool:
    """Delete from Linux secret-service."""
    try:
        result = subprocess.run([
            "secret-tool", "clear",
            "service", SERVICE_NAME,
            "account", ACCOUNT_NAME
        ], capture_output=True)
        return result.returncode == 0
    except Exception:
        return False

def encrypt_key(private_key: str, password: str) -> bytes:
    """Encrypt private key with password using Fernet."""
    try:
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        import base64
        
        # Derive key from password
        salt = b'qrcoin_wallet_salt_v1'  # Fixed salt (key is already random)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        f = Fernet(key)
        return f.encrypt(private_key.encode())
    except ImportError:
        # Fallback: simple XOR (not recommended but works without dependencies)
        key_hash = hashlib.sha256(password.encode()).digest()
        encrypted = bytes(a ^ b for a, b in zip(private_key.encode(), key_hash * 3))
        return b"SIMPLE:" + encrypted

def decrypt_key(encrypted: bytes, password: str) -> str:
    """Decrypt private key with password."""
    try:
        if encrypted.startswith(b"SIMPLE:"):
            # Simple XOR fallback
            encrypted = encrypted[7:]
            key_hash = hashlib.sha256(password.encode()).digest()
            decrypted = bytes(a ^ b for a, b in zip(encrypted, key_hash * 3))
            return decrypted.decode()
        
        from cryptography.fernet import Fernet, InvalidToken
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        import base64
        
        salt = b'qrcoin_wallet_salt_v1'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        f = Fernet(key)
        return f.decrypt(encrypted).decode()
    except Exception as e:
        return None

def file_store(private_key: str) -> bool:
    """Store encrypted in file (fallback)."""
    password = getpass("Enter encryption password: ")
    password2 = getpass("Confirm password: ")
    
    if password != password2:
        print("Passwords don't match!")
        return False
    
    encrypted = encrypt_key(private_key, password)
    
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(ENCRYPTED_FILE, 'wb') as f:
        f.write(encrypted)
    os.chmod(ENCRYPTED_FILE, 0o600)
    
    return True

def file_retrieve() -> str:
    """Retrieve from encrypted file."""
    if not ENCRYPTED_FILE.exists():
        return None
    
    password = getpass("Enter wallet password: ")
    
    with open(ENCRYPTED_FILE, 'rb') as f:
        encrypted = f.read()
    
    return decrypt_key(encrypted, password)

def file_delete() -> bool:
    """Delete encrypted file."""
    if ENCRYPTED_FILE.exists():
        ENCRYPTED_FILE.unlink()
        return True
    return False

# Platform-specific function mapping
BACKENDS = {
    "macos": (macos_store, macos_retrieve, macos_delete),
    "linux": (linux_store, linux_retrieve, linux_delete),
    "file": (file_store, file_retrieve, file_delete),
}

def store_key(private_key: str) -> bool:
    """Store private key in most secure available backend."""
    backend = get_platform()
    store_fn, _, _ = BACKENDS[backend]
    
    print(f"Using {backend} keychain...")
    success = store_fn(private_key)
    
    if success:
        print(f"✓ Private key stored securely ({backend})")
        
        # Update config to indicate keychain storage
        config_file = CONFIG_DIR / "config.json"
        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)
            config['keyStorage'] = backend
            config.pop('privateKey', None)  # Remove plain key from config
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
    
    return success

def retrieve_key() -> str:
    """Retrieve private key from keychain."""
    # Check config for storage method
    config_file = CONFIG_DIR / "config.json"
    backend = get_platform()
    
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
        
        # If plain key still in config, return it (legacy)
        if 'privateKey' in config:
            return config['privateKey']
        
        # Use stored backend preference
        backend = config.get('keyStorage', backend)
    
    _, retrieve_fn, _ = BACKENDS.get(backend, BACKENDS['file'])
    return retrieve_fn()

def delete_key() -> bool:
    """Delete private key from keychain."""
    backend = get_platform()
    
    config_file = CONFIG_DIR / "config.json"
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
        backend = config.get('keyStorage', backend)
    
    _, _, delete_fn = BACKENDS.get(backend, BACKENDS['file'])
    success = delete_fn()
    
    if success:
        print(f"✓ Private key removed from {backend}")
    
    return success

def check_status():
    """Check keychain status."""
    backend = get_platform()
    
    config_file = CONFIG_DIR / "config.json"
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
        
        stored_backend = config.get('keyStorage')
        has_plain_key = 'privateKey' in config
        
        print(f"Platform: {platform.system()}")
        print(f"Available backend: {backend}")
        print(f"Config storage: {stored_backend or 'none'}")
        print(f"Plain key in config: {'YES ⚠️' if has_plain_key else 'No ✓'}")
        
        if stored_backend:
            # Try to retrieve
            _, retrieve_fn, _ = BACKENDS.get(stored_backend, BACKENDS['file'])
            key = retrieve_fn() if stored_backend != 'file' else None
            print(f"Key accessible: {'Yes ✓' if key else 'Unknown'}")
    else:
        print("No config found. Run setup.sh first.")

def load_policy():
    """Load wallet security policy."""
    policy_file = Path.home() / ".clawdbot" / "config" / "wallet-policy.json"
    if policy_file.exists():
        with open(policy_file) as f:
            return json.load(f)
    return {"policies": {}}

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'store':
        if len(sys.argv) < 3:
            print("Usage: keychain.py store <private_key>")
            sys.exit(1)
        success = store_key(sys.argv[2])
        sys.exit(0 if success else 1)
    
    elif cmd == 'retrieve':
        # Check for --internal flag (used by scripts for signing)
        internal = '--internal' in sys.argv
        
        if not internal:
            # Check policy for direct retrieval
            policy = load_policy()
            if not policy.get("policies", {}).get("allowKeyExport", True):
                print("🔒 Key retrieval disabled by policy", file=sys.stderr)
                print("", file=sys.stderr)
                print("For manual access on macOS:", file=sys.stderr)
                print("  security find-generic-password -s qrcoin-wallet -a agent-wallet -w", file=sys.stderr)
                sys.exit(1)
        
        key = retrieve_key()
        if key:
            print(key)
        else:
            print("No key found", file=sys.stderr)
            sys.exit(1)
    
    elif cmd == 'delete':
        success = delete_key()
        sys.exit(0 if success else 1)
    
    elif cmd == 'status':
        check_status()
    
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)

if __name__ == '__main__':
    main()
