import streamlit as st
import pandas as pd
from datetime import date
import time

def render_pestana_proyectos_eventos(client):
    st.markdown("<h3 style='margin-top: -15px;'>🗓️ Proyectos, Reuniones y Eventos</h3>", unsafe_allow_html=True)
    
    # Extraer lista de empleados para usarla globalmente en bloqueos y ferias
    try:
        res_emp = client.table("personal_empleados").select("nombre").eq("activo", True).execute()
        emp_list = ["Todas"] + [e['nombre'] for e in res_emp.data] if res_emp.data else ["Todas"]
    except: emp_list = ["Todas"]
    
    tab_macro, tab_ferias, tab_talleres, tab_reuniones = st.tabs([
        "🚀 Proyectos de Expansión", 
        "🎪 Ferias y Eventos Externos",
        "🎟️ Talleres y Cursos (Clientes)",
        "⛔ Reuniones y Bloqueos"
    ])

    with tab_macro:
        st.markdown("#### 🚀 Gestión de Macro-Proyectos")
        st.info("Administra proyectos a gran escala (Ej: Abrir nueva clínica, Reformas). Para tareas del día a día, usa la pestaña 'Tareas'.")
        
        try:
            res_macro = client.table("proyectos_macro").select("*").order("created_at", desc=True).execute()
            proyectos = res_macro.data if res_macro.data else []
        except Exception:
            proyectos = []
            
        opciones_proy = ["➕ Crear Nuevo Proyecto"] + [f"{p['titulo']} ({p['estado']})" for p in proyectos]
        proy_sel_str = st.selectbox("Selecciona un proyecto:", opciones_proy)
        
        if proy_sel_str == "➕ Crear Nuevo Proyecto":
            with st.form("form_nuevo_macro", clear_on_submit=True):
                m_tit = st.text_input("Título del Proyecto *", placeholder="Ej: Apertura Clínica Veterinaria")
                m_desc = st.text_area("Descripción / Objetivos")
                c1, c2 = st.columns(2)
                with c1: m_ini = st.date_input("Fecha Inicio", value=date.today())
                with c2: m_fin = st.date_input("Fecha Fin Estimada", value=date.today())
                c3, c4 = st.columns(2)
                with c3: m_pres = st.number_input("Presupuesto Estimado (€)", min_value=0.0, format="%.2f", step=100.0)
                with c4: m_est = st.selectbox("Estado", ["Planificación", "En curso", "Pausado", "Completado", "Cancelado"])
                
                if st.form_submit_button("Crear Proyecto", type="primary", use_container_width=True):
                    if m_tit:
                        client.table("proyectos_macro").insert({
                            "titulo": m_tit, "descripcion": m_desc, "estado": m_est,
                            "fecha_inicio": str(m_ini), "fecha_fin_estimada": str(m_fin),
                            "presupuesto_estimado": float(m_pres), "coste_real": 0.0
                        }).execute()
                        st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                        st.success("Proyecto creado."); time.sleep(1); st.rerun()
                    else: st.warning("El título es obligatorio.")
        else:
            idx = opciones_proy.index(proy_sel_str) - 1
            p_actual = proyectos[idx]
            p_id = p_actual['id']
            
            c_m1, c_m2, c_m3 = st.columns(3)
            with c_m1: st.metric("Presupuesto Estimado", f"{p_actual['presupuesto_estimado']:.2f} €")
            with c_m2: 
                desviacion = p_actual['presupuesto_estimado'] - p_actual['coste_real']
                st.metric("Coste Real Acumulado", f"{p_actual['coste_real']:.2f} €", delta=f"{desviacion:.2f} € (Margen)", delta_color="normal" if desviacion >=0 else "inverse")
            with c_m3: 
                f_i = pd.to_datetime(p_actual.get('fecha_inicio', '')).strftime('%d/%m/%Y') if p_actual.get('fecha_inicio') else '---'
                f_f = pd.to_datetime(p_actual.get('fecha_fin_estimada', '')).strftime('%d/%m/%Y') if p_actual.get('fecha_fin_estimada') else '---'
                st.metric("Fechas", f"{f_i} ➔ {f_f}")
            
            st.markdown("---")
            t_hitos, t_ajustes = st.tabs(["📌 Hitos y Tareas (Línea de tiempo)", "⚙️ Ajustes del Proyecto"])
            
            with t_hitos:
                c_h1, c_h2 = st.columns([1, 2])
                with c_h1:
                    st.markdown("##### ➕ Añadir Hito")
                    with st.form(f"nuevo_hito_{p_id}", clear_on_submit=True):
                        h_tit = st.text_input("Título del Hito *")
                        h_lim = st.date_input("Fecha Límite", value=date.today())
                        h_res = st.text_input("Responsable")
                        if st.form_submit_button("Añadir Hito", use_container_width=True):
                            if h_tit:
                                client.table("proyectos_hitos").insert({
                                    "proyecto_id": p_id, "titulo": h_tit, "fecha_limite": str(h_lim), "responsable": h_res, "estado": "Pendiente ⏳"
                                }).execute()
                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                st.success("Añadido."); time.sleep(0.5); st.rerun()
                            else: st.warning("Escribe el título.")
                with c_h2:
                    st.markdown("##### 📅 Calendario de Hitos")
                    res_hitos = client.table("proyectos_hitos").select("*").eq("proyecto_id", p_id).order("fecha_limite", desc=False).execute()
                    if res_hitos.data:
                        df_hitos = pd.DataFrame(res_hitos.data)
                        df_hitos['Fecha'] = pd.to_datetime(df_hitos['fecha_limite']).dt.strftime('%d/%m/%Y')
                        
                        df_v_hitos = df_hitos[['id', 'Fecha', 'titulo', 'responsable', 'estado']].copy()
                        df_v_hitos.insert(0, "Borrar", False)
                        
                        ed_h = st.data_editor(
                            df_v_hitos, hide_index=True, use_container_width=True,
                            column_config={
                                "Borrar": st.column_config.CheckboxColumn("🗑️", width="small"),
                                "id": None, "titulo": "Hito", "responsable": "Responsable",
                                "estado": st.column_config.SelectboxColumn("Estado", options=["Pendiente ⏳", "En curso 🏗️", "Completado ✅", "Bloqueado 🛑"])
                            }, key=f"ed_hitos_{p_id}"
                        )
                        if st.button("💾 Guardar Cambios en Hitos", type="primary"):
                            for _, r in ed_h[ed_h["Borrar"] == True].iterrows():
                                client.table("proyectos_hitos").delete().eq("id", r['id']).execute()
                            for _, r in ed_h[ed_h["Borrar"] == False].iterrows():
                                client.table("proyectos_hitos").update({"estado": str(r['estado']), "titulo": str(r['titulo']), "responsable": str(r['responsable'])}).eq("id", r['id']).execute()
                            st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                            st.success("Guardado"); time.sleep(0.5); st.rerun()
                    else: st.info("No hay hitos en este proyecto. Añade el primero en el panel izquierdo.")
            
            with t_ajustes:
                with st.form(f"ajustes_proy_{p_id}"):
                    st.markdown("##### ⚙️ Propiedades del Proyecto")
                    a_tit = st.text_input("Título", value=p_actual['titulo'])
                    a_est = st.selectbox("Estado", ["Planificación", "En curso", "Pausado", "Completado", "Cancelado"], index=["Planificación", "En curso", "Pausado", "Completado", "Cancelado"].index(p_actual['estado']))
                    c_a1, c_a2 = st.columns(2)
                    with c_a1: a_pres = st.number_input("Presupuesto Estimado (€)", value=float(p_actual['presupuesto_estimado']), step=10.0)
                    with c_a2: a_coste = st.number_input("Coste Real Acumulado (€)", value=float(p_actual['coste_real']), step=10.0)
                    a_desc = st.text_area("Descripción / Notas", value=p_actual.get('descripcion', ''))
                    if st.form_submit_button("💾 Guardar Ajustes del Proyecto", type="primary"):
                        client.table("proyectos_macro").update({
                            "titulo": a_tit, "estado": a_est, "presupuesto_estimado": float(a_pres),
                            "coste_real": float(a_coste), "descripcion": a_desc
                        }).eq("id", p_id).execute()
                        st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                        st.success("Ajustes guardados."); time.sleep(0.5); st.rerun()
                        
                if st.button("🗑️ Eliminar Proyecto Completo", type="secondary"):
                    client.table("proyectos_hitos").delete().eq("proyecto_id", p_id).execute()
                    client.table("proyectos_macro").delete().eq("id", p_id).execute()
                    st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                    st.warning("Proyecto eliminado."); time.sleep(1); st.rerun()

    with tab_reuniones:
        st.markdown("#### ⛔ Gestión de Reuniones y Bloqueos de Agenda")
        st.info("💡 Lo que programes aquí bloqueando agenda, impedirá dar citas en esos tramos a las peluqueras afectadas. Las reuniones aparecerán dibujadas en la Agenda.")
        c_r1, c_r2 = st.columns([1, 2.5])
        with c_r1:
            with st.form("form_nuevo_bloqueo", clear_on_submit=True):
                st.markdown("##### ➕ Nuevo Bloqueo / Reunión")
                b_tit = st.text_input("Título (Ej: Reunión de equipo) *")
                b_fec = st.date_input("Fecha *", value=date.today())
                c_h1, c_h2 = st.columns(2)
                with c_h1: b_ini = st.time_input("Hora Inicio *")
                with c_h2: b_fin = st.time_input("Hora Fin *")
                
                b_emp = st.selectbox("Afecta a:", emp_list)
                b_bloq = st.checkbox("🚫 Bloquear agenda de peluquería en este tramo", value=True)
                
                if st.form_submit_button("Programar Reunión", type="primary", use_container_width=True):
                    if b_tit and b_ini and b_fin:
                        client.table("agenda_bloqueos").insert({
                            "fecha": str(b_fec), "hora_inicio": b_ini.strftime("%H:%M"), "hora_fin": b_fin.strftime("%H:%M"),
                            "titulo": b_tit, "empleado_afectado": b_emp, "bloquea_agenda": b_bloq
                        }).execute()
                        st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                        st.success("Reunión programada."); time.sleep(1); st.rerun()
                    else:
                        st.warning("Completa título y horas.")

        with c_r2:
            st.markdown("##### 📅 Bloqueos y Reuniones Programadas")
            try:
                res_bl = client.table("agenda_bloqueos").select("*").order("fecha", desc=False).execute()
                if res_bl.data:
                    df_bl = pd.DataFrame(res_bl.data)
                    df_bl['Fecha'] = pd.to_datetime(df_bl['fecha']).dt.strftime('%d/%m/%Y')
                    df_bl_vista = df_bl[['id', 'Fecha', 'hora_inicio', 'hora_fin', 'titulo', 'empleado_afectado', 'bloquea_agenda']].copy()
                    df_bl_vista.insert(0, "Borrar", False)
                    
                    ed_bl = st.data_editor(
                        df_bl_vista, hide_index=True, use_container_width=True,
                        column_config={
                            "Borrar": st.column_config.CheckboxColumn("🗑️", width="small"),
                            "hora_inicio": "Inicio", "hora_fin": "Fin", "titulo": "Asunto",
                            "empleado_afectado": "Afecta a",
                            "bloquea_agenda": st.column_config.CheckboxColumn("Bloquea Agenda"), "id": None
                        }
                    )
                    if st.button("💾 Guardar Cambios de Reuniones", type="primary"):
                        for _, r in ed_bl[ed_bl["Borrar"] == True].iterrows():
                            client.table("agenda_bloqueos").delete().eq("id", r['id']).execute()
                        for _, r in ed_bl[ed_bl["Borrar"] == False].iterrows():
                            client.table("agenda_bloqueos").update({
                                "titulo": r['titulo'], "empleado_afectado": r['empleado_afectado'], "bloquea_agenda": r['bloquea_agenda']
                            }).eq("id", r['id']).execute()
                        st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                        st.success("Actualizado"); time.sleep(0.5); st.rerun()
                else:
                    st.info("No hay reuniones ni bloqueos programados en el sistema.")
            except Exception as e:
                st.info("Crea la tabla agenda_bloqueos en Supabase para habilitar esta vista.")

    with tab_ferias:
        st.markdown("#### 🎪 Gestión de Ferias y Eventos Externos")
        st.info("Organiza la logística, stands y tareas de eventos corporativos o ferias (Ej: 100x100 Mascota).")
        
        try:
            res_ferias = client.table("eventos_ferias").select("*").order("created_at", desc=True).execute()
            ferias = res_ferias.data if res_ferias.data else []
        except Exception:
            ferias = []
            
        opciones_f = ["➕ Crear Nueva Feria / Evento"] + [f"{f['titulo']} ({f['estado']})" for f in ferias]
        f_sel_str = st.selectbox("Selecciona un evento:", opciones_f)
        
        if f_sel_str == "➕ Crear Nueva Feria / Evento":
            with st.form("form_nueva_feria", clear_on_submit=True):
                f_tit = st.text_input("Título de la Feria/Evento *", placeholder="Ej: Feria 100x100 Mascota")
                f_lug = st.text_input("Lugar / Recinto")
                c1, c2 = st.columns(2)
                with c1: f_ini = st.date_input("Fecha Inicio", value=date.today())
                with c2: f_fin = st.date_input("Fecha Fin", value=date.today())
                
                f_stands = st.text_area("Logística / Stands", placeholder="Ej: 2 stands de 3x2, necesitamos 4 mesas...")
                f_planos = st.text_input("Enlace a Planos (Canva, Google Drive, OneDrive...)", placeholder="https://...")
                f_pres = st.number_input("Presupuesto Estimado (€)", min_value=0.0, format="%.2f", step=100.0)
                
                st.markdown("---")
                st.markdown("##### 📅 Bloqueo Rápido en Agenda (Opcional)")
                f_bloquear = st.checkbox("🚫 Bloquear horario (Podrás editar turnos y rotaciones luego dentro del evento)", value=False)
                c3, c4 = st.columns(2)
                import datetime as dt_module
                from datetime import timedelta
                with c3: f_hora_ini = st.time_input("Hora Inicio Bloqueo", value=dt_module.time(9, 0))
                with c4: f_hora_fin = st.time_input("Hora Fin Bloqueo", value=dt_module.time(21, 0))
                f_emp_bloq = st.multiselect("Afecta a (Peluqueros):", emp_list, default=["Todas"])
                
                if st.form_submit_button("Crear Feria", type="primary", use_container_width=True):
                    if f_tit:
                        client.table("eventos_ferias").insert({
                            "titulo": f_tit, "fecha_inicio": str(f_ini), "fecha_fin": str(f_fin),
                            "lugar": f_lug, "presupuesto": float(f_pres), "coste_real": 0.0,
                            "logistica_stands": f_stands, "enlaces_planos": f_planos, "estado": "Planificación"
                        }).execute()
                        
                        if f_bloquear and f_emp_bloq:
                            delta = f_fin - f_ini
                            inserts_bloqueos = []
                            empleados_a_bloquear = ["Todas"] if "Todas" in f_emp_bloq else f_emp_bloq
                            for i in range(delta.days + 1):
                                dia_bloqueo = f_ini + timedelta(days=i)
                                for emp in empleados_a_bloquear:
                                    inserts_bloqueos.append({
                                        "fecha": str(dia_bloqueo),
                                        "hora_inicio": f_hora_ini.strftime("%H:%M"),
                                        "hora_fin": f_hora_fin.strftime("%H:%M"),
                                        "titulo": f"🎪 {f_tit}",
                                        "empleado_afectado": emp,
                                        "bloquea_agenda": True
                                    })
                            if inserts_bloqueos:
                                client.table("agenda_bloqueos").insert(inserts_bloqueos).execute()
                                
                        st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                        st.success("Feria creada y agendada."); time.sleep(1); st.rerun()
                    else: st.warning("El título es obligatorio.")
        else:
            idx = opciones_f.index(f_sel_str) - 1
            f_actual = ferias[idx]
            f_id = f_actual['id']
            
            c_f1, c_f2, c_f3 = st.columns(3)
            with c_f1: st.metric("Lugar", f_actual.get('lugar', 'No definido'))
            with c_f2: 
                desviacion = f_actual['presupuesto'] - f_actual['coste_real']
                st.metric("Presupuesto vs Coste", f"{f_actual['coste_real']} €", delta=f"{desviacion:.2f} € (Margen)", delta_color="normal" if desviacion >=0 else "inverse")
            with c_f3: 
                f_i = pd.to_datetime(f_actual.get('fecha_inicio', '')).strftime('%d/%m/%Y') if f_actual.get('fecha_inicio') else '---'
                f_f = pd.to_datetime(f_actual.get('fecha_fin', '')).strftime('%d/%m/%Y') if f_actual.get('fecha_fin') else '---'
                st.metric("Fechas", f"{f_i} ➔ {f_f}")
                
            st.markdown("---")
            t_ftareas, t_flog = st.tabs(["📌 Lluvia de Ideas y Preparación", "⚙️ Logística, Planos y Ajustes"])
            
            with t_ftareas:
                c_ft1, c_ft2 = st.columns([1, 2])
                with c_ft1:
                    st.markdown("##### ➕ Añadir Tarea")
                    with st.form(f"nueva_tar_fer_{f_id}", clear_on_submit=True):
                        ft_tar = st.text_input("Tarea / Idea *")
                        ft_res = st.text_input("Responsable")
                        ft_lim = st.date_input("Fecha Límite", value=date.today())
                        if st.form_submit_button("Añadir Tarea", use_container_width=True):
                            if ft_tar:
                                client.table("eventos_ferias_tareas").insert({
                                    "feria_id": f_id, "tarea": ft_tar, "responsable": ft_res, "fecha_limite": str(ft_lim), "estado": "Pendiente ⏳"
                                }).execute()
                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                st.success("Añadida."); time.sleep(0.5); st.rerun()
                            else: st.warning("Escribe la tarea.")
                with c_ft2:
                    st.markdown("##### 📋 Panel de Preparación")
                    res_ft = client.table("eventos_ferias_tareas").select("*").eq("feria_id", f_id).order("fecha_limite", desc=False).execute()
                    if res_ft.data:
                        df_ft = pd.DataFrame(res_ft.data)
                        df_ft['Fecha'] = pd.to_datetime(df_ft['fecha_limite']).dt.strftime('%d/%m/%Y')
                        df_v_ft = df_ft[['id', 'Fecha', 'tarea', 'responsable', 'estado']].copy()
                        df_v_ft.insert(0, "Borrar", False)
                        
                        ed_ft = st.data_editor(
                            df_v_ft, hide_index=True, use_container_width=True,
                            column_config={
                                "Borrar": st.column_config.CheckboxColumn("🗑️", width="small"),
                                "id": None, "tarea": "Tarea / Idea", "responsable": "Responsable",
                                "estado": st.column_config.SelectboxColumn("Estado", options=["Pendiente ⏳", "En curso 🏗️", "Completado ✅"])
                            }, key=f"ed_ftar_{f_id}"
                        )
                        if st.button("💾 Guardar Cambios en Tareas", type="primary"):
                            for _, r in ed_ft[ed_ft["Borrar"] == True].iterrows():
                                client.table("eventos_ferias_tareas").delete().eq("id", r['id']).execute()
                            for _, r in ed_ft[ed_ft["Borrar"] == False].iterrows():
                                client.table("eventos_ferias_tareas").update({"estado": str(r['estado']), "tarea": str(r['tarea']), "responsable": str(r['responsable'])}).eq("id", r['id']).execute()
                            st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                            st.success("Guardado"); time.sleep(0.5); st.rerun()
                    else: st.info("No hay tareas asignadas para esta feria.")
            
            with t_flog:
                with st.form(f"ajustes_fer_{f_id}"):
                    st.markdown("##### ⚙️ Configuración Logística")
                    fa_tit = st.text_input("Título", value=f_actual['titulo'])
                    fa_est = st.selectbox("Estado", ["Planificación", "En curso", "Pausado", "Completado", "Cancelado"], index=["Planificación", "En curso", "Pausado", "Completado", "Cancelado"].index(f_actual.get('estado', 'Planificación')))
                    c_fa1, c_fa2 = st.columns(2)
                    with c_fa1: fa_pres = st.number_input("Presupuesto (€)", value=float(f_actual['presupuesto']), step=10.0)
                    with c_fa2: fa_coste = st.number_input("Coste Real (€)", value=float(f_actual.get('coste_real', 0.0)), step=10.0)
                    fa_stands = st.text_area("Logística / Stands", value=f_actual.get('logistica_stands', ''), height=100)
                    fa_planos = st.text_input("Enlace a Planos/Documentos", value=f_actual.get('enlaces_planos', ''))
                    
                    if st.form_submit_button("💾 Guardar Detalles Logísticos", type="primary"):
                        client.table("eventos_ferias").update({
                            "titulo": fa_tit, "estado": fa_est, "presupuesto": float(fa_pres),
                            "coste_real": float(fa_coste), "logistica_stands": fa_stands, "enlaces_planos": fa_planos
                        }).eq("id", f_id).execute()
                        st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                        st.success("Detalles guardados."); time.sleep(0.5); st.rerun()
                        
                if f_actual.get('enlaces_planos'):
                    url_plano = f_actual['enlaces_planos']
                    if not url_plano.startswith('http'): url_plano = 'https://' + url_plano
                    st.markdown(f"**🔗 Enlace asociado:** <a href='{url_plano}' target='_blank'>Abrir Documento / Plano en nueva pestaña</a>", unsafe_allow_html=True)
                        
                st.markdown("---")
                st.markdown("##### 📅 Sincronización Avanzada con Agenda")
                st.info("Añade bloqueos específicos por día, hora y empleado para gestionar las rotaciones del evento sin alterar sus cuadrantes.")
                
                # Mostrar bloqueos actuales
                res_bl_fer = client.table("agenda_bloqueos").select("*").eq("titulo", f"🎪 {f_actual['titulo']}").order("fecha", desc=False).execute()
                if res_bl_fer.data:
                    df_bl_fer = pd.DataFrame(res_bl_fer.data)
                    df_bl_fer['Fecha'] = pd.to_datetime(df_bl_fer['fecha']).dt.strftime('%d/%m/%Y')
                    df_bl_fer_v = df_bl_fer[['id', 'Fecha', 'hora_inicio', 'hora_fin', 'empleado_afectado']].copy()
                    df_bl_fer_v.insert(0, "Borrar", False)
                    
                    ed_bl_fer = st.data_editor(
                        df_bl_fer_v, hide_index=True, use_container_width=True,
                        column_config={
                            "Borrar": st.column_config.CheckboxColumn("🗑️", width="small"),
                            "id": None, "hora_inicio": "Inicio", "hora_fin": "Fin", "empleado_afectado": "Afecta a"
                        }, key=f"ed_bl_fer_{f_id}"
                    )
                    if st.button("💾 Eliminar bloqueos marcados", key=f"btn_del_bl_{f_id}"):
                        for _, r in ed_bl_fer[ed_bl_fer["Borrar"] == True].iterrows():
                            client.table("agenda_bloqueos").delete().eq("id", r['id']).execute()
                        st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                        st.rerun()
                else:
                    st.write("No hay bloqueos activos para este evento.")
                
                with st.form(f"add_bloqueo_fer_{f_id}", clear_on_submit=True):
                    import datetime as dt_module
                    from datetime import timedelta
                    
                    c_fec1, c_fec2 = st.columns(2)
                    with c_fec1: fb_fec_ini = st.date_input("Desde el día", value=pd.to_datetime(f_actual.get('fecha_inicio')).date())
                    with c_fec2: fb_fec_fin = st.date_input("Hasta el día", value=pd.to_datetime(f_actual.get('fecha_inicio')).date())
                    
                    c_hor1, c_hor2 = st.columns(2)
                    with c_hor1: fb_ini = st.time_input("Hora Inicio", value=dt_module.time(9, 0))
                    with c_hor2: fb_fin = st.time_input("Hora Fin", value=dt_module.time(21, 0))
                    
                    fb_emp = st.multiselect("Bloquear a (Peluqueros):", emp_list, default=["Todas"])
                    
                    if st.form_submit_button("➕ Añadir Turno/Bloqueo al Evento"):
                        if fb_emp:
                            if fb_fec_fin >= fb_fec_ini:
                                delta = fb_fec_fin - fb_fec_ini
                                inserts_bloqueos = []
                                empleados_a_bloquear = ["Todas"] if "Todas" in fb_emp else fb_emp
                                
                                for i in range(delta.days + 1):
                                    dia_actual = fb_fec_ini + timedelta(days=i)
                                    for emp in empleados_a_bloquear:
                                        inserts_bloqueos.append({
                                            "fecha": str(dia_actual),
                                            "hora_inicio": fb_ini.strftime("%H:%M"),
                                            "hora_fin": fb_fin.strftime("%H:%M"),
                                            "titulo": f"🎪 {f_actual['titulo']}",
                                            "empleado_afectado": emp,
                                            "bloquea_agenda": True
                                        })
                                        
                                if inserts_bloqueos:
                                    client.table("agenda_bloqueos").insert(inserts_bloqueos).execute()
                                    st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                    st.success("Bloqueo añadido."); time.sleep(1); st.rerun()
                            else:
                                st.error("La fecha de fin no puede ser anterior a la de inicio.")
                        else:
                            st.warning("Selecciona al menos un empleado o 'Todas'.")

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Eliminar Feria Completa", type="secondary"):
                    client.table("eventos_ferias_tareas").delete().eq("feria_id", f_id).execute()
                    client.table("eventos_ferias").delete().eq("id", f_id).execute()
                    client.table("agenda_bloqueos").delete().eq("titulo", f"🎪 {f_actual['titulo']}").execute()
                    st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                    st.warning("Feria eliminada."); time.sleep(1); st.rerun()

    with tab_talleres:
        st.markdown("#### 🎟️ Gestión de Talleres y Cursos (Clientes)")
        st.info("Organiza cursos presenciales en la tienda (cepillado, nutrición, etc.), controla el aforo y gestiona las reservas de los clientes.")
        c_ev1, c_ev2 = st.columns([1, 2.5])
        with c_ev1:
            with st.container(border=True):
                st.markdown("##### ➕ Crear Nuevo Evento")
                with st.form("form_nuevo_evento", clear_on_submit=True):
                    e_titulo = st.text_input("Título del Taller *", placeholder="Ej: Taller de cepillado básico")
                    e_fecha = st.date_input("Fecha planificada", value=date.today())
                    e_hora = st.text_input("Hora y Turno", placeholder="Ej: Sábado 10:00 - 12:00")
                    c_e1, c_e2 = st.columns(2)
                    with c_e1: e_plazas = st.number_input("Plazas totales", min_value=1, value=8)
                    with c_e2: e_precio = st.number_input("Precio Reserva (€)", min_value=0.0, format="%.2f", value=15.0, step=0.01)
                    e_desc = st.text_area("Descripción / Temario")
                    if st.form_submit_button("Crear Evento", type="primary", use_container_width=True):
                        if e_titulo:
                            try:
                                client.table("eventos_talleres").insert({"titulo": e_titulo, "fecha": str(e_fecha), "hora": e_hora, "plazas_totales": int(e_plazas), "precio": float(e_precio), "descripcion": e_desc}).execute()
                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                st.success("Evento creado."); time.sleep(1); st.rerun()
                            except: st.error("⚠️ Ejecuta el código SQL en Supabase primero.")
                        else: st.warning("El título es obligatorio.")
        with c_ev2:
            try:
                res_ev = client.table("eventos_talleres").select("*").order("fecha", desc=False).execute()
                if res_ev.data:
                    df_ev = pd.DataFrame(res_ev.data); df_ev['Fecha'] = pd.to_datetime(df_ev['fecha']).dt.strftime('%d/%m/%Y')
                    st.markdown("##### 📅 Panel de Gestión de Inscripciones")
                    opciones_ev = {f"{e['Fecha']} | {e['titulo']} (Reserva: {e['precio']}€)": e['id'] for _, e in df_ev.iterrows()}
                    ev_sel_str = st.selectbox("Selecciona un evento para gestionar su aforo:", list(opciones_ev.keys()))
                    if ev_sel_str:
                        ev_id = opciones_ev[ev_sel_str]; ev_data = df_ev[df_ev['id'] == ev_id].iloc[0]
                        res_asi = client.table("eventos_asistentes").select("id, pagado, clientes(nombre_dueno, telefono)").eq("evento_id", ev_id).execute()
                        inscritos = len(res_asi.data) if res_asi.data else 0; plazas_libres = ev_data['plazas_totales'] - inscritos
                        st.markdown(f"**Aforo actual:** {inscritos} de {ev_data['plazas_totales']} plazas ocupadas. (<span style='color:green;'>{plazas_libres} libres</span>)", unsafe_allow_html=True)
                        st.progress(inscritos / ev_data['plazas_totales'] if ev_data['plazas_totales'] > 0 else 0)
                        c_asi1, c_asi2 = st.columns([2, 1])
                        with c_asi1:
                            res_cli = client.table("clientes").select("id, nombre_dueno, telefono").execute()
                            dict_cli = {f"{c['nombre_dueno']} ({c.get('telefono','')})": c['id'] for c in res_cli.data} if res_cli.data else {}
                            cli_sel = st.selectbox("Inscribir nuevo cliente al evento:", [""] + list(dict_cli.keys()))
                        with c_asi2:
                            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                            if st.button("➕ Añadir a la Lista", use_container_width=True, disabled=plazas_libres<=0):
                                if cli_sel:
                                    try:
                                        client.table("eventos_asistentes").insert({"evento_id": ev_id, "cliente_id": dict_cli[cli_sel], "pagado": False}).execute()
                                        st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                        st.success("Inscrito."); time.sleep(0.5); st.rerun()
                                    except: st.error("Este cliente ya estaba inscrito.")
                        if res_asi.data:
                            df_a = pd.DataFrame([{"id": a['id'], "Cliente": a['clientes']['nombre_dueno'], "Teléfono": a['clientes']['telefono'], "Reserva Pagada": a['pagado']} for a in res_asi.data])
                            df_a_vista = df_a.copy(); df_a_vista.insert(0, "Quitar", False)
                            ed_a = st.data_editor(df_a_vista, hide_index=True, use_container_width=True, column_config={"Quitar": st.column_config.CheckboxColumn("🗑️", width="small"), "Reserva Pagada": st.column_config.CheckboxColumn("💰 Reserva Pagada"), "id": None, "Cliente": st.column_config.TextColumn(disabled=True), "Teléfono": st.column_config.TextColumn(disabled=True)}, key=f"ed_asi_{ev_id}")
                            if st.button("💾 Guardar Cambios en la Lista de Asistentes", type="primary"):
                                for _, rb in ed_a[ed_a["Quitar"] == True].iterrows(): client.table("eventos_asistentes").delete().eq("id", rb['id']).execute()
                                for _, rg in ed_a[ed_a["Quitar"] == False].iterrows(): client.table("eventos_asistentes").update({"pagado": bool(rg['Reserva Pagada'])}).eq("id", rg['id']).execute()
                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                st.success("Lista de asistentes actualizada"); time.sleep(0.5)
                                st.rerun()
                else: st.info("No hay eventos programados. Rellena el formulario de la izquierda para crear el primero.")
            except Exception as e: st.info("🔧 Ejecuta el código SQL en Supabase para activar la función de Eventos.")