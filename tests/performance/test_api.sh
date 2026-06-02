#!/usr/bin/env bash
# test_api.sh — API endpoint performance test suite.
# Cold pass: clear cache, hit all endpoints, assert HTTP 200 + response time.
# Warm pass: same endpoints, assert HTTP 200 + under WARM_MAX_API_SECONDS.
# Usage: bash tests/performance/test_api.sh
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$REPO_ROOT/tests/performance/config.sh"

LOGS_DIR="$REPO_ROOT/logs"
mkdir -p "$LOGS_DIR"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
LOG_COLD="$LOGS_DIR/api_perf_cold_${TIMESTAMP}.log"
LOG_WARM="$LOGS_DIR/api_perf_warm_${TIMESTAMP}.log"

API_KEY="$(grep '^API_KEY=' "$REPO_ROOT/.env" 2>/dev/null | cut -d= -f2- | tr -d '[:space:]')"
if [[ -z "$API_KEY" ]]; then
  echo "ERROR: API_KEY not found in .env" >&2
  exit 1
fi

API_BASE="http://localhost:9471"

# "label:path:threshold_key"
ENDPOINTS=(
  "health:/health:health"
  "streamers:/api/streamers?tomorrow=true:streamers"
  "recent-drops:/api/recent-drops:recent_drops"
  "pitcher-starts:/api/pitcher-starts?tomorrow=true:pitcher_starts"
  "weekly-scores:/api/weekly-scores?latest_scored=true:weekly_scores"
  "roster-optimizer:/api/roster-optimizer:roster_optimizer"
  "dashboard:/api/dashboard:dashboard"
)

wait_for_api() {
  local max=30 i=0
  until curl -sf "$API_BASE/health" -o /dev/null 2>/dev/null; do
    i=$((i+1))
    [[ $i -ge $max ]] && { echo "ERROR: API did not become ready." >&2; exit 1; }
    sleep 2
  done
}

hit_endpoint() {
  local path="$1"
  local result
  if [[ "$path" == "/health" ]]; then
    result=$(curl -s -o /dev/null -w "%{http_code} %{time_total}" "$API_BASE$path" 2>/dev/null)
  else
    result=$(curl -s -o /dev/null -w "%{http_code} %{time_total}" \
      -H "X-API-Key: $API_KEY" "$API_BASE$path" 2>/dev/null)
  fi
  echo "$result"
}

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  API ENDPOINT PERFORMANCE TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

reset_counters

# ── Restart containers and clear API cache ───────────────────────────────────
echo ""
echo "  Restarting dev containers..."
cd "$REPO_ROOT"
docker compose -f docker-compose.dev.yml down --remove-orphans 2>&1 | grep -E 'Removed|Stopped|Started|Created|Error' || true
docker compose -f docker-compose.dev.yml up -d 2>&1 | grep -E 'Removed|Stopped|Started|Created|Error' || true
wait_for_api
rm -f "$REPO_ROOT/.cache"/api_*.json
echo "  Ready. API cache cleared."

# ── Cold pass ────────────────────────────────────────────────────────────────
echo ""
echo "  ── Cold pass ──"
log_since="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

for entry in "${ENDPOINTS[@]}"; do
  IFS=':' read -r label path threshold_key <<< "$entry"
  threshold_var="COLD_MAX_${threshold_key}"
  threshold="${!threshold_var:-60}"

  result=$(hit_endpoint "$path")
  http_code=$(echo "$result" | awk '{print $1}')
  time_total=$(echo "$result" | awk '{print $2}')

  assert_http_ok    "API :: ${label} :: cold :: http_status"    "$http_code"
  assert_under      "API :: ${label} :: cold :: response_time"  "$time_total" "$threshold"
  sleep 0.3
done

# Collect [FEED] lines from docker logs
docker compose -f docker-compose.dev.yml logs --since "$log_since" --no-log-prefix api 2>/dev/null \
  | grep '^\[FEED\]' > "$LOG_COLD" || true
assert_no_feed_errors "API :: cold_pass :: no_feed_errors" "$LOG_COLD"

# ── Warm pass ────────────────────────────────────────────────────────────────
echo ""
echo "  ── Warm pass ──"

for entry in "${ENDPOINTS[@]}"; do
  IFS=':' read -r label path threshold_key <<< "$entry"

  result=$(hit_endpoint "$path")
  http_code=$(echo "$result" | awk '{print $1}')
  time_total=$(echo "$result" | awk '{print $2}')

  assert_http_ok    "API :: ${label} :: warm :: http_status"    "$http_code"
  assert_under      "API :: ${label} :: warm :: response_time"  "$time_total" "$WARM_MAX_API_SECONDS"
  sleep 0.3
done

# Warm pass should produce no [FEED] lines (served from API cache)
log_since_warm="$(date -u -d '30 seconds ago' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u +%Y-%m-%dT%H:%M:%SZ)"
docker compose -f docker-compose.dev.yml logs --since "$log_since_warm" --no-log-prefix api 2>/dev/null \
  | grep '^\[FEED\]' > "$LOG_WARM" || true
assert_no_feed_errors "API :: warm_pass :: no_feed_errors" "$LOG_WARM"

report_summary "API Endpoint Tests"
