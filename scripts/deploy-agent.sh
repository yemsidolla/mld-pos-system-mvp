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
#
# Every command that can block (docker, git-over-network, the notifier) runs
# under `timeout`: a hang would otherwise hold the flock forever with no alert —
# the one failure the EXIT trap cannot catch, because the process never exits.
# The container swap touches ONLY web (--no-deps): postgres and garage are
# never reconciled by an automated deploy.
set -uo pipefail

REPO="${DEPLOY_AGENT_REPO:-/opt/mld-pos-system-mvp}"
# Compose file selection — colon-separated, the same syntax as COMPOSE_FILE.
# The default is EMPTY on purpose. With no -f, compose reads the COMPOSE_FILE
# pin from the repo's own .env, and that pin is load-bearing: it adds
# docker-compose.lan.yml, the override that publishes the 192.168.1.212:<port>
# binding nginx proxies to. An explicit -f OVERRIDES the pin and silently drops
# it — a bare `-f docker-compose.prod.yml` took production down for six days in
# Aug 2026, and an in-container probe cannot see that failure. Set this only to
# deploy a box whose .env is not pinned.
COMPOSE_FILES="${DEPLOY_AGENT_COMPOSE:-}"
LIVE="${DEPLOY_AGENT_LIVE:-0}"
STATE_DIR="${DEPLOY_AGENT_STATE_DIR:-/var/lib/mld-deploy-agent}"
ALERT_CMD="${DEPLOY_AGENT_ALERT_CMD:-}"          # optional notifier; run as: CMD "<message>"
HEALTH_URL="${DEPLOY_AGENT_HEALTH_URL:-}"        # optional host/nginx URL; else in-container probe

# Bounded time for anything that can block. A hang would hold the single-flight
# lock forever with DONE=0 and no alert — worse than any clean failure.
T_GIT="${DEPLOY_AGENT_T_GIT:-120}"               # fetch (network)
T_BACKUP="${DEPLOY_AGENT_T_BACKUP:-600}"
T_BUILD="${DEPLOY_AGENT_T_BUILD:-1800}"          # pip + Tailwind can be slow; pre-swap, till unaffected
T_SWAP="${DEPLOY_AGENT_T_SWAP:-120}"             # post-swap commands must fail FAST
T_STATIC="${DEPLOY_AGENT_T_STATIC:-180}"
T_PROBE="${DEPLOY_AGENT_T_PROBE:-30}"
T_ALERT="${DEPLOY_AGENT_T_ALERT:-30}"            # a hung notifier must never block the trap

# State dir must be writable BEFORE anything else: without it there is no log,
# no durable alert, and no quarantine — never proceed on `|| true`.
if ! mkdir -p "$STATE_DIR" 2>/dev/null || [ ! -w "$STATE_DIR" ]; then
  echo "deploy-agent: STATE_DIR $STATE_DIR not writable — refusing to run" >&2
  exit 1
fi
LOG="$STATE_DIR/deploy-agent.log"
ALERT_FILE="$STATE_DIR/DEPLOY-ALERT.txt"
QUARANTINE="$STATE_DIR/quarantine"
# Lock lives in STATE_DIR, not /tmp: tmp cleaners unlink held locks, and two
# agents on one worktree can swap a torn build.
LOCK="${DEPLOY_AGENT_LOCK:-$STATE_DIR/lock}"

DCF=()           # -f arguments; empty means "honour the COMPOSE_FILE pin in .env"
DC_SHOW="docker compose"
if [ -n "$COMPOSE_FILES" ]; then
  IFS=':' read -ra _CF <<< "$COMPOSE_FILES"
  for _f in "${_CF[@]}"; do
    [ -n "$_f" ] || continue
    DCF+=(-f "$_f"); DC_SHOW="$DC_SHOW -f $_f"
  done
fi

SWAPPED=0        # 1 once the new container is running (till is now affected on failure)
DONE=0           # 1 once we reach a terminal, handled state (success or handled failure)

RECOVER="cd $REPO && git checkout main && $DC_SHOW build web && $DC_SHOW up -d --no-deps --force-recreate web"

# TERM then KILL: coreutils timeout without --kill-after waits FOREVER on a
# child that ignores SIGTERM (docker compose routinely does). Every bound in
# this script goes through here, including the notifier called from the trap.
bounded() { timeout --kill-after=5 "$@"; }

log() { echo "$(date -u +%FT%TZ) $*" >> "$LOG" 2>/dev/null; }

alert() {  # $1 severity, $2 message — durable file first; notifier bounded after
  local sev="$1" msg="$2" when; when="$(date -u +%FT%TZ)"
  log "  ALERT[$sev] $msg"
  # APPEND, never truncate: a follow-up alert (e.g. back_to_main's) must not
  # clobber the till-down recovery message. Cleared on successful deploy.
  { printf '%s [%s] %s\n' "$when" "$sev" "$msg" >> "$ALERT_FILE"; } 2>/dev/null \
    || echo "$when [$sev] $msg" >&2   # last resort: stderr (cron mails it)
  if [ -n "$ALERT_CMD" ]; then
    local -a acmd; read -ra acmd <<< "$ALERT_CMD"
    DEPLOY_ALERT_SEVERITY="$sev" bounded "$T_ALERT" "${acmd[@]}" "$msg" >>"$LOG" 2>&1 \
      || log "  ALERT-CMD FAILED/TIMED OUT (message preserved in $ALERT_FILE)"
  fi
}

quarantine_set() {  # atomic; a failed write after swap risks redeploying a bad commit
  if printf '%s\n' "$1" > "${QUARANTINE}.tmp" 2>/dev/null && mv -f "${QUARANTINE}.tmp" "$QUARANTINE" 2>/dev/null; then
    return 0
  fi
  if [ "$SWAPPED" = "1" ]; then
    alert CRITICAL "quarantine write FAILED for ${1:0:8} after container swap — next cron WILL redeploy it. Disable cron or fix $STATE_DIR now."
  else
    alert WARN "quarantine write failed for ${1:0:8}; may retry a bad commit."
  fi
}

back_to_main() {  # failure paths must not strand HEAD detached at a bad commit
  bounded 30 git checkout -q main 2>>"$LOG" && return 0
  if [ "$SWAPPED" = "1" ]; then  # caller already raised the till-down CRITICAL
    log "  ERROR: could not return checkout to main (HEAD likely detached)"
  else
    alert CRITICAL "could not return checkout to main — HEAD may be detached in $REPO. Fix: cd $REPO && git checkout main"
  fi
}

on_exit() {  # safety net: an unexpected death after swap must still alert
  local rc=$?
  if [ "$SWAPPED" = "1" ] && [ "$DONE" != "1" ]; then
    alert CRITICAL "deploy-agent exited (rc=$rc) after container swap without completing — TILL MAY BE DOWN. Recover: $RECOVER"
  fi
}
trap on_exit EXIT


probe() {
  if [ -n "$HEALTH_URL" ]; then
    # pipefail would report the RIGHTMOST failure: a curl killed at 124 shows
    # as python's 1 and healthy() would retry a hang. Surface the 124.
    bounded "$T_PROBE" curl -fsS --max-time 5 "$HEALTH_URL" 2>/dev/null \
      | python3 -c "import json,sys; sys.exit(0 if json.load(sys.stdin).get('status')=='ok' else 1)" 2>/dev/null
    local -a ps=("${PIPESTATUS[@]}")
    [ "${ps[0]}" -eq 124 ] && return 124   # curl leg hung/killed: this is a hang, not "not ready"
    [ "${ps[0]}" -ne 0 ] && return 1
    return "${ps[1]}"
  else
    bounded "$T_PROBE" docker compose ${DCF[@]+"${DCF[@]}"} exec -T web python -c \
      "import json,urllib.request,sys; sys.exit(0 if json.load(urllib.request.urlopen('http://127.0.0.1:8000/health/',timeout=5)).get('status')=='ok' else 1)" \
      2>/dev/null
  fi
}
healthy() {  # 124 = the probe HUNG (wedged docker/engine): fail now, not after 6x35s
  local rc
  for _ in 1 2 3 4 5 6; do
    sleep 5
    probe && return 0
    rc=$?; [ "$rc" -eq 124 ] && { log "  probe timed out (rc=124); not retrying a wedged probe"; return 1; }
  done
  return 1
}

# ---- published-port guard ----
# The in-container probe cannot tell a healthy container apart from one nginx
# can no longer reach: `web` publishes BOTH 127.0.0.1:8001 and
# 192.168.1.212:8001, and only docker-compose.lan.yml provides the second — the
# one nginx on 192.168.1.99 proxies to. Losing it is invisible to every other
# check in this script, so snapshot the bindings before the swap and assert they
# survive it. Advisory: if the bindings cannot be read, log and carry on rather
# than block a deploy on the guard itself.
web_ports() {  # -> sorted "hostip:hostport->containerport" lines, one per binding
  local cid
  cid="$(bounded 30 docker compose ${DCF[@]+"${DCF[@]}"} ps -q web 2>/dev/null | head -n1)"
  [ -n "$cid" ] || return 1
  bounded 30 docker inspect --format '{{json .NetworkSettings.Ports}}' "$cid" 2>/dev/null \
    | python3 -c 'import json,sys
d = json.load(sys.stdin) or {}
out = set()
for cport, binds in d.items():
    for b in (binds or []):
        out.add("%s:%s->%s" % (b.get("HostIp", ""), b.get("HostPort", ""), cport))
print("\n".join(sorted(out)))' 2>/dev/null
}

# ---- single-flight ----
if ! exec 9>"$LOCK"; then
  alert WARN "deploy-agent: cannot open lock $LOCK — deploys are NOT running."
  exit 1
fi
flock -n 9 || exit 0

cd "$REPO" || { alert WARN "deploy-agent: repo $REPO missing — deploys are NOT running."; exit 1; }
git rev-parse --verify -q main >/dev/null || { alert WARN "deploy-agent: no main branch in $REPO — deploys are NOT running."; exit 1; }
git checkout -q main 2>>"$LOG" || { alert WARN "deploy-agent: cannot checkout main in $REPO (HEAD may be detached) — deploys are NOT running."; exit 1; }
bounded "$T_GIT" git fetch -q origin main || { log "ERROR: git fetch failed/timed out (transient; will retry)"; exit 1; }

GOOD="$(git rev-parse main)"
TARGET="$(git rev-parse origin/main)"
[ "$GOOD" = "$TARGET" ] && { DONE=1; exit 0; }
if [ -f "$QUARANTINE" ] && [ "$(cat "$QUARANTINE" 2>/dev/null)" = "$TARGET" ]; then DONE=1; exit 0; fi

log "main advanced ${GOOD:0:8} -> ${TARGET:0:8}"
[ -n "$HEALTH_URL" ] || log "  note: DEPLOY_AGENT_HEALTH_URL unset; health is probed inside the container only (port guard still applies)"

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
  back_to_main; alert WARN "Deploy failed at checkout of ${TARGET:0:8}. Till unaffected."; quarantine_set "$TARGET"; DONE=1; exit 1
fi
# Backup failure is an ENVIRONMENT fault (disk, pg down) — like a dirty
# worktree, it does not quarantine: retry when the environment recovers.
if ! bounded "$T_BACKUP" scripts/backup_db.sh >>"$LOG" 2>&1; then
  back_to_main; alert WARN "Deploy aborted: DB backup failed/timed out for ${TARGET:0:8}. Till unaffected (retries next run)."; DONE=1; exit 1
fi
# Build failure is plausibly the COMMIT's fault (Dockerfile, deps) — quarantine
# so a broken commit does not rebuild every cron tick.
if ! bounded "$T_BUILD" docker compose ${DCF[@]+"${DCF[@]}"} build web >>"$LOG" 2>&1; then
  back_to_main; alert WARN "Deploy failed: build error/timeout for ${TARGET:0:8}. Till unaffected (old container still serving)."; quarantine_set "$TARGET"; DONE=1; exit 1
fi

# Snapshot the published bindings while the OLD container is still up, so the
# post-swap comparison has a baseline. Taken before SWAPPED=1: the till is
# still unaffected here.
if ! PORTS_BEFORE="$(web_ports)" || [ -z "$PORTS_BEFORE" ]; then
  PORTS_BEFORE=""
  log "  WARN: could not read published ports before swap; port guard disabled for this run"
fi

# Point of no easy return: swap the running container to the new image.
# ONLY web, --no-deps: postgres health must not block the swap, and an
# automated deploy must never restart the database or media store.
SWAPPED=1
if ! bounded "$T_SWAP" docker compose ${DCF[@]+"${DCF[@]}"} up -d --no-deps --force-recreate web >>"$LOG" 2>&1; then
  alert CRITICAL "Deploy of ${TARGET:0:8} failed/timed out during container swap — TILL MAY BE DOWN. Recover: $RECOVER"; back_to_main; quarantine_set "$TARGET"; DONE=1; exit 1
fi
# A swap that succeeds but drops a published binding leaves a container that is
# healthy from the inside and unreachable from nginx — the six-day outage shape.
# Treat it exactly like an unhealthy deploy.
if [ -n "$PORTS_BEFORE" ]; then
  PORTS_AFTER="$(web_ports)" || PORTS_AFTER=""
  LOST="$(comm -23 <(printf '%s\n' "$PORTS_BEFORE") <(printf '%s\n' "$PORTS_AFTER") | tr '\n' ' ')"
  if [ -n "${LOST// /}" ]; then
    alert CRITICAL "Deploy of ${TARGET:0:8} LOST published port(s) [${LOST% }] — container is up but nginx cannot reach it. Check COMPOSE_FILE in $REPO/.env still pins the LAN override. Recover: $RECOVER"
    back_to_main; quarantine_set "$TARGET"; DONE=1; exit 1
  fi
  log "  published ports intact after swap: $(printf '%s' "$PORTS_AFTER" | tr '\n' ' ')"
fi

if ! bounded "$T_STATIC" docker compose ${DCF[@]+"${DCF[@]}"} exec -T web python manage.py collectstatic --noinput >>"$LOG" 2>&1; then
  alert CRITICAL "Deploy of ${TARGET:0:8}: collectstatic FAILED/timed out after swap — TILL LIKELY BROKEN. Recover: $RECOVER"; back_to_main; quarantine_set "$TARGET"; DONE=1; exit 1
fi

# Restart AFTER collectstatic, and this is not optional.
# ManifestStaticFilesStorage reads staticfiles.json ONCE and caches it in the
# running process. collectstatic rewrites that file on disk, but the container
# that started before it keeps serving the PREVIOUS hashed filenames — so a
# deploy that changes any static asset ships stale CSS/JS while every check
# here passes: the container is healthy, the ports are bound, the probe
# returns ok. Observed doing exactly this on the V8 deploy (2026-09-02), where
# production served tailwind.a02c4501125a.css while the manifest already said
# a4c12a1ea295. Silent, and invisible to the health probe.
#
# `restart` not `up -d`: the container is already the new image, we only need
# the process to re-read the manifest. It also cannot change the published
# ports, which the guard above just verified.
if ! bounded "$T_SWAP" docker compose ${DCF[@]+"${DCF[@]}"} restart web >>"$LOG" 2>&1; then
  alert CRITICAL "Deploy of ${TARGET:0:8}: restart after collectstatic FAILED/timed out — TILL MAY BE DOWN or serving stale assets. Recover: $RECOVER"; back_to_main; quarantine_set "$TARGET"; DONE=1; exit 1
fi

if healthy; then
  if git checkout -q -B main "$TARGET" 2>>"$LOG"; then
    rm -f "$QUARANTINE" "$ALERT_FILE" 2>/dev/null
    DONE=1; log "  DEPLOYED OK -> ${TARGET:0:8}"
  else
    alert CRITICAL "Deploy of ${TARGET:0:8} healthy but could not advance main — state inconsistent. Check: cd $REPO && git status"; DONE=1; exit 1
  fi
else
  alert CRITICAL "Deploy of ${TARGET:0:8} UNHEALTHY after swap — TILL LIKELY DOWN. Recover: $RECOVER"; back_to_main; quarantine_set "$TARGET"; DONE=1; exit 1
fi
