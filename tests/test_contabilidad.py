import pytest
import sys
import os
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from unittest.mock import MagicMock
from core_contabilidad import eliminar_documento_contabilidad, calcular_bases_e_igic_y_lineas

def test_eliminar_documento_contabilidad():
    client = MagicMock()
    df_comp = pd.DataFrame([
        {'id': 100, 'productos': [{'id': 1, 'Cantidad': 5}]}
    ])
    
    # Mock para stock
    res_stock = MagicMock()
    res_stock.data = [{'stock_actual': 20}]
    
    def fetch_stock(c, p_id):
        return res_stock
        
    client.table().update().eq().execute.return_value = None
    client.table().delete().eq().execute.return_value = None
    
    res = eliminar_documento_contabilidad(client, df_comp, 100, fetch_stock)
    assert res == True
    
    # Comprobar que se restó el stock: 20 - 5 = 15
    args, kwargs = client.table().update.call_args
    assert args[0]['stock_actual'] == 15

def test_calcular_bases_e_igic_y_lineas():
    # Simulamos un producto y un servicio
    productos = [
        {"id": 1, "Producto": "Pienso", "Precio Venta": 10.0, "Cantidad": 2, "Desc %": 0},
        {"id": 2, "Producto": "Baño Perro", "Precio Venta": 21.40, "Cantidad": 1, "Desc %": 0, "IGIC %": 7.0}
    ]
    
    mapa_cat = {"1": "Producto", "2": "Servicio"}
    palabras_clave = ["baño"]
    
    b_p, b_s, i_s, l_p, l_s = calcular_bases_e_igic_y_lineas(
        productos, desc_global=0.0, is_factura=True, 
        doc_id_str="F-1", fecha_str="01/01/2023", cliente_nom="Juan",
        mapa_categorias=mapa_cat, palabras_clave_serv=palabras_clave
    )
    
    # 2 piensos a 10 = 20
    assert b_p == 20.0
    
    # 1 baño a 21.40 (incluye IGIC) -> base = 21.40 / 1.07 = 20.0
    assert b_s == 20.0
    assert i_s == 1.40
    
    assert len(l_p) == 1
    assert len(l_s) == 1
    
    assert l_p[0]["Total (0% IGIC) (€)"] == 20.0
    assert l_s[0]["Base Imponible (€)"] == 20.0
    assert l_s[0]["Cuota IGIC (€)"] == 1.40
