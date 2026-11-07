#!/usr/bin/env python3
"""Prepare external storage without executing the .env as shell code."""
import argparse
import os
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--env', default='.env')
args = parser.parse_args()
values = {}
for raw in Path(args.env).read_text().splitlines():
    line = raw.strip()
    if not line or line.startswith('#'):
        continue
    key, sep, value = line.partition('=')
    if not sep:
        raise SystemExit('Invalid .env line')
    values[key.strip()] = value.strip().strip('"').strip("'")
root = Path(values.get('DATA_ROOT', ''))
if not root.is_absolute() or root == Path('/'):
    raise SystemExit('DATA_ROOT must be an absolute directory other than /')
root = root.resolve()
repo = Path(__file__).resolve().parents[1]
if root == repo or repo in root.parents or root in repo.parents:
    raise SystemExit('DATA_ROOT must be separate from the repository')
uid, gid = int(values['PUID']), int(values['PGID'])
for name in ('config', 'cache', 'media/videos', 'media/series', 'media/music', 'media/audiobooks', 'backups', 'caddy/data', 'caddy/config'):
    target = root / name
    target.mkdir(parents=True, exist_ok=True, mode=0o750)
    if not name.startswith('caddy/'):
        os.chown(target, uid, gid)
print(f'External runtime directories prepared: {root}')
print('No media, accounts, or progress data is stored in the repository.')
