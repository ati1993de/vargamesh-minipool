# Architecture and security model

## Data path

`Bitaxe/ASIC -> Stratum V1 TCP 3938 -> pool work engine -> local-only VargaMesh JSON-RPC 29667 -> VMESH mainnet`

Dashboard: read-only HTTP server on `127.0.0.1:8686` (never binds publicly).

## Exactly one synthetic parent; no Bitcoin Core

VMESH mainnet mandatory AuxPoW is satisfied by a SHA256d synthetic parent header. Do not call it native child-header PoW: the VMESH child nonce remains fixed at `22093`. The parent coinbase has zero satoshi outputs and is **not submitted to the BTC chain**. Its `scriptSig` contains `fabe6d6d + child_hash_display_bytes + LE32(1) + LE32(0)`.

The Stratum miner gets a unique extranonce1; chooses extranonce2/ntime/nonce. The backend builds the parent coinbase, hashes its txid, populates parent Merkle root (one transaction), checks share difficulty, then compares parent PoW to the **child** compact nBits target.

A winning VMESH block is serialized as:

```text
[child-header-80-bytes]
[parent-coinbase-transaction]
[legacy-hashBlock-32-zero-bytes]
[parent-coinbase-merkle-branch-varint: 0]
[parent-index-int32: 0]
[aux-chain-merkle-branch-varint: 0]
[aux-chain-index-int32: 0]
[parent-header-80-bytes]
[VMESH tx-count CompactSize]
[VMESH witness coinbase with 99/1 output split]
[all GBT transactions in canonical order]
```

This mirrors `CAuxPow::Check` and `CheckAuxPowProofOfWork` in VargaMesh Core. Hash byte order and BIP34/SegWit commitment rules are important. Template construction refuses unrecognized AuxPoW metadata, missing witness commitment, network chain ID changes, malformed fee output addresses, or invalid target values.

## Developer fee accounting

`developer_value = floor(coinbasevalue * 100 / 10000)` (integer smallest-VMESH units, no floats). `miner_value = coinbasevalue - developer_value`. Child outputs are `[miner P2WPKH, developer P2WPKH, zero-valued witness-commitment OP_RETURN]`. No Bitcoin fee, subsidy, address, or wallet.

Every miner's authorized VMESH `vm1...` username selects its child coinbase payout. On a real block the *block's* miner is paid, not a weighted-share PPLNS split.

## Threat model

- RPC cookie and private data: only read by local Python process, never served by HTTP.
- Stratum: anonymous public TCP listener by default, limited to LAN by recommended firewall rules. Not a public hardened hosting service. Use a tunnel/reverse proxy only after explicit security configuration.
- JSON socket frames: 64 KiB maximum and idle read timeout.
- Pool jobs: one current job per miner; submitted shares are checked for duplicate nonce/extranonce/time, network target, timestamp and node best tip.
- Unsupported miner features: version rolling is declined. Miners requiring Stratum V2 or version rolling will not work until explicitly supported.
- Process failure: no restart daemon/watchdog included. For servers use an external process supervisor.
- Mainnet block acceptance: requires full synchronized VargaMesh Core and real valid work. Mock integration tests cannot prove acceptance under live mainnet consensus.

## Compatibility

Tested programmatically on Python 3.13 using stdlib unit and mock-RPC Stratum tests. Windows EXE packaging is defined as GitHub Actions and will need to run on the target GitHub repository. No connected Bitaxe device or live mainnet acceptance has been tested in the author's build environment here.
