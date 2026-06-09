#!/usr/bin/env sh
set -eu

BACKUP_DIR="${BACKUP_DIR:-backups}"
MEDIA_SOURCE="${MEDIA_SOURCE:-data/media}"
mkdir -p "$BACKUP_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$BACKUP_DIR/melodu_pos_media_$STAMP.tar.gz"

tar -czf "$OUT" "$MEDIA_SOURCE"
echo "$OUT"
