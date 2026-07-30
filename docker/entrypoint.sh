#!/bin/sh
set -e

mkdir -p /app/logs

if [ "${MKT_KPIS_CRON_ENABLED:-true}" = "true" ]; then
  # Cron no hereda el ENV de Docker Compose: inyectar API_URL en la línea del job.
  API_URL_VAL="${API_URL:-http://animalarium-api:3000}"
  {
    echo "CRON_TZ=Atlantic/Canary"
    echo "5 23 * * * cd /app && API_URL=${API_URL_VAL} /usr/local/bin/python scripts/sync_marketing_kpis_cron.py >> /app/logs/kpis_cron.log 2>&1"
  } | crontab -
  cron
  echo "Cron KPIs activo (23:05 Atlantic/Canary) API_URL=${API_URL_VAL} — log: /app/logs/kpis_cron.log"
else
  echo "Cron KPIs desactivado (MKT_KPIS_CRON_ENABLED=false)"
fi

exec streamlit run app.py --server.port=8501 --server.address=0.0.0.0
