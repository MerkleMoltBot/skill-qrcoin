#!/bin/bash
# Build transaction calldata for QR Coin auction
# Usage: build-tx.sh <action> [args...]
#
# Actions:
#   approve <amount_usdc>
#   createBid <url> [name]
#   contributeToBid <url> [name]
#   status

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$HOME/.clawdbot/skills/qrcoin/config.json"

# Contract addresses
AUCTION="0x7309779122069EFa06ef71a45AE0DB55A259A176"
USDC="0x833589fCD6eDb6E08f4c7c32D4f71b54bdA02913"
CHAIN_ID="8453"  # Base

# Load config
if [ -f "$CONFIG_FILE" ]; then
    RPC_URL=$(jq -r '.rpcUrl // "https://mainnet.base.org"' "$CONFIG_FILE")
    X_HANDLE=$(jq -r '.xHandle // "Anonymous"' "$CONFIG_FILE")
else
    RPC_URL="https://mainnet.base.org"
    X_HANDLE="Anonymous"
fi

# Encoding function - uses cast if available, falls back to Python
encode_calldata() {
    local func="$1"
    shift
    
    if command -v cast &> /dev/null; then
        case "$func" in
            approve)
                cast calldata "approve(address,uint256)" "$@"
                ;;
            createBid)
                cast calldata "createBid(uint256,string,string)" "$@"
                ;;
            contributeToBid)
                cast calldata "contributeToBid(uint256,string,string)" "$@"
                ;;
        esac
    else
        # Fall back to Python encoder
        python3 "$SCRIPT_DIR/encode.py" "$func" "$@"
    fi
}

# RPC call function
rpc_call() {
    local to="$1"
    local data="$2"
    
    curl -s -X POST "$RPC_URL" \
        -H "Content-Type: application/json" \
        -d "{\"jsonrpc\":\"2.0\",\"method\":\"eth_call\",\"params\":[{\"to\":\"$to\",\"data\":\"$data\"},\"latest\"],\"id\":1}" \
        | jq -r '.result // .error.message'
}

# Get current token ID
get_token_id() {
    local result=$(rpc_call "$AUCTION" "0x7d9f6db5")
    if [ -n "$result" ] && [ "$result" != "null" ]; then
        # Token ID is first 32 bytes
        echo $((16#${result:2:64}))
    else
        echo "0"
    fi
}

# Convert USDC to wei (6 decimals)
usdc_to_wei() {
    python3 -c "print(int($1 * 1000000))"
}

ACTION="${1:-help}"
shift || true

case "$ACTION" in
    approve)
        AMOUNT_USDC="${1:-10}"
        AMOUNT_WEI=$(usdc_to_wei "$AMOUNT_USDC")
        
        echo "═══════════════════════════════════════════════════════"
        echo "  APPROVE USDC"
        echo "═══════════════════════════════════════════════════════"
        echo ""
        echo "Action: Approve $AMOUNT_USDC USDC for QR Coin auction"
        echo ""
        
        # Encode calldata
        CALLDATA=$(encode_calldata approve "$AUCTION" "$AMOUNT_WEI")
        
        echo "To: $USDC"
        echo "Chain: Base ($CHAIN_ID)"
        echo "Calldata: $CALLDATA"
        echo ""
        echo "═══════════════════════════════════════════════════════"
        echo ""
        echo "Copy this JSON to submit.html:"
        echo ""
        cat << EOF
{
  "to": "$USDC",
  "data": "$CALLDATA",
  "chainId": "$CHAIN_ID",
  "description": "Approve $AMOUNT_USDC USDC for QR Coin auction"
}
EOF
        ;;
        
    createBid)
        URL="${1:-}"
        NAME="${2:-$X_HANDLE}"
        
        if [ -z "$URL" ]; then
            echo "Usage: build-tx.sh createBid <url> [name]"
            exit 1
        fi
        
        TOKEN_ID=$(get_token_id)
        
        echo "═══════════════════════════════════════════════════════"
        echo "  CREATE BID"
        echo "═══════════════════════════════════════════════════════"
        echo ""
        echo "Token ID: $TOKEN_ID"
        echo "URL: $URL"
        echo "Name: $NAME"
        echo ""
        
        # Encode calldata
        CALLDATA=$(encode_calldata createBid "$TOKEN_ID" "$URL" "$NAME")
        
        echo "To: $AUCTION"
        echo "Chain: Base ($CHAIN_ID)"
        echo "Calldata: $CALLDATA"
        echo ""
        echo "═══════════════════════════════════════════════════════"
        echo ""
        echo "Copy this JSON to submit.html:"
        echo ""
        cat << EOF
{
  "to": "$AUCTION",
  "data": "$CALLDATA",
  "chainId": "$CHAIN_ID",
  "description": "Create bid for $URL as $NAME"
}
EOF
        ;;
        
    contributeToBid|contribute)
        URL="${1:-}"
        NAME="${2:-$X_HANDLE}"
        
        if [ -z "$URL" ]; then
            echo "Usage: build-tx.sh contributeToBid <url> [name]"
            exit 1
        fi
        
        TOKEN_ID=$(get_token_id)
        
        echo "═══════════════════════════════════════════════════════"
        echo "  CONTRIBUTE TO BID"
        echo "═══════════════════════════════════════════════════════"
        echo ""
        echo "Token ID: $TOKEN_ID"
        echo "URL: $URL"
        echo "Name: $NAME"
        echo ""
        
        # Encode calldata
        CALLDATA=$(encode_calldata contributeToBid "$TOKEN_ID" "$URL" "$NAME")
        
        echo "To: $AUCTION"
        echo "Chain: Base ($CHAIN_ID)"
        echo "Calldata: $CALLDATA"
        echo ""
        echo "═══════════════════════════════════════════════════════"
        echo ""
        echo "Copy this JSON to submit.html:"
        echo ""
        cat << EOF
{
  "to": "$AUCTION",
  "data": "$CALLDATA",
  "chainId": "$CHAIN_ID",
  "description": "Contribute to bid for $URL as $NAME"
}
EOF
        ;;
        
    status)
        echo "═══════════════════════════════════════════════════════"
        echo "  AUCTION STATUS"
        echo "═══════════════════════════════════════════════════════"
        echo ""
        echo "RPC: $RPC_URL"
        echo "X Handle: $X_HANDLE"
        echo ""
        
        TOKEN_ID=$(get_token_id)
        echo "Current Token ID: $TOKEN_ID"
        
        # Get auction data
        AUCTION_DATA=$(rpc_call "$AUCTION" "0x7d9f6db5")
        
        if [ -n "$AUCTION_DATA" ] && [ "$AUCTION_DATA" != "null" ]; then
            # Parse end time (3rd 32-byte value after offset)
            END_HEX=${AUCTION_DATA:130:64}
            END_TIME=$((16#$END_HEX))
            NOW=$(date +%s)
            
            if [ $NOW -lt $END_TIME ]; then
                REMAINING=$(($END_TIME - $NOW))
                HOURS=$(($REMAINING / 3600))
                MINS=$((($REMAINING % 3600) / 60))
                echo "Status: 🟢 ACTIVE ($HOURS h $MINS m remaining)"
                echo "End: $(date -r $END_TIME 2>/dev/null || date -d @$END_TIME)"
            else
                echo "Status: 🔴 ENDED"
            fi
        fi
        
        # Get reserve prices (correct selectors)
        CREATE_RESERVE=$(rpc_call "$AUCTION" "0x85d6cdd2")  # createBidReservePrice()
        CONTRIB_RESERVE=$(rpc_call "$AUCTION" "0xd71c745e")  # contributeBidReservePrice()
        
        if [ -n "$CREATE_RESERVE" ] && [ "$CREATE_RESERVE" != "null" ]; then
            CREATE_USDC=$(python3 -c "print(f'{int(\"$CREATE_RESERVE\", 16) / 1000000:.2f}')")
            echo ""
            echo "Create Bid Reserve: $CREATE_USDC USDC"
        fi
        
        if [ -n "$CONTRIB_RESERVE" ] && [ "$CONTRIB_RESERVE" != "null" ]; then
            CONTRIB_USDC=$(python3 -c "print(f'{int(\"$CONTRIB_RESERVE\", 16) / 1000000:.2f}')")
            echo "Contribute Reserve: $CONTRIB_USDC USDC"
        fi
        ;;
        
    help|*)
        echo "QR Coin Transaction Builder"
        echo ""
        echo "Usage: build-tx.sh <action> [args...]"
        echo ""
        echo "Actions:"
        echo "  approve <amount_usdc>           Approve USDC spending"
        echo "  createBid <url> [name]          Create new bid"
        echo "  contributeToBid <url> [name]    Contribute to existing bid"  
        echo "  status                          Check auction status"
        echo ""
        echo "The output JSON can be pasted into submit.html to send via MetaMask."
        echo ""
        echo "Examples:"
        echo "  build-tx.sh approve 50"
        echo "  build-tx.sh createBid https://example.com MerkleMoltBot"
        echo "  build-tx.sh contribute https://grokipedia.com/page/debtreliefbot"
        echo ""
        echo "Config: $CONFIG_FILE"
        ;;
esac
