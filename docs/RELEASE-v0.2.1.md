# VargaMesh MiniPool v0.2.1 — Bitaxe BIP310 / Version Rolling Fix

**VMESH-only SOLO pool** with local VargaMesh Core full node, Windows GUI, SHA-256d Stratum V1, synthetic AuxPoW and transparent **1% VMESH** developer fee. No Bitcoin node or BTC mining.

## What changed since v0.2.0

- Fixes Bitaxe/AxeOS **"Version rolling not supported (100%)"** caused by an unsupported BIP310 `mining.configure` extension.
- Implements BIP310 `version-rolling` negotiation with safe parent mask `1fffe000` and support for the sixth `mining.submit` field.
- Enforces the negotiated mask, detects duplicate shares per version and validates rolled synthetic AuxPoW parent headers.
- **VMESH child block version, chain ID and 99% miner / 1% developer coinbase allocation remain unchanged.**
- Windows GUI displays rejected shares; adds English and German troubleshooting guidance.
- GitHub CI builds Windows GUI, runs unit/integration tests and verifies the official Core v0.2.0 Windows node download/checksum/executable.

## Download and install (Windows)

1. Under **Assets** download `VargaMesh-MiniPool-Windows-x64.zip` and `SHA256SUMS-MiniPool-Windows`.
2. In PowerShell verify the ZIP via `Get-FileHash -Algorithm SHA256 .\VargaMesh-MiniPool-Windows-x64.zip` and compare the digest.
3. Close any running older MiniPool GUI. Extract all files to a fresh directory, open `VargaMesh-MiniPool.exe`, then click **ONE CLICK: Install VMESH Node & Start Pool**. Existing dedicated VMESH blockchain data is reused.
4. Wait for node sync and **Pool: ONLINE**. Configure **Primary** pool on Bitaxe to your Windows PC's LAN IP and port `3938` using **Stratum V1**; username `vm1YOUR_ADDRESS.bitaxe01`, password `x`.
5. If you see **"Using fallback pool"**, check that the Bitaxe *primary* pool is reachable; the fallback message is independent of version rolling. Restart Bitaxe after the MiniPool update if it does not renegotiate immediately.
6. Monitor **accepted** and **rejected** shares on the MiniPool GUI and dashboard. Hashrate without valid accepted shares is not proof of working mining.

## Documentation

- [English README and quick start](https://github.com/ati1993de/vargamesh-minipool#one-click-quick-start--windows-1011-no-manual-node-setup)
- [Deutsche Anleitung](https://github.com/ati1993de/vargamesh-minipool/blob/main/docs/README.de.md)
- [Official VMESH Core](https://github.com/ati1993de/vargamesh-core/releases/tag/v0.2.0)

**Safety:** Unsigned developer preview for trusted local networks only. BIP310 behavior passes simulated miner tests, but no real hardware-mined VMESH mainnet accepted block is yet independently verified. SOLO block rewards and profitability are not guaranteed.
