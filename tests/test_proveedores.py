import pytest
import sys
import os
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from unittest.mock import MagicMock
from core_proveedores import auto_distribuir_borradores

def test_auto_distribuir_borradores():
    client = MagicMock()
    
    # Mock para fetch_productos_proveedores_rels
    rels_mock = MagicMock()
    rels_mock.data = [
        {'producto_id': 1, 'proveedor_id': 100, 'precio_coste': 5.0}, # Prov A: caro
        {'producto_id': 1, 'proveedor_id': 200, 'precio_coste': 3.0}, # Prov B: barato
    ]
    def mock_fetch_rels(c):
        return rels_mock
        
    # Mock para fetch_pedidos_proveedor_borrador
    # Simulamos que no hay borradores (se creara uno nuevo)
    def mock_fetch_borrador(c, prov_id):
        m = MagicMock()
        m.data = []
        return m
        
    prods = pd.DataFrame([
        {'id': 1, 'nombre': 'Pienso Gato', 'cantidad_reponer': 10}
    ])
    
    generados = auto_distribuir_borradores(client, prods, mock_fetch_rels, mock_fetch_borrador)
    
    assert generados == True
    
    # Comprobar que se llamo a insert
    client.table().insert.assert_called()
    args, kwargs = client.table().insert.call_args
    # Debe haberse asignado al proveedor 200 (el mas barato)
    assert args[0]['proveedor_id'] == 200
    assert args[0]['productos'][0]['Producto'] == 'Pienso Gato'
    assert args[0]['productos'][0]['Cantidad'] == 10


def test_auto_distribuir_fusiona_borrador_existente():
    """Si ya hay borrador del proveedor barato, fusiona productos sin duplicar nombre."""
    client = MagicMock()
    rels_mock = MagicMock()
    rels_mock.data = [
        {"producto_id": 1, "proveedor_id": 200, "precio_coste": 3.0},
        {"producto_id": 2, "proveedor_id": 200, "precio_coste": 4.0},
    ]

    draft = MagicMock()
    draft.data = [{
        "id": 55,
        "productos": [{"Producto": "Pienso Gato", "Cantidad": 2}],
    }]

    def mock_fetch_rels(c):
        return rels_mock

    def mock_fetch_borrador(c, prov_id):
        return draft

    prods = pd.DataFrame([
        {"id": 1, "nombre": "Pienso Gato", "cantidad_reponer": 10},
        {"id": 2, "nombre": "Arena", "cantidad_reponer": 5},
    ])

    assert auto_distribuir_borradores(client, prods, mock_fetch_rels, mock_fetch_borrador) is True
    client.table().update.assert_called()
    args, _ = client.table().update.call_args
    nombres = [p["Producto"] for p in args[0]["productos"]]
    assert nombres.count("Pienso Gato") == 1
    assert "Arena" in nombres


def test_auto_distribuir_sin_relaciones():
    client = MagicMock()
    rels = MagicMock()
    rels.data = []
    prods = pd.DataFrame([{"id": 99, "nombre": "X", "cantidad_reponer": 1}])
    assert auto_distribuir_borradores(client, prods, lambda c: rels, lambda c, p: MagicMock(data=[])) is False
    client.table().insert.assert_not_called()
