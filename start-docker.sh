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
docker compose up -d --build
echo "VMESH-only MiniPool started. Full node sync takes time."
echo "Dashboard: http://127.0.0.1:8686"
echo "Stratum: 127.0.0.1:3938 (default local only)"
echo "LAN Bitaxe / NPM: see docs/DOCKER.de.md"
echo "Logs: docker compose logs --tail=70 -f"
