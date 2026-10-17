"""Standalone dashboard smoke test with a mocked VMESH RPC endpoint.

Does not mine cryptocurrency, contact the Internet or touch a real node.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import json
import socket
import tempfile
import urllib.request
from pathlib import Path

from minipool.dashboard import start_dashboard
from minipool.service import PoolState

conf={'node':{'cookie_path':'unused','rpc_port':29667},
      'pool':{'bind':'127.0.0.1','stratum_port':0,'dashboard_port':0,'share_difficulty':1024}}
pool=PoolState(conf)
with socket.socket() as sock:
    sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
webroot=Path(__file__).resolve().parent.parent/'web'
server=start_dashboard(pool,port,webroot)
try:
    for path in ('/','/app.js','/style.css','/api/status'):
        with urllib.request.urlopen(f'http://127.0.0.1:{port}{path}',timeout=2) as response:
            assert response.status==200,path
            content=response.read()
            assert content,path
            if path=='/api/status':
                data=json.loads(content)
                assert data['fee_percent']==1
                assert data['mode']=='VMESH-only SOLO'
    print('Dashboard smoke test passed: HTML/CSS/JS/API all served on local loopback')
finally:
    server.shutdown();server.server_close()
