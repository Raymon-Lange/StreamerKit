#!/usr/bin/env bash
# config.sh — thresholds and shared assertion helpers for the performance test suite.
# Source this file from test_scripts.sh and test_api.sh.

# ── CLI script cold-pass max seconds (2× observed baseline) ─────────────────
COLD_MAX_run_sp_streamers=15
COLD_MAX_run_free_agent_hitters=40
COLD_MAX_run_team_hitter_eval=15
COLD_MAX_run_team_pitcher_eval=15
COLD_MAX_run_recent_drops_waiver_review=30
COLD_MAX_run_roster_optimizer=12
COLD_MAX_run_pitcher_start_eval=18

# ── API endpoint cold-pass max seconds ──────────────────────────────────────
COLD_MAX_health=2
COLD_MAX_streamers=20
COLD_MAX_recent_drops=120
COLD_MAX_pitcher_starts=20
COLD_MAX_weekly_scores=30
COLD_MAX_roster_optimizer=15
COLD_MAX_dashboard=90

# ── Warm-pass API max (all cached responses must be under this) ──────────────
WARM_MAX_API_SECONDS=0.5

# ── Internal counters (reset per suite) ─────────────────────────────────────
_PASS=0
_FAIL=0
declare -a _FAILURES=()

reset_counters() {
  _PASS=0
  _FAIL=0
  _FAILURES=()
}

# ── Assertion helpers ────────────────────────────────────────────────────────

# assert_exit_zero "label" exit_code
assert_exit_zero() {
  local label="$1" code="$2"
  if [[ "$code" -eq 0 ]]; then
    printf "  \033[32mPASS\033[0m  %s\n" "$label"
    _PASS=$(( _PASS + 1 ))
  else
    printf "  \033[31mFAIL\033[0m  %s  (exit %s)\n" "$label" "$code"
    _FAIL=$(( _FAIL + 1 ))
    _FAILURES+=("$label")
  fi
}

# assert_http_ok "label" http_code
assert_http_ok() {
  local label="$1" code="$2"
  if [[ "$code" == "200" ]]; then
    printf "  \033[32mPASS\033[0m  %s  (HTTP %s)\n" "$label" "$code"
    _PASS=$(( _PASS + 1 ))
  else
    printf "  \033[31mFAIL\033[0m  %s  (HTTP %s, expected 200)\n" "$label" "$code"
    _FAIL=$(( _FAIL + 1 ))
    _FAILURES+=("$label")
  fi
}

# assert_under "label" actual_seconds threshold_seconds
assert_under() {
  local label="$1" actual="$2" threshold="$3"
  local ok
  ok=$(awk -v a="$actual" -v t="$threshold" 'BEGIN { print (a+0 <= t+0) ? "1" : "0" }')
  if [[ "$ok" == "1" ]]; then
    printf "  \033[32mPASS\033[0m  %-60s (%ss < %ss)\n" "$label" "$actual" "$threshold"
    _PASS=$(( _PASS + 1 ))
  else
    printf "  \033[31mFAIL\033[0m  %-60s (%ss > %ss)\n" "$label" "$actual" "$threshold"
    _FAIL=$(( _FAIL + 1 ))
    _FAILURES+=("$label")
  fi
}

# assert_no_feed_errors "label" logfile
assert_no_feed_errors() {
  local label="$1" logfile="$2"
  local count
  count=$(grep -F '| error |' "$logfile" 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$count" -eq 0 ]]; then
    printf "  \033[32mPASS\033[0m  %s  (0 feed errors)\n" "$label"
    _PASS=$(( _PASS + 1 ))
  else
    printf "  \033[31mFAIL\033[0m  %s  (%s feed error(s) found)\n" "$label" "$count"
    grep -F '| error |' "$logfile" | sed 's/^/          /' >&2
    _FAIL=$(( _FAIL + 1 ))
    _FAILURES+=("$label")
  fi
}

# report_summary "suite name" — prints totals and returns exit code
report_summary() {
  local suite="$1"
  local total=$(( _PASS + _FAIL ))
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  if [[ $_FAIL -eq 0 ]]; then
    printf "  \033[32m%s: %d/%d passed\033[0m\n" "$suite" "$_PASS" "$total"
  else
    printf "  \033[31m%s: %d/%d passed, %d failed\033[0m\n" "$suite" "$_PASS" "$total" "$_FAIL"
    for f in "${_FAILURES[@]}"; do
      printf "    FAIL  %s\n" "$f"
    done
  fi
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  return $_FAIL
}
