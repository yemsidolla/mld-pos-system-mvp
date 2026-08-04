#!/usr/bin/env sh
# Restore Garage data from a tarball produced by scripts/backup_garage.sh.
#
# Safety:
#   - Requires CONFIRM_RESTORE=yes
#   - Requires Garage to be stopped (refuses if running)
#   - Moves the existing data/garage aside rather than merging into it
#   - Then extracts the archive (paths are typically data/garage/...)
#
# Usage:
#   docker compose stop garage
#   CONFIRM_RESTORE=yes scripts/restore_garage.sh backups/melodu_pos_garage_YYYYMMDD_HHMMSS.tar.gz
#   docker compose start garage
#
# Optional:
#   COMPOSE_FILE=docker-compose.yml:docker-compose.local.yml
#   GARAGE_TARGET=.          # directory that will receive the archived paths
#   GARAGE_DATA_DIR=data/garage  # live data dir to move aside before extract

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

if [ "$#" -ne 1 ]; then
  echo "Usage: scripts/restore_garage.sh backups/melodu_pos_garage_YYYYMMDD_HHMMSS.tar.gz" >&2
  exit 1
fi

ARCHIVE="$1"

if [ ! -f "$ARCHIVE" ]; then
  echo "Archive not found: $ARCHIVE" >&2
  exit 1
fi

if [ "${CONFIRM_RESTORE:-}" != "yes" ]; then
  echo "Set CONFIRM_RESTORE=yes to confirm this Garage restore." >&2
  exit 2
fi

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
export COMPOSE_FILE
GARAGE_TARGET="${GARAGE_TARGET:-.}"
GARAGE_DATA_DIR="${GARAGE_DATA_DIR:-data/garage}"

garage_running() {
  docker compose ps --status running --services 2>/dev/null | grep -qx garage
}

if garage_running; then
  echo "Garage is running. Stop it before restore to avoid corrupting live metadata." >&2
  echo "  docker compose stop garage" >&2
  echo "  CONFIRM_RESTORE=yes scripts/restore_garage.sh $ARCHIVE" >&2
  echo "  docker compose start garage" >&2
  exit 1
fi

# Move existing data aside (do not merge two database states).
if [ -e "$GARAGE_DATA_DIR" ]; then
  STAMP="$(date +%Y%m%d_%H%M%S)"
  ASIDE="${GARAGE_DATA_DIR}.before_restore_${STAMP}"
  echo "Moving existing $GARAGE_DATA_DIR -> $ASIDE"
  mv "$GARAGE_DATA_DIR" "$ASIDE"
fi

mkdir -p "$GARAGE_TARGET"
tar -xzf "$ARCHIVE" -C "$GARAGE_TARGET"
echo "Restored $ARCHIVE into $GARAGE_TARGET"
echo "Start Garage when ready: docker compose start garage"
