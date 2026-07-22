import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from unittest.mock import MagicMock
from core_historial import procesar_devolucion

def test_procesar_devolucion():
    client = MagicMock()
    
    # Mocking supabase client
    client.table().select().eq().execute.return_value.data = [{'stock_actual': 10, 'id': 1, 'puntos': 100}]
    client.table().update().eq().execute.return_value = None
    client.table().insert().execute.return_value = None
    
    t_info = {
        'cliente_vip_nombre': 'Juan Perez',
        'puntos_ganados': 5,
        'puntos_usados': 0
    }
    
    prods = [
        {'id': 'prod_1', 'Cantidad': 2},
        {'id': 'cita_1', 'Cantidad': 1} # shouldn't trigger stock update
    ]
    
    bancos = [
        {'nombre_banco': 'BBVA', 'id': 2, 'saldo_actual': 500}
    ]
    
    # 1. Devolución en efectivo
    vale_info = procesar_devolucion(
        client=client, tk_id=101, t_info=t_info, prods=prods,
        btn_abono=True, btn_vale=False, sel_metodo_abono="Efectivo",
        bancos_abono=bancos, total_final_calculado=20.0
    )
    
    assert vale_info is None
    # Verify stock check was called for prod_1
    client.table().select().eq().execute.assert_called()
    
    # 2. Devolución en Tarjeta
    vale_info = procesar_devolucion(
        client=client, tk_id=102, t_info=t_info, prods=prods,
        btn_abono=True, btn_vale=False, sel_metodo_abono="💳 Tarjeta (BBVA)",
        bancos_abono=bancos, total_final_calculado=20.0
    )
    
    assert vale_info is None
    
    # 3. Devolución en Vale
    vale_info = procesar_devolucion(
        client=client, tk_id=103, t_info=t_info, prods=prods,
        btn_abono=False, btn_vale=True, sel_metodo_abono="",
        bancos_abono=bancos, total_final_calculado=20.0
    )
    
    assert vale_info is not None
    assert "VALE-" in vale_info["codigo"]
    assert vale_info["valor"] == 20.0
