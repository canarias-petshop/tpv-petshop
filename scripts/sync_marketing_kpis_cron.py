#!/usr/bin/env python3
"""
Sync nocturno de KPIs marketing (cron Docker, ~23:05 Atlantic/Canary).

Uso manual:
  python scripts/sync_marketing_kpis_cron.py
  python scripts/sync_marketing_kpis_cron.py --force

Variables de entorno:
  API_URL          PostgREST (def. http://animalarium-api:3000 en Docker)
  MKT_KPIS_CRON_ENABLED  true/false — desactiva ejecución
  MKT_KPIS_LOG     ruta log (def. logs/kpis_cron.log)
  MKT_KPIS_TARGET  local | prod (prod lee .streamlit/secrets.toml)
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from postgrest import SyncPostgrestClient

from core_marketing import sincronizar_objetivos_desde_tpv

TZ_CANARIAS = ZoneInfo("Atlantic/Canary")
LOCAL_JWT = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJyb2xlIjoiYWRtaW4iLCJpc3MiOiJzdXBhYmFzZSIsImlhdCI6MTc4NDQ3MTUyOCwiZXhwIjoxODE2MDA3NTI4fQ."
    "JVdkbQovJjMJeN-mbU29N2Z6Pc90iki7wsF_g2D8wXw"
)


def cron_habilitado() -> bool:
    return os.getenv("MKT_KPIS_CRON_ENABLED", "true").strip().lower() not in (
        "0", "false", "no", "off",
    )


def build_postgrest_client() -> SyncPostgrestClient:
    target = os.getenv("MKT_KPIS_TARGET", "local").strip().lower()
    if target == "prod":
        import tomllib
        secrets_path = ROOT / ".streamlit" / "secrets.toml"
        with open(secrets_path, "rb") as f:
            secrets = tomllib.load(f)
        raw = str(secrets.get("url", "")).strip().strip('"').strip("'").rstrip("/")
        key = str(secrets.get("key", "")).strip().strip('"').strip("'")
        if not raw or not key:
            raise RuntimeError("Faltan url/key en .streamlit/secrets.toml")
        api_url = raw if raw.endswith("/rest/v1") else f"{raw}/rest/v1"
        api_key = key
    else:
        api_url = os.getenv("API_URL", "http://animalarium-api:3000").rstrip("/")
        api_key = os.getenv("LOCAL_POSTGREST_KEY", LOCAL_JWT)
    return SyncPostgrestClient(
        api_url,
        headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"},
    )


def resumir_sync(resumen: list[dict]) -> str:
    n_ok = sum(1 for r in resumen if r.get("accion") == "actualizado")
    n_omit = sum(1 for r in resumen if r.get("accion") == "omitido")
    n_err = sum(1 for r in resumen if r.get("accion") == "error")
    return f"{n_ok} actualizado(s), {n_omit} omitido(s), {n_err} error(es)"


def run_sync(log_path: Path | None = None) -> list[dict]:
    ahora = datetime.now(TZ_CANARIAS).strftime("%Y-%m-%d %H:%M:%S %Z")
    client = build_postgrest_client()
    resumen = sincronizar_objetivos_desde_tpv(client)
    linea = f"[{ahora}] Sync KPIs cron: {resumir_sync(resumen)}"
    print(linea)
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(linea + "\n")
    return resumen


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync KPIs marketing (cron nocturno)")
    parser.add_argument("--force", action="store_true", help="Ejecutar aunque cron esté desactivado")
    args = parser.parse_args(argv)

    if not args.force and not cron_habilitado():
        print("Sync KPIs cron desactivado (MKT_KPIS_CRON_ENABLED=false)")
        return 0

    log_default = ROOT / "logs" / "kpis_cron.log"
    log_path = Path(os.getenv("MKT_KPIS_LOG", str(log_default)))

    try:
        run_sync(log_path=log_path)
        return 0
    except Exception as exc:
        err = f"ERROR sync KPIs cron: {exc}"
        print(err)
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(err + "\n")
        except OSError:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
