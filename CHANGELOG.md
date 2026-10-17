# Changelog

## 0.2.2 — 2026-10-17

Fixes Stratum V1 ASIC share verification and wrong duplicate counting.

- Correctly reconstruct synthetic parent coinbase from `coinb1 + extranonce1 + extranonce2 + coinb2`, matching how Bitaxe/AxeOS and other miners compute work.
- Do not embed extranonce1 inside `coinb1`; still include its 4 bytes in the parent coinbase's declared script length.
- Rejected low-difficulty shares are not stored as previously accepted duplicate work.
- Diagnostics display computed and required share difficulty for rejected work.
- New independent Stratum miner regression tests generate valid and invalid candidate shares and verify serialized submitted VMESH AuxPoW blocks.
- Retain BIP310 version rolling, exactly 99% miner / 1% developer child coinbase output, and Windows one-click verified VMESH Core node installation.

**Status:** Developer preview. Independent ASIC mainnet accepted-block proof still pending.

## 0.2.1 — 2026-10-17

Bitaxe / AxeOS Stratum V1 BIP310 compatibility fix.

- Proper `mining.configure` version-rolling negotiation and mask intersection (server mask `1fffe000`).
- Accept `version_bits` as sixth Stratum `mining.submit` parameter only after negotiation; reject bits outside the negotiated mask.
- Recompute synthetic AuxPoW parent header nVersion from the negotiated mask while keeping the VMESH child header and 1% developer coinbase output unchanged.
- Share duplicate detection now includes rolled version bits.
- Improved rejection diagnostics and Windows GUI rejected-share counter.
- Automated Bitaxe-like Stratum tests: handshake, mask rejection and simulated rolled block submission.
- Updated English/German Bitaxe setup guidance, including primary-versus-fallback pool troubleshooting.
- Updated Windows EXE release with checksum and source tag.

**Scope:** Developer preview. Not yet validated with an actual hardware-mined VMESH mainnet block. Do not expose Stratum to public internet without hardening.

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
