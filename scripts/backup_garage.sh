#!/usr/bin/env sh
# Consistent backup of Garage data directory.
#
# Garage keeps metadata in an embedded database. A hot tar of data/garage while
# the server is running can capture a torn state that silently fails to restore.
#
# This script refuses to run if Garage is running, unless GARAGE_BACKUP_STOP=yes
# is set (script stops Garage, archives, then always restarts it — including on
# failure via EXIT trap).
#
# Usage:
#   docker compose ... stop garage && scripts/backup_garage.sh && docker compose ... start garage
#   GARAGE_BACKUP_STOP=yes scripts/backup_garage.sh
#
# Optional:
#   COMPOSE_FILE=docker-compose.yml:docker-compose.local.yml
#   GARAGE_SOURCE=data/garage
#   BACKUP_DIR=backups

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

# Avoid macOS AppleDouble / xattr noise in archives.
export COPYFILE_DISABLE="${COPYFILE_DISABLE:-1}"

BACKUP_DIR="${BACKUP_DIR:-backups}"
GARAGE_SOURCE="${GARAGE_SOURCE:-data/garage}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
export COMPOSE_FILE

mkdir -p "$BACKUP_DIR"

WE_STOPPED=0

garage_running() {
  docker compose ps --status running --services 2>/dev/null | grep -qx garage
}

restart_garage_if_needed() {
  if [ "$WE_STOPPED" -eq 1 ]; then
    echo "Restarting Garage (was stopped by this script)..." >&2
    docker compose start garage >/dev/null
    WE_STOPPED=0
  fi
}

trap restart_garage_if_needed EXIT

if garage_running; then
  if [ "${GARAGE_BACKUP_STOP:-}" != "yes" ]; then
    echo "Garage is running. Refusing a hot tar of $GARAGE_SOURCE." >&2
    echo "A live archive can capture inconsistent Garage metadata and fail to restore." >&2
    echo "" >&2
    echo "Stop Garage, then re-run this script:" >&2
    echo "  docker compose stop garage && scripts/backup_garage.sh && docker compose start garage" >&2
    echo "" >&2
    echo "Or let this script stop/restart Garage safely:" >&2
    echo "  GARAGE_BACKUP_STOP=yes scripts/backup_garage.sh" >&2
    exit 1
  fi
  echo "Stopping Garage for a consistent backup..."
  docker compose stop garage
  WE_STOPPED=1
fi

if [ ! -d "$GARAGE_SOURCE" ]; then
  echo "GARAGE_SOURCE does not exist: $GARAGE_SOURCE" >&2
  exit 1
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$BACKUP_DIR/melodu_pos_garage_$STAMP.tar.gz"

tar -czf "$OUT" "$GARAGE_SOURCE"
echo "$OUT"

# Restart before exiting successfully (trap also covers failures).
restart_garage_if_needed
trap - EXIT
