"""Offline tests for the official one-click Core installer."""
import hashlib
import io
import tempfile
from pathlib import Path
import unittest
from unittest import mock
import zipfile

from minipool import node_installer as installer

class CoreInstallerTests(unittest.TestCase):
    def test_checksum_manifest_validation(self):
        digest='a'*64
        self.assertEqual(installer.expected_checksum(f'{digest}  {installer.ASSET_NAME}\n'),digest)
        with self.assertRaises(installer.InstallError):
            installer.expected_checksum(f'{digest}  invalid.zip\n')
        with self.assertRaises(installer.InstallError):
            installer.expected_checksum(f'{digest}  {installer.ASSET_NAME}\n{digest}  {installer.ASSET_NAME}\n')

    def test_archive_hash_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'archive.zip'
            p.write_bytes(b'archive')
            installer._verify(p,hashlib.sha256(b'archive').hexdigest())
            with self.assertRaises(installer.InstallError):
                installer._verify(p,'0'*64)

    def test_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder)
            for name in ('../out.txt','/root/out.txt','C:/evil.exe'):
                with zipfile.ZipFile(base/'bad.zip','w') as archive:
                    archive.writestr(name,'bad')
                with self.subTest(name=name),self.assertRaises(installer.InstallError):
                    installer._unpack_verified(base/'bad.zip',base/'unpacked')

    def test_valid_installer_transaction_and_reuse(self):
        payload=io.BytesIO()
        with zipfile.ZipFile(payload,'w') as archive:
            archive.writestr('bin/vargameshd.exe',b'fake official fixture')
            archive.writestr('bin/vargamesh-cli.exe',b'fake cli')
        binary=payload.getvalue()
        digest=hashlib.sha256(binary).hexdigest()
        manifest=f'{digest}  {installer.ASSET_NAME}\n'.encode()
        def fake_download(url,path,limit,progress=None):
            if url.endswith('SHA256SUMS'):
                path.write_bytes(manifest)
            else:
                path.write_bytes(binary)
                if progress:progress('Downloading',len(binary),len(binary))
        with tempfile.TemporaryDirectory() as folder:
            with mock.patch.object(installer,'_supported_windows',return_value=True), \
                 mock.patch.object(installer,'CORE_ARCHIVE_SHA256',digest), \
                 mock.patch.object(installer,'SHA256SUMS_SHA256',hashlib.sha256(manifest).hexdigest()), \
                 mock.patch.object(installer,'_download',side_effect=fake_download):
                result=installer.install_windows_core(Path(folder)/'core')
                self.assertEqual(result.read_bytes(),b'fake official fixture')
                self.assertEqual(installer.install_windows_core(Path(folder)/'core'),result)

    def test_bad_checksum_does_not_publish_binary(self):
        payload=io.BytesIO()
        with zipfile.ZipFile(payload,'w') as archive:
            archive.writestr('bin/vargameshd.exe',b'invalid test fixture')
        manifest=f'{"0"*64}  {installer.ASSET_NAME}\n'.encode()
        def fake_download(url,path,limit,progress=None):
            path.write_bytes(manifest if url.endswith('SHA256SUMS') else payload.getvalue())
        with tempfile.TemporaryDirectory() as folder:
            with mock.patch.object(installer,'_supported_windows',return_value=True), \
                 mock.patch.object(installer,'SHA256SUMS_SHA256',hashlib.sha256(manifest).hexdigest()), \
                 mock.patch.object(installer,'_download',side_effect=fake_download):
                with self.assertRaises(installer.InstallError):
                    installer.install_windows_core(Path(folder)/'core')
                self.assertFalse((Path(folder)/'core'/installer.CORE_VERSION).exists())

if __name__=='__main__':
    unittest.main()
