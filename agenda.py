import streamlit as st
import pandas as pd
from datetime import date, timedelta
import time
import urllib.parse

@st.cache_data(show_spinner=False, ttl=15)
def get_masc_ag_cached(_client, v):
    _all = []
    _off = 0
    while True:
        _r = _client.table("mascotas").select("id, nombre, clientes(nombre_dueno, telefono)").range(_off, _off + 999).execute()
        if _r.data:
            _all.extend(_r.data)
            if len(_r.data) < 1000: break
            _off += 1000
        else: break
    return _all

@st.cache_data(show_spinner=False, ttl=15)
def get_citas_ag_cached(_client, v):
    _all = []
    _off = 0
    while True:
        _r = _client.table("citas").select("id, fecha_hora, servicio, duracion_minutos, observaciones, mascotas(id, nombre, clientes(nombre_dueno, telefono, direccion, servicio_domicilio))").order("fecha_hora", desc=False).range(_off, _off + 999).execute()
        if _r.data:
            _all.extend(_r.data)
            if len(_r.data) < 1000: break
            _off += 1000
        else: break
    return _all

@st.cache_data(show_spinner=False, ttl=15)
def get_masc_info_cached(_client, v, mid):
    return _client.table("mascotas").select("*").eq("id", mid).execute().data

@st.cache_data(show_spinner=False, ttl=15)
def get_alertas_m_ag_cached(_client, v):
    _all = []
    _off = 0
    while True:
        _r = _client.table("mascotas").select("id, nombre, historial_trabajos, clientes(nombre_dueno, telefono, metodo_contacto)").range(_off, _off + 999).execute()
        if _r.data:
            _all.extend(_r.data)
            if len(_r.data) < 1000: break
            _off += 1000
        else: break
    return _all

@st.cache_data(show_spinner=False, ttl=15)
def get_manana_ag_cached(_client, v, m_ini, m_fin):
    return _client.table("citas").select("fecha_hora, servicio, mascotas(nombre, clientes(nombre_dueno, telefono, metodo_contacto, direccion, servicio_domicilio))").gte("fecha_hora", m_ini).lte("fecha_hora", m_fin).execute().data

@st.cache_data(show_spinner=False, ttl=15)
def get_futuras_ag_cached(_client, v, h_str):
    return _client.table("citas").select("mascotas_id, servicio").gte("fecha_hora", h_str).execute().data

@st.cache_data(show_spinner=False, ttl=15)
def get_canc_ag_cached(_client, v):
    return _client.table("citas").select("fecha_hora, servicio, mascotas(nombre, clientes(nombre_dueno, telefono))").like("servicio", "%[ESTADO: Cancelada]%").order("fecha_hora", desc=True).limit(200).execute().data

@st.cache_data(show_spinner=False, ttl=15)
def get_sin_hist_ag_cached(_client, v, h_str):
    return _client.table("citas").select("fecha_hora, servicio, mascotas(id, nombre, historial_trabajos)").lt("fecha_hora", h_str).like("servicio", "%[ESTADO: Confirmada]%").execute().data

def render_pestana_agenda(client):
    if 'llave_agenda_cita' not in st.session_state: st.session_state.llave_agenda_cita = 0

    st.markdown("<h3 style='margin-bottom: 5px;'>📅 Agenda Animalarium</h3>", unsafe_allow_html=True)

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

    def generar_enlace_wa(telefono, mensaje):
        tel_limpio = ''.join(filter(str.isdigit, str(telefono)))
        if not tel_limpio: return None
        if len(tel_limpio) == 9 and not tel_limpio.startswith('34'): tel_limpio = '34' + tel_limpio
        return f"https://wa.me/{tel_limpio}?text={urllib.parse.quote(mensaje)}"
    
    # --- DATOS COMUNES PARA TODAS LAS SUB-PESTAÑAS DE AGENDA ---
    all_mascotas = get_masc_ag_cached(client, st.session_state.get('db_version', 0))

    dict_mascotas = {}
    if all_mascotas:
        for m in all_mascotas:
            dueno = m['clientes']['nombre_dueno'] if m.get('clientes') else "Desconocido"
            telefono = m['clientes']['telefono'] if m.get('clientes') and m['clientes'].get('telefono') else "Sin teléfono"
            dict_mascotas[f"🐾 {m['nombre']} (De: {dueno} - 📱 {telefono})"] = m['id']
            
    all_citas = get_citas_ag_cached(client, st.session_state.get('db_version', 0))

    class DummyRes: pass
    res_citas = DummyRes()
    res_citas.data = all_citas
    
    # --- DATOS COMUNES ---
    try:
        emp_res = client.table("personal_empleados").select("id, nombre").eq("activo", True).execute()
        empleados_lista = [e['nombre'] for e in emp_res.data] if emp_res.data else []
    except: empleados_lista = []
    
    try:
        serv_res = client.table("productos").select("nombre, precio_pvp, precio_base").eq("categoria", "Servicio").order("nombre").execute()
        if serv_res.data:
            servicios_lista = [s['nombre'] for s in serv_res.data] + ["Otro"]
            precios_servicios = {s['nombre']: float(s.get('precio_pvp') or s.get('precio_base') or 0.0) for s in serv_res.data}
        else:
            servicios_lista = ["Peluquería", "Otro"]
            precios_servicios = {}
    except: 
        servicios_lista = ["Otro"]
        precios_servicios = {}

    ESTADOS_CITA = ["Confirmada", "Cancelada", "Cambio de cita", "Servicio de recogida pendiente", "Servicio de recogida confirmado", "Cambio (día antes)", "Cambio (mismo día)", "Oferta / Descuento", "Pendiente"]
    EMOJIS_ESTADO = {
        "Confirmada": "🟢", "Cancelada": "💖", "Cambio de cita": "🔵", 
        "Servicio de recogida": "🟣", "Servicio de recogida pendiente": "🟣🟡", "Servicio de recogida confirmado": "🟣🟢",
        "Cambio (día antes)": "🟠", 
        "Cambio (mismo día)": "⚪", "Oferta / Descuento": "🟩", "Pendiente": "🟡"
    }

    def parse_cita_estado(servicio_raw):
        estado = "Confirmada"
        import re
        m_est = re.search(r'\[ESTADO:\s*(.*?)\]', servicio_raw)
        if m_est:
            estado = m_est.group(1).strip()
            # Migración automática de estados antiguos
            if estado == "Servicio de recogida":
                estado = "Servicio de recogida pendiente"
            servicio_raw = re.sub(r'\[ESTADO:\s*.*?\]\s*', '', servicio_raw)
            
        emp = "Sin Asignar"
        for e in empleados_lista:
            if f"({e})" in servicio_raw:
                emp = e; servicio_raw = servicio_raw.replace(f"({e})", "").replace("  ", " ").strip(); break
        return estado, servicio_raw.strip(), emp
    
    # --- PESTAÑAS DE VISTAS ---
    sub_agenda, sub_diario, sub_semanal, sub_recordatorios, sub_cancelaciones, sub_sin_historial = st.tabs(["📝 Gestión de Citas", "🕒 Vista Diaria", "🗓️ Vista Semanal", "🔔 Recordatorios", "🚫 Cancelaciones", "🚨 Sin Historial"])
    
    with sub_agenda:
        c_agenda1, c_agenda2 = st.columns([1, 2.5], gap="large")
        
        with c_agenda1:
            with st.container(border=True):
                st.markdown("#### ➕ Nueva Cita")
                
                crear_rapido = st.toggle("🐾 Mascota no registrada (Crear ficha rápida)", key=f"ag_cr_{st.session_state.llave_agenda_cita}")
                mascota_sel = None
                n_mascota, n_cliente, n_tel = "", "", ""
                
                if crear_rapido:
                    st.markdown("<p style='font-size: 13px; color: gray; margin-top:-10px;'>Se creará una ficha básica automáticamente en Clientes.</p>", unsafe_allow_html=True)
                    c_nx1, c_nx2, c_nx3 = st.columns([1.5, 1.5, 1])
                    with c_nx1: n_mascota = st.text_input("Nombre Mascota *", key=f"ag_nmasc_{st.session_state.llave_agenda_cita}")
                    with c_nx2: n_cliente = st.text_input("Dueño *", key=f"ag_ncli_{st.session_state.llave_agenda_cita}")
                    with c_nx3: n_tel = st.text_input("Teléfono", key=f"ag_ntel_{st.session_state.llave_agenda_cita}")
                else:
                    mascota_sel = st.selectbox("Selecciona Mascota *", list(dict_mascotas.keys()), index=None, key=f"ag_masc_sel_{st.session_state.llave_agenda_cita}")
                
                pref_actual = "Cualquiera"
                dur_media = 60
                if mascota_sel:
                    m_id_sel = dict_mascotas[mascota_sel]
                    res_m_info = client.table("mascotas").select("observaciones, historial_trabajos").eq("id", m_id_sel).execute()
                    if res_m_info.data:
                        obs = res_m_info.data[0].get('observaciones', '')
                        import re
                        m_pref = re.search(r'\[Pref:\s*(.*?)\]', str(obs))
                        if m_pref: pref_actual = m_pref.group(1)
                        
                        historial = res_m_info.data[0].get('historial_trabajos', [])
                        duraciones = [t['Duración (min)'] for t in historial if isinstance(t, dict) and isinstance(t.get('Duración (min)'), (int, float))]
                        if duraciones: 
                            dur_media = int(sum(duraciones) / len(duraciones))
                            st.info(f"⏱️ **Info de la mascota:** Tiempo medio de {dur_media} min | Peluquero/a pref: {pref_actual}")
                        else:
                            st.info(f"⏱️ **Info de la mascota:** Sin historial (60 min por defecto) | Peluquero/a pref: {pref_actual}")
                        
                fecha_c = st.date_input("Fecha *", value=date.today(), key=f"ag_fec_{st.session_state.llave_agenda_cita}")
                duracion_c = st.number_input("Duración estimada (minutos) *", min_value=5, max_value=300, value=dur_media, step=5, key=f"ag_dur_{st.session_state.llave_agenda_cita}")
                
                opciones_emp = ["Cualquiera"] + empleados_lista
                def_index = opciones_emp.index(pref_actual) if pref_actual in opciones_emp else 0
                f_emp = st.selectbox("Peluquera/o Preferido:", opciones_emp, index=def_index, key=f"ag_emp_{st.session_state.llave_agenda_cita}")
                
                # Buscador inteligente de huecos cruzado con el preferido
                res_turnos = client.table("personal_cuadrantes").select("empleado_id, turno, personal_empleados(nombre)").eq("fecha", str(fecha_c)).execute()
                turnos_dict = {}
                if res_turnos.data:
                    for t in res_turnos.data:
                        if t.get('personal_empleados'): turnos_dict[t['personal_empleados']['nombre']] = t['turno'].lower()
                            
                empleados_a_revisar = [f_emp] if f_emp != "Cualquiera" else empleados_lista
                huecos_obj = []
                
                citas_dia = []
                if res_citas.data:
                    for c in res_citas.data:
                        try:
                            dt_c = pd.to_datetime(c['fecha_hora'])
                            if dt_c.tzinfo: dt_c = dt_c.tz_localize(None)
                            if dt_c.date() == fecha_c: citas_dia.append(c)
                        except: pass
                
                for emp_nombre in empleados_a_revisar:
                    turno_str = turnos_dict.get(emp_nombre, "")
                    if not turno_str or "libre" in turno_str or "vacaciones" in turno_str: continue
                        
                    import re
                    times = re.findall(r'(\d{1,2}:\d{2})', turno_str)
                    if len(times) >= 2:
                        h_ini = pd.to_datetime(f"{fecha_c} {times[0]}")
                        h_fin = pd.to_datetime(f"{fecha_c} {times[1]}")
                    else:
                        if fecha_c.weekday() < 5: # Lunes a Viernes
                            h_ini = pd.to_datetime(f"{fecha_c} 09:00")
                            h_fin = pd.to_datetime(f"{fecha_c} 21:00")
                        else: # Sábados y Domingos
                            h_ini = pd.to_datetime(f"{fecha_c} 10:00")
                            h_fin = pd.to_datetime(f"{fecha_c} 14:00")
                        
                    for h in range(0, 24):
                        for m in range(0, 60, 5):
                            dt_ini = pd.to_datetime(f"{fecha_c} {h:02d}:{m:02d}")
                            if dt_ini < h_ini: continue
                            dt_fin = dt_ini + pd.Timedelta(minutes=duracion_c)
                            if dt_fin > h_fin: continue
                            
                            solapa = False
                            for c in citas_dia:
                                if "[ESTADO: Cancelada]" in c.get('servicio', '') or "[ESTADO: Cambio" in c.get('servicio', ''): continue
                                c_ini = pd.to_datetime(c['fecha_hora'])
                                if c_ini.tzinfo: c_ini = c_ini.tz_localize(None)
                                c_fin = c_ini + pd.Timedelta(minutes=c.get('duracion_minutos') or 60)
                                if dt_ini < c_fin and dt_fin > c_ini:
                                    s = c.get('servicio', '')
                                    assigned_e = None
                                    for e in empleados_lista:
                                        if f"({e})" in s: assigned_e = e; break
                                    if assigned_e == emp_nombre or assigned_e is None:
                                        solapa = True; break
                            if not solapa: huecos_obj.append({"dt": dt_ini, "hora": f"{h:02d}:{m:02d}", "emp": emp_nombre})
                
                huecos_obj.sort(key=lambda x: x["dt"])
                huecos_formateados = [f"{x['hora']} (Con {x['emp']})" for x in huecos_obj]
                huecos_formateados.append("Asignación Manual")
                
                if len(huecos_formateados) == 1: st.warning("No hay huecos disponibles en el cuadrante.")
                f_hora_sel = st.selectbox("Hora recomendada:", huecos_formateados, key=f"ag_hsel_{st.session_state.llave_agenda_cita}")
                    
                hora_manual = None
                solapa_manual = False
                motivo_solape = ""
                motivo_extra = ""
                
                if f_hora_sel == "Asignación Manual":
                    hora_manual = st.time_input("Hora de Inicio *", key=f"ag_hman_{st.session_state.llave_agenda_cita}")
                    if hora_manual:
                        dt_ini_man = pd.to_datetime(f"{fecha_c} {hora_manual.strftime('%H:%M')}")
                        dt_fin_man = dt_ini_man + pd.Timedelta(minutes=duracion_c)
                        for c in citas_dia:
                            if "[ESTADO: Cancelada]" in c.get('servicio', '') or "[ESTADO: Cambio" in c.get('servicio', ''): continue
                            c_ini = pd.to_datetime(c['fecha_hora'])
                            if c_ini.tzinfo: c_ini = c_ini.tz_localize(None)
                            c_fin = c_ini + pd.Timedelta(minutes=c.get('duracion_minutos') or 60)
                            if dt_ini_man < c_fin and dt_fin_man > c_ini:
                                s = c.get('servicio', '')
                                assigned_e = None
                                for e in empleados_lista:
                                    if f"({e})" in s: assigned_e = e; break
                                if f_emp != "Cualquiera":
                                    if assigned_e == f_emp or assigned_e is None: solapa_manual = True; break
                                else:
                                    solapa_manual = True; break
                        
                        if solapa_manual:
                            st.warning("⚠️ La hora seleccionada ya está ocupada o hay citas sin asignar en esa franja.")
                            motivo_solape = st.selectbox("Motivo para forzar la cita: *", ["", "Tenemos otro peluquero disponible", "Se va a ayudar con la peluquería", "Se puede hacer a la vez", "Otro motivo"], key=f"ag_msol_{st.session_state.llave_agenda_cita}")
                            if motivo_solape == "Otro motivo":
                                motivo_extra = st.text_input("Especificar otro motivo: *", key=f"ag_mext_{st.session_state.llave_agenda_cita}")
                
                servicio_sel = st.selectbox("Servicio *", servicios_lista, key=f"ag_serv_{st.session_state.llave_agenda_cita}")
                f_obs = st.text_input("📝 Observaciones / Petición (Opcional)", key=f"ag_obs_{st.session_state.llave_agenda_cita}")
                
                if st.button("Guardar Cita", type="primary", use_container_width=True):
                    m_id_final = None
                    
                    if solapa_manual and (not motivo_solape or (motivo_solape == "Otro motivo" and not motivo_extra)):
                        st.error("Debes indicar un motivo para forzar la cita en una hora ocupada.")
                    else:
                        if crear_rapido:
                            if n_mascota and n_cliente:
                                res_cli = client.table("clientes").insert({
                                    "nombre_dueno": n_cliente, "telefono": n_tel, "puntos": 0
                                }).execute()
                                if res_cli.data:
                                    res_m = client.table("mascotas").insert({
                                        "cliente_id": res_cli.data[0]['id'], "nombre": n_mascota
                                    }).execute()
                                    if res_m.data: m_id_final = res_m.data[0]['id']
                            else:
                                st.error("Debes indicar al menos el nombre de la mascota y del dueño para crear la ficha.")
                        else:
                            if mascota_sel:
                                m_id_final = dict_mascotas[mascota_sel]
                            else:
                                st.error("Debes seleccionar una mascota.")
                                
                        if m_id_final:
                            if f_hora_sel == "Asignación Manual":
                                hora_final_str = hora_manual.strftime('%H:%M')
                                emp_final = f_emp if f_emp != "Cualquiera" else ""
                            else:
                                hora_final_str = f_hora_sel.split(" (")[0]
                                emp_final = f_hora_sel.split("(Con ")[1].replace(")", "")
                                
                            servicio_final = f"{servicio_sel} ({emp_final})" if emp_final else servicio_sel
                            
                            if solapa_manual:
                                motivo_final = motivo_extra if motivo_solape == "Otro motivo" else motivo_solape
                                servicio_final += f" [Forzado: {motivo_final}]"
                                
                            servicio_final = f"[ESTADO: Pendiente] {servicio_final}"
                            fecha_hora_str = f"{fecha_c} {hora_final_str}"
                            
                            client.table("citas").insert({
                                "mascotas_id": m_id_final, "fecha_hora": fecha_hora_str,
                                "servicio": servicio_final, "duracion_minutos": int(duracion_c),
                                "observaciones": str(f_obs)
                            }).execute()
                            st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                            st.session_state.llave_agenda_cita += 1
                            st.success("Cita agendada."); time.sleep(1); st.rerun()

        with c_agenda2:
            st.markdown("#### 🗓️ Directorio de Citas (Editable)")
            mostrar_pasadas = st.toggle("🕰️ Mostrar citas pasadas", value=False)
            
            if res_citas.data:
                citas_formateadas = []
                hoy_fecha = date.today()
                for c in res_citas.data:
                    mascota_info = c.get('mascotas', {})
                    cliente_info = mascota_info.get('clientes', {}) if mascota_info else {}
                    dur = c.get('duracion_minutos') if c.get('duracion_minutos') is not None else 60
                    
                    dt_obj = pd.to_datetime(c['fecha_hora'])
                    
                    estado_c, s_clean, assigned_e = parse_cita_estado(c.get('servicio', ''))
                    
                    emoji_estado = EMOJIS_ESTADO.get(estado_c, "🟢")
                    estado_con_emoji = f"{emoji_estado} {estado_c}"
                            
                    msg_cita = f"¡Hola {cliente_info.get('nombre_dueno', '')}! 🐾 Te escribimos de Animalarium para recordarte la cita de {mascota_info.get('nombre', '')} el día {dt_obj.strftime('%d/%m/%Y')} a las {dt_obj.strftime('%H:%M')}. Por favor, confírmanos tu asistencia. ¡Te esperamos! ✂️"
                    url_wa = generar_enlace_wa(cliente_info.get('telefono', ''), msg_cita)

                    citas_formateadas.append({
                        "Ver Ficha": False,
                        "mascota_id": mascota_info.get('id'),
                        "Borrar": False,
                        "id": c['id'],
                        "Día": dt_obj.strftime('%d/%m/%Y'),
                        "Hora": dt_obj.strftime('%H:%M'),
                        "Estado": estado_con_emoji,
                        "Duración (min)": dur,
                        "Peluquero/a": assigned_e,
                        "Servicio": s_clean,
                        "Mascota": mascota_info.get('nombre', 'N/A'),
                        "Dueño": cliente_info.get('nombre_dueno', 'N/A'),
                        "Teléfono": cliente_info.get('telefono', 'N/A'),
                        "Observaciones": c.get('observaciones', ''),
                        "WhatsApp": url_wa,
                        "Es_Pasada": dt_obj.date() < hoy_fecha
                    })
                    
                df_citas = pd.DataFrame(citas_formateadas)
                
                if not mostrar_pasadas:
                    df_citas = df_citas[df_citas["Es_Pasada"] == False]
                
                if df_citas.empty:
                    st.info("No hay citas próximas agendadas. Activa 'Mostrar citas pasadas' para ver el historial antiguo.")
                else:
                    # Evitar que Streamlit oculte servicios antiguos que ya no coinciden con el catálogo
                    servicios_en_agenda = [s for s in df_citas["Servicio"].dropna().unique().tolist() if str(s).strip() != ""]
                    opciones_seguras_ag = servicios_lista + [s for s in servicios_en_agenda if s not in servicios_lista]

                    ed_citas = st.data_editor(
                        df_citas[['Ver Ficha', 'Borrar', 'id', 'mascota_id', 'Día', 'Hora', 'Estado', 'Duración (min)', 'Peluquero/a', 'Servicio', 'Observaciones', 'Mascota', 'Dueño', 'Teléfono', 'WhatsApp']],
                        use_container_width=True, hide_index=True, num_rows="dynamic", key="ed_citas_ag", height=400,
                        column_order=["Ver Ficha", "Borrar", "Día", "Hora", "Estado", "Peluquero/a", "Mascota", "Servicio", "Observaciones", "Duración (min)", "Dueño", "Teléfono", "WhatsApp"],
                        column_config={
                            "Ver Ficha": st.column_config.CheckboxColumn("👁️ Ver Ficha", default=False),
                            "Borrar": st.column_config.CheckboxColumn("🗑️ Borrar", default=False),
                            "id": None,
                            "mascota_id": None,
                            "Día": st.column_config.TextColumn("Día (DD/MM/AAAA)", width="small"),
                            "Hora": st.column_config.TextColumn("Hora", width="small"),
                            "Estado": st.column_config.SelectboxColumn("🎨 Estado", options=[f"{EMOJIS_ESTADO.get(e, '')} {e}" for e in ESTADOS_CITA], required=True),
                            "Peluquero/a": st.column_config.SelectboxColumn("👩‍🦰 Peluquero/a", options=["Sin Asignar"] + empleados_lista, required=True),
                            "Servicio": st.column_config.SelectboxColumn("✂️ Servicio", options=opciones_seguras_ag, required=True),
                            "Mascota": st.column_config.TextColumn(disabled=True),
                            "Dueño": st.column_config.TextColumn(disabled=True),
                            "Dirección": st.column_config.TextColumn(disabled=True),
                            "Teléfono": st.column_config.TextColumn(disabled=True),
                            "Observaciones": st.column_config.TextColumn("Anotación"),
                            "WhatsApp": st.column_config.LinkColumn("📱 Avisar", display_text="💬 Recordatorio")
                        }
                    )
                    
                    if st.button("💾 Guardar Cambios en Agenda", type="primary"):
                        ids_actuales = ed_citas['id'].dropna().tolist()
                        ids_orig = df_citas['id'].tolist()
                        ids_borrar = [i for i in ids_orig if i not in ids_actuales]
                        
                        for id_b in ids_borrar: client.table("citas").delete().eq("id", id_b).execute()
                        
                        for _, row in ed_citas.iterrows():
                            if pd.notna(row['id']):
                                if row.get('Borrar', False) == True:
                                    client.table("citas").delete().eq("id", row['id']).execute()
                                else:
                                    try:
                                        dt_str = pd.to_datetime(f"{row['Día']} {row['Hora']}", format='%d/%m/%Y %H:%M').strftime('%Y-%m-%d %H:%M:%S')
                                    except:
                                        dt_str = pd.to_datetime(f"{row['Día']} {row['Hora']}").strftime('%Y-%m-%d %H:%M:%S')
                                        
                                    srv = str(row['Servicio'])
                                    pelu = str(row['Peluquero/a'])
                                    est_raw = str(row['Estado'])
                                    est = est_raw.split(" ", 1)[1] if " " in est_raw else est_raw
                                    if pelu != "Sin Asignar":
                                        srv_base = f"{srv} ({pelu})"
                                    else:
                                        srv_base = srv
                                        
                                    srv_final = f"[ESTADO: {est}] {srv_base}"
                                        
                                    client.table("citas").update({
                                        "fecha_hora": dt_str,
                                        "duracion_minutos": int(row['Duración (min)']),
                                        "servicio": srv_final,
                                        "observaciones": str(row.get('Observaciones', ''))
                                    }).eq("id", row['id']).execute()
                        st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                        st.success("Agenda actualizada."); time.sleep(0.8); st.rerun()
                        
                    # LÓGICA VER FICHA
                    for _, row in ed_citas.iterrows():
                        if row.get('Ver Ficha', False):
                            m_id = row['mascota_id']
                            if pd.notna(m_id):
                                res_m = client.table("mascotas").select("*").eq("id", m_id).execute()
                                if res_m.data:
                                    from ficha_clinica import mostrar_ficha_clinica
                                    st.markdown("---")
                                    mostrar_ficha_clinica(m_id, row['Mascota'], res_m.data[0], "agenda_dir", client, servicios_lista, empleados_lista, precios_servicios)
                            break
            else:
                st.info("No hay citas agendadas en el sistema.")
                
    with sub_diario:
        st.markdown("#### 🕒 Cuadrante de Trabajo Diario (Intervalos de 5 min)")
        
        c_diario1, c_diario2, c_diario3 = st.columns([1, 1.5, 1])
        with c_diario1:
            dia_ver = st.date_input("Selecciona un día para ver los huecos libres:", value=date.today())
            fest_diario = es_festivo(dia_ver)
            if fest_diario:
                st.info(f"🌴 **Día Festivo:** {fest_diario}")
        with c_diario2:
            rango_defecto = (9, 21) if dia_ver.weekday() < 5 else (10, 14)
            rango_horas = st.slider("⏱️ Rango de horas visible:", min_value=6, max_value=23, value=rango_defecto, format="%d:00")
        with c_diario3:
            st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
            ocultar_libres = st.checkbox("Ocultar tramos libres (Vista compacta)", value=False)
        
        # Creamos una cuadrícula estricta adaptada a la selección
        horas_trabajo = [f"{h:02d}:{m:02d}" for h in range(rango_horas[0], rango_horas[1]) for m in range(0, 60, 5)]
        df_cuadrante = pd.DataFrame({"Hora": horas_trabajo})
        df_cuadrante["Estado"] = "🟩 Libre"
        df_cuadrante["Detalle"] = ""
        
        if res_citas.data:
            for c in res_citas.data:
                try:
                    if "[ESTADO: Cancelada]" in c.get('servicio', ''): continue
                    dt_start = pd.to_datetime(c['fecha_hora'])
                    if dt_start.tzinfo: dt_start = dt_start.tz_localize(None)
                    if dt_start.date() == dia_ver:
                        dur = c.get('duracion_minutos') if c.get('duracion_minutos') is not None else 60
                        dt_end = dt_start + pd.Timedelta(minutes=dur)
                        mascota = c.get('mascotas', {}).get('nombre', 'Mascota')
                        
                        estado_c, s_clean, assigned_e = parse_cita_estado(c.get('servicio', ''))
                        emoji = EMOJIS_ESTADO.get(estado_c, "🟢")
                                
                        detalle_texto = f"{emoji} [{assigned_e}] {mascota} ({dur} min) - {s_clean}"
                        
                        # Recorremos la cuadrícula y rellenamos los huecos afectados
                        primer_bloque = True
                        for idx, row in df_cuadrante.iterrows():
                            q_time = pd.to_datetime(f"{dia_ver} {row['Hora']}")
                            if dt_start <= q_time < dt_end:
                                # Estado dinámico (Soporta múltiples peluqueros a la vez)
                                if "Cambio" in estado_c:
                                    if df_cuadrante.loc[idx, "Estado"] == "🟩 Libre":
                                        df_cuadrante.loc[idx, "Estado"] = "🔵 Liberado"
                                else:
                                    if df_cuadrante.loc[idx, "Estado"] in ["� Libre", "🔵 Liberado"]:
                                        df_cuadrante.loc[idx, "Estado"] = "🔴 Ocupado"
                                    elif "Ocupado" in df_cuadrante.loc[idx, "Estado"]:
                                        df_cuadrante.loc[idx, "Estado"] = "⚠️ Múltiple"
                                
                                # Texto compacto si la cita ocupa muchos tramos
                                if primer_bloque:
                                    texto_add = detalle_texto
                                    primer_bloque = False
                                else:
                                    texto_add = f"⏬ (Continúa {mascota})"
                                
                                if df_cuadrante.loc[idx, "Detalle"]:
                                    df_cuadrante.loc[idx, "Detalle"] += "  |  " + texto_add
                                else:
                                    df_cuadrante.loc[idx, "Detalle"] = texto_add
                except: pass
                
        df_cuadrante = df_cuadrante.sort_values("Hora").reset_index(drop=True)
        
        if ocultar_libres:
            df_cuadrante = df_cuadrante[df_cuadrante["Estado"] != "🟩 Libre"]
            if df_cuadrante.empty:
                st.info("No hay citas programadas para este día.")
                
        st.dataframe(df_cuadrante, use_container_width=True, hide_index=True, height=600)

    with sub_semanal:
        st.markdown("#### 🗓️ Cuadrante de Trabajo Semanal (Vista Flexible)")
        dia_referencia = st.date_input("Selecciona una fecha para ver su semana:", value=date.today(), key="semana_picker")
        
        start_of_week = dia_referencia - timedelta(days=dia_referencia.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        st.markdown(f"##### Semana del {start_of_week.strftime('%d/%m/%Y')} al {end_of_week.strftime('%d/%m/%Y')}")

        dias_semana_dt = [(start_of_week + timedelta(days=i)) for i in range(7)]
        nombres_dias_col = []
        for d in dias_semana_dt:
            fest = es_festivo(d.date())
            nombres_dias_col.append(d.strftime('%A\n%d/%m') + (f"\n{fest}" if fest else ""))

        # Diccionario para agrupar citas por columna (día)
        citas_por_dia = {dia: [] for dia in nombres_dias_col}

        if res_citas.data:
            for cita in res_citas.data:
                try:
                    dt_start = pd.to_datetime(cita['fecha_hora'])
                    if dt_start.tzinfo: dt_start = dt_start.tz_localize(None)
                    if start_of_week <= dt_start.date() <= end_of_week:
                        if "[ESTADO: Cancelada]" in cita.get('servicio', ''): continue
                        duracion = cita.get('duracion_minutos') if cita.get('duracion_minutos') is not None else 60
                        dt_end = dt_start + timedelta(minutes=duracion)
                        
                        col_dia = dt_start.strftime('%A\n%d/%m')
                        mascota_nombre = cita.get('mascotas', {}).get('nombre', 'Cita')
                        
                        estado_c, s_clean, assigned_e = parse_cita_estado(cita.get('servicio', ''))
                        emoji = EMOJIS_ESTADO.get(estado_c, "🟢")
                        
                        texto_cita = f"{emoji} {dt_start.strftime('%H:%M')}-{dt_end.strftime('%H:%M')} | {mascota_nombre} ({assigned_e})"
                        citas_por_dia[col_dia].append((dt_start, texto_cita))
                except Exception: pass
        
        # Ordenar cronológicamente y preparar para la tabla
        max_filas = 0
        for dia in nombres_dias_col:
            citas_por_dia[dia].sort(key=lambda x: x[0])  # Ordenar por hora de inicio
            citas_por_dia[dia] = [c[1] for c in citas_por_dia[dia]]  # Quedarnos solo con el texto
            if len(citas_por_dia[dia]) > max_filas:
                max_filas = len(citas_por_dia[dia])
                
        if max_filas == 0:
            df_semana = pd.DataFrame([["" for _ in nombres_dias_col]], columns=nombres_dias_col)
            st.info("Semana completamente libre. No hay citas agendadas.")
        else:
            # Rellenar con blancos las listas más cortas para cuadrar el DataFrame
            for dia in nombres_dias_col:
                while len(citas_por_dia[dia]) < max_filas:
                    citas_por_dia[dia].append("")
            df_semana = pd.DataFrame(citas_por_dia)
            st.dataframe(df_semana, use_container_width=True, hide_index=True)
            
    with sub_recordatorios:
        st.markdown("#### 🔔 Centro de Recordatorios (Citas y Mantenimiento)")
        st.info("Espacio centralizado para gestionar las confirmaciones de citas y mantenimientos diarios (vía WhatsApp o llamada telefónica).")
        
        # --- 1. CONFIRMACIONES DEL PRÓXIMO DÍA HÁBIL ---
        hoy_dt = pd.to_datetime('today')
        manana_dt = hoy_dt + pd.Timedelta(days=1)
        
        # Si el próximo día es domingo (6), saltamos automáticamente al lunes
        if manana_dt.weekday() == 6:
            manana_dt += pd.Timedelta(days=1)
            
        dias_es = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}
        meses_es = {1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio", 7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"}
        nombre_dia_obj = dias_es[manana_dt.weekday()]
        
        st.markdown(f"##### 📅 1. Confirmaciones para el {nombre_dia_obj} ({manana_dt.strftime('%d/%m')})")
        
        manana_str_ini = manana_dt.strftime('%Y-%m-%dT00:00:00')
        manana_str_fin = manana_dt.strftime('%Y-%m-%dT23:59:59')
        
        res_manana = client.table("citas").select("fecha_hora, servicio, mascotas(nombre, clientes(nombre_dueno, telefono, metodo_contacto, direccion, servicio_domicilio))").gte("fecha_hora", manana_str_ini).lte("fecha_hora", manana_str_fin).execute()
        
        citas_manana = []
        if res_manana.data:
            for c in res_manana.data:
                if "[ESTADO: Cancelada]" in c.get('servicio', ''): continue
                mascota_info = c.get('mascotas', {}) or {}
                cliente_info = mascota_info.get('clientes', {}) or {}
                dueno = cliente_info.get('nombre_dueno', 'Dueño')
                telefono = cliente_info.get('telefono', '')
                pref_contacto = cliente_info.get('metodo_contacto') or 'WhatsApp'
                domicilio = cliente_info.get('servicio_domicilio', False)
                direccion = cliente_info.get('direccion', '')
                nombre_m = mascota_info.get('nombre', 'tu mascota')
                
                dt_obj = pd.to_datetime(c['fecha_hora'])
                hora_str = dt_obj.strftime('%H:%M')
                
                fecha_str_wa = f"{nombre_dia_obj.lower()} {manana_dt.day} {meses_es[manana_dt.month]}"
                
                if domicilio:
                    msg = f"Hola buenos 🐾🐾 días desde Animalarium le recordamos la cita de peluquería para {nombre_m}\nHora: {hora_str}\nDía: {fecha_str_wa}\nDirección de recogida: {direccion}\nConfirmanos contestando a este mensaje, de lo contrario la cita será cancelada.\nSi desea cambiar la cita no dude en comunicarlo.🐾😊❤️🐶🚗"
                else:
                    msg = f"Hola buenos 🐾🐾 días desde Animalarium le recordamos la cita de peluquería para {nombre_m}\nHora: {hora_str}\nDía: {fecha_str_wa}\nConfirmanos contestando a este mensaje, de lo contrario la cita será cancelada.\nSi desea cambiar la cita no dude en comunicarlo.🐾😊❤️🐶"
                    
                url_wa = generar_enlace_wa(telefono, msg)
                    
                import re
                s_raw = c.get('servicio', '')
                s_clean = re.sub(r'\[ESTADO:\s*.*?\]\s*', '', s_raw).strip()
                
                citas_manana.append({
                    "Hora": hora_str,
                    "Mascota": nombre_m,
                    "Dueño": dueno + (" 🚚" if domicilio else ""),
                    "Dirección": direccion if domicilio else "En local",
                    "Canal Pref.": pref_contacto,
                    "Servicio": s_clean,
                    "WhatsApp": url_wa
                })
                
        if citas_manana:
            df_manana = pd.DataFrame(citas_manana).sort_values("Hora")
            st.dataframe(df_manana, use_container_width=True, hide_index=True, column_config={"WhatsApp": st.column_config.LinkColumn("📱 Acción Automática", display_text="💬 Pedir Confirmación")})
        else:
            st.success(f"No hay citas programadas para el {nombre_dia_obj.lower()} o ya están todas canceladas.")

        st.markdown("---")
        
        # --- 2. RECORDATORIOS DE MANTENIMIENTO ---
        st.markdown("##### ✂️ 2. Recordatorios de Mantenimiento")
        st.markdown("<p style='color:gray; font-size:14px;'>Clientes que superan los días sin venir y <b>NO tienen ya una cita futura agendada</b>.</p>", unsafe_allow_html=True)
        
        c_al1, c_al2 = st.columns([1, 2])
        with c_al1:
            dias_aviso = st.slider("Mostrar mascotas sin venir en más de (días):", min_value=15, max_value=180, value=45, step=5)
        
        hoy_str = hoy_dt.strftime('%Y-%m-%dT00:00:00')
        res_futuras = client.table("citas").select("mascotas_id, servicio").gte("fecha_hora", hoy_str).execute()
        mascotas_con_cita = set()
        if res_futuras.data:
            for c in res_futuras.data:
                if "[ESTADO: Cancelada]" not in c.get("servicio", ""):
                    mascotas_con_cita.add(c["mascotas_id"])
        
        m_alertas_data = get_alertas_m_ag_cached(client, st.session_state.get('db_version', 0))
        
        if m_alertas_data:
            alertas = []
            for m in m_alertas_data:
                if m['id'] in mascotas_con_cita: continue
                    
                hist = m.get('historial_trabajos', [])
                if isinstance(hist, list) and len(hist) > 0:
                    try:
                        fechas = [pd.to_datetime(h['Fecha'], format='%d/%m/%Y', errors='coerce') for h in hist if h.get('Fecha')]
                        fechas = [f for f in fechas if pd.notna(f)]
                        if fechas:
                            ultima_visita = max(fechas)
                            dias_transcurridos = (hoy_dt - ultima_visita).days
                            
                            if dias_transcurridos >= dias_aviso:
                                cliente_info = m.get('clientes') or {}
                                dueno = cliente_info.get('nombre_dueno', 'Dueño')
                                telefono = cliente_info.get('telefono', '')
                                pref_contacto = cliente_info.get('metodo_contacto') or 'WhatsApp'
                                
                                mensaje = f"¡Hola {dueno}! 🐾 Nos ponemos en contacto desde Animalarium porque, revisando la ficha de {m['nombre']}, hemos visto que ya le va tocando su sesión de peluquería para mantener el manto perfecto. Recuerda que si reservas antes de que se cumplan los 2 meses de su última visita, te aplicamos un 10% de descuento en el servicio. ¿Te buscamos un huequito para estos días? ¡Un abrazo! 🐶✂️"
                                url_wa = generar_enlace_wa(telefono, mensaje)
                                
                                alertas.append({
                                    "Mascota": m['nombre'], "Dueño": dueno,
                                    "Canal Pref.": pref_contacto,
                                    "Última Visita": ultima_visita.strftime('%d/%m/%Y'),
                                    "Días Sin Venir": dias_transcurridos, "WhatsApp": url_wa
                                })
                    except Exception as e: pass
            
            if alertas:
                df_alertas = pd.DataFrame(alertas).sort_values(by="Días Sin Venir", ascending=False)
                st.warning(f"⚠️ Tienes **{len(alertas)}** clientes pendientes de contactar para mantenimiento.")
                st.dataframe(df_alertas, use_container_width=True, hide_index=True, column_config={"WhatsApp": st.column_config.LinkColumn("📱 Acción Automática", display_text="💬 Enviar WhatsApp")})
            else:
                st.success("✨ ¡Genial! Tienes la agenda al día. Ninguna mascota supera los días de alerta o ya tienen su cita.")

    with sub_cancelaciones:
        st.markdown("#### 🚫 Registro de Cancelaciones")
        st.info("Aquí aparecen todas las citas que han sido marcadas como 'Cancelada' desde el Directorio. Estas citas liberan su hueco automáticamente en la agenda para que puedas dárselo a otro.")
        canceladas = []
        res_canc = client.table("citas").select("fecha_hora, servicio, mascotas(nombre, clientes(nombre_dueno, telefono))").like("servicio", "%[ESTADO: Cancelada]%").order("fecha_hora", desc=True).limit(200).execute()
        if res_canc.data:
            for c in res_canc.data:
                mascota_info = c.get('mascotas', {})
                cliente_info = mascota_info.get('clientes', {}) if mascota_info else {}
                dt_obj = pd.to_datetime(c['fecha_hora'])
                _, s_clean, assigned_e = parse_cita_estado(c.get('servicio', ''))

                canceladas.append({
                        "Fecha": dt_obj.strftime('%d/%m/%Y'),
                        "Hora": dt_obj.strftime('%H:%M'),
                        "Mascota": mascota_info.get('nombre', 'N/A'),
                        "Dueño": cliente_info.get('nombre_dueno', 'N/A'),
                        "Teléfono": cliente_info.get('telefono', 'N/A'),
                        "Peluquero/a": assigned_e,
                        "Servicio Programado": s_clean
                    })
        if canceladas: st.dataframe(pd.DataFrame(canceladas), use_container_width=True, hide_index=True)
        else: st.success("No hay cancelaciones registradas en el sistema.")

    with sub_sin_historial:
        st.markdown("#### 🚨 Alertas Operativas: Citas sin Registro en Historial")
        st.info("Estas son las citas **confirmadas** de días pasados a las que aún **no se les ha rellenado el importe o el registro del trabajo** en la ficha de la mascota.")
        
        hoy_str = str(date.today())
        # Buscamos citas confirmadas anteriores a hoy
        
        d_sin_hist = get_sin_hist_ag_cached(client, st.session_state.get('db_version', 0), hoy_str)
        alertas = []
        if d_sin_hist:
            for c in d_sin_hist:
                try:
                    dt_c_raw = pd.to_datetime(c['fecha_hora'])
                    dt_c = dt_c_raw.date()
                    
                    masc = c.get('mascotas')
                    if not isinstance(masc, dict): continue
                    
                    hist = masc.get('historial_trabajos')
                    encontrado = False
                    if isinstance(hist, list):
                        for t in hist:
                            try:
                                f_str = str(t.get('Fecha', ''))
                                if f_str:
                                    dt_t = pd.to_datetime(f_str, format="%d/%m/%Y").date()
                                    if dt_t == dt_c:
                                        encontrado = True; break
                            except: pass
                    
                    if not encontrado:
                        _, s_clean, assigned_e = parse_cita_estado(c.get('servicio', ''))
                        alertas.append({
                            "Ver Ficha": False,
                            "mascota_id": masc.get('id'),
                            "Fecha Cita": dt_c.strftime("%d/%m/%Y"),
                            "Peluquero/a": assigned_e,
                            "Mascota": masc.get('nombre', 'Desconocida'),
                            "Servicio": s_clean
                        })
                except: pass
                
        if alertas:
            st.warning(f"⚠️ Hay {len(alertas)} citas pasadas confirmadas sin historial rellenado.")
            df_alertas = pd.DataFrame(alertas)
            ed_alertas = st.data_editor(
                df_alertas, 
                use_container_width=True, hide_index=True,
                column_config={
                    "mascota_id": None, 
                    "Ver Ficha": st.column_config.CheckboxColumn("👁️ Ver Ficha", default=False)
                }
            )
            for _, row in ed_alertas.iterrows():
                if row.get('Ver Ficha', False):
                    m_id = row['mascota_id']
                    if pd.notna(m_id):
                        res_m_data = get_masc_info_cached(client, st.session_state.get('db_version', 0), m_id)
                        if res_m_data:
                            from ficha_clinica import mostrar_ficha_clinica
                            st.markdown("---")
                            mostrar_ficha_clinica(m_id, row['Mascota'], res_m_data[0], "agenda_hist", client, servicios_lista, empleados_lista, precios_servicios)
                    break
        else:
            st.success("¡Todo al día! Todas las citas pasadas tienen su historial registrado correctamente.")