#!/usr/bin/env bash
# Build Melodu Tailwind CSS with the standalone CLI (no Node/npm).
# Pin must match docker/django/Dockerfile TAILWIND_VERSION.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="${TAILWIND_VERSION:-4.3.3}"
INPUT="$ROOT/tailwind/input.css"
OUTPUT="$ROOT/app/core/static/core/css/tailwind.css"
BIN_DIR="${TAILWIND_BIN_DIR:-$ROOT/.tools}"
BIN="$BIN_DIR/tailwindcss"

mkdir -p "$BIN_DIR"

detect_asset() {
  local os arch
  os="$(uname -s | tr '[:upper:]' '[:lower:]')"
  arch="$(uname -m)"
  case "$os-$arch" in
    darwin-arm64) echo "macos-arm64" ;;
    darwin-x86_64) echo "macos-x64" ;;
    linux-x86_64|linux-amd64) echo "linux-x64" ;;
    linux-aarch64|linux-arm64) echo "linux-arm64" ;;
    *)
      echo "Unsupported platform: $os $arch" >&2
      exit 1
      ;;
  esac
}

ensure_cli() {
  if [[ -x "$BIN" ]]; then
    local reported
    reported="$("$BIN" --help 2>&1 | head -1 || true)"
    if [[ "$reported" == *"$VERSION"* ]]; then
      return 0
    fi
  fi
  local asset url sums expected
  asset="$(detect_asset)"
  url="https://github.com/tailwindlabs/tailwindcss/releases/download/v${VERSION}/tailwindcss-${asset}"
  sums="https://github.com/tailwindlabs/tailwindcss/releases/download/v${VERSION}/sha256sums.txt"
  echo "Downloading Tailwind standalone CLI v${VERSION} (${asset})…"
  curl -fsSL "$url" -o "$BIN"
  expected="$(curl -fsSL "$sums" | awk -v f="./tailwindcss-${asset}" '$2 == f { print $1; exit }')"
  if [[ -z "$expected" ]]; then
    echo "Could not find checksum for tailwindcss-${asset}" >&2
    exit 1
  fi
  echo "${expected}  ${BIN}" | shasum -a 256 -c -
  chmod +x "$BIN"
}

ensure_cli

WATCH=0
MINIFY=1
for arg in "$@"; do
  case "$arg" in
    --watch|-w) WATCH=1 ;;
    --no-minify) MINIFY=0 ;;
  esac
done

ARGS=(-i "$INPUT" -o "$OUTPUT")
if [[ "$MINIFY" -eq 1 && "$WATCH" -eq 0 ]]; then
  ARGS+=(--minify)
fi
if [[ "$WATCH" -eq 1 ]]; then
  ARGS+=(--watch)
  echo "Watching templates; writing $OUTPUT"
fi

exec "$BIN" "${ARGS[@]}"
