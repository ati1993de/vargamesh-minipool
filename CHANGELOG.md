# Changelog

## 0.2.0 — 2026-10-17

Windows one-click VMESH-only setup (developer preview).

- Official VargaMesh Core v0.2.0 Windows x64 download on explicit first-run click.
- Pinned SHA-256 verification of the release manifest and the Core archive before extraction; safe extraction checks.
- Dedicated VMESH node with authenticated loopback-only RPC and automatic initial synchronization progress.
- Stratum pool starts only when Core reports the mainnet synchronized.
- One-click copy of Bitaxe/ASIC Stratum settings with the miner's public `vm1...` payout address.
- Windows x64 GUI artifact built and verified by GitHub Actions; CI downloads, verifies and executes the official Windows Core binary.
- English and German setup guides, release ZIP checksum and published release notes.
- Original VMESH-only SOLO Stratum, synthetic AuxPoW proofs and the transparent 1% VMESH developer coinbase output remain unchanged.

**Limitations:** This is an unsigned developer preview. Hardware-backed acceptance of a real VMESH mainnet block has not been demonstrated. First synchronization still requires time/disk space. Do not expose Stratum or VargaMesh RPC directly to the public internet.

## 0.1.0 — 2026-10-17

Initial developer preview of VMESH-only Stratum V1 SOLO mining with synthetic SHA-256d AuxPoW parent proofs, 1% VMESH developer coinbase output, locally authenticated VargaMesh RPC, read-only responsive monitoring dashboard, Windows Tkinter manager, headless Linux mode, tests, and GitHub Actions Windows packaging recipe.

No full-mainnet acceptance test or signed Windows distributable included in source release.
