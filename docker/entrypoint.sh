#!/bin/sh
set -e

mkdir -p /app/logs

if [ "${MKT_KPIS_CRON_ENABLED:-true}" = "true" ]; then
  sed 's/\r$//' /app/docker/crontab | crontab -
  cron
  echo "Cron KPIs activo (23:05 Atlantic/Canary) — log: /app/logs/kpis_cron.log"
else
  echo "Cron KPIs desactivado (MKT_KPIS_CRON_ENABLED=false)"
fi

exec streamlit run app.py --server.port=8501 --server.address=0.0.0.0
