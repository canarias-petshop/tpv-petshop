import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_proyectos import calcular_desviacion_presupuesto, analizar_estado_proyecto

def test_calcular_desviacion_presupuesto():
    # Bajo presupuesto (bien)
    d, s = calcular_desviacion_presupuesto(1000.0, 800.0)
    assert d == 200.0
    assert not s
    
    # Sobre presupuesto (mal)
    d2, s2 = calcular_desviacion_presupuesto(1000.0, 1200.0)
    assert d2 == -200.0
    assert s2
    
    # Datos corruptos
    d3, s3 = calcular_desviacion_presupuesto("algo", None)
    assert d3 == 0.0
    assert not s3

def test_analizar_estado_proyecto():
    # Proyecto en curso con sobrecoste -> En peligro
    p_peligro = {
        'presupuesto_estimado': 500,
        'coste_real': 600,
        'estado': 'En curso'
    }
    res_p = analizar_estado_proyecto(p_peligro)
    assert res_p['en_peligro']
    assert res_p['desviacion'] == -100.0
    
    # Proyecto completado con sobrecoste -> Ya no está en peligro (ya se completó)
    p_comp = {
        'presupuesto_estimado': 500,
        'coste_real': 600,
        'estado': 'Completado'
    }
    res_c = analizar_estado_proyecto(p_comp)
    assert not res_c['en_peligro']
    
    # Proyecto sin inicializar
    assert analizar_estado_proyecto(None) is None
