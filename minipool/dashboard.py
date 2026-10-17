"""Local read-only dashboard. No external libraries or network calls."""
import json
import pathlib
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

class Dashboard(ThreadingHTTPServer):
    daemon_threads=True
    allow_reuse_address=True


def start_dashboard(pool,port,webroot):
    root=pathlib.Path(webroot).resolve()
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(root),**kwargs)
        def end_headers(self):
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'")
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Cache-Control','no-store')
            self.send_header('Referrer-Policy','no-referrer')
            super().end_headers()
        def do_GET(self):
            if self.headers.get('Host','').split(':')[0].lower() not in ('localhost','127.0.0.1','[::1]'):
                self.send_error(403); return
            if self.path.split('?')[0]=='/api/status':
                b=json.dumps(pool.status()).encode()
                self.send_response(200)
                self.send_header('Content-Type','application/json; charset=utf-8')
                self.send_header('Content-Length',str(len(b)))
                self.end_headers();self.wfile.write(b);return
            if self.path.split('?')[0] not in ('/','/index.html','/app.js','/style.css'):
                self.send_error(404); return
            return super().do_GET()
        def log_message(self,*args): pass
    server=Dashboard(('127.0.0.1',int(port)),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True,name='Dashboard')
    thread.start()
    return server
