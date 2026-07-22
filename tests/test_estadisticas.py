import pytest
import sys
import os
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_estadisticas import calcular_balance_financiero, calcular_roi_laboral

def test_calcular_balance_financiero():
    df_ventas = pd.DataFrame([
        {'id': 1, 'total': 100.0, 'estado': 'COMPLETADO'},
        {'id': 2, 'total': 50.0, 'estado': 'COMPLETADO'},
        {'id': 3, 'total': 50.0, 'estado': 'DEVUELTO'}  # Should be excluded
    ])
    
    df_compras = pd.DataFrame([
        {'id': 1, 'total': 30.0}
    ])
    
    gastos_fijos = [
        {'importe_estimado': 120.0, 'frecuencia': 'Mensual'},
        {'importe_estimado': 60.0, 'frecuencia': 'Bimestral'} # 30 al mes
    ] # Total al mes = 150
    
    res = calcular_balance_financiero(df_ventas, df_compras, gastos_fijos, factor_fijos=1.0)
    
    assert res['total_ventas'] == 150.0
    assert res['num_operaciones'] == 2
    assert res['ticket_medio'] == 75.0
    assert res['total_compras'] == 30.0
    assert res['total_fijos_mes'] == 150.0
    assert res['gastos_totales'] == 180.0
    assert res['balance_neto'] == -30.0 # 150 - 180

def test_calcular_roi_laboral():
    empleados = ['Ana', 'Juan']
    citas_data = [
        {
            'fecha_hora': '2023-01-01T10:00:00',
            'servicio': 'Baño (Ana)',
            'mascotas': {
                'historial_trabajos': [
                    {'Fecha': '01/01/2023', 'Importe (€)': '25.0', 'Extras (€)': '5.0'}
                ]
            }
        },
        {
            'fecha_hora': '2023-01-01T11:00:00',
            'servicio': 'Corte (Juan)',
            'mascotas': {
                'historial_trabajos': [
                    {'Fecha': '01/01/2023', 'Precio con desc. (€)': '30.0'}
                ]
            }
        },
        {
            'fecha_hora': '2023-01-02T10:00:00',
            'servicio': '[ESTADO: Cancelada] Baño (Ana)', # Should be ignored
            'mascotas': {}
        }
    ]
    
    res = calcular_roi_laboral(citas_data, empleados)
    
    assert res['Ana']['Citas'] == 1
    assert res['Ana']['Ingresos'] == 30.0
    
    assert res['Juan']['Citas'] == 1
    assert res['Juan']['Ingresos'] == 30.0
