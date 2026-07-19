import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from unittest.mock import MagicMock
from core_bancos import realizar_transferencia_interna

def test_realizar_transferencia_interna():
    client = MagicMock()
    
    lista_bancos = [
        {'id': 1, 'nombre_banco': 'Caixa', 'saldo_actual': 1000},
        {'id': 2, 'nombre_banco': 'BBVA', 'saldo_actual': 500}
    ]
    
    # Mocks para caja y bancos
    client.table().select().eq().execute.return_value.data = [{'id': 10, 'estado': 'Abierta'}]
    client.table().update().eq().execute.return_value = None
    client.table().insert().execute.return_value = None
    
    # Test Mismo Origen Destino
    ok, msg = realizar_transferencia_interna(client, "Banco A", "Banco A", 100, lista_bancos)
    assert not ok
    assert "no pueden ser el mismo" in msg
    
    # Test Cantidad <= 0
    ok, msg = realizar_transferencia_interna(client, "Banco A", "Banco B", 0, lista_bancos)
    assert not ok
    assert "mayor que 0" in msg
    
    # Test Transferencia de Banco a Banco
    ori = "🏦 Caixa (1000.00 €)"
    des = "🏦 BBVA (500.00 €)"
    ok, msg = realizar_transferencia_interna(client, ori, des, 200, lista_bancos)
    assert ok
    assert "completada con éxito" in msg
    
    # Test Transferencia de Caja a Banco
    ori = "Caja Fuerte (Efectivo)"
    des = "🏦 BBVA (500.00 €)"
    ok, msg = realizar_transferencia_interna(client, ori, des, 300, lista_bancos)
    assert ok
    assert "completada con éxito" in msg
    
    # Test Caja Cerrada
    client.table().select().eq().execute.return_value.data = []
    ok, msg = realizar_transferencia_interna(client, ori, des, 300, lista_bancos)
    assert ok
    assert "caja fuerte está cerrada" in msg
