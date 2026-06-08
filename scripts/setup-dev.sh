#!/usr/bin/env bash
set -euo pipefail

# setup-dev.sh — one-shot local dev bootstrap.
# Run from the app root: bash scripts/setup-dev.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$APP_DIR/docker-compose.dev.yml"
ENV_EXAMPLE="$APP_DIR/.env.dev.example"
ENV_FILE="$APP_DIR/.env"

# --- Validate tooling ---
if ! command -v docker &>/dev/null; then
  echo "ERROR: docker is not installed or not on PATH"
  exit 1
fi
if ! docker compose version &>/dev/null; then
  echo "ERROR: docker compose (v2) is required."
  exit 1
fi

# --- Validate local compose file ---
if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "ERROR: docker-compose.dev.yml not found."
  echo "Run /hive-ops-local-dev from the app root to generate it."
  exit 1
fi

# --- Set up .env ---
if [[ ! -f "$ENV_FILE" ]]; then
  if [[ -f "$ENV_EXAMPLE" ]]; then
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    echo "==> Copied .env.dev.example → .env"
    echo "    Fill in any 'changeme' values before continuing."
  else
    echo "ERROR: .env not found and no .env.dev.example to copy from."
    exit 1
  fi
else
  echo "==> Found existing .env — not overwriting."
fi

# --- Start services ---
echo "==> Starting local dev containers"
docker compose -f "$COMPOSE_FILE" up -d

echo ""
echo "==> Container status:"
docker compose -f "$COMPOSE_FILE" ps

echo ""
echo "==> Local dev is running. Check docker-compose.dev.yml for exposed ports."
echo "    To stop: docker compose -f docker-compose.dev.yml down"
