#!/usr/bin/env python3
"""
Check for wallet skill availability.
Returns wallet info if configured, or instructions to set up.
"""

import json
import sys
from pathlib import Path

# Possible wallet skill locations
WALLET_LOCATIONS = [
    Path.home() / "clawd" / "skills" / "wallet",
    Path.home() / ".clawdbot" / "skills" / "wallet",
]

# Possible wallet config locations
CONFIG_LOCATIONS = [
    Path.home() / ".clawdbot" / "skills" / "wallet" / "config.json",
    Path.home() / ".clawdbot" / "skills" / "qrcoin" / "config.json",  # Legacy
]

def find_wallet_skill():
    """Find installed wallet skill."""
    for loc in WALLET_LOCATIONS:
        if (loc / "SKILL.md").exists():
            return loc
    return None

def find_wallet_config():
    """Find wallet configuration."""
    for loc in CONFIG_LOCATIONS:
        if loc.exists():
            return loc
    return None

def get_wallet_info():
    """Get wallet information if available."""
    config_path = find_wallet_config()
    if not config_path:
        return None
    
    with open(config_path) as f:
        config = json.load(f)
    
    return {
        "address": config.get("address"),
        "chain": config.get("defaultChain", "base"),
        "storage": config.get("keyStorage", "unknown"),
        "config_path": str(config_path)
    }

def main():
    wallet_skill = find_wallet_skill()
    wallet_config = find_wallet_config()
    wallet_info = get_wallet_info()
    
    print("═" * 50)
    print("  WALLET STATUS")
    print("═" * 50)
    print()
    
    if wallet_skill:
        print(f"✓ Wallet skill found: {wallet_skill}")
    else:
        print("✗ Wallet skill not found")
        print("  Install from: ~/clawd/skills/wallet")
    
    if wallet_config:
        print(f"✓ Wallet configured: {wallet_config}")
    else:
        print("✗ Wallet not configured")
    
    if wallet_info:
        print()
        print(f"  Address: {wallet_info['address']}")
        print(f"  Chain:   {wallet_info['chain']}")
        print(f"  Storage: {wallet_info['storage']}")
    
    print()
    
    # Return status for scripts
    if wallet_info and wallet_info.get('address'):
        sys.exit(0)  # Wallet ready
    else:
        sys.exit(1)  # Wallet not configured

if __name__ == "__main__":
    main()
