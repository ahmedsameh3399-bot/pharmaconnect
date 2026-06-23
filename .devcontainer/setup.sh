#!/usr/bin/env bash
# One-time setup: generate .env with the Codespace-derived URLs and pre-build
# the Docker images so the first `docker compose up` is fast.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  cp .env.example .env

  # In Codespaces these two env vars are set automatically. We rewrite
  # CORS_ORIGINS and VITE_API_BASE_URL to the actual forwarded URLs so the
  # browser (which sees app.github.dev, not localhost) can reach the API.
  if [ -n "${CODESPACE_NAME:-}" ]; then
    DOMAIN="${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}"
    FRONTEND_URL="https://${CODESPACE_NAME}-5173.${DOMAIN}"
    BACKEND_URL="https://${CODESPACE_NAME}-8000.${DOMAIN}"

    sed -i "s|^VITE_API_BASE_URL=.*|VITE_API_BASE_URL=${BACKEND_URL}|" .env
    sed -i "s|^CORS_ORIGINS=.*|CORS_ORIGINS=${FRONTEND_URL}|" .env

    echo "Configured .env for Codespace ${CODESPACE_NAME}:"
    echo "  Frontend:  ${FRONTEND_URL}"
    echo "  Backend:   ${BACKEND_URL}"
  else
    echo "Configured .env with localhost defaults."
  fi
else
  echo ".env already exists; leaving it untouched."
fi

echo "Pre-building Docker images (one-time)..."
docker compose build

echo "Setup done. The stack will start automatically next."
