#!/usr/bin/env bash
set -euo pipefail

if docker compose version >/dev/null 2>&1; then
  docker compose down --remove-orphans
elif command -v docker-compose >/dev/null 2>&1; then
  docker-compose down --remove-orphans
else
  echo "docker compose is not available" >&2
  exit 1
fi
