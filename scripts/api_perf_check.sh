#!/usr/bin/env bash
# api_perf_check.sh — restart dev containers, hit every API endpoint cold then
# warm, capture curl timing + [FEED]/[SCRIPT] lines from docker logs, print summary.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGS_DIR="$REPO_ROOT/logs"
mkdir -p "$LOGS_DIR"

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
LOG_COLD="$LOGS_DIR/api_cold_${TIMESTAMP}.log"
LOG_WARM="$LOGS_DIR/api_warm_${TIMESTAMP}.log"
TIMING_FILE="$LOGS_DIR/api_timing_${TIMESTAMP}.tsv"

# Load API_KEY from .env
API_KEY="$(grep '^API_KEY=' "$REPO_ROOT/.env" 2>/dev/null | cut -d= -f2- | tr -d '[:space:]')"
if [[ -z "$API_KEY" ]]; then
  echo "ERROR: API_KEY not found in .env" >&2
  exit 1
fi

API_BASE="http://localhost:9471"

# Endpoints: "label|path"
ENDPOINTS=(
  "health|/health"
  "streamers (tomorrow)|/api/streamers?tomorrow=true"
  "recent-drops|/api/recent-drops"
  "pitcher-starts (tomorrow)|/api/pitcher-starts?tomorrow=true"
  "weekly-scores (latest)|/api/weekly-scores?latest_scored=true"
  "roster-optimizer|/api/roster-optimizer"
  "dashboard|/api/dashboard"
)

wait_for_api() {
  echo "  Waiting for API to be ready..."
  local max=30 i=0
  until curl -sf "$API_BASE/health" -o /dev/null 2>/dev/null; do
    i=$((i+1))
    if [[ $i -ge $max ]]; then echo "  ERROR: API did not become ready in time." >&2; exit 1; fi
    sleep 2
  done
  echo "  API is up."
}

clear_api_cache() {
  echo "  Clearing API response cache (.cache/api_*.json)..."
  rm -f "$REPO_ROOT/.cache"/api_*.json
  echo "  Cache cleared."
}

hit_endpoint() {
  local label="$1" path="$2" pass="$3"
  local url="${API_BASE}${path}"
  local result

  # Time the request; /health needs no auth header
  if [[ "$path" == "/health" ]]; then
    result=$(curl -s -o /dev/null -w "%{http_code} %{time_total}" "$url" 2>/dev/null)
  else
    result=$(curl -s -o /dev/null -w "%{http_code} %{time_total}" \
      -H "X-API-Key: $API_KEY" "$url" 2>/dev/null)
  fi

  local http_code time_total
  http_code=$(echo "$result" | awk '{print $1}')
  time_total=$(echo "$result" | awk '{print $2}')

  printf "  %-38s  HTTP %s  %ss\n" "$label" "$http_code" "$time_total"

  # TSV row: pass | label | path | http_code | time_total
  printf "%s\t%s\t%s\t%s\t%s\n" "$pass" "$label" "$path" "$http_code" "$time_total" \
    >> "$TIMING_FILE"
}

run_pass() {
  local pass_label="$1" pass_key="$2" logfile="$3"

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  PASS: $pass_label"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # Snapshot container log position before this pass
  local log_since
  log_since="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  for entry in "${ENDPOINTS[@]}"; do
    IFS='|' read -r label path <<< "$entry"
    hit_endpoint "$label" "$path" "$pass_key"
    sleep 0.3   # slight gap so docker log timestamps don't collide
  done

  # Collect [FEED] lines from docker logs since pass start
  echo ""
  echo "  Collecting [FEED] lines from docker logs..."
  docker compose -f "$REPO_ROOT/docker-compose.dev.yml" logs \
    --since "$log_since" \
    --no-log-prefix \
    api 2>/dev/null \
    | grep '^\[FEED\]' \
    >> "$logfile" || true

  local feed_count
  feed_count=$(grep -c '^\[FEED\]' "$logfile" 2>/dev/null || echo 0)
  echo "  $feed_count [FEED] lines captured → $logfile"
}

# ── 1. Restart dev containers ────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Restarting dev containers"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd "$REPO_ROOT"
docker compose -f docker-compose.dev.yml down --remove-orphans 2>&1 || true
docker compose -f docker-compose.dev.yml up -d 2>&1
wait_for_api

# ── 2. Cold pass ─────────────────────────────────────────────────────────────
clear_api_cache
: > "$LOG_COLD"
: > "$TIMING_FILE"
run_pass "COLD (no API cache)" "cold" "$LOG_COLD"

# ── 3. Warm pass (API response_cache already populated from cold pass) ────────
: > "$LOG_WARM"
run_pass "WARM (API cache hit)" "warm" "$LOG_WARM"

# ── 4. Summary ───────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ENDPOINT RESPONSE TIMES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
printf "  %-38s  %-10s  %-10s  %s\n" "ENDPOINT" "COLD" "WARM" "SPEEDUP"
printf "  %-38s  %-10s  %-10s  %s\n" \
  "──────────────────────────────────────" "──────────" "──────────" "───────"

# Join cold/warm rows from TSV by label
declare -A cold_times warm_times cold_codes warm_codes
while IFS=$'\t' read -r pass label path code time; do
  if [[ "$pass" == "cold" ]]; then
    cold_times["$label"]="$time"
    cold_codes["$label"]="$code"
  elif [[ "$pass" == "warm" ]]; then
    warm_times["$label"]="$time"
    warm_codes["$label"]="$code"
  fi
done < "$TIMING_FILE"

for entry in "${ENDPOINTS[@]}"; do
  IFS='|' read -r label path <<< "$entry"
  c="${cold_times[$label]:-?}"
  w="${warm_times[$label]:-?}"
  cc="${cold_codes[$label]:-?}"
  wc="${warm_codes[$label]:-?}"

  speedup="—"
  if [[ "$c" != "?" && "$w" != "?" ]]; then
    speedup=$(awk -v c="$c" -v w="$w" 'BEGIN {
      if (w > 0 && c > w) printf "%.1fx faster", c/w
      else if (c > 0 && w > c) printf "%.1fx slower", w/c
      else printf "≈ same"
    }')
  fi

  printf "  %-38s  %-10s  %-10s  %s\n" \
    "$label" "${c}s (${cc})" "${w}s (${wc})" "$speedup"
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  FEED OPERATIONS DURING COLD PASS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [[ -s "$LOG_COLD" ]] && grep -q '^\[FEED\]' "$LOG_COLD" 2>/dev/null; then
  printf "  %-22s  %-38s  %-16s  %s\n" "COLLECTOR" "OPERATION" "OUTCOME" "DURATION"
  printf "  %-22s  %-38s  %-16s  %s\n" \
    "──────────────────────" "──────────────────────────────────────" "────────────────" "────────"
  grep '^\[FEED\]' "$LOG_COLD" | awk -F' \\| ' \
    '{printf "  %-22s  %-38s  %-16s  %s\n", $3, $4, $5, $6}'
  echo ""
  # Outcome counts
  local_total=$(grep -c '^\[FEED\]' "$LOG_COLD" || echo 0)
  local_success=$(grep '^\[FEED\]' "$LOG_COLD" | grep -c '| success |' || echo 0)
  local_cache=$(grep '^\[FEED\]' "$LOG_COLD" | grep -c '| cache-fallback |' || echo 0)
  local_err=$(grep '^\[FEED\]' "$LOG_COLD" | grep -c '| error |' || echo 0)
  echo "  Totals: $local_total — $local_success success, $local_cache cache-fallback, $local_err error"
else
  echo "  (no [FEED] lines captured — container logs may need a moment to flush)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  WARM PASS: only [FEED] lines present (should be zero — served from API cache)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
warm_feeds=$(grep -c '^\[FEED\]' "$LOG_WARM" 2>/dev/null || echo 0)
echo "  [FEED] lines in warm pass: $warm_feeds"
echo "  (0 expected — all responses served from API response_cache)"

echo ""
echo "  Full logs:"
echo "    Cold: $LOG_COLD"
echo "    Warm: $LOG_WARM"
echo "    Timing TSV: $TIMING_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
