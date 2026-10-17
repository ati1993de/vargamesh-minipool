"""BIP310 compatibility tests for AxeOS / Bitaxe Stratum V1 clients."""
import json
import socket
import struct
import time
import unittest

from minipool.crypto import (DEV_FEE_ADDRESS, DEV_FEE_SCRIPT, VERSION_ROLLING_MASK,
                             compact_target, dsha, make_child_work, parent_candidate, parent_job)
from minipool.service import PoolState
from tests.test_stratum import FakeRPC

class MinerConnection:
    def __init__(self,s):self.s=s;self.buffer=b''
    def send(self,id,method,params):
        self.s.sendall((json.dumps({'id':id,'method':method,'params':params})+'\n').encode())
    def read(self):
        while b'\n' not in self.buffer:
            part=self.s.recv(4096)
            if not part:raise EOFError('Stratum closed unexpectedly')
            self.buffer+=part
        part,self.buffer=self.buffer.split(b'\n',1)
        return json.loads(part)

class BIP310Tests(unittest.TestCase):
    def start(self):
        cfg={'node':{'cookie_path':'nonexistent','rpc_port':29667},'pool':{
            'bind':'127.0.0.1','stratum_port':0,'refresh_seconds':10,'share_difficulty':1}}
        pool=PoolState(cfg)
        pool.rpc=FakeRPC()
        pool.start()
        return pool

    def test_parent_version_changes_only_inside_safe_mask(self):
        from tests.test_crypto import sample_gbt
        job=parent_job(make_child_work(sample_gbt(),DEV_FEE_ADDRESS),b'ABCD','id')
        orig,base=parent_candidate(job,b'1234',1700000001,9)
        rolled,block=parent_candidate(job,b'1234',1700000001,9,version=0x20002000)
        self.assertEqual(struct.unpack('<I',rolled[:4])[0],0x20002000)
        self.assertNotEqual(orig,rolled)
        self.assertEqual(block[:80],base[:80])  # child header is immutable
        self.assertIn(DEV_FEE_SCRIPT,block)  # 1% fee remains in child coinbase
        self.assertEqual(VERSION_ROLLING_MASK,0x1fffe000)
        with self.assertRaises(ValueError):
            parent_candidate(job,b'1234',1700000001,9,version=0x40000000)

    def test_bitaxe_configure_handshake(self):
        pool=self.start()
        try:
            with socket.create_connection(pool.server.server_address,timeout=4) as sock:
                sock.settimeout(4);c=MinerConnection(sock)
                c.send(1,'mining.configure',[['version-rolling','minimum-difficulty'],
                    {'version-rolling.mask':'1fffe000','version-rolling.min-bit-count':2}])
                ans=c.read()
                self.assertIsNone(ans['error'])
                self.assertTrue(ans['result']['version-rolling'])
                self.assertEqual(ans['result']['version-rolling.mask'],'1fffe000')
                self.assertIs(ans['result']['minimum-difficulty'],False)
                c.send(2,'mining.subscribe',[])
                sub=c.read()
                self.assertEqual(sub['id'],2)
                c.send(3,'mining.authorize',[DEV_FEE_ADDRESS+'.bitaxe','x'])
                self.assertTrue(c.read()['result'])
                self.assertEqual(c.read()['method'],'mining.set_difficulty')
                job=c.read()
                self.assertEqual(job['method'],'mining.notify')
                self.assertEqual(job['params'][5],'20000000')
        finally:pool.close()

    def test_rejects_unnnegotiated_version_and_out_of_mask(self):
        pool=self.start()
        try:
            with socket.create_connection(pool.server.server_address,timeout=4) as sock:
                sock.settimeout(4);c=MinerConnection(sock)
                c.send(1,'mining.subscribe',[])
                self.assertEqual(c.read()['id'],1)
                c.send(2,'mining.authorize',[DEV_FEE_ADDRESS+'.test','x'])
                self.assertTrue(c.read()['result'])
                c.read();notify=c.read()['params']
                base=[DEV_FEE_ADDRESS+'.test',notify[0],'12345678',notify[7],'00000000']
                c.send(3,'mining.submit',base+['00002000'])
                self.assertIn('not negotiated',c.read()['error'][1])
                c.send(4,'mining.configure',[['version-rolling'],
                    {'version-rolling.mask':'00002000','version-rolling.min-bit-count':1}])
                result=c.read()['result'];self.assertEqual(result['version-rolling.mask'],'00002000')
                c.send(5,'mining.submit',base+['00004000'])
                self.assertIn('outside negotiated mask',c.read()['error'][1])
                self.assertEqual(pool.status()['accepted'],0)
                self.assertGreaterEqual(pool.status()['rejected'],2)
        finally:pool.close()

    def test_rolled_share_success_and_vm_only_block_submission(self):
        import minipool.service as svc
        pool=self.start()
        fake=pool.rpc
        old_diff1=svc.DIFF1;svc.DIFF1=2**256-1
        try:
            with socket.create_connection(pool.server.server_address,timeout=4) as sock:
                sock.settimeout(5);c=MinerConnection(sock)
                c.send(1,'mining.configure',[['version-rolling'],
                    {'version-rolling.mask':'1fffe000','version-rolling.min-bit-count':2}])
                self.assertTrue(c.read()['result']['version-rolling'])
                c.send(2,'mining.subscribe',[]);sub=c.read();self.assertEqual(sub['id'],2)
                c.send(3,'mining.authorize',[DEV_FEE_ADDRESS+'.bitaxe','x'])
                self.assertTrue(c.read()['result'])
                self.assertEqual(c.read()['method'],'mining.set_difficulty')
                notify=c.read()['params']
                parent_coinbase=bytes.fromhex(notify[2])+bytes.fromhex('12345678')+bytes.fromhex(notify[3])
                merkle=dsha(parent_coinbase)
                target=compact_target(notify[6])
                ts=int(notify[7],16);bits=int(notify[6],16)
                for nonce in range(100):
                    header=(struct.pack('<I',0x20002000)+b'\x00'*32+merkle+
                            struct.pack('<III',ts,bits,nonce))
                    if int.from_bytes(dsha(header),'little')<=target:break
                else:self.fail('Mock target not met')
                c.send(4,'mining.submit',[DEV_FEE_ADDRESS+'.bitaxe',notify[0],
                      '12345678',notify[7],f'{nonce:08x}','00002000'])
                reply=c.read()
                self.assertTrue(reply['result'],str(reply))
                for _ in range(50):
                    if fake.last_block is not None:break
                    time.sleep(0.02)
                self.assertIsNotNone(fake.last_block)
                self.assertIn(DEV_FEE_SCRIPT,fake.last_block)
                self.assertEqual(pool.status()['accepted'],1)
                self.assertEqual(pool.status()['blocks'],1)
                self.assertIn(header,fake.last_block)
        finally:
            pool.close()
            svc.DIFF1=old_diff1

if __name__=='__main__':unittest.main()
