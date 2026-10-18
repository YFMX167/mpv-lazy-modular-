#!/usr/bin/env python3
"""Isolated, transactional mpv configuration manager (Python >= 3.12)."""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
import zipfile

SOURCE = Path(__file__).resolve().parent

def digest(data):
    return hashlib.sha256(data).hexdigest()

def manifest(root):
    return {p.relative_to(root).as_posix(): digest(p.read_bytes())
            for p in sorted(root.rglob('*')) if p.is_file() and p.name != 'manifest.json'}

def release_id():
    data = (SOURCE / 'dependencies.lock.json').read_bytes()
    for p in sorted((SOURCE / 'config').rglob('*')):
        if p.is_file():
            data += str(p.relative_to(SOURCE)).encode() + p.read_bytes()
    data += (SOURCE / 'lazy.py').read_bytes()
    return (SOURCE / 'VERSION').read_text().strip() + '-' + digest(data)[:12]

def verify(root):
    if manifest(root) != json.loads((root / 'manifest.json').read_text()):
        raise RuntimeError('Release modified or incomplete: ' + str(root))

def point(root, name, target):
    link = root / name
    if link.exists() and not link.is_symlink():
        raise RuntimeError('Refusing to replace non-symlink: ' + str(link))
    temporary = root / ('.' + name + '-' + str(os.getpid()))
    temporary.symlink_to(target)
    os.replace(temporary, link)

def backup(root):
    current = root / 'current'
    if not current.is_symlink():
        return None
    target = current.resolve()
    if target.parent != (root / 'releases').resolve():
        raise RuntimeError('Current release escapes managed directory')
    folder = root / 'backups'
    folder.mkdir(exist_ok=True)
    dest = folder / (time.strftime('%Y%m%d-%H%M%S') + '-' + str(time.time_ns()) + '.tar.gz')
    with tarfile.open(dest, 'w:gz') as archive:
        archive.add(target, arcname=target.name)
    return dest

def fetch(asset, cache):
    dest = cache / asset['sha256']
    if dest.exists() and digest(dest.read_bytes()) == asset['sha256']:
        return dest
    if not asset['url'].startswith(('https://github.com/', 'https://raw.githubusercontent.com/', 'https://codeload.github.com/')):
        raise RuntimeError('Unexpected download host')
    with urllib.request.urlopen(asset['url'], timeout=90) as response:
        data = response.read(64 * 1024 * 1024 + 1)
    if len(data) > 64 * 1024 * 1024 or digest(data) != asset['sha256']:
        raise RuntimeError('Download checksum/size mismatch: ' + asset['name'])
    tmp = dest.with_suffix('.part')
    tmp.write_bytes(data)
    os.replace(tmp, dest)
    return dest

def safe_destination(root, relative):
    path = root / relative
    if Path(relative).is_absolute() or not path.resolve().is_relative_to(root.resolve()):
        raise RuntimeError('Unsafe archive/asset path')
    return path

def install(root, cache):
    check = subprocess.run(['mpv', '--version'], capture_output=True, text=True, check=True).stdout
    version = re.search(r'mpv v?(\d+)\.(\d+)', check)
    if not version or tuple(map(int, version.groups())) < (0, 41):
        raise RuntimeError('mpv >= 0.41 required')
    cache.mkdir(parents=True, exist_ok=True)
    releases = root / 'releases'
    releases.mkdir(exist_ok=True)
    rid = release_id()
    destination = releases / rid
    if not destination.exists():
        with tempfile.TemporaryDirectory(prefix='.stage-', dir=root) as directory:
            stage = Path(directory)
            shutil.copytree(SOURCE / 'config', stage, dirs_exist_ok=True)
            for asset in json.loads((SOURCE / 'dependencies.lock.json').read_text())['assets']:
                archive = fetch(asset, cache)
                if asset['kind'] == 'file':
                    path = safe_destination(stage, asset['dest'])
                    path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(archive, path)
                elif asset['kind'] == 'zip':
                    with zipfile.ZipFile(archive) as z:
                        if sum(i.file_size for i in z.infolist()) > 128 * 1024 * 1024:
                            raise RuntimeError('Oversized archive')
                        for entry in z.infolist():
                            path = safe_destination(stage, entry.filename)
                            # Exclude bundled executables; basic local playback needs no helper.
                            if '/bin/' in entry.filename or entry.is_dir():
                                continue
                            if (entry.external_attr >> 16) & 0o170000 == 0o120000:
                                raise RuntimeError('Archive symlinks are forbidden')
                            path.parent.mkdir(parents=True, exist_ok=True)
                            path.write_bytes(z.read(entry))
                else:
                    raise RuntimeError('Unknown asset kind')
            (stage / 'manifest.json').write_text(json.dumps(manifest(stage), indent=2))
            os.rename(stage, destination)
    verify(destination)
    current = root / 'current'
    if current.is_symlink() and current.resolve() == destination:
        print('Already installed:', rid)
        return
    if current.is_symlink():
        saved = backup(root)
        print('Backup:', saved)
        point(root, 'previous', current.readlink())
    point(root, 'current', Path('releases') / rid)
    print('Activated:', rid)

def doctor(root):
    # Deliberately no environment dump, media filenames, EDID serials, or logs.
    result = {'session': os.environ.get('XDG_SESSION_TYPE', 'unknown'),
              'commands': {c: bool(shutil.which(c)) for c in ['mpv','ffmpeg','vulkaninfo','kscreen-doctor']}}
    if shutil.which('mpv'):
        result['mpv'] = subprocess.run(['mpv','--version'], capture_output=True, text=True).stdout.splitlines()[:3]
    if (root / 'current').is_symlink():
        verify((root / 'current').resolve())
        result['release'] = (root / 'current').resolve().name
        result['integrity'] = 'OK'
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result['commands']['mpv'] else 1

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=SOURCE / 'runtime')
    parser.add_argument('--cache', type=Path, default=SOURCE / '.cache')
    parser.add_argument('command', choices=['install','update','rollback','backup','doctor','play'])
    parser.add_argument('mpv_args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == 'play':
        current = root / 'current'
        verify(current.resolve())
        extra = args.mpv_args
        if extra[:1] == ['--']:
            extra = extra[1:]
        os.execvp('mpv', ['mpv', '--config-dir=' + str(current.resolve()), *extra])
    if args.command == 'doctor':
        return doctor(root)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (root / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if args.command in ['install','update']:
            install(root, args.cache.resolve())
        elif args.command == 'backup':
            print(backup(root) or 'No installed release')
        elif args.command == 'rollback':
            previous = root / 'previous'
            current = root / 'current'
            if not previous.is_symlink() or not current.is_symlink():
                raise RuntimeError('No previous release')
            target = previous.resolve()
            if target.parent != (root / 'releases').resolve():
                raise RuntimeError('Invalid rollback target')
            verify(target)
            backup(root)
            old = current.readlink()
            point(root, 'current', previous.readlink())
            point(root, 'previous', old)
            print('Rolled back:', target.name)
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print('ERROR:', error, file=sys.stderr)
        sys.exit(1)
