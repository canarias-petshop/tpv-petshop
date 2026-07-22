import pytest
import os
import sys
import time
import jwt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_inventario import (crear_producto, crear_servicio, traspasar_stock, 
                             actualizar_producto, eliminar_producto)
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

@pytest.fixture
def clean_db(db_client):
    """Limpia las tablas relacionadas con el inventario antes de cada test."""
    db_client.table("productos_proveedores").delete().neq("producto_id", "00000000-0000-0000-0000-000000000000").execute()
    db_client.table("productos").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    db_client.table("proveedores").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    
    # Crear un proveedor de prueba
    res_prov = db_client.table("proveedores").insert({"nombre_empresa": "Test Prov"}).execute()
    prov_id = res_prov.data[0]['id']
    return prov_id

def test_crear_producto(db_client, clean_db):
    prov_id = clean_db
    
    prod = crear_producto(
        db_client, "Saco Test", "SKU123", "123456789", 
        10.0, 7.0, 20.0, 5, 2, 5, [prov_id]
    )
    
    assert prod is not None
    assert prod['nombre'] == "Saco Test"
    assert prod['categoria'] == "Producto"
    assert prod['precio_base'] == 10.0

def test_crear_servicio(db_client, clean_db):
    serv = crear_servicio(db_client, "Corte de Pelo", "SERV01", 30.0, 7.0)
    
    assert serv is not None
    assert serv['categoria'] == "Servicio"
    # p_base_calc = 30 / 1.07 = 28.037
    assert round(serv['precio_base'], 2) == 28.04
    assert serv['precio_pvp'] == 30.0

def test_traspasar_stock(db_client, clean_db):
    caja = crear_producto(db_client, "Caja Latas", "CAJA01", "", 10.0, 7.0, 15.0, 10, 2, 5, [])
    unidad = crear_producto(db_client, "Lata Individual", "LATA01", "", 1.0, 7.0, 2.0, 5, 2, 5, [])
    
    res_tras = traspasar_stock(db_client, caja['id'], unidad['id'], 2, 12)
    
    # Verificamos
    assert res_tras['caja_nombre'] == "Caja Latas"
    assert res_tras['nuevo_stock_caja'] == 8
    assert res_tras['nuevo_stock_unidad'] == 29 # 5 + (2 * 12)

def test_actualizar_y_eliminar_producto(db_client, clean_db):
    prov_id = clean_db
    prod = crear_producto(db_client, "Update Test", "UP01", "", 5.0, 7.0, 10.0, 1, 1, 1, [])
    
    prod_upd = actualizar_producto(
        db_client, prod['id'], 
        {"nombre": "Update Done", "precio_pvp": 15.0}, 
        prov_id, 4.5
    )
    
    assert prod_upd is not None
    assert prod_upd['nombre'] == "Update Done"
    assert prod_upd['precio_pvp'] == 15.0
    
    # Comprobar eliminación
    eliminar_producto(db_client, prod['id'])
    res = db_client.table("productos").select("*").eq("id", prod['id']).execute()
    assert len(res.data) == 0

def test_errores_validacion(db_client, clean_db):
    with pytest.raises(ValueError, match="Nombre y SKU son obligatorios"):
        crear_producto(db_client, "", "SKU1", "", 1.0, 7.0, 2.0, 1, 1, 1, [])
        
    with pytest.raises(ValueError, match="Nombre y SKU son obligatorios"):
        crear_servicio(db_client, "", "S1", 10.0, 7.0)
        
    with pytest.raises(ValueError, match="Cantidades inválidas para traspaso"):
        traspasar_stock(db_client, 1, 2, 0, 12)
        
    with pytest.raises(ValueError, match="Uno o ambos productos no existen"):
        traspasar_stock(db_client, "ffffffff-ffff-ffff-ffff-ffffffffffff", "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee", 1, 12)
        
    caja = crear_producto(db_client, "Caja Vacia", "CAJA00", "", 10.0, 7.0, 15.0, 0, 2, 5, [])
    unidad = crear_producto(db_client, "Lata Vacia", "LATA00", "", 1.0, 7.0, 2.0, 0, 2, 5, [])
    
    with pytest.raises(ValueError, match="No hay suficiente stock de cajas para desempaquetar"):
        traspasar_stock(db_client, caja['id'], unidad['id'], 1, 12)
        
    with pytest.raises(ValueError, match="ID de producto inválido"):
        actualizar_producto(db_client, "", {})
        
    with pytest.raises(ValueError, match="ID de producto inválido"):
        eliminar_producto(db_client, "")
