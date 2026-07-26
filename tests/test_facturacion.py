import pytest
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_facturacion import (emitir_factura_cliente, registrar_compra_borrador, registrar_pago_deuda)
from unittest.mock import MagicMock

@pytest.fixture
def mock_supabase_client():
    client = MagicMock()
    
    table_mock = MagicMock()
    client.table.return_value = table_mock
    
    op_mock = MagicMock()
    table_mock.insert.return_value = op_mock
    table_mock.update.return_value = op_mock
    table_mock.select.return_value = op_mock
    
    eq_mock = MagicMock()
    op_mock.eq.return_value = eq_mock
    
    insert_execute_mock = MagicMock()
    insert_execute_mock.data = [{"id": 999, "stock_actual": 10, "saldo_actual": 100.0, "pendiente": 50.0, "pagado": 10.0, "total": 60.0}]
    
    op_mock.execute.return_value = insert_execute_mock
    eq_mock.execute.return_value = insert_execute_mock
    
    return client

def test_emitir_factura_cliente(mock_supabase_client):
    productos = [{"id": 1, "Cantidad": 2}]
    res = emitir_factura_cliente(
        mock_supabase_client,
        cliente_id=1,
        total_neto=20.0,
        total_igic=1.4,
        total_final=21.4,
        descuento_global=0.0,
        forma_pago="Efectivo",
        fecha_vencimiento="2026-12-31",
        productos=productos
    )
    assert res["id"] == 999
    
def test_emitir_factura_vacia(mock_supabase_client):
    with pytest.raises(ValueError, match="sin productos"):
        emitir_factura_cliente(mock_supabase_client, 1, 0, 0, 0, 0, "Ef", "2026", [])

def test_registrar_compra_borrador_nuevo(mock_supabase_client):
    # Mocking that there is NO duplicate
    mock_supabase_client.table().select().eq().eq().execute().data = []
    
    productos = [{"id": 1, "Cantidad": 5}]
    res = registrar_compra_borrador(
        mock_supabase_client,
        proveedor_id=1,
        num_fac="F-001",
        es_abono=False,
        productos=productos,
        dto_pp=0.0,
        fecha_fac="2026-07-19",
        total=100.0
    )
    assert res["fusionado"] is False
    assert res["data"]["id"] == 999

def test_registrar_compra_borrador_fusion(mock_supabase_client):
    # Mocking an existing draft
    mock_supabase_client.table().select().eq().eq().execute().data = [
        {"id": 1, "estado": "Borrador", "productos": [], "total": 50.0, "pendiente": 50.0}
    ]
    
    productos = [{"id": 1, "Cantidad": 5}]
    res = registrar_compra_borrador(
        mock_supabase_client,
        proveedor_id=1,
        num_fac="F-001",
        es_abono=False,
        productos=productos,
        dto_pp=0.0,
        fecha_fac="2026-07-19",
        total=100.0
    )
    assert res["fusionado"] is True
    assert res["data"]["id"] == 999

def test_registrar_compra_borrador_archivada(mock_supabase_client):
    # Mocking an existing archived invoice
    mock_supabase_client.table().select().eq().eq().execute().data = [
        {"id": 1, "estado": "Completado", "productos": [], "total": 50.0, "pendiente": 50.0}
    ]
    
    productos = [{"id": 1, "Cantidad": 5}]
    with pytest.raises(ValueError, match="ya existe y está archivado"):
        registrar_compra_borrador(
            mock_supabase_client,
            proveedor_id=1,
            num_fac="F-001",
            es_abono=False,
            productos=productos,
            dto_pp=0.0,
            fecha_fac="2026-07-19",
            total=100.0
        )

def test_registrar_pago_deuda(mock_supabase_client):
    # Setup mock specifically for this test
    mock_supabase_client.table().select().eq().execute().data = [
        {"id": 1, "pagado": 10.0, "pendiente": 50.0, "total": 60.0}
    ]
    
    res = registrar_pago_deuda(mock_supabase_client, compra_id=1, pago_eur=20.0, cuenta_id=None)
    assert res["id"] == 1

def test_registrar_pago_deuda_importe_exacto_centimos(mock_supabase_client):
    """Pago exacto del pendiente no debe rechazarse por ruido de float."""
    mock_supabase_client.table().select().eq().execute().data = [
        {"id": 1, "pagado": 0.0, "pendiente": 177.01, "total": 177.01}
    ]
    res = registrar_pago_deuda(mock_supabase_client, compra_id=1, pago_eur=177.01, cuenta_id=None)
    assert res["id"] == 1
    update_payload = mock_supabase_client.table().update.call_args[0][0]
    assert update_payload["estado"] == "Pagado"
    assert update_payload["pendiente"] == 0.0

def test_registrar_pago_deuda_exceso_real(mock_supabase_client):
    mock_supabase_client.table().select().eq().execute().data = [
        {"id": 1, "pagado": 0.0, "pendiente": 177.01, "total": 177.01}
    ]
    with pytest.raises(ValueError, match="la deuda pendiente es"):
        registrar_pago_deuda(mock_supabase_client, compra_id=1, pago_eur=177.02, cuenta_id=None)

def test_registrar_pago_deuda_negativo(mock_supabase_client):
    with pytest.raises(ValueError, match="mayor a 0"):
        registrar_pago_deuda(mock_supabase_client, compra_id=1, pago_eur=-10.0, cuenta_id=None)
