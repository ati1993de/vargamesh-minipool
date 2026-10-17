# VargaMesh MiniPool v0.2.2 — Bitaxe Low-Difficulty Share Fix

This is a **VMESH-only** SHA-256d Stratum V1 SOLO pool for Bitaxe, NerdAxe, Lucky Miner and compatible miners. It runs with your own VargaMesh Core full node — **no Bitcoin node or BTC mining**.

## Main fix

The v0.2.1 Stratum server built a synthetic AuxPoW parent coinbase incorrectly: `extranonce1` was embedded in `coinb1` but not included in the server-side reconstruction at the same position where Stratum V1 ASICs insert it. The miner and pool could therefore calculate **different hashes** for the same nominal job, causing the user's **“Low difficulty share”** errors and potentially preventing valid shares from being accepted.

**v0.2.2 correctly uses `coinb1 + extranonce1 + extranonce2 + coinb2` for both miner and server.** The parent coinbase's script length remains correct.

Additional changes:

- Retain BIP310 `version-rolling` for Bitaxe/AxeOS.
- Fix **“Duplicate share”** misclassification: rejected low-difficulty work is no longer cached as a valid duplicate.
- Rejected-share details show actual computed difficulty and required difficulty.
- Add independent simulated ASIC Stratum tests for correct share acceptance and VMESH AuxPoW block serialization.
- The VMESH child block, consensus parameters and on-chain **1% developer fee / 99% miner payout** remain unchanged.

## Install on Windows

1. Download `VargaMesh-MiniPool-Windows-x64.zip` and `SHA256SUMS-MiniPool-Windows` below under **Assets**.
2. In PowerShell, verify the ZIP with `Get-FileHash -Algorithm SHA256 .\VargaMesh-MiniPool-Windows-x64.zip` and compare against the digest in `SHA256SUMS-MiniPool-Windows`.
3. Fully close the old MiniPool, unzip v0.2.2 into a **new folder**, and start `VargaMesh-MiniPool.exe`.
4. Choose **ONE CLICK: Install VMESH Node & Start Pool**. Existing separate VMESH Core v0.2.0 binary and synchronized blockchain data can be reused; **do not delete the VMESH chain folder**.
5. In AxeOS, configure **Primary Pool** with your PC's LAN IP, port `3938`, Stratum V1; username is your public `vm1... .bitaxe01` address without spaces, password `x`. Save and reconnect your Bitaxe.
6. Initially keep **share difficulty 1024**. Watch accepted/rejected counters: accepted shares should eventually appear if the connection and ASIC configuration are correct.

If AxeOS still says **“Using fallback pool”**, verify the primary pool host/IP and Bitaxe fallback selection; that is separate from the low-difficulty fix.

## Notes and documentation

- [English setup](https://github.com/ati1993de/vargamesh-minipool/blob/main/README.md)
- [Deutsche Anleitung](https://github.com/ati1993de/vargamesh-minipool/blob/main/docs/README.de.md)
- [VMESH Core source](https://github.com/ati1993de/vargamesh-core)

**Developer preview**: The new code has automated synthetic-miner validation. No independent physical Bitaxe mainnet accepted-block test has yet been completed. Do not expose RPC/Stratum publicly. Mining profitability and block discovery cannot be guaranteed. The Windows executable remains unsigned.
