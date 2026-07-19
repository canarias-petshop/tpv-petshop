import pytest
import sys
import os

# Añadir el directorio raíz al path para que pueda importar caja.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from caja import calcular_arqueo

def test_calcular_arqueo_caja_cuadrada():
    """Prueba que si todo cuadra, el descuadre es 0."""
    fondo = 100.0
    ventas_efectivo = 50.0
    ingresos = 10.0
    retiradas = 20.0
    # Teórico = 100 + 50 + 10 - 20 = 140
    efectivo_declarado = 140.0
    
    teorico, descuadre = calcular_arqueo(fondo, ventas_efectivo, ingresos, retiradas, efectivo_declarado)
    
    assert teorico == 140.0
    assert descuadre == 0.0

def test_calcular_arqueo_falta_dinero():
    """Prueba cuando falta dinero en la caja."""
    fondo = 100.0
    ventas_efectivo = 50.0
    ingresos = 0.0
    retiradas = 0.0
    # Teórico = 150
    efectivo_declarado = 140.0 # ¡Faltan 10 euros!
    
    teorico, descuadre = calcular_arqueo(fondo, ventas_efectivo, ingresos, retiradas, efectivo_declarado)
    
    assert teorico == 150.0
    assert descuadre == -10.0

def test_calcular_arqueo_sobra_dinero():
    """Prueba cuando sobra dinero en la caja."""
    fondo = 100.0
    ventas_efectivo = 0.0
    ingresos = 0.0
    retiradas = 0.0
    # Teórico = 100
    efectivo_declarado = 105.0 # ¡Sobran 5 euros!
    
    teorico, descuadre = calcular_arqueo(fondo, ventas_efectivo, ingresos, retiradas, efectivo_declarado)
    
    assert teorico == 100.0
    assert descuadre == 5.0
