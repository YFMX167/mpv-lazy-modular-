#!/usr/bin/env python3
"""Optional offline SDR frame interpolation. Never loaded by mpv."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import time

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--binary', required=True, type=Path)
p.add_argument('--sha256', required=True, help='Expected SHA-256 of your verified binary')
p.add_argument('--model', required=True, type=Path)
p.add_argument('--input', required=True, type=Path, help='SDR PNG frame directory')
p.add_argument('--output', required=True, type=Path, help='New empty output directory')
p.add_argument('--frames', required=True, type=int)
p.add_argument('--gpu', type=int, default=0)
a = p.parse_args()
if hashlib.sha256(a.binary.read_bytes()).hexdigest() != a.sha256.lower():
    p.error('Binary checksum mismatch')
if not a.model.is_dir() or not a.input.is_dir() or a.frames < 2:
    p.error('Valid model/input directories and frames >= 2 required')
if a.output.exists():
    p.error('Output must not exist; refusing overwrite')
if len(list(a.input.glob('*.png'))) < 2:
    p.error('At least two SDR PNG frames are required')
a.output.mkdir(parents=True)
start = time.monotonic()
subprocess.run([str(a.binary.resolve()), '-i',str(a.input.resolve()), '-o',str(a.output.resolve()),
                '-m',str(a.model.resolve()), '-n',str(a.frames), '-g',str(a.gpu), '-f','%08d.png'], check=True)
elapsed = time.monotonic()-start
count = len(list(a.output.glob('*.png')))
if count != a.frames:
    raise SystemExit(f'Incomplete output: {count}/{a.frames}; retained for diagnosis')
print(f'{count} frames, {elapsed:.2f}s, {count/elapsed:.2f} output frames/s (offline measurement)')
