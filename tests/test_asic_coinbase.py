"""Independent miner reconstructions catching extranonce1 accounting errors."""
import json
import socket
import struct
import time
import unittest

from minipool.crypto import (DEV_FEE_ADDRESS, DEV_FEE_SCRIPT,
                             compact_target, dsha)
from minipool.service import PoolState
from tests.test_stratum import FakeRPC
from tests.test_version_rolling import MinerConnection
import minipool.service as svc

class ASICCoinbaseTests(unittest.TestCase):
    def setUp(self):
        self.cfg={'node':{'cookie_path':'nonexistent','rpc_port':29667},
                  'pool':{'bind':'127.0.0.1','stratum_port':0,
                          'refresh_seconds':12,'share_difficulty':1024}}
        self.pool=PoolState(self.cfg)
        self.fake=FakeRPC()
        self.pool.rpc=self.fake
        self.pool.start()
    def tearDown(self):
        self.pool.close()

    def connect(self, rolled=False):
        sock=socket.create_connection(self.pool.server.server_address,timeout=4)
        sock.settimeout(5)
        c=MinerConnection(sock)
        if rolled:
            c.send(1,'mining.configure',[['version-rolling'],
                {'version-rolling.mask':'1fffe000','version-rolling.min-bit-count':2}])
            self.assertTrue(c.read()['result']['version-rolling'])
        c.send(2,'mining.subscribe',[])
        sub=c.read()
        nonce1=bytes.fromhex(sub['result'][1])
        self.assertEqual(len(nonce1),4)
        c.send(3,'mining.authorize',[DEV_FEE_ADDRESS+'.bitaxe01','x'])
        self.assertTrue(c.read()['result'])
        diff=c.read()
        self.assertEqual(diff['method'],'mining.set_difficulty')
        notify=c.read()
        self.assertEqual(notify['method'],'mining.notify')
        return sock,c,nonce1,notify['params']

    @staticmethod
    def independent_miner_header(notify, extranonce1, extranonce2, version, nonce):
        # Standard Stratum V1 client: inject extranonce1 and extranonce2.
        cb=(bytes.fromhex(notify[2])+extranonce1+extranonce2+bytes.fromhex(notify[3]))
        header=(struct.pack('<I',version)+bytes.fromhex(notify[1])
                +dsha(cb)+struct.pack('<III',int(notify[7],16),
                    int(notify[6],16),nonce))
        return cb,header

    def test_asic_work_without_rolling_matches_submitted_parent(self):
        previous=svc.DIFF1
        svc.DIFF1=2**256-1
        try:
            sock,c,en1,notify=self.connect()
            with sock:
                en2=bytes.fromhex('12aabbcd')
                target=compact_target(notify[6])
                for nonce in range(100):
                    cb,header=self.independent_miner_header(notify,en1,en2,
                                                int(notify[5],16),nonce)
                    if int.from_bytes(dsha(header),'little')<=target:break
                else:self.fail('No easy target found')
                c.send(4,'mining.submit',[DEV_FEE_ADDRESS+'.bitaxe01',
                    notify[0],en2.hex(),notify[7],f'{nonce:08x}'])
                accepted=c.read()
                self.assertTrue(accepted['result'],accepted)
                for _ in range(100):
                    if self.fake.last_block is not None:break
                    time.sleep(.015)
                self.assertIsNotNone(self.fake.last_block)
                self.assertEqual(self.fake.last_block[80:80+len(cb)],cb)
                self.assertIn(header,self.fake.last_block)
                self.assertIn(DEV_FEE_SCRIPT,self.fake.last_block)
                self.assertEqual(self.pool.status()['accepted'],1)
                self.assertEqual(self.pool.status()['blocks'],1)
                # Only a previously ACCEPTED share is considered duplicate.
                c.send(5,'mining.submit',[DEV_FEE_ADDRESS+'.bitaxe01',
                    notify[0],en2.hex(),notify[7],f'{nonce:08x}'])
                self.assertIn('Duplicate share',c.read()['error'][1])
        finally:
            svc.DIFF1=previous

    def test_invalid_share_resubmission_is_not_a_duplicate(self):
        sock,c,en1,notify=self.connect()
        with sock:
            en2=bytes.fromhex('00000001')
            # The pool needs diff >=1024: find a nonce which unambiguously
            # misses share target.  No real VMESH network work required.
            for nonce in range(50):
                _,header=self.independent_miner_header(notify,en1,en2,
                                               int(notify[5],16),nonce)
                if int.from_bytes(dsha(header),'little')>svc.DIFF1//1024:break
            else:self.fail('Could not find low-diff nonce')
            p=[DEV_FEE_ADDRESS+'.bitaxe01',notify[0],
                  en2.hex(),notify[7],f'{nonce:08x}']
            c.send(4,'mining.submit',p)
            r1=c.read()
            c.send(5,'mining.submit',p)
            r2=c.read()
            self.assertIn('Low difficulty share',r1['error'][1])
            self.assertIn('Low difficulty share',r2['error'][1])
            self.assertEqual(self.pool.status()['rejected'],2)
            self.assertEqual(self.pool.status()['accepted'],0)

if __name__=='__main__':
    unittest.main()
