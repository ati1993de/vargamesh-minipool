#!/usr/bin/env python3
"""Install pinned official VargaMesh Core for Linux x86_64 (stdlib-only)."""
import argparse
import hashlib
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile
import urllib.request

VERSION="v0.2.0"
ARCHIVE="vargamesh-core-0.2.0-linux-x86_64.tar.gz"
ARCHIVE_SHA256="d24087cf3dd73d6f113076fd751446041a08aaa2820bb9d409f5e4ea3696dd72"
MANIFEST_SHA256="f84414804092f6b89642bd52381f77eb53589a3cdf23e00df4a9344803f234dd"
BASE_URL=f"https://github.com/ati1993de/vargamesh-core/releases/download/{VERSION}/"
MAX_DOWNLOAD=120*1024*1024
MAX_UNPACKED=480*1024*1024

class CoreInstallError(RuntimeError):
    pass

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def download(url,path,limit=MAX_DOWNLOAD):
    request=urllib.request.Request(url,headers={"User-Agent":"VargaMesh-MiniPool-Docker/0.3"})
    with urllib.request.urlopen(request,timeout=50) as response,Path(path).open("wb") as f:
        size=response.headers.get("Content-Length")
        if size and size.isdecimal() and int(size)>limit:raise CoreInstallError("Oversized download")
        count=0
        while True:
            part=response.read(131072)
            if not part:break
            count+=len(part)
            if count>limit:raise CoreInstallError("Oversized download")
            f.write(part)
        if not count or (size and size.isdecimal() and count!=int(size)):raise CoreInstallError("Incomplete Core download")

def verify(path,expected):
    if sha256(path)!=expected:raise CoreInstallError("SHA256 mismatch: "+Path(path).name)

def manifest_digest(text,name=ARCHIVE):
    found=[]
    for line in text.splitlines():
        part=line.strip().split(maxsplit=1)
        if len(part)!=2:continue
        if part[1].removeprefix("*").removeprefix("./")!=name:continue
        h=part[0].lower()
        if len(h)==64 and all(x in "0123456789abcdef" for x in h):found.append(h)
    if len(found)!=1:raise CoreInstallError("Manifest does not contain exactly one Linux archive entry")
    return found[0]

def extract_core(archive,dest):
    dest=Path(dest)
    dest.mkdir(parents=True,exist_ok=True)
    seen=set()
    found={}
    size=0
    with tarfile.open(archive,"r:gz") as tf:
        members=tf.getmembers()
        if len(members)>2000:raise CoreInstallError("Too many tar members")
        for m in members:
            p=PurePosixPath(m.name)
            if (not p.parts or p.is_absolute() or any(x in (".","..") for x in p.parts)
                or "\\" in m.name or ":" in m.name or not (m.isdir() or m.isfile())):
                raise CoreInstallError("Unsafe tar member: "+m.name)
            key=str(p).casefold().rstrip("/")
            if key in seen:raise CoreInstallError("Duplicate tar path")
            seen.add(key)
            if m.isfile():
                size+=m.size
                if size>MAX_UNPACKED:raise CoreInstallError("Unpacked content too large")
                if p.name in ("vargameshd","vargamesh-cli"):
                    if p.name in found:raise CoreInstallError("Duplicate executable")
                    found[p.name]=m
        if "vargameshd" not in found:raise CoreInstallError("Core archive has no vargameshd")
        bindir=dest/"bin"
        bindir.mkdir(parents=True,exist_ok=True)
        for name,member in found.items():
            src=tf.extractfile(member)
            if src is None:raise CoreInstallError("Cannot read binary")
            output=bindir/name
            with src,output.open("wb") as out:shutil.copyfileobj(src,out,1024*1024)
            output.chmod(0o755)
    return bindir/"vargameshd"

def install(dest):
    dest=Path(dest)
    if dest.exists() and any(dest.iterdir()):raise CoreInstallError("Refusing to overwrite Core installation")
    dest.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vmesh-official-core-") as temp:
        base=Path(temp)
        manifest=base/"SHA256SUMS"
        archive=base/ARCHIVE
        download(BASE_URL+"SHA256SUMS",manifest,128*1024)
        verify(manifest,MANIFEST_SHA256)
        h=manifest_digest(manifest.read_text("utf-8"))
        if h!=ARCHIVE_SHA256:raise CoreInstallError("Official manifest differs from pinned Linux Core checksum")
        download(BASE_URL+ARCHIVE,archive)
        verify(archive,h)
        result=extract_core(archive,dest)
        (dest/"CORE-SHA256.txt").write_text(f"{VERSION}\n{h}  {ARCHIVE}\n","utf-8")
        return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dest",required=True)
    result=install(p.parse_args().dest)
    print("Verified official VargaMesh Core executable:",result)
