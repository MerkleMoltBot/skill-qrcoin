#!/usr/bin/env python3
"""
Wallet management for QR Coin skill.
Generates new wallets, exports keys, checks balances.

Usage:
  wallet.py create                  Create new wallet (shows seed phrase)
  wallet.py export                  Export private key from config
  wallet.py address                 Show wallet address
  wallet.py balance                 Check ETH and USDC balance
"""

import sys
import os
import json
from pathlib import Path

try:
    from eth_account import Account
    from web3 import Web3
except ImportError:
    print("Error: Required packages not installed.")
    print("Run: pip install eth-account web3")
    sys.exit(1)

# Enable mnemonic features
Account.enable_unaudited_hdwallet_features()

CONFIG_DIR = Path.home() / ".clawdbot" / "skills" / "qrcoin"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Contract addresses
USDC = "0x833589fCD6eDb6E08f4c7c32D4f71b54bdA02913"
RPC_DEFAULT = "https://mainnet.base.org"

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}

def get_private_key():
    """Get private key from keychain or config."""
    import subprocess
    script_dir = Path(__file__).parent
    
    # Try keychain first
    try:
        result = subprocess.run(
            ['python3', str(script_dir / 'keychain.py'), 'retrieve'],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except:
        pass
    
    # Fallback to config
    config = load_config()
    return config.get('privateKey')

def save_config(config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    os.chmod(CONFIG_FILE, 0o600)

def create_wallet():
    """Generate a new wallet with mnemonic seed phrase."""
    # Generate mnemonic and derive account
    Account.enable_unaudited_hdwallet_features()
    acct, mnemonic = Account.create_with_mnemonic()
    
    print("═" * 60)
    print("  NEW WALLET CREATED")
    print("═" * 60)
    print()
    print("⚠️  BACKUP THIS INFORMATION NOW!")
    print("   You will NOT see the seed phrase again.")
    print()
    print("─" * 60)
    print("SEED PHRASE (12 words):")
    print()
    print(f"  {mnemonic}")
    print()
    print("─" * 60)
    print(f"ADDRESS:      {acct.address}")
    print(f"PRIVATE KEY:  {acct.key.hex()}")
    print("─" * 60)
    print()
    print("Store the seed phrase in a safe place!")
    print("The private key will be saved to config for transactions.")
    print()
    
    return acct.key.hex(), acct.address, mnemonic

def export_key():
    """Export private key from keychain."""
    pk = get_private_key()
    if not pk:
        print("No wallet configured. Run setup.sh first.")
        return None
    
    acct = Account.from_key(pk)
    
    print("═" * 60)
    print("  WALLET EXPORT")
    print("═" * 60)
    print()
    print(f"ADDRESS:      {acct.address}")
    print(f"PRIVATE KEY:  {pk}")
    print()
    print("⚠️  Keep this private key secure!")
    print()
    
    return pk

def get_address():
    """Get wallet address from config or derive from key."""
    config = load_config()
    
    # Try config first
    if 'address' in config:
        print(config['address'])
        return config['address']
    
    # Derive from key
    pk = get_private_key()
    if not pk:
        print("No wallet configured. Run setup.sh first.")
        return None
    
    acct = Account.from_key(pk)
    print(acct.address)
    return acct.address

def check_balance():
    """Check ETH and USDC balance."""
    config = load_config()
    pk = get_private_key()
    
    if not pk:
        print("No wallet configured. Run setup.sh first.")
        return
    
    rpc_url = config.get('rpcUrl', RPC_DEFAULT)
    acct = Account.from_key(pk)
    
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    # ETH balance
    eth_balance = w3.eth.get_balance(acct.address)
    eth_formatted = w3.from_wei(eth_balance, 'ether')
    
    # USDC balance
    usdc_contract = w3.eth.contract(
        address=Web3.to_checksum_address(USDC),
        abi=[{
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        }]
    )
    usdc_balance = usdc_contract.functions.balanceOf(acct.address).call()
    usdc_formatted = usdc_balance / 1_000_000
    
    print("═" * 60)
    print("  WALLET BALANCE")
    print("═" * 60)
    print()
    print(f"Address: {acct.address}")
    print(f"Chain:   Base")
    print()
    print(f"ETH:     {eth_formatted:.6f} ETH")
    print(f"USDC:    ${usdc_formatted:.2f}")
    print()
    
    if eth_balance == 0:
        print("⚠️  No ETH for gas! Send some ETH to this address.")
    if usdc_balance == 0:
        print("⚠️  No USDC for bidding! Send USDC to this address.")

def import_key(private_key):
    """Import an existing private key."""
    try:
        acct = Account.from_key(private_key)
        print(f"Imported wallet: {acct.address}")
        return private_key, acct.address
    except Exception as e:
        print(f"Invalid private key: {e}")
        return None, None

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'create':
        pk, addr, mnemonic = create_wallet()
        
        # Ask to save
        print("Save this wallet to config? (y/n): ", end='')
        response = input().strip().lower()
        if response == 'y':
            config = load_config()
            config['privateKey'] = pk
            config['address'] = addr
            config['mode'] = 'privateKey'
            save_config(config)
            print(f"✓ Saved to {CONFIG_FILE}")
        else:
            print("Wallet not saved. You can import it later with the private key.")
    
    elif cmd == 'export':
        export_key()
    
    elif cmd == 'address':
        get_address()
    
    elif cmd == 'balance':
        check_balance()
    
    elif cmd == 'import':
        if len(sys.argv) < 3:
            print("Usage: wallet.py import <private_key>")
            sys.exit(1)
        pk, addr = import_key(sys.argv[2])
        if pk:
            config = load_config()
            config['privateKey'] = pk
            config['address'] = addr
            config['mode'] = 'privateKey'
            save_config(config)
            print(f"✓ Saved to {CONFIG_FILE}")
    
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)

if __name__ == '__main__':
    main()
