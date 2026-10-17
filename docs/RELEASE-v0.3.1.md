# VargaMesh MiniPool v0.3.1 — Public Linux VPS Docker Bindings + English Deployment Guide

**VMESH-only** SOLO mining pool for Bitaxe, Lucky Miner, NerdAxe and SHA-256d ASICs. Run a dedicated full VargaMesh Core node, Stratum V1 and the web dashboard with Docker Compose on Linux x86_64, or run the Windows one-click GUI. **No Bitcoin node, BTC mining or Node.js/npm dependencies.**

## New in v0.3.1: opt-in public web and Stratum on 0.0.0.0

The Docker host bindings are now configurable **independently** using `.env`. By default both remain private (`127.0.0.1`). If you intentionally want both accessible from the public internet on your Linux VPS:

```dotenv
MINIPOOL_STRATUM_BIND_IP=0.0.0.0
MINIPOOL_WEB_BIND_IP=0.0.0.0
MINIPOOL_DASHBOARD_ALLOWED_HOSTS=YOUR_PUBLIC_IPV4,pool.example.com
```

Run `docker compose up -d --build`. The **VPS provider firewall** must permit inbound TCP `3938` (Stratum) and `8686` (web); avoid changing firewall settings in a way that locks you out of SSH. Set `MINIPOOL_DASHBOARD_ALLOWED_HOSTS` to the actual public IP and/or DNS hostname that visitors will use. The VargaMesh Core **RPC stays private** inside the container on `127.0.0.1:29667`. Existing persistent chain data remains in Docker volumes across container restarts.

**[COMPLETE ENGLISH PUBLIC VPS INSTALLATION GUIDE — firewall, access, Docker commands, NPM HTTPS and rollback](https://github.com/ati1993de/vargamesh-minipool/blob/main/docs/PUBLIC-DEPLOYMENT.en.md)**

## Safety warning

The embedded dashboard is **read-only but has no login or TLS**: public access exposes miners' public wallet addresses, worker names, status and pool events. HTTP Host allowlisting is **not authentication**. Public Stratum V1 is **unencrypted** and not hardened against abusive/untrusted network clients or denial-of-service. Prefer an **authenticated HTTPS reverse proxy** for web and upstream firewall/rate limiting or a private VPN for mining. Docker published ports may bypass normal UFW INPUT filtering. Do not expose RPC.

## Other capabilities unchanged

- Integrated verified official VargaMesh Core v0.2.0 x86_64 in Linux Docker.
- VMESH-only SHA-256d/AuxPoW SOLO Stratum V1, BIP310 version rolling and AxeOS-compatible mining notifications.
- 99% miner / 1% developer VMESH child-chain Coinbase split (no BTC payouts).
- Read-only responsive dashboard, live sync information, accepted/rejected shares and persistent data volumes.
- Windows v0.3.1 unsigned GUI ZIP attached under Assets with SHA-256 checksum.
- Offline unit/integration tests and GitHub Linux Docker build + actual container/dashboard smoke checks.

**Release status:** Developer Preview. A real ASIC-found VMESH mainnet block accepted by consensus has not yet been independently demonstrated; do not claim production-audited pool operation.

[Main README](https://github.com/ati1993de/vargamesh-minipool) · [German Linux/Docker guide](https://github.com/ati1993de/vargamesh-minipool/blob/main/docs/DOCKER.de.md) · [Official VargaMesh Core](https://github.com/ati1993de/vargamesh-core).
