#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: scripts/restore_db.sh backups/melodu_pos_db_YYYYMMDD_HHMMSS.sql" >&2
  exit 1
fi

cat "$1" | docker compose exec -T postgres sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"'
