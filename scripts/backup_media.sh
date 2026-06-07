#!/usr/bin/env sh
set -eu

BACKUP_DIR="${BACKUP_DIR:-backups}"
mkdir -p "$BACKUP_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$BACKUP_DIR/melodu_pos_media_$STAMP.tar.gz"

tar -czf "$OUT" data/media
echo "$OUT"
