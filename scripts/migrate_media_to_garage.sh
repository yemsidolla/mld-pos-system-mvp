#!/usr/bin/env sh
# Upload local filesystem media -> Garage bucket.
#
# Object keys MUST equal paths relative to the media root (exactly what Django
# stores in FieldFile.name, e.g. products/foo.jpg). Source files are never
# deleted or modified.
#
# Required env:
#   GARAGE_ENDPOINT_URL  e.g. http://127.0.0.1:3900  (or S3_ENDPOINT_URL)
#   S3_ACCESS_KEY_ID / S3_SECRET_ACCESS_KEY
#   S3_STORAGE_BUCKET_NAME
#
# Optional:
#   MEDIA_ROOT=data/media
#   S3_MEDIA_CACHE_CONTROL=max-age=86400
#   AWS_CLI_IMAGE=amazon/aws-cli:2.15.57
#   MIGRATE_DOCKER_NETWORK=host
#   MIGRATE_WORK_DIR=/tmp/melodu_media_to_garage_$$
#
# Usage (host, Garage S3 published to localhost):
#   GARAGE_ENDPOINT_URL=http://127.0.0.1:3900 \
#   S3_ACCESS_KEY_ID=... S3_SECRET_ACCESS_KEY=... \
#   S3_STORAGE_BUCKET_NAME=melodu-media \
#   scripts/migrate_media_to_garage.sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

BUCKET="${S3_STORAGE_BUCKET_NAME:-melodu-media}"
GARAGE_ENDPOINT_URL="${GARAGE_ENDPOINT_URL:-${S3_ENDPOINT_URL:-}}"
GARAGE_ACCESS_KEY_ID="${S3_ACCESS_KEY_ID:-}"
GARAGE_SECRET_ACCESS_KEY="${S3_SECRET_ACCESS_KEY:-}"
AWS_CLI_IMAGE="${AWS_CLI_IMAGE:-amazon/aws-cli:2.15.57}"
REGION="${S3_REGION_NAME:-us-east-1}"
CACHE_CONTROL="${S3_MEDIA_CACHE_CONTROL:-max-age=86400}"
MEDIA_ROOT="${MEDIA_ROOT:-data/media}"
WORK_DIR="${MIGRATE_WORK_DIR:-/tmp/melodu_media_to_garage_$$}"

need() {
  if [ -z "$1" ]; then
    echo "$2 is required." >&2
    exit 1
  fi
}

need "$GARAGE_ENDPOINT_URL" "GARAGE_ENDPOINT_URL (or S3_ENDPOINT_URL)"
need "$GARAGE_ACCESS_KEY_ID" "S3_ACCESS_KEY_ID"
need "$GARAGE_SECRET_ACCESS_KEY" "S3_SECRET_ACCESS_KEY"

case "$MEDIA_ROOT" in
  /*) MEDIA_ABS="$MEDIA_ROOT" ;;
  *) MEDIA_ABS="$ROOT_DIR/$MEDIA_ROOT" ;;
esac

if [ ! -d "$MEDIA_ABS" ]; then
  echo "MEDIA_ROOT is not a directory: $MEDIA_ABS" >&2
  exit 1
fi

mkdir -p "$WORK_DIR"

file_size_bytes() {
  wc -c <"$1" | tr -d ' \n'
}

# Build "key\tsize" manifest. find -print0 handles spaces/unicode; never parse ls.
# Write paths to a file first so the reader is not a pipeline subshell.
find "$MEDIA_ABS" -type f -print0 >"$WORK_DIR/paths.bin"

: >"$WORK_DIR/source_keys.tsv"
while IFS= read -r -d '' filepath; do
  rel=${filepath#"$MEDIA_ABS"/}
  if [ -z "$rel" ] || [ "$rel" = "$filepath" ]; then
    echo "Could not derive relative key for: $filepath" >&2
    exit 1
  fi
  size=$(file_size_bytes "$filepath")
  printf '%s\t%s\n' "$rel" "$size" >>"$WORK_DIR/source_keys.tsv"
done <"$WORK_DIR/paths.bin"

SRC_COUNT=$(wc -l <"$WORK_DIR/source_keys.tsv" | tr -d ' ')
SRC_BYTES=$(awk -F'\t' '{s+=$2} END {print s+0}' "$WORK_DIR/source_keys.tsv")

echo "Source ($MEDIA_ABS): $SRC_COUNT file(s), $SRC_BYTES bytes"

if [ "$SRC_COUNT" -eq 0 ]; then
  echo "ERROR: source media has zero files under $MEDIA_ABS." >&2
  echo "Refusing empty-source success. Populate MEDIA_ROOT or fix the path." >&2
  exit 1
fi

# Upload all objects in one container (Content-Type + Cache-Control per object).
# Inner script is written to the work dir so we do not nest complex quoting.
cat >"$WORK_DIR/upload.sh" <<'UPLOAD_EOF'
#!/bin/sh
set -eu
content_type_for() {
  ext=$(printf '%s' "$1" | awk -F. '{print tolower($NF)}')
  case "$ext" in
    jpg|jpeg) printf '%s' "image/jpeg" ;;
    png) printf '%s' "image/png" ;;
    webp) printf '%s' "image/webp" ;;
    gif) printf '%s' "image/gif" ;;
    svg) printf '%s' "image/svg+xml" ;;
    *) printf '%s' "application/octet-stream" ;;
  esac
}
fail=0
while IFS="$(printf '\t')" read -r key size || [ -n "${key:-}" ]; do
  [ -n "${key:-}" ] || continue
  ctype=$(content_type_for "$key")
  echo "PUT s3://$BUCKET/$key ($ctype)"
  if ! aws --endpoint-url "$ENDPOINT" --region "$REGION" \
    s3 cp "/media/$key" "s3://$BUCKET/$key" \
    --content-type "$ctype" \
    --cache-control "$CACHE_CONTROL"; then
    echo "UPLOAD FAILED: $key" >&2
    fail=1
  fi
done < /work/source_keys.tsv
exit "$fail"
UPLOAD_EOF

echo "Uploading to s3://$BUCKET (Cache-Control=$CACHE_CONTROL)..."
docker run --rm \
  --network "${MIGRATE_DOCKER_NETWORK:-host}" \
  -e AWS_ACCESS_KEY_ID="$GARAGE_ACCESS_KEY_ID" \
  -e AWS_SECRET_ACCESS_KEY="$GARAGE_SECRET_ACCESS_KEY" \
  -e AWS_DEFAULT_REGION="$REGION" \
  -e AWS_EC2_METADATA_DISABLED=true \
  -e ENDPOINT="$GARAGE_ENDPOINT_URL" \
  -e REGION="$REGION" \
  -e BUCKET="$BUCKET" \
  -e CACHE_CONTROL="$CACHE_CONTROL" \
  -v "$MEDIA_ABS:/media:ro" \
  -v "$WORK_DIR:/work" \
  --entrypoint /bin/sh \
  "$AWS_CLI_IMAGE" \
  /work/upload.sh

aws_docker() {
  docker run --rm \
    --network "${MIGRATE_DOCKER_NETWORK:-host}" \
    -e AWS_ACCESS_KEY_ID="$GARAGE_ACCESS_KEY_ID" \
    -e AWS_SECRET_ACCESS_KEY="$GARAGE_SECRET_ACCESS_KEY" \
    -e AWS_DEFAULT_REGION="$REGION" \
    -e AWS_EC2_METADATA_DISABLED=true \
    -v "$WORK_DIR:$WORK_DIR" \
    "$AWS_CLI_IMAGE" \
    --endpoint-url "$GARAGE_ENDPOINT_URL" \
    --region "$REGION" \
    "$@"
}

# Build "key\tsize" from `aws s3 ls --recursive` lines:
#   2026-08-04 16:00:00         17 products/from-media.txt
# Do NOT swallow listing failures — a failed list must not look like empty OK.
parse_listing() {
  awk 'NF >= 4 && $1 ~ /^[0-9]{4}-/ {
    size=$3
    key=$4
    for (i = 5; i <= NF; i++) key = key " " $i
    print key "\t" size
  }'
}

echo "Listing destination (Garage) objects..."
aws_docker s3 ls "s3://$BUCKET" --recursive --summarize >"$WORK_DIR/garage_list.txt"

parse_listing <"$WORK_DIR/garage_list.txt" >"$WORK_DIR/garage_keys.tsv"
DST_COUNT=$(wc -l <"$WORK_DIR/garage_keys.tsv" | tr -d ' ')
DST_BYTES=$(awk -F'\t' '{s+=$2} END {print s+0}' "$WORK_DIR/garage_keys.tsv")
echo "Destination: $DST_COUNT object(s), $DST_BYTES bytes (may include pre-existing keys)"

FAIL=0
while IFS="$(printf '\t')" read -r key size || [ -n "${key:-}" ]; do
  [ -n "${key:-}" ] || continue
  dest_size=$(awk -F'\t' -v k="$key" '$1==k {print $2; exit}' "$WORK_DIR/garage_keys.tsv")
  if [ -z "$dest_size" ]; then
    echo "MISSING on Garage: $key" >&2
    FAIL=1
  elif [ "$dest_size" != "$size" ]; then
    echo "SIZE MISMATCH for $key: source=$size garage=$dest_size" >&2
    FAIL=1
  fi
done <"$WORK_DIR/source_keys.tsv"

if [ "$FAIL" -ne 0 ]; then
  echo "Verification FAILED. Lists: $WORK_DIR/source_keys.tsv $WORK_DIR/garage_list.txt" >&2
  exit 1
fi

echo "Verification OK: all $SRC_COUNT source object(s) present on Garage with matching sizes ($SRC_BYTES bytes)."
echo "Source files under $MEDIA_ABS were not modified."
echo "Work dir left at $WORK_DIR (delete when satisfied)."
