#!/bin/bash
# Submit transaction to QR Coin auction
# Usage: submit-tx.sh <action> [args...]
#
# Actions:
#   approve <amount_usdc>
#   createBid <url> [name]
#   contributeToBid <url> [name]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$HOME/.clawdbot/skills/qrcoin/config.json"

# Contract addresses
AUCTION="0x7309779122069EFa06ef71a45AE0DB55A259A176"
USDC="0x833589fCD6eDb6E08f4c7c32D4f71b54bdA02913"

# Load config
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: No config found. Run setup.sh first."
    exit 1
fi

X_HANDLE=$(jq -r '.xHandle // "Anonymous"' "$CONFIG_FILE")

# Check if using shared wallet
WALLET_SOURCE=$(jq -r '.walletSource // "local"' "$CONFIG_FILE")
if [ "$WALLET_SOURCE" = "shared" ]; then
    WALLET_CONFIG=$(jq -r '.walletConfig' "$CONFIG_FILE")
    if [ ! -f "$WALLET_CONFIG" ]; then
        echo "Error: Shared wallet config not found: $WALLET_CONFIG"
        exit 1
    fi
    ADDRESS=$(jq -r '.address' "$WALLET_CONFIG")
    RPC_URL=$(jq -r '.rpcUrls.base // "https://mainnet.base.org"' "$WALLET_CONFIG")
else
    ADDRESS=$(jq -r '.address' "$CONFIG_FILE")
    RPC_URL=$(jq -r '.rpcUrl // "https://mainnet.base.org"' "$CONFIG_FILE")
fi

# Get private key from keychain (with --internal flag for tx signing)
PRIVATE_KEY=$(python3 "$SCRIPT_DIR/keychain.py" retrieve --internal 2>/dev/null)

if [ -z "$PRIVATE_KEY" ]; then
    echo "Error: Could not retrieve private key. Run setup.sh first."
    exit 1
fi

# Get current token ID via RPC
get_token_id() {
    local result=$(curl -s -X POST "$RPC_URL" \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"eth_call","params":[{"to":"'"$AUCTION"'","data":"0x7d9f6db5"},"latest"],"id":1}' \
        | jq -r '.result')
    echo $((16#${result:2:64}))
}

# Convert USDC to wei
usdc_to_wei() {
    python3 -c "print(int($1 * 1000000))"
}

# Send transaction using Python/web3
send_tx() {
    local to="$1"
    local data="$2"
    local desc="$3"
    
    python3 << PYEOF
from web3 import Web3
from eth_account import Account

w3 = Web3(Web3.HTTPProvider("$RPC_URL"))
acct = Account.from_key("$PRIVATE_KEY")

# Build transaction
nonce = w3.eth.get_transaction_count(acct.address)
gas_price = w3.eth.gas_price
to_addr = Web3.to_checksum_address("$to")

# Estimate gas with 30% buffer to avoid out-of-gas
try:
    estimated = w3.eth.estimate_gas({
        'from': acct.address,
        'to': to_addr,
        'data': "$data",
    })
    gas_limit = int(estimated * 1.3)  # 30% buffer
    print(f"Estimated gas: {estimated}, using: {gas_limit}")
except Exception as e:
    gas_limit = 500000  # Fallback to safe default
    print(f"Gas estimation failed ({e}), using default: {gas_limit}")

tx = {
    'to': to_addr,
    'data': "$data",
    'gas': gas_limit,
    'gasPrice': gas_price,
    'nonce': nonce,
    'chainId': 8453  # Base
}

# Sign and send
signed = acct.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

print(f"Transaction sent!")
print(f"Hash: 0x{tx_hash.hex()}")
print(f"View: https://basescan.org/tx/0x{tx_hash.hex()}")
PYEOF
}

# Check for --yes flag and filter args
YES_FLAG=false
ARGS=()
for arg in "$@"; do
    if [ "$arg" = "--yes" ] || [ "$arg" = "-y" ]; then
        YES_FLAG=true
    else
        ARGS+=("$arg")
    fi
done

ACTION="${ARGS[0]:-help}"

case "$ACTION" in
    approve)
        AMOUNT_USDC="${ARGS[1]:-30}"
        AMOUNT_WEI=$(usdc_to_wei "$AMOUNT_USDC")
        
        echo "═══════════════════════════════════════════════════════"
        echo "  APPROVE USDC"
        echo "═══════════════════════════════════════════════════════"
        echo ""
        echo "Amount: $AMOUNT_USDC USDC"
        echo "From:   $ADDRESS"
        echo ""
        
        # Encode approve(address,uint256)
        CALLDATA=$(python3 "$SCRIPT_DIR/encode.py" approve "$AUCTION" "$AMOUNT_WEI")
        
        if [ "$YES_FLAG" = true ]; then
            send_tx "$USDC" "$CALLDATA" "Approve USDC"
        else
            read -p "Submit transaction? (y/N): " CONFIRM
            if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
                send_tx "$USDC" "$CALLDATA" "Approve USDC"
            else
                echo "Cancelled."
            fi
        fi
        ;;
        
    createBid)
        URL="${ARGS[1]:-}"
        NAME="${ARGS[2]:-$X_HANDLE}"
        
        if [ -z "$URL" ]; then
            echo "Usage: submit-tx.sh createBid <url> [name]"
            exit 1
        fi
        
        TOKEN_ID=$(get_token_id)
        
        echo "═══════════════════════════════════════════════════════"
        echo "  CREATE BID"
        echo "═══════════════════════════════════════════════════════"
        echo ""
        echo "Token ID: $TOKEN_ID"
        echo "URL:      $URL"
        echo "Name:     $NAME"
        echo "From:     $ADDRESS"
        echo ""
        
        # Encode createBid(uint256,string,string)
        CALLDATA=$(python3 "$SCRIPT_DIR/encode.py" createBid "$TOKEN_ID" "$URL" "$NAME")
        
        if [ "$YES_FLAG" = true ]; then
            send_tx "$AUCTION" "$CALLDATA" "Create bid"
        else
            read -p "Submit transaction? (y/N): " CONFIRM
            if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
                send_tx "$AUCTION" "$CALLDATA" "Create bid"
            else
                echo "Cancelled."
            fi
        fi
        ;;
        
    contributeToBid|contribute)
        URL="${ARGS[1]:-}"
        NAME="${ARGS[2]:-$X_HANDLE}"
        
        if [ -z "$URL" ]; then
            echo "Usage: submit-tx.sh contributeToBid <url> [name]"
            exit 1
        fi
        
        TOKEN_ID=$(get_token_id)
        
        echo "═══════════════════════════════════════════════════════"
        echo "  CONTRIBUTE TO BID"
        echo "═══════════════════════════════════════════════════════"
        echo ""
        echo "Token ID: $TOKEN_ID"
        echo "URL:      $URL"
        echo "Name:     $NAME"
        echo "From:     $ADDRESS"
        echo ""
        
        # Encode contributeToBid(uint256,string,string)
        CALLDATA=$(python3 "$SCRIPT_DIR/encode.py" contributeToBid "$TOKEN_ID" "$URL" "$NAME")
        
        if [ "$YES_FLAG" = true ]; then
            send_tx "$AUCTION" "$CALLDATA" "Contribute to bid"
        else
            read -p "Submit transaction? (y/N): " CONFIRM
            if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
                send_tx "$AUCTION" "$CALLDATA" "Contribute to bid"
            else
                echo "Cancelled."
            fi
        fi
        ;;
        
    help|*)
        echo "QR Coin Transaction Submitter"
        echo ""
        echo "Usage: submit-tx.sh <action> [args...]"
        echo ""
        echo "Actions:"
        echo "  approve <amount_usdc>           Approve USDC spending"
        echo "  createBid <url> [name]          Create new bid"
        echo "  contributeToBid <url> [name]    Contribute to existing bid"
        echo ""
        echo "Options:"
        echo "  --yes, -y                       Skip confirmation prompt"
        echo ""
        echo "Examples:"
        echo "  submit-tx.sh approve 50"
        echo "  submit-tx.sh createBid https://example.com"
        echo "  submit-tx.sh contribute https://grokipedia.com/page/debtreliefbot --yes"
        ;;
esac
