# VargaMesh MiniPool v0.2.3 — AxeOS "Block Header" Fix

**VMESH-only** SHA-256d SOLO pool for Bitaxe, NerdAxe, Lucky Miner and compatible Stratum V1 ASIC miners. Dedicated VargaMesh Core node, Windows one-click GUI, synthetic AuxPoW parent, 1% developer output in the **VMESH child** coinbase. No Bitcoin full node or BTC mining.

## Fix: blank Block Header and "Failed to process mining notification"

AxeOS v2.14 tries to decode a BIP34-style block height from the very beginning of `mining.notify`'s `coinb1` scriptSig. Before this release, our synthetic AuxPoW parent coinbase began with `/VMESH/`, so AxeOS incorrectly treated `0x2f` (the slash) as a length of 47 bytes and rejected the metadata decoder. Mining could **still work and receive accepted shares**, but AxeOS left the Block Header panel blank.

MiniPool now encodes the VMESH **child chain's height** as a BIP34-compatible prefix, then retains the normal `/VMESH/` tag, Stratum extranonces, and AuxPoW commitment. This is not the BTC block height; the parent is synthetic. This patch leaves the actual VMESH block header, consensus, job share difficulty, and 99% miner / 1% developer fee unchanged.

**AxeOS Amount may still show 0:** the synthetic parent coinbase carries **no Bitcoin rewards**. Check actual VMESH coinbase/payout information through VargaMesh Core or the VMESH explorer.

## Installation (Windows 10/11 x64)

1. Download the `VargaMesh-MiniPool-Windows-x64.zip` and `SHA256SUMS-MiniPool-Windows` assets below.
2. Verify the ZIP SHA-256 checksum in PowerShell using `Get-FileHash -Algorithm SHA256 .\VargaMesh-MiniPool-Windows-x64.zip`.
3. Close old MiniPool, unzip into a **new folder**, launch `VargaMesh-MiniPool.exe` and use **ONE CLICK: Install VMESH Node & Start Pool**. Existing separately stored VargaMesh node data and synced blockchain are reused; do not delete the chain directory.
4. Set Bitaxe Stratum V1 pool host to your MiniPool PC's LAN IP and port `3938`, username `vm1YOUR_VALID_ADDRESS.bitaxe01`, password `x`; reconnect the ASIC.
5. Verify the MiniPool's accepted-share count and AxeOS logs. A successful `mining.submit` result `{"result":true}` proves the connected server accepted a share, **not** that a VMESH mainnet block was mined.
6. If AxeOS says **"Using fallback pool"**, review its primary/fallback setup separately. If you intentionally put the MiniPool into fallback, valid shares can still be submitted there.

[English quick start](https://github.com/ati1993de/vargamesh-minipool/blob/main/README.md) · [Deutsche Anleitung](https://github.com/ati1993de/vargamesh-minipool/blob/main/docs/README.de.md) · [VargaMesh Explorer](https://mempool.vargamesh.com/)

**Security:** Developer preview / unsigned Windows EXE; only operate Stratum on a trusted private LAN. No real hardware-backed VMESH mainnet accepted-block test has been independently completed.
