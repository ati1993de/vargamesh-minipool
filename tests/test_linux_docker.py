"""Offline regression tests for the verified Docker Linux Core installer."""
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest import mock
import hashlib
from scripts import install_linux_core as core

class LinuxInstallerTests(unittest.TestCase):
    def archive(self,members):
        buf=io.BytesIO()
        with tarfile.open(fileobj=buf,mode='w:gz') as tar:
            for name,data in members:
                i=tarfile.TarInfo(name)
                i.size=len(data)
                tar.addfile(i,io.BytesIO(data))
        return buf.getvalue()

    def test_manifest_checksum_parser(self):
        digest='a'*64
        self.assertEqual(core.manifest_digest(f'{digest}  {core.ARCHIVE}\n'),digest)
        with self.assertRaises(core.CoreInstallError):
            core.manifest_digest(f'{digest}  wrong.tar.gz\n')
        with self.assertRaises(core.CoreInstallError):
            core.manifest_digest(f'{digest}  {core.ARCHIVE}\n{digest}  {core.ARCHIVE}\n')

    def test_extraction_and_executable_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)
            archive=base/'core.tar.gz'
            archive.write_bytes(self.archive([
                ('core/bin/vargameshd',b'fake node binary'),
                ('core/bin/vargamesh-cli',b'fake cli binary')
            ]))
            out=core.extract_core(archive,base/'target')
            self.assertEqual(out.read_bytes(),b'fake node binary')
            self.assertTrue(out.stat().st_mode & 0o111)

    def test_reject_tar_traversal_and_missing_daemon(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)
            for ix,entries in enumerate([
                [('../outside.txt',b'bad'),('core/bin/vargameshd',b'ok')],
                [('/tmp/outside.txt',b'bad'),('core/bin/vargameshd',b'ok')],
                [('core/bin/vargamesh-cli',b'only cli')]
            ]):
                archive=base/f'{ix}.tar.gz'
                archive.write_bytes(self.archive(entries))
                with self.subTest(index=ix),self.assertRaises(core.CoreInstallError):
                    core.extract_core(archive,base/f'dest{ix}')
            self.assertFalse((base/'outside.txt').exists())

    def test_verified_transaction_download_fixture(self):
        data=self.archive([('core/bin/vargameshd',b'verified fake exe')])
        digest=hashlib.sha256(data).hexdigest()
        manifest=f'{digest}  {core.ARCHIVE}\n'.encode()
        def fake_download(url,path,limit=core.MAX_DOWNLOAD):
            Path(path).write_bytes(manifest if url.endswith('SHA256SUMS') else data)
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(core,'download',side_effect=fake_download), \
                mock.patch.object(core,'MANIFEST_SHA256',hashlib.sha256(manifest).hexdigest()), \
                mock.patch.object(core,'ARCHIVE_SHA256',digest):
                self.assertEqual(core.install(Path(directory)/'core').read_bytes(),b'verified fake exe')
                with self.assertRaises(core.CoreInstallError):
                    core.install(Path(directory)/'core')

if __name__=='__main__':
    unittest.main()
