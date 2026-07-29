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


def test_eliminar_borrador_no_toca_stock():
    """Borrado seguro: borradores no revierten stock (Compendio §2)."""
    from core_contabilidad import eliminar_documento_contabilidad

    client = MagicMock()
    df_comp = pd.DataFrame([
        {"id": 200, "estado": "Borrador", "productos": [{"id": 1, "Cantidad": 5}]}
    ])
    fetch_stock = MagicMock()
    assert eliminar_documento_contabilidad(client, df_comp, 200, fetch_stock) is True
    fetch_stock.assert_not_called()
    client.table().delete().eq().execute.assert_called()


def test_safe_float_y_lineas_por_palabra_clave():
    from core_contabilidad import safe_float, calcular_bases_e_igic_y_lineas
    import json

    assert safe_float(None) == 0.0
    assert safe_float("") == 0.0
    assert safe_float("12,5") == 12.5
    assert safe_float("xx", default=3.0) == 3.0

    # vacío / JSON string / dict único / cita_ / excepción champú
    assert calcular_bases_e_igic_y_lineas(
        None, 0, True, "F-1", "01/01/2026", "A", {}, []
    )[0] == 0.0

    productos_json = json.dumps([
        {"id": "cita_99", "Producto": "Peluquería", "Precio Venta": 10.7, "Cantidad": 1, "IGIC %": 7},
        {"id": 3, "Producto": "Champú premium", "Precio Venta": 8.0, "Cantidad": 1},
        {"id": 4, "Producto": "Corte pelo", "Precio Venta": 21.4, "Cantidad": 1, "IGIC %": 7},
        "basura",
    ])
    mapa = {"3": "Desconocido", "4": "Desconocido"}
    palabras = ["corte", "baño", "pelu"]
    b_p, b_s, i_s, l_p, l_s = calcular_bases_e_igic_y_lineas(
        productos_json, desc_global=10.0, is_factura=True,
        doc_id_str="F-2", fecha_str="01/01/2026", cliente_nom="Ana",
        mapa_categorias=mapa, palabras_clave_serv=palabras,
    )
    assert b_p > 0  # champú no es servicio pese a keyword genérica en otros
    assert any("Champú" in x["Producto"] for x in l_p)
    assert b_s > 0 and len(l_s) >= 1

    # dict único como productos_raw
    b_p2, *_ = calcular_bases_e_igic_y_lineas(
        {"id": 1, "Producto": "Pienso", "Precio": 5.0, "Cantidad": 1},
        0, False, "T-1", "01/01/2026", "B", {"1": "Producto"}, [],
    )
    assert b_p2 == 5.0

    # JSON inválido
    assert calcular_bases_e_igic_y_lineas(
        "{no-json", 0, True, "F", "d", "c", {}, []
    )[0] == 0.0
