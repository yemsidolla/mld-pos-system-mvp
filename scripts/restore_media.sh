#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: scripts/restore_media.sh backups/melodu_pos_media_YYYYMMDD_HHMMSS.tar.gz" >&2
  exit 1
fi

if [ "${CONFIRM_RESTORE:-}" != "yes" ]; then
  echo "Set CONFIRM_RESTORE=yes to confirm this media restore." >&2
  exit 2
fi

MEDIA_TARGET="${MEDIA_TARGET:-.}"
tar -xzf "$1" -C "$MEDIA_TARGET"
