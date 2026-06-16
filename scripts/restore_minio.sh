#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: scripts/restore_minio.sh backups/melodu_pos_minio_YYYYMMDD_HHMMSS.tar.gz" >&2
  exit 1
fi

if [ "${CONFIRM_RESTORE:-}" != "yes" ]; then
  echo "Set CONFIRM_RESTORE=yes to confirm this MinIO restore." >&2
  exit 2
fi

MINIO_TARGET="${MINIO_TARGET:-.}"
tar -xzf "$1" -C "$MINIO_TARGET"
