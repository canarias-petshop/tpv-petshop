import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
from datetime import date
from core_agenda import calcular_huecos_libres, verificar_solape_manual

def test_calcular_huecos_libres():
    fecha_c = date(2023, 10, 10) # Martes (weekday 1)
    
    # 1 empleado, trabajando turno de mañana
    turnos_dict = {"Ana": "09:00 - 14:00"}
    empleados_lista = ["Ana"]
    empleados_a_revisar = ["Ana"]
    
    # Citas existentes
    # Una cita de 09:30 a 10:00 con Ana
    citas_dia = [
        {"fecha_hora": "2023-10-10 09:30:00", "duracion_minutos": 30, "servicio": "Baño (Ana)"}
    ]
    
    # Bloqueos
    # Bloqueo de 11:00 a 12:00
    bloqueos_parciales = [
        {"empleado_afectado": "Ana", "hora_inicio": "11:00", "hora_fin": "12:00"}
    ]
    
    huecos, formateados, citas_virt = calcular_huecos_libres(
        fecha_c, citas_dia, bloqueos_parciales, empleados_a_revisar, empleados_lista, turnos_dict, 30
    )
    
    # Check slots available
    # 09:00 - 09:30 -> Available
    # 09:05 - 09:35 -> Not available (overlaps 09:30 cita)
    # ...
    # 10:00 - 10:30 -> Available
    # 11:00 - 11:30 -> Blocked
    
    dt_9am = pd.to_datetime("2023-10-10 09:00:00")
    dt_10am = pd.to_datetime("2023-10-10 10:00:00")
    dt_11am = pd.to_datetime("2023-10-10 11:00:00")
    
    huecos_dts = [h['dt'] for h in huecos]
    
    assert dt_9am in huecos_dts, "9:00 should be available"
    assert dt_10am in huecos_dts, "10:00 should be available"
    assert dt_11am not in huecos_dts, "11:00 should be blocked"
    
def test_empleado_ausente_bugfix():
    fecha_c = date(2023, 10, 10)
    
    # Bugfix: Ausencia or Baja should return no slots
    turnos_dict = {"Ana": "Ausencia"}
    empleados_lista = ["Ana"]
    empleados_a_revisar = ["Ana"]
    
    huecos, formateados, citas_virt = calcular_huecos_libres(
        fecha_c, [], [], empleados_a_revisar, empleados_lista, turnos_dict, 30
    )
    
    # The only element in formateados should be "Asignación Manual"
    assert len(huecos) == 0
    assert formateados == ["Asignación Manual"]
    
    turnos_dict = {"Ana": "Vacaciones"}
    huecos, formateados, citas_virt = calcular_huecos_libres(
        fecha_c, [], [], empleados_a_revisar, empleados_lista, turnos_dict, 30
    )
    assert len(huecos) == 0

def test_verificar_solape_manual():
    fecha_c = date(2023, 10, 10)
    dt_ini_man = pd.to_datetime("2023-10-10 10:00:00")
    duracion = 30
    
    citas_virtuales = [
        {"fecha_hora": "2023-10-10 09:45:00", "duracion_minutos": 30, "servicio": "Pelu (Ana)"}
    ]
    
    # Test overlap with appointment
    turnos_dict = {"Ana": "09:00 - 14:00"}
    empleados_lista = ["Ana"]
    
    solapa, motivo = verificar_solape_manual(dt_ini_man, duracion, citas_virtuales, empleados_lista, turnos_dict, "Ana")
    assert solapa == True
    assert "Pelu (Ana)" in motivo
    
    # Test overlap with absent employee
    turnos_dict = {"Ana": "Baja Médica"}
    solapa, motivo = verificar_solape_manual(dt_ini_man, duracion, [], empleados_lista, turnos_dict, "Ana")
    assert solapa == True
    assert "ausente" in motivo

    # Test working hours
    turnos_dict = {"Ana": "12:00 - 20:00"}
    solapa, motivo = verificar_solape_manual(dt_ini_man, duracion, [], empleados_lista, turnos_dict, "Ana")
    assert solapa == True
    assert "fuera de su horario" in motivo

    # Test OK
    turnos_dict = {"Ana": "09:00 - 14:00"}
    solapa, motivo = verificar_solape_manual(dt_ini_man, duracion, [], empleados_lista, turnos_dict, "Ana")
    assert solapa == False
    assert motivo == ""
