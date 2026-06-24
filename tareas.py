import streamlit as st
import pandas as pd
import time
from datetime import date, timedelta

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
        tabs = st.tabs([" 1. Calendario General", "👤 2. Mi Ficha de Trabajo", "⚙️ 3. Gestión y Dueños"])
        tab_general, tab_individual, tab_admin = tabs
    else:
        tabs = st.tabs([" 1. Calendario General", "👤 2. Mi Ficha de Trabajo"])
        tab_general, tab_individual = tabs[0], tabs[1]
        tab_admin = None
        
    with tab_general:
        st.markdown("#### 📅 Calendario General de Plannings")
        st.info("Visión global de todas las rutinas de la tienda para esta semana.")
        c_cale1, c_cale2 = st.columns([1, 3])
        with c_cale1:
            dia_ref_emp = st.date_input("Ver semana del:", value=date.today(), key="sem_ref_emp")
        
        start_week_emp = dia_ref_emp - timedelta(days=dia_ref_emp.weekday())
        end_week_emp = start_week_emp + timedelta(days=6)
        
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
        
    with tab_individual:
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

    if tab_admin:
        with tab_admin:
            st.markdown("#### ⚙️ Configuración y Administración General")
            sub_admin = st.tabs(["👔 1. Calendario y Tareas de Dueños", "⚙️ 2. Configurar Plannings", "✅ 3. Historial de Cumplimiento"])
            
            with sub_admin[0]:
                c_cal1, c_cal2 = st.columns([1, 3])
                with c_cal1:
                    dia_ref_due = st.date_input("Ver semana del:", value=date.today(), key="sem_ref_due")
                
                start_week_due = dia_ref_due - timedelta(days=dia_ref_due.weekday())
                end_week_due = start_week_due + timedelta(days=6)
                
                try:
                    tareas_sem = fetch_tareas_duenos_rango(client, str(start_week_due), str(end_week_due))
                except:
                    tareas_sem = []
                    
                dias_semana_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                html_cal_due = '''
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
                </style>
                <table class="cal-due-table"><tr>
                '''
                for d_name in dias_semana_nombres: html_cal_due += f"<th>{d_name}</th>"
                html_cal_due += "</tr><tr>"
                
                hoy_str_g = str(date.today())
                for i in range(7):
                    d_obj = start_week_due + timedelta(days=i)
                    d_str = str(d_obj)
                    td_class = "td-today-due" if d_str == hoy_str_g else ""
                    
                    html_cal_due += f"<td class='{td_class}'>"
                    html_cal_due += f"<div class='day-head-due'>{d_obj.strftime('%d/%m')}</div>"
                    
                    t_dia = [t for t in tareas_sem if t.get('fecha_programada') == d_str]
                    for t in t_dia:
                        est = t.get('estado', '')
                        t_class = "t-pend"; icon = "⏳"
                        if "curso" in est.lower(): t_class = "t-cur"; icon = "🏗️"
                        elif "completada" in est.lower(): t_class = "t-comp"; icon = "✅"
                        html_cal_due += f"<div class='tarea-card {t_class}'><b>{icon} {t['titulo']}</b><br><span style='color:#666;'>{t.get('periodicidad','')}</span></div>"
                        
                    html_cal_due += "</td>"
                html_cal_due += "</tr></table>"
                
                st.markdown(html_cal_due, unsafe_allow_html=True)
                st.markdown("---")
                
                c_due1, c_due2 = st.columns([1, 2])
                with c_due1:
                    with st.form("form_nueva_gestion", clear_on_submit=True):
                        st.markdown("##### ➕ Nueva Gestión / Reunión")
                        g_titulo = st.text_input("Asunto / Tarea *", key=f"g_tit_{st.session_state.llave_tarea_due}")
                        g_fecha = st.date_input("Fecha", value=date.today(), key=f"g_fec_{st.session_state.llave_tarea_due}")
                        g_frecuencia = st.selectbox("Periodicidad", ["Puntual", "Semanal", "Mensual", "Anual"], key=f"g_fre_{st.session_state.llave_tarea_due}")
                        g_notas = st.text_area("Notas", key=f"g_not_{st.session_state.llave_tarea_due}")
                        
                        if st.form_submit_button("Programar", type="primary", use_container_width=True):
                            if g_titulo:
                                client.table("tareas_duenos").insert({"titulo": g_titulo, "fecha_programada": str(g_fecha), "periodicidad": g_frecuencia, "notas": g_notas, "estado": "Pendiente ⏳"}).execute()
                                st.session_state.llave_tarea_due += 1
                                limpiar_cache_tareas()
                                st.success("Agendado."); time.sleep(0.5); st.rerun()
                            else: st.warning("El asunto es obligatorio.")
                        
                with c_due2:
                    try:
                        res_due = fetch_tareas_duenos_all(client)
                        if res_due:
                            df_due = pd.DataFrame(res_due)
                            df_due['Fecha'] = pd.to_datetime(df_due['fecha_programada']).dt.strftime('%d/%m/%Y')
                            df_v_due = df_due[['id', 'Fecha', 'titulo', 'periodicidad', 'estado', 'notas']].copy()
                            df_v_due.insert(0, "Borrar", False)
                            
                            ed_due = st.data_editor(
                                df_v_due, hide_index=True, use_container_width=True, height=350,
                                column_config={"Borrar": st.column_config.CheckboxColumn("🗑️", width="small"), "id": None, "titulo": "Asunto", "periodicidad": "Frecuencia", "estado": st.column_config.SelectboxColumn("Estado", options=["Pendiente ⏳", "En curso 🏗️", "Completada ✅"])}, key="ed_duenos"
                            )
                            if st.button("💾 Guardar Cambios", type="primary"):
                                for _, rb in ed_due[ed_due["Borrar"] == True].iterrows(): client.table("tareas_duenos").delete().eq("id", rb['id']).execute()
                                for _, rv in ed_due[ed_due["Borrar"] == False].iterrows(): client.table("tareas_duenos").update({"titulo": str(rv['titulo']), "estado": str(rv['estado']), "notas": str(rv['notas'])}).eq("id", rv['id']).execute()
                                limpiar_cache_tareas()
                                st.success("Guardado"); time.sleep(0.5); st.rerun()
                        else: st.info("No hay gestiones pendientes.")
                    except: pass
                    
            with sub_admin[1]:
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
            with sub_admin[2]:
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