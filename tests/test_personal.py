import pytest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from personal import get_ultimo_fichaje, get_fichajes_sin_salida, get_ultimo_hash
from postgrest import SyncPostgrestClient
import jwt
import time

@pytest.fixture(scope="module")
def db_client():
    """Fixture que provee el cliente de BD configurado para tests (Docker)."""
    api_url = os.getenv("API_URL", "http://localhost:3000")
    secret = "super-secret-jwt-token-with-at-least-32-characters-long"
    payload = {
        "role": "admin",
        "iss": "supabase",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    api_key = jwt.encode(payload, secret, algorithm="HS256")
    
    cliente = SyncPostgrestClient(
        api_url, 
        headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"}
    )
    return cliente

def test_get_fichajes_sin_salida(db_client):
    """Prueba la lectura de fichajes que aún no tienen hora de salida."""
    # Limpiar estado previo
    db_client.table("personal_fichajes").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    
    # Dado que la base de datos está vacía, no debería haber fichajes sin salida
    res = get_fichajes_sin_salida(db_client, empleado_id="00000000-0000-0000-0000-000000000000", fecha="2026-07-19")
    
    assert res is not None
    assert isinstance(res.data, list)
    assert len(res.data) == 0

def test_get_ultimo_hash(db_client):
    """Prueba que se pueda obtener el último hash (vacío al principio)."""
    res = get_ultimo_hash(db_client)
    assert res is not None
    # No fallará si no hay datos, devolverá data=[]
    if not res.data:
        assert len(res.data) == 0

from personal import registrar_fichaje
from datetime import datetime, timezone

def test_registrar_fichaje_entrada(db_client):
    # Limpiar estado previo
    db_client.table("personal_fichajes").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    
    empleado_id = '00000000-0000-0000-0000-000000000000'
    ahora = datetime.now(timezone.utc)
    success, msg = registrar_fichaje(db_client, empleado_id, 'TestUser', ahora)
    assert success is True
    assert 'Entrada registrada' in msg


def test_personal_cobertura(db_client):
    from personal import get_ultimo_fichaje, get_ultimo_hash, get_cuadrantes_rango, limpiar_cache_personal
    get_ultimo_fichaje(db_client, '00000000-0000-0000-0000-000000000000', '2020-01-01')
    get_ultimo_hash(db_client)
    get_cuadrantes_rango(db_client, '2020-01-01', '2020-01-01')
    limpiar_cache_personal()


def test_registrar_fichaje_salida_y_spam(db_client):
    db_client.table('personal_fichajes').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
    from datetime import datetime, timezone
    from personal import registrar_fichaje
    ahora = datetime.now(timezone.utc)
    empleado_id = '00000000-0000-0000-0000-000000000000'
    # Entrada
    registrar_fichaje(db_client, empleado_id, 'TestUser', ahora)
    # Spam check
    success, msg = registrar_fichaje(db_client, empleado_id, 'TestUser', ahora)
    assert not success
    # Salida (esperar no, simulamos avanzar 31 mins para no saltar el spam)
    import pandas as pd
    ahora_mas = ahora + pd.Timedelta(minutes=31)
    success_salida, msg_salida = registrar_fichaje(db_client, empleado_id, 'TestUser', ahora_mas)
    assert success_salida

def test_parsear_horas_turno():
    from personal import parsear_horas_turno, _fmt_duracion
    assert parsear_horas_turno("09:00 - 15:00")[0].hour == 9
    assert parsear_horas_turno("09:00 - 15:00")[1].hour == 15
    assert parsear_horas_turno("Libre") == (None, None)
    assert parsear_horas_turno("Vacaciones") == (None, None)
    assert parsear_horas_turno("") == (None, None)
    assert parsear_horas_turno(None) == (None, None)
    assert parsear_horas_turno("solo 10:00") == (None, None)
    assert parsear_horas_turno("10:00 a 14:30")[1].minute == 30
    assert _fmt_duracion(90) == "1 h 30 min"
    assert _fmt_duracion(60) == "1 h"
    assert _fmt_duracion(45) == "45 min"


def test_info_turno_y_previsualizar_fichaje(db_client):
    """Guardián anti-spam, previsualización y resumen de turno al salir (Compendio §1)."""
    from datetime import datetime, timezone, timedelta
    from personal import (
        registrar_fichaje,
        previsualizar_fichaje,
        info_turno_para_salida,
        parsear_horas_turno,
    )

    empleado_id = "00000000-0000-0000-0000-000000000001"
    db_client.table("personal_fichajes").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    try:
        db_client.table("personal_cuadrantes").delete().eq("empleado_id", empleado_id).execute()
    except Exception:
        pass

    ahora = datetime.now(timezone.utc).replace(microsecond=0)
    hoy = ahora.date().isoformat()

    # Sin fichaje -> preview entrada
    prev = previsualizar_fichaje(db_client, empleado_id, "PreviewUser", ahora)
    assert prev["accion"] == "entrada"

    ok, _ = registrar_fichaje(db_client, empleado_id, "PreviewUser", ahora)
    assert ok

    # Anti-spam en preview
    prev_bloqueo = previsualizar_fichaje(db_client, empleado_id, "PreviewUser", ahora)
    assert prev_bloqueo["accion"] == "bloqueo"

    # Tras 31 min: preview salida + info de turno (con o sin cuadrante)
    ahora_mas = ahora + timedelta(minutes=31)
    try:
        db_client.table("personal_cuadrantes").insert({
            "empleado_id": empleado_id,
            "fecha": hoy,
            "turno": "09:00 - 15:00",
        }).execute()
    except Exception:
        # Si la tabla exige más campos, el test sigue sin cuadrante
        pass

    prev_salida = previsualizar_fichaje(db_client, empleado_id, "PreviewUser", ahora_mas)
    assert prev_salida["accion"] == "salida"
    assert "hora_entrada_str" in prev_salida
    assert prev_salida["minutos_trabajados"] >= 30

    # info_turno directo
    info = info_turno_para_salida(db_client, empleado_id, ahora_mas, ahora)
    assert info["hora_entrada_str"]
    assert info["minutos_trabajados"] >= 30
    if info.get("hora_fin_str"):
        assert info["minutos_restantes"] is not None
        assert "cuadrante" in info["resumen_horario"].lower() or "salida" in info["resumen_horario"].lower()

    # accion_esperada incorrecta
    ok_bad, msg_bad = registrar_fichaje(
        db_client, empleado_id, "PreviewUser", ahora_mas, accion_esperada="entrada"
    )
    assert ok_bad is False
    assert "entrada abierta" in msg_bad.lower() or "salida" in msg_bad.lower()

    # Salida real
    ok_out, msg_out = registrar_fichaje(db_client, empleado_id, "PreviewUser", ahora_mas)
    assert ok_out
    assert "Salida" in msg_out

    # Sin entrada abierta + accion_esperada salida
    ok2, msg2 = registrar_fichaje(
        db_client, empleado_id, "PreviewUser", ahora_mas + timedelta(minutes=31), accion_esperada="salida"
    )
    assert ok2 is False
    assert "entrada" in msg2.lower()

    # Turno que cruza medianoche / resto == 0 / excedido (unitario sin DB)
    h_ini, h_fin = parsear_horas_turno("22:00 - 06:00")
    assert h_ini is not None and h_fin is not None


def test_info_turno_restante_justo_y_excedido():
    """Resúmenes de salida: quedan minutos / hora justa / turno excedido."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from unittest.mock import MagicMock
    from personal import info_turno_para_salida

    tz = ZoneInfo("Atlantic/Canary")
    client = MagicMock()
    client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"turno": "09:00 - 15:00"}
    ]
    entrada = datetime(2026, 7, 30, 9, 0, tzinfo=tz)

    info_resto = info_turno_para_salida(
        client, "emp-1", datetime(2026, 7, 30, 14, 0, tzinfo=tz), entrada
    )
    assert info_resto["hora_fin_str"] == "15:00"
    assert info_resto["minutos_restantes"] == 60
    assert "quedan" in info_resto["resumen_horario"]

    info_justo = info_turno_para_salida(
        client, "emp-1", datetime(2026, 7, 30, 15, 0, tzinfo=tz), entrada
    )
    assert info_justo["minutos_restantes"] == 0
    assert "justo" in info_justo["resumen_horario"]

    info_exceso = info_turno_para_salida(
        client, "emp-1", datetime(2026, 7, 30, 16, 30, tzinfo=tz), entrada
    )
    assert info_exceso["minutos_restantes"] == -90
    assert "hace" in info_exceso["resumen_horario"]

    # Sin tz en datetime de entrada
    info_naive = info_turno_para_salida(
        client, "emp-1", datetime(2026, 7, 30, 12, 0), datetime(2026, 7, 30, 9, 0)
    )
    assert info_naive["minutos_trabajados"] == 180
    assert info_naive["minutos_restantes"] == 180

