#!/usr/bin/env bash
# Melodu deploy-agent — watches origin/main and deploys to this box from cron.
#
# Safe by construction (each guard answers a real failure mode):
#   - DRY-RUN by default (DEPLOY_AGENT_LIVE=1 to arm).
#   - Single-flight lock — never two deploys at once.
#   - Migration guard — commits that add migrations are HELD for a human; the
#     automated path deploys only no-schema-change commits, so rollback is purely
#     code+image and always safe (DB rollback is not automated).
#   - Exact-SHA pin — deploys the fetched target commit, not a re-pulled newer one.
#   - main stays at the known-good commit until the new one passes health; a
#     mid-deploy death therefore never marks a broken commit as "deployed".
#   - Image retag rollback — the running image is tagged :rollback before the
#     build, so recovery restores it without rebuilding old source.
#   - Explicit error handling (NOT `set -e`) so rollback ALWAYS runs on any
#     failed step, with a retrying health check on both deploy and rollback.
#   - Quarantine — a commit that failed deploy is not retried until main moves,
#     so a bad commit can't cause a redeploy storm every tick.
set -uo pipefail

REPO="${DEPLOY_AGENT_REPO:-/opt/mld-pos-system-mvp}"
COMPOSE="${DEPLOY_AGENT_COMPOSE:-docker-compose.prod.yml}"
IMG="${DEPLOY_AGENT_IMAGE:-mld-pos-system-mvp-web}"
LIVE="${DEPLOY_AGENT_LIVE:-0}"
LOG="${DEPLOY_AGENT_LOG:-$REPO/deploy-agent.log}"
LOCK="${DEPLOY_AGENT_LOCK:-/tmp/mld-deploy-agent.lock}"
QUARANTINE="${DEPLOY_AGENT_QUARANTINE:-/tmp/mld-deploy-agent.quarantine}"

log() { echo "$(date -u +%FT%TZ) $*" >> "$LOG"; }
dc()  { docker compose -f "$COMPOSE" "$@"; }

# One internal health probe; caller retries. Checks the real health payload.
probe() {
  dc exec -T web python -c \
    "import urllib.request,sys; sys.exit(0 if '\"status\": \"ok\"' in urllib.request.urlopen('http://127.0.0.1:8000/health/',timeout=5).read().decode() else 1)" \
    2>/dev/null
}
healthy() {  # retry for slow startup: 6 x 5s = 30s
  for _ in 1 2 3 4 5 6; do sleep 5; probe && return 0; done
  return 1
}

# ---- single-flight ----
exec 9>"$LOCK"
flock -n 9 || exit 0

cd "$REPO" || { log "ERROR: repo $REPO missing"; exit 1; }

git fetch -q origin main || { log "ERROR: git fetch failed"; exit 1; }
GOOD="$(git rev-parse HEAD)"            # currently checked-out & running = known good
TARGET="$(git rev-parse origin/main)"
[ "$GOOD" = "$TARGET" ] && exit 0       # nothing new — the quiet common case

# Quarantine: don't retry a commit we already failed to deploy.
if [ -f "$QUARANTINE" ] && [ "$(cat "$QUARANTINE" 2>/dev/null)" = "$TARGET" ]; then
  exit 0
fi

log "main advanced ${GOOD:0:8} -> ${TARGET:0:8}"

# Migration guard — schema changes are a human's job (DB rollback isn't safe to
# automate). Hold and stop.
NEWMIG="$(git diff --name-only "$GOOD" "$TARGET" -- '*/migrations/*.py' | grep -v '__init__' || true)"
if [ -n "$NEWMIG" ]; then
  log "  HELD: ${TARGET:0:8} adds migration(s) — manual deploy required:"
  while IFS= read -r m; do log "    $m"; done <<< "$NEWMIG"
  echo "$TARGET" > "$QUARANTINE"   # don't re-log every tick
  exit 0
fi

if [ "$LIVE" != "1" ]; then
  log "  DRY-RUN: would deploy ${TARGET:0:8} (no migrations; retag-rollback armed). Set DEPLOY_AGENT_LIVE=1 to arm."
  exit 0
fi

# ---- deploy: build TARGET while main stays at GOOD (detached), promote on health ----
deploy() {
  scripts/backup_db.sh                         >>"$LOG" 2>&1 || return 1
  docker image inspect "${IMG}:latest" >/dev/null 2>&1 \
    && { docker tag "${IMG}:latest" "${IMG}:rollback" >>"$LOG" 2>&1 || return 1; }
  git checkout -q --detach "$TARGET"           >>"$LOG" 2>&1 || return 1
  dc build web                                 >>"$LOG" 2>&1 || return 1
  dc up -d                                     >>"$LOG" 2>&1 || return 1
  dc exec -T web python manage.py collectstatic --noinput >>"$LOG" 2>&1 || return 1
  healthy || return 1
  git checkout -q -B main "$TARGET"            >>"$LOG" 2>&1 || return 1   # promote: main = TARGET
  return 0
}

rollback() {
  log "  ROLLING BACK to ${GOOD:0:8}"
  git checkout -q -B main "$GOOD" >>"$LOG" 2>&1
  if docker image inspect "${IMG}:rollback" >/dev/null 2>&1; then
    docker tag "${IMG}:rollback" "${IMG}:latest" >>"$LOG" 2>&1
    dc up -d >>"$LOG" 2>&1
  else
    dc build web >>"$LOG" 2>&1; dc up -d >>"$LOG" 2>&1   # last resort: rebuild old source
  fi
  if healthy; then
    log "  ROLLED BACK OK -> ${GOOD:0:8} (deploy of ${TARGET:0:8} rejected)"
  else
    log "  ROLLBACK UNHEALTHY — MANUAL INTERVENTION NEEDED (known-good ${GOOD:0:8})"
  fi
}

if deploy; then
  rm -f "$QUARANTINE"
  log "  DEPLOYED OK -> ${TARGET:0:8}"
else
  log "  DEPLOY FAILED for ${TARGET:0:8}"
  rollback
  echo "$TARGET" > "$QUARANTINE"   # don't retry this bad commit until main moves
  exit 1
fi
