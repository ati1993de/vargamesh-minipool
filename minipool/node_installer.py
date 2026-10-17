"""Verified, opt-in official VargaMesh Core Windows installer (stdlib only)."""
import hashlib
import os
import pathlib
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import tempfile
import urllib.request
import zipfile

CORE_VERSION = 'v0.2.0'
ASSET_NAME = 'vargamesh-core-0.2.0-windows-x86_64.zip'
CORE_ARCHIVE_SHA256 = '6670b11d9f7bfb86347d9c4fa02238c5f2c1c0e8135793d47c62c5656d058ec3'
SHA256SUMS_SHA256 = 'f84414804092f6b89642bd52381f77eb53589a3cdf23e00df4a9344803f234dd'
RELEASE_BASE = f'https://github.com/ati1993de/vargamesh-core/releases/download/{CORE_VERSION}/'
MAX_ARCHIVE_BYTES = 120 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 450 * 1024 * 1024

class InstallError(RuntimeError):
    pass

def expected_checksum(sums_text, filename=ASSET_NAME):
    matches=[]
    for line in sums_text.splitlines():
        fields=line.strip().split(maxsplit=1)
        if len(fields)!=2:
            continue
        digest,name=fields
        name=name.lstrip('*').removeprefix('./')
        if name==filename and len(digest)==64 and all(c in '0123456789abcdefABCDEF' for c in digest):
            matches.append(digest.lower())
    if len(matches)!=1:
        raise InstallError('Official SHA256SUMS has no unique Windows Core archive entry.')
    return matches[0]

def _download(url, path, maximum, progress=None):
    req=urllib.request.Request(url,headers={'User-Agent':'VargaMesh-MiniPool/0.2'})
    with urllib.request.urlopen(req,timeout=40) as response,path.open('wb') as f:
        length=response.headers.get('Content-Length')
        expected=int(length) if length and length.isdecimal() else None
        if expected is not None and expected>maximum:
            raise InstallError('Official download exceeds the safety size limit.')
        count=0
        while True:
            part=response.read(128*1024)
            if not part:break
            count+=len(part)
            if count>maximum:raise InstallError('Official download exceeds the safety size limit.')
            f.write(part)
            if progress:progress('Downloading official VargaMesh Core',count,expected)
        if not count or (expected is not None and count!=expected):
            raise InstallError('Incomplete or empty Core download.')

def _verify(file_path,digest):
    sha=hashlib.sha256()
    with file_path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            sha.update(chunk)
    if sha.hexdigest()!=digest:
        raise InstallError('SHA-256 checksum mismatch; Core installation stopped.')

def _unpack_verified(zip_path,dest):
    with zipfile.ZipFile(zip_path) as archive:
        infos=archive.infolist()
        if not infos or len(infos)>1500:raise InstallError('Unexpected archive entry count.')
        used=set()
        total=0
        for info in infos:
            name=info.filename.replace('\\','/')
            path=PurePosixPath(name)
            if path.is_absolute() or not path.parts or any(v in ('.','..') for v in path.parts) or ':' in name:
                raise InstallError('Unsafe path inside the official Core archive.')
            key=str(path).casefold().rstrip('/')
            if key in used:raise InstallError('Duplicate Core archive filename.')
            used.add(key)
            if stat.S_IFMT(info.external_attr>>16)==stat.S_IFLNK:
                raise InstallError('Archive symlinks are not permitted.')
            total+=info.file_size
            if total>MAX_UNCOMPRESSED_BYTES:raise InstallError('Core archive is unexpectedly large.')
        for info in infos:
            name=info.filename.replace('\\','/')
            target=dest.joinpath(*PurePosixPath(name).parts)
            if info.is_dir():target.mkdir(parents=True,exist_ok=True)
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                with archive.open(info) as src,target.open('wb') as out:
                    shutil.copyfileobj(src,out,length=1024*1024)
    matches=list(dest.rglob('vargameshd.exe'))
    if len(matches)!=1:raise InstallError('Core archive is missing a unique vargameshd.exe.')
    return matches[0]

def _supported_windows():
    return sys.platform=='win32' and os.environ.get('PROCESSOR_ARCHITECTURE','').lower() in ('amd64','arm64')

def install_windows_core(install_root,progress=None):
    """Install official pinned Core without modifying any existing installation."""
    if not _supported_windows():
        raise InstallError('One-click installation requires Windows x64 or compatible Windows ARM64.')
    base=Path(install_root).expanduser()
    target=base/CORE_VERSION
    existing=list(target.rglob('vargameshd.exe')) if target.exists() else []
    if len(existing)==1 and existing[0].is_file():
        return existing[0]
    if target.exists():
        raise InstallError('Incomplete old Core installation detected. Rename it and retry: '+str(target))
    base.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='vmesh-core-',dir=base) as temp:
        stage=Path(temp)
        sums=stage/'SHA256SUMS'
        archive=stage/ASSET_NAME
        if progress:progress('Fetching official checksum manifest',0,None)
        _download(RELEASE_BASE+'SHA256SUMS',sums,128*1024)
        _verify(sums,SHA256SUMS_SHA256)
        expected=expected_checksum(sums.read_text(encoding='utf-8'))
        if expected!=CORE_ARCHIVE_SHA256:
            raise InstallError('Official manifest does not match pinned Core v0.2.0 checksum.')
        _download(RELEASE_BASE+ASSET_NAME,archive,MAX_ARCHIVE_BYTES,progress)
        if progress:progress('Verifying Core archive SHA-256',0,None)
        _verify(archive,expected)
        unpack=stage/'unpacked'
        unpack.mkdir()
        if progress:progress('Installing verified Core',0,None)
        exe=_unpack_verified(archive,unpack)
        rel=exe.relative_to(unpack)
        (unpack/'MINIPOOL-INSTALL-MANIFEST.txt').write_text(
            f'Version: {CORE_VERSION}\nArchive: {ASSET_NAME}\nSHA256: {expected}\nSource: {RELEASE_BASE}\n',
            encoding='utf-8')
        unpack.replace(target)
        if progress:progress('VargaMesh Core installed',1,1)
        return target/rel
