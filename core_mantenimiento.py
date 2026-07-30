"""Lógica de negocio: calendario de mantenimiento de material."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Optional

FRECUENCIAS = [
    "Diaria",
    "Semanal",
    "2 veces por semana",
    "Cada 15 días",
    "Mensual",
    "Cada 3 meses",
    "Cada 6 meses",
    "Puntual",
]

TIPOS_MANTENIMIENTO = [
    "Limpieza",
    "Desinfección",
    "Revisión",
    "Afilado",
    "Cambio / Recambio",
    "Mantenimiento técnico",
    "Limpieza a fondo",
    "Otro",
]

CATEGORIAS_MATERIAL = [
    "Máquina",
    "Cuchillas",
    "Cepillos / Peines",
    "Bañera",
    "Zona peluquería",
    "Desinfección",
    "Herramienta",
    "General",
]

DIAS_SEMANA_LABELS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

TIPOS_MOVIMIENTO = [
    "Sale a afilar",
    "Sale a reparación",
    "Sale a mantenimiento",
    "Vuelve de taller",
    "Incidencia",
    "Anotación",
]


def _as_date(value) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date) and not hasattr(value, "hour"):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except Exception:
        return None


def calcular_siguiente_fecha(
    frecuencia_tipo: str,
    desde: date,
    dias_semana: Optional[list] = None,
    fecha_inicio: Optional[date] = None,
) -> Optional[date]:
    """
    Calcula la siguiente fecha de mantenimiento a partir de `desde` (incluida si encaja).

    - Diaria: el mismo día `desde` (o siguiente si se usa como post-cierre, pasar desde+1).
    - Semanal: mismo weekday que fecha_inicio (o desde).
    - 2 veces por semana: próximos días de `dias_semana` (0=Lunes … 6=Domingo).
    - Cada 15 días / Mensual / 3m / 6m: desde fecha_inicio saltando intervalos.
    - Puntual: None (no se regenera).
    """
    dias_semana = list(dias_semana or [])
    f_ini = fecha_inicio or desde
    freq = (frecuencia_tipo or "").strip()

    if freq == "Puntual":
        return None

    if freq == "Diaria":
        return desde

    if freq == "Semanal":
        target_wd = f_ini.weekday()
        d = desde
        for _ in range(8):
            if d.weekday() == target_wd:
                return d
            d += timedelta(days=1)
        return desde

    if freq == "2 veces por semana":
        targets = sorted({int(x) for x in dias_semana if 0 <= int(x) <= 6})
        if not targets:
            targets = [0, 3]  # Lun / Jue por defecto
        d = desde
        for _ in range(14):
            if d.weekday() in targets:
                return d
            d += timedelta(days=1)
        return desde

    if freq == "Cada 15 días":
        if desde <= f_ini:
            return f_ini
        delta = (desde - f_ini).days
        steps = (delta + 14) // 15
        return f_ini + timedelta(days=steps * 15)

    if freq in ("Mensual", "Cada 3 meses", "Cada 6 meses"):
        months = {"Mensual": 1, "Cada 3 meses": 3, "Cada 6 meses": 6}[freq]
        # Avanzar por meses desde f_ini hasta >= desde
        y, m, day = f_ini.year, f_ini.month, f_ini.day
        curr = f_ini
        guard = 0
        while curr < desde and guard < 500:
            guard += 1
            m += months
            while m > 12:
                m -= 12
                y += 1
            # día seguro (ej. 31 en feb)
            for try_day in range(day, 0, -1):
                try:
                    curr = date(y, m, try_day)
                    break
                except ValueError:
                    continue
        return curr if curr >= desde else desde

    return desde


def siguiente_tras_completar(
    frecuencia_tipo: str,
    fecha_realizada: date,
    dias_semana: Optional[list] = None,
    fecha_inicio: Optional[date] = None,
) -> Optional[date]:
    """Tras marcar hecho: próxima ocurrencia estrictamente posterior a la fecha realizada."""
    freq = (frecuencia_tipo or "").strip()
    if freq == "Puntual":
        return None
    if freq == "Diaria":
        return fecha_realizada + timedelta(days=1)
    if freq == "Cada 15 días":
        return fecha_realizada + timedelta(days=15)
    if freq == "Mensual":
        return calcular_siguiente_fecha(freq, fecha_realizada + timedelta(days=1), dias_semana, fecha_inicio or fecha_realizada)
    if freq in ("Cada 3 meses", "Cada 6 meses"):
        return calcular_siguiente_fecha(freq, fecha_realizada + timedelta(days=1), dias_semana, fecha_inicio or fecha_realizada)
    # Semanal / 2x semana: buscar desde el día siguiente
    return calcular_siguiente_fecha(freq, fecha_realizada + timedelta(days=1), dias_semana, fecha_inicio)


def proyectar_fechas_plan(
    frecuencia_tipo: str,
    fecha_inicio: date,
    desde: date,
    hasta: date,
    dias_semana: Optional[list] = None,
    max_eventos: int = 90,
) -> list[date]:
    """Lista de fechas programadas en [desde, hasta] para un plan."""
    freq = (frecuencia_tipo or "").strip()
    if freq == "Puntual":
        if desde <= fecha_inicio <= hasta:
            return [fecha_inicio]
        return []

    fechas = []
    cursor = calcular_siguiente_fecha(freq, max(desde, fecha_inicio), dias_semana, fecha_inicio)
    if cursor is None:
        return []
    # Si la primera cae antes de desde, avanzar
    while cursor is not None and cursor < desde:
        nxt = siguiente_tras_completar(freq, cursor, dias_semana, fecha_inicio)
        if nxt is None or nxt <= cursor:
            break
        cursor = nxt

    guard = 0
    while cursor is not None and cursor <= hasta and guard < max_eventos:
        if cursor >= desde:
            fechas.append(cursor)
        nxt = siguiente_tras_completar(freq, cursor, dias_semana, fecha_inicio)
        if nxt is None or nxt <= cursor:
            break
        cursor = nxt
        guard += 1
    return fechas


def clasificar_estado_pendiente(fecha_programada: date, hoy: Optional[date] = None) -> str:
    hoy = hoy or date.today()
    if fecha_programada < hoy:
        return "Atrasado"
    if fecha_programada == hoy:
        return "Pendiente hoy"
    return "Programado"


def resumen_mantenimientos_por_dia(
    items: list[dict],
    fecha: date,
) -> dict[str, Any]:
    """
    items: lista con al menos fecha_programada, estado, etiqueta (nombre material + tipo).
    Devuelve conteos y etiquetas para el calendario general.
    """
    f_str = str(fecha)
    del_dia = []
    for it in items:
        fp = _as_date(it.get("fecha_programada"))
        if fp and str(fp) == f_str:
            del_dia.append(it)

    pendientes = [i for i in del_dia if str(i.get("estado", "")).lower() in ("pendiente", "atrasado")]
    hechos = [i for i in del_dia if str(i.get("estado", "")).lower() in ("hecho", "completada", "completado")]
    atrasados = [i for i in pendientes if clasificar_estado_pendiente(_as_date(i["fecha_programada"]), fecha) == "Atrasado"
                 or str(i.get("estado", "")).lower() == "atrasado"]

    # Si estamos viendo un día pasado y siguen pendientes, cuentan como atrasados visualmente
    if fecha < date.today():
        atrasados = [i for i in pendientes]

    etiquetas = [i.get("etiqueta") or i.get("titulo") or "Mantenimiento" for i in del_dia]
    return {
        "total": len(del_dia),
        "pendientes": len(pendientes),
        "hechos": len(hechos),
        "atrasados": len(atrasados),
        "etiquetas": etiquetas[:8],
        "items": del_dia,
    }


def construir_etiqueta(nombre_material: str, tipo_mantenimiento: str) -> str:
    return f"{nombre_material} · {tipo_mantenimiento}"


def asegurar_ejecuciones_abiertas(
    planes: list[dict],
    ejecuciones_existentes: list[dict],
    hoy: Optional[date] = None,
    horizonte_dias: int = 14,
) -> list[dict]:
    """
    Genera filas de ejecución pendientes que faltan (sin escribir en BD).
    Útil para preview / sync: planes activos con proxima_ejecucion <= hoy+horizonte
    o fechas proyectadas atrasadas no cerradas.
    """
    hoy = hoy or date.today()
    hasta = hoy + timedelta(days=horizonte_dias)
    existentes = {
        (int(e["plan_id"]), str(_as_date(e["fecha_programada"])))
        for e in ejecuciones_existentes
        if e.get("plan_id") is not None and e.get("fecha_programada")
    }
    nuevas = []
    for p in planes:
        if not p.get("activo", True):
            continue
        f_ini = _as_date(p.get("fecha_inicio")) or hoy
        dias = p.get("dias_semana") or []
        freq = p.get("frecuencia_tipo") or "Mensual"
        # Empezar desde la más antigua pendiente relevante: min(proxima, fecha_inicio) limitada
        prox = _as_date(p.get("proxima_ejecucion")) or f_ini
        start = min(prox, hoy) if prox <= hoy else prox
        start = max(start, f_ini - timedelta(days=0))
        # Para atrasados: proyectar desde prox si está en el pasado hasta hoy
        rango_ini = min(prox, hoy) if prox < hoy else max(prox, hoy)
        if prox < hoy:
            rango_ini = prox
        else:
            rango_ini = max(prox, hoy)

        fechas = proyectar_fechas_plan(freq, f_ini, rango_ini, hasta, dias)
        # Incluir también la propia proxima si cae en rango y no está
        if prox and hoy - timedelta(days=365) <= prox <= hasta and prox not in fechas:
            fechas = sorted(set(fechas + [prox]))

        for f in fechas:
            key = (int(p["id"]), str(f))
            if key in existentes:
                continue
            estado = "Atrasado" if f < hoy else "Pendiente"
            nuevas.append({
                "plan_id": int(p["id"]),
                "fecha_programada": str(f),
                "estado": estado,
                "material_id": p.get("material_id"),
                "tipo_mantenimiento": p.get("tipo_mantenimiento"),
                "frecuencia_tipo": freq,
            })
    return nuevas
