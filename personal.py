import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from postgrest import SyncPostgrestClient

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
                        hoy = date.today().isoformat()
                        ahora = datetime.now().isoformat()
                        
                        # Buscar si ya tiene una entrada sin salida hoy
                        fichajes_res = client.table("personal_fichajes").select("*").eq("empleado_id", emp_sel['id']).eq("fecha", hoy).is_("hora_salida", "null").execute()
                        fichajes = fichajes_res.data
                        
                        if fichajes:
                            # Fichar salida
                            fichaje_id = fichajes[0]['id']
                            hora_entrada = datetime.fromisoformat(fichajes[0]['hora_entrada'])
                            minutos = int((datetime.now() - hora_entrada.replace(tzinfo=None)).total_seconds() / 60)
                            
                            client.table("personal_fichajes").update({
                                "hora_salida": ahora,
                                "minutos_trabajados": minutos
                            }).eq("id", fichaje_id).execute()
                            st.success(f"Salida registrada para {nombre_sel} a las {datetime.now().strftime('%H:%M')}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            # Fichar entrada
                            client.table("personal_fichajes").insert({
                                "empleado_id": emp_sel['id'],
                                "fecha": hoy,
                                "hora_entrada": ahora
                            }).execute()
                            st.success(f"Entrada registrada para {nombre_sel} a las {datetime.now().strftime('%H:%M')}")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.error("PIN incorrecto.")

        # Visualizar Cuadrante Semanal
        st.subheader("📅 Tu Cuadrante de la Semana")
        # Obtener inicio de la semana actual
        hoy = date.today()
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        fin_semana = inicio_semana + timedelta(days=6)
        
        try:
            cuadrantes_res = client.table("personal_cuadrantes").select("*").gte("fecha", inicio_semana.isoformat()).lte("fecha", fin_semana.isoformat()).execute()
            df_cuadrante = pd.DataFrame(cuadrantes_res.data)
            
            if not df_cuadrante.empty:
                # Combinar con nombres
                df_emp = pd.DataFrame(empleados)[['id', 'nombre']]
                df_cuadrante = df_cuadrante.merge(df_emp, left_on='empleado_id', right_on='id')
                # Pivotar para mostrar semana
                df_pivot = df_cuadrante.pivot_table(index='nombre', columns='fecha', values='turno', aggfunc='first').fillna('-')
                st.dataframe(df_pivot, use_container_width=True)
            else:
                st.info("No hay turnos asignados para esta semana.")
        except Exception as e:
            st.error(f"Error al cargar cuadrante: {e}")

    # Panel de Administrador
    if st.session_state.rol == "Admin":
        st.divider()
        st.subheader("🛠️ Panel de Administrador (Gestión de Personal)")
        
        tab_admin1, tab_admin2, tab_admin3 = st.tabs(["Empleados", "Asignar Turnos", "Ver Fichajes"])
        
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
            st.markdown("Asignar turnos rotativos:")
            if empleados:
                with st.form("form_asignar_turno"):
                    c1, c2, c3 = st.columns(3)
                    emp_asig = c1.selectbox("Empleado", options=list(emp_nombres.keys()), key="emp_asig")
                    fecha_asig = c2.date_input("Fecha")
                    turno_asig = c3.selectbox("Turno", ["Mañana", "Tarde", "Completo", "Libre"])
                    
                    if st.form_submit_button("Asignar Turno"):
                        emp_id = emp_nombres[emp_asig]['id']
                        # Usar upsert o comprobar si existe
                        existente = client.table("personal_cuadrantes").select("id").eq("empleado_id", emp_id).eq("fecha", fecha_asig.isoformat()).execute()
                        if existente.data:
                            client.table("personal_cuadrantes").update({"turno": turno_asig}).eq("id", existente.data[0]['id']).execute()
                        else:
                            client.table("personal_cuadrantes").insert({"empleado_id": emp_id, "fecha": fecha_asig.isoformat(), "turno": turno_asig}).execute()
                        st.success("Turno asignado/actualizado.")
                        st.rerun()
        
        with tab_admin3:
            st.markdown("Historial de fichajes:")
            try:
                fichajes_totales = client.table("personal_fichajes").select("*").order("fecha", desc=True).limit(50).execute()
                if fichajes_totales.data:
                    df_fich = pd.DataFrame(fichajes_totales.data)
                    df_emp = pd.DataFrame(empleados)[['id', 'nombre']]
                    df_fich = df_fich.merge(df_emp, left_on='empleado_id', right_on='id', how='left')
                    cols = ['nombre', 'fecha', 'hora_entrada', 'hora_salida', 'minutos_trabajados']
                    st.dataframe(df_fich[cols], use_container_width=True, hide_index=True)
                else:
                    st.info("No hay fichajes registrados.")
            except Exception as e:
                pass
