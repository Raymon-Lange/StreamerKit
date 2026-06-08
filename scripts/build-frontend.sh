#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"
FRONTEND_DIR="$REPO_ROOT/frontend"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: $ENV_FILE not found" >&2
  exit 1
fi

API_KEY="$(grep -E '^API_KEY=' "$ENV_FILE" | cut -d= -f2- | tr -d '"' | tr -d "'")"
if [[ -z "$API_KEY" ]]; then
  echo "ERROR: API_KEY not set in $ENV_FILE" >&2
  exit 1
fi

echo "Building frontend with API key from .env..."
cd "$FRONTEND_DIR"
VITE_API_KEY="$API_KEY" npm run build
echo "Done. Output: frontend/dist/"
