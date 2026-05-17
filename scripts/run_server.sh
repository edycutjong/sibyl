#!/usr/bin/env bash
# Sibyl — Launch the forecasting agent server
set -euo pipefail

PORT="${PORT:-8001}"
echo "🔮 Starting Sibyl on port ${PORT}..."
exec uvicorn sibyl.server:app --host 0.0.0.0 --port "${PORT}" --log-level info
