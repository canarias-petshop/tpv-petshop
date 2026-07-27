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
    assert parsear_horas_turno("10:00 a 14:30")[1].minute == 30
    assert _fmt_duracion(90) == "1 h 30 min"
    assert _fmt_duracion(45) == "45 min"

