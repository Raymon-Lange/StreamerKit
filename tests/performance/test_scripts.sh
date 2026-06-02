#!/usr/bin/env bash
# test_scripts.sh — CLI script performance test suite.
# For each script: cold run + warm run, asserting on runtime, exit code, and feed errors.
# Usage: bash tests/performance/test_scripts.sh
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$REPO_ROOT/tests/performance/config.sh"

PYTHON="$REPO_ROOT/.venv/bin/python"
LOGS_DIR="$REPO_ROOT/logs"
mkdir -p "$LOGS_DIR"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"

# Scripts: "module:extra_args"
SCRIPTS=(
  "run_sp_streamers:--tomorrow"
  "run_free_agent_hitters:--top 10 --size 75"
  "run_team_hitter_eval:"
  "run_team_pitcher_eval:"
  "run_recent_drops_waiver_review:"
  "run_roster_optimizer:"
  "run_pitcher_start_eval:"
)

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  CLI SCRIPT PERFORMANCE TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

reset_counters

run_and_assert() {
  local pass_label="$1" module="$2" args="$3"
  local threshold_var="COLD_MAX_${module}"
  local threshold="${!threshold_var:-60}"
  local logfile="$LOGS_DIR/scripts_${pass_label}_${module}_${TIMESTAMP}.log"
  local script_path="$REPO_ROOT/scripts/${module}.py"

  echo ""
  echo "  ▶  ${pass_label} :: ${module}"

  # Run script; suppress stdout, capture stderr ([FEED]/[SCRIPT] lines) to logfile
  local exit_code=0
  $PYTHON "$script_path" $args >/dev/null 2>"$logfile" || exit_code=$?

  # Exit code assertion
  assert_exit_zero "SCRIPTS :: ${module} :: ${pass_label} :: exit_code" "$exit_code"

  # Runtime from [SCRIPT] line
  local duration
  duration=$(grep '^\[SCRIPT\]' "$logfile" 2>/dev/null \
    | awk -F' \\| ' '{print $4}' \
    | sed 's/s$//' \
    | head -1 || true)

  if [[ -n "$duration" ]]; then
    if [[ "$pass_label" == "cold" ]]; then
      assert_under "SCRIPTS :: ${module} :: cold :: runtime" "$duration" "$threshold"
    else
      # Warm: just report timing, no threshold (cache hit speed varies by platform)
      printf "  \033[36mINFO\033[0m  SCRIPTS :: %s :: warm :: runtime  (%ss)\n" "$module" "$duration"
    fi
  else
    printf "  \033[33mWARN\033[0m  SCRIPTS :: %s :: %s :: runtime  (no [SCRIPT] line found)\n" "$module" "$pass_label"
  fi

  # Feed error assertion (both passes)
  assert_no_feed_errors "SCRIPTS :: ${module} :: ${pass_label} :: no_feed_errors" "$logfile"
}

for entry in "${SCRIPTS[@]}"; do
  IFS=':' read -r module args <<< "$entry"
  run_and_assert "cold" "$module" "$args"
done

echo ""
echo "  ── Warm pass ──"

for entry in "${SCRIPTS[@]}"; do
  IFS=':' read -r module args <<< "$entry"
  run_and_assert "warm" "$module" "$args"
done

report_summary "CLI Script Tests"
