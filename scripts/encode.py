#!/usr/bin/env python3
"""
Encode transaction calldata for QR Coin auction.
Usage: encode.py <function> [args...]

Functions:
  approve <spender> <amount_wei>
  createBid <tokenId> <url> <name>
  contributeToBid <tokenId> <url> <name>
"""

import sys
from eth_abi import encode
from web3 import Web3

# Function selectors (keccak256 of signature, first 4 bytes)
SELECTORS = {
    'approve': Web3.keccak(text='approve(address,uint256)')[:4].hex(),
    'createBid': Web3.keccak(text='createBid(uint256,string,string)')[:4].hex(),
    'contributeToBid': Web3.keccak(text='contributeToBid(uint256,string,string)')[:4].hex(),
}

def encode_approve(spender: str, amount_wei: int) -> str:
    selector = SELECTORS['approve']
    params = encode(['address', 'uint256'], [spender, amount_wei])
    return selector + params.hex()

def encode_create_bid(token_id: int, url: str, name: str) -> str:
    selector = SELECTORS['createBid']
    params = encode(['uint256', 'string', 'string'], [token_id, url, name])
    return selector + params.hex()

def encode_contribute_to_bid(token_id: int, url: str, name: str) -> str:
    selector = SELECTORS['contributeToBid']
    params = encode(['uint256', 'string', 'string'], [token_id, url, name])
    return selector + params.hex()

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    func = sys.argv[1]
    
    if func == 'approve':
        if len(sys.argv) != 4:
            print("Usage: encode.py approve <spender> <amount_wei>")
            sys.exit(1)
        spender = sys.argv[2]
        amount = int(sys.argv[3])
        print(encode_approve(spender, amount))
        
    elif func == 'createBid':
        if len(sys.argv) != 5:
            print("Usage: encode.py createBid <tokenId> <url> <name>")
            sys.exit(1)
        token_id = int(sys.argv[2])
        url = sys.argv[3]
        name = sys.argv[4]
        print(encode_create_bid(token_id, url, name))
        
    elif func == 'contributeToBid':
        if len(sys.argv) != 5:
            print("Usage: encode.py contributeToBid <tokenId> <url> <name>")
            sys.exit(1)
        token_id = int(sys.argv[2])
        url = sys.argv[3]
        name = sys.argv[4]
        print(encode_contribute_to_bid(token_id, url, name))
        
    elif func == 'selectors':
        for name, sel in SELECTORS.items():
            print(f"{name}: {sel}")
    else:
        print(f"Unknown function: {func}")
        print(__doc__)
        sys.exit(1)

if __name__ == '__main__':
    main()
