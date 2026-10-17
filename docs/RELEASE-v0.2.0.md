# VargaMesh MiniPool v0.2.0 — One-Click VMESH SOLO Mining (Developer Preview)

Self-hosted **VMESH-only** SHA-256d SOLO mining pool for Bitaxe, Lucky Miner, NerdAxe and compatible ASIC miners. **No Bitcoin node, BTC mining, or BTC wallet required.**

## What's new

- **One-click Windows GUI:** click **ONE CLICK: Install VMESH Node & Start Pool**.
- Downloads the **official VargaMesh Core v0.2.0** Windows x64 node and verifies both the pinned SHA-256 manifest and release archive digests.
- Starts a dedicated VMESH mainnet full node using authenticated loopback-only RPC.
- Displays node synchronization progress. SOLO Stratum activates **only after full synchronization**.
- Copy verified miner settings: `stratum+tcp://<your-local-PC-IP>:3938`, public VMESH wallet as username, password `x`.
- Responsive read-only local dashboard: `http://127.0.0.1:8686`.
- **Transparent 1% VMESH developer fee** in the child coinbase; remaining 99% pays the successful miner.
- Windows build CI performs 13 tests and verifies execution of the real official VargaMesh Core binary.

## Download and install (Windows 10/11 x64)

1. Under **Assets** below, download **VargaMesh-MiniPool-Windows-x64.zip** and **SHA256SUMS-MiniPool-Windows**.
2. Verify the ZIP with PowerShell: `Get-FileHash -Algorithm SHA256 .\VargaMesh-MiniPool-Windows-x64.zip`; compare to the published SHA-256 digest.
3. Extract the full ZIP; run `VargaMesh-MiniPool.exe`. This developer-preview binary is **unsigned** and may show a Windows SmartScreen warning.
4. Click **ONE CLICK: Install VMESH Node & Start Pool**. The installer asks for no seed phrase, no wallet password and no private key.
5. Wait for the VargaMesh node to synchronize fully. This **cannot be instantaneous**.
6. Enter your public `vm1...` wallet address, click **Copy Bitaxe settings**, and paste the settings into your ASIC. Allow the local Stratum port only on trusted private networks.

**Important:** The Windows GUI ZIP does **not** bundle VargaMesh Core. The node is downloaded separately from its official pinned release and verified when the user starts the setup. No Bitcoin software is installed.

## Links

- [English quick start and technical details](https://github.com/ati1993de/vargamesh-minipool#one-click-quick-start--windows-1011-no-manual-node-setup)
- [Deutsche Schritt-für-Schritt-Anleitung](https://github.com/ati1993de/vargamesh-minipool/blob/main/docs/README.de.md)
- [VargaMesh Core (official node)](https://github.com/ati1993de/vargamesh-core/releases/tag/v0.2.0)
- [Open-source implementation](https://github.com/ati1993de/vargamesh-minipool)
- [VMESH network explorer](https://mempool.vargamesh.com/)

## Release safety and scope

**This is a developer preview**, not audited production software. Automated tests and Windows binary/Core smoke tests have passed, but successful acceptance of a real ASIC-mined VMESH mainnet block has **not yet been demonstrated**. Stratum V1 is unencrypted and intended only for a trusted local network. No block finds or mining profitability are guaranteed. The 1% VMESH developer fee is a pool implementation choice, not a network-wide consensus tax.
