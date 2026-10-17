import json
import socket
import struct
import time
import unittest
from unittest import mock
from minipool.crypto import DEV_FEE_ADDRESS, DEV_FEE_SCRIPT, dsha, compact_target
from minipool.service import PoolState
from tests.test_crypto import sample_gbt

class FakeRPC:
    last_block=None
    def chain_info(self):return {'chain':'main','initialblockdownload':False}
    def template(self):return sample_gbt()
    def call(self,method,*args):
        if method=='getnetworkinfo':return {'connections':2}
        if method=='getbestblockhash':return sample_gbt()['previousblockhash']
        if method=='submitblock':
            self.last_block=bytes.fromhex(args[0]);return None
        if method=='getblockhash':
            return dsha(self.last_block[:80])[::-1].hex() if self.last_block else None
        raise AssertionError(method)

class StratumTests(unittest.TestCase):
    def test_subscription_auth_and_job_then_reject_low_difficulty_share(self):
        cfg={'node':{'cookie_path':'nonexistent','rpc_port':29667},'pool':{'bind':'127.0.0.1',
             'stratum_port':0,'refresh_seconds':1,'share_difficulty':1024}}
        pool=PoolState(cfg);pool.rpc=FakeRPC();pool.start()
        try:
            with socket.create_connection(pool.server.server_address,timeout=4) as s:
                s.settimeout(3)
                def send(msg):s.sendall(json.dumps(msg).encode()+b'\n')
                def read():
                    b=b''
                    while not b.endswith(b'\n'):
                        b+=s.recv(1)
                    return json.loads(b)
                send({'id':1,'method':'mining.subscribe','params':[]})
                reply=read();self.assertEqual(reply['id'],1);self.assertEqual(len(reply['result'][1]),8)
                send({'id':2,'method':'mining.authorize','params':[DEV_FEE_ADDRESS+'.bitaxe','x']})
                reply=read();self.assertTrue(reply['result'])
                diff=read();self.assertEqual(diff['method'],'mining.set_difficulty')
                job=read();self.assertEqual(job['method'],'mining.notify')
                self.assertEqual(job['params'][6],sample_gbt()['bits'])
                self.assertIn('fabe6d6d',job['params'][3])
                send({'id':3,'method':'mining.submit','params':[DEV_FEE_ADDRESS+'.bitaxe',job['params'][0],
                     '00000001',job['params'][7],'00000001']})
                reply=read();self.assertFalse(reply['result']);self.assertEqual(reply['id'],3)
        finally:pool.close()


    def test_successful_mock_block_submission_and_one_percent_fee(self):
        # Fake work has an intentionally easy target: this tests the entire
        # miner-to-RPC serialization path, NOT a VMESH mainnet consensus proof.
        import minipool.service as svc
        cfg={'node':{'cookie_path':'nonexistent','rpc_port':29667},'pool':{'bind':'127.0.0.1',
             'stratum_port':0,'refresh_seconds':10,'share_difficulty':1}}
        pool=PoolState(cfg); fake=FakeRPC();pool.rpc=fake
        old_diff1=svc.DIFF1
        svc.DIFF1=2**256-1
        pool.start()
        try:
            with socket.create_connection(pool.server.server_address,timeout=4) as s:
                s.settimeout(4)
                def read():
                    b=b''
                    while not b.endswith(b'\n'):b+=s.recv(1)
                    return json.loads(b)
                def send(id,method,params):
                    s.sendall((json.dumps({'id':id,'method':method,'params':params})+'\n').encode())
                send(1,'mining.subscribe',[])
                subscription=read(); extranonce1=subscription['result'][1]
                send(2,'mining.authorize',[DEV_FEE_ADDRESS+'.worker','x'])
                self.assertTrue(read()['result'])
                self.assertEqual(read()['method'],'mining.set_difficulty')
                notification=read()['params']
                cb=(bytes.fromhex(notification[2])+bytes.fromhex(extranonce1)
                    +bytes.fromhex('12345678')+bytes.fromhex(notification[3]))
                merkle=dsha(cb)
                ts=int(notification[7],16)
                bits=int(notification[6],16)
                for nonce in range(100):
                    header=(struct.pack('<I',0x20000000)+b'\x00'*32+merkle+
                        struct.pack('<III',ts,bits,nonce))
                    if int.from_bytes(dsha(header),'little')<=compact_target(notification[6]):break
                else:self.fail('mock target was not met in 100 nonces')
                send(3,'mining.submit',[DEV_FEE_ADDRESS+'.worker',notification[0],
                     '12345678',notification[7],f'{nonce:08x}'])
                self.assertTrue(read()['result'])
                # submitblock RPC completes immediately in the fake node
                for _ in range(40):
                    if fake.last_block: break
                    time.sleep(.025)
                self.assertIsNotNone(fake.last_block)
                self.assertIn(DEV_FEE_SCRIPT, fake.last_block)
                self.assertIn(struct.pack('<Q',25000000),fake.last_block)
                self.assertEqual(pool.status()['blocks'],1)
        finally:
            pool.close()
            svc.DIFF1=old_diff1

if __name__=='__main__':unittest.main()
