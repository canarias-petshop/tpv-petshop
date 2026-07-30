import pandas as pd
from datetime import date, datetime

ESTADOS_CITA_EXCLUIDOS = (
    "[ESTADO: Cancelada]",
    "[ESTADO: Anulada]",
    "[ESTADO: No presentado]",
)

KEYWORDS_PACKS_CALMA = (
    "calma",
    "pirotecnia",
    "estrés",
    "estres",
    "anti-estrés",
    "anti-estres",
)


def calcular_progreso_objetivo(valor_actual, meta_cuantitativa):
    """
    Calcula el porcentaje de progreso de un objetivo de marketing.
    Retorna un valor entre 0.0 y 1.0
    """
    try:
        val = float(valor_actual)
        meta = float(meta_cuantitativa)
        if meta <= 0:
            return 0.0
        progreso = val / meta
        return min(max(progreso, 0.0), 1.0)
    except Exception:
        return 0.0


def verificar_alertas_plan_marketing(ultima_fecha_str):
    """
    Verifica si el plan de marketing está a punto de caducar (menos de 45 días)
    Retorna un diccionario con 'nivel' (error/warning/info) y 'mensaje'.
    """
    if not ultima_fecha_str:
        return None

    try:
        ultima_fecha = pd.to_datetime(ultima_fecha_str).date()
        dias_restantes = (ultima_fecha - date.today()).days

        if 0 <= dias_restantes <= 30:
            return {
                "nivel": "error",
                "mensaje": f"🚨 **¡ALERTA DE CONTENIDO!** Tu plan de marketing programado se agota el **{ultima_fecha.strftime('%d/%m/%Y')}** (en {dias_restantes} días). ¡Pídele a tu asistente que te redacte y prepare la campaña de la siguiente temporada!"
            }
        elif 30 < dias_restantes <= 45:
            return {
                "nivel": "warning",
                "mensaje": f"⚠️ **Aviso de Temporada:** Tu plan de marketing actual abarca hasta el **{ultima_fecha.strftime('%d/%m/%Y')}**. Recuerda solicitar la redacción de la próxima tanda de publicaciones pronto para no quedarte sin contenido."
            }
        return None
    except Exception:
        return None


def clasificar_tipo_kpi(kpi_medidor):
    """Clasifica el texto libre de kpi_medidor en un tipo interno. Matching por keywords."""
    t = (kpi_medidor or "").strip().lower()
    if not t:
        return "desconocido"

    if "roi" in t or "atribuidas" in t or ("gastado" in t and ("ads" in t or "carteler" in t)):
        return "roi_ads"
    if "citas" in t or ("pelu" in t and "semana" in t):
        return "citas_semana"
    if "altas" in t or ("crm" in t and ("nueva" in t or "nuevas" in t)) or "clientes nuevos" in t:
        return "altas_crm"
    if "ticket medio" in t:
        return "ticket_medio"
    if "plazas" in t or "ocupac" in t:
        return "ocupacion_talleres"
    if "facturación" in t or "facturacion" in t:
        return "facturacion_productos"
    if any(k in t for k in ("anti-estrés", "anti-estres", "calma", "pirotecnia")):
        return "packs_calma"
    return "desconocido"


def cita_esta_excluida(servicio):
    """True si la cita no debe contar (cancelada / anulada / no presentado)."""
    s = servicio or ""
    return any(e in s for e in ESTADOS_CITA_EXCLUIDOS)


def _to_date(valor):
    if valor is None:
        return None
    if isinstance(valor, date) and not isinstance(valor, datetime):
        return valor
    return pd.to_datetime(valor).date()


def _semanas_en_rango(fecha_inicio, fecha_fin):
    fi = _to_date(fecha_inicio)
    ff = _to_date(fecha_fin)
    if fi is None or ff is None:
        return 1.0
    dias = max((ff - fi).days + 1, 1)
    return max(dias / 7.0, 1.0)


def _rango_bounds(fecha_inicio, fecha_fin):
    fi = _to_date(fecha_inicio)
    ff = _to_date(fecha_fin)
    if fi is None or ff is None:
        raise ValueError("Fechas de objetivo inválidas")
    return f"{fi.isoformat()}T00:00:00", f"{ff.isoformat()}T23:59:59", fi, ff


def _fetch_paginado(make_query, page_size=1000):
    """Ejecuta una query PostgREST (factory) paginando con .range()."""
    filas = []
    offset = 0
    while True:
        res = make_query().range(offset, offset + page_size - 1).execute()
        chunk = res.data or []
        filas.extend(chunk)
        if len(chunk) < page_size:
            break
        offset += page_size
    return filas


def media_citas_por_semana(citas, fecha_inicio, fecha_fin):
    """Media semanal de citas válidas (excluye canceladas/anuladas/no presentado)."""
    validas = [c for c in (citas or []) if not cita_esta_excluida(c.get("servicio"))]
    return round(len(validas) / _semanas_en_rango(fecha_inicio, fecha_fin), 2)


def ticket_medio_de_ventas(ventas):
    """Media de total excluyendo DEVUELTO. None si no hay tickets válidos."""
    validas = [
        float(v.get("total") or 0)
        for v in (ventas or [])
        if str(v.get("estado") or "").upper() != "DEVUELTO"
    ]
    if not validas:
        return None
    return round(sum(validas) / len(validas), 2)


def suma_facturacion_ventas(ventas):
    """Suma de total excluyendo DEVUELTO."""
    total = 0.0
    for v in (ventas or []):
        if str(v.get("estado") or "").upper() == "DEVUELTO":
            continue
        total += float(v.get("total") or 0)
    return round(total, 2)


def media_ocupacion_talleres(talleres, asistentes_por_evento):
    """
    Media de % ocupación. asistentes_por_evento: dict evento_id -> count.
    None si no hay talleres con plazas > 0.
    """
    pcts = []
    for t in (talleres or []):
        plazas = int(t.get("plazas_totales") or 0)
        if plazas <= 0:
            continue
        inscritos = int(asistentes_por_evento.get(t.get("id"), 0))
        pcts.append(100.0 * inscritos / plazas)
    if not pcts:
        return None
    return round(sum(pcts) / len(pcts), 2)


def _texto_contiene_calma(texto):
    t = (texto or "").lower()
    return any(k in t for k in KEYWORDS_PACKS_CALMA)


def _nombre_producto_linea(linea):
    if not isinstance(linea, dict):
        return ""
    return str(
        linea.get("Producto")
        or linea.get("nombre")
        or linea.get("Name")
        or linea.get("producto")
        or ""
    )


def calcular_packs_calma(talleres, asistentes_por_evento, ventas):
    """
    Cuenta asistentes a talleres con keywords + unidades de líneas de venta matching.
    Si no hay ninguna entidad matching clara → None (omitir).
    """
    hubo_match = False
    total = 0

    for t in (talleres or []):
        if not _texto_contiene_calma(t.get("titulo") or ""):
            continue
        hubo_match = True
        total += int(asistentes_por_evento.get(t.get("id"), 0))

    for v in (ventas or []):
        if str(v.get("estado") or "").upper() == "DEVUELTO":
            continue
        prods = v.get("productos") or []
        if isinstance(prods, str):
            try:
                import json
                prods = json.loads(prods)
            except Exception:
                prods = []
        if not isinstance(prods, list):
            continue
        for linea in prods:
            nombre = _nombre_producto_linea(linea)
            if not _texto_contiene_calma(nombre):
                continue
            hubo_match = True
            try:
                total += int(float(linea.get("Cantidad") or linea.get("cantidad") or 1))
            except Exception:
                total += 1

    if not hubo_match:
        return None
    return float(total)


def calcular_valor_kpi(client, tipo, fecha_inicio, fecha_fin):
    """
    Calcula el valor actual de un KPI tipado desde datos TPV.
    Retorna float o None (omitir / no aplicable).
    """
    if tipo in ("roi_ads", "desconocido"):
        return None

    ini_iso, fin_iso, fi, ff = _rango_bounds(fecha_inicio, fecha_fin)

    if tipo == "citas_semana":
        citas = _fetch_paginado(
            lambda: client.table("citas").select("id, servicio, fecha_hora")
            .gte("fecha_hora", ini_iso).lte("fecha_hora", fin_iso)
        )
        return media_citas_por_semana(citas, fi, ff)

    if tipo == "altas_crm":
        clientes = _fetch_paginado(
            lambda: client.table("clientes").select("id, created_at")
            .gte("created_at", ini_iso).lte("created_at", fin_iso)
        )
        return float(len(clientes))

    if tipo == "ticket_medio":
        ventas = _fetch_paginado(
            lambda: client.table("ventas_historial").select("id, total, estado, created_at")
            .gte("created_at", ini_iso).lte("created_at", fin_iso)
        )
        return ticket_medio_de_ventas(ventas)

    if tipo == "facturacion_productos":
        ventas = _fetch_paginado(
            lambda: client.table("ventas_historial").select("id, total, estado, created_at")
            .gte("created_at", ini_iso).lte("created_at", fin_iso)
        )
        return suma_facturacion_ventas(ventas)

    if tipo == "ocupacion_talleres":
        talleres = _fetch_paginado(
            lambda: client.table("eventos_talleres").select("id, titulo, fecha, plazas_totales")
            .gte("fecha", fi.isoformat()).lte("fecha", ff.isoformat())
        )
        if not talleres:
            return None
        asistentes_por_evento = {}
        for t in talleres:
            res = client.table("eventos_asistentes").select("id").eq("evento_id", t["id"]).execute()
            asistentes_por_evento[t["id"]] = len(res.data or [])
        return media_ocupacion_talleres(talleres, asistentes_por_evento)

    if tipo == "packs_calma":
        talleres = _fetch_paginado(
            lambda: client.table("eventos_talleres").select("id, titulo, fecha, plazas_totales")
            .gte("fecha", fi.isoformat()).lte("fecha", ff.isoformat())
        )
        asistentes_por_evento = {}
        for t in talleres:
            res = client.table("eventos_asistentes").select("id").eq("evento_id", t["id"]).execute()
            asistentes_por_evento[t["id"]] = len(res.data or [])
        ventas = _fetch_paginado(
            lambda: client.table("ventas_historial").select("id, total, estado, productos, created_at")
            .gte("created_at", ini_iso).lte("created_at", fin_iso)
        )
        return calcular_packs_calma(talleres, asistentes_por_evento, ventas)

    return None


def sincronizar_objetivos_desde_tpv(client, objetivos=None):
    """
    Recalcula valor_actual de objetivos En progreso desde datos TPV.
    Solo escribe si el cálculo no es None. No cambia estado.
    Retorna lista de {id, titulo, valor_antes, valor_despues, accion}.
    """
    if objetivos is None:
        res = client.table("marketing_objetivos").select("*").execute()
        objetivos = res.data or []

    resumen = []
    for obj in objetivos:
        if (obj.get("estado") or "") != "En progreso":
            continue

        oid = obj.get("id")
        titulo = obj.get("titulo") or ""
        valor_antes = obj.get("valor_actual")
        kpi = obj.get("kpi_medidor") or ""
        tipo = clasificar_tipo_kpi(kpi)

        try:
            nuevo = calcular_valor_kpi(
                client, tipo, obj.get("fecha_inicio"), obj.get("fecha_fin")
            )
        except Exception as exc:
            resumen.append({
                "id": oid,
                "titulo": titulo,
                "valor_antes": valor_antes,
                "valor_despues": valor_antes,
                "accion": "error",
                "detalle": str(exc),
            })
            continue

        if nuevo is None:
            resumen.append({
                "id": oid,
                "titulo": titulo,
                "valor_antes": valor_antes,
                "valor_despues": valor_antes,
                "accion": "omitido",
                "detalle": tipo,
            })
            continue

        client.table("marketing_objetivos").update(
            {"valor_actual": float(nuevo)}
        ).eq("id", oid).execute()

        resumen.append({
            "id": oid,
            "titulo": titulo,
            "valor_antes": valor_antes,
            "valor_despues": float(nuevo),
            "accion": "actualizado",
            "detalle": tipo,
        })

    return resumen
