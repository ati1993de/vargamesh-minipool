# VargaMesh MiniPool — Self-Hosted VMESH SOLO Mining Pool for Bitaxe & SHA-256d ASICs

**Your hardware. Your VMESH rewards.** A lightweight, standalone **VargaMesh (VMESH) SOLO mining pool** for **Bitaxe, Lucky Miner, NerdAxe and compatible SHA-256d ASIC miners** with a native Windows manager, local web dashboard and direct connection to **VargaMesh Core**. **No Bitcoin node, Bitcoin wallet, centralized pool account, or BTC mining required.**

[![VMESH](https://img.shields.io/badge/VMESH-mainnet-38bcab)](https://vargamesh.com/) [![SHA256d](https://img.shields.io/badge/Mining-SHA--256d-blue)](https://vargamesh.com/mining.html) [![Fee](https://img.shields.io/badge/Developer%20fee-1%25-6b85ff)](#transparent-1-developer-fee) [![CI](https://github.com/ati1993de/vargamesh-minipool/actions/workflows/test.yml/badge.svg)](https://github.com/ati1993de/vargamesh-minipool/actions) [![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> **Release status: v0.3.0 developer preview (Windows GUI + Docker for Linux x86_64).** Offline serialization and mock-Stratum tests pass, and the GitHub Windows build checks the official VargaMesh Core download, checksum, and executable. An end-to-end, hardware-backed VMESH **mainnet accepted-block test has NOT been performed** for this release. Do not present this preview as audited or production-proven. Test with a dedicated synchronized node before production use. No guarantee of block rewards or profitability.

## Why MiniPool?

- **VMESH only** — native VMESH coins and wallets, not an ERC-20 token.
- **Self-hosted** — connect miners to your own PC / server and your own VargaMesh full node.
- **SOLO payout** — each authorized miner supplies a valid `vm1...` address; block rewards go to that address, minus the fixed 1% developer fee.
- **No BTC full node needed** — VMESH mainnet AuxPoW is fulfilled with a *synthetic local SHA-256d parent header*. No Bitcoin blocks or BTC rewards are involved.
- **Stratum V1** — `mining.subscribe`, `mining.authorize`, `mining.notify`, `mining.set_difficulty` and verified `mining.submit`.
- **One-click Windows GUI** — download SHA-256 verified VMESH Core, start/sync the dedicated node, automatically enable SOLO mining and copy Bitaxe settings.
- **Responsive dashboard** — worker count, estimated hashrate, shares, node health, block finds, per-worker stats.
- **Mainnet only** — rejects incorrect AuxPoW chain IDs and out-of-sync nodes.
- **Minimal dependencies** — Python 3.10+ standard library; no database, cloud APIs or extra Python pip packages required at runtime.
- **Privacy** — no website accounts, cloud analytics or private keys in the MiniPool.

## Linux Docker Compose (VMESH node included, no BTC, no npm)

**Tested build:** GitHub Actions compiles a Docker image with pinned official VargaMesh Core v0.2.0 for Linux x86_64, launches the integrated Core + MiniPool container, and probes the live dashboard/status API. Docker stores blockchain and pool files in persistent volumes, runs without root, binds Core RPC to container loopback only, and keeps host Stratum/Dashboard local by default.

```bash
git clone https://github.com/ati1993de/vargamesh-minipool.git
cd vargamesh-minipool
bash start-docker.sh
docker compose logs -f --tail=80
```

Local dashboard: `http://127.0.0.1:8686`. Local Stratum: `127.0.0.1:3938`. Wait until the VMESH node sync is completed; initial synchronization is NOT instant. **For Bitaxe on your private LAN**, configure `STRATUM_BIND_IP` in `.env` and run:

```bash
docker compose -f compose.yaml -f compose.lan.yaml up -d --build
```

For **Nginx Proxy Manager (NPM)**, use `compose.npm.yaml` with a shared external Docker network and an authenticated HTTPS Proxy Host; the dashboard is read-only but exposes public miner identities. Node.js/npm is *not* needed. **Do not publish Stratum or the dashboard on an unprotected public VPS**; for remote miners use a private VPN.

**[Complete Linux + Docker + Bitaxe + NPM manual (German)](docs/DOCKER.de.md)** · [Linux Docker GitHub CI](.github/workflows/docker.yml) · [Dockerfile](Dockerfile)

## One-click quick start — Windows 10/11 (no manual node setup)

[**Download current MiniPool v0.3.0 release (Windows + source)**](https://github.com/ati1993de/vargamesh-minipool/releases/tag/v0.3.0) · [**Deutsche Anleitung**](docs/README.de.md) · [**Release notes**](docs/RELEASE-v0.2.0.md)


**Recommended:** Download **VargaMesh-MiniPool-Windows-x64.zip** from the [official v0.2.0 GitHub Release](https://github.com/ati1993de/vargamesh-minipool/releases/tag/v0.3.0). Extract the ZIP completely and run **VargaMesh-MiniPool.exe**. The release also provides a separate SHA-256 checksum file. Alternatively, obtain the latest developer artifact from [GitHub Actions](https://github.com/ati1993de/vargamesh-minipool/actions/workflows/windows.yml), or use Python 3.10+ with **start-windows.bat**.

1. Click **ONE CLICK: Install VMESH Node & Start Pool** in the Windows GUI.
2. MiniPool downloads **official VargaMesh Core v0.2.0 (Windows x64)** from the official GitHub release, verifies the manifest and archive against two **pinned SHA-256 hashes**, and extracts the node into your user's Local AppData folder.
3. It launches a dedicated **VargaMesh mainnet node** with authenticated loopback-only RPC, and shows synchronization status. The first blockchain download takes time.
4. **Only after the VargaMesh node reports full synchronization**, MiniPool starts VMESH Stratum and opens the local dashboard.
5. Paste a public **vm1... payout address** into the GUI and click **Copy Bitaxe settings**. Configure your SHA-256d miner using those credentials.

No Bitcoin node or BTC wallet is required. No VMESH seed phrase or private key is ever requested. The node installer runs **only after an explicit click** and does not touch any existing VMESH installation. Manual advanced setup controls remain available.

**Status:** Windows builds from main are developer previews, not production-audited releases. No hardware-confirmed mainnet block acceptance has been demonstrated yet. The Windows EXE is currently unsigned and may trigger SmartScreen. Do not expose Stratum/RPC to the public Internet.

### AxeOS "Block Header" blank / mining notification decoder fix (v0.2.3)

**Fixed:** AxeOS v2.14 coinbase-decoding code expects the parent coinbase `scriptSig` to begin with a BIP34-style block-height push. The VMESH-only synthetic AuxPoW parent previously began directly with `/VMESH/`. AxeOS interpreted `/` (byte `0x2f`) as a **47-byte height field**, rejected the decode, logged `Failed to process mining notification` and left its **Block Header** fields blank — despite successfully mining and submitting valid shares.

The v0.2.3 parent coinbase instead begins with `push(scriptnum(VMESH_child_height)) + b'/VMESH/'`, followed by the Stratum extranonces and AuxPoW commitment. This changes **only the synthetic parent coinbase** and makes the AxeOS Bitcoin-oriented display parser happy. It does **not** mine Bitcoin or alter the VMESH child block, 1% VMESH developer fee, or share-validation difficulty. AxeOS may show **Amount = 0** (the synthetic parent has no BTC output); actual VMESH rewards are in the VMESH child block, verified through the VargaMesh explorer / Core node.

The warning **"Using fallback pool"** is independent of this decoder error. AxeOS can mine valid VMESH shares using MiniPool configured as its fallback. For predictable failover, make MiniPool the *primary* server or review the primary/fallback entries. The presence of `"result":true` in the AxeOS log and an increasing MiniPool accepted-share counter confirm the active MiniPool connection.

### Bitaxe / AxeOS: low-difficulty shares and extranonce1 fix (v0.2.3)

**Fixed in v0.2.3:** Standard Stratum V1 miners construct the synthetic parent coinbase as `coinb1 + extranonce1 + extranonce2 + coinb2`. The server previously omitted `extranonce1` from the reconstruction while embedding it directly inside `coinb1`, causing the ASIC and server to hash **different parent work** and reject valid miner shares with `Low difficulty share`. The corrected server gives the miner `coinb1` *without* `extranonce1`, then inserts both extranonces when reconstructing its parent header.

Shares are now marked as duplicates **only after valid proof-of-work verification**. An invalid share retried by the same miner remains a low-difficulty rejection instead of being incorrectly counted as a duplicate. With a real ASIC, check that accepted shares rise and invalid/duplicate counters remain low after restarting MiniPool. The share-difficulty setting of `1024` can remain unchanged while verifying the fix. Independent synthetic-miner Stratum integration tests cover the full extranonce1/2 reconstruction and the 1% VMESH developer coinbase.

**Compatibility inherited from v0.2.1:**

MiniPool implements `mining.configure` with the **BIP310 `version-rolling` extension** and negotiates the safe parent header mask `1fffe000` (intersected with the miner mask). Bitaxe/AxeOS can submit the optional sixth `version_bits` field. Submitted bits outside the negotiated mask are rejected. Only the **synthetic AuxPoW parent nVersion** may roll; the **VMESH child header, AuxPoW chain ID and 99/1 VMESH coinbase payouts stay unchanged**.

If AxeOS reports **"Version rolling not supported (100%)"**, update MiniPool to v0.2.3 or later. Restart the old MiniPool Windows application (and, if required, restart the Bitaxe) so the Stratum connection renegotiates BIP310. With a 0.48 TH/s Bitaxe at share difficulty 1024, accepted shares may arrive roughly every 9 seconds on average, but arrival times vary. There is no guarantee of finding a VMESH block.

If AxeOS shows **"Using fallback pool"**, the configured **primary pool is unreachable or rejected**. On the Bitaxe Pool Settings page, set the intended primary Stratum V1 host to the LAN IP of the MiniPool PC (example `192.168.178.55`, port `3938`), username `vm1YOUR_VALID_ADDRESS.bitaxe01`, password `x`. Disable an unused backup/fallback entry or configure a separate working backup. Do not confuse the active fallback selection with successful primary connectivity. Keep the local PC and Bitaxe on trusted private LAN and allow TCP 3938 only on the private Windows firewall profile.

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

The default `share_difficulty` is fixed at **1024**. Select a lower value for slower devices or higher for many fast ASICs. Automatic variable difficulty (VarDiff) and Stratum V2 are **not implemented** in v0.2.3.

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

### Verify the Windows release ZIP

Download `VargaMesh-MiniPool-Windows-x64.zip` and `SHA256SUMS-MiniPool-Windows` from the same [v0.2.3 release](https://github.com/ati1993de/vargamesh-minipool/releases/tag/v0.3.0). In PowerShell, compare the `Get-FileHash -Algorithm SHA256` output of the ZIP with the first digest in the checksum file. The MiniPool Windows ZIP **does not bundle the node**: the separately downloaded official VargaMesh Core v0.2.0 archive is verified at installation time.

## Security and limitations

- **Only run on a trusted LAN / firewalled host.** Stratum V1 is unencrypted and unauthenticated beyond payout-address validation. Do not expose Stratum on the public internet without a secure tunnel and independent review.
- Keep VargaMesh RPC bound to `127.0.0.1`; never expose the node cookie, RPC port or node private keys.
- The local dashboard is read-only and has no user accounts. It is deliberately bound to loopback.
- Windows GUI auto-downloads **official, version-pinned and checksum-verified VargaMesh Core** only after a user click. It does not modify the wallet or store private keys.
- VMESH node must finish synchronization. Miner shares before sync are not valid work.
- The pool uses fixed share difficulty and one active job per miner. Jobs are invalidated on template refresh. No historical share database, VarDiff, public API authorization, TLS or automatic network edge security yet.
- All users should independently verify coinbase payouts and accepted AuxPoW blocks on test infrastructure before mainnet production.

## Development and Windows EXE builds

No external runtime dependencies: `python -m unittest discover -v` runs the stdlib unit tests and a fake-RPC Stratum integration test.

The workflow [.github/workflows/windows.yml](.github/workflows/windows.yml) packages the Windows GUI with PyInstaller on Windows runners on each main update. The **v0.2.3 release** includes a tested Windows ZIP and published SHA-256 checksum file; source snapshots are provided automatically by GitHub. After future development commits, Actions artifacts may be newer than the tagged release. The EXE installs official Core on first run after an explicit click, rather than bundling it.

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
