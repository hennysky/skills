#!/usr/bin/env python3
"""Package the full independent Skill; optional install uses a verified copy."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAME = 'visual-planning'
EXCLUDED = {'.git', 'node_modules', 'output', 'dist', '__pycache__', '.visualplan', '.DS_Store'}


def package(out=None, install=None):
    target = Path(out or ROOT / 'dist').resolve()
    if target == ROOT or ROOT.is_relative_to(target):
        raise ValueError('Package output must not be the source root or its ancestor')
    target.mkdir(parents=True, exist_ok=True)
    version = json.loads((ROOT / 'package.json').read_text())['version']
    files = sorted(p for p in ROOT.rglob('*') if p.is_file() and not any(x in EXCLUDED for x in p.relative_to(ROOT).parts) and not p.is_relative_to(target))
    if any(p.is_symlink() for p in files):
        raise ValueError('Skill package cannot depend on file symlinks')
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    archive = target / f'{NAME}-{version}.zip'
    with tempfile.NamedTemporaryFile(dir=target, suffix='.zip', delete=False) as tmp:
        temporary = Path(tmp.name)
    try:
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            for p in files:
                z.write(p, NAME + '/' + str(p.relative_to(ROOT)))
            z.writestr(NAME + '/distribution-manifest.json', json.dumps({'name': NAME, 'version': version, 'files': hashes}, ensure_ascii=False, indent=2) + '\n')
        temporary.replace(archive)
    finally:
        temporary.unlink(missing_ok=True)
    installed = None
    with tempfile.TemporaryDirectory(prefix='visual-skill-package-') as directory:
        stage = Path(directory)
        with zipfile.ZipFile(archive) as z:
            for entry in z.infolist():
                path = Path(entry.filename)
                if path.is_absolute() or '..' in path.parts:
                    raise ValueError('Unsafe package entry')
            z.extractall(stage)
        unpacked = stage / NAME
        for name, digest in hashes.items():
            if hashlib.sha256((unpacked / name).read_bytes()).hexdigest() != digest:
                raise ValueError('Package checksum mismatch: ' + name)
        if install:
            installed = Path(install).expanduser().resolve()
            if installed.exists():
                raise ValueError('Refusing to overwrite existing Skill: ' + str(installed))
            installed.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(unpacked, installed)
    receipt = {'name': NAME, 'version': version, 'archive': str(archive), 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'files': len(hashes), 'installed': str(installed) if installed else None}
    (target / 'package-receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out')
    parser.add_argument('--install')
    args = parser.parse_args()
    print(json.dumps(package(args.out, args.install), ensure_ascii=False, indent=2))
