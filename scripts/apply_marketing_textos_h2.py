#!/usr/bin/env python3
"""
Aplica SOLO contenido_detallado enriquecido del H2 2026.

- No borra filas.
- No cambia objetivo_id, presupuesto, canal, tema, fecha ni estado.
- Empareja por (fecha_planificada, canal, tema).
- Por defecto: local + dry-run.

Uso:
  python scripts/apply_marketing_textos_h2.py              # dry-run local
  python scripts/apply_marketing_textos_h2.py --apply      # escribe local
  python scripts/apply_marketing_textos_h2.py --prod --apply
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "scripts" / "data" / "marketing_h2_2026_textos_enriquecidos.json"

API = "http://localhost:3001"
AUTH_HEADERS: dict[str, str] = {}


def configure_target(prod: bool) -> str:
    global API, AUTH_HEADERS
    if not prod:
        API = "http://localhost:3001"
        AUTH_HEADERS = {}
        return "local"
    import tomllib

    secrets_path = ROOT / ".streamlit" / "secrets.toml"
    with open(secrets_path, "rb") as f:
        secrets = tomllib.load(f)
    raw = str(secrets.get("url", "")).strip().strip('"').strip("'").rstrip("/")
    key = str(secrets.get("key", "")).strip().strip('"').strip("'")
    if not raw or not key:
        raise SystemExit("Faltan url/key en .streamlit/secrets.toml para producción.")
    API = raw if raw.endswith("/rest/v1") else f"{raw}/rest/v1"
    AUTH_HEADERS = {"apikey": key, "Authorization": f"Bearer {key}"}
    return "production"


def api(method: str, path: str, body: Optional[Any] = None, prefer: Optional[str] = None) -> Any:
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": "application/json", **AUTH_HEADERS}
    if prefer:
        headers["Prefer"] = prefer
    req = urllib.request.Request(f"{API}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {e.code} {path}: {err}") from e


def key_of(fecha: str, canal: str, tema: str) -> tuple[str, str, str]:
    return (str(fecha)[:10], canal or "", tema or "")


def main() -> None:
    parser = argparse.ArgumentParser(description="Actualiza solo contenido_detallado H2")
    parser.add_argument("--prod", "--production", action="store_true")
    parser.add_argument("--apply", action="store_true", help="Escribe cambios (sin esto = dry-run)")
    parser.add_argument("--data", type=Path, default=DATA)
    args = parser.parse_args()

    if not args.data.exists():
        raise SystemExit(f"No existe {args.data}")

    payload = json.loads(args.data.read_text(encoding="utf-8"))
    incoming = payload.get("rows") or []
    target = configure_target(args.prod)
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[{mode}] destino={target} filas_json={len(incoming)}")

    remote = api(
        "GET",
        "/marketing_plan?fecha_planificada=gte.2026-08-01"
        "&select=id,fecha_planificada,canal,tema,contenido_detallado,objetivo_id"
        "&order=fecha_planificada",
    ) or []
    by_key = {key_of(r["fecha_planificada"], r.get("canal") or "", r.get("tema") or ""): r for r in remote}

    matched = missing = unchanged = updated = 0
    obj_mismatch = 0
    for row in incoming:
        k = key_of(row["fecha_planificada"], row.get("canal") or "", row.get("tema") or "")
        cur = by_key.get(k)
        if not cur:
            missing += 1
            print(f"  FALTA en {target}: {k[0]} | {k[2][:60]}")
            continue
        matched += 1
        # aviso si objetivo distinto (no bloquea; el JSON guarda el de local)
        if row.get("objetivo_id") is not None and cur.get("objetivo_id") is not None:
            if row["objetivo_id"] != cur["objetivo_id"]:
                obj_mismatch += 1
        new_text = row.get("contenido_detallado") or ""
        old_text = cur.get("contenido_detallado") or ""
        if new_text == old_text:
            unchanged += 1
            continue
        if args.apply:
            api(
                "PATCH",
                f"/marketing_plan?id=eq.{cur['id']}",
                {"contenido_detallado": new_text},
                prefer="return=minimal",
            )
        updated += 1

    print(
        f"OK matched={matched} update={updated} unchanged={unchanged} "
        f"missing={missing} objetivo_id_diff={obj_mismatch}"
    )
    if missing:
        print("AVISO: hay filas del JSON que no existen en el destino (no se insertan).")
    if not args.apply:
        print("Dry-run: no se escribió nada. Repite con --apply para aplicar.")
        sys.exit(0 if missing == 0 else 2)


if __name__ == "__main__":
    main()
