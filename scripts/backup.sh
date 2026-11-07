#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v docker >/dev/null
root=$(python3 - <<'PYROOT'
from pathlib import Path
for line in Path('.env').read_text().splitlines():
    if line.strip().startswith('DATA_ROOT='):
        p=Path(line.split('=',1)[1].strip().strip('"').strip("'"))
        if not p.is_absolute() or p == Path('/'):
            raise SystemExit('Invalid DATA_ROOT')
        print(p.resolve())
        break
else:
    raise SystemExit('Missing DATA_ROOT')
PYROOT
)
mkdir -p "$root/backups"
chmod 700 "$root/backups"
umask 077
# Refuse a stopped server so this script never unexpectedly starts it.
if ! docker compose ps --status running --services | grep -qx jellyfin; then
    echo 'Jellyfin must be running before backup.' >&2
    exit 1
fi
archive="$root/backups/jellyfin-config-$(date -u +%Y%m%dT%H%M%SZ)-$$.tar.gz"
docker compose stop jellyfin
trap 'docker compose start jellyfin' EXIT
tar -czf "$archive.partial" -C "$root" config
mv "$archive.partial" "$archive"
printf 'Saved private configuration backup: %s\n' "$archive"
