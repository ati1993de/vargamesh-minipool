# VargaMesh MiniPool — Self-Hosted VMESH SOLO Mining Pool for Bitaxe & SHA-256d ASICs

**Your hardware. Your VMESH rewards.** A lightweight, standalone **VargaMesh (VMESH) SOLO mining pool** for **Bitaxe, Lucky Miner, NerdAxe and compatible SHA-256d ASIC miners** with a native Windows manager, local web dashboard and direct connection to **VargaMesh Core**. **No Bitcoin node, Bitcoin wallet, centralized pool account, or BTC mining required.**

[![VMESH](https://img.shields.io/badge/VMESH-mainnet-38bcab)](https://vargamesh.com/) [![SHA256d](https://img.shields.io/badge/Mining-SHA--256d-blue)](https://vargamesh.com/mining.html) [![Fee](https://img.shields.io/badge/Developer%20fee-1%25-6b85ff)](#transparent-1-developer-fee) [![CI](https://github.com/ati1993de/vargamesh-minipool/actions/workflows/test.yml/badge.svg)](https://github.com/ati1993de/vargamesh-minipool/actions) [![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> **Release status: v0.1.0 developer preview.** Local serialization and mock-Stratum tests pass. An end-to-end, hardware-backed VMESH **mainnet accepted-block test has NOT been performed** for this release. Do not present this preview as audited or production-proven. Test with a dedicated synchronized node before production use. No guarantee of block rewards or profitability.

## Why MiniPool?

- **VMESH only** — native VMESH coins and wallets, not an ERC-20 token.
- **Self-hosted** — connect miners to your own PC / server and your own VargaMesh full node.
- **SOLO payout** — each authorized miner supplies a valid `vm1...` address; block rewards go to that address, minus the fixed 1% developer fee.
- **No BTC full node needed** — VMESH mainnet AuxPoW is fulfilled with a *synthetic local SHA-256d parent header*. No Bitcoin blocks or BTC rewards are involved.
- **Stratum V1** — `mining.subscribe`, `mining.authorize`, `mining.notify`, `mining.set_difficulty` and verified `mining.submit`.
- **Windows GUI** — launch the official VMESH node, start/stop the SOLO pool, open the dashboard and inspect logs.
- **Responsive dashboard** — worker count, estimated hashrate, shares, node health, block finds, per-worker stats.
- **Mainnet only** — rejects incorrect AuxPoW chain IDs and out-of-sync nodes.
- **Minimal dependencies** — Python 3.10+ standard library; no database, cloud APIs or extra Python pip packages required at runtime.
- **Privacy** — no website accounts, cloud analytics or private keys in the MiniPool.

## Quick start — Windows 10/11

1. Download the official **VargaMesh Core Windows x86_64 release** from [vargamesh-core/releases](https://github.com/ati1993de/vargamesh-core/releases). Verify `SHA256SUMS` from the release and extract the archive. Find `vargameshd.exe` inside its `bin` folder. **Never download Core from an unknown website.**
2. Install [Python 3.10+](https://www.python.org/downloads/windows/) and tick **Add Python to PATH**, or build/download the Windows GUI artifact from the GitHub Actions workflow.
3. Download/extract this MiniPool repository, then double-click **`start-windows.bat`** (for source distribution) or **`VargaMesh-MiniPool.exe`** (GitHub Actions Windows build).
4. Click **Browse** and select your official `vargameshd.exe`. Keep the suggested dedicated blockchain data folder. Click **Start VargaMesh Node**. The first mainnet sync may take time. The GUI does not bypass synchronization.
5. Click **Start SOLO Pool**. The dashboard will report *Waiting for VargaMesh Core* until the node reports synchronized mainnet and can serve AuxPoW block templates.
6. Click **Dashboard** and configure your Bitaxe or ASIC as below.

**Wallet note:** MiniPool never asks for private keys. Use an address from a validated VMESH mainnet wallet. Each worker's username determines its own on-chain payout destination.

### Connect a Bitaxe / NerdAxe / Lucky Miner

| Miner setting | Value |
|---|---|
| URL | `stratum+tcp://192.168.1.50:3938` (replace with your Windows PC's LAN IP) |
| Username | `vm1YOUR_VALID_VMESH_ADDRESS.bitaxe01` |
| Password | `x` |
| Algorithm | SHA-256d |
| SOLO rewards | 99% to the worker's wallet / 1% developer output |

The Windows firewall may prompt for access. Permit **private/home networks only**, not public network exposure. Stratum listens on `0.0.0.0:3938` by default so LAN miners can connect. The read-only web dashboard stays on `127.0.0.1:8686`, and **RPC stays loopback-only**.

**Important:** `vm1YOUR_VALID_VMESH_ADDRESS` is a placeholder, not a valid address. Use your actual wallet address. Each worker has one payout address, and an optional `.workerName` suffix (e.g. `.supra400`). The miner's account needs no registration.

## Quick start — Linux / headless

Install official [VargaMesh Core](https://github.com/ati1993de/vargamesh-core/releases) and sync a dedicated mainnet node with its RPC bound to `127.0.0.1:29667`.

```bash
git clone https://github.com/ati1993de/vargamesh-minipool.git
cd vargamesh-minipool
python3 main.py --headless
```

On the first launch, create `~/.config/VargaMeshMiniPool/config.json` using [config.example.json](config.example.json) and set `node.cookie_path` to the node's actual `.cookie` file. The headless process runs only the pool plus a local HTTP dashboard. It **does not start VargaMesh Core**; start the node separately.

Example dedicated Linux node (replace paths with real installed binaries):

```bash
mkdir -p "$HOME/vmesh-node"
/path/to/vargameshd -datadir="$HOME/vmesh-node" -server=1 \
  -rpcbind=127.0.0.1 -rpcallowip=127.0.0.1 -rpcport=29667 -port=29666
```

Configure `node.cookie_path` as `$HOME/vmesh-node/.cookie`, using the expanded absolute path in JSON. The node's RPC cookie is sensitive: do not commit, disclose or copy it to a web-served directory.

Start pool and dashboard:

```bash
python3 main.py --headless
# Open http://127.0.0.1:8686/ on the same host.
```

### Persistent configuration

Saved GUI configuration: `%APPDATA%\VargaMeshMiniPool\config.json` on Windows, or `~/.config/VargaMeshMiniPool/config.json` on typical Linux installations.

```json
{
  "node": {
    "binary": "C:\\path\\to\\vargameshd.exe",
    "data_dir": "C:\\path\\to\\private\\VMESH-chain",
    "cookie_path": "C:\\path\\to\\private\\VMESH-chain\\.cookie",
    "rpc_port": 29667
  },
  "pool": {
    "bind": "0.0.0.0",
    "stratum_port": 3938,
    "dashboard_port": 8686,
    "share_difficulty": 1024,
    "refresh_seconds": 12
  }
}
```

The default `share_difficulty` is fixed at **1024**. Select a lower value for slower devices or higher for many fast ASICs. Automatic variable difficulty (VarDiff) and Stratum V2 are **not implemented** in v0.1.0.

## Transparent 1% developer fee

**Exactly 1% of the VMESH block's full `coinbasevalue` (subsidy plus included transaction fees), rounded down to the smallest unit, is paid directly in the child's coinbase transaction.** The remaining 99% is assigned to the submitting miner's `vm1...` address. There are no Bitcoin fee outputs because there is no BTC mining in this program.

- Developer fee: **100 basis points (1.00%)**, fixed in `minipool/crypto.py`.
- Developer wallet: `vm1qsfsgj70pdv86nguvexzvsflmcknz4lrsj87wx9`
- No mandatory user registration, account balance or custodial wallet.
- Example on a 25 VMESH block without transaction fees: **24.75 VMESH to miner + 0.25 VMESH to developer**.
- On-chain payouts are subject to normal VMESH coinbase maturity (**100 blocks**).
- As open-source software, a modified fork can change its own fee. This is a **pool implementation rule, not a VMESH blockchain consensus tax**.

## How VMESH-only AuxPoW works without Bitcoin Core

VMESH mainnet sets `nAuxpowChainId = 22093` and activates mandatory AuxPoW from height 1. Its **child** header nonce is fixed to that chain ID; trying to mine the child nonce like Bitcoin is invalid.

MiniPool generates a VMESH child block template using VargaMesh Core `getblocktemplate`, creates a VMESH coinbase with the 99/1 output split, calculates the 80-byte child header hash, then constructs a *synthetic* parent coinbase with a `fabe6d6d` merged-mining commitment to that child hash. Stratum miners hash the local synthetic parent header. When a hash satisfies the **VMESH child target**, MiniPool serializes a Namecoin-style AuxPoW proof with a one-leaf auxiliary Merkle tree, appends all VMESH transactions and submits the resulting VMESH block to **`submitblock`** on VargaMesh Core.

The parent hash is **not** a valid Bitcoin block and does not need to be. VargaMesh checks the parent proof against VMESH consensus difficulty. There is no Bitcoin Core RPC and no bitcoin-chain synchronization or rewards.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the serialization and validation path.

## Security and limitations

- **Only run on a trusted LAN / firewalled host.** Stratum V1 is unencrypted and unauthenticated beyond payout-address validation. Do not expose Stratum on the public internet without a secure tunnel and independent review.
- Keep VargaMesh RPC bound to `127.0.0.1`; never expose the node cookie, RPC port or node private keys.
- The local dashboard is read-only and has no user accounts. It is deliberately bound to loopback.
- Windows GUI starts **a separately downloaded official VargaMesh Core binary**; it never bundles or auto-downloads an unaudited node binary. It does not modify the wallet or store private keys.
- VMESH node must finish synchronization. Miner shares before sync are not valid work.
- The pool uses fixed share difficulty and one active job per miner. Jobs are invalidated on template refresh. No historical share database, VarDiff, public API authorization, TLS or automatic network edge security yet.
- All users should independently verify coinbase payouts and accepted AuxPoW blocks on test infrastructure before mainnet production.

## Development and Windows EXE builds

No external runtime dependencies: `python -m unittest discover -v` runs the stdlib unit tests and a fake-RPC Stratum integration test.

The workflow [.github/workflows/windows.yml](.github/workflows/windows.yml) packages the Windows GUI using PyInstaller on a Windows GitHub runner. **That workflow has to run on GitHub before its executable can be downloaded**; there is no prebuilt exe in the source archive.

Repository SEO / topics suggestion: `vargamesh`, `vmesh`, `bitaxe`, `solo-mining`, `mining-pool`, `sha256d`, `asic-mining`, `stratum`, `auxpow`, `windows`, `bitcoin-mining-hardware`, `open-source`, `cryptocurrency`.

**Suggested GitHub description:** `Self-hosted VMESH SOLO mining pool for Bitaxe and SHA-256d ASICs. Windows GUI, Stratum V1, VargaMesh Core, synthetic AuxPoW and transparent 1% developer fee. No Bitcoin node required.`

## Related links

- [VargaMesh](https://vargamesh.com/)
- [VargaMesh Core (mainnet/testnet)](https://github.com/ati1993de/vargamesh-core)
- [Technical mining / exchange integration docs](https://vargamesh.com/listing/)
- [VMESH Mempool Explorer](https://mempool.vargamesh.com/)
- [Existing BTC+VMESH merged-mining project](https://github.com/ati1993de/vargamesh-ckpool-auxpow) (a **different** product)

## License and acknowledgement

MIT License. VargaMesh AuxPoW semantics and coinbase serialization are implemented in accordance with the public MIT-licensed [vargamesh-core](https://github.com/ati1993de/vargamesh-core) and [vargamesh-auxpow-bridge](https://github.com/ati1993de/vargamesh-auxpow-bridge) references. Hatchaus/Bitaxe-Pool was an interface idea only; its incomplete / unlicensed code has **not** been copied.
