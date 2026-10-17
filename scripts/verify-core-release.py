"""Windows CI smoke test: download real pinned VMESH Core and execute --version.

No blockchain sync and no RPC port are started. This verifies that
first-run users get a runnable official package after checksum checks.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from minipool.node_installer import install_windows_core, CORE_VERSION


def main():
    if sys.platform != 'win32':
        print('Windows-only official Core smoke test: skipped')
        return
    with tempfile.TemporaryDirectory(prefix='vmesh-core-ci-') as folder:
        binary=install_windows_core(Path(folder)/'core',
            progress=lambda stage,count,total: print(stage, f'{count}/{total}' if total else ''))
        if not binary.exists():
            raise RuntimeError('Installer did not provide a node executable')
        proc=subprocess.run([str(binary),'-version'],text=True,capture_output=True,timeout=35)
        print((proc.stdout or proc.stderr)[:900])
        if proc.returncode!=0:
            raise RuntimeError(f'Official VargaMesh Core {CORE_VERSION} failed to start ({proc.returncode}).')


if __name__=='__main__':
    main()
