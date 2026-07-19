import sys
import os
import pytest
from datetime import datetime, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from caja import abrir_caja, registrar_movimiento_caja, cerrar_caja, fetch_caja_abierta, fetch_movimientos_caja, limpiar_cache_caja
from postgrest import SyncPostgrestClient
import jwt
import time

@pytest.fixture(scope="module")
def db_client():
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

def test_flujo_completo_caja(db_client):
    # Limpiar estado previo
    db_client.table("control_caja").delete().neq("id", -1).execute()
    db_client.table("movimientos_caja").delete().neq("id", -1).execute()

    # 1. Abrir caja
    fondo_inicial = 150.0
    abrir_caja(db_client, fondo_inicial)
    
    # Comprobar que está abierta
    res = fetch_caja_abierta(db_client)
    assert len(res.data) == 1
    caja_id = res.data[0]['id']
    fecha_apertura = res.data[0]['created_at']
    
    # 2. Registrar movimientos
    registrar_movimiento_caja(db_client, caja_id, "Ingreso", 50.0, "Cambio")
    registrar_movimiento_caja(db_client, caja_id, "Retirada", 20.0, "Pago proveedor")
    
    movs = fetch_movimientos_caja(db_client, caja_id)
    assert len(movs.data) >= 2
    
    # 3. Cerrar caja
    # No hay ventas registradas en el test para esta fecha de apertura, así que ventas = 0
    # Efectivo teórico = 150 (fondo) + 50 (ingreso) - 20 (retirada) = 180
    efectivo_final_real = 180.0
    descuadre = cerrar_caja(db_client, caja_id, fondo_inicial, fecha_apertura, efectivo_final_real)
    
    assert descuadre == 0.0
    
    limpiar_cache_caja()
    
    # Comprobar que ya no está abierta
    res_cerrada = fetch_caja_abierta(db_client)
    assert len(res_cerrada.data) == 0


def test_caja_cobertura(db_client):
    from caja import fetch_ventas_historial_desde, limpiar_cache_caja
    fetch_ventas_historial_desde(db_client, '2020-01-01T00:00:00Z')
    limpiar_cache_caja()
