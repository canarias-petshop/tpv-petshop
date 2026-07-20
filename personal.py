import streamlit as st
import pandas as pd
import pytz
from datetime import datetime, date, timedelta
import time
from postgrest import SyncPostgrestClient
from zoneinfo import ZoneInfo
import hashlib

@st.cache_data(show_spinner=False, ttl=300)
def get_empleados_activos(_client: SyncPostgrestClient):
    return _client.table("personal_empleados").select("*").eq("activo", True).execute()

@st.cache_data(show_spinner=False, ttl=300)
def get_ultimo_fichaje(_client: SyncPostgrestClient, empleado_id, fecha: str):
    return _client.table("personal_fichajes").select("*").eq("empleado_id", empleado_id).eq("fecha", fecha).order("id", desc=True).limit(1).execute()

@st.cache_data(show_spinner=False, ttl=300)
def get_fichajes_sin_salida(_client: SyncPostgrestClient, empleado_id, fecha: str):
    return _client.table("personal_fichajes").select("*").eq("empleado_id", empleado_id).eq("fecha", fecha).is_("hora_salida", "null").execute()

@st.cache_data(show_spinner=False, ttl=300)
def get_ultimo_hash(_client: SyncPostgrestClient):
    return _client.table("personal_fichajes").select("hash_actual").order("id", desc=True).limit(1).execute()

@st.cache_data(show_spinner=False, ttl=300)
def get_cuadrantes_rango(_client: SyncPostgrestClient, fecha_inicio: str, fecha_fin: str):
    return _client.table("personal_cuadrantes").select("*").gte("fecha", fecha_inicio).lte("fecha", fecha_fin).execute()

@st.cache_data(show_spinner=False, ttl=300)
def get_fichajes_totales(_client: SyncPostgrestClient):
    return _client.table("personal_fichajes").select("*").order("fecha", desc=True).limit(50).execute()

@st.cache_data(show_spinner=False, ttl=300)
def get_agenda_bloqueos_futuros(_client: SyncPostgrestClient, fecha_inicio: str):
    return _client.table("agenda_bloqueos").select("*").gte("fecha", fecha_inicio).order("fecha", desc=False).execute()

def limpiar_cache_personal():
    get_empleados_activos.clear()
    get_ultimo_fichaje.clear()
    get_fichajes_sin_salida.clear()
    get_ultimo_hash.clear()
    get_cuadrantes_rango.clear()
    get_fichajes_totales.clear()
    get_agenda_bloqueos_futuros.clear()
    st.cache_data.clear()

def registrar_fichaje(client: SyncPostgrestClient, empleado_id: str, nombre_empleado: str, ahora_dt: datetime) -> tuple[bool, str]:
    """Registra la entrada o salida de un empleado asegurando las reglas de negocio."""
    tz_canarias = pytz.timezone('Atlantic/Canary')
    hoy = ahora_dt.date().isoformat()
    ahora = ahora_dt.isoformat()
    
    # 1. Anti-spam de 30 minutos
    res_ultimo = get_ultimo_fichaje(client, empleado_id, hoy)
    if res_ultimo.data:
        ultimo = res_ultimo.data[0]
        str_hora = ultimo.get('hora_salida') or ultimo.get('hora_entrada')
        if str_hora:
            hora_ultima = pd.to_datetime(str_hora)
            if hora_ultima.tzinfo is None:
                hora_ultima = hora_ultima.tz_localize(tz_canarias)
            hora_ultima_utc = hora_ultima.tz_convert('UTC')
            ahora_utc = pd.to_datetime(ahora_dt).tz_convert('UTC') if pd.to_datetime(ahora_dt).tzinfo else pd.to_datetime(ahora_dt).tz_localize('UTC')
                
            min_diff = int((ahora_utc - hora_ultima_utc).total_seconds() / 60)
            if min_diff < 30:
                return False, f"⏳ **Bloqueo Activo:** El usuario **{nombre_empleado}** ya fichó hace {min_diff} minuto(s). Espera {30 - min_diff} minutos más."
                
    # 2. Buscar si ya tiene una entrada sin salida hoy
    fichajes_res = get_fichajes_sin_salida(client, empleado_id, hoy)
    fichajes = fichajes_res.data
    
    if fichajes:
        fichaje_id = fichajes[0]['id']
        hora_entrada = pd.to_datetime(fichajes[0]['hora_entrada'])
        if hora_entrada.tzinfo is None:
            hora_entrada = hora_entrada.tz_localize(tz_canarias)
        hora_entrada_utc = hora_entrada.tz_convert('UTC')
        ahora_utc = pd.to_datetime(ahora_dt).tz_convert('UTC') if pd.to_datetime(ahora_dt).tzinfo else pd.to_datetime(ahora_dt).tz_localize('UTC')
        minutos = int((ahora_utc - hora_entrada_utc).total_seconds() / 60)
        
        hash_anterior = fichajes[0].get('hash_anterior', '')
        data_to_hash = f"FICHAJE|OUT|{empleado_id}|{fichajes[0]['hora_entrada']}|{ahora}|{hash_anterior}"
        hash_actual = hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest().upper()
        
        client.table("personal_fichajes").update({
            "hora_salida": ahora,
            "minutos_trabajados": minutos,
            "hash_actual": hash_actual
        }).eq("id", fichaje_id).execute()
        
        limpiar_cache_personal()
        return True, f"✅ Salida registrada para {nombre_empleado} a las {ahora_dt.strftime('%H:%M')}"
        
    else:
        res_last = get_ultimo_hash(client)
        hash_anterior = res_last.data[0].get("hash_actual", "") if res_last.data else ""
        data_to_hash = f"FICHAJE|IN|{empleado_id}|{ahora}|{hash_anterior}"
        hash_actual = hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest().upper()
        
        client.table("personal_fichajes").insert({
            "empleado_id": empleado_id,
            "fecha": hoy,
            "hora_entrada": ahora,
            "hash_anterior": hash_anterior,
            "hash_actual": hash_actual
        }).execute()
        
        limpiar_cache_personal()
        return True, f"✅ Entrada registrada para {nombre_empleado} a las {ahora_dt.strftime('%H:%M')}"

def render_pestana_personal(client: SyncPostgrestClient):
    st.header("⏱️ Control de Personal y Horarios")

    def es_festivo(d: date):
        fijos = {
            (1, 1): "🎊 Año Nuevo", (1, 6): "🎁 Reyes", (2, 2): "🕯️ Candelaria (TF)",
            (5, 1): "👷 Trabajador", (5, 3): "✝️ Cruz (S/C)",
            (5, 30): "🇮🇨 Día Canarias", (8, 15): "⛪ Asunción",
            (10, 12): "🇪🇸 Hispanidad", (11, 1): "🕯️ Todos Santos",
            (12, 6): "📜 Constitución", (12, 8): "⛪ Inmaculada", (12, 25): "🎄 Navidad"
        }
        variables = {
            date(2024, 2, 13): "🎭 Carnaval (S/C)", date(2024, 3, 28): "✝️ Jueves Santo", date(2024, 3, 29): "✝️ Viernes Santo",
            date(2025, 3, 4): "🎭 Carnaval (S/C)", date(2025, 4, 17): "✝️ Jueves Santo", date(2025, 4, 18): "✝️ Viernes Santo",
            date(2026, 2, 17): "🎭 Carnaval (S/C)", date(2026, 4, 2): "✝️ Jueves Santo", date(2026, 4, 3): "✝️ Viernes Santo",
            date(2027, 2, 9): "🎭 Carnaval (S/C)", date(2027, 3, 25): "✝️ Jueves Santo", date(2027, 3, 26): "✝️ Viernes Santo"
        }
        if (d.month, d.day) in fijos: return fijos[(d.month, d.day)]
        if d in variables: return variables[d]
        return ""

    try:
        empleados_res = get_empleados_activos(client)
        empleados = empleados_res.data
    except Exception as e:
        st.error(f"Error al cargar empleados: {e}")
        empleados = []

    if not empleados:
        st.warning("No hay empleados registrados.")
    else:
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
                        ahoy = date.today().isoformat()
                        res_bl = get_agenda_bloqueos_futuros(client, ahoy)
                        if res_bl.data:
                            for b in res_bl.data:
                                if b['fecha'] == ahoy and b.get('bloquea_agenda'):
                                    emp_af = b.get('empleado_afectado', '')
                                    if (emp_af == 'Todas' or emp_af == emp_sel['nombre']) and b.get('hora_inicio') == '00:00' and b.get('hora_fin') == '23:59':
                                        st.error(f"⛔ **Acceso Denegado:** No puedes fichar hoy porque estás marcado/a con una excepción de día completo ({b.get('titulo')}).")
                                        st.stop()
                        
                        ahora_dt = datetime.now(tz_canarias)
                        success, msg = registrar_fichaje(client, emp_sel['id'], nombre_sel, ahora_dt)
                        if success:
                            st.success(msg)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(msg)
                            st.stop()
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

            cuadrantes_res = get_cuadrantes_rango(client, start_aligned.isoformat(), end_aligned.isoformat())
            df_cuadrante = pd.DataFrame(cuadrantes_res.data)
            
            dias_es = {0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue", 4: "Vie", 5: "Sáb", 6: "Dom"}
            
            if not df_cuadrante.empty:
                df_emp = pd.DataFrame(empleados)[['id', 'nombre']]
                df_cuadrante = df_cuadrante.merge(df_emp, left_on='empleado_id', right_on='id')
                df_cuadrante['Fecha_Str'] = pd.to_datetime(df_cuadrante['fecha']).apply(lambda x: f"{dias_es[x.weekday()]} {x.strftime('%d/%m')}" + (f" {es_festivo(x.date())}" if es_festivo(x.date()) else ""))
                df_pivot = df_cuadrante.pivot_table(index='nombre', columns='Fecha_Str', values='turno', aggfunc='first')
            else:
                df_pivot = pd.DataFrame()
                
            curr_w = start_aligned
            while curr_w <= end_aligned:
                w_end = curr_w + timedelta(days=6)
                st.markdown(f"<h5 style='margin-bottom: 5px; color: #005275; margin-top: 10px;'>Semana del {curr_w.strftime('%d/%m/%Y')} al {w_end.strftime('%d/%m/%Y')}</h5>", unsafe_allow_html=True)
                
                fechas_semana = [curr_w + timedelta(days=x) for x in range(7)]
                cols_semana = [f"{dias_es[d.weekday()]} {d.strftime('%d/%m')}" + (f" {es_festivo(d)}" if es_festivo(d) else "") for d in fechas_semana]
                
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
        
        seccion_admin = st.radio("Sección Personal:", ["Empleados", "Gestión de Cuadrante (Editable)", "Ver Fichajes", "❌ Ausencias y Excepciones"], horizontal=True, label_visibility="collapsed")
        
        if seccion_admin == "Empleados":
            st.markdown("Añadir nuevo empleado:")
            with st.form("form_nuevo_empleado"):
                c1, c2 = st.columns(2)
                nuevo_nom = c1.text_input("Nombre")
                nuevo_pin = c2.text_input("PIN (4 dígitos)", max_chars=4)
                if st.form_submit_button("Crear Empleado"):
                    if nuevo_nom and len(nuevo_pin) == 4:
                        client.table("personal_empleados").insert({"nombre": nuevo_nom, "pin_fichaje": nuevo_pin, "activo": True}).execute()
                        st.success("Empleado creado")
                        limpiar_cache_personal()
                        st.rerun()
                    else:
                        st.error("El nombre y un PIN de 4 dígitos son obligatorios.")
                        
            st.markdown("Lista de empleados:")
            st.dataframe(pd.DataFrame(empleados), hide_index=True)

        elif seccion_admin == "Gestión de Cuadrante (Editable)":
            st.markdown("#### 🗓️ Editor Visual de Cuadrantes")
            st.info("Selecciona el rango de fechas. Edita los turnos haciendo **doble clic en las celdas**. Las tablas se dividen por semanas para mayor comodidad. Al terminar, pulsa 'Guardar Todo el Cuadrante'.")
            
            c_e1, c_e2 = st.columns(2)
            from datetime import date, timedelta
            hoy = date.today()
            with c_e1: f_ini_ed = st.date_input("Editor Desde:", value=hoy - timedelta(days=hoy.weekday()), key="e_ini")
            with c_e2: f_fin_ed = st.date_input("Editor Hasta:", value=f_ini_ed + timedelta(days=27), key="e_fin")
            
            if empleados:
                start_aligned_ed = f_ini_ed - timedelta(days=f_ini_ed.weekday())
                end_aligned_ed = f_fin_ed + timedelta(days=6 - f_fin_ed.weekday())
                dias_es = {0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue", 4: "Vie", 5: "Sáb", 6: "Dom"}
                
                # Cargar datos existentes
                res_q = get_cuadrantes_rango(client, start_aligned_ed.isoformat(), end_aligned_ed.isoformat())
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
                        fest = es_festivo(d)
                        col_name = f"{dias_es[d.weekday()]} {d.strftime('%d/%m')}"
                        if fest: col_name += f" ({fest})"
                        col_config[d.isoformat()] = st.column_config.TextColumn(col_name)
                        
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
                    st.success("¡Cuadrante guardado exitosamente!"); time.sleep(1); limpiar_cache_personal(); st.rerun()
        
        elif seccion_admin == "Ver Fichajes":
            st.markdown("Historial de fichajes:")
            st.warning("🔒 **REGISTRO INALTERABLE**: Según la normativa laboral vigente, los fichajes están sellados con criptografía SHA-256 (Hash) y vinculados a la hora del servidor. No se pueden modificar ni eliminar.")
            try:
                fichajes_totales = get_fichajes_totales(client)
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
                    
                    # Columnas de seguridad legal
                    df_fich['🔒 Estado'] = "🔒 Sellado"
                    if 'hash_actual' not in df_fich.columns: df_fich['hash_actual'] = ""
                    df_fich['Firma Hash'] = df_fich['hash_actual'].apply(lambda x: str(x)[:8] + "..." if pd.notna(x) and str(x).strip() != "" else "No encriptado")
                    
                    cols = ['🔒 Estado', 'nombre', 'fecha', 'hora_entrada', 'hora_salida', 'minutos_trabajados', 'Firma Hash']
                    st.dataframe(df_fich[cols], use_container_width=True, hide_index=True)
                else:
                    st.info("No hay fichajes registrados.")
            except Exception as e:
                pass

        elif seccion_admin == "❌ Ausencias y Excepciones":
            st.markdown("#### 🌴 Gestión de Ausencias, Vacaciones y Cierres")
            st.info("💡 Añade excepciones al cuadrante sin borrar la planificación base. Estas excepciones generarán un **Bloqueo en la Agenda** automáticamente para que no entren citas en esos tramos.")
            
            c_aus1, c_aus2 = st.columns([1, 1.5], gap="large")
            
            with c_aus1:
                tipo_ausencia = st.selectbox("Tipo de Excepción", ["🌴 Vacaciones (Días completos)", "🏢 Cierre de Empresa (Festivos/Obras)", "⏱️ Ausencia Parcial / Jornada Reducida", "🔄 Cambio de Turno Rápido"])
                
                with st.form("form_ausencia", clear_on_submit=True):
                    if tipo_ausencia == "🌴 Vacaciones (Días completos)":
                        emp_aus = st.selectbox("Empleado", [e['nombre'] for e in empleados])
                        c_vd1, c_vd2 = st.columns(2)
                        with c_vd1: d_ini = st.date_input("Desde el día")
                        with c_vd2: d_fin = st.date_input("Hasta el día (inclusive)")
                        btn = st.form_submit_button("Registrar Vacaciones", type="primary", use_container_width=True)
                        
                        if btn:
                            delta = d_fin - d_ini
                            inserts = []
                            for i in range(delta.days + 1):
                                dia_bloqueo = d_ini + timedelta(days=i)
                                inserts.append({
                                    "fecha": str(dia_bloqueo), "hora_inicio": "00:00", "hora_fin": "23:59",
                                    "titulo": "🌴 Vacaciones", "empleado_afectado": emp_aus, "bloquea_agenda": True
                                })
                            if inserts:
                                client.table("agenda_bloqueos").insert(inserts).execute()
                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                st.success("Vacaciones registradas y agenda bloqueada."); time.sleep(1); limpiar_cache_personal(); st.rerun()
                                
                    elif tipo_ausencia == "🏢 Cierre de Empresa (Festivos/Obras)":
                        motivo = st.text_input("Motivo (Ej: Festivo Local, Obras...)")
                        c_vd1, c_vd2 = st.columns(2)
                        with c_vd1: d_ini = st.date_input("Desde el día")
                        with c_vd2: d_fin = st.date_input("Hasta el día (inclusive)")
                        btn = st.form_submit_button("Registrar Cierre", type="primary", use_container_width=True)
                        
                        if btn and motivo:
                            delta = d_fin - d_ini
                            inserts = []
                            for i in range(delta.days + 1):
                                dia_bloqueo = d_ini + timedelta(days=i)
                                inserts.append({
                                    "fecha": str(dia_bloqueo), "hora_inicio": "00:00", "hora_fin": "23:59",
                                    "titulo": f"🏢 {motivo}", "empleado_afectado": "Todas", "bloquea_agenda": True
                                })
                            if inserts:
                                client.table("agenda_bloqueos").insert(inserts).execute()
                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                st.success("Cierre registrado y agenda bloqueada."); time.sleep(1); limpiar_cache_personal(); st.rerun()
                        elif btn:
                            st.warning("Por favor, indica un motivo.")
                            
                    elif tipo_ausencia == "⏱️ Ausencia Parcial / Jornada Reducida":
                        emp_aus = st.selectbox("Empleado", [e['nombre'] for e in empleados])
                        d_aus = st.date_input("Fecha")
                        c_vt1, c_vt2 = st.columns(2)
                        with c_vt1: t_ini = st.time_input("Inicio de la ausencia")
                        with c_vt2: t_fin = st.time_input("Fin de la ausencia")
                        motivo = st.text_input("Motivo (Ej: Médico, Jornada reducida)")
                        btn = st.form_submit_button("Registrar Ausencia Parcial", type="primary", use_container_width=True)
                        
                        if btn and motivo:
                            client.table("agenda_bloqueos").insert({
                                "fecha": str(d_aus), "hora_inicio": t_ini.strftime("%H:%M"), "hora_fin": t_fin.strftime("%H:%M"),
                                "titulo": f"⏱️ {motivo}", "empleado_afectado": emp_aus, "bloquea_agenda": True
                            }).execute()
                            st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                            st.success("Ausencia registrada y agenda bloqueada."); time.sleep(1); limpiar_cache_personal(); st.rerun()
                        elif btn:
                            st.warning("Por favor, indica un motivo.")
                            
                    elif tipo_ausencia == "🔄 Cambio de Turno Rápido":
                        st.info("Sustituye el turno de un empleado para uno o varios días sin tener que buscarlo en el Cuadrante Visual.")
                        emp_aus = st.selectbox("Empleado", [e['nombre'] for e in empleados])
                        
                        c_ct1, c_ct2 = st.columns(2)
                        with c_ct1: d_ini_ct = st.date_input("Desde el día", key="ct_ini")
                        with c_ct2: d_fin_ct = st.date_input("Hasta el día (inclusive)", key="ct_fin")
                        
                        nuevo_turno = st.text_input("Nuevo Turno (Ej: 09:00 - 15:00, o Libre)")
                        btn = st.form_submit_button("Actualizar Turno", type="primary", use_container_width=True)
                        
                        if btn and nuevo_turno:
                            if d_fin_ct >= d_ini_ct:
                                emp_id = next(e['id'] for e in empleados if e['nombre'] == emp_aus)
                                delta = d_fin_ct - d_ini_ct
                                
                                client.table("personal_cuadrantes").delete().eq("empleado_id", emp_id).gte("fecha", str(d_ini_ct)).lte("fecha", str(d_fin_ct)).execute()
                                
                                inserts = [{"empleado_id": emp_id, "fecha": str(d_ini_ct + timedelta(days=i)), "turno": nuevo_turno} for i in range(delta.days + 1)]
                                if inserts:
                                    client.table("personal_cuadrantes").insert(inserts).execute()
                                    
                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                st.success(f"Turno(s) de {emp_aus} actualizado(s) correctamente."); time.sleep(1.5); limpiar_cache_personal(); st.rerun()
                            else:
                                st.error("La fecha de fin no puede ser anterior a la de inicio.")
                        elif btn:
                            st.warning("Por favor, escribe el nuevo turno.")
                            
            with c_aus2:
                st.markdown("##### 📅 Excepciones y Bloqueos Activos")
                hoy_str = str(date.today())
                try:
                    res_bl = get_agenda_bloqueos_futuros(client, hoy_str)
                    if res_bl.data:
                        df_bl = pd.DataFrame(res_bl.data)
                        
                        # Filtramos para mostrar SÓLO las creadas desde este panel (Vacaciones, Cierres, Ausencias)
                        df_bl = df_bl[df_bl['titulo'].str.contains('🌴|🏢|⏱️', regex=True, na=False)]
                        
                        if not df_bl.empty:
                            df_bl['Fecha'] = pd.to_datetime(df_bl['fecha']).dt.strftime('%d/%m/%Y')
                            df_bl_vista = df_bl[['id', 'Fecha', 'hora_inicio', 'hora_fin', 'titulo', 'empleado_afectado']].copy()
                            df_bl_vista.insert(0, "Borrar", False)
                            
                            ed_bl = st.data_editor(
                                df_bl_vista, hide_index=True, use_container_width=True, height=350,
                                column_config={
                                    "Borrar": st.column_config.CheckboxColumn("🗑️", width="small"),
                                    "id": None, "hora_inicio": "Desde", "hora_fin": "Hasta", "titulo": "Asunto / Motivo", "empleado_afectado": "Afecta a"
                                }, key="ed_ausencias_bloqueos"
                            )
                            if st.button("🗑️ Eliminar Excepciones Seleccionadas", type="primary"):
                                for _, r in ed_bl[ed_bl["Borrar"] == True].iterrows():
                                    client.table("agenda_bloqueos").delete().eq("id", r['id']).execute()
                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                st.success("Excepciones eliminadas. La agenda vuelve a estar libre en esos tramos."); time.sleep(1); limpiar_cache_personal(); st.rerun()
                        else:
                            st.info("No hay ausencias, vacaciones ni bloqueos de personal futuros registrados.")
                    else:
                        st.info("No hay ausencias, vacaciones ni bloqueos de personal futuros registrados.")
                except Exception as e:
                    pass
