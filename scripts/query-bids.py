#!/usr/bin/env python3
"""
Query QR Coin auction bids directly from the contract.
Usage:
    ./query-bids.py              # Full output with all bids
    ./query-bids.py --summary    # Just auction info and top 10
    ./query-bids.py --json       # JSON output for programmatic use
    ./query-bids.py --url URL    # Get specific bid by URL
"""

import argparse
import json
import sys
from datetime import datetime, timezone

try:
    from web3 import Web3
except ImportError:
    print("Error: web3 not installed. Run: pip install web3", file=sys.stderr)
    sys.exit(1)

# Contract addresses (Base Mainnet)
CONTRACT_ADDR = "0x7309779122069EFa06ef71a45AE0DB55A259A176"
RPC_URL = "https://mainnet.base.org"

# Minimal ABI for read operations
ABI = [
    {
        "inputs": [],
        "name": "auction",
        "outputs": [
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"},
            {
                "components": [
                    {"internalType": "uint256", "name": "totalAmount", "type": "uint256"},
                    {"internalType": "string", "name": "urlString", "type": "string"},
                    {
                        "components": [
                            {"internalType": "address", "name": "contributor", "type": "address"},
                            {"internalType": "uint256", "name": "amount", "type": "uint256"},
                            {"internalType": "uint256", "name": "timestamp", "type": "uint256"}
                        ],
                        "internalType": "struct AuctionTypesV5.BidContribution[]",
                        "name": "contributions",
                        "type": "tuple[]"
                    }
                ],
                "internalType": "struct AuctionTypesV5.Bid",
                "name": "highestBid",
                "type": "tuple"
            },
            {"internalType": "uint256", "name": "startTime", "type": "uint256"},
            {"internalType": "uint256", "name": "endTime", "type": "uint256"},
            {"internalType": "bool", "name": "settled", "type": "bool"},
            {
                "components": [
                    {"internalType": "uint256", "name": "validUntil", "type": "uint256"},
                    {"internalType": "string", "name": "urlString", "type": "string"}
                ],
                "internalType": "struct AuctionTypesV5.QRData",
                "name": "qrMetadata",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getAllBids",
        "outputs": [
            {
                "components": [
                    {"internalType": "uint256", "name": "totalAmount", "type": "uint256"},
                    {"internalType": "string", "name": "urlString", "type": "string"},
                    {
                        "components": [
                            {"internalType": "address", "name": "contributor", "type": "address"},
                            {"internalType": "uint256", "name": "amount", "type": "uint256"},
                            {"internalType": "uint256", "name": "timestamp", "type": "uint256"}
                        ],
                        "internalType": "struct AuctionTypesV5.BidContribution[]",
                        "name": "contributions",
                        "type": "tuple[]"
                    }
                ],
                "internalType": "struct AuctionTypesV5.Bid[]",
                "name": "",
                "type": "tuple[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "string", "name": "_urlString", "type": "string"}],
        "name": "getBid",
        "outputs": [
            {
                "components": [
                    {"internalType": "uint256", "name": "totalAmount", "type": "uint256"},
                    {"internalType": "string", "name": "urlString", "type": "string"},
                    {
                        "components": [
                            {"internalType": "address", "name": "contributor", "type": "address"},
                            {"internalType": "uint256", "name": "amount", "type": "uint256"},
                            {"internalType": "uint256", "name": "timestamp", "type": "uint256"}
                        ],
                        "internalType": "struct AuctionTypesV5.BidContribution[]",
                        "name": "contributions",
                        "type": "tuple[]"
                    }
                ],
                "internalType": "struct AuctionTypesV5.Bid",
                "name": "",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getBidCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "createBidReservePrice",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "contributeBidReservePrice",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]


def get_contract():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print("Error: Cannot connect to Base RPC", file=sys.stderr)
        sys.exit(1)
    return w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDR), abi=ABI)


def format_time_remaining(end_time):
    """Format time remaining until auction end."""
    now = datetime.now(timezone.utc).timestamp()
    remaining = end_time - now
    
    if remaining <= 0:
        return "ENDED"
    
    hours = int(remaining // 3600)
    minutes = int((remaining % 3600) // 60)
    
    if hours > 24:
        days = hours // 24
        hours = hours % 24
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def get_auction_info(contract):
    """Get current auction state."""
    auction = contract.functions.auction().call()
    create_reserve = contract.functions.createBidReservePrice().call()
    contribute_reserve = contract.functions.contributeBidReservePrice().call()
    
    return {
        "tokenId": auction[0],
        "highestBid": {
            "totalAmount": auction[1][0],
            "urlString": auction[1][1],
            "contributions": [
                {"contributor": c[0], "amount": c[1], "timestamp": c[2]}
                for c in auction[1][2]
            ]
        },
        "startTime": auction[2],
        "endTime": auction[3],
        "settled": auction[4],
        "qrMetadata": {
            "validUntil": auction[5][0],
            "urlString": auction[5][1]
        },
        "createReserve": create_reserve,
        "contributeReserve": contribute_reserve
    }


def get_all_bids(contract):
    """Get all current bids."""
    bids = contract.functions.getAllBids().call()
    return [
        {
            "totalAmount": bid[0],
            "urlString": bid[1],
            "contributions": [
                {"contributor": c[0], "amount": c[1], "timestamp": c[2]}
                for c in bid[2]
            ]
        }
        for bid in bids
    ]


def get_bid_by_url(contract, url):
    """Get a specific bid by URL."""
    try:
        bid = contract.functions.getBid(url).call()
        if bid[0] == 0:  # No bid found
            return None
        return {
            "totalAmount": bid[0],
            "urlString": bid[1],
            "contributions": [
                {"contributor": c[0], "amount": c[1], "timestamp": c[2]}
                for c in bid[2]
            ]
        }
    except Exception:
        return None


def print_summary(auction_info, bids):
    """Print auction summary."""
    token_id = auction_info["tokenId"]
    end_time = auction_info["endTime"]
    settled = auction_info["settled"]
    time_remaining = format_time_remaining(end_time)
    
    status = "🔴 ENDED" if settled or time_remaining == "ENDED" else "🟢 ACTIVE"
    
    print("═" * 55)
    print(f"  QR AUCTION #{token_id}")
    print("═" * 55)
    print()
    print(f"Status: {status}")
    if status == "🟢 ACTIVE":
        print(f"Time Remaining: {time_remaining}")
        end_dt = datetime.fromtimestamp(end_time, timezone.utc)
        print(f"Ends: {end_dt.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Total Bids: {len(bids)}")
    print(f"Create Reserve: ${auction_info['createReserve'] / 1_000_000:.2f} USDC")
    print(f"Contribute Reserve: ${auction_info['contributeReserve'] / 1_000_000:.2f} USDC")
    print()
    
    # Sort bids by amount
    sorted_bids = sorted(bids, key=lambda x: x["totalAmount"], reverse=True)
    
    # Top 10
    print("─" * 55)
    print("  TOP 10 BIDS")
    print("─" * 55)
    
    for rank, bid in enumerate(sorted_bids[:10], 1):
        amount = bid["totalAmount"] / 1_000_000
        url = bid["urlString"]
        contributors = len(bid["contributions"])
        
        # Truncate URL for display
        display_url = url if len(url) <= 45 else url[:42] + "..."
        
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")
        print(f"{medal} ${amount:>8.2f} USDC ({contributors} contrib) - {display_url}")
    
    print()
    
    # Check for DRB bid
    drb_url = "https://grokipedia.com/page/debtreliefbot"
    drb_bid = next((b for b in bids if b["urlString"] == drb_url), None)
    
    if drb_bid:
        drb_rank = next(i for i, b in enumerate(sorted_bids, 1) if b["urlString"] == drb_url)
        drb_amount = drb_bid["totalAmount"] / 1_000_000
        leader_amount = sorted_bids[0]["totalAmount"] / 1_000_000
        gap = leader_amount - drb_amount
        
        print("─" * 55)
        print("  🌿 $DRB BID STATUS")
        print("─" * 55)
        print(f"Rank: #{drb_rank} of {len(bids)}")
        print(f"Amount: ${drb_amount:.2f} USDC")
        print(f"Gap to Leader: ${gap:.2f} USDC")
        print(f"Contributors: {len(drb_bid['contributions'])}")
        print()


def print_full(auction_info, bids):
    """Print full bid details."""
    print_summary(auction_info, bids)
    
    sorted_bids = sorted(bids, key=lambda x: x["totalAmount"], reverse=True)
    
    print("─" * 55)
    print("  ALL BIDS")
    print("─" * 55)
    
    for rank, bid in enumerate(sorted_bids, 1):
        amount = bid["totalAmount"] / 1_000_000
        url = bid["urlString"]
        
        print(f"\n#{rank} | ${amount:.2f} USDC")
        print(f"   URL: {url}")
        print(f"   Contributors: {len(bid['contributions'])}")
        for c in bid["contributions"]:
            addr = c["contributor"][:8] + "..." + c["contributor"][-4:]
            c_amount = c["amount"] / 1_000_000
            print(f"      - {addr}: ${c_amount:.2f}")


def print_json(auction_info, bids):
    """Print JSON output."""
    output = {
        "auction": {
            "tokenId": auction_info["tokenId"],
            "endTime": auction_info["endTime"],
            "settled": auction_info["settled"],
            "status": "ended" if auction_info["settled"] or format_time_remaining(auction_info["endTime"]) == "ENDED" else "active",
            "timeRemaining": format_time_remaining(auction_info["endTime"]),
            "createReserveUsdc": auction_info["createReserve"] / 1_000_000,
            "contributeReserveUsdc": auction_info["contributeReserve"] / 1_000_000
        },
        "bidCount": len(bids),
        "bids": [
            {
                "rank": rank,
                "totalUsdc": bid["totalAmount"] / 1_000_000,
                "url": bid["urlString"],
                "contributorCount": len(bid["contributions"]),
                "contributions": [
                    {
                        "address": c["contributor"],
                        "amountUsdc": c["amount"] / 1_000_000,
                        "timestamp": c["timestamp"]
                    }
                    for c in bid["contributions"]
                ]
            }
            for rank, bid in enumerate(sorted(bids, key=lambda x: x["totalAmount"], reverse=True), 1)
        ]
    }
    print(json.dumps(output, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Query QR Coin auction bids from contract")
    parser.add_argument("--summary", action="store_true", help="Show summary only (auction info + top 10)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--url", type=str, help="Get specific bid by URL")
    args = parser.parse_args()
    
    contract = get_contract()
    
    if args.url:
        bid = get_bid_by_url(contract, args.url)
        if bid:
            if args.json:
                print(json.dumps({
                    "url": bid["urlString"],
                    "totalUsdc": bid["totalAmount"] / 1_000_000,
                    "contributorCount": len(bid["contributions"]),
                    "contributions": [
                        {"address": c["contributor"], "amountUsdc": c["amount"] / 1_000_000}
                        for c in bid["contributions"]
                    ]
                }, indent=2))
            else:
                print(f"URL: {bid['urlString']}")
                print(f"Total: ${bid['totalAmount'] / 1_000_000:.2f} USDC")
                print(f"Contributors: {len(bid['contributions'])}")
                for c in bid["contributions"]:
                    addr = c["contributor"][:8] + "..." + c["contributor"][-4:]
                    print(f"  - {addr}: ${c['amount'] / 1_000_000:.2f}")
        else:
            print(f"No bid found for URL: {args.url}", file=sys.stderr)
            sys.exit(1)
        return
    
    auction_info = get_auction_info(contract)
    bids = get_all_bids(contract)
    
    if args.json:
        print_json(auction_info, bids)
    elif args.summary:
        print_summary(auction_info, bids)
    else:
        print_full(auction_info, bids)


if __name__ == "__main__":
    main()
