import pytest
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_tpv import calcular_totales, procesar_venta
from unittest.mock import MagicMock
from copy import deepcopy
import hashlib
from datetime import datetime

# ==========================================
# TESTS PARA CALCULAR_TOTALES
# ==========================================

def test_calcular_totales_basico():
    carrito = [
        {"Precio": 10.0, "Cantidad": 2, "Subtotal": 20.0},
        {"Precio": 5.0, "Cantidad": 1, "Subtotal": 5.0}
    ]
    res = calcular_totales(carrito)
    
    assert res["subtotal_bruto"] == 25.0
    assert res["subtotal_lineas"] == 25.0
    assert res["total_final"] == 25.0
    assert res["puntos_usados"] == 0
    assert res["desc_puntos_eur"] == 0.0
    assert res["desc_vale_eur"] == 0.0

def test_calcular_totales_descuento_global():
    carrito = [{"Precio": 100.0, "Cantidad": 1, "Subtotal": 100.0}]
    res = calcular_totales(carrito, descuento_global_pct=10.0)
    
    assert res["subtotal_bruto"] == 100.0
    assert res["total_final"] == 90.0

def test_calcular_totales_uso_puntos():
    carrito = [{"Precio": 100.0, "Cantidad": 1, "Subtotal": 100.0}]
    # max descuento 50% = 50€. 50€ / 0.50€ = 100 pts max.
    # Tenemos 200 pts, usaremos 100 pts (50€).
    res = calcular_totales(carrito, puntos_disp=200, usar_puntos=True)
    
    assert res["total_final"] == 50.0
    assert res["desc_puntos_eur"] == 50.0
    assert res["puntos_usados"] == 100

def test_calcular_totales_deuda_bloquea_puntos():
    carrito = [{"Precio": 100.0, "Cantidad": 1, "Subtotal": 100.0}]
    # Si hay deuda, no se pueden usar puntos
    res = calcular_totales(carrito, puntos_disp=200, tiene_deuda=True, usar_puntos=True)
    
    assert res["total_final"] == 100.0
    assert res["desc_puntos_eur"] == 0.0
    assert res["puntos_usados"] == 0

def test_calcular_totales_uso_vale():
    carrito = [{"Precio": 100.0, "Cantidad": 1, "Subtotal": 100.0}]
    res = calcular_totales(carrito, saldo_vale=30.0)
    
    assert res["total_final"] == 70.0
    assert res["desc_vale_eur"] == 30.0

# ==========================================
# TESTS PARA PROCESAR_VENTA
# ==========================================

@pytest.fixture
def mock_supabase_client():
    client = MagicMock()
    
    # Configuramos el mock encadenado (client.table().select/update/insert().eq().execute())
    table_mock = MagicMock()
    client.table.return_value = table_mock
    
    op_mock = MagicMock()
    table_mock.insert.return_value = op_mock
    table_mock.update.return_value = op_mock
    table_mock.select.return_value = op_mock
    
    eq_mock = MagicMock()
    op_mock.eq.return_value = eq_mock
    
    # Mock para el insert que devuelve el ID del ticket
    insert_execute_mock = MagicMock()
    insert_execute_mock.data = [{"id": 999}]
    op_mock.execute.return_value = insert_execute_mock
    eq_mock.execute.return_value = insert_execute_mock
    
    return client

def test_procesar_venta_vacia(mock_supabase_client):
    carrito = []
    with pytest.raises(ValueError, match="vacío o contiene líneas no válidas"):
        procesar_venta(
            mock_supabase_client, carrito, 0.0, 0.0, 0.0, "Efectivo", 0.0, 0.0, 0.0, 0.0,
            None, 0, None, None, 0.0, False, "", {}
        )

def test_procesar_venta_efectivo_anonimo(mock_supabase_client):
    carrito = [{"id": "1", "Producto": "Collar", "Cantidad": 1, "Precio": 15.0, "Subtotal": 15.0}]
    
    res = procesar_venta(
        mock_supabase_client, carrito, total_f=15.0, pagado_hoy=15.0, pendiente=0.0,
        metodo_log="Efectivo", p_efectivo=15.0, p_tarjeta=0.0, p_bizum=0.0, desc_g_val=0.0,
        cliente_info=None, puntos_a_descontar=0, vale_aplicado=None, banco_sel_id=None,
        banco_sel_saldo=0.0, enviar_domicilio=False, dir_entrega="", cfg={}
    )
    
    assert res["id"] == 999
    assert res["total"] == 15.0
    assert res["metodo"] == "Efectivo"
    assert res["cliente_fidel"] == ""
    assert res["puntos_ganados"] == 0

def test_procesar_venta_fidelidad_suma_puntos(mock_supabase_client):
    carrito = [{"id": "1", "Producto": "Pienso", "Cantidad": 1, "Precio": 45.0, "Subtotal": 45.0}]
    cliente_info = {"id": 1, "nombre_dueno": "Juan", "puntos": 10, "email": "juan@test.com"}
    cfg = {"euros_para_un_punto": 10.0} # 45€ / 10 = 4 puntos ganados
    
    res = procesar_venta(
        mock_supabase_client, carrito, total_f=45.0, pagado_hoy=45.0, pendiente=0.0,
        metodo_log="Tarjeta", p_efectivo=0.0, p_tarjeta=45.0, p_bizum=0.0, desc_g_val=0.0,
        cliente_info=cliente_info, puntos_a_descontar=0, vale_aplicado=None, banco_sel_id=1,
        banco_sel_saldo=1000.0, enviar_domicilio=False, dir_entrega="", cfg=cfg
    )
    
    assert res["cliente_fidel"] == "Juan"
    assert res["puntos_ganados"] == 4
    assert res["nuevo_saldo"] == 14 # 10 act - 0 usados + 4 ganados
    assert res["email_cliente"] == "juan@test.com"

def test_procesar_venta_deuda_no_suma_puntos(mock_supabase_client):
    carrito = [{"id": "1", "Producto": "Pienso", "Cantidad": 1, "Precio": 45.0, "Subtotal": 45.0}]
    cliente_info = {"id": 1, "nombre_dueno": "Juan", "puntos": 10}
    cfg = {"euros_para_un_punto": 10.0}
    
    res = procesar_venta(
        mock_supabase_client, carrito, total_f=45.0, pagado_hoy=20.0, pendiente=25.0,
        metodo_log="Efectivo", p_efectivo=20.0, p_tarjeta=0.0, p_bizum=0.0, desc_g_val=0.0,
        cliente_info=cliente_info, puntos_a_descontar=0, vale_aplicado=None, banco_sel_id=None,
        banco_sel_saldo=0.0, enviar_domicilio=False, dir_entrega="", cfg=cfg
    )
    
    assert res["puntos_ganados"] == 0 # Deuda no suma puntos
    assert res["nuevo_saldo"] == 10

def test_procesar_venta_vale_aplicado(mock_supabase_client):
    carrito = [{"id": "1", "Producto": "Arnés", "Cantidad": 1, "Precio": 30.0, "Subtotal": 30.0}]
    vale = {"id": 1, "codigo_vale": "V-123", "saldo_actual": 50.0, "desc_vale_eur": 30.0}
    
    res = procesar_venta(
        mock_supabase_client, carrito, total_f=0.0, pagado_hoy=0.0, pendiente=0.0,
        metodo_log="Efectivo", p_efectivo=0.0, p_tarjeta=0.0, p_bizum=0.0, desc_g_val=0.0,
        cliente_info=None, puntos_a_descontar=0, vale_aplicado=vale, banco_sel_id=None,
        banco_sel_saldo=0.0, enviar_domicilio=False, dir_entrega="", cfg={}
    )
    
    assert res["desc_vale_eur"] == 30.0
    assert res["vale_aplicado"] == "V-123"
    assert "Vale (V-123)" in res["metodo"]
