#!/usr/bin/env bash
# Runs every time the Codespace starts (including resumes from sleep).
# Brings the stack up in the background; logs are visible via:
#   docker compose logs -f
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose up -d

DOMAIN="${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}"
if [ -n "${CODESPACE_NAME:-}" ]; then
  echo ""
  echo "==========================================================="
  echo "  Pharma Connect is starting."
  echo ""
  echo "  Frontend:  https://${CODESPACE_NAME}-5173.${DOMAIN}"
  echo "  API docs:  https://${CODESPACE_NAME}-8000.${DOMAIN}/docs"
  echo ""
  echo "  Demo logins (password: Pass1234!):"
  echo "    alpha@pharma.local       Pharmacy"
  echo "    ibnsina@dist.local       Distributor"
  echo "    admin@pharma.local       Admin (password: AdminPass123!)"
  echo ""
  echo "  Tail logs:  docker compose logs -f"
  echo "==========================================================="
fi
