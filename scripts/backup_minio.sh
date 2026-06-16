#!/usr/bin/env sh
set -eu

BACKUP_DIR="${BACKUP_DIR:-backups}"
MINIO_SOURCE="${MINIO_SOURCE:-data/minio}"
mkdir -p "$BACKUP_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$BACKUP_DIR/melodu_pos_minio_$STAMP.tar.gz"

tar -czf "$OUT" "$MINIO_SOURCE"
echo "$OUT"
