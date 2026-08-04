#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: scripts/restore_garage.sh backups/melodu_pos_garage_YYYYMMDD_HHMMSS.tar.gz" >&2
  exit 1
fi

if [ "${CONFIRM_RESTORE:-}" != "yes" ]; then
  echo "Set CONFIRM_RESTORE=yes to confirm this Garage restore." >&2
  exit 2
fi

GARAGE_TARGET="${GARAGE_TARGET:-.}"
tar -xzf "$1" -C "$GARAGE_TARGET"
