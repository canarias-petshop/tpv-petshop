import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import time
from postgrest import SyncPostgrestClient
from zoneinfo import ZoneInfo

def render_pestana_personal(client: SyncPostgrestClient):
    st.header("⏱️ Control de Personal y Horarios")

    # 1. Cargar empleados activos
    try:
        empleados_res = client.table("personal_empleados").select("*").eq("activo", True).execute()
        empleados = empleados_res.data
    except Exception as e:
        st.error(f"Error al cargar empleados: {e}")
        empleados = []

    if not empleados:
        st.warning("No hay empleados registrados. El administrador debe añadir personal primero.")
    else:
        # Fichaje Rápido
        with st.container(border=True):
            st.subheader("Registrar Fichaje")
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                emp_nombres = {e['nombre']: e for e in empleados}
                nombre_sel = st.selectbox("Empleado", options=list(emp_nombres.keys()))
                emp_sel = emp_nombres.get(nombre_sel)
            with c2:
                pin = st.text_input("PIN (4 dígitos)", type="password", max_chars=4)
            with c3:
                st.write("")
                st.write("")
                if st.button("Fichar Entrada/Salida", use_container_width=True, type="primary"):
                    if emp_sel and pin == emp_sel['pin_fichaje']:
                        tz_canarias = ZoneInfo("Atlantic/Canary")
                        ahora_dt = datetime.now(tz_canarias)
                        hoy = ahora_dt.date().isoformat()
                        ahora = ahora_dt.isoformat()
                        
                        # Buscar si ya tiene una entrada sin salida hoy
                        fichajes_res = client.table("personal_fichajes").select("*").eq("empleado_id", emp_sel['id']).eq("fecha", hoy).is_("hora_salida", "null").execute()
                        fichajes = fichajes_res.data
                        
                        if fichajes:
                            # Fichar salida
                            fichaje_id = fichajes[0]['id']
                            hora_entrada = datetime.fromisoformat(fichajes[0]['hora_entrada'])
                            if hora_entrada.tzinfo is None:
                                hora_entrada = hora_entrada.replace(tzinfo=tz_canarias)
                            minutos = int((ahora_dt - hora_entrada).total_seconds() / 60)
                            
                            client.table("personal_fichajes").update({
                                "hora_salida": ahora,
                                "minutos_trabajados": minutos
                            }).eq("id", fichaje_id).execute()
                            st.success(f"Salida registrada para {nombre_sel} a las {ahora_dt.strftime('%H:%M')}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            # Fichar entrada
                            client.table("personal_fichajes").insert({
                                "empleado_id": emp_sel['id'],
                                "fecha": hoy,
                                "hora_entrada": ahora
                            }).execute()
                            st.success(f"Entrada registrada para {nombre_sel} a las {ahora_dt.strftime('%H:%M')}")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.error("PIN incorrecto.")

        # Visualizar Cuadrante Flexible (Para todos)
        st.subheader("📅 Cuadrante de Trabajo")
        hoy = date.today()
        c_v1, c_v2 = st.columns(2)
        with c_v1: f_ini_ver = st.date_input("Desde:", value=hoy - timedelta(days=hoy.weekday()), key="v_ini")
        with c_v2: f_fin_ver = st.date_input("Hasta:", value=f_ini_ver + timedelta(days=27), key="v_fin") # Default 4 semanas
        
        try:
            # Alinear siempre a Lunes y Domingo para mostrar semanas completas
            start_aligned = f_ini_ver - timedelta(days=f_ini_ver.weekday())
            end_aligned = f_fin_ver + timedelta(days=6 - f_fin_ver.weekday())

            cuadrantes_res = client.table("personal_cuadrantes").select("*").gte("fecha", start_aligned.isoformat()).lte("fecha", end_aligned.isoformat()).execute()
            df_cuadrante = pd.DataFrame(cuadrantes_res.data)
            
            dias_es = {0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue", 4: "Vie", 5: "Sáb", 6: "Dom"}
            
            if not df_cuadrante.empty:
                df_emp = pd.DataFrame(empleados)[['id', 'nombre']]
                df_cuadrante = df_cuadrante.merge(df_emp, left_on='empleado_id', right_on='id')
                df_cuadrante['Fecha_Str'] = pd.to_datetime(df_cuadrante['fecha']).apply(lambda x: f"{dias_es[x.weekday()]} {x.strftime('%d/%m')}")
                df_pivot = df_cuadrante.pivot_table(index='nombre', columns='Fecha_Str', values='turno', aggfunc='first')
            else:
                df_pivot = pd.DataFrame()
                
            curr_w = start_aligned
            while curr_w <= end_aligned:
                w_end = curr_w + timedelta(days=6)
                st.markdown(f"<h5 style='margin-bottom: 5px; color: #005275; margin-top: 10px;'>Semana del {curr_w.strftime('%d/%m/%Y')} al {w_end.strftime('%d/%m/%Y')}</h5>", unsafe_allow_html=True)
                
                fechas_semana = [curr_w + timedelta(days=x) for x in range(7)]
                cols_semana = [f"{dias_es[d.weekday()]} {d.strftime('%d/%m')}" for d in fechas_semana]
                
                if not df_pivot.empty:
                    # Mostrar solo las columnas de esta semana, rellenar si no hay turno
                    df_show = df_pivot.reindex(columns=cols_semana).fillna('-')
                else:
                    df_show = pd.DataFrame(index=[e['nombre'] for e in empleados], columns=cols_semana).fillna('-')
                    
                st.dataframe(df_show, use_container_width=True)
                curr_w += timedelta(days=7)
                
        except Exception as e:
            st.error(f"Error al cargar cuadrante: {e}")

    # Panel de Administrador
    if st.session_state.rol == "Admin":
        st.divider()
        st.subheader("🛠️ Panel de Administrador (Gestión de Personal)")
        
        tab_admin1, tab_admin2, tab_admin3 = st.tabs(["Empleados", "Gestión de Cuadrante (Editable)", "Ver Fichajes"])
        
        with tab_admin1:
            st.markdown("Añadir nuevo empleado:")
            with st.form("form_nuevo_empleado"):
                c1, c2 = st.columns(2)
                nuevo_nom = c1.text_input("Nombre")
                nuevo_pin = c2.text_input("PIN (4 dígitos)", max_chars=4)
                if st.form_submit_button("Crear Empleado"):
                    if nuevo_nom and len(nuevo_pin) == 4:
                        client.table("personal_empleados").insert({"nombre": nuevo_nom, "pin_fichaje": nuevo_pin}).execute()
                        st.success("Empleado creado")
                        st.rerun()
                    else:
                        st.error("El nombre y un PIN de 4 dígitos son obligatorios.")
                        
            st.markdown("Lista de empleados:")
            st.dataframe(pd.DataFrame(empleados), hide_index=True)

        with tab_admin2:
            st.markdown("#### 🗓️ Editor Visual de Cuadrantes")
            st.info("Selecciona el rango de fechas. Edita los turnos haciendo **doble clic en las celdas**. Las tablas se dividen por semanas para mayor comodidad. Al terminar, pulsa 'Guardar Todo el Cuadrante'.")
            
            c_e1, c_e2 = st.columns(2)
            with c_e1: f_ini_ed = st.date_input("Editor Desde:", value=hoy - timedelta(days=hoy.weekday()), key="e_ini")
            with c_e2: f_fin_ed = st.date_input("Editor Hasta:", value=f_ini_ed + timedelta(days=27), key="e_fin")
            
            if empleados:
                start_aligned_ed = f_ini_ed - timedelta(days=f_ini_ed.weekday())
                end_aligned_ed = f_fin_ed + timedelta(days=6 - f_fin_ed.weekday())
                dias_es = {0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue", 4: "Vie", 5: "Sáb", 6: "Dom"}
                
                # Cargar datos existentes
                res_q = client.table("personal_cuadrantes").select("*").gte("fecha", start_aligned_ed.isoformat()).lte("fecha", end_aligned_ed.isoformat()).execute()
                q_map = {(d['empleado_id'], d['fecha']): d['turno'] for d in (res_q.data if res_q.data else [])}
                
                curr_w = start_aligned_ed
                edited_dfs = []
                
                while curr_w <= end_aligned_ed:
                    w_end = curr_w + timedelta(days=6)
                    st.markdown(f"<h5 style='margin-bottom: 5px; color: #005275; margin-top: 15px;'>Semana del {curr_w.strftime('%d/%m/%Y')} al {w_end.strftime('%d/%m/%Y')}</h5>", unsafe_allow_html=True)
                    fechas_semana = [curr_w + timedelta(days=x) for x in range(7)]
                    
                    grid_data = []
                    for emp in empleados:
                        row = {"Empleado": emp['nombre'], "id_emp": emp['id']}
                        for d in fechas_semana: 
                            row[d.isoformat()] = q_map.get((emp['id'], d.isoformat()), "")
                        grid_data.append(row)
                        
                    col_config = {"id_emp": None, "Empleado": st.column_config.TextColumn("Empleado", disabled=True)}
                    for d in fechas_semana:
                        col_config[d.isoformat()] = st.column_config.TextColumn(f"{dias_es[d.weekday()]} {d.strftime('%d/%m')}")
                        
                    ed_grid = st.data_editor(pd.DataFrame(grid_data), column_config=col_config, hide_index=True, use_container_width=True, key=f"ed_grid_{curr_w.isoformat()}")
                    edited_dfs.append((fechas_semana, ed_grid))
                    
                    curr_w += timedelta(days=7)
                
                st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                if st.button("💾 Guardar Todo el Cuadrante", type="primary", use_container_width=True):
                    emp_ids = [e['id'] for e in empleados]
                    # 1. Limpiamos el rango de fechas seleccionado
                    client.table("personal_cuadrantes").delete().in_("empleado_id", emp_ids).gte("fecha", start_aligned_ed.isoformat()).lte("fecha", end_aligned_ed.isoformat()).execute()
                    # 2. Insertamos todos los turnos que no estén en blanco
                    inserts = []
                    for fechas_semana, ed_grid in edited_dfs:
                        for _, row in ed_grid.iterrows():
                            for d in fechas_semana:
                                val = row.get(d.isoformat(), "")
                                if val and str(val).strip() != "":
                                    inserts.append({"empleado_id": row['id_emp'], "fecha": d.isoformat(), "turno": str(val).strip()})
                    if inserts: client.table("personal_cuadrantes").insert(inserts).execute()
                    st.success("¡Cuadrante guardado exitosamente!"); time.sleep(1); st.rerun()
        
        with tab_admin3:
            st.markdown("Historial de fichajes:")
            try:
                fichajes_totales = client.table("personal_fichajes").select("*").order("fecha", desc=True).limit(50).execute()
                if fichajes_totales.data:
                    df_fich = pd.DataFrame(fichajes_totales.data)
                    df_emp = pd.DataFrame(empleados)[['id', 'nombre']]
                    df_fich = df_fich.merge(df_emp, left_on='empleado_id', right_on='id', how='left')
                    
                    def format_hm(ts):
                        if not ts: return ""
                        try:
                            dt = datetime.fromisoformat(ts)
                            if dt.tzinfo is None: dt = dt.replace(tzinfo=ZoneInfo("Atlantic/Canary"))
                            else: dt = dt.astimezone(ZoneInfo("Atlantic/Canary"))
                            return dt.strftime('%H:%M')
                        except: return ts
                        
                    df_fich['hora_entrada'] = df_fich['hora_entrada'].apply(format_hm)
                    df_fich['hora_salida'] = df_fich['hora_salida'].apply(format_hm)
                    df_fich['fecha'] = pd.to_datetime(df_fich['fecha']).dt.strftime('%d/%m/%Y')
                    
                    cols = ['nombre', 'fecha', 'hora_entrada', 'hora_salida', 'minutos_trabajados']
                    st.dataframe(df_fich[cols], use_container_width=True, hide_index=True)
                else:
                    st.info("No hay fichajes registrados.")
            except Exception as e:
                pass
