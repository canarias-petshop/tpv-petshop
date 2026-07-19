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
