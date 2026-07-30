#!/bin/sh
# Replica local del job CI (requiere Docker).
set -e
cd "$(dirname "$0")/.."

echo "==> Docker: db + postgrest"
docker compose up -d db postgrest

echo "==> Esperando PostgREST..."
for i in $(seq 1 45); do
  if curl -sf "http://localhost:3001/" >/dev/null 2>&1; then
    echo "PostgREST OK"
    break
  fi
  sleep 2
done

export API_URL=http://localhost:3001

if [ -x ".venv/Scripts/python.exe" ]; then
  PY=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  PY=python3
fi

echo "==> pytest"
"$PY" -m pytest tests/ -v --tb=short --junitxml=pytest-results.xml

echo "==> smoke sync KPIs"
"$PY" scripts/sync_marketing_kpis_cron.py --force

echo "==> CI local OK — ver pytest-results.xml"
