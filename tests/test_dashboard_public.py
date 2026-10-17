"""Public web dashboard allowlist tests; no external network is used."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import urllib.error
import urllib.request

from minipool.dashboard import start_dashboard

class DummyPool:
    def status(self):
        return {"name":"VargaMesh MiniPool","mode":"VMESH-only SOLO",
                "workers":1,"fee_percent":1,"node_ready":False}

class DashboardPublicTests(unittest.TestCase):
    def open_dashboard(self, allowed_hosts):
        self.tmp=tempfile.TemporaryDirectory(prefix='vmesh-dashboard-test-')
        self.addCleanup(self.tmp.cleanup)
        Path(self.tmp.name,'index.html').write_text('hello VMESH','utf-8')
        with mock.patch.dict(os.environ,{"MINIPOOL_DASHBOARD_BIND":"127.0.0.1",
            "MINIPOOL_DASHBOARD_ALLOWED_HOSTS":allowed_hosts}):
            self.server=start_dashboard(DummyPool(),0,self.tmp.name)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        return self.server.server_address[1]

    @staticmethod
    def request(port, host):
        req=urllib.request.Request(f'http://127.0.0.1:{port}/api/status',
                headers={"Host":host})
        with urllib.request.urlopen(req,timeout=3) as reply:
            return json.load(reply)

    def test_public_ip_and_domain_allowed_only_if_configured(self):
        p=self.open_dashboard('pool.example.com,203.0.113.10')
        self.assertEqual(self.request(p,'pool.example.com')['name'],'VargaMesh MiniPool')
        self.assertEqual(self.request(p,'203.0.113.10:8686')['workers'],1)
        self.assertEqual(self.request(p,'127.0.0.1')['fee_percent'],1)
        for name in ['203.0.113.11:8686','attacker.example.com','0.0.0.0']:
            with self.subTest(name=name),self.assertRaises(urllib.error.HTTPError) as ctx:
                self.request(p,name)
            self.assertEqual(ctx.exception.code,403)

    def test_empty_allowlist_never_permits_public_host(self):
        p=self.open_dashboard('')
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.request(p,'203.0.113.10')
        self.assertEqual(ctx.exception.code,403)

if __name__=='__main__':
    unittest.main()
