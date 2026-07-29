import pytest
import sys
import os
from datetime import date, timedelta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_marketing import calcular_progreso_objetivo, verificar_alertas_plan_marketing

def test_calcular_progreso_objetivo():
    assert calcular_progreso_objetivo(50, 100) == 0.5
    assert calcular_progreso_objetivo(150, 100) == 1.0 # Should cap at 1.0
    assert calcular_progreso_objetivo(50, 0) == 0.0 # Division by zero prevention
    assert calcular_progreso_objetivo(0, 100) == 0.0
    assert calcular_progreso_objetivo(-10, 100) == 0.0 # Negative progress prevention
    
def test_verificar_alertas_plan_marketing():
    hoy = date.today()
    
    # Error: less than 30 days
    fecha_error = (hoy + timedelta(days=20)).strftime('%Y-%m-%d')
    res_error = verificar_alertas_plan_marketing(fecha_error)
    assert res_error is not None
    assert res_error["nivel"] == "error"
    
    # Warning: 31-45 days
    fecha_warning = (hoy + timedelta(days=40)).strftime('%Y-%m-%d')
    res_warning = verificar_alertas_plan_marketing(fecha_warning)
    assert res_warning is not None
    assert res_warning["nivel"] == "warning"
    
    # None: > 45 days
    fecha_ok = (hoy + timedelta(days=60)).strftime('%Y-%m-%d')
    res_ok = verificar_alertas_plan_marketing(fecha_ok)
    assert res_ok is None
    
    # None: empty date
    assert verificar_alertas_plan_marketing("") is None
    assert verificar_alertas_plan_marketing(None) is None
    assert verificar_alertas_plan_marketing("fecha-invalida") is None
    # Caducado (días negativos) -> sin alerta
    fecha_pasada = (hoy - timedelta(days=5)).strftime("%Y-%m-%d")
    assert verificar_alertas_plan_marketing(fecha_pasada) is None


def test_calcular_progreso_objetivo_entradas_invalidas():
    assert calcular_progreso_objetivo("abc", 100) == 0.0
    assert calcular_progreso_objetivo(10, "x") == 0.0
    assert calcular_progreso_objetivo("25", "50") == 0.5
