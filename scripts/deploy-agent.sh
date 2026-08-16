#!/usr/bin/env bash
# Melodu deploy-agent — watches origin/main and deploys to this box from cron.
#
# Model: automate the happy path, ALERT on the sad path — never auto-rollback.
# A failed deploy STOPS, quarantines the commit, and raises a durable, loud alert
# for a human to recover. Chosen by Sidolla 2026-08-16.
#
# Operational state (log, alert, quarantine) lives OUTSIDE the repo in
# DEPLOY_AGENT_STATE_DIR, so it never dirties the worktree the agent must build
# from cleanly. An EXIT trap raises a CRITICAL alert if the process dies after
# swapping the container without completing — so the till is never left down
# silently. Migrations and dirty worktrees are held for a human.
set -uo pipefail

REPO="${DEPLOY_AGENT_REPO:-/opt/mld-pos-system-mvp}"
COMPOSE="${DEPLOY_AGENT_COMPOSE:-docker-compose.prod.yml}"
LIVE="${DEPLOY_AGENT_LIVE:-0}"
STATE_DIR="${DEPLOY_AGENT_STATE_DIR:-/var/lib/mld-deploy-agent}"
LOCK="${DEPLOY_AGENT_LOCK:-/tmp/mld-deploy-agent.lock}"
ALERT_CMD="${DEPLOY_AGENT_ALERT_CMD:-}"          # optional notifier; run as: CMD "<message>"
HEALTH_URL="${DEPLOY_AGENT_HEALTH_URL:-}"        # optional host/nginx URL; else in-container probe

mkdir -p "$STATE_DIR" 2>/dev/null || true
LOG="$STATE_DIR/deploy-agent.log"
ALERT_FILE="$STATE_DIR/DEPLOY-ALERT.txt"
QUARANTINE="$STATE_DIR/quarantine"

SWAPPED=0        # 1 once the new container is running (till is now affected on failure)
DONE=0           # 1 once we reach a terminal, handled state (success or handled failure)

RECOVER="cd $REPO && git checkout main && docker compose -f $COMPOSE build web && docker compose -f $COMPOSE up -d --force-recreate web"

log() { echo "$(date -u +%FT%TZ) $*" >> "$LOG" 2>/dev/null; }

alert() {  # $1 severity, $2 message — durable: STATE_DIR is ours, outside the repo
  local sev="$1" msg="$2" when; when="$(date -u +%FT%TZ)"
  log "  ALERT[$sev] $msg"
  { printf '%s\n[%s] %s\n' "$when" "$sev" "$msg" > "$ALERT_FILE"; } 2>/dev/null \
    || echo "$when [$sev] $msg" >&2   # last resort: stderr (cron mails it)
  if [ -n "$ALERT_CMD" ]; then
    local -a acmd; read -ra acmd <<< "$ALERT_CMD"
    DEPLOY_ALERT_SEVERITY="$sev" "${acmd[@]}" "$msg" >>"$LOG" 2>&1 \
      || log "  ALERT-CMD FAILED (message preserved in $ALERT_FILE)"
  fi
}

quarantine_set() {  # atomic; log if it fails (a failed write risks a redeploy storm)
  printf '%s\n' "$1" > "${QUARANTINE}.tmp" 2>/dev/null && mv -f "${QUARANTINE}.tmp" "$QUARANTINE" 2>/dev/null \
    || { log "  WARN: could not write quarantine for ${1:0:8}"; alert WARN "quarantine write failed for ${1:0:8}; may retry a bad commit."; }
}

on_exit() {  # safety net: an unexpected death after swap must still alert
  local rc=$?
  if [ "$SWAPPED" = "1" ] && [ "$DONE" != "1" ]; then
    alert CRITICAL "deploy-agent exited (rc=$rc) after container swap without completing — TILL MAY BE DOWN. Recover: $RECOVER"
  fi
}
trap on_exit EXIT

dc() { docker compose -f "$COMPOSE" "$@"; }

probe() {
  if [ -n "$HEALTH_URL" ]; then
    curl -fsS --max-time 5 "$HEALTH_URL" 2>/dev/null \
      | python3 -c "import json,sys; sys.exit(0 if json.load(sys.stdin).get('status')=='ok' else 1)" 2>/dev/null
  else
    dc exec -T web python -c \
      "import json,urllib.request,sys; sys.exit(0 if json.load(urllib.request.urlopen('http://127.0.0.1:8000/health/',timeout=5)).get('status')=='ok' else 1)" \
      2>/dev/null
  fi
}
healthy() { for _ in 1 2 3 4 5 6; do sleep 5; probe && return 0; done; return 1; }

# ---- single-flight ----
exec 9>"$LOCK"
flock -n 9 || exit 0

cd "$REPO" || { log "ERROR: repo $REPO missing"; exit 1; }
git rev-parse --verify -q main >/dev/null || { log "ERROR: no main branch"; exit 1; }
git checkout -q main 2>>"$LOG" || { log "ERROR: cannot checkout main"; exit 1; }
git fetch -q origin main || { log "ERROR: git fetch failed"; exit 1; }

GOOD="$(git rev-parse main)"
TARGET="$(git rev-parse origin/main)"
[ "$GOOD" = "$TARGET" ] && { DONE=1; exit 0; }
if [ -f "$QUARANTINE" ] && [ "$(cat "$QUARANTINE" 2>/dev/null)" = "$TARGET" ]; then DONE=1; exit 0; fi

log "main advanced ${GOOD:0:8} -> ${TARGET:0:8}"

# Migration guard — fail CLOSED if the diff itself errors.
if ! MIGDIFF="$(git diff --name-only "$GOOD" "$TARGET" -- '*/migrations/*.py')"; then
  log "  ABORT: migration diff failed; holding."
  alert WARN "Deploy held: could not diff ${TARGET:0:8} for migrations. Till unaffected."
  DONE=1; exit 1
fi
if printf '%s\n' "$MIGDIFF" | grep -v '__init__' | grep -q .; then
  log "  HELD: ${TARGET:0:8} changes migrations — manual deploy required."
  quarantine_set "$TARGET"
  alert WARN "Deploy held: ${TARGET:0:8} changes migrations; manual deploy needed. Till unaffected."
  DONE=1; exit 0
fi

# Clean worktree — an environment issue, NOT a bad commit, so do not quarantine.
if [ -n "$(git status --porcelain)" ]; then
  log "  ABORT: worktree dirty; refusing to build."
  alert WARN "Deploy aborted: production worktree dirty. Till unaffected; clean it (retries when clean)."
  DONE=1; exit 1
fi

if [ "$LIVE" != "1" ]; then
  log "  DRY-RUN: would deploy ${TARGET:0:8} (no migrations, clean tree). Set DEPLOY_AGENT_LIVE=1 to arm."
  DONE=1; exit 0
fi

# ---- deploy: build TARGET detached; promote main only after health ----
if ! git checkout -q --detach "$TARGET" 2>>"$LOG"; then
  git checkout -q main; alert WARN "Deploy failed at checkout of ${TARGET:0:8}. Till unaffected."; quarantine_set "$TARGET"; DONE=1; exit 1
fi
if ! scripts/backup_db.sh >>"$LOG" 2>&1; then
  git checkout -q main; alert WARN "Deploy aborted: DB backup failed for ${TARGET:0:8}. Till unaffected."; quarantine_set "$TARGET"; DONE=1; exit 1
fi
if ! dc build web >>"$LOG" 2>&1; then
  git checkout -q main; alert WARN "Deploy failed: build error for ${TARGET:0:8}. Till unaffected (old container still serving)."; quarantine_set "$TARGET"; DONE=1; exit 1
fi

# Point of no easy return: swap the running container to the new image.
SWAPPED=1
if ! dc up -d >>"$LOG" 2>&1; then
  alert CRITICAL "Deploy of ${TARGET:0:8} failed during container swap — TILL MAY BE DOWN. Recover: $RECOVER"; git checkout -q main; quarantine_set "$TARGET"; DONE=1; exit 1
fi
if ! dc exec -T web python manage.py collectstatic --noinput >>"$LOG" 2>&1; then
  alert CRITICAL "Deploy of ${TARGET:0:8}: collectstatic FAILED after swap — TILL LIKELY BROKEN. Recover: $RECOVER"; git checkout -q main; quarantine_set "$TARGET"; DONE=1; exit 1
fi

if healthy; then
  if git checkout -q -B main "$TARGET" 2>>"$LOG"; then
    rm -f "$QUARANTINE" "$ALERT_FILE" 2>/dev/null
    DONE=1; log "  DEPLOYED OK -> ${TARGET:0:8}"
  else
    alert CRITICAL "Deploy of ${TARGET:0:8} healthy but could not advance main — state inconsistent. Check: cd $REPO && git status"; DONE=1; exit 1
  fi
else
  alert CRITICAL "Deploy of ${TARGET:0:8} UNHEALTHY after swap — TILL LIKELY DOWN. Recover: $RECOVER"; git checkout -q main; quarantine_set "$TARGET"; DONE=1; exit 1
fi
