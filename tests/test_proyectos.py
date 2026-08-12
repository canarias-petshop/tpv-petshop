import pytest
import sys
import os
from datetime import date
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_proyectos import (
    calcular_desviacion_presupuesto,
    analizar_estado_proyecto,
    construir_bloqueos_rango,
)

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


def test_construir_bloqueos_rango_varios_dias():
    filas = construir_bloqueos_rango(
        date(2026, 8, 13),
        date(2026, 8, 15),
        "09:00",
        "11:00",
        "Reunión de equipo",
        "Todas",
        True,
    )
    assert len(filas) == 3
    assert [f["fecha"] for f in filas] == ["2026-08-13", "2026-08-14", "2026-08-15"]
    assert all(f["hora_inicio"] == "09:00" and f["titulo"] == "Reunión de equipo" for f in filas)


def test_construir_bloqueos_rango_un_dia_y_errores():
    un_dia = construir_bloqueos_rango(
        date(2026, 8, 13), date(2026, 8, 13), "10:00", "10:30", "Briefing", "Ana", False
    )
    assert len(un_dia) == 1
    assert un_dia[0]["empleado_afectado"] == "Ana"
    assert un_dia[0]["bloquea_agenda"] is False

    with pytest.raises(ValueError, match="fecha de fin"):
        construir_bloqueos_rango(
            date(2026, 8, 15), date(2026, 8, 13), "09:00", "10:00", "X", "Todas"
        )
    with pytest.raises(ValueError, match="obligatorios"):
        construir_bloqueos_rango(date(2026, 8, 13), date(2026, 8, 13), "09:00", "10:00", "", "Todas")
