#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
compose=(docker compose --env-file infra/sandbox/.env -f infra/sandbox/compose.yaml)
"${compose[@]}" exec -T --user hermes hermes-sandbox python /workspace/trading-agent/scripts/verify-agent.py
"${compose[@]}" exec -T kis-proxy python - < scripts/verify-proxy.py
"${compose[@]}" exec -T --user hermes hermes-sandbox python -m trading_agent.cli status
