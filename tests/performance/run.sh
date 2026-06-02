#!/usr/bin/env bash
# run.sh — runs both performance test suites and reports overall pass/fail.
# Usage: bash tests/performance/run.sh
# Exit code: 0 = all tests passed, 1 = one or more tests failed.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

SCRIPTS_RC=0
API_RC=0

bash "$REPO_ROOT/tests/performance/test_scripts.sh" || SCRIPTS_RC=$?
bash "$REPO_ROOT/tests/performance/test_api.sh"     || API_RC=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ $SCRIPTS_RC -eq 0 && $API_RC -eq 0 ]]; then
  printf "  \033[32mALL PERFORMANCE TESTS PASSED\033[0m\n"
else
  printf "  \033[31mPERFORMANCE TESTS FAILED\033[0m"
  [[ $SCRIPTS_RC -ne 0 ]] && printf "  (CLI scripts)" || true
  [[ $API_RC -ne 0 ]]     && printf "  (API endpoints)" || true
  printf "\n"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit $(( SCRIPTS_RC | API_RC ))
