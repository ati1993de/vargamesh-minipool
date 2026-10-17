"""Local-only authenticated VargaMesh Core JSON-RPC, no third-party dependencies."""
import base64
import json
import pathlib
import urllib.request

class RPCError(RuntimeError):
    pass

class VMeshRPC:
    def __init__(self, cookie_path, port=29667, timeout=12):
        self.cookie_path = pathlib.Path(cookie_path).expanduser()
        self.port = int(port)
        self.timeout = timeout
        if not 1 <= self.port <= 65535: raise ValueError('invalid RPC port')

    def call(self, method, *params):
        try:
            auth = self.cookie_path.read_text(encoding='utf-8').strip()
            if not auth.startswith('__cookie__:'): raise RPCError('Invalid node .cookie; select correct VargaMesh data directory')
            payload = json.dumps({'jsonrpc':'1.0','id':'minipool','method':method,'params':list(params)}).encode()
            req = urllib.request.Request(f'http://127.0.0.1:{self.port}/', data=payload,
                headers={'Content-Type':'application/json', 'Authorization':'Basic '+base64.b64encode(auth.encode()).decode()})
            try:
                with urllib.request.urlopen(req,timeout=self.timeout) as response:
                    obj = json.load(response)
            except urllib.error.HTTPError as err:
                # Bitcoin Core may return a JSON-RPC error with HTTP 500.
                try: obj = json.loads(err.read())
                except Exception: raise RPCError(f'Node HTTP {err.code}') from err
            if obj.get('error'): raise RPCError(str(obj['error']))
            return obj['result']
        except (OSError, ValueError, KeyError) as e:
            raise RPCError(str(e)) from e

    def chain_info(self):
        info = self.call('getblockchaininfo')
        if info.get('chain') not in ('main','mainnet'):
            raise RPCError('Refusing to mine: mainnet is required')
        if info.get('initialblockdownload',True):
            raise RPCError('VargaMesh full node is still synchronizing (IBD)')
        return info

    def template(self):
        self.chain_info()
        return self.call('getblocktemplate', {'rules':['segwit']})
