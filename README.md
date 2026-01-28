# QR Coin Auction Skill

An agent skill for interacting with [QR Coin](https://qrcoin.fun) auctions on Base blockchain.

## Features

- 🎯 Create and contribute to bids
- 🔐 Secure keychain storage (macOS/Linux)
- 💰 USDC approval management
- 📊 Auction status monitoring
- 🔗 Shared wallet support

## Installation

```bash
# Clone to your skills directory
git clone https://github.com/MerkleMoltBot/skill-qrcoin.git ~/clawd/skills/qrcoin

# Install dependencies
pip install web3 eth-account

# Run setup
cd ~/clawd/skills/qrcoin
./scripts/setup.sh
```

## Setup

The setup wizard will:
1. Create a new wallet or import existing
2. Store private key in system keychain
3. Configure your X handle for bids

```bash
./scripts/setup.sh
```

## Usage

### Check Auction Status
```bash
./scripts/build-tx.sh status
```

### Approve USDC
```bash
./scripts/submit-tx.sh approve 50  # Approve 50 USDC
```

### Create New Bid
```bash
./scripts/submit-tx.sh createBid "https://your-url.com" "YourName"
```

### Contribute to Existing Bid
```bash
./scripts/submit-tx.sh contribute "https://existing-bid-url.com"
```

## Contracts (Base Mainnet)

| Contract | Address |
|----------|---------|
| Auction | `0x7309779122069EFa06ef71a45AE0DB55A259A176` |
| USDC | `0x833589fCD6eDb6E08f4c7c32D4f71b54bdA02913` |

## Security

- Private keys stored in OS keychain (never plain text)
- Export disabled by default (policy-controlled)
- Supports shared wallet architecture

## Requirements

- Python 3.8+
- `web3` and `eth-account` packages
- macOS Keychain or Linux secret-service

## License

MIT
