#!/usr/bin/env bash
# One command VMESH Docker start: VMESH Core + Stratum + Dashboard.
set -Eeuo pipefail
cd "$(dirname "$0")"
if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
  echo "Docker Engine + Compose plugin required: https://docs.docker.com/engine/install/" >&2
  exit 1
fi
if [[ "$(uname -m)" != "x86_64" ]]; then
  echo "Current pinned official Core archive supports Linux x86_64 only." >&2
  exit 1
fi
if [[ ! -f .env ]]; then
  cp .env.example .env
  chmod 600 .env
fi
docker compose config --quiet
# Read the effective bindings from .env without executing .env as shell code.
STRATUM_BIND="$(docker compose config --format json | python3 -c 'import json,sys; d=json.load(sys.stdin); p=d["services"]["minipool"]["ports"]; print(next(x["host_ip"] for x in p if x["target"]==3938))')"
WEB_BIND="$(docker compose config --format json | python3 -c 'import json,sys; d=json.load(sys.stdin); p=d["services"]["minipool"]["ports"]; print(next(x["host_ip"] for x in p if x["target"]==8686))')"
if [[ "$WEB_BIND" == "0.0.0.0" ]]; then
  if ! grep -Eq '^MINIPOOL_DASHBOARD_ALLOWED_HOSTS=[^[:space:]]+' .env; then
    echo "ERROR: Public web bind requires MINIPOOL_DASHBOARD_ALLOWED_HOSTS=public-ip-or-domain in .env." >&2
    exit 1
  fi
  echo "WARNING: Public HTTP dashboard has NO built-in authentication/TLS; use a reverse proxy with HTTPS + authentication."
fi
if [[ "$STRATUM_BIND" == "0.0.0.0" ]]; then
  echo "WARNING: Public Stratum V1 is unencrypted and has no authentication or rate limiting."
fi
docker compose up -d --build
echo "VMESH-only MiniPool started. Full node sync takes time."
echo "Dashboard host bind: $WEB_BIND:8686"
echo "Stratum host bind: $STRATUM_BIND:3938"
echo "Public deployment guide: docs/PUBLIC-DEPLOYMENT.en.md"
echo "LAN Bitaxe / NPM: see docs/DOCKER.de.md"
echo "Logs: docker compose logs --tail=70 -f"
