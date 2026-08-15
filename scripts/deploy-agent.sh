#!/usr/bin/env bash
# Melodu deploy-agent — watches origin/main and deploys to this box.
#
# Runs from cron on the production host. Deploys ONLY when origin/main has moved
# ahead of the deployed commit. Safe by construction:
#   - DRY-RUN by default (DEPLOY_AGENT_LIVE=1 to actually deploy)
#   - single-flight lock (never two deploys at once)
#   - DB backup before any change
#   - migrate-before-serve ordering
#   - post-deploy health check with automatic rollback to the previous commit
#
# Install: copy to a STABLE path outside the repo working tree (so a pull can't
# swap the running agent), e.g. /usr/local/bin/mld-deploy-agent.sh, and run it
# from cron. Rollback assumes additive/backward-compatible migrations (the
# project's standard); a destructive migration must be deployed by hand.
set -euo pipefail

REPO="${DEPLOY_AGENT_REPO:-/opt/mld-pos-system-mvp}"
COMPOSE="${DEPLOY_AGENT_COMPOSE:-docker-compose.prod.yml}"
LIVE="${DEPLOY_AGENT_LIVE:-0}"          # 0 = dry-run (default), 1 = really deploy
LOG="${DEPLOY_AGENT_LOG:-$REPO/deploy-agent.log}"
LOCK="${DEPLOY_AGENT_LOCK:-/tmp/mld-deploy-agent.lock}"

log() { echo "$(date -u +%FT%TZ) $*" >> "$LOG"; }

# Single-flight: exit quietly if another run holds the lock.
exec 9>"$LOCK"
flock -n 9 || exit 0

cd "$REPO"
git fetch -q origin main
LOCAL="$(git rev-parse HEAD)"
REMOTE="$(git rev-parse origin/main)"
[ "$LOCAL" = "$REMOTE" ] && exit 0      # nothing new — the common case, stays quiet

log "main advanced ${LOCAL:0:8} -> ${REMOTE:0:8}"

if [ "$LIVE" != "1" ]; then
  log "  DRY-RUN: would deploy ${REMOTE:0:8} (backup, pull, build, migrate, up, health, rollback-on-fail). Set DEPLOY_AGENT_LIVE=1 to arm."
  exit 0
fi

dc() { docker compose -f "$COMPOSE" "$@"; }

# --- real deploy ---
log "  backup DB"
scripts/backup_db.sh >>"$LOG" 2>&1 || { log "  ABORT: backup failed"; exit 1; }

log "  pull ${REMOTE:0:8}"
git pull --ff-only origin main >>"$LOG" 2>&1

log "  build web image"
dc build web >>"$LOG" 2>&1

log "  migrate (before serving new code)"
dc run --rm web python manage.py migrate --noinput >>"$LOG" 2>&1

log "  recreate web + collectstatic"
dc up -d >>"$LOG" 2>&1
dc exec -T web python manage.py collectstatic --noinput >>"$LOG" 2>&1

# --- health check with auto-rollback ---
sleep 5
if dc exec -T web python -c "import urllib.request,sys; sys.exit(0 if 'ok' in urllib.request.urlopen('http://127.0.0.1:8000/health/',timeout=5).read().decode() else 1)" 2>/dev/null; then
  log "  DEPLOYED OK -> ${REMOTE:0:8}"
else
  log "  HEALTH CHECK FAILED — rolling back to ${LOCAL:0:8}"
  git reset --hard "$LOCAL" >>"$LOG" 2>&1
  dc build web >>"$LOG" 2>&1
  dc up -d >>"$LOG" 2>&1
  if dc exec -T web python -c "import urllib.request,sys; sys.exit(0 if 'ok' in urllib.request.urlopen('http://127.0.0.1:8000/health/',timeout=5).read().decode() else 1)" 2>/dev/null; then
    log "  ROLLED BACK OK -> ${LOCAL:0:8} (deploy of ${REMOTE:0:8} rejected)"
  else
    log "  ROLLBACK ALSO UNHEALTHY — manual intervention needed (was ${LOCAL:0:8})"
  fi
  exit 1
fi
