import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_configuracion import get_configuracion_negocio_default, construir_payload_configuracion

def test_get_configuracion_negocio_default():
    cfg = get_configuracion_negocio_default()
    assert cfg['nombre_tienda'] == 'Animalarium'
    assert cfg['envio_gratis_a_partir_de'] == 110.0
    
def test_construir_payload_configuracion():
    # Caso 1: Todo correcto y limpieza de tipos
    raw1 = {
        'nombre_tienda': ' Tienda Guay ',
        'envio_gratis_a_partir_de': '150.0', # str to float
        'limite_descuento_puntos_porcentaje': 150 # Out of bounds
    }
    
    p1 = construir_payload_configuracion(raw1, current_time_iso="2023-10-01")
    assert p1 is not None
    assert p1['nombre_tienda'] == 'Tienda Guay'
    assert p1['envio_gratis_a_partir_de'] == 150.0
    assert p1['limite_descuento_puntos_porcentaje'] == 100.0 # Capped at 100
    
    # Caso 2: Euros para un punto negativo
    raw2 = {
        'euros_para_un_punto': -5
    }
    p2 = construir_payload_configuracion(raw2)
    assert p2['euros_para_un_punto'] == 10.0 # Default if negative/zero
    
    # Caso 3: Fallo catastrófico (datos ilegibles)
    raw3 = {
        'envio_gratis_a_partir_de': 'esto no es un numero'
    }
    p3 = construir_payload_configuracion(raw3)
    assert p3 is None
