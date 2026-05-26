import streamlit as st
import pandas as pd
from datetime import date
import time

def render_pestana_proyectos_eventos(client):
    st.markdown("<h3 style='margin-top: -15px;'>🗓️ Proyectos, Reuniones y Eventos</h3>", unsafe_allow_html=True)
    
    tab_kanban, tab_reuniones, tab_eventos = st.tabs([
        "📋 Proyectos (Kanban)", 
        "⛔ Reuniones y Bloqueos", 
        "🎟️ Eventos y Talleres"
    ])

    with tab_kanban:
        st.markdown("#### 📋 Panel Kanban de Proyectos")
        st.info("Visualiza las tareas de gerencia por estados (Crea y edita tareas desde la pestaña 'Tareas' > 'Gestión de Dueños').")
        try:
            res_due = client.table("tareas_duenos").select("*").order("fecha_programada", desc=False).execute()
            if res_due.data:
                df_due = pd.DataFrame(res_due.data)
                c_pend, c_cur, c_comp = st.columns(3)
                
                with c_pend:
                    st.markdown("<h5 style='background-color:#ffebee; padding:10px; border-radius:5px;'>⏳ Pendientes</h5>", unsafe_allow_html=True)
                    for _, r in df_due[df_due['estado'].str.contains('Pendiente')].iterrows():
                        with st.container(border=True):
                            st.markdown(f"**{r['titulo']}**")
                            st.caption(f"📅 {pd.to_datetime(r['fecha_programada']).strftime('%d/%m/%Y')}")
                            if r.get('notas'): st.write(f"📝 {r['notas']}")
                with c_cur:
                    st.markdown("<h5 style='background-color:#fff3e0; padding:10px; border-radius:5px;'>🏗️ En curso</h5>", unsafe_allow_html=True)
                    for _, r in df_due[df_due['estado'].str.contains('curso')].iterrows():
                        with st.container(border=True):
                            st.markdown(f"**{r['titulo']}**")
                            st.caption(f"📅 {pd.to_datetime(r['fecha_programada']).strftime('%d/%m/%Y')}")
                            if r.get('notas'): st.write(f"📝 {r['notas']}")
                with c_comp:
                    st.markdown("<h5 style='background-color:#e8f5e9; padding:10px; border-radius:5px;'>✅ Completadas</h5>", unsafe_allow_html=True)
                    for _, r in df_due[df_due['estado'].str.contains('Completada')].iterrows():
                        with st.container(border=True):
                            st.markdown(f"**{r['titulo']}**")
                            st.caption(f"📅 {pd.to_datetime(r['fecha_programada']).strftime('%d/%m/%Y')}")
                            if r.get('notas'): st.write(f"📝 {r['notas']}")
            else:
                st.info("No hay proyectos o tareas en la base de datos.")
        except Exception as e:
            st.error(f"Error cargando Kanban: {e}")

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
                
                try:
                    res_emp = client.table("personal_empleados").select("nombre").eq("activo", True).execute()
                    emp_list = ["Todas"] + [e['nombre'] for e in res_emp.data] if res_emp.data else ["Todas"]
                except: emp_list = ["Todas"]
                
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

    with tab_eventos:
        st.markdown("#### 🎟️ Gestión de Eventos y Talleres")
        st.info("Organiza cursos de fin de semana (cepillado, nutrición, etc.), controla el aforo y gestiona las reservas de los clientes.")
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
                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1; st.rerun()
                else: st.info("No hay eventos programados. Rellena el formulario de la izquierda para crear el primero.")
            except Exception as e: st.info("🔧 Ejecuta el código SQL en Supabase para activar la función de Eventos.")