import streamlit as st
import pandas as pd
import time
from datetime import date

def render_pestana_tareas(client):
    if 'llave_tarea_plan' not in st.session_state: st.session_state.llave_tarea_plan = 0
    if 'llave_tarea_due' not in st.session_state: st.session_state.llave_tarea_due = 0

    st.markdown("<h3 style='margin-top: -15px;'>✅ Planificación y Tareas</h3>", unsafe_allow_html=True)
    
    is_admin = st.session_state.get('rol') == 'Admin'
    
    # Extraer empleados activos de la base de datos
    try:
        res_emp = client.table("personal_empleados").select("id, nombre").eq("activo", True).execute()
        empleados = res_emp.data if res_emp.data else []
        mapa_emp = {e['nombre']: e['id'] for e in empleados}
        mapa_emp_inv = {e['id']: e['nombre'] for e in empleados}
    except:
        empleados, mapa_emp, mapa_emp_inv = [], {}, {}
        
    opciones_rol = ["Cualquiera / Todos", "Rol: Tienda / Dependiente", "Rol: Peluquería"]
    opciones_asignacion = opciones_rol + [f"👤 {e['nombre']}" for e in empleados]

    if is_admin:
        tabs = st.tabs(["👥 1. Gestión de Empleados", "👔 2. Gestión de Dueños"])
        tab_empleados, tab_duenos = tabs
    else:
        tabs = st.tabs(["👥 1. Mis Plannings y Tareas"])
        tab_empleados = tabs[0]
        tab_duenos = None
        
    with tab_empleados:
        st.markdown("#### 👥 Plannings y Funciones del Personal")
        
        if is_admin:
            sub_tabs_emp = st.tabs(["📋 Rutinas para Hoy", "✅ Historial de Cumplimiento", "⚙️ Configurar Plannings/Roles"])
        else:
            sub_tabs_emp = st.tabs(["📋 Mis Tareas para Hoy", "✅ Mi Historial"])
        
        with sub_tabs_emp[0]:
            st.write(f"**Tareas a realizar hoy ({date.today().strftime('%d/%m/%Y')})**")
            try:
                # Leer plannings activos
                res_plan = client.table("tareas_plannings").select("*").eq("activo", True).execute()
                # Leer lo que ya se ha completado hoy
                hoy_str = str(date.today())
                res_reg = client.table("tareas_registro").select("tarea_id").eq("fecha_completada", hoy_str).execute()
                tareas_hechas_hoy = [r['tarea_id'] for r in res_reg.data] if res_reg.data else []
                
                if res_plan.data:
                    pendientes = []
                    for p in res_plan.data:
                        # Omitimos las que ya se han hecho hoy
                        if p['id'] not in tareas_hechas_hoy:
                            nom_asig = mapa_emp_inv.get(p['empleado_id'], p.get('rol_asignado', 'General'))
                            pendientes.append({
                                "id": p['id'], "Tarea": p['tarea'], "Asignado a": nom_asig, "Frecuencia": p['periodicidad']
                            })
                    
                    if pendientes:
                        df_pend = pd.DataFrame(pendientes)
                        df_pend.insert(0, "¡Hecho!", False)
                        
                        st.info("Marca la casilla '¡Hecho!' y pulsa Guardar para registrar que has completado la tarea.")
                        ed_pend = st.data_editor(
                            df_pend, hide_index=True, use_container_width=True,
                            column_config={"¡Hecho!": st.column_config.CheckboxColumn("✅ ¡Hecho!"), "id": None}, key="ed_tareas_pend"
                        )
                        
                        c_he1, c_he2 = st.columns([1, 2])
                        with c_he1: emp_completado = st.selectbox("¿Quién completó la(s) tarea(s)?", [e['nombre'] for e in empleados])
                        with c_he2:
                            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                            if st.button("💾 Registrar Tareas Completadas", type="primary"):
                                id_emp_comp = mapa_emp.get(emp_completado)
                                filas_hechas = ed_pend[ed_pend["¡Hecho!"] == True]
                                if not filas_hechas.empty and id_emp_comp:
                                    inserts = [{"tarea_id": r['id'], "empleado_id": id_emp_comp, "fecha_completada": hoy_str} for _, r in filas_hechas.iterrows()]
                                    client.table("tareas_registro").insert(inserts).execute()
                                    st.success("¡Buen trabajo! Tareas registradas."); time.sleep(1); st.rerun()
                    else:
                        st.success("🎉 ¡Todas las tareas de hoy están completadas!")
                else:
                    st.info("No hay plannings configurados.")
            except:
                st.error("🔧 Fallo de lectura. Asegúrate de haber ejecutado el nuevo código SQL.")
            
        with sub_tabs_emp[1]:
            st.write("**Historial (Quién hizo qué)**")
            try:
                res_hist = client.table("tareas_registro").select("fecha_completada, personal_empleados(nombre), tareas_plannings(tarea, periodicidad)").order("fecha_completada", desc=True).limit(100).execute()
                if res_hist.data:
                    hist_data = []
                    for h in res_hist.data:
                        emp = h.get('personal_empleados', {}).get('nombre', 'Desconocido') if h.get('personal_empleados') else 'Desconocido'
                        tar = h.get('tareas_plannings', {}).get('tarea', 'Tarea borrada') if h.get('tareas_plannings') else 'Tarea borrada'
                        per = h.get('tareas_plannings', {}).get('periodicidad', '-') if h.get('tareas_plannings') else '-'
                        fecha = pd.to_datetime(h['fecha_completada']).strftime('%d/%m/%Y')
                        hist_data.append({"Fecha": fecha, "Empleado": emp, "Tarea": tar, "Tipo": per})
                    st.dataframe(pd.DataFrame(hist_data), use_container_width=True, hide_index=True)
                else:
                    st.info("Aún no hay registros de tareas completadas.")
            except: pass
            
        if is_admin:
            with sub_tabs_emp[2]:
                c_p1, c_p2 = st.columns([1, 2])
                with c_p1:
                    with st.form("form_nuevo_plan", clear_on_submit=True):
                        st.markdown("##### ➕ Asignar Nuevo Planning/Tarea")
                        p_tar = st.text_input("Descripción de la tarea *", key=f"p_tar_{st.session_state.llave_tarea_plan}")
                        p_asig = st.selectbox("Asignar a", opciones_asignacion, key=f"p_asi_{st.session_state.llave_tarea_plan}")
                        p_per = st.selectbox("Frecuencia", ["Diaria", "Semanal", "Mensual", "Puntual"], key=f"p_per_{st.session_state.llave_tarea_plan}")
                        p_fec = None
                        if p_per == "Puntual": p_fec = st.date_input("Fecha límite", value=date.today())
                            
                        if st.form_submit_button("Guardar Planning", type="primary", use_container_width=True):
                            if p_tar:
                                emp_id, rol = None, "Cualquiera / Todos"
                                if p_asig.startswith("👤 "):
                                    emp_id = mapa_emp.get(p_asig.replace("👤 ", ""))
                                    rol = None
                                else: rol = p_asig
                                    
                                client.table("tareas_plannings").insert({
                                    "tarea": p_tar, "empleado_id": emp_id, "rol_asignado": rol,
                                    "periodicidad": p_per, "fecha_puntual": str(p_fec) if p_fec else None, "activo": True
                                }).execute()
                                st.session_state.llave_tarea_plan += 1
                                st.success("Añadido."); time.sleep(0.5); st.rerun()
                            else: st.warning("Escribe la tarea.")
                with c_p2:
                    try:
                        res_act = client.table("tareas_plannings").select("*").eq("activo", True).order("id", desc=True).execute()
                        if res_act.data:
                            df_act = pd.DataFrame(res_act.data)
                            df_act['Asignado'] = df_act.apply(lambda x: mapa_emp_inv.get(x['empleado_id'], x['rol_asignado']), axis=1)
                            df_v_act = df_act[['id', 'tarea', 'Asignado', 'periodicidad']].copy()
                            df_v_act.insert(0, "Borrar", False)
                            
                            st.markdown("##### ⚙️ Plannings Activos")
                            ed_act = st.data_editor(df_v_act, hide_index=True, use_container_width=True, column_config={"Borrar": st.column_config.CheckboxColumn("🗑️", width="small"), "id": None, "tarea": "Tarea", "periodicidad": "Frec."})
                            if st.button("💾 Guardar Cambios"):
                                for _, rb in ed_act[ed_act["Borrar"] == True].iterrows():
                                    client.table("tareas_plannings").update({"activo": False}).eq("id", rb['id']).execute()
                                st.success("Actualizado"); time.sleep(0.5); st.rerun()
                    except: pass
                
    if tab_duenos:
        with tab_duenos:
            st.markdown("#### 👔 Gestiones, Reuniones y Calendario de Gerencia")
            
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
                            st.success("Agendado."); time.sleep(0.5); st.rerun()
                        else: st.warning("El asunto es obligatorio.")
                    
            with c_due2:
                try:
                    res_due = client.table("tareas_duenos").select("*").order("fecha_programada", desc=False).execute()
                    if res_due.data:
                        df_due = pd.DataFrame(res_due.data)
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
                            st.success("Guardado"); time.sleep(0.5); st.rerun()
                    else: st.info("No hay gestiones pendientes.")
                except: pass