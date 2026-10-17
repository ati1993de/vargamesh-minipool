import struct
import unittest
from minipool.crypto import *

ADDRESS=DEV_FEE_ADDRESS

def sample_gbt():
    commitment='6a24aa21a9ed'+dsha(b'\x00'*64).hex()
    return {'height':24,'version':0x20000100,'previousblockhash':'ab'*32,
        'bits':'207fffff','target':f'{compact_target("207fffff"):064x}',
        'curtime':1700000000,'mintime':1699999900,'coinbasevalue':2500000000,
        'transactions':[],'auxpow':True,'auxpow_chainid':22093,
        'auxpow_childnonce':22093,'auxpow_submit':'submitblock',
        'default_witness_commitment':commitment,'coinbaseaux':{'flags':'062f503253482f'}}

class CryptoTests(unittest.TestCase):
    def test_dev_address_script_matches_audited_code(self):
        self.assertEqual(bech32_script(ADDRESS),DEV_FEE_SCRIPT)
        for bad in ('btc1abc','VM1xyz','vm1badsum','vm1mixCase'):
            with self.assertRaises(ValueError):bech32_script(bad)

    def test_fee_and_merkle(self):
        self.assertEqual(payout_split(2500000000),(2475000000,25000000))
        a=dsha(b'a')[::-1].hex();b=dsha(b'b')[::-1].hex()
        self.assertEqual(merkle_txids([a,b]),dsha(dsha(b'a')+dsha(b'b')))
        self.assertEqual(varint(252),b'\xfc')
        self.assertEqual(varint(253),b'\xfd\xfd\x00')

    def test_child_header_contains_fixed_chain_nonce_and_fee(self):
        g=sample_gbt();w=make_child_work(g,ADDRESS)
        self.assertEqual(len(w.child_header),80)
        self.assertEqual(w.child_header[-4:],struct.pack('<I',22093))
        self.assertEqual(w.reward,2475000000)
        self.assertEqual(w.fee,25000000)
        self.assertIn(struct.pack('<Q',25000000)+varint(len(DEV_FEE_SCRIPT))+DEV_FEE_SCRIPT,w.tx_vector)
        self.assertEqual(w.child_hash,dsha(w.child_header)[::-1].hex())

    def test_one_leaf_auxpow_proof(self):
        work=make_child_work(sample_gbt(),ADDRESS)
        job=parent_job(work,b'ABCD','job1')
        parent,full=parent_candidate(job,b'1234',1700000001,42)
        # Independent Stratum V1 reconstruction: the miner injects BOTH
        # extranonce1 from subscribe and extranonce2 into the coinbase.
        coinbase=job.coinb1+job.extranonce1+b'1234'+job.coinb2
        self.assertEqual(parent[36:68],dsha(coinbase))
        self.assertNotIn(job.extranonce1,job.coinb1)
        self.assertEqual(coinbase[4],1)
        # Regression for AxeOS 2.14+ coinbase_decode: expects BIP34 height
        # immediately after the scriptSig-length at byte 42 of coinb1.
        script_len = job.coinb1[41]
        height_len = job.coinb1[42]
        self.assertTrue(1 <= height_len <= 4)
        self.assertEqual(int.from_bytes(job.coinb1[43:43+height_len],'little'),work.height)
        # Parent tx: 42-byte input prefix + scriptSig + 4-byte sequence,
        # one zero-valued OP_TRUE output (11 bytes) + 4-byte locktime.
        self.assertEqual(len(coinbase),61+script_len)
        self.assertIn(b'/VMESH/',job.coinb1)
        self.assertNotIn(b'\xf1\xbe',job.coinb1)
        self.assertIn(MAGIC+bytes.fromhex(work.child_hash)+struct.pack('<II',1,0),coinbase)
        self.assertEqual(full[:80],work.child_header)
        self.assertEqual(full[80:80+len(coinbase)],coinbase)
        self.assertEqual(full[80+len(coinbase):80+len(coinbase)+32],b'\x00'*32)
        self.assertTrue(full.endswith(work.tx_vector))
        self.assertEqual(len(parent),80)
        self.assertEqual(job.notify()[3],job.coinb2.hex())

    def test_fail_closed_wrong_chain(self):
        for field,val in [('auxpow',False),('auxpow_chainid',1),('auxpow_childnonce',1),('auxpow_submit','none')]:
            g=sample_gbt();g[field]=val
            with self.assertRaises(ValueError):make_child_work(g,ADDRESS)

    def test_invalid_missing_segwit(self):
        g=sample_gbt();del g['default_witness_commitment']
        with self.assertRaises(ValueError):make_child_work(g,ADDRESS)

if __name__=='__main__':unittest.main()
