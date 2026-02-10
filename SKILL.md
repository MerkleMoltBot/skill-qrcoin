# QR Coin Auction Skill (V5)

Interact with the QR Coin auction platform on Base blockchain (qrcoin.fun).

## Contract Addresses (Base Mainnet)

- **Auction Contract:** `0x7309779122069EFa06ef71a45AE0DB55A259A176`
- **USDC Token:** `0x833589fCD6eDb6E08f4c7c32D4f71b54bdA02913`
- **Platform:** https://qrcoin.fun

---

## First-Time Setup

Run the setup wizard to create a dedicated wallet:

```bash
./scripts/setup.sh
```

The setup will:
1. **Create a new wallet** or import an existing one
2. **Display the seed phrase** — back this up immediately!
3. **Save the private key** to config for transactions
4. **Configure RPC and X handle**

### What You'll Need

After setup, fund the wallet on Base:
- **ETH** for gas (~0.001 ETH is enough for many transactions)
- **USDC** for bidding (minimum 1 USDC to contribute, ~11 USDC to create new bid)

### Config Location

```
~/.clawdbot/skills/qrcoin/config.json
```

Contains: `privateKey`, `address`, `rpcUrl`, `xHandle`

**Security:** File is chmod 600 (owner read/write only)

---

## Wallet Management

```bash
# Check wallet balance
./scripts/wallet.py balance

# Export private key (for backup)
./scripts/wallet.py export

# Show wallet address
./scripts/wallet.py address

# Import existing wallet
./scripts/wallet.py import 0xYOUR_PRIVATE_KEY
```

---

## Submitting Transactions

Use `submit-tx.sh` to sign and submit transactions directly:

### Approve USDC

Before bidding, approve USDC spending:

```bash
./scripts/submit-tx.sh approve      # Approve 30 USDC (default)
./scripts/submit-tx.sh approve 50   # Approve 50 USDC
```

> ⚠️ **Important:** The `contributeToBid` function has no amount parameter — it pulls the **entire approved amount** from your wallet. Set your approval to exactly what you want to bid.

### Create New Bid

```bash
./scripts/submit-tx.sh createBid "https://your-url.com"
./scripts/submit-tx.sh createBid "https://your-url.com" "YourName"
```

### Contribute to Existing Bid

```bash
./scripts/submit-tx.sh contribute "https://existing-bid-url.com"
```

Name defaults to your configured X handle.

> ⚠️ **Warning:** This will transfer your **entire approved USDC amount** to the bid. The contract has no partial contribution — approve only what you want to bid.

### Non-Interactive Mode

Use `--yes` or `-y` to skip confirmation prompts (for automation/cron):

```bash
./scripts/submit-tx.sh contribute "https://grokipedia.com/page/debtreliefbot" --yes
```

---

## Read-Only Operations

Use `build-tx.sh` for status and building transaction data:

```bash
# Check auction status
./scripts/build-tx.sh status

# Build transaction without submitting (for inspection)
./scripts/build-tx.sh contribute "https://example.com"
```

---

## Query Bids (Direct Contract)

Use `query-bids.py` to query auction data directly from the contract:

```bash
# Full output with all bids
./scripts/query-bids.py

# Summary only (auction info + top 10 + DRB status)
./scripts/query-bids.py --summary

# JSON output for programmatic use
./scripts/query-bids.py --json

# Get specific bid by URL
./scripts/query-bids.py --url "https://grokipedia.com/page/debtreliefbot"
```

### JSON Output Structure

```json
{
  "auction": {
    "tokenId": 332,
    "endTime": 1769965200,
    "settled": false,
    "status": "active",
    "timeRemaining": "2h 30m",
    "createReserveUsdc": 11.11,
    "contributeReserveUsdc": 1.0
  },
  "bidCount": 32,
  "bids": [
    {
      "rank": 1,
      "totalUsdc": 357.0,
      "url": "https://example.com",
      "contributorCount": 5,
      "contributions": [...]
    }
  ]
}
```

**Use this for cron jobs** to get accurate auction state and bid rankings.

---

## Agent Identity

When bidding, the `name` parameter should be your X/Twitter handle (without @):
- Configured during setup as `xHandle`
- Links on-chain activity to your social identity
- Example: `MerkleMoltBot`

---

## USDC Conversion

- USDC uses 6 decimals
- 1 USDC = 1,000,000 wei
- 10 USDC = 10,000,000 wei

---

## Reserve Prices

- **Create Bid:** ~11.11 USDC minimum
- **Contribute:** ~1.00 USDC minimum

Check current prices with `./scripts/build-tx.sh status`

---

## Error Codes

| Error | Meaning |
|-------|---------|
| `RESERVE_PRICE_NOT_MET` | Bid amount too low |
| `URL_ALREADY_HAS_BID` | Use contributeToBid instead |
| `BID_NOT_FOUND` | URL doesn't have existing bid |
| `AUCTION_OVER` | Auction has ended |
| `AUCTION_NOT_STARTED` | Auction hasn't begun |

---

## Typical Workflow

```bash
# 1. Setup (first time only)
./scripts/setup.sh

# 2. Fund wallet with ETH + USDC on Base

# 3. Check balance
./scripts/wallet.py balance

# 4. Approve USDC (this is the amount that will be bid!)
./scripts/submit-tx.sh approve 30  # Default: 30 USDC

# 5. Check auction status
./scripts/build-tx.sh status

# 6. Place or contribute to bid
./scripts/submit-tx.sh contribute "https://grokipedia.com/page/debtreliefbot"
```

---

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `setup.sh` | Interactive wallet setup wizard |
| `wallet.py` | Wallet management (create/export/balance) |
| `submit-tx.sh` | Sign and submit transactions |
| `build-tx.sh` | Build calldata / check status |
| `query-bids.py` | Query bids directly from contract (recommended for cron) |
| `encode.py` | Low-level calldata encoding |

---

## Reference

- Full ABI: `references/auction-abi.json`
- Platform: https://qrcoin.fun
- Contract: [BaseScan](https://basescan.org/address/0x7309779122069EFa06ef71a45AE0DB55A259A176)
