#!/usr/bin/env sh
set -eu

# Avoid macOS AppleDouble / xattr noise in archives.
export COPYFILE_DISABLE="${COPYFILE_DISABLE:-1}"

BACKUP_DIR="${BACKUP_DIR:-backups}"
GARAGE_SOURCE="${GARAGE_SOURCE:-data/garage}"
mkdir -p "$BACKUP_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$BACKUP_DIR/melodu_pos_garage_$STAMP.tar.gz"

tar -czf "$OUT" "$GARAGE_SOURCE"
echo "$OUT"
