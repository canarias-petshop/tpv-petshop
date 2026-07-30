import pytest
from datetime import date, timedelta
from core_mantenimiento import (
    calcular_siguiente_fecha,
    siguiente_tras_completar,
    proyectar_fechas_plan,
    clasificar_estado_pendiente,
    resumen_mantenimientos_por_dia,
    construir_etiqueta,
    asegurar_ejecuciones_abiertas,
)


def test_frecuencias_basicas():
    base = date(2026, 8, 1)  # sábado
    assert calcular_siguiente_fecha("Diaria", base) == base
    assert siguiente_tras_completar("Diaria", base) == date(2026, 8, 2)

    assert siguiente_tras_completar("Cada 15 días", base) == date(2026, 8, 16)
    assert siguiente_tras_completar("Puntual", base) is None


def test_dos_veces_semana_lun_jue():
    # Martes 4 ago 2026 → siguiente debería ser jueves 6
    d = date(2026, 8, 4)
    nxt = calcular_siguiente_fecha("2 veces por semana", d, dias_semana=[0, 3])
    assert nxt == date(2026, 8, 6)
    nxt2 = siguiente_tras_completar("2 veces por semana", nxt, dias_semana=[0, 3])
    assert nxt2 == date(2026, 8, 10)  # lunes


def test_trimestral_y_semestral():
    ini = date(2026, 1, 15)
    assert calcular_siguiente_fecha("Cada 3 meses", date(2026, 1, 15), fecha_inicio=ini) == ini
    assert calcular_siguiente_fecha("Cada 3 meses", date(2026, 2, 1), fecha_inicio=ini) == date(2026, 4, 15)
    # desde agosto: 15 jul ya pasó → siguiente 15 ene 2027
    assert calcular_siguiente_fecha("Cada 6 meses", date(2026, 8, 1), fecha_inicio=ini) == date(2027, 1, 15)


def test_proyectar_rango_mensual():
    fechas = proyectar_fechas_plan(
        "Mensual", date(2026, 1, 10), date(2026, 1, 1), date(2026, 4, 30)
    )
    assert date(2026, 1, 10) in fechas
    assert date(2026, 2, 10) in fechas
    assert date(2026, 3, 10) in fechas
    assert date(2026, 4, 10) in fechas
    assert len(fechas) == 4


def test_resumen_y_etiqueta():
    hoy = date(2026, 8, 10)
    items = [
        {"fecha_programada": "2026-08-10", "estado": "Pendiente", "etiqueta": "Máquina A · Revisión"},
        {"fecha_programada": "2026-08-10", "estado": "Hecho", "etiqueta": "Bañera · Desinfección"},
        {"fecha_programada": "2026-08-09", "estado": "Pendiente", "etiqueta": "Cuchillas · Afilado"},
    ]
    r = resumen_mantenimientos_por_dia(items, hoy)
    assert r["total"] == 2
    assert r["pendientes"] == 1
    assert r["hechos"] == 1
    assert construir_etiqueta("Máquina A", "Revisión") == "Máquina A · Revisión"
    assert clasificar_estado_pendiente(hoy - timedelta(days=1), hoy) == "Atrasado"


def test_asegurar_ejecuciones_abiertas():
    hoy = date(2026, 8, 10)
    planes = [{
        "id": 1,
        "activo": True,
        "material_id": 9,
        "tipo_mantenimiento": "Limpieza",
        "frecuencia_tipo": "Diaria",
        "fecha_inicio": "2026-08-01",
        "proxima_ejecucion": "2026-08-09",
        "dias_semana": [],
    }]
    existentes = [
        {"plan_id": 1, "fecha_programada": "2026-08-09", "estado": "Pendiente"},
    ]
    nuevas = asegurar_ejecuciones_abiertas(planes, existentes, hoy=hoy, horizonte_dias=2)
    fechas = {n["fecha_programada"] for n in nuevas}
    assert "2026-08-09" not in fechas  # ya existe
    assert "2026-08-10" in fechas
    assert any(n["estado"] == "Pendiente" for n in nuevas if n["fecha_programada"] == "2026-08-10")
