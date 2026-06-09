#!/usr/bin/env bash
set -euo pipefail

# deploy.sh — deploy or update a hive-ops standard app.
# Run from the app's directory (/home/deploy/<app>/):
#   bash scripts/deploy.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# --- Load .env ---
ENV_FILE="$APP_DIR/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: .env not found at $ENV_FILE"
  echo "Copy .env.example to .env and fill in all values."
  exit 1
fi
# shellcheck disable=SC1090
source "$ENV_FILE"

APP_NAME="${APP_NAME:?APP_NAME must be set in .env}"
STORAGE_PATH="${STORAGE_PATH:-/home/deploy}"
DEPLOY_ROOT="$STORAGE_PATH/$APP_NAME"

echo "==> Deploying $APP_NAME from $APP_DIR"

# --- Validate tooling ---
if ! command -v docker &>/dev/null; then
  echo "ERROR: docker is not installed or not on PATH"
  exit 1
fi
if ! docker compose version &>/dev/null; then
  echo "ERROR: docker compose (v2) is required. 'docker-compose' (v1) is not supported."
  exit 1
fi

# --- Create standard directory layout ---
echo "==> Creating directory layout under $DEPLOY_ROOT"
mkdir -p \
  "$DEPLOY_ROOT/data" \
  "$DEPLOY_ROOT/backups" \
  "$DEPLOY_ROOT/logs" \
  "$DEPLOY_ROOT/scripts" \
  "$DEPLOY_ROOT/nginx"

# --- Validate compose file ---
echo "==> Validating docker-compose.yml"
docker compose -f "$APP_DIR/docker-compose.yml" config --quiet

# --- Pull latest images ---
echo "==> Pulling images"
docker compose -f "$APP_DIR/docker-compose.yml" pull

# --- Start / update services ---
echo "==> Starting services"
docker compose -f "$APP_DIR/docker-compose.yml" up -d --remove-orphans

# --- Report status ---
echo ""
echo "==> Container status:"
docker compose -f "$APP_DIR/docker-compose.yml" ps

echo ""
echo "==> Deploy complete. Run 'bash scripts/healthcheck.sh' to verify health."

# --- App-specific post-deploy hook ---
if [[ -f "$SCRIPT_DIR/deploy.local.sh" ]]; then
  echo "==> Running app-specific hook (scripts/deploy.local.sh)"
  bash "$SCRIPT_DIR/deploy.local.sh"
fi
