#!/bin/bash
# QR Coin Skill Setup
# Uses shared wallet skill if available, otherwise creates one

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$HOME/.clawdbot/skills/qrcoin"
CONFIG_FILE="$CONFIG_DIR/config.json"

# Shared wallet locations
WALLET_SKILL="$HOME/clawd/skills/wallet"
WALLET_CONFIG="$HOME/.clawdbot/skills/wallet/config.json"

echo "═══════════════════════════════════════════════════════"
echo "  QR Coin Auction Skill - Setup"
echo "═══════════════════════════════════════════════════════"
echo ""

# Check for existing shared wallet
if [ -f "$WALLET_CONFIG" ]; then
    WALLET_ADDR=$(jq -r '.address // empty' "$WALLET_CONFIG" 2>/dev/null || echo "")
    if [ -n "$WALLET_ADDR" ]; then
        echo "✓ Found existing wallet: $WALLET_ADDR"
        echo ""
        echo "Options:"
        echo "  1. Use existing wallet (recommended)"
        echo "  2. Create new wallet for QR Coin only"
        echo ""
        read -p "Choose (1 or 2): " USE_EXISTING
        
        if [ "${USE_EXISTING:-1}" = "1" ]; then
            echo ""
            echo "Using shared wallet..."
            
            # Get X handle
            read -p "Your X/Twitter handle (without @): " X_HANDLE
            
            # Create QR Coin config pointing to shared wallet
            mkdir -p "$CONFIG_DIR"
            cat > "$CONFIG_FILE" << EOF
{
  "walletSource": "shared",
  "walletConfig": "$WALLET_CONFIG",
  "xHandle": "$X_HANDLE",
  "auctionContract": "0x7309779122069EFa06ef71a45AE0DB55A259A176",
  "usdcContract": "0x833589fCD6eDb6E08f4c7c32D4f71b54bdA02913"
}
EOF
            chmod 600 "$CONFIG_FILE"
            
            echo ""
            echo "═══════════════════════════════════════════════════════"
            echo "  ✓ SETUP COMPLETE (using shared wallet)"
            echo "═══════════════════════════════════════════════════════"
            echo ""
            echo "Wallet:   $WALLET_ADDR"
            echo "X Handle: $X_HANDLE"
            echo ""
            exit 0
        fi
    fi
fi

# Check if QR Coin already has its own wallet
if [ -f "$CONFIG_FILE" ]; then
    EXISTING_ADDR=$(jq -r '.address // empty' "$CONFIG_FILE" 2>/dev/null || echo "")
    if [ -n "$EXISTING_ADDR" ]; then
        echo "⚠️  QR Coin wallet already configured: $EXISTING_ADDR"
        echo ""
        read -p "Create new wallet? (y/N): " OVERWRITE
        if [ "$OVERWRITE" != "y" ] && [ "$OVERWRITE" != "Y" ]; then
            echo "Setup cancelled."
            exit 0
        fi
        python3 "$SCRIPT_DIR/keychain.py" delete 2>/dev/null || true
    fi
fi

echo ""
echo "Creating dedicated wallet for QR Coin..."
echo ""
echo "Options:"
echo "  1. Create NEW wallet"
echo "  2. Import EXISTING wallet (private key)"
echo ""
read -p "Choose (1 or 2): " WALLET_CHOICE

# Get X handle
echo ""
read -p "Your X/Twitter handle (without @): " X_HANDLE

# Get RPC URL
echo ""
read -p "RPC URL (Enter for default https://mainnet.base.org): " RPC_URL
RPC_URL="${RPC_URL:-https://mainnet.base.org}"

mkdir -p "$CONFIG_DIR"

if [ "$WALLET_CHOICE" = "1" ]; then
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  CREATING NEW WALLET"
    echo "═══════════════════════════════════════════════════════"
    
    WALLET_OUTPUT=$(python3 << 'PYEOF'
from eth_account import Account
Account.enable_unaudited_hdwallet_features()
acct, mnemonic = Account.create_with_mnemonic()
print(f"MNEMONIC:{mnemonic}")
print(f"ADDRESS:{acct.address}")
print(f"PRIVKEY:{acct.key.hex()}")
PYEOF
)
    
    MNEMONIC=$(echo "$WALLET_OUTPUT" | grep "^MNEMONIC:" | cut -d: -f2-)
    ADDRESS=$(echo "$WALLET_OUTPUT" | grep "^ADDRESS:" | cut -d: -f2)
    PRIVKEY=$(echo "$WALLET_OUTPUT" | grep "^PRIVKEY:" | cut -d: -f2)
    
    echo ""
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║  ⚠️  BACKUP THIS SEED PHRASE NOW!                    ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo ""
    echo "SEED PHRASE: $MNEMONIC"
    echo ""
    echo "ADDRESS: $ADDRESS"
    echo ""
    
    read -p "Backed up? (y/N): " BACKED_UP
    if [ "$BACKED_UP" != "y" ] && [ "$BACKED_UP" != "Y" ]; then
        echo "Please backup first!"
        exit 1
    fi
    
elif [ "$WALLET_CHOICE" = "2" ]; then
    echo ""
    read -sp "Enter private key (0x...): " PRIVKEY
    echo ""
    
    ADDRESS=$(python3 -c "
from eth_account import Account
try:
    print(Account.from_key('$PRIVKEY').address)
except: print('ERROR')
")
    
    if [ "$ADDRESS" = "ERROR" ]; then
        echo "Invalid private key"
        exit 1
    fi
    echo "Address: $ADDRESS"
else
    echo "Invalid choice"
    exit 1
fi

# Store in keychain
echo ""
python3 "$SCRIPT_DIR/keychain.py" store "$PRIVKEY"

# Save config
cat > "$CONFIG_FILE" << EOF
{
  "walletSource": "local",
  "address": "$ADDRESS",
  "rpcUrl": "$RPC_URL",
  "xHandle": "$X_HANDLE",
  "keyStorage": "keychain",
  "auctionContract": "0x7309779122069EFa06ef71a45AE0DB55A259A176",
  "usdcContract": "0x833589fCD6eDb6E08f4c7c32D4f71b54bdA02913"
}
EOF
chmod 600 "$CONFIG_FILE"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ✓ SETUP COMPLETE"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Wallet:   $ADDRESS"
echo "X Handle: $X_HANDLE"
echo "Storage:  🔐 System Keychain"
echo ""
echo "Next: Fund with ETH + USDC on Base"
echo ""
