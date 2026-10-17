# VargaMesh MiniPool v0.3.0 — Windows One-Click + Linux Docker Compose

The **self-hosted, VMESH-only SOLO mining pool** for Bitaxe, NerdAxe, Lucky Miner and compatible SHA-256d ASICs now works with both Windows (native GUI) and **Linux x86_64 / Docker Compose** (bundled official VMESH full node). No Bitcoin node or Bitcoin mining. The transparent **1% VMESH developer coinbase output** remains unchanged.

## New: Linux Docker one-command setup

```bash
git clone https://github.com/ati1993de/vargamesh-minipool.git
cd vargamesh-minipool
bash start-docker.sh
```

Docker **builds from source**, securely downloading the official VargaMesh Core v0.2.0 Linux x86_64 archive from the official GitHub release and verifying both the pinned SHA256SUMS manifest and Core archive digests. No precompiled Linux archive is attached to this release: Docker performs the image build.

- Dedicated node, Stratum V1 and responsive read-only dashboard in one container.
- Independent persistent Docker volumes for blockchain and pool configuration.
- Non-root container, read-only root filesystem, loopback-only RPC and default loopback-only host ports.
- Initial chain sync must complete before any VMESH mining work is distributed.
- Local dashboard: `http://127.0.0.1:8686`; local Stratum: `127.0.0.1:3938`.
- Trusted private LAN Bitaxe access: set `STRATUM_BIND_IP` in `.env`, then `docker compose -f compose.yaml -f compose.lan.yaml up -d --build`.
- Optional Nginx Proxy Manager: `compose.npm.yaml` with shared Docker network and **authenticated HTTPS** dashboard. No Node.js/npm required.

**[Complete German Docker + Bitaxe + Nginx Proxy Manager instructions](https://github.com/ati1993de/vargamesh-minipool/blob/main/docs/DOCKER.de.md)**

## Windows GUI (retained)

Under **Assets**, download `VargaMesh-MiniPool-Windows-x64.zip` and `SHA256SUMS-MiniPool-Windows`. Check the ZIP with PowerShell `Get-FileHash -Algorithm SHA256 .\VargaMesh-MiniPool-Windows-x64.zip`. Extract and launch the EXE; click **ONE CLICK: Install VMESH Node & Start Pool**. It installs the pinned official Windows VargaMesh Core v0.2.0 after explicit user action and waits for sync. Existing Core blockchain data can be reused.

## Compatibility and validation

- Stratum V1 + BIP310 version rolling, correct extranonce1/2 share reconstruction, AxeOS block-height display.
- GitHub unit/integration tests and **real Linux Docker Core launch + dashboard smoke** verified.
- The synthetic AuxPoW parent has no BTC payout: AxeOS may show `UNKNOWN:51` for a zero-valued `OP_TRUE` output. Actual 99/1 VMESH rewards live in the VargaMesh child coinbase.
- **Developer preview:** A genuine VMESH mainnet block mined using a hardware ASIC and accepted by consensus has not been independently verified. Do not expose Stratum or the dashboard to untrusted public networks.

Documentation: [English README](https://github.com/ati1993de/vargamesh-minipool) · [Deutsche Anleitung](https://github.com/ati1993de/vargamesh-minipool/blob/main/docs/README.de.md) · [Linux Docker CI](https://github.com/ati1993de/vargamesh-minipool/actions/workflows/docker.yml).
