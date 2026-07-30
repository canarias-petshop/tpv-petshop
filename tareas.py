import streamlit as st
import pandas as pd
import time
from datetime import date, timedelta
import calendar

def generar_proyeccion_virtual(todas_tareas, fecha_inicio, fecha_fin):
    from core_tareas import generar_proyeccion_virtual as gpv
    return gpv(todas_tareas, fecha_inicio, fecha_fin)

@st.cache_data(show_spinner=False, ttl=300)
def fetch_empleados_activos(_client):
    res = _client.table("personal_empleados").select("id, nombre").eq("activo", True).execute()
    return res.data if res.data else []

@st.cache_data(show_spinner=False, ttl=300)
def fetch_tareas_plannings_activos(_client):
    res = _client.table("tareas_plannings").select("*").eq("activo", True).order("id", desc=True).execute()
    return res.data if res.data else []

@st.cache_data(show_spinner=False, ttl=300)
def fetch_tareas_registro_rango(_client, start, end):
    res = _client.table("tareas_registro").select("tarea_id, fecha_completada, notas, personal_empleados(nombre)").gte("fecha_completada", start).lte("fecha_completada", end).execute()
    return res.data if res.data else []

@st.cache_data(show_spinner=False, ttl=300)
def fetch_tareas_registro_hoy(_client, hoy_str):
    res = _client.table("tareas_registro").select("tarea_id").eq("fecha_completada", hoy_str).execute()
    return res.data if res.data else []

@st.cache_data(show_spinner=False, ttl=300)
def fetch_tareas_duenos_rango(_client, start, end):
    res = _client.table("tareas_duenos").select("*").gte("fecha_programada", start).lte("fecha_programada", end).execute()
    return res.data if res.data else []

@st.cache_data(show_spinner=False, ttl=300)
def fetch_tareas_duenos_all(_client):
    res = _client.table("tareas_duenos").select("*").order("fecha_programada", desc=False).execute()
    return res.data if res.data else []

@st.cache_data(show_spinner=False, ttl=300)
def fetch_tareas_historial(_client):
    res = _client.table("tareas_registro").select("fecha_completada, notas, personal_empleados(nombre), tareas_plannings(tarea, periodicidad)").order("fecha_completada", desc=True).limit(100).execute()
    return res.data if res.data else []

def limpiar_cache_tareas():
    fetch_tareas_plannings_activos.clear()
    fetch_tareas_registro_rango.clear()
    fetch_tareas_registro_hoy.clear()
    fetch_tareas_duenos_rango.clear()
    fetch_tareas_duenos_all.clear()
    fetch_tareas_historial.clear()

def render_pestana_tareas(client):
    if 'llave_tarea_plan' not in st.session_state: st.session_state.llave_tarea_plan = 0
    if 'llave_tarea_due' not in st.session_state: st.session_state.llave_tarea_due = 0

    st.markdown("<h3 style='margin-top: -15px;'>✅ Planificación y Tareas</h3>", unsafe_allow_html=True)
    
    is_admin = st.session_state.get('rol') == 'Admin'
    
    # Extraer empleados activos de la base de datos
    try:
        empleados = fetch_empleados_activos(client)
        mapa_emp = {e['nombre']: e['id'] for e in empleados}
        mapa_emp_inv = {e['id']: e['nombre'] for e in empleados}
    except:
        empleados, mapa_emp, mapa_emp_inv = [], {}, {}
        
    opciones_rol = ["Cualquiera / Todos", "Rol: Tienda / Dependiente", "Rol: Peluquería"]
    opciones_asignacion = opciones_rol + [f"👤 {e['nombre']}" for e in empleados]

    if is_admin:
        opciones_seccion = [
            "📅 1. Calendario General",
            "👤 2. Mi Ficha de Trabajo",
            "📝 3. Notas Internas",
            "🛠️ 4. Mantenimiento Material",
            "⚙️ 5. Gestión y Dueños",
        ]
    else:
        opciones_seccion = [
            "📅 1. Calendario General",
            "👤 2. Mi Ficha de Trabajo",
            "📝 3. Notas Internas",
            "🛠️ 4. Mantenimiento Material",
        ]
        
    seccion_tareas = st.radio("Sección Tareas:", opciones_seccion, horizontal=True, label_visibility="collapsed")

    if seccion_tareas == "🛠️ 4. Mantenimiento Material":
        from mantenimiento_material import render_mantenimiento_material
        render_mantenimiento_material(client, empleados, mapa_emp, mapa_emp_inv)
        return
        
    if seccion_tareas == "📅 1. Calendario General":
        st.markdown("#### 📅 Calendario General de Plannings")
        st.info("Visión global de todas las rutinas de la tienda para esta semana. Incluye resumen de mantenimiento de material.")
        c_cale1, c_cale2 = st.columns([1, 3])
        with c_cale1:
            dia_ref_emp = st.date_input("Ver semana del:", value=date.today(), key="sem_ref_emp")
        
        start_week_emp = dia_ref_emp - timedelta(days=dia_ref_emp.weekday())
        end_week_emp = start_week_emp + timedelta(days=6)

        mant_items = []
        try:
            from mantenimiento_material import items_para_calendario_general, render_html_resumen_dia, sincronizar_ejecuciones
            try:
                sincronizar_ejecuciones(client)
            except Exception:
                pass
            mant_items = items_para_calendario_general(client, start_week_emp, end_week_emp)
        except Exception:
            mant_items = []
            render_html_resumen_dia = None
        
        try:
            plan_activos = fetch_tareas_plannings_activos(client)
            registros_sem = fetch_tareas_registro_rango(client, str(start_week_emp), str(end_week_emp))
        except:
            plan_activos = []
            registros_sem = []
        
        dias_semana_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        html_cal_emp = '''
        <style>
            .cal-emp-table { width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 13px; background-color: white; margin-bottom: 20px;}
            .cal-emp-table th { background-color: #005275; color: white; padding: 6px; text-align: center; border: 1px solid #ddd; }
            .cal-emp-table td { border: 1px solid #ddd; vertical-align: top; padding: 5px; height: 100px; background-color: #fafafa; }
            .day-head-emp { font-weight: bold; font-size: 1.1em; color: #333; margin-bottom: 5px; border-bottom: 1px solid #eee; padding-bottom: 2px;}
            .td-today-emp { background-color: #fffde7 !important; border: 2px solid #fbc02d !important; }
            .tarea-emp-card { background-color: white; border-left: 4px solid #f57c00; padding: 5px; margin-bottom: 5px; border-radius: 3px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); font-size: 0.8em; line-height: 1.2; word-wrap: break-word;}
            .te-pend { border-left-color: #f57c00; }
            .te-comp { border-left-color: #4caf50; opacity: 0.8; }
            .te-asig { font-size: 0.85em; color: #666; display: block; margin-top: 2px;}
            .te-who { font-size: 0.85em; color: #2e7d32; display: block; margin-top: 2px; font-weight: bold;}
            .te-tipo { font-size: 0.75em; display: inline-block; padding: 1px 4px; border-radius: 3px; background: #e0e0e0; margin-top: 3px; margin-right: 3px; color: #333;}
            .te-tramo { font-size: 0.75em; display: inline-block; padding: 1px 4px; border-radius: 3px; background: #e3f2fd; margin-top: 3px; color: #1565c0;}
        </style>
        <table class="cal-emp-table"><tr>
        '''
        for d_name in dias_semana_nombres: html_cal_emp += f"<th>{d_name}</th>"
        html_cal_emp += "</tr><tr>"
        
        hoy_str_emp = str(date.today())
        for i in range(7):
            d_obj = start_week_emp + timedelta(days=i)
            d_str = str(d_obj)
            td_class = "td-today-emp" if d_str == hoy_str_emp else ""
            
            html_cal_emp += f"<td class='{td_class}'>"
            html_cal_emp += f"<div class='day-head-emp'>{d_obj.strftime('%d/%m')}</div>"

            if render_html_resumen_dia and mant_items:
                html_cal_emp += render_html_resumen_dia(mant_items, d_obj)
            
            regs_dia = [r for r in registros_sem if r.get('fecha_completada') == d_str]
            hechas_ids_dia = {r['tarea_id']: r for r in regs_dia}
            
            tareas_dia_cats = {}
            for p in plan_activos:
                created_date = str(p.get('created_at', '2000-01-01'))[:10]
                aplica = False
                if d_str >= created_date:
                    if p.get('periodicidad') == 'Diaria': aplica = True
                    elif p.get('periodicidad') == 'Puntual' and str(p.get('fecha_puntual')) == d_str: aplica = True
                    elif p.get('periodicidad') == 'Semanal' and d_obj.weekday() == 0: aplica = True
                    elif p.get('periodicidad') == 'Mensual' and d_obj.day == 1: aplica = True
                
                is_done = p['id'] in hechas_ids_dia
                
                if is_done or aplica:
                    tipo_cat = p.get('tipo', 'General/Otro')
                    if not tipo_cat: tipo_cat = 'General/Otro'
                    if tipo_cat not in tareas_dia_cats: tareas_dia_cats[tipo_cat] = []
                    
                    tramo_html = f"<span class='te-tramo'>{p.get('tramo_horario', 'Cualquiera')}</span>" if p.get('tramo_horario') and p.get('tramo_horario') != 'Cualquiera' else ""
                    
                    if is_done:
                        r_info = hechas_ids_dia[p['id']]
                        who = r_info.get('personal_empleados', {}).get('nombre', 'Alguien') if isinstance(r_info.get('personal_empleados'), dict) else 'Alguien'
                        nota_html = f"<br><span style='color:#555; font-size: 0.9em;'>📝 {r_info.get('notas')}</span>" if r_info.get('notas') else ""
                        tareas_dia_cats[tipo_cat].append(f"<div class='tarea-emp-card te-comp'><b>✅ {p['tarea']}</b><span class='te-who'>Por: {who}</span><div style='margin-top:2px;'>{tramo_html}</div>{nota_html}</div>")
                    elif aplica:
                        nom_asig = mapa_emp_inv.get(p.get('empleado_id'), p.get('rol_asignado', 'General'))
                        if d_str < hoy_str_emp:
                            tareas_dia_cats[tipo_cat].append(f"<div class='tarea-emp-card te-pend' style='border-left-color: #e53935; opacity: 0.8;'><b>❌ {p['tarea']}</b><span class='te-asig' style='color:#e53935;'>Olvidada</span></div>")
                        else:
                            tareas_dia_cats[tipo_cat].append(f"<div class='tarea-emp-card te-pend'><b>⏳ {p['tarea']}</b><div style='margin-top:2px;'>{tramo_html}</div><span class='te-asig'>Para: {nom_asig}</span></div>")
                            
            for cat in sorted(tareas_dia_cats.keys()):
                html_cal_emp += f"<div style='font-size: 0.85em; font-weight: bold; color: #005275; margin-top: 10px; margin-bottom: 4px; border-bottom: 1px solid #ccc;'>🏷️ {cat}</div>"
                for card_html in tareas_dia_cats[cat]:
                    html_cal_emp += card_html
                        
            html_cal_emp += "</td>"
        html_cal_emp += "</tr></table>"
        
        st.markdown(html_cal_emp, unsafe_allow_html=True)
        
    elif seccion_tareas == "👤 2. Mi Ficha de Trabajo":
        st.markdown("#### 👤 Mi Ficha de Trabajo Individual")
        st.info("Selecciona tu nombre para ver y marcar exclusivamente las tareas que debes cubrir hoy.")
        
        mi_nombre = st.selectbox("👋 ¿Quién eres?", [e['nombre'] for e in empleados], key="sel_quien_soy_ind")
        mi_emp_id = mapa_emp.get(mi_nombre)
        
        hoy_str = str(date.today())
        hoy_obj = date.today()
        
        try:
            plan_activos_hoy = fetch_tareas_plannings_activos(client)
            res_reg = fetch_tareas_registro_hoy(client, hoy_str)
            tareas_hechas_hoy = [r['tarea_id'] for r in res_reg]
            
            pendientes_mias = []
            for p in plan_activos_hoy:
                if p['id'] in tareas_hechas_hoy: continue
                
                created_date = str(p.get('created_at', '2000-01-01'))[:10]
                aplica = False
                if hoy_str >= created_date:
                    if p.get('periodicidad') == 'Diaria': aplica = True
                    elif p.get('periodicidad') == 'Puntual' and str(p.get('fecha_puntual')) == hoy_str: aplica = True
                    elif p.get('periodicidad') == 'Semanal' and hoy_obj.weekday() == 0: aplica = True
                    elif p.get('periodicidad') == 'Mensual' and hoy_obj.day == 1: aplica = True
                    
                if aplica:
                    is_for_me = False
                    if p.get('empleado_id') == mi_emp_id: is_for_me = True
                    elif not p.get('empleado_id'): is_for_me = True # Para roles y 'Cualquiera'
                    
                    if is_for_me:
                        nom_asig = mapa_emp_inv.get(p.get('empleado_id'), p.get('rol_asignado', 'General'))
                        pendientes_mias.append({
                            "id": p['id'], "Tarea": p['tarea'], "Tipo": p.get('tipo', 'General'), "Tramo": p.get('tramo_horario', 'Cualquiera'), "Asignado a": nom_asig, "Frecuencia": p['periodicidad']
                        })
            
            if pendientes_mias:
                df_pend = pd.DataFrame(pendientes_mias)
                df_pend.insert(0, "¡Hecho!", False)
                df_pend["Notas"] = ""
                
                st.markdown(f"**Tus tareas para hoy ({hoy_obj.strftime('%d/%m/%Y')})**")
                ed_pend = st.data_editor(
                    df_pend, hide_index=True, use_container_width=True,
                    column_config={"¡Hecho!": st.column_config.CheckboxColumn("✅ ¡Hecho!"), "id": None, "Notas": st.column_config.TextColumn("📝 Anotación (Opcional)")}, key="ed_tareas_pend_ind"
                )
                if st.button("💾 Registrar Mis Tareas Completadas", type="primary", use_container_width=True):
                    filas_hechas = ed_pend[ed_pend["¡Hecho!"] == True]
                    if not filas_hechas.empty and mi_emp_id:
                        inserts = []
                        for _, r in filas_hechas.iterrows():
                            nota_val = r.get('Notas')
                            nota_texto = str(nota_val).strip() if pd.notna(nota_val) else ""
                            inserts.append({"tarea_id": r['id'], "empleado_id": mi_emp_id, "fecha_completada": hoy_str, "notas": nota_texto})
                            
                        client.table("tareas_registro").insert(inserts).execute()
                        st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                        limpiar_cache_tareas()
                        st.success("¡Buen trabajo! Tareas registradas."); time.sleep(1); st.rerun()
            else:
                st.success(f"🎉 ¡Genial, {mi_nombre}! No tienes tareas pendientes asignadas para hoy.")
        except Exception as e:
            st.error(f"Error cargando tareas individuales: {e}")

    elif seccion_tareas == "📝 3. Notas Internas":
        st.markdown("#### 📝 Notas y Avisos Internos")
        st.info("Tablón colaborativo para dejar notas a otros compañeros o apuntes generales.")
        
        nombres_empleados = [e['nombre'] for e in empleados]
        opciones_personas = ["Administración", "Todos los empleados"] + nombres_empleados
        autor_defecto = "Administración" if is_admin else (nombres_empleados[0] if nombres_empleados else "Administración")
            
        with st.expander("➕ Escribir Nueva Nota", expanded=False):
            with st.form(f"form_nueva_nota_{st.session_state.get('db_version', 0)}"):
                c1, c2 = st.columns(2)
                with c1:
                    autor_nota = st.selectbox("Autor (Quién escribe):", opciones_personas, index=opciones_personas.index(autor_defecto) if autor_defecto in opciones_personas else 0)
                    destinatario_nota = st.selectbox("Destinatario (Para quién):", opciones_personas, index=1)
                with c2:
                    asunto_nota = st.text_input("Asunto / Título *")
                    urgencia_nota = st.selectbox("Urgencia:", ["Normal", "Importante", "Urgente"])
                
                contenido_nota = st.text_area("Contenido de la nota *")
                
                if st.form_submit_button("Enviar Nota", type="primary"):
                    if asunto_nota and contenido_nota:
                        try:
                            client.table("notas_internas").insert({
                                "autor": autor_nota,
                                "destinatario": destinatario_nota,
                                "asunto": asunto_nota,
                                "contenido": contenido_nota,
                                "urgencia": urgencia_nota,
                                "estado": "Pendiente"
                            }).execute()
                            st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                            st.success("Nota enviada correctamente.")
                            time.sleep(0.8)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al enviar la nota: {e}\n(Asegúrate de haber creado la tabla notas_internas en Supabase)")
                    else:
                        st.warning("El Asunto y el Contenido son obligatorios.")
                        
        st.markdown("---")
        c_filtro1, c_filtro2 = st.columns(2)
        with c_filtro1:
            filtro_destinatario = st.selectbox("Ver notas para:", ["Todos"] + opciones_personas)
        with c_filtro2:
            filtro_estado = st.selectbox("Estado de las notas:", ["Pendientes", "Resueltas/Archivadas", "Todas"])
            
        try:
            query = client.table("notas_internas").select("*").order("created_at", desc=True)
            if filtro_estado == "Pendientes":
                query = query.eq("estado", "Pendiente")
            elif filtro_estado == "Resueltas/Archivadas":
                query = query.eq("estado", "Resuelta")
                
            res_notas = query.execute()
            notas_data = res_notas.data
            
            if filtro_destinatario != "Todos":
                notas_data = [n for n in notas_data if n['destinatario'] == filtro_destinatario or n['destinatario'] == "Todos los empleados" or n['autor'] == filtro_destinatario]
                
            if not notas_data:
                st.info("No hay notas que coincidan con estos filtros.")
            else:
                for n in notas_data:
                    color_urg = "#4caf50" if n['urgencia'] == 'Normal' else ("#ff9800" if n['urgencia'] == 'Importante' else "#f44336")
                    bg_color = "#fff" if n['estado'] == 'Pendiente' else "#f5f5f5"
                    
                    st.markdown(f'''
                    <div style="border: 1px solid #ddd; border-left: 5px solid {color_urg}; border-radius: 5px; padding: 15px; margin-bottom: 10px; background-color: {bg_color};">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <h5 style="margin: 0; color: #333; font-size: 1.1rem;">{n['asunto']}</h5>
                            <span style="font-size: 0.8rem; background-color: {color_urg}; color: white; padding: 3px 8px; border-radius: 12px; font-weight: bold;">{n['urgencia']}</span>
                        </div>
                        <div style="font-size: 0.9rem; color: #666; margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px dashed #eee;">
                            <b>De:</b> {n['autor']} &nbsp;|&nbsp; <b>Para:</b> {n['destinatario']} &nbsp;|&nbsp; <b>Fecha:</b> {str(n['created_at'])[:16].replace('T', ' ')}
                        </div>
                        <div style="font-size: 1rem; color: #444; white-space: pre-wrap; margin-bottom: 10px; line-height: 1.4;">{n['contenido']}</div>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    if n['estado'] == 'Pendiente':
                        if st.button(f"✅ Marcar como Resuelta / Leída", key=f"res_nota_{n['id']}_{st.session_state.get('db_version', 0)}"):
                            client.table("notas_internas").update({"estado": "Resuelta"}).eq("id", n['id']).execute()
                            st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                            st.rerun()
                            
        except Exception as e:
            st.warning(f"Aún no hay notas registradas o falta crear la tabla `notas_internas`. (Aviso interno: {e})")



    if is_admin and seccion_tareas == "⚙️ 5. Gestión y Dueños":
            st.markdown("#### ⚙️ Configuración y Administración General")
            seccion_admin_tareas = st.radio("Sección Administración Tareas:", ["👔 1. Calendario y Tareas de Dueños", "⚙️ 2. Configurar Plannings", "✅ 3. Historial de Cumplimiento"], horizontal=True, label_visibility="collapsed")
            
            if seccion_admin_tareas == "👔 1. Calendario y Tareas de Dueños":
                st.markdown("##### 📅 Calendario de Proyección Virtual")
                c_cal1, c_cal2 = st.columns([1, 3])
                with c_cal1:
                    vista_cal = st.radio("Tipo de Vista", ["Semanal", "Mensual"], horizontal=True)
                    dia_ref_due = st.date_input("Fecha de referencia:", value=date.today(), key="sem_ref_due")
                
                try:
                    todas_tareas_db = fetch_tareas_duenos_all(client)
                except:
                    todas_tareas_db = []
                
                if vista_cal == "Semanal":
                    start_view = dia_ref_due - timedelta(days=dia_ref_due.weekday())
                    end_view = start_view + timedelta(days=6)
                    tareas_proy = generar_proyeccion_virtual(todas_tareas_db, start_view, end_view)
                    
                    dias_semana_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                    html_cal = '''
                    <style>
                        .cal-due-table { width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 13px; background-color: white; margin-bottom: 20px;}
                        .cal-due-table th { background-color: #005275; color: white; padding: 6px; text-align: center; border: 1px solid #ddd; }
                        .cal-due-table td { border: 1px solid #ddd; vertical-align: top; padding: 5px; height: 100px; background-color: #fafafa; }
                        .day-head-due { font-weight: bold; font-size: 1.1em; color: #333; margin-bottom: 5px; border-bottom: 1px solid #eee; padding-bottom: 2px;}
                        .td-today-due { background-color: #fffde7 !important; border: 2px solid #fbc02d !important; }
                        .tarea-card { background-color: white; border-left: 4px solid #f57c00; padding: 5px; margin-bottom: 5px; border-radius: 3px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); font-size: 0.85em; line-height: 1.2; word-wrap: break-word;}
                        .t-pend { border-left-color: #f57c00; }
                        .t-cur { border-left-color: #2196f3; }
                        .t-comp { border-left-color: #4caf50; opacity: 0.7; text-decoration: line-through; }
                        .t-fail { border-left-color: #d32f2f; opacity: 0.7; text-decoration: line-through; color: #d32f2f; }
                    </style>
                    <table class="cal-due-table"><tr>
                    '''
                    for d_name in dias_semana_nombres: html_cal += f"<th>{d_name}</th>"
                    html_cal += "</tr><tr>"
                    
                    hoy_str_g = str(date.today())
                    for i in range(7):
                        d_obj = start_view + timedelta(days=i)
                        d_str = str(d_obj)
                        td_class = "td-today-due" if d_str == hoy_str_g else ""
                        
                        html_cal += f"<td class='{td_class}'>"
                        html_cal += f"<div class='day-head-due'>{d_obj.strftime('%d/%m')}</div>"
                        
                        t_dia = [t for t in tareas_proy if t.get('fecha_programada') == d_str]
                        for t in t_dia:
                            est = str(t.get('estado', ''))
                            t_class = "t-pend"; icon = "⏳"
                            if "curso" in est.lower(): t_class = "t-cur"; icon = "🏗️"
                            elif "completada" in est.lower(): t_class = "t-comp"; icon = "✅"
                            elif "no realizada" in est.lower() or "fallida" in est.lower() or "❌" in est: t_class = "t-fail"; icon = "❌"
                            
                            virt_mark = "✦" if t.get('es_virtual') else ""
                            html_cal += f"<div class='tarea-card {t_class}' title='{est}'><b>{icon} {t['titulo']} {virt_mark}</b></div>"
                            
                        html_cal += "</td>"
                    html_cal += "</tr></table>"
                    st.markdown(html_cal, unsafe_allow_html=True)
                    
                else: # Mensual
                    year = dia_ref_due.year
                    month = dia_ref_due.month
                    _, num_days = calendar.monthrange(year, month)
                    start_view = date(year, month, 1)
                    end_view = date(year, month, num_days)
                    tareas_proy = generar_proyeccion_virtual(todas_tareas_db, start_view, end_view)
                    
                    html_cal = '''
                    <style>
                        .cal-due-table { width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 13px; background-color: white; margin-bottom: 20px;}
                        .cal-due-table th { background-color: #005275; color: white; padding: 6px; text-align: center; border: 1px solid #ddd; }
                        .cal-due-table td { border: 1px solid #ddd; vertical-align: top; padding: 5px; height: 100px; background-color: #fafafa; }
                        .day-head-due { font-weight: bold; font-size: 1.1em; color: #333; margin-bottom: 5px; border-bottom: 1px solid #eee; padding-bottom: 2px;}
                        .td-today-due { background-color: #fffde7 !important; border: 2px solid #fbc02d !important; }
                        .tarea-card { background-color: white; border-left: 4px solid #f57c00; padding: 5px; margin-bottom: 5px; border-radius: 3px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); font-size: 0.85em; line-height: 1.2; word-wrap: break-word;}
                        .t-pend { border-left-color: #f57c00; }
                        .t-cur { border-left-color: #2196f3; }
                        .t-comp { border-left-color: #4caf50; opacity: 0.7; text-decoration: line-through; }
                        .t-fail { border-left-color: #d32f2f; opacity: 0.7; text-decoration: line-through; color: #d32f2f; }
                    </style>
                    <table class="cal-due-table">
                    <tr><th>Lunes</th><th>Martes</th><th>Miércoles</th><th>Jueves</th><th>Viernes</th><th>Sábado</th><th>Domingo</th></tr>
                    <tr>
                    '''
                    first_weekday = start_view.weekday()
                    for _ in range(first_weekday): html_cal += "<td></td>"
                    
                    hoy_str_g = str(date.today())
                    current_col = first_weekday
                    
                    for day in range(1, num_days + 1):
                        d_obj = date(year, month, day)
                        d_str = str(d_obj)
                        td_class = "td-today-due" if d_str == hoy_str_g else ""
                        html_cal += f"<td class='{td_class}' style='height: 80px;'><div class='day-head-due'>{day}</div>"
                        
                        t_dia = [t for t in tareas_proy if t.get('fecha_programada') == d_str]
                        for t in t_dia:
                            est = str(t.get('estado', ''))
                            t_class = "t-pend"; icon = "⏳"
                            if "curso" in est.lower(): t_class = "t-cur"; icon = "🏗️"
                            elif "completada" in est.lower(): t_class = "t-comp"; icon = "✅"
                            elif "no realizada" in est.lower() or "❌" in est: t_class = "t-fail"; icon = "❌"
                            
                            html_cal += f"<div class='tarea-card {t_class}' style='font-size: 0.7em; padding: 2px;' title='{t['titulo']} - {est}'><b>{icon} {t['titulo'][:12]}..</b></div>"
                            
                        html_cal += "</td>"
                        current_col += 1
                        if current_col == 7:
                            html_cal += "</tr><tr>"
                            current_col = 0
                            
                    while current_col < 7 and current_col > 0:
                        html_cal += "<td></td>"
                        current_col += 1
                    html_cal += "</tr></table>"
                    st.markdown(html_cal, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # PANEL DE CONTROL DIARIO
                c_due1, c_due2 = st.columns([1, 2])
                with c_due1:
                    st.markdown("##### 📝 Panel de Control Diario")
                    st.info("Selecciona la fecha que quieras gestionar en la tabla de la derecha.")
                    dia_gestionar = st.date_input("Día a gestionar:", value=date.today(), key="dia_gest_due")
                    
                    with st.form("form_nueva_gestion", clear_on_submit=True):
                        st.markdown("➕ **Nueva Tarea / Master**")
                        g_titulo = st.text_input("Asunto / Tarea *", key="g_tit")
                        g_frecuencia = st.selectbox("Periodicidad", ["Puntual", "Diario", "Semanal", "Mensual", "Anual", "Por horas"], key="g_fre")
                        g_hora = st.time_input("Hora (Opcional)", value=None, key="g_hor_due")
                        g_notas = st.text_area("Notas", key="g_not")
                        
                        if st.form_submit_button("Añadir al Plan", type="primary", use_container_width=True):
                            if g_titulo:
                                tit_final = f"🕒 {g_hora.strftime('%H:%M')} - {g_titulo}" if g_hora else g_titulo
                                client.table("tareas_duenos").insert({"titulo": tit_final, "fecha_programada": str(dia_gestionar), "periodicidad": g_frecuencia, "notas": g_notas, "estado": "Pendiente ⏳"}).execute()
                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                limpiar_cache_tareas()
                                st.success("Añadido."); time.sleep(0.5); st.rerun()
                            else: st.warning("El asunto es obligatorio.")
                            
                with c_due2:
                    st.markdown(f"**Gestiones Proyectadas para el {dia_gestionar.strftime('%d/%m/%Y')}**")
                    try:
                        todas_tareas_hoy = fetch_tareas_duenos_all(client)
                        tareas_hoy_proy = generar_proyeccion_virtual(todas_tareas_hoy, str(dia_gestionar), str(dia_gestionar))
                        
                        if tareas_hoy_proy:
                            df_hoy = pd.DataFrame(tareas_hoy_proy)
                            df_v_hoy = df_hoy[['id', 'titulo', 'periodicidad', 'estado', 'notas', 'es_virtual']].copy()
                            df_v_hoy.insert(0, "Borrar", False)
                            
                            ed_hoy = st.data_editor(
                                df_v_hoy, hide_index=True, use_container_width=True, height=350,
                                column_config={
                                    "Borrar": st.column_config.CheckboxColumn("🗑️", width="small"), 
                                    "id": None, "es_virtual": None,
                                    "titulo": "Asunto", 
                                    "periodicidad": st.column_config.SelectboxColumn("Frecuencia", options=["Puntual", "Diario", "Semanal", "Mensual", "Anual", "Por horas"]), 
                                    "estado": st.column_config.SelectboxColumn("Estado", options=["Pendiente ⏳", "En curso 🏗️", "Completada ✅", "No realizada ❌"])
                                }, key=f"ed_duenos_hoy_{st.session_state.get('db_version', 0)}"
                            )
                            if st.button("💾 Guardar Estado del Día", type="primary"):
                                cambios = 0
                                for _, rb in ed_hoy[ed_hoy["Borrar"] == True].iterrows():
                                    if not rb['es_virtual']: 
                                        client.table("tareas_duenos").delete().eq("id", rb['id']).execute()
                                        cambios += 1
                                
                                for _, rv in ed_hoy[ed_hoy["Borrar"] == False].iterrows():
                                    t_id = str(rv['id'])
                                    nuevo_estado = str(rv['estado'])
                                    es_virt = rv['es_virtual']
                                    
                                    if not es_virt:
                                        fila_orig = df_hoy[df_hoy['id'].astype(str) == t_id].iloc[0]
                                        if nuevo_estado != str(fila_orig['estado']) or str(rv['notas']) != str(fila_orig.get('notas','')):
                                            client.table("tareas_duenos").update({
                                                "titulo": str(rv['titulo']), "periodicidad": str(rv['periodicidad']),
                                                "estado": nuevo_estado, "notas": str(rv['notas'])
                                            }).eq("id", int(float(t_id)) if t_id.replace('.','',1).isdigit() else t_id).execute()
                                            cambios += 1
                                    else:
                                        # Es una fila virtual, solo la insertamos si cambiaron el estado o añadieron notas
                                        if nuevo_estado != "Pendiente ⏳" or str(rv['notas']).strip():
                                            client.table("tareas_duenos").insert({
                                                "titulo": str(rv['titulo']), 
                                                "fecha_programada": str(dia_gestionar), 
                                                "periodicidad": str(rv['periodicidad']), 
                                                "notas": str(rv['notas']), 
                                                "estado": nuevo_estado
                                            }).execute()
                                            cambios += 1
                                            
                                if cambios > 0:
                                    st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                    limpiar_cache_tareas()
                                    st.success(f"Día actualizado ({cambios} cambios)."); time.sleep(0.5); st.rerun()
                                else:
                                    st.info("Sin cambios.")
                        else:
                            st.info("🎉 ¡Día libre! No hay tareas ni gestiones proyectadas para este día.")
                    except Exception as e:
                        st.error(f"Error cargando el control diario: {e}")
                    
            elif seccion_admin_tareas == "⚙️ 2. Configurar Plannings":
                try:
                    res_act_load = fetch_tareas_plannings_activos(client)
                    if res_act_load:
                        df_load = pd.DataFrame(res_act_load)
                        df_load['Asig'] = df_load.apply(lambda x: f"👤 {mapa_emp_inv[x['empleado_id']]}" if pd.notna(x['empleado_id']) and x['empleado_id'] in mapa_emp_inv else x['rol_asignado'], axis=1)
                        conteo = df_load['Asig'].value_counts()
                        
                        st.markdown("##### 📊 Balance de Carga de Trabajo (Planes Activos)")
                        st.markdown("<span style='font-size:13px; color:gray;'>Recuento del número de tareas recurrentes asignadas a cada empleado o rol.</span>", unsafe_allow_html=True)
                        html_tags = "".join([f"<span style='display:inline-block; background-color:#e3f2fd; color:#1565c0; padding:6px 12px; border-radius:15px; margin-right:8px; margin-bottom:8px; font-weight:bold; font-size:14px;'>{k}: <span style='color:#d32f2f;'>{v}</span> tareas</span>" for k, v in conteo.items()])
                        st.markdown(html_tags, unsafe_allow_html=True)
                        st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)
                except:
                    pass
                
                c_p1, c_p2 = st.columns([1, 2])
                with c_p1:
                    with st.form("form_nuevo_plan", clear_on_submit=True):
                        st.markdown("##### ➕ Asignar Nuevo Planning/Tarea")
                        p_tar = st.text_input("Descripción de la tarea *", key=f"p_tar_{st.session_state.llave_tarea_plan}")
                        c_form1, c_form2 = st.columns(2)
                        with c_form1:
                            categorias_tareas = ["Operativa de Tienda", "Inventario y Almacén", "Peluquería y Clínica", "Mantenimiento y Limpieza", "Logística y Repartos", "Marketing y Redes", "Compras: Proveedores (Catálogo)", "Compras: Consumibles y Material", "Administración y Finanzas", "Gestión de Equipo", "General/Otro"]
                            p_tipo = st.selectbox("Tipo de Tarea", categorias_tareas, key=f"p_tip_{st.session_state.llave_tarea_plan}")
                            p_asig = st.selectbox("Asignar a", opciones_asignacion, key=f"p_asi_{st.session_state.llave_tarea_plan}")
                        with c_form2:
                            p_tramo = st.selectbox("Tramo Horario", ["Cualquiera", "Mañana (Apertura)", "Mediodía", "Tarde", "Cierre"], key=f"p_tra_{st.session_state.llave_tarea_plan}")
                            p_per = st.selectbox("Frecuencia", ["Diaria", "Semanal", "Mensual", "Puntual"], key=f"p_per_{st.session_state.llave_tarea_plan}")
                        
                        p_hora_txt = st.time_input("O fijar hora exacta", value=None, key=f"p_hor_txt_{st.session_state.llave_tarea_plan}")
                        p_fec = None
                        if p_per == "Puntual": p_fec = st.date_input("Fecha límite", value=date.today())
                            
                        if st.form_submit_button("Guardar Planning", type="primary", use_container_width=True):
                            if p_tar:
                                tramo_final = p_hora_txt.strftime('%H:%M') if p_hora_txt else p_tramo
                                emp_id, rol = None, "Cualquiera / Todos"
                                if p_asig.startswith("👤 "):
                                    emp_id = mapa_emp.get(p_asig.replace("👤 ", ""))
                                    rol = None
                                else: rol = p_asig
                                    
                                client.table("tareas_plannings").insert({
                                    "tarea": p_tar, "empleado_id": emp_id, "rol_asignado": rol,
                                    "periodicidad": p_per, "fecha_puntual": str(p_fec) if p_fec else None, "activo": True,
                                    "tipo": p_tipo, "tramo_horario": tramo_final
                                }).execute()
                                st.session_state.llave_tarea_plan += 1
                                limpiar_cache_tareas()
                                st.success("Añadido."); time.sleep(0.5); st.rerun()
                            else: st.warning("Escribe la tarea.")
                with c_p2:
                    try:
                        res_act = fetch_tareas_plannings_activos(client)
                        if res_act:
                            df_act = pd.DataFrame(res_act)
                            df_act['Asignado'] = df_act.apply(lambda x: f"👤 {mapa_emp_inv[x['empleado_id']]}" if pd.notna(x['empleado_id']) and x['empleado_id'] in mapa_emp_inv else x['rol_asignado'], axis=1)
                            
                            tramos_base = ["Cualquiera", "Mañana (Apertura)", "Mediodía", "Tarde", "Cierre"]
                            df_act['Tramo'] = df_act['tramo_horario'].apply(lambda x: x if x in tramos_base else "Hora Exacta")
                            
                            def parse_time(x):
                                try: return pd.to_datetime(x).time()
                                except: return None
                                
                            df_act['Hora'] = df_act['tramo_horario'].apply(lambda x: parse_time(x) if x not in tramos_base and x else None)
                            
                            df_v_act = df_act[['id', 'tarea', 'tipo', 'Tramo', 'Hora', 'Asignado', 'periodicidad']].copy()
                            df_v_act.insert(0, "Borrar", False)
                            
                            st.markdown("##### ⚙️ Plannings Activos")
                            categorias_t = ["Operativa de Tienda", "Inventario y Almacén", "Peluquería y Clínica", "Mantenimiento y Limpieza", "Logística y Repartos", "Marketing y Redes", "Compras: Proveedores (Catálogo)", "Compras: Consumibles y Material", "Administración y Finanzas", "Gestión de Equipo", "General/Otro"]
                            
                            ed_act = st.data_editor(
                                df_v_act, hide_index=True, use_container_width=True, 
                                column_config={
                                    "Borrar": st.column_config.CheckboxColumn("🗑️", width="small"), 
                                    "id": None, 
                                    "tarea": "Tarea", 
                                    "tipo": st.column_config.SelectboxColumn("Tipo", options=categorias_t), 
                                    "Tramo": st.column_config.SelectboxColumn("Tramo", options=["Cualquiera", "Mañana (Apertura)", "Mediodía", "Tarde", "Cierre", "Hora Exacta"]),
                                    "Hora": st.column_config.TimeColumn("Hora", format="HH:mm", help="Rellenar si el tramo es 'Hora Exacta'"),
                                    "Asignado": st.column_config.SelectboxColumn("Asignado a", options=opciones_asignacion),
                                    "periodicidad": st.column_config.SelectboxColumn("Frec.", options=["Diaria", "Semanal", "Mensual", "Puntual"])
                                }
                            )
                            if st.button("💾 Guardar Cambios"):
                                for _, rb in ed_act[ed_act["Borrar"] == True].iterrows():
                                    client.table("tareas_plannings").update({"activo": False}).eq("id", rb['id']).execute()
                                
                                for _, rv in ed_act[ed_act["Borrar"] == False].iterrows():
                                    tram_val = rv['Hora'].strftime('%H:%M') if pd.notna(rv['Hora']) and rv['Tramo'] == "Hora Exacta" else rv['Tramo']
                                    if tram_val == "Hora Exacta" and pd.isna(rv['Hora']): tram_val = "Cualquiera"
                                    
                                    asi = str(rv['Asignado'])
                                    if asi.startswith("👤 "):
                                        e_id = mapa_emp.get(asi.replace("👤 ", ""))
                                        r_asi = None
                                    else:
                                        e_id = None
                                        r_asi = asi

                                    client.table("tareas_plannings").update({
                                        "tarea": rv['tarea'],
                                        "tipo": rv['tipo'],
                                        "tramo_horario": tram_val,
                                        "periodicidad": rv['periodicidad'],
                                        "empleado_id": e_id,
                                        "rol_asignado": r_asi
                                    }).eq("id", rv['id']).execute()
                                    
                                limpiar_cache_tareas()
                                st.success("Actualizado"); time.sleep(0.5); st.rerun()
                    except: pass
            elif seccion_admin_tareas == "✅ 3. Historial de Cumplimiento":
                try:
                    res_hist = fetch_tareas_historial(client)
                    if res_hist:
                        hist_data = []
                        for h in res_hist:
                            emp = h.get('personal_empleados', {}).get('nombre', 'Desconocido') if h.get('personal_empleados') else 'Desconocido'
                            tar = h.get('tareas_plannings', {}).get('tarea', 'Tarea borrada') if h.get('tareas_plannings') else 'Tarea borrada'
                            per = h.get('tareas_plannings', {}).get('periodicidad', '-') if h.get('tareas_plannings') else '-'
                            fecha = pd.to_datetime(h['fecha_completada']).strftime('%d/%m/%Y')
                            nota = h.get('notas', '')
                            hist_data.append({"Fecha": fecha, "Empleado": emp, "Tarea": tar, "Tipo": per, "Anotación": nota})
                        st.dataframe(pd.DataFrame(hist_data), use_container_width=True, hide_index=True)
                    else:
                        st.info("Aún no hay registros de tareas completadas.")
                except: pass