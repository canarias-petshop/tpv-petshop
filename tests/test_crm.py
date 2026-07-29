import pytest
import os
import sys
import time
import jwt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_crm import (crear_cliente, crear_mascota, actualizar_cliente, 
                      anonimizar_cliente, crear_encargo, agendar_cita,
                      registrar_recogida_desde_cita)
from postgrest import SyncPostgrestClient

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

def test_crear_cliente_y_mascota(db_client):
    db_client.table("mascotas").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    db_client.table("clientes").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    
    nuevo_cli = crear_cliente(
        db_client, "Juan Perez", "600123456", email="juan@perez.com"
    )
    assert nuevo_cli is not None
    assert nuevo_cli['nombre_dueno'] == "Juan Perez"
    
    cli_id = nuevo_cli['id']
    
    nueva_masc = crear_mascota(
        db_client, cli_id, "Rex", especie="Perro", raza="Pastor Alemán"
    )
    assert nueva_masc is not None
    assert nueva_masc['nombre'] == "Rex"
    assert nueva_masc['cliente_id'] == cli_id

def test_anonimizar_cliente(db_client):
    cli = crear_cliente(db_client, "Anonimizar Test", "699999999", email="test@test.com")
    cli_id = cli['id']
    
    cli_anon = anonimizar_cliente(db_client, cli_id)
    assert cli_anon is not None
    assert cli_anon['nombre_dueno'] == "Cliente Borrado"
    assert cli_anon['telefono'] == ""
    assert cli_anon['email'] == ""
    assert cli_anon['rgpd_consent'] is False

def test_actualizar_cliente(db_client):
    cli = crear_cliente(db_client, "Pedro", "611222333")
    cli_id = cli['id']
    
    cli_upd = actualizar_cliente(db_client, cli_id, {"telefono": "677888999", "puntos": 50})
    assert cli_upd is not None
    assert cli_upd['telefono'] == "677888999"
    assert cli_upd['puntos'] == 50

def test_crear_encargo(db_client):
    db_client.table("encargos_clientes").delete().neq("id", 0).execute()
    encargo = crear_encargo(db_client, "Maria", "655444333", "Saco Pienso 12kg", 2, "Llamar cuando llegue")
    assert encargo is not None
    assert encargo['nombre_cliente'] == "Maria"
    assert encargo['detalle_pedido'] == "2x Saco Pienso 12kg"
    assert encargo['estado'] == "Pendiente"

def test_agendar_cita(db_client):
    db_client.table("citas").delete().neq("id", 0).execute()
    
    cli = crear_cliente(db_client, "Cita Test", "600000000")
    masc = crear_mascota(db_client, cli['id'], "Firulais")
    
    cita = agendar_cita(
        db_client, masc['id'], "2026-07-20", "10:00", 
        "Peluquería", 60, peluquero="Ana", forzado=True, motivo_forzado="Urgent", fianza_pagada=True
    )
    assert cita is not None
    assert "FIANZA PAGADA" in cita['servicio']
    assert "Ana" in cita['servicio']
    assert cita['duracion_minutos'] == 60
    assert "2026-07-20T10:00" in cita['fecha_hora']

def test_agendar_cita_con_recogida_actualiza_cliente(db_client):
    """Al agendar con recogida: estado pendiente de recogida, servicio creado y ficha actualizada."""
    db_client.table("citas").delete().neq("id", 0).execute()
    try:
        db_client.table("servicios_recogida").delete().neq("id", 0).execute()
    except Exception:
        pass

    cli = crear_cliente(db_client, "Sin Domicilio", "611111111", direccion="", servicio_domicilio=False)
    masc = crear_mascota(db_client, cli['id'], "Rocky")

    cita = agendar_cita(
        db_client, masc['id'], "2026-07-21", "11:30",
        "Peluquería", 45, peluquero="Lucia",
        recogida=True, direccion_recogida="Calle Test 12, La Laguna",
        cliente_id=cli['id'], nombre_cliente=cli['nombre_dueno'],
        telefono=cli['telefono'], nombre_mascota=masc['nombre']
    )
    assert cita is not None
    assert "Servicio de recogida pendiente" in cita['servicio']

    cli_upd = db_client.table("clientes").select("direccion, servicio_domicilio").eq("id", cli['id']).execute().data[0]
    assert cli_upd["servicio_domicilio"] is True
    assert "Calle Test 12" in str(cli_upd.get("direccion") or "")

    recos = db_client.table("servicios_recogida").select("*").eq("mascota", "Rocky").execute().data
    assert recos, "Debe crearse el servicio de recogida"
    assert "Calle Test 12" in str(recos[0].get("direccion") or "")

def test_registrar_recogida_desde_cita_sin_mascota(db_client):
    with pytest.raises(ValueError, match="Falta el ID de la mascota"):
        registrar_recogida_desde_cita(db_client, "", "2026-07-21", "10:00")


def test_registrar_recogida_mascota_inexistente(db_client):
    with pytest.raises(ValueError, match="No se encontró la mascota"):
        registrar_recogida_desde_cita(
            db_client, "00000000-0000-0000-0000-999999999999", "2026-07-21", "10:00"
        )


def test_agendar_cita_recogida_rollback_si_falla_cascada(db_client, monkeypatch):
    """Si falla registrar_recogida_desde_cita, se borra la cita huérfana."""
    import core_crm as crm_mod

    db_client.table("citas").delete().neq("id", 0).execute()
    cli = crear_cliente(db_client, "Rollback Recogida", "622222222")
    masc = crear_mascota(db_client, cli["id"], "Nala")

    def boom(**kwargs):
        raise RuntimeError("fallo cascada recogida")

    monkeypatch.setattr(crm_mod, "registrar_recogida_desde_cita", boom)
    with pytest.raises(RuntimeError, match="fallo cascada"):
        agendar_cita(
            db_client, masc["id"], "2026-08-01", "12:00",
            "Peluquería", 30, recogida=True, direccion_recogida="Calle X 1",
        )
    citas = db_client.table("citas").select("id").eq("mascotas_id", masc["id"]).execute().data
    assert citas == []

def test_errores_validacion(db_client):
    with pytest.raises(ValueError, match="El nombre del dueño es obligatorio"):
        crear_cliente(db_client, "", "123")
        
    with pytest.raises(ValueError, match="El nombre de la mascota es obligatorio"):
        crear_mascota(db_client, "id-dummy", "")
        
    with pytest.raises(ValueError, match="El ID del cliente es obligatorio"):
        crear_mascota(db_client, "", "Pipo")
        
    with pytest.raises(ValueError, match="ID de cliente inválido"):
        actualizar_cliente(db_client, "", {"puntos": 10})
        
    with pytest.raises(ValueError, match="ID de cliente inválido"):
        anonimizar_cliente(db_client, "")
        
    with pytest.raises(ValueError, match="Nombre de cliente y producto son obligatorios"):
        crear_encargo(db_client, "", "123", "Pienso", 1)
        
    with pytest.raises(ValueError, match="Faltan datos obligatorios para la cita"):
        agendar_cita(db_client, "", "2026-07-20", "10:00", "Serv", 60)
