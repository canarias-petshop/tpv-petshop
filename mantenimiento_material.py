"""UI: submódulo de mantenimiento de material (dentro de Tareas)."""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import time
from datetime import date, timedelta
import calendar
from html import escape as html_escape

from core_mantenimiento import (
    FRECUENCIAS,
    TIPOS_MANTENIMIENTO,
    CATEGORIAS_MATERIAL,
    DIAS_SEMANA_LABELS,
    TIPOS_MOVIMIENTO,
    calcular_siguiente_fecha,
    siguiente_tras_completar,
    proyectar_fechas_plan,
    construir_etiqueta,
    asegurar_ejecuciones_abiertas,
    resumen_mantenimientos_por_dia,
    _as_date,
)


@st.cache_data(show_spinner=False, ttl=120)
def fetch_materiales(_client, v=0):
    try:
        return _client.table("mantenimiento_materiales").select("*").order("nombre").execute().data or []
    except Exception:
        return []


@st.cache_data(show_spinner=False, ttl=120)
def fetch_planes(_client, v=0):
    try:
        return _client.table("mantenimiento_planes").select(
            "*, mantenimiento_materiales(nombre, categoria, activo)"
        ).order("id", desc=True).execute().data or []
    except Exception:
        return []


@st.cache_data(show_spinner=False, ttl=60)
def fetch_ejecuciones_rango(_client, v, f_ini, f_fin):
    try:
        return _client.table("mantenimiento_ejecuciones").select(
            "*, mantenimiento_planes(tipo_mantenimiento, frecuencia_tipo, material_id, mantenimiento_materiales(nombre))"
        ).gte("fecha_programada", f_ini).lte("fecha_programada", f_fin).execute().data or []
    except Exception:
        return []


@st.cache_data(show_spinner=False, ttl=60)
def fetch_ejecuciones_abiertas(_client, v):
    try:
        return _client.table("mantenimiento_ejecuciones").select(
            "*, mantenimiento_planes(tipo_mantenimiento, frecuencia_tipo, material_id, dias_semana, fecha_inicio, mantenimiento_materiales(nombre))"
        ).in_("estado", ["Pendiente", "Atrasado"]).order("fecha_programada").execute().data or []
    except Exception:
        return []


@st.cache_data(show_spinner=False, ttl=120)
def fetch_movimientos(_client, v=0):
    try:
        return _client.table("mantenimiento_movimientos").select(
            "*, mantenimiento_materiales(nombre)"
        ).order("fecha", desc=True).limit(80).execute().data or []
    except Exception:
        return []


def limpiar_cache_mantenimiento():
    fetch_materiales.clear()
    fetch_planes.clear()
    fetch_ejecuciones_rango.clear()
    fetch_ejecuciones_abiertas.clear()
    fetch_movimientos.clear()


def _plan_label(p):
    mat = (p.get("mantenimiento_materiales") or {})
    nombre = mat.get("nombre") if isinstance(mat, dict) else None
    if not nombre:
        nombre = f"Material #{p.get('material_id')}"
    return construir_etiqueta(nombre, p.get("tipo_mantenimiento") or "Mantenimiento")


def sincronizar_ejecuciones(client, hoy=None, horizonte_dias=21):
    """Crea en BD las ejecuciones pendientes que faltan según los planes activos."""
    hoy = hoy or date.today()
    v = st.session_state.get("db_version", 0)
    planes = [p for p in fetch_planes(client, v) if p.get("activo", True)]
    # Ejecuciones en ventana amplia (incluye atrasados de hasta 60 días)
    f_ini = str(hoy - timedelta(days=60))
    f_fin = str(hoy + timedelta(days=horizonte_dias))
    existentes = fetch_ejecuciones_rango(client, v, f_ini, f_fin)
    nuevas = asegurar_ejecuciones_abiertas(planes, existentes, hoy=hoy, horizonte_dias=horizonte_dias)
    inserts = []
    for n in nuevas:
        inserts.append({
            "plan_id": n["plan_id"],
            "fecha_programada": n["fecha_programada"],
            "estado": n["estado"],
        })
    if inserts:
        # Insertar en lotes; ignorar conflictos de unique si PostgREST los devuelve
        try:
            client.table("mantenimiento_ejecuciones").insert(inserts).execute()
        except Exception:
            for row in inserts:
                try:
                    client.table("mantenimiento_ejecuciones").insert(row).execute()
                except Exception:
                    pass
        st.session_state.db_version = st.session_state.get("db_version", 0) + 1
        limpiar_cache_mantenimiento()
    # Actualizar estados Atrasado de pendientes viejos
    try:
        abiertas = fetch_ejecuciones_abiertas(client, st.session_state.get("db_version", 0))
        for e in abiertas:
            fp = _as_date(e.get("fecha_programada"))
            if fp and fp < hoy and e.get("estado") == "Pendiente":
                client.table("mantenimiento_ejecuciones").update({"estado": "Atrasado"}).eq("id", e["id"]).execute()
        limpiar_cache_mantenimiento()
    except Exception:
        pass
    return len(inserts)


def items_para_calendario_general(client, f_ini, f_fin):
    """Lista plana para pintar resumen en el calendario general de tareas."""
    v = st.session_state.get("db_version", 0)
    rows = fetch_ejecuciones_rango(client, v, str(f_ini), str(f_fin))
    items = []
    for e in rows:
        plan = e.get("mantenimiento_planes") or {}
        mat = plan.get("mantenimiento_materiales") if isinstance(plan, dict) else {}
        nombre = (mat or {}).get("nombre") if isinstance(mat, dict) else "Material"
        tipo = (plan or {}).get("tipo_mantenimiento") if isinstance(plan, dict) else "Mantenimiento"
        items.append({
            "fecha_programada": e.get("fecha_programada"),
            "estado": e.get("estado"),
            "etiqueta": construir_etiqueta(nombre or "Material", tipo or "Mantenimiento"),
        })
    return items


def render_html_resumen_dia(items_dia, fecha_obj):
    """HTML compacto para incrustar en celdas del calendario general."""
    r = resumen_mantenimientos_por_dia(items_dia, fecha_obj)
    if r["total"] == 0:
        return ""
    color = "#c62828" if r["atrasados"] else ("#ef6c00" if r["pendientes"] else "#2e7d32")
    bg = "#ffebee" if r["atrasados"] else ("#fff3e0" if r["pendientes"] else "#e8f5e9")
    titulo = " · ".join(r["etiquetas"][:3])
    if len(r["etiquetas"]) > 3:
        titulo += "…"
    label = f"🛠️ {r['total']} mant."
    if r["atrasados"]:
        label = f"🚨 {r['atrasados']} atrasado(s)"
    elif r["pendientes"]:
        label = f"🛠️ {r['pendientes']} pendiente(s)"
    else:
        label = f"✅ {r['hechos']} hecho(s)"
    return (
        f"<div style='font-size:0.75em;font-weight:bold;color:{color};background:{bg};"
        f"padding:2px 4px;border-radius:3px;margin-top:4px;' title='{titulo}'>{label}</div>"
    )


def render_mantenimiento_material(client, empleados=None, mapa_emp=None, mapa_emp_inv=None):
    empleados = empleados or []
    mapa_emp = mapa_emp or {}
    mapa_emp_inv = mapa_emp_inv or {}

    st.markdown("#### 🛠️ Mantenimiento de Material")
    st.info(
        "Programa limpiezas, desinfecciones, afilados y revisiones. "
        "Lo pendiente **sigue avisando hasta marcarlo como hecho**."
    )

    # Sync silencioso al abrir
    try:
        sincronizar_ejecuciones(client)
    except Exception as e:
        st.warning(f"No se pudieron sincronizar pendientes automáticamente: {e}")

    v = st.session_state.get("db_version", 0)
    pest = st.radio(
        "Mantenimiento:",
        ["📋 Pendientes", "📅 Calendario", "🧰 Materiales y planes", "🚚 Salidas / taller"],
        horizontal=True,
        label_visibility="collapsed",
        key="mant_subpest",
    )

    materiales = fetch_materiales(client, v)
    planes = fetch_planes(client, v)
    mapa_mat = {m["id"]: m for m in materiales}

    # ---------- PENDIENTES ----------
    if pest == "📋 Pendientes":
        abiertas = fetch_ejecuciones_abiertas(client, st.session_state.get("db_version", 0))
        if not abiertas:
            st.success("🎉 No hay mantenimientos pendientes ni atrasados.")
        else:
            filas = []
            for e in abiertas:
                plan = e.get("mantenimiento_planes") or {}
                mat = plan.get("mantenimiento_materiales") if isinstance(plan, dict) else {}
                nombre = (mat or {}).get("nombre") if isinstance(mat, dict) else "?"
                filas.append({
                    "id": e["id"],
                    "plan_id": e["plan_id"],
                    "¡Hecho!": False,
                    "Fecha": str(e.get("fecha_programada")),
                    "Estado": e.get("estado"),
                    "Material": nombre,
                    "Tarea": plan.get("tipo_mantenimiento") if isinstance(plan, dict) else "",
                    "Frecuencia": plan.get("frecuencia_tipo") if isinstance(plan, dict) else "",
                    "Notas": e.get("notas") or "",
                    "Detalle técnico": e.get("detalle_tecnico") or "",
                })
            df = pd.DataFrame(filas)
            quien = st.selectbox(
                "Quién marca (opcional):",
                ["—"] + [e["nombre"] for e in empleados],
                key="mant_quien_marca",
            )
            ed = st.data_editor(
                df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "id": None,
                    "plan_id": None,
                    "¡Hecho!": st.column_config.CheckboxColumn("✅ Hecho"),
                    "Estado": st.column_config.TextColumn("Estado", disabled=True),
                    "Notas": st.column_config.TextColumn("📝 Notas"),
                    "Detalle técnico": st.column_config.TextColumn("🔧 Detalle (afilado, piezas…)"),
                },
                key="ed_mant_pend",
            )
            if st.button("💾 Registrar mantenimientos hechos", type="primary", use_container_width=True):
                hechos = ed[ed["¡Hecho!"] == True]
                if hechos.empty:
                    st.warning("Marca al menos una fila.")
                else:
                    emp_id = mapa_emp.get(quien) if quien != "—" else None
                    hoy = date.today()
                    n = 0
                    for _, r in hechos.iterrows():
                        client.table("mantenimiento_ejecuciones").update({
                            "estado": "Hecho",
                            "fecha_realizada": str(hoy),
                            "notas": str(r.get("Notas") or ""),
                            "detalle_tecnico": str(r.get("Detalle técnico") or ""),
                            "empleado_id": emp_id,
                        }).eq("id", int(r["id"])).execute()

                        # Recalcular próxima del plan
                        plan_row = next((p for p in planes if p["id"] == int(r["plan_id"])), None)
                        if plan_row:
                            freq = plan_row.get("frecuencia_tipo") or "Mensual"
                            dias = plan_row.get("dias_semana") or []
                            f_ini = _as_date(plan_row.get("fecha_inicio")) or hoy
                            nxt = siguiente_tras_completar(freq, hoy, dias, f_ini)
                            upd = {"ultima_ejecucion": str(hoy)}
                            if nxt:
                                upd["proxima_ejecucion"] = str(nxt)
                            else:
                                upd["proxima_ejecucion"] = None
                                upd["activo"] = False if freq == "Puntual" else plan_row.get("activo", True)
                            client.table("mantenimiento_planes").update(upd).eq("id", int(r["plan_id"])).execute()
                        n += 1
                    st.session_state.db_version = st.session_state.get("db_version", 0) + 1
                    limpiar_cache_mantenimiento()
                    try:
                        sincronizar_ejecuciones(client)
                    except Exception:
                        pass
                    st.success(f"Registrados {n} mantenimiento(s)."); time.sleep(0.7); st.rerun()

    # ---------- CALENDARIO ----------
    elif pest == "📅 Calendario":
        c1, c2 = st.columns([1, 3])
        with c1:
            vista = st.radio("Vista", ["Semanal", "Mensual"], horizontal=True, key="mant_vista_cal")
            ref = st.date_input("Fecha ref.", value=date.today(), key="mant_ref_cal")
        if vista == "Semanal":
            start = ref - timedelta(days=ref.weekday())
            end = start + timedelta(days=6)
        else:
            start = date(ref.year, ref.month, 1)
            _, nd = calendar.monthrange(ref.year, ref.month)
            end = date(ref.year, ref.month, nd)

        # Combinar ejecuciones BD + proyección de planes activos
        rows = fetch_ejecuciones_rango(client, st.session_state.get("db_version", 0), str(start), str(end))
        by_day = {}
        for e in rows:
            fp = str(e.get("fecha_programada"))
            plan = e.get("mantenimiento_planes") or {}
            mat = plan.get("mantenimiento_materiales") if isinstance(plan, dict) else {}
            nombre = (mat or {}).get("nombre") if isinstance(mat, dict) else "?"
            tipo = plan.get("tipo_mantenimiento") if isinstance(plan, dict) else "?"
            est = e.get("estado") or "Pendiente"
            by_day.setdefault(fp, []).append({"est": est, "label": construir_etiqueta(nombre, tipo)})

        # También proyectar planes sin ejecución aún
        for p in planes:
            if not p.get("activo", True):
                continue
            f_ini = _as_date(p.get("fecha_inicio")) or start
            dias = p.get("dias_semana") or []
            for f in proyectar_fechas_plan(p.get("frecuencia_tipo") or "Mensual", f_ini, start, end, dias):
                key = str(f)
                lab = _plan_label(p)
                existentes_labs = [x["label"] for x in by_day.get(key, [])]
                if lab not in existentes_labs:
                    by_day.setdefault(key, []).append({"est": "Programado", "label": lab})

        if vista == "Semanal":
            dias_n = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            html = (
                "<style>"
                ".mcal{width:100%;border-collapse:collapse;table-layout:fixed;font-size:13px;background:#fff;font-family:sans-serif}"
                ".mcal th{background:#37474f;color:#fff;padding:6px;border:1px solid #ddd}"
                ".mcal td{border:1px solid #ddd;vertical-align:top;padding:5px;height:110px;background:#fafafa}"
                ".mhead{font-weight:bold;margin-bottom:4px;border-bottom:1px solid #eee}"
                ".mtoday{background:#fffde7!important;border:2px solid #fbc02d!important}"
                ".mcard{background:#fff;border-left:4px solid #ef6c00;padding:4px;margin-bottom:4px;border-radius:3px;font-size:.8em}"
                ".m-atras{border-left-color:#c62828}.m-hecho{border-left-color:#2e7d32;opacity:.75}"
                ".m-prog{border-left-color:#90a4ae}"
                "</style><table class='mcal'><tr>"
            )
            for d in dias_n:
                html += f"<th>{d}</th>"
            html += "</tr><tr>"
            hoy_s = str(date.today())
            for i in range(7):
                d_obj = start + timedelta(days=i)
                d_s = str(d_obj)
                cls = "mtoday" if d_s == hoy_s else ""
                html += f"<td class='{cls}'><div class='mhead'>{d_obj.strftime('%d/%m')}</div>"
                for it in by_day.get(d_s, []):
                    est = it["est"]
                    c = "m-atras" if est == "Atrasado" else ("m-hecho" if est == "Hecho" else ("m-prog" if est == "Programado" else ""))
                    icon = "🚨" if est == "Atrasado" else ("✅" if est == "Hecho" else ("📌" if est == "Programado" else "⏳"))
                    lab = html_escape(str(it["label"]))
                    html += f"<div class='mcard {c}'>{icon} {lab}</div>"
                html += "</td>"
            html += "</tr></table>"
            components.html(html, height=320, scrolling=True)
        else:
            html = (
                "<style>"
                ".mcal{width:100%;border-collapse:collapse;table-layout:fixed;font-size:12px;background:#fff;font-family:sans-serif}"
                ".mcal th{background:#37474f;color:#fff;padding:6px;border:1px solid #ddd}"
                ".mcal td{border:1px solid #ddd;vertical-align:top;padding:4px;height:85px;background:#fafafa}"
                ".mhead{font-weight:bold;margin-bottom:2px}"
                ".mtoday{background:#fffde7!important;border:2px solid #fbc02d!important}"
                ".mcard{background:#fff;border-left:3px solid #ef6c00;padding:2px;margin-bottom:2px;font-size:.7em}"
                ".m-atras{border-left-color:#c62828}.m-hecho{border-left-color:#2e7d32}"
                "</style><table class='mcal'><tr>"
                "<th>Lun</th><th>Mar</th><th>Mié</th><th>Jue</th><th>Vie</th><th>Sáb</th><th>Dom</th>"
                "</tr><tr>"
            )
            first_wd = start.weekday()
            for _ in range(first_wd):
                html += "<td></td>"
            col = first_wd
            hoy_s = str(date.today())
            d = start
            while d <= end:
                cls = "mtoday" if str(d) == hoy_s else ""
                html += f"<td class='{cls}'><div class='mhead'>{d.day}</div>"
                for it in by_day.get(str(d), [])[:4]:
                    est = it["est"]
                    c = "m-atras" if est == "Atrasado" else ("m-hecho" if est == "Hecho" else "")
                    lab = html_escape(str(it["label"]))
                    short = html_escape(str(it["label"])[:22])
                    html += f"<div class='mcard {c}' title='{lab}'>{short}</div>"
                html += "</td>"
                col += 1
                if col == 7:
                    html += "</tr><tr>"
                    col = 0
                d += timedelta(days=1)
            while col < 7 and col > 0:
                html += "<td></td>"
                col += 1
            html += "</tr></table>"
            components.html(html, height=560, scrolling=True)

    # ---------- MATERIALES Y PLANES ----------
    elif pest == "🧰 Materiales y planes":
        c_a, c_b = st.columns(2)
        with c_a:
            st.markdown("##### ➕ Alta de material")
            with st.form("form_nuevo_material", clear_on_submit=True):
                m_nombre = st.text_input("Nombre *", placeholder="Ej: Máquina de rapar A")
                m_cat = st.selectbox("Categoría", CATEGORIAS_MATERIAL)
                m_ubi = st.text_input("Ubicación", placeholder="Peluquería / Armario 2")
                m_notas = st.text_area("Notas", height=70)
                if st.form_submit_button("Guardar material", type="primary", use_container_width=True):
                    if m_nombre.strip():
                        client.table("mantenimiento_materiales").insert({
                            "nombre": m_nombre.strip(),
                            "categoria": m_cat,
                            "ubicacion": m_ubi or None,
                            "notas": m_notas or None,
                            "activo": True,
                        }).execute()
                        st.session_state.db_version = st.session_state.get("db_version", 0) + 1
                        limpiar_cache_mantenimiento()
                        st.success("Material guardado."); time.sleep(0.5); st.rerun()
                    else:
                        st.warning("El nombre es obligatorio.")

            st.markdown("##### 📦 Materiales")
            if materiales:
                df_m = pd.DataFrame(materiales)
                vista_m = df_m[["id", "nombre", "categoria", "ubicacion", "activo", "notas"]].copy()
                vista_m.insert(0, "Borrar", False)
                ed_m = st.data_editor(
                    vista_m, hide_index=True, use_container_width=True, height=260,
                    column_config={"id": None, "Borrar": st.column_config.CheckboxColumn("🗑️", width="small")},
                    key="ed_mant_mats",
                )
                if st.button("💾 Guardar cambios materiales"):
                    for _, rb in ed_m[ed_m["Borrar"] == True].iterrows():
                        client.table("mantenimiento_materiales").update({"activo": False}).eq("id", int(rb["id"])).execute()
                    for _, rv in ed_m[ed_m["Borrar"] == False].iterrows():
                        client.table("mantenimiento_materiales").update({
                            "nombre": rv["nombre"],
                            "categoria": rv["categoria"],
                            "ubicacion": rv["ubicacion"],
                            "activo": bool(rv["activo"]),
                            "notas": rv["notas"],
                        }).eq("id", int(rv["id"])).execute()
                    st.session_state.db_version = st.session_state.get("db_version", 0) + 1
                    limpiar_cache_mantenimiento()
                    st.success("Materiales actualizados."); time.sleep(0.5); st.rerun()
            else:
                st.caption("Aún no hay materiales. Da de alta el primero a la izquierda.")

        with c_b:
            st.markdown("##### ➕ Plan de mantenimiento")
            mats_activos = [m for m in materiales if m.get("activo", True)]
            if not mats_activos:
                st.warning("Primero crea al menos un material.")
            else:
                with st.form("form_nuevo_plan", clear_on_submit=True):
                    opts = {f"{m['nombre']} ({m.get('categoria')})": m["id"] for m in mats_activos}
                    p_mat_label = st.selectbox("Material *", list(opts.keys()))
                    p_tipo = st.selectbox("Tipo de mantenimiento", TIPOS_MANTENIMIENTO)
                    p_freq = st.selectbox("Frecuencia", FRECUENCIAS)
                    dias_sel = []
                    if p_freq == "2 veces por semana":
                        dias_sel = st.multiselect(
                            "Días de la semana",
                            options=list(range(7)),
                            default=[0, 3],
                            format_func=lambda i: DIAS_SEMANA_LABELS[i],
                        )
                    p_inicio = st.date_input("Fecha de inicio / primera vez", value=date.today())
                    p_rol = st.selectbox("Asignado a (rol)", ["Rol: Peluquería", "Rol: Tienda / Dependiente", "Cualquiera / Todos"])
                    p_notas = st.text_area("Notas del plan", height=60)
                    if st.form_submit_button("Crear plan", type="primary", use_container_width=True):
                        mat_id = opts[p_mat_label]
                        if p_freq == "2 veces por semana" and len(dias_sel) < 2:
                            st.warning("Elige al menos 2 días.")
                        else:
                            prox = calcular_siguiente_fecha(p_freq, p_inicio, dias_sel, p_inicio)
                            client.table("mantenimiento_planes").insert({
                                "material_id": mat_id,
                                "tipo_mantenimiento": p_tipo,
                                "frecuencia_tipo": p_freq,
                                "dias_semana": dias_sel if p_freq == "2 veces por semana" else [],
                                "fecha_inicio": str(p_inicio),
                                "proxima_ejecucion": str(prox) if prox else str(p_inicio),
                                "activo": True,
                                "rol_asignado": p_rol,
                                "notas": p_notas or None,
                            }).execute()
                            st.session_state.db_version = st.session_state.get("db_version", 0) + 1
                            limpiar_cache_mantenimiento()
                            try:
                                sincronizar_ejecuciones(client)
                            except Exception:
                                pass
                            st.success("Plan creado."); time.sleep(0.5); st.rerun()

            st.markdown("##### ⚙️ Planes activos")
            planes_act = [p for p in planes if p.get("activo", True)]
            if planes_act:
                rows_p = []
                for p in planes_act:
                    mat = p.get("mantenimiento_materiales") or {}
                    dias = p.get("dias_semana") or []
                    dias_txt = ", ".join(DIAS_SEMANA_LABELS[i] for i in dias) if dias else "—"
                    rows_p.append({
                        "id": p["id"],
                        "Desactivar": False,
                        "Material": mat.get("nombre") if isinstance(mat, dict) else "?",
                        "Tipo": p.get("tipo_mantenimiento"),
                        "Frecuencia": p.get("frecuencia_tipo"),
                        "Días": dias_txt,
                        "Próxima": str(p.get("proxima_ejecucion") or ""),
                        "Última": str(p.get("ultima_ejecucion") or "—"),
                        "Notas": p.get("notas") or "",
                    })
                df_p = pd.DataFrame(rows_p)
                ed_p = st.data_editor(
                    df_p, hide_index=True, use_container_width=True, height=280,
                    column_config={"id": None, "Desactivar": st.column_config.CheckboxColumn("⏹️")},
                    key="ed_mant_planes",
                )
                if st.button("⏹️ Desactivar planes marcados"):
                    for _, rb in ed_p[ed_p["Desactivar"] == True].iterrows():
                        client.table("mantenimiento_planes").update({"activo": False}).eq("id", int(rb["id"])).execute()
                    st.session_state.db_version = st.session_state.get("db_version", 0) + 1
                    limpiar_cache_mantenimiento()
                    st.success("Planes desactivados."); time.sleep(0.5); st.rerun()
            else:
                st.caption("No hay planes activos.")

    # ---------- MOVIMIENTOS / TALLER ----------
    elif pest == "🚚 Salidas / taller":
        st.markdown("##### Registrar salida, afilado o incidencia")
        mats_activos = [m for m in materiales if m.get("activo", True)]
        if not mats_activos:
            st.warning("Necesitas materiales dados de alta.")
            return
        with st.form("form_mant_mov", clear_on_submit=True):
            opts = {m["nombre"]: m["id"] for m in mats_activos}
            mov_mat = st.selectbox("Material", list(opts.keys()))
            mov_tipo = st.selectbox("Tipo", TIPOS_MOVIMIENTO)
            mov_fecha = st.date_input("Fecha", value=date.today())
            mov_det = st.text_area("Detalle *", placeholder="Ej: Cuchillas 10F y 7F salen a afilar; vuelven el viernes")
            mov_est = st.selectbox("Estado", ["Abierto", "Cerrado"])
            if st.form_submit_button("Guardar registro", type="primary"):
                if mov_det.strip():
                    client.table("mantenimiento_movimientos").insert({
                        "material_id": opts[mov_mat],
                        "tipo_movimiento": mov_tipo,
                        "fecha": str(mov_fecha),
                        "detalle": mov_det.strip(),
                        "estado": mov_est,
                    }).execute()
                    st.session_state.db_version = st.session_state.get("db_version", 0) + 1
                    limpiar_cache_mantenimiento()
                    st.success("Registrado."); time.sleep(0.5); st.rerun()
                else:
                    st.warning("El detalle es obligatorio.")

        movs = fetch_movimientos(client, st.session_state.get("db_version", 0))
        if movs:
            hist = []
            for m in movs:
                mat = m.get("mantenimiento_materiales") or {}
                hist.append({
                    "id": m["id"],
                    "Cerrar": False,
                    "Fecha": str(m.get("fecha")),
                    "Material": mat.get("nombre") if isinstance(mat, dict) else "?",
                    "Tipo": m.get("tipo_movimiento"),
                    "Estado": m.get("estado"),
                    "Detalle": m.get("detalle"),
                })
            ed_h = st.data_editor(
                pd.DataFrame(hist), hide_index=True, use_container_width=True,
                column_config={"id": None, "Cerrar": st.column_config.CheckboxColumn("✅ Cerrar")},
                key="ed_mant_movs",
            )
            if st.button("Marcar seleccionados como cerrados"):
                for _, r in ed_h[ed_h["Cerrar"] == True].iterrows():
                    client.table("mantenimiento_movimientos").update({"estado": "Cerrado"}).eq("id", int(r["id"])).execute()
                st.session_state.db_version = st.session_state.get("db_version", 0) + 1
                limpiar_cache_mantenimiento()
                st.success("Actualizado."); time.sleep(0.5); st.rerun()
        else:
            st.caption("Sin movimientos todavía.")
