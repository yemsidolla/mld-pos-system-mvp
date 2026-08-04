#!/usr/bin/env sh
# First-run (and re-runnable) Garage bootstrap for Melodu POS.
#
# Prerequisites:
#   - garage service is up (docker compose ... up -d)
#   - .env has GARAGE_RPC_SECRET, S3_STORAGE_BUCKET_NAME, S3_ACCESS_KEY_ID,
#     S3_SECRET_ACCESS_KEY
#
# Steps (scripted):
#   1. garage layout assign
#   2. garage layout apply
#   3. garage bucket create
#   4. garage key import (uses S3_* from env so Django credentials match)
#   5. garage bucket allow --read --write
#
# Usage:
#   scripts/bootstrap_garage.sh
#   COMPOSE_FILE=docker-compose.yml:docker-compose.local.yml scripts/bootstrap_garage.sh
#   COMPOSE_FILE=docker-compose.prod.yml scripts/bootstrap_garage.sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

# Read KEY=VALUE from .env without sourcing (values may contain spaces).
env_get() {
  key="$1"
  if [ ! -f .env ]; then
    return 0
  fi
  # Prefer the last matching assignment; strip optional surrounding quotes.
  line=$(grep -E "^${key}=" .env | tail -1 || true)
  [ -n "$line" ] || return 0
  val=${line#*=}
  val=$(printf '%s' "$val" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
  printf '%s' "$val"
}

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
export COMPOSE_FILE

# Env file values win only when the variable is unset in the shell.
: "${GARAGE_RPC_SECRET:=$(env_get GARAGE_RPC_SECRET)}"
: "${GARAGE_ADMIN_TOKEN:=$(env_get GARAGE_ADMIN_TOKEN)}"
: "${S3_STORAGE_BUCKET_NAME:=$(env_get S3_STORAGE_BUCKET_NAME)}"
: "${S3_ACCESS_KEY_ID:=$(env_get S3_ACCESS_KEY_ID)}"
: "${S3_SECRET_ACCESS_KEY:=$(env_get S3_SECRET_ACCESS_KEY)}"
: "${S3_ENDPOINT_URL:=$(env_get S3_ENDPOINT_URL)}"
: "${GARAGE_KEY_NAME:=$(env_get GARAGE_KEY_NAME)}"
: "${GARAGE_ZONE:=$(env_get GARAGE_ZONE)}"
: "${GARAGE_CAPACITY:=$(env_get GARAGE_CAPACITY)}"

BUCKET="${S3_STORAGE_BUCKET_NAME:-melodu-media}"
KEY_NAME="${GARAGE_KEY_NAME:-melodu-media-key}"
ACCESS_KEY="${S3_ACCESS_KEY_ID:-}"
SECRET_KEY="${S3_SECRET_ACCESS_KEY:-}"
ZONE="${GARAGE_ZONE:-dc1}"
CAPACITY="${GARAGE_CAPACITY:-10G}"

if [ -z "${GARAGE_RPC_SECRET:-}" ]; then
  echo "GARAGE_RPC_SECRET is required (64 hex chars from: openssl rand -hex 32)." >&2
  exit 1
fi

if [ -z "$ACCESS_KEY" ] || [ -z "$SECRET_KEY" ]; then
  echo "S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY are required." >&2
  exit 1
fi

garage_cmd() {
  docker compose exec -T \
    -e GARAGE_RPC_SECRET="$GARAGE_RPC_SECRET" \
    ${GARAGE_ADMIN_TOKEN:+-e GARAGE_ADMIN_TOKEN="$GARAGE_ADMIN_TOKEN"} \
    garage /garage "$@"
}

echo "Waiting for Garage to accept status..."
i=0
while [ "$i" -lt 30 ]; do
  if garage_cmd status >/tmp/melodu_garage_status.out 2>/tmp/melodu_garage_status.err; then
    break
  fi
  i=$((i + 1))
  sleep 1
done
if [ "$i" -ge 30 ]; then
  echo "Garage status failed after wait. Last stderr:" >&2
  cat /tmp/melodu_garage_status.err >&2 || true
  exit 1
fi

NODE_ID=$(awk '/^[0-9a-f]{16}/ {print $1; exit}' /tmp/melodu_garage_status.out)
if [ -z "$NODE_ID" ]; then
  echo "Could not parse Garage node ID from status output:" >&2
  cat /tmp/melodu_garage_status.out >&2
  exit 1
fi
echo "Node: $NODE_ID"

STATUS_NOW=$(garage_cmd status 2>/dev/null || true)
if printf '%s\n' "$STATUS_NOW" | grep -q 'NO ROLE ASSIGNED'; then
  echo "Assigning layout: zone=$ZONE capacity=$CAPACITY"
  garage_cmd layout assign -z "$ZONE" -c "$CAPACITY" "$NODE_ID"
  if ! garage_cmd layout apply --version 1; then
    echo "layout apply --version 1 failed; showing layout and retrying without --version." >&2
    garage_cmd layout show || true
    garage_cmd layout apply
  fi
else
  echo "Layout already assigned; skipping layout assign/apply."
fi

if garage_cmd bucket info "$BUCKET" >/dev/null 2>&1; then
  echo "Bucket exists: $BUCKET"
else
  echo "Creating bucket: $BUCKET"
  garage_cmd bucket create "$BUCKET"
fi

if garage_cmd key info "$KEY_NAME" >/dev/null 2>&1 || garage_cmd key info "$ACCESS_KEY" >/dev/null 2>&1; then
  echo "Access key already present ($KEY_NAME / $ACCESS_KEY)."
else
  echo "Importing access key as $KEY_NAME (credentials from env; secret not logged)."
  garage_cmd key import -n "$KEY_NAME" --yes "$ACCESS_KEY" "$SECRET_KEY"
fi

echo "Allowing read/write on $BUCKET for $KEY_NAME"
garage_cmd bucket allow --read --write --owner "$BUCKET" --key "$KEY_NAME" >/dev/null

echo "Bootstrap complete."
echo "  Bucket:  $BUCKET"
echo "  Key:     $KEY_NAME ($ACCESS_KEY)"
echo "  S3 URL:  ${S3_ENDPOINT_URL:-http://garage:3900}"
garage_cmd bucket info "$BUCKET"
