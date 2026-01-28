# QR Coin Auction Skill

An agent skill for interacting with [QR Coin](https://qrcoin.fun) auctions on Base blockchain.

## Features

- 🎯 Create and contribute to bids
- 🔐 Secure keychain storage (macOS/Linux)
- 🔒 Policy-based key export protection
- 💰 USDC approval management
- 📊 Auction status monitoring
- 🔗 Shared wallet support

## Installation

```bash
# Clone to your skills directory
git clone https://github.com/MerkleMoltBot/skill-qrcoin.git ~/clawd/skills/qrcoin

# Install dependencies
pip install web3 eth-account

# Copy default security policy (IMPORTANT)
mkdir -p ~/.clawdbot/config
cp ~/clawd/skills/qrcoin/config/wallet-policy.json ~/.clawdbot/config/

# Run setup
cd ~/clawd/skills/qrcoin
./scripts/setup.sh
```

## Setup

The setup wizard will:
1. Create a new wallet or import existing
2. Store private key in system keychain (never plain text)
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

### Key Storage
- Private keys stored in OS keychain (macOS Keychain / Linux secret-service)
- Keys are **never** stored in plain text config files
- Supports shared wallet architecture across multiple skills

### Export Protection
By default, private key export is **disabled**. This prevents the agent from being tricked into revealing keys.

The policy file at `~/.clawdbot/config/wallet-policy.json` controls this:

```json
{
  "policies": {
    "allowKeyExport": false,
    "allowSeedExport": false,
    "allowKeyImport": true
  }
}
```

**To export keys manually** (requires machine access):
```bash
# macOS
security find-generic-password -s qrcoin-wallet -a agent-wallet -w

# Linux
secret-tool lookup service qrcoin-wallet account agent-wallet
```

### Default Policy
A secure default policy is included in `config/wallet-policy.json`. Copy it during installation:

```bash
cp ~/clawd/skills/qrcoin/config/wallet-policy.json ~/.clawdbot/config/
```

## Requirements

- Python 3.8+
- `web3` and `eth-account` packages
- macOS Keychain or Linux secret-service

## File Structure

```
qrcoin/
├── README.md
├── SKILL.md              # Agent instructions
├── LICENSE
├── config/
│   └── wallet-policy.json  # Default security policy
├── references/
│   └── auction-abi.json
└── scripts/
    ├── setup.sh          # Wallet setup wizard
    ├── submit-tx.sh      # Sign & submit transactions
    ├── build-tx.sh       # Build tx / check status
    ├── wallet.py         # Wallet management
    ├── keychain.py       # Secure key storage
    └── encode.py         # ABI encoding
```

## License

MIT
