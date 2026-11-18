#!/usr/bin/env bash
# ai-morning-catchup.sh: make sure today's AI Morning episode gets built, and say so loudly when it is not.
#
# WHY: GitHub's scheduler dropped every 5:15-7:15 AM run on 2026-11-18 (first run 12:51 PM) and nothing
# alerted. This box is always on, so it is the independent trigger and the watchdog. The build itself still
# runs on GitHub Actions; this only starts it and reports.
#
# Every 30 min (cron.d). Cheap no-op once the episode exists.
#   - episode exists            -> heartbeat ok=true, done
#   - before 06:00 Central      -> do nothing (GitHub's own schedule gets first go)
#   - missing, a run is active  -> leave it
#   - missing, none active      -> start the workflow (max 3 starts per day, so a persistent failure
#                                  cannot loop and burn API spend)
#   - missing at/after 09:00    -> heartbeat ok=false: heartbeat-watch pushes the operator's alert
# heartbeat-watch also alerts if this job stops reporting (25 h window), so a dead cron is not silent either.
#
# Config: /etc/ai-morning/github.env holds GITHUB_TOKEN=<fine-grained PAT, this repo only, Actions: read+write>.
set -uo pipefail

REPO="AutomAIton/amf-1cfbea55"
CONF=/etc/ai-morning/github.env
HB_ENV=/etc/certpath/heartbeat-watch.env
STATE=/var/lib/ai-morning
ALERT_HOUR=9
FIRST_HOUR=6
MAX_STARTS=3

today=$(TZ=America/Chicago date +%F)
hour=$((10#$(TZ=America/Chicago date +%H)))
mkdir -p "$STATE"

report() {  # report <true|false> <summary>
  local tok
  tok=$(grep -oP '(?<=HEARTBEAT_TOKEN=).*' "$HB_ENV" 2>/dev/null) || tok=""
  echo "$(date -u +%FT%TZ) ok=$1 $2"
  [ -n "$tok" ] || { echo "no heartbeat token readable"; return; }
  curl -sS -m 20 -X POST http://127.0.0.1:3002/heartbeat \
    -H "content-type: application/json" -H @<(printf 'x-heartbeat-token: %s\n' "$tok") \
    -d "$(printf '{"name":"ai-morning-episode","ok":%s,"summary":%s}' "$1" \
          "$(printf '%s' "$2" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')")" \
    >/dev/null || echo "heartbeat POST failed (non-fatal)"
}

# Is today's episode on main? (repo is public, no token needed)
hist=$(curl -fsS -m 30 --retry 2 "https://raw.githubusercontent.com/${REPO}/main/data/history.json?cb=$(date +%s)") || hist=""
if [ -z "$hist" ]; then
  [ "$hour" -ge "$ALERT_HOUR" ] && report false "cannot read ${REPO} data/history.json"
  exit 0
fi
have=$(printf '%s' "$hist" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(any(e.get("date")==sys.argv[1] for e in d.get("episodes",[])))' "$today" 2>/dev/null) || have=""
if [ "$have" = "True" ]; then
  report true "episode ${today} published"
  exit 0
fi
if [ "$have" != "False" ]; then
  [ "$hour" -ge "$ALERT_HOUR" ] && report false "history.json unreadable"
  exit 0
fi

# Missing. Too early: let GitHub's scheduler try first.
[ "$hour" -lt "$FIRST_HOUR" ] && exit 0

TOKEN=$(grep -oP '(?<=GITHUB_TOKEN=).*' "$CONF" 2>/dev/null) || TOKEN=""
# Secrets go in via a header file (process substitution), never in argv where `ps` shows them.
api() { curl -sS -m 30 -H @<(printf 'Authorization: Bearer %s\n' "$TOKEN") -H "Accept: application/vnd.github+json" "$@"; }

last="no run info"
active=0
if [ -n "$TOKEN" ]; then
  runs=$(api "https://api.github.com/repos/${REPO}/actions/workflows/daily.yml/runs?per_page=5") || runs=""
  if [ -n "$runs" ]; then
    active=$(printf '%s' "$runs" | python3 -c 'import json,sys; r=json.load(sys.stdin).get("workflow_runs",[]); print(sum(1 for x in r if x["status"] in ("queued","in_progress","waiting","pending")))' 2>/dev/null) || active=0
    last=$(printf '%s' "$runs" | python3 -c 'import json,sys; r=json.load(sys.stdin).get("workflow_runs",[]); x=r[0] if r else None; print("last run %s/%s %s" % (x["status"],x["conclusion"],x["html_url"]) if x else "no runs")' 2>/dev/null) || last="no run info"
  fi
fi

started=""
if [ "$active" -gt 0 ]; then
  started="a run is active"
elif [ -z "$TOKEN" ]; then
  started="no GitHub token in ${CONF}"
else
  n=$(cat "$STATE/starts-$today" 2>/dev/null || echo 0)
  if [ "$n" -ge "$MAX_STARTS" ]; then
    started="already started ${n} builds today, not starting another"
  else
    code=$(api -o /dev/null -w '%{http_code}' -X POST \
      "https://api.github.com/repos/${REPO}/actions/workflows/daily.yml/dispatches" -d '{"ref":"main"}') || code=000
    if [ "$code" = "204" ]; then
      echo $((n + 1)) > "$STATE/starts-$today"
      started="build started (#$((n + 1)) today)"
    else
      started="could not start build (HTTP ${code})"
    fi
  fi
fi

if [ "$hour" -ge "$ALERT_HOUR" ]; then
  report false "episode ${today} missing; ${started}; ${last}"
else
  echo "$(date -u +%FT%TZ) episode ${today} missing; ${started}; ${last}"
fi
exit 0
