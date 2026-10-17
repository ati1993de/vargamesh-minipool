"""Bitcoin-compatible serialization for VMESH-only AuxPoW solo mining.

The parent header is a synthetic SHA256d work container: NO Bitcoin RPC,
blockchain, coinbase subsidy or Bitcoin payouts exist in this program.
"""
import hashlib
import struct
import time
from dataclasses import dataclass

CHAIN_ID = 22093
DEV_FEE_BPS = 100
DEV_FEE_ADDRESS = 'vm1qsfsgj70pdv86nguvexzvsflmcknz4lrsj87wx9'
DEV_FEE_SCRIPT = bytes.fromhex('001482608979e16b0fa9a38cc984c827fbc5a62afc70')
DIFF1 = 0x00000000FFFF0000000000000000000000000000000000000000000000000000
ALPHABET = 'qpzry9x8gf2tvdw0s3jn54khce6mua7l'
MAGIC = bytes.fromhex('fabe6d6d')
# BIP310: rolling is permitted on the synthetic AuxPoW parent header ONLY.
# The VMESH child header/version and its 1% coinbase payout never change.
VERSION_ROLLING_MASK = 0x1fffe000


def dsha(b: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(b).digest()).digest()


def varint(n: int) -> bytes:
    if n < 0: raise ValueError('negative varint')
    if n < 253: return bytes([n])
    if n <= 0xffff: return b'\xfd' + struct.pack('<H', n)
    if n <= 0xffffffff: return b'\xfe' + struct.pack('<I', n)
    return b'\xff' + struct.pack('<Q', n)


def push(b: bytes) -> bytes:
    if len(b) > 75: raise ValueError('oversized script push')
    return bytes([len(b)]) + b


def scriptnum(n: int) -> bytes:
    if n < 0: raise ValueError('negative block height')
    b = bytearray()
    while n:
        b.append(n & 0xff); n >>= 8
    if not b: b.append(0)
    if b[-1] & 128: b.append(0)
    return bytes(b)


def bech32_polymod(v):
    g = (0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3)
    chk = 1
    for n in v:
        top = chk >> 25
        chk = ((chk & 0x1ffffff) << 5) ^ n
        for i, gen in enumerate(g):
            if (top >> i) & 1: chk ^= gen
    return chk


def bech32_script(addr: str) -> bytes:
    if not isinstance(addr, str) or len(addr) > 90 or addr.lower() != addr or not addr.startswith('vm1'):
        raise ValueError('expected lowercase VMESH mainnet vm1... address')
    pos = addr.rfind('1')
    try: data = [ALPHABET.index(x) for x in addr[pos+1:]]
    except ValueError as e: raise ValueError('invalid address character') from e
    if len(data) < 7: raise ValueError('address too short')
    hrp = addr[:pos]
    chk = bech32_polymod([ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp] + data)
    ver = data[0]
    if ver > 16: raise ValueError('invalid witness version')
    if chk != (1 if ver == 0 else 0x2bc830a3): raise ValueError('invalid Bech32/Bech32m checksum')
    accum = bits = 0
    raw = []
    for x in data[1:-6]:
        accum = (accum << 5) | x
        bits += 5
        if bits >= 8:
            bits -= 8
            raw.append((accum >> bits) & 255)
    if bits >= 5 or ((accum << (8-bits)) & 255): raise ValueError('invalid address padding')
    if not 2 <= len(raw) <= 40 or (ver == 0 and len(raw) not in (20, 32)):
        raise ValueError('invalid witness program')
    return bytes([0 if ver == 0 else 0x50 + ver, len(raw)]) + bytes(raw)


def payout_split(total: int) -> tuple[int, int]:
    if type(total) is not int or total <= 0: raise ValueError('invalid coinbase value')
    fee = total * DEV_FEE_BPS // 10000
    if not 0 < fee < total: raise ValueError('reward too small for fee')
    return total - fee, fee


def merkle_txids(txid_hexes):
    hashes = [bytes.fromhex(x)[::-1] for x in txid_hexes]
    if not hashes: raise ValueError('empty merkle tree')
    while len(hashes) > 1:
        if len(hashes) & 1: hashes.append(hashes[-1])
        hashes = [dsha(hashes[i] + hashes[i+1]) for i in range(0, len(hashes), 2)]
    return hashes[0]


def compact_target(bits: str) -> int:
    n = int(bits, 16)
    exponent, mantissa = n >> 24, n & 0x007fffff
    if not mantissa or n & 0x00800000: raise ValueError('invalid target encoding')
    target = (mantissa >> (8*(3-exponent))) if exponent <= 3 else (mantissa << (8*(exponent-3)))
    if target <= 0 or target >= 2**256: raise ValueError('invalid target')
    return target


@dataclass(frozen=True)
class ChildWork:
    height: int
    previous: str
    child_hash: str
    child_header: bytes
    tx_vector: bytes
    bits: str
    curtime: int
    mintime: int
    target: int
    payout: str
    reward: int
    fee: int


def make_child_work(g: dict, payout: str) -> ChildWork:
    script = bech32_script(payout)
    if (g.get('auxpow') is not True or g.get('auxpow_chainid') != CHAIN_ID or
            g.get('auxpow_childnonce') != CHAIN_ID or g.get('auxpow_submit') != 'submitblock'):
        raise ValueError('VargaMesh Node must support mainnet AuxPoW; unsupported template')
    height = g['height']
    version = g['version']
    if version & 0x100 == 0: raise ValueError('missing AuxPoW version flag')
    if not isinstance(g.get('transactions'), list): raise ValueError('missing transactions')
    if not g.get('default_witness_commitment'): raise ValueError('missing SegWit witness commitment')
    miner_value, fee = payout_split(g['coinbasevalue'])
    child_sig = push(scriptnum(height)) + b''.join(bytes.fromhex(v) for v in g.get('coinbaseaux', {}).values()) + push(b'/VMESH MiniPool/')
    if not 2 <= len(child_sig) <= 100: raise ValueError('invalid VMESH coinbase script')
    vin = (b'\x01' + b'\x00'*32 + b'\xff'*4 + varint(len(child_sig)) + child_sig + b'\xff'*4)
    witness = bytes.fromhex(g['default_witness_commitment'])
    if not witness.startswith(bytes.fromhex('6a24aa21a9ed')) or len(witness) != 38:
        raise ValueError('invalid witness commitment from GBT')
    outputs = (varint(3) + struct.pack('<Q', miner_value) + varint(len(script)) + script +
               struct.pack('<Q', fee) + varint(len(DEV_FEE_SCRIPT)) + DEV_FEE_SCRIPT +
               struct.pack('<Q', 0) + varint(len(witness)) + witness)
    ver = struct.pack('<I', 2)
    cb_nowit = ver + vin + outputs + b'\x00'*4
    cb = ver + b'\x00\x01' + vin + outputs + b'\x01\x20' + b'\x00'*32 + b'\x00'*4
    txids = [dsha(cb_nowit)[::-1].hex()] + [x['txid'] for x in g['transactions']]
    root = merkle_txids(txids)
    header = (struct.pack('<I', version) + bytes.fromhex(g['previousblockhash'])[::-1] + root +
              struct.pack('<I', g['curtime']) + struct.pack('<I', int(g['bits'], 16)) + struct.pack('<I', CHAIN_ID))
    if len(header) != 80: raise ValueError('invalid child header')
    chain_target = compact_target(g['bits'])
    if int(g['target'], 16) != chain_target: raise ValueError('VMESH target mismatch')
    vector = varint(len(txids)) + cb + b''.join(bytes.fromhex(x['data']) for x in g['transactions'])
    return ChildWork(height, g['previousblockhash'], dsha(header)[::-1].hex(), header, vector,
                     g['bits'], g['curtime'], g.get('mintime',g['curtime']), chain_target,
                     payout, miner_value, fee)


@dataclass(frozen=True)
class ParentJob:
    id: str
    work: ChildWork
    extranonce1: bytes
    extranonce2_size: int
    coinb1: bytes
    coinb2: bytes
    parent_version: int
    parent_prev: bytes
    parent_time: int

    def notify(self, clean=True):
        return [self.id, self.parent_prev.hex(), self.coinb1.hex(), self.coinb2.hex(), [],
                f'{self.parent_version:08x}', self.work.bits, f'{self.parent_time:08x}', clean]


def parent_job(work: ChildWork, extranonce1: bytes, job_id: str, extranonce2_size=4) -> ParentJob:
    if len(extranonce1) != 4: raise ValueError('extranonce1 must be 4 bytes')
    # The synthetic parent pays NO Bitcoin rewards; 0-satoshi OP_TRUE output.
    prefix = b'/VMESH/' + extranonce1
    suffix = MAGIC + bytes.fromhex(work.child_hash) + struct.pack('<II', 1, 0)
    sig_len = len(prefix) + extranonce2_size + len(suffix)
    if sig_len > 100: raise ValueError('parent scriptSig too long')
    coinb1 = b'\x01\x00\x00\x00' + b'\x01' + b'\x00'*32 + b'\xff'*4 + varint(sig_len) + prefix
    coinb2 = suffix + b'\xff'*4 + b'\x01' + struct.pack('<Q', 0) + b'\x01\x51' + b'\x00'*4
    return ParentJob(job_id, work, extranonce1, extranonce2_size, coinb1, coinb2,
                     0x20000000, b'\x00'*32, max(work.curtime, int(time.time())))


def parent_candidate(job: ParentJob, extranonce2: bytes, ntime: int, nonce: int, version=None):
    if len(extranonce2) != job.extranonce2_size: raise ValueError('invalid extranonce2 size')
    if not 0 <= nonce < 2**32 or not 0 <= ntime < 2**32: raise ValueError('nonce/time out of range')
    v = job.parent_version if version is None else version
    if not isinstance(v,int) or v < 0 or v >= 2**32 or ((v ^ job.parent_version) & ~VERSION_ROLLING_MASK):
        raise ValueError('parent version changed outside safe BIP310 rolling mask')
    parent_coinbase = job.coinb1 + extranonce2 + job.coinb2
    root = dsha(parent_coinbase)
    header = (struct.pack('<I', v) + job.parent_prev + root +
              struct.pack('<I', ntime) + struct.pack('<I', int(job.work.bits,16)) + struct.pack('<I',nonce))
    proof = (parent_coinbase + b'\x00'*32 + varint(0) + struct.pack('<i',0) +
             varint(0) + struct.pack('<i',0) + header)
    return header, job.work.child_header + proof + job.work.tx_vector


def hash_meets_target(header: bytes, target: int) -> bool:
    return int.from_bytes(dsha(header), 'little') <= target
