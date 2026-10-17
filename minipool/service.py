"""VMESH-only Stratum V1 SOLO pool backed by a local VargaMesh Core node.

One VMESH payout address per subscribed Stratum worker. No Bitcoin node.
"""
import json
import pathlib
import logging
import secrets
import socket
import socketserver
import threading
import time
from collections import deque
from dataclasses import dataclass, field

from .crypto import (DIFF1, bech32_script, compact_target, hash_meets_target,
                     make_child_work, parent_candidate, parent_job)
from .rpc import VMeshRPC

LOG = logging.getLogger('minipool')

class PoolState:
    def __init__(self, config):
        self.config = config
        self.rpc = VMeshRPC(config['node']['cookie_path'], config['node'].get('rpc_port',29667))
        self.lock = threading.RLock()
        self.template = None
        self.node_info = None
        self.node_error = 'Waiting for VargaMesh Core...'
        self.connected = set()
        self.started = time.monotonic()
        self.accepted = 0
        self.rejected = 0
        self.blocks = 0
        self.best_share = 0.0
        self.history = deque(maxlen=150)
        self.finds = deque(maxlen=30)
        self.audit_file = pathlib.Path(config['pool'].get('audit_file', '')).expanduser() if config['pool'].get('audit_file') else None
        if self.audit_file and self.audit_file.is_file():
            try:
                for line in self.audit_file.read_text(encoding='utf-8').splitlines()[-30:]:
                    self.finds.appendleft(json.loads(line))
                self.blocks = len(self.finds)
            except (OSError,ValueError) as error:
                LOG.warning('Could not read existing local block audit: %s',error)
        self.share_events = deque(maxlen=5000)
        self.stop = threading.Event()
        self.scheduler = None
        self.server = None
        self.server_thread = None

    def log(self, msg, level='info'):
        with self.lock:
            self.history.appendleft({'time':int(time.time()),'level':level,'message':msg})
        getattr(LOG,level if level in ('info','warning','error') else 'info')(msg)

    def status(self):
        with self.lock:
            now=time.time()
            total_diff = sum(diff for timestamp, diff in self.share_events if timestamp > now - 120)
            miners = [{'worker':w.worker, 'address':w.address, 'accepted':w.accepted,
                       'rejected':w.rejected,'last_share':w.last_share, 'difficulty':w.difficulty}
                      for w in list(self.connected) if w.authorized]
            return {'name':'VargaMesh MiniPool', 'mode':'VMESH-only SOLO','fee_percent':1,
                    'network':'mainnet', 'uptime':int(time.monotonic()-self.started),
                    'node_ready':self.template is not None,'node_error':self.node_error,
                    'height':self.template['height'] if self.template else None,
                    'tip':self.template['previousblockhash'] if self.template else None,
                    'peers':self.node_info.get('connections') if self.node_info else None,
                    'miners':miners, 'workers':len(miners), 'accepted':self.accepted,
                    'rejected':self.rejected, 'blocks':self.blocks,
                    'hashrate_hs':round(total_diff * 2**32 / 120,2),
                    'best_share_difficulty':self.best_share,
                    'found':list(self.finds), 'events':list(self.history)[:60],
                    'timestamp':int(now)}

    def refresh_loop(self):
        last_key=None
        while not self.stop.is_set():
            try:
                g=self.rpc.template()
                key=(g['previousblockhash'],g['curtime'],g['coinbasevalue'],len(g['transactions']))
                # Validate chain semantics BEFORE distributing work.
                from .crypto import CHAIN_ID
                if g.get('auxpow') is not True or g.get('auxpow_chainid') != CHAIN_ID:
                    raise RuntimeError('Wrong chain or AuxPoW support missing')
                if g.get('auxpow_childnonce') != CHAIN_ID:
                    raise RuntimeError('Wrong VMESH child nonce')
                network_info=self.rpc.call('getnetworkinfo')
                with self.lock:
                    self.node_error = ''
                    self.node_info = network_info
                    if key != last_key:
                        self.template=g
                        last_key=key
                        clients=list(self.connected)
                    else:
                        clients=[]
                for c in clients:
                    if c.authorized: c.new_job()
            except Exception as e:
                with self.lock:
                    was_ready=self.template is not None
                    self.template=None
                    self.node_error=str(e)[:250]
                if was_ready: self.log('Mining paused: '+str(e)[:180],'warning')
            self.stop.wait(self.config['pool'].get('refresh_seconds',12))

    def start(self):
        cfg=self.config['pool']
        address=cfg.get('bind','0.0.0.0')
        port=int(cfg.get('stratum_port',3938))
        self.server=StratumTCP((address,port),MinerHandler)
        self.server.pool=self
        self.server_thread=threading.Thread(target=self.server.serve_forever,name='Stratum',daemon=True)
        self.server_thread.start()
        self.scheduler=threading.Thread(target=self.refresh_loop,name='VMESH-template',daemon=True)
        self.scheduler.start()
        self.log(f'Stratum listening at {address}:{port} (VMESH-only, 1% developer fee)')

    def close(self):
        self.stop.set()
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        with self.lock:
            clients=list(self.connected)
        for c in clients:
            c.disconnect()
        if self.scheduler: self.scheduler.join(timeout=3)
        if self.server_thread: self.server_thread.join(timeout=3)

class StratumTCP(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address=True
    daemon_threads=True
    request_queue_size=64

    def verify_request(self, request, client_address):
        with self.pool.lock:
            return len(self.pool.connected) < int(self.pool.config['pool'].get('max_connections',64))

class MinerHandler(socketserver.BaseRequestHandler):
    def setup(self):
        self.pool=self.server.pool
        self.send_lock=threading.Lock()
        self.job_lock=threading.RLock()
        self.nonce1=secrets.token_bytes(4)
        self.difficulty=int(self.pool.config['pool'].get('share_difficulty',1024))
        self.authorized=False
        self.subscribed=False
        self.worker=''
        self.address=''
        self.accepted=self.rejected=0
        self.last_share=0
        self.jobs={}
        self.duplicates=set()
        self.request.settimeout(180)
        with self.pool.lock: self.pool.connected.add(self)

    def disconnect(self):
        try: self.request.shutdown(socket.SHUT_RDWR)
        except OSError: pass
        try: self.request.close()
        except OSError: pass

    def finish(self):
        with self.pool.lock: self.pool.connected.discard(self)

    def send(self, data):
        payload=json.dumps(data,separators=(',',':')).encode()+b'\n'
        with self.send_lock:
            self.request.sendall(payload)

    def respond(self, id, result=None, error=None):
        self.send({'id':id,'result':result,'error':error})

    def push(self,method, params):
        self.send({'id':None,'method':method,'params':params})

    def handle(self):
        buf=b''
        while not self.pool.stop.is_set():
            try: chunk=self.request.recv(4096)
            except (TimeoutError,OSError): break
            if not chunk: break
            buf+=chunk
            if len(buf)>65536: break
            while b'\n' in buf:
                line,buf=buf.split(b'\n',1)
                if not line.strip(): continue
                try:
                    data=json.loads(line)
                    self.message(data)
                except (ValueError,TypeError,KeyError,IndexError) as e:
                    try:self.respond(None,None,[20,'Invalid Stratum request',None])
                    except OSError:return
                except OSError:return

    def message(self, m):
        if not isinstance(m,dict) or not isinstance(m.get('method'),str):
            raise ValueError('Malformed Stratum')
        id=m.get('id'); method=m['method']; p=m.get('params',[])
        if not isinstance(p,list): raise ValueError('Invalid parameters')
        if method=='mining.configure':
            # Explicitly do not negotiate version rolling (our jobs pin nVersion).
            self.respond(id, {'version-rolling':False},None)
        elif method=='mining.subscribe':
            self.subscribed=True
            self.respond(id,[[['mining.set_difficulty','minipool'],['mining.notify','minipool']],self.nonce1.hex(),4],None)
        elif method=='mining.authorize':
            if not self.subscribed: return self.respond(id,False,[25,'Subscribe first',None])
            candidate=str(p[0]) if p else ''
            address=candidate.split('.')[0]
            try:bech32_script(address)
            except ValueError:
                return self.respond(id,False,[24,'Use a valid VMESH mainnet vm1 address as username',None])
            self.worker=candidate[:140]
            self.address=address
            self.authorized=True
            self.respond(id,True,None)
            self.new_job()
        elif method=='mining.submit':
            if not self.authorized: return self.respond(id,False,[24,'Not authorized',None])
            self.submit(id,p)
        elif method=='mining.extranonce.subscribe':
            self.respond(id,True,None)
        elif method=='mining.ping': self.respond(id,True,None)
        else:self.respond(id,None,[20,'Unsupported method',None])

    def new_job(self):
        with self.pool.lock: g=self.pool.template
        if not g or not self.authorized: return
        try:
            child=make_child_work(g,self.address)
            job=parent_job(child,self.nonce1,secrets.token_hex(5))
            with self.job_lock:
                self.jobs={job.id:job}
                self.duplicates.clear()
                self.push('mining.set_difficulty',[self.difficulty])
                self.push('mining.notify',job.notify(True))
        except (OSError,ValueError,KeyError,TypeError) as e:
            self.pool.log('Job creation failed: '+str(e),'error')

    def submit(self, id, p):
        try:
            if len(p)<5 or str(p[0])!=self.worker: raise ValueError('Worker mismatch')
            jobid=str(p[1]); ex2=str(p[2]); ts=str(p[3]); nonce_s=str(p[4])
            if len(ex2)!=8 or len(ts)!=8 or len(nonce_s)!=8: raise ValueError('Invalid hex field length')
            extra=bytes.fromhex(ex2)
            ntime=int(ts,16); nonce=int(nonce_s,16)
            if len(p)>=6 and int(str(p[5]),16)!=0x20000000: raise ValueError('Version rolling not supported')
            with self.job_lock:
                job=self.jobs.get(jobid)
                if not job: raise ValueError('Unknown/stale job')
                key=(jobid,ex2,ts,nonce_s)
                if key in self.duplicates: raise ValueError('Duplicate share')
                if len(self.duplicates)>=20000: raise ValueError('Job share limit reached, await next job')
                self.duplicates.add(key)
            if ntime < job.work.mintime or ntime > time.time()+7200:
                raise ValueError('Invalid block timestamp')
            with self.pool.lock:
                if (not self.pool.template or
                    self.pool.template['previousblockhash']!=job.work.previous):
                    raise ValueError('Stale chain tip')
            header, rawblock=parent_candidate(job,extra,ntime,nonce)
            hash_num=int.from_bytes(__import__('hashlib').sha256(__import__('hashlib').sha256(header).digest()).digest(),'little')
            target=min((DIFF1 // self.difficulty),2**256-1)
            if hash_num > target: raise ValueError('Low difficulty share')
            diff=DIFF1/hash_num if hash_num else float('inf')
            now=time.time()
            with self.pool.lock:
                self.accepted+=1
                self.last_share=int(now)
                self.pool.accepted+=1
                self.pool.best_share=max(self.pool.best_share,min(diff,1e30))
                self.pool.share_events.append((now,self.difficulty))
            self.respond(id,True,None)
            if hash_num <= job.work.target:
                self.pool.log(f'BLOCK CANDIDATE {job.work.height} from {self.worker}')
                self.block_candidate(job,rawblock)
        except (ValueError,TypeError,KeyError) as e:
            self.rejected+=1
            with self.pool.lock:self.pool.rejected+=1
            self.respond(id,False,[23,str(e)[:100],None])
        except Exception as e:
            self.pool.log('Share processing failure: '+str(e)[:150],'error')
            self.respond(id,False,[20,'Internal share verification error',None])

    def block_candidate(self,job,rawblock):
        try:
            if self.pool.rpc.call('getbestblockhash')!=job.work.previous:
                self.pool.log('Candidate stale: VMESH network tip changed','warning')
                return
            # Ensure the same job and miner address are paid by the pre-built immutable child coinbase.
            result=self.pool.rpc.call('submitblock',rawblock.hex())
            if result is not None:
                self.pool.log(f'VMESH submitblock rejected: {result}','warning')
                return
            actual=self.pool.rpc.call('getblockhash',job.work.height)
            if actual.lower()!=job.work.child_hash.lower():
                self.pool.log('VMESH block submitted but not on active chain; do not record a confirmed find','warning')
                return
            found={'time':int(time.time()),'height':job.work.height,
                   'address':job.work.payout,'miner_reward_sats':job.work.reward,
                   'developer_fee_sats':job.work.fee,'child_hash':job.work.child_hash}
            with self.pool.lock:
                self.pool.blocks+=1
                self.pool.finds.appendleft(found)
                self.pool.template=None
                if self.pool.audit_file:
                    try:
                        self.pool.audit_file.parent.mkdir(parents=True,exist_ok=True)
                        with self.pool.audit_file.open('a',encoding='utf-8') as audit:
                            audit.write(json.dumps(found,separators=(',',':'))+'\n')
                    except OSError as error:
                        self.pool.log('Block accepted but writing local audit log failed: '+str(error),'warning')
            self.pool.log(f'VMESH block confirmed on active chain at height {job.work.height}, payout {job.work.payout}')
        except Exception as e:
            self.pool.log('VMESH block submission failed: '+str(e)[:180],'error')
