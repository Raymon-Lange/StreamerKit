#!/usr/bin/env bash
# perf_check.sh — restart dev containers, run all scripts twice (cold then cached),
# capture [FEED]/[SCRIPT] log lines, print a performance summary.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$REPO_ROOT/.venv/bin/python"
LOGS_DIR="$REPO_ROOT/logs"
mkdir -p "$LOGS_DIR"

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
LOG_COLD="$LOGS_DIR/perf_cold_${TIMESTAMP}.log"
LOG_WARM="$LOGS_DIR/perf_warm_${TIMESTAMP}.log"

# Scripts in menu order; each entry is "label:script_module:extra_args"
SCRIPTS=(
  "Streaming Pitchers:run_sp_streamers:--tomorrow"
  "Free Agent Hitters:run_free_agent_hitters:--top 10 --size 75"
  "Team Hitters:run_team_hitter_eval:"
  "Team Pitchers:run_team_pitcher_eval:"
  "Waiver Pickup Review:run_recent_drops_waiver_review:"
  "Roster Optimizer:run_roster_optimizer:"
  "Pitcher Start Eval:run_pitcher_start_eval:"
  "Ranking Page Sources:show_ranking_page_sources:"
)

run_all_scripts() {
  local pass_label="$1"
  local logfile="$2"

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  PASS: $pass_label"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  : > "$logfile"   # truncate / create

  for entry in "${SCRIPTS[@]}"; do
    IFS=':' read -r label module args <<< "$entry"
    script_path="$REPO_ROOT/scripts/${module}.py"

    echo ""
    echo "  ▶  $label ($module)"

    # Run script; stdout goes to terminal, stderr (our [FEED]/[SCRIPT] lines) to logfile + terminal
    if $PYTHON "$script_path" $args \
        2> >(tee -a "$logfile" >&2); then
      echo "     ✓ exited 0"
    else
      echo "     ✗ exited non-zero (credentials missing or network error — logged)"
    fi
  done

  echo ""
  echo "  Log saved → $logfile"
}

# ── 1. Restart dev containers ────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Restarting dev containers"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd "$REPO_ROOT"
docker compose -f docker-compose.dev.yml down --remove-orphans 2>&1 || true
docker compose -f docker-compose.dev.yml up -d 2>&1
echo "  Containers up."

# ── 2. Cold pass (first run — fetches from network, populates cache) ─────────
run_all_scripts "COLD (network fetch)" "$LOG_COLD"

# ── 3. Warm pass (second run — all reads should be cache-fallback) ───────────
run_all_scripts "WARM (cached)" "$LOG_WARM"

# ── 4. Performance summary ───────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PERFORMANCE SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

summarise() {
  local label="$1"
  local logfile="$2"
  echo "  ── $label ──"
  if [[ ! -s "$logfile" ]]; then
    echo "    (no log entries)"
    return
  fi

  # Script-level totals
  echo ""
  echo "  Script runtimes ([SCRIPT] lines):"
  grep '^\[SCRIPT\]' "$logfile" | while IFS= read -r line; do
    # [SCRIPT] 2026-06-02T14:17:14Z | run_sp_streamers.py | completed | 2.18s
    script_name=$(echo "$line" | awk -F' \\| ' '{print $2}')
    outcome=$(echo "$line" | awk -F' \\| ' '{print $3}')
    duration=$(echo "$line" | awk -F' \\| ' '{print $4}')
    printf "    %-42s  %-12s  %s\n" "$script_name" "$outcome" "$duration"
  done

  # Feed-level breakdown
  echo ""
  echo "  Feed operation timings ([FEED] lines):"
  printf "    %-20s  %-35s  %-16s  %s\n" "COLLECTOR" "OPERATION" "OUTCOME" "DURATION"
  printf "    %-20s  %-35s  %-16s  %s\n" "────────────────────" "───────────────────────────────────" "────────────────" "────────"
  grep '^\[FEED\]' "$logfile" | while IFS= read -r line; do
    # [FEED] ts | triggered_by | collector | operation | outcome | duration | [error]
    collector=$(echo "$line" | awk -F' \\| ' '{print $3}')
    operation=$(echo "$line" | awk -F' \\| ' '{print $4}')
    outcome=$(echo "$line" | awk -F' \\| ' '{print $5}')
    duration=$(echo "$line" | awk -F' \\| ' '{print $6}')
    printf "    %-20s  %-35s  %-16s  %s\n" "$collector" "$operation" "$outcome" "$duration"
  done

  # Outcome counts
  local total success errors cache_fallback
  total=$(grep -c '^\[FEED\]' "$logfile" 2>/dev/null || echo 0)
  success=$(grep '^\[FEED\]' "$logfile" | grep -c '| success |' 2>/dev/null || echo 0)
  errors=$(grep '^\[FEED\]' "$logfile" | grep -c '| error |' 2>/dev/null || echo 0)
  cache_fallback=$(grep '^\[FEED\]' "$logfile" | grep -c '| cache-fallback |' 2>/dev/null || echo 0)
  echo ""
  echo "  Totals: $total feed events — $success success, $cache_fallback cache-fallback, $errors error"
  echo ""
}

summarise "COLD PASS  →  $LOG_COLD" "$LOG_COLD"
summarise "WARM PASS  →  $LOG_WARM" "$LOG_WARM"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Done. Full logs:"
echo "    Cold: $LOG_COLD"
echo "    Warm: $LOG_WARM"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
