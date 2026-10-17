#!/usr/bin/env python3
"""GitHub CI: assert a running Linux Docker container serves VMESH MiniPool."""
import json
import time
import urllib.error
import urllib.request

def run():
    url="http://127.0.0.1:8686/api/status"
    last=None
    for _ in range(70):
        try:
            with urllib.request.urlopen(url,timeout=3) as res:
                obj=json.load(res)
            assert obj["name"]=="VargaMesh MiniPool"
            assert obj["mode"]=="VMESH-only SOLO"
            assert obj["fee_percent"]==1
            assert obj["network"]=="mainnet"
            assert obj["blocks"]>=0
            print("Docker integration smoke passed:",{
                "name":obj["name"],"mode":obj["mode"],
                "fee":obj["fee_percent"],"sync_progress":obj.get("sync_progress"),
                "node_error":obj.get("node_error")
            })
            return
        except (OSError,ValueError,AssertionError) as error:
            last=error
            time.sleep(1)
    raise RuntimeError(f"No working MiniPool Docker dashboard within 70s: {last}")

if __name__=="__main__":
    run()
