#!/usr/bin/env sh
# One-shot object copy: MinIO bucket -> Garage bucket.
# Preserves object keys exactly. Safe to re-run (sync/overwrite same keys).
# Does NOT delete source MinIO data.
#
# Required env:
#   MINIO_ENDPOINT_URL   e.g. http://127.0.0.1:9000
#   MINIO_ACCESS_KEY_ID
#   MINIO_SECRET_ACCESS_KEY
#   GARAGE_ENDPOINT_URL  e.g. http://127.0.0.1:3900  (or http://garage:3900 on compose network)
#   S3_ACCESS_KEY_ID / S3_SECRET_ACCESS_KEY   (Garage key)
#   S3_STORAGE_BUCKET_NAME                    (same bucket name on both sides)
#
# Optional:
#   AWS_CLI_IMAGE=amazon/aws-cli:2.15.57
#   MIGRATE_WORK_DIR=/tmp/melodu_minio_to_garage_$$
#
# Usage (host, both APIs published to localhost):
#   MINIO_ENDPOINT_URL=http://127.0.0.1:9000 \
#   MINIO_ACCESS_KEY_ID=... MINIO_SECRET_ACCESS_KEY=... \
#   GARAGE_ENDPOINT_URL=http://127.0.0.1:3900 \
#   S3_ACCESS_KEY_ID=... S3_SECRET_ACCESS_KEY=... \
#   S3_STORAGE_BUCKET_NAME=melodu-media \
#   scripts/migrate_minio_to_garage.sh

set -eu

BUCKET="${S3_STORAGE_BUCKET_NAME:-melodu-media}"
MINIO_ENDPOINT_URL="${MINIO_ENDPOINT_URL:-}"
GARAGE_ENDPOINT_URL="${GARAGE_ENDPOINT_URL:-${S3_ENDPOINT_URL:-}}"
MINIO_ACCESS_KEY_ID="${MINIO_ACCESS_KEY_ID:-}"
MINIO_SECRET_ACCESS_KEY="${MINIO_SECRET_ACCESS_KEY:-}"
GARAGE_ACCESS_KEY_ID="${S3_ACCESS_KEY_ID:-}"
GARAGE_SECRET_ACCESS_KEY="${S3_SECRET_ACCESS_KEY:-}"
AWS_CLI_IMAGE="${AWS_CLI_IMAGE:-amazon/aws-cli:2.15.57}"
REGION="${S3_REGION_NAME:-us-east-1}"
WORK_DIR="${MIGRATE_WORK_DIR:-/tmp/melodu_minio_to_garage_$$}"

need() {
  if [ -z "$1" ]; then
    echo "$2 is required." >&2
    exit 1
  fi
}

need "$MINIO_ENDPOINT_URL" "MINIO_ENDPOINT_URL"
need "$GARAGE_ENDPOINT_URL" "GARAGE_ENDPOINT_URL (or S3_ENDPOINT_URL)"
need "$MINIO_ACCESS_KEY_ID" "MINIO_ACCESS_KEY_ID"
need "$MINIO_SECRET_ACCESS_KEY" "MINIO_SECRET_ACCESS_KEY"
need "$GARAGE_ACCESS_KEY_ID" "S3_ACCESS_KEY_ID"
need "$GARAGE_SECRET_ACCESS_KEY" "S3_SECRET_ACCESS_KEY"

mkdir -p "$WORK_DIR/objects"

aws_docker() {
  endpoint="$1"
  access="$2"
  secret="$3"
  shift 3
  docker run --rm \
    --network "${MIGRATE_DOCKER_NETWORK:-host}" \
    -e AWS_ACCESS_KEY_ID="$access" \
    -e AWS_SECRET_ACCESS_KEY="$secret" \
    -e AWS_DEFAULT_REGION="$REGION" \
    -e AWS_EC2_METADATA_DISABLED=true \
    -v "$WORK_DIR:$WORK_DIR" \
    "$AWS_CLI_IMAGE" \
    --endpoint-url "$endpoint" \
    --region "$REGION" \
    "$@"
}

# Build "key size" maps from `aws s3 ls --recursive` lines:
#   2026-08-04 16:00:00         17 products/from-minio.txt
parse_listing() {
  awk 'NF >= 4 && $1 ~ /^[0-9]{4}-/ { size=$3; key=$4; for (i=5;i<=NF;i++) key=key" "$i; print key "\t" size }'
}

echo "Listing source (MinIO) objects in s3://$BUCKET ..."
aws_docker "$MINIO_ENDPOINT_URL" "$MINIO_ACCESS_KEY_ID" "$MINIO_SECRET_ACCESS_KEY" \
  s3 ls "s3://$BUCKET" --recursive --summarize >"$WORK_DIR/minio_list.txt" || true

parse_listing <"$WORK_DIR/minio_list.txt" >"$WORK_DIR/minio_keys.tsv"
SRC_COUNT=$(wc -l <"$WORK_DIR/minio_keys.tsv" | tr -d ' ')
SRC_BYTES=$(awk -F'\t' '{s+=$2} END {print s+0}' "$WORK_DIR/minio_keys.tsv")
echo "Source: $SRC_COUNT objects, $SRC_BYTES bytes"

echo "Syncing MinIO -> local mirror (keys preserved)..."
aws_docker "$MINIO_ENDPOINT_URL" "$MINIO_ACCESS_KEY_ID" "$MINIO_SECRET_ACCESS_KEY" \
  s3 sync "s3://$BUCKET" "$WORK_DIR/objects"

echo "Syncing local mirror -> Garage (keys preserved; re-run safe)..."
aws_docker "$GARAGE_ENDPOINT_URL" "$GARAGE_ACCESS_KEY_ID" "$GARAGE_SECRET_ACCESS_KEY" \
  s3 sync "$WORK_DIR/objects" "s3://$BUCKET"

echo "Listing destination (Garage) objects..."
aws_docker "$GARAGE_ENDPOINT_URL" "$GARAGE_ACCESS_KEY_ID" "$GARAGE_SECRET_ACCESS_KEY" \
  s3 ls "s3://$BUCKET" --recursive --summarize >"$WORK_DIR/garage_list.txt" || true

parse_listing <"$WORK_DIR/garage_list.txt" >"$WORK_DIR/garage_keys.tsv"
DST_COUNT=$(wc -l <"$WORK_DIR/garage_keys.tsv" | tr -d ' ')
DST_BYTES=$(awk -F'\t' '{s+=$2} END {print s+0}' "$WORK_DIR/garage_keys.tsv")
echo "Destination: $DST_COUNT objects, $DST_BYTES bytes (may include pre-existing keys)"

# Verify every source key exists on dest with the same byte size.
# Destination may legitimately have additional objects already.
FAIL=0
while IFS="$(printf '\t')" read -r key size; do
  [ -n "$key" ] || continue
  dest_size=$(awk -F'\t' -v k="$key" '$1==k {print $2; exit}' "$WORK_DIR/garage_keys.tsv")
  if [ -z "$dest_size" ]; then
    echo "MISSING on Garage: $key" >&2
    FAIL=1
  elif [ "$dest_size" != "$size" ]; then
    echo "SIZE MISMATCH for $key: minio=$size garage=$dest_size" >&2
    FAIL=1
  fi
done <"$WORK_DIR/minio_keys.tsv"

if [ "$FAIL" -ne 0 ]; then
  echo "Verification FAILED. Lists: $WORK_DIR/minio_list.txt $WORK_DIR/garage_list.txt" >&2
  exit 1
fi

echo "Verification OK: all $SRC_COUNT source object(s) present on Garage with matching sizes ($SRC_BYTES bytes)."
echo "Work dir left at $WORK_DIR (delete when satisfied)."
