import pytest
import sys
import os
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_ficha_clinica import aplicar_descuentos_fidelidad

def test_aplicar_descuentos_fidelidad_oferta():
    # Test que se aplica si la fecha coincide con oferta
    data = [
        {"Fecha": "10/10/2023", "Trabajo / Servicio": "Baño", "Precio Base (€)": 10.0, "Precio con desc. (€)": "", "Nota Sesión": ""}
    ]
    df = pd.DataFrame(data, dtype=object)
    fechas_oferta = ["10/10/2023"]
    
    df_res, msgs = aplicar_descuentos_fidelidad(df, fechas_oferta)
    
    assert df_res.at[0, "Precio con desc. (€)"] == 9.0
    assert len(msgs) == 1
    assert "10%" in msgs[0]

def test_aplicar_descuentos_fidelidad_recurrencia():
    # Test que se aplica si vino hace menos de 60 dias
    data = [
        {"Fecha": "01/01/2023", "Trabajo / Servicio": "Baño", "Precio Base (€)": 10.0, "Precio con desc. (€)": "", "Nota Sesión": ""},
        {"Fecha": "15/01/2023", "Trabajo / Servicio": "Baño", "Precio Base (€)": 20.0, "Precio con desc. (€)": "", "Nota Sesión": ""}
    ]
    df = pd.DataFrame(data, dtype=object)
    fechas_oferta = []
    
    df_res, msgs = aplicar_descuentos_fidelidad(df, fechas_oferta)
    
    # 01/01 no tiene descuento (es la primera vez que se registra)
    assert df_res.at[0, "Precio con desc. (€)"] == 10.0
    
    # 15/01 si tiene descuento, pasaron 14 dias
    assert df_res.at[1, "Precio con desc. (€)"] == 18.0
    assert "10%" in df_res.at[1, "Nota Sesión"]

def test_no_aplicar_descuentos_si_pasaron_mas_de_60_dias():
    data = [
        {"Fecha": "01/01/2023", "Trabajo / Servicio": "Baño", "Precio Base (€)": 10.0, "Precio con desc. (€)": "", "Nota Sesión": ""},
        {"Fecha": "15/04/2023", "Trabajo / Servicio": "Baño", "Precio Base (€)": 20.0, "Precio con desc. (€)": "", "Nota Sesión": ""}
    ]
    df = pd.DataFrame(data, dtype=object)
    fechas_oferta = []
    
    df_res, msgs = aplicar_descuentos_fidelidad(df, fechas_oferta)
    
    assert df_res.at[0, "Precio con desc. (€)"] == 10.0
    assert df_res.at[1, "Precio con desc. (€)"] == 20.0
    assert len(msgs) == 0
