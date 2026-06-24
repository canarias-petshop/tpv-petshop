import streamlit as st
import pandas as pd
from datetime import date, timedelta
import time
import urllib.parse
import calendar

@st.cache_data(show_spinner=False, ttl=300)
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

@st.cache_data(show_spinner=False, ttl=300)
def get_citas_ag_cached(_client, v):
    _all = []
    _off = 0
    while True:
        _r = _client.table("citas").select("id, fecha_hora, servicio, duracion_minutos, observaciones, mascotas(id, nombre, especie, raza, clientes(nombre_dueno, telefono, direccion, servicio_domicilio))").order("fecha_hora", desc=False).range(_off, _off + 999).execute()
        if _r.data:
            _all.extend(_r.data)
            if len(_r.data) < 1000: break
            _off += 1000
        else: break
    return _all

@st.cache_data(show_spinner=False, ttl=300)
def get_masc_info_cached(_client, v, mid):
    return _client.table("mascotas").select("*").eq("id", mid).execute().data

@st.cache_data(show_spinner=False, ttl=300)
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

@st.cache_data(show_spinner=False, ttl=300)
def get_manana_ag_cached(_client, v, m_ini, m_fin):
    return _client.table("citas").select("id, fecha_hora, servicio, observaciones, mascotas(nombre, clientes(nombre_dueno, telefono, metodo_contacto, direccion, servicio_domicilio))").gte("fecha_hora", m_ini).lte("fecha_hora", m_fin).execute().data

@st.cache_data(show_spinner=False, ttl=300)
def get_futuras_ag_cached(_client, v, h_str):
    return _client.table("citas").select("mascotas_id, servicio").gte("fecha_hora", h_str).execute().data

@st.cache_data(show_spinner=False, ttl=300)
def get_canc_ag_cached(_client, v):
    return _client.table("citas").select("fecha_hora, servicio, mascotas(nombre, clientes(nombre_dueno, telefono))").or_("servicio.ilike.%[ESTADO: Cancelada]%,servicio.ilike.%[ESTADO: No presentado]%,servicio.ilike.%[ESTADO: Anulada]%").order("fecha_hora", desc=True).limit(200).execute().data

@st.cache_data(show_spinner=False, ttl=300)
def get_sin_hist_ag_cached(_client, v, h_str):
    return _client.table("citas").select("fecha_hora, servicio, mascotas(id, nombre, historial_trabajos)").lt("fecha_hora", h_str).like("servicio", "%[ESTADO: Confirmada]%").execute().data

@st.cache_data(show_spinner=False, ttl=300)
def get_turnos_ag_cached(_client, v, f_ini, f_fin):
    _all = []
    _off = 0
    while True:
        _r = _client.table("personal_cuadrantes").select("fecha, turno, personal_empleados(nombre)").gte("fecha", f_ini).lte("fecha", f_fin).range(_off, _off + 999).execute()
        if _r.data:
            _all.extend(_r.data)
            if len(_r.data) < 1000: break
            _off += 1000
        else: break
    return _all

@st.cache_data(show_spinner=False, ttl=300)
def get_bloqueos_ag_cached(_client, v, f_ini, f_fin):
    try:
        return _client.table("agenda_bloqueos").select("*").gte("fecha", f_ini).lte("fecha", f_fin).execute().data
    except: return []

@st.cache_data(show_spinner=False, ttl=300)
def get_ferias_ag_cached(_client, v, f_ini, f_fin):
    try:
        # Esta consulta encuentra cualquier evento que se solape con el rango de fechas seleccionado
        return _client.table("eventos_ferias").select("titulo, fecha_inicio, fecha_fin").lte("fecha_inicio", f_fin).gte("fecha_fin", f_ini).execute().data
    except: return []

@st.cache_data(show_spinner=False, ttl=300)
def get_empleados_ag_cached(_client, v):
    return _client.table("personal_empleados").select("id, nombre").eq("activo", True).execute().data

@st.cache_data(show_spinner=False, ttl=300)
def get_servicios_ag_cached(_client, v):
    return _client.table("productos").select("nombre, precio_pvp, precio_base").eq("categoria", "Servicio").order("nombre").execute().data

@st.cache_data(show_spinner=False, ttl=300)
def get_masc_obs_hist_cached(_client, v, m_id):
    return _client.table("mascotas").select("observaciones, historial_trabajos").eq("id", m_id).execute().data

@st.cache_data(show_spinner=False, ttl=300)
def get_turnos_dia_ag_cached(_client, v, fecha_c):
    return _client.table("personal_cuadrantes").select("empleado_id, turno, personal_empleados(nombre)").eq("fecha", str(fecha_c)).execute().data

@st.cache_data(show_spinner=False, ttl=300)
def get_citas_mes_ag_cached(_client, v, f_ini_mes, f_fin_mes):
    return _client.table("citas").select("fecha_hora, servicio, mascotas(nombre, raza, clientes(nombre_dueno, telefono))").gte("fecha_hora", f"{f_ini_mes}T00:00:00").lte("fecha_hora", f"{f_fin_mes}T23:59:59").execute().data

def limpiar_cache_agenda():
    get_masc_ag_cached.clear()
    get_citas_ag_cached.clear()
    get_masc_info_cached.clear()
    get_alertas_m_ag_cached.clear()
    get_manana_ag_cached.clear()
    get_futuras_ag_cached.clear()
    get_canc_ag_cached.clear()
    get_sin_hist_ag_cached.clear()
    get_turnos_ag_cached.clear()
    get_bloqueos_ag_cached.clear()
    get_ferias_ag_cached.clear()
    get_empleados_ag_cached.clear()
    get_servicios_ag_cached.clear()
    get_masc_obs_hist_cached.clear()
    get_turnos_dia_ag_cached.clear()
    get_citas_mes_ag_cached.clear()

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
        emp_res_data = get_empleados_ag_cached(client, st.session_state.get('db_version', 0))
        empleados_lista = [e['nombre'] for e in emp_res_data] if emp_res_data else []
    except: empleados_lista = []
    
    try:
        serv_res_data = get_servicios_ag_cached(client, st.session_state.get('db_version', 0))
        if serv_res_data:
            servicios_lista = [s['nombre'] for s in serv_res_data] + ["Otro"]
            precios_servicios = {s['nombre']: float(s.get('precio_pvp') or s.get('precio_base') or 0.0) for s in serv_res_data}
        else:
            servicios_lista = ["Peluquería", "Otro"]
            precios_servicios = {}
    except: 
        servicios_lista = ["Otro"]
        precios_servicios = {}

    ESTADOS_CITA = ["Confirmada", "Asistió", "Cancelada", "Anulada", "No presentado", "Cambio (días después)", "Servicio de recogida pendiente", "Servicio de recogida confirmado", "Cambio (día antes)", "Cambio (mismo día)", "Oferta / Descuento", "Pendiente", "Pendiente (Avisar hueco)"]
    EMOJIS_ESTADO = {
        "Confirmada": "🟢", "Asistió": "✅", "Cancelada": "💖", "Anulada": "🚫", "No presentado": "❌", "Cambio (días después)": "🔵", "Cambio de cita": "🔵", 
        "Servicio de recogida": "🟣", "Servicio de recogida pendiente": "🟣🟡", "Servicio de recogida confirmado": "🟣🟢",
        "Cambio (día antes)": "🟤", "Cambio (mismo día)": "⚪", 
        "Oferta / Descuento": "🟩", "Pendiente": "🟡", "Pendiente (Avisar hueco)": "🟡🟠"
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
            elif estado == "Cambio de cita":
                estado = "Cambio (días después)"
            servicio_raw = re.sub(r'\[ESTADO:\s*.*?\]\s*', '', servicio_raw)
            
        emp = "Sin Asignar"
        for e in empleados_lista:
            if f"({e})" in servicio_raw:
                emp = e; servicio_raw = servicio_raw.replace(f"({e})", "").replace("  ", " ").strip(); break
        return estado, servicio_raw.strip(), emp
    
    # --- PESTAÑAS DE VISTAS ---
    sub_agenda, sub_diario, sub_semanal, sub_mensual, sub_recordatorios, sub_cancelaciones, sub_sin_historial = st.tabs(["📝 Gestión de Citas", "🕒 Vista Diaria", "🗓️ Vista Semanal", "📅 Vista Mensual", "🔔 Recordatorios", "🚫 Cancelaciones", "🚨 Sin Historial"])
    
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
                strikes = 0
                if mascota_sel:
                    m_id_sel = dict_mascotas[mascota_sel]
                    res_m_info_data = get_masc_obs_hist_cached(client, st.session_state.get('db_version', 0), m_id_sel)
                    if res_m_info_data:
                        obs = res_m_info_data[0].get('observaciones', '')
                        import re
                        from ficha_clinica import fetch_ficha_alerts_cached
                        _, r_canc = fetch_ficha_alerts_cached(client, st.session_state.get('db_version', 0), m_id_sel, str(date.today()))
                        strikes = len(r_canc) if r_canc else 0
                        
                        m_pref = re.search(r'\[Pref:\s*(.*?)\]', str(obs))
                        if m_pref: pref_actual = m_pref.group(1)
                        
                        historial = res_m_info_data[0].get('historial_trabajos', [])
                        duraciones = [t['Duración (min)'] for t in historial if isinstance(t, dict) and isinstance(t.get('Duración (min)'), (int, float))]
                        if duraciones: 
                            dur_media = int(sum(duraciones) / len(duraciones))
                            st.info(f"⏱️ **Info de la mascota:** Tiempo medio de {dur_media} min | Peluquero/a pref: {pref_actual}")
                        else:
                            st.info(f"⏱️ **Info de la mascota:** Sin historial (60 min por defecto) | Peluquero/a pref: {pref_actual}")
                        
                fecha_c = st.date_input("Fecha *", value=pd.Timestamp.now('Atlantic/Canary').date(), key=f"ag_fec_{st.session_state.llave_agenda_cita}")
                duracion_c = st.number_input("Duración estimada (minutos) *", min_value=5, max_value=300, value=dur_media, step=5, key=f"ag_dur_{st.session_state.llave_agenda_cita}")
                
                opciones_emp = ["Cualquiera"] + empleados_lista
                def_index = opciones_emp.index(pref_actual) if pref_actual in opciones_emp else 0
                f_emp = st.selectbox("Peluquera/o Preferido:", opciones_emp, index=def_index, key=f"ag_emp_{st.session_state.llave_agenda_cita}")
                
                # Buscador inteligente de huecos cruzado con el preferido
                res_turnos_data = get_turnos_dia_ag_cached(client, st.session_state.get('db_version', 0), fecha_c)
                turnos_dict = {}
                if res_turnos_data:
                    for t in res_turnos_data:
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
                                if "[ESTADO: Cancelada]" in c.get('servicio', '') or "[ESTADO: Anulada]" in c.get('servicio', '') or "[ESTADO: Cambio" in c.get('servicio', '') or "[ESTADO: No presentado]" in c.get('servicio', ''): continue
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
                            if "[ESTADO: Cancelada]" in c.get('servicio', '') or "[ESTADO: Anulada]" in c.get('servicio', '') or "[ESTADO: Cambio" in c.get('servicio', '') or "[ESTADO: No presentado]" in c.get('servicio', ''): continue
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
                
                if strikes >= 2:
                    st.error(f"🚨 **CLIENTE REINCIDENTE ({strikes} faltas):** Por política, es obligatorio cobrar fianza o pago por adelantado para agendar.")
                    fianza_pagada = st.checkbox("✅ Confirmo cobro de fianza o pago por adelantado", key=f"ag_fianza_{st.session_state.llave_agenda_cita}")
                else:
                    fianza_pagada = False
                
                if st.button("Guardar Cita", type="primary", use_container_width=True):
                    m_id_final = None
                    
                    if solapa_manual and (not motivo_solape or (motivo_solape == "Otro motivo" and not motivo_extra)):
                        st.error("Debes indicar un motivo para forzar la cita en una hora ocupada.")
                    elif strikes >= 2 and not fianza_pagada:
                        st.error("Debes confirmar el cobro de la fianza para poder agendar a este cliente.")
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
                                
                            if fianza_pagada:
                                servicio_final = f"[ESTADO: Pendiente] [💰 FIANZA PAGADA] {servicio_final}"
                            else:
                                servicio_final = f"[ESTADO: Pendiente] {servicio_final}"
                            fecha_hora_str = f"{fecha_c} {hora_final_str}"
                            
                            client.table("citas").insert({
                                "mascotas_id": m_id_final, "fecha_hora": fecha_hora_str,
                                "servicio": servicio_final, "duracion_minutos": int(duracion_c),
                                "observaciones": str(f_obs)
                            }).execute()
                            st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                            st.session_state.llave_agenda_cita += 1
                            st.success("Cita agendada."); time.sleep(1); limpiar_cache_agenda(); st.rerun()

        with c_agenda2:
            st.markdown("#### 🗓️ Directorio de Citas (Editable)")
            
            # --- RADAR DE LISTA DE ESPERA ---
            espera_citas = []
            if res_citas.data:
                hoy_dt = pd.Timestamp.now('Atlantic/Canary').replace(tzinfo=None)
                for cx in res_citas.data:
                    estado_cx, _, _ = parse_cita_estado(cx.get('servicio', ''))
                    if estado_cx == "Pendiente (Avisar hueco)":
                        try:
                            dt_obj_x = pd.to_datetime(cx['fecha_hora'])
                            if dt_obj_x.tzinfo: dt_obj_x = dt_obj_x.tz_localize(None)
                            if dt_obj_x >= hoy_dt:
                                masc_info = cx.get('mascotas') or {}
                                cli_info = masc_info.get('clientes') or {}
                                espera_citas.append({
                                    "Fecha Original": dt_obj_x.strftime('%d/%m/%Y a las %H:%M'),
                                    "Mascota": masc_info.get('nombre', 'N/A'),
                                    "Dueño": cli_info.get('nombre_dueno', 'N/A'),
                                    "Teléfono": cli_info.get('telefono', '')
                                })
                        except: pass
            
            if espera_citas:
                with st.expander(f"🚨 Radar de Huecos: {len(espera_citas)} cliente(s) en lista de espera", expanded=True):
                    st.info("Estos clientes tienen una cita agendada, pero te han pedido que les avises si se cancela alguna cita antes para poder adelantarla.")
                    for esp in espera_citas:
                        msg_radar = f"¡Hola {esp['Dueño']}! Nos pediste que te avisáramos si quedaba un hueco libre antes de tu cita del {esp['Fecha Original']} para {esp['Mascota']}. ¡Se nos ha liberado una hora! ¿Te interesa adelantar la cita?"
                        tel_radar = ''.join(filter(str.isdigit, str(esp['Teléfono'])))
                        if tel_radar and len(tel_radar) == 9 and not tel_radar.startswith('34'): tel_radar = '34' + tel_radar
                        url_wa_radar = f"https://wa.me/{tel_radar}?text={urllib.parse.quote(msg_radar)}" if tel_radar else ""
                        
                        c_rad1, c_rad2 = st.columns([3, 1])
                        c_rad1.write(f"🐾 **{esp['Mascota']}** ({esp['Dueño']}) - Cita actual: {esp['Fecha Original']}")
                        if url_wa_radar: 
                            c_rad2.markdown(f"<a href='{url_wa_radar}' target='_blank'><button style='width:100%; padding:4px; background-color:#25D366; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;'>💬 Avisar de hueco</button></a>", unsafe_allow_html=True)
                    st.markdown("<div style='margin-bottom:10px;'></div>", unsafe_allow_html=True)

            mostrar_pasadas = st.toggle("🕰️ Mostrar citas pasadas", value=False)
            
            if res_citas.data:
                citas_formateadas = []
                hoy_fecha = pd.Timestamp.now('Atlantic/Canary').date()
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

                    nombre_m = mascota_info.get('nombre', 'N/A')
                    especie_m = mascota_info.get('especie', '')
                    if especie_m: nombre_m += f" ({especie_m})"

                    citas_formateadas.append({
                        "Ver Ficha": False,
                        "mascota_id": mascota_info.get('id'),
                        "Borrar": False,
                        "id": c['id'],
                        "Día": dt_obj.date(),
                        "Hora": dt_obj.time(),
                        "Estado": estado_con_emoji,
                        "Duración (min)": dur,
                        "Peluquero/a": assigned_e,
                        "Servicio": s_clean,
                        "Mascota": nombre_m,
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
                            "Día": st.column_config.DateColumn("Día", format="DD/MM/YYYY", width="small"),
                            "Hora": st.column_config.TimeColumn("Hora", format="HH:mm", width="small"),
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
                                        try:
                                            dt_str = pd.Timestamp.combine(row['Día'], row['Hora']).strftime('%Y-%m-%d %H:%M:%S')
                                        except:
                                            dt_str = pd.to_datetime(f"{row['Día']} {row['Hora']}").strftime('%Y-%m-%d %H:%M:%S')
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
                        st.success("Agenda actualizada."); time.sleep(0.8); limpiar_cache_agenda(); st.rerun()
                        
                    # LÓGICA VER FICHA
                    for _, row in ed_citas.iterrows():
                        if row.get('Ver Ficha', False):
                            m_id = row['mascota_id']
                            if pd.notna(m_id):
                                res_m_data = get_masc_info_cached(client, st.session_state.get('db_version', 0), m_id)
                                if res_m_data:
                                    from ficha_clinica import mostrar_ficha_clinica
                                    st.markdown("---")
                                    mostrar_ficha_clinica(m_id, row['Mascota'], res_m_data[0], "agenda_dir", client, servicios_lista, empleados_lista, precios_servicios)
                            break
            else:
                st.info("No hay citas agendadas en el sistema.")
                
            st.markdown("---")
            with st.expander("ℹ️ Leyenda de Estados y Políticas de la Agenda", expanded=False):
                st.markdown("##### 🎨 Leyenda de Estados")
                c_ley1, c_ley2, c_ley3 = st.columns(3)
                with c_ley1:
                    st.write("🟡 **Pendiente** (Por defecto)")
                    st.write("🟡🟠 **Pendiente (Avisar hueco)**")
                    st.write("🟢 **Confirmada**")
                    st.write("✅ **Asistió**")
                    st.write("🟩 **Oferta / Dto.**")
                with c_ley2:
                    st.write("💖 **Cancelada por cliente** (Libera hueco)")
                    st.write("🚫 **Anulada por tienda** (Libera hueco)")
                    st.write("❌ **No presentado** (Falta - Libera hueco)")
                    st.write("⚪ **Cambio (mismo día)** (Falta - Libera hueco)")
                with c_ley3:
                    st.write("🔵 **Cambio (días después)** (Libera hueco)")
                    st.write("🟤 **Cambio (día antes)** (Libera hueco)")
                    st.write("🟣🟡 **Recogida Pendiente**")
                    st.write("🟣🟢 **Recogida Confirmada**")

                st.markdown("##### 🚨 Política de Cancelaciones y Reincidentes (Sistema Automático)")
                st.info("""**Diferencia entre Cancelada y Anulada:**
* **Cancelada:** La cancela explícitamente el cliente.
* **Anulada:** La anulamos nosotros (ej. no abona la fianza tras aviso de 24h).

**Sistema de Faltas (Strikes):** El sistema rastrea automáticamente los estados *Cancelada*, *Anulada*, *No presentado* y *Cambio (mismo día)*.""")
                st.markdown("""
                * **Margen de confianza:** Se otorga **1 falta** de margen al cliente sin penalización.
                * **Bloqueo Automático:** Al acumular **2 faltas o más**, el sistema bloquea el botón de nueva cita con una alerta roja.
                * **Fianzas / Adelantos:** Para volver a agendar a un cliente bloqueado, se le debe exigir una fianza (ej. Bizum). Al hacer la reserva, deberás marcar la casilla de confirmación, añadiendo la etiqueta `[💰 FIANZA PAGADA]` a la cita para que quede constancia en caja.
                * **Liberación de Huecos:** Marcar una cita como *Cancelada*, *Anulada*, *No presentado* o *Cambio* libera instantáneamente esa hora en el cuadrante para cubrirla de manera espontánea.
                """)

    with sub_diario:
        st.markdown("#### 🕒 Cuadrante de Trabajo Diario (Intervalos de 5 min)")
        
        c_diario1, c_diario2, c_diario3 = st.columns([1, 1.5, 1])
        with c_diario1:
            dia_ver = st.date_input("Selecciona un día para ver los huecos libres:", value=pd.Timestamp.now('Atlantic/Canary').date())
            fest_diario = es_festivo(dia_ver)
            if fest_diario:
                st.info(f"🌴 **Día Festivo:** {fest_diario}")
        with c_diario2:
            rango_defecto = (9, 21) if dia_ver.weekday() < 5 else (10, 14)
            rango_horas = st.slider("⏱️ Rango de horas visible:", min_value=6, max_value=23, value=rango_defecto, format="%d:00")
        with c_diario3:
            st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
            ocultar_libres = st.checkbox("Ocultar tramos libres (Vista compacta)", value=False)
        
        # --- Turnos del día actual ---
        turnos_dia = get_turnos_ag_cached(client, st.session_state.get('db_version', 0), str(dia_ver), str(dia_ver))
        textos_t = []
        if turnos_dia:
            for t in turnos_dia:
                nm = t.get('personal_empleados', {}).get('nombre', 'Desconocido') if t.get('personal_empleados') else 'Desconocido'
                tr = t.get('turno', '')
                if tr and tr.lower() not in ["", "libre", "vacaciones", "-"]:
                    textos_t.append(f"**{nm}**: {tr}")
        if textos_t: st.success("👥 **Personal trabajando hoy:** " + " | ".join(textos_t))
        else: st.warning("👥 **Personal trabajando hoy:** Nadie tiene turno asignado.")
        
        # Creamos una cuadrícula estricta adaptada a la selección
        horas_trabajo = [f"{h:02d}:{m:02d}" for h in range(rango_horas[0], rango_horas[1]) for m in range(0, 60, 5)]
        df_cuadrante = pd.DataFrame({"Hora": horas_trabajo})
        df_cuadrante["Estado"] = "🟩 Libre"
        df_cuadrante["Detalle"] = ""
        
        bloqueos_dia = get_bloqueos_ag_cached(client, st.session_state.get('db_version', 0), str(dia_ver), str(dia_ver))
        
        if res_citas.data:
            for c in res_citas.data:
                try:
                    if "[ESTADO: Cancelada]" in c.get('servicio', '') or "[ESTADO: Anulada]" in c.get('servicio', '') or "[ESTADO: No presentado]" in c.get('servicio', '') or "[ESTADO: Cambio" in c.get('servicio', ''): continue
                    dt_start = pd.to_datetime(c['fecha_hora'])
                    if dt_start.tzinfo: dt_start = dt_start.tz_localize(None)
                    if dt_start.date() == dia_ver:
                        dur = c.get('duracion_minutos') if c.get('duracion_minutos') is not None else 60
                        dt_end = dt_start + pd.Timedelta(minutes=dur)
                        
                        masc_info = c.get('mascotas') or {}
                        cli_info = masc_info.get('clientes') or {}
                        
                        mascota = masc_info.get('nombre', 'Mascota')
                        especie = masc_info.get('especie', '')
                        raza = masc_info.get('raza', '')
                        dueno = cli_info.get('nombre_dueno', 'Sin dueño')
                        tel = cli_info.get('telefono', 'Sin tel')
                        
                        if especie: mascota += f" ({especie})"
                        if raza: mascota += f" - {raza}"
                        
                        estado_c, s_clean, assigned_e = parse_cita_estado(c.get('servicio', ''))
                        emoji = EMOJIS_ESTADO.get(estado_c, "🟢")
                                
                        detalle_texto = f"{emoji} [{assigned_e}] {mascota} | 👤 {dueno} (📱 {tel}) | ⏱️ {dur} min | ✂️ {s_clean}"
                        
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
                                    if df_cuadrante.loc[idx, "Estado"] in ["🟩 Libre", "🔵 Liberado"]:
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
                
        if bloqueos_dia:
            for b in bloqueos_dia:
                try:
                    dt_start = pd.to_datetime(f"{dia_ver} {b['hora_inicio']}")
                    dt_end = pd.to_datetime(f"{dia_ver} {b['hora_fin']}")
                    for idx, row in df_cuadrante.iterrows():
                        q_time = pd.to_datetime(f"{dia_ver} {row['Hora']}")
                        if dt_start <= q_time < dt_end:
                            df_cuadrante.loc[idx, "Estado"] = "⛔ Bloqueo"
                            texto_add = f"⛔ [{b.get('empleado_afectado','Todas')}] {b['titulo']}"
                            if df_cuadrante.loc[idx, "Detalle"]:
                                if texto_add not in df_cuadrante.loc[idx, "Detalle"]:
                                    df_cuadrante.loc[idx, "Detalle"] = texto_add + "  |  " + df_cuadrante.loc[idx, "Detalle"]
                            else:
                                df_cuadrante.loc[idx, "Detalle"] = texto_add
                except: pass
                
        df_cuadrante = df_cuadrante.sort_values("Hora").reset_index(drop=True)
        
        # --- Renderizado de Cuadrante Diario ---
        if ocultar_libres:
            df_cuadrante = df_cuadrante[df_cuadrante["Estado"] != "🟩 Libre"]

        if not df_cuadrante.empty:
            html_daily = '''
            <style>
            .daily-table { width: 100%; border-collapse: collapse; font-size: 14px; background-color: white; margin-bottom: 10px; }
            .daily-table th { background-color: #005275; color: white; padding: 10px; text-align: left; font-weight: bold; border: 1px solid #ddd; position: sticky; top: 0; z-index: 1;}
            .daily-table td { border: 1px solid #ddd; padding: 8px 10px; vertical-align: middle; }
            .time-col { width: 80px; font-weight: bold; color: #444; text-align: center !important; background-color: #f5f5f5; border-right: 2px solid #ddd !important; }
            .status-col { width: 110px; font-weight: bold; }
            .detail-col { color: #333; }
            .row-hover:hover { background-color: #f0f8ff; }
            .st-libre { color: #2e7d32; }
            .st-ocupado { color: #d32f2f; }
            .st-liberado { color: #1976d2; }
            .st-multiple { color: #f57c00; }
            .st-bloqueo { color: #9c27b0; font-weight: bold; }
            </style>
            <div style="max-height: 600px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px;">
            <table class="daily-table">
            <tr><th class="time-col">Hora</th><th class="status-col">Estado</th><th>Detalle</th></tr>
            '''
            for _, row in df_cuadrante.iterrows():
                estado = row["Estado"]
                st_class = "st-libre"
                if "Ocupado" in estado: st_class = "st-ocupado"
                elif "Liberado" in estado: st_class = "st-liberado"
                elif "Múltiple" in estado: st_class = "st-multiple"
                elif "Bloqueo" in estado: st_class = "st-bloqueo"
                
                html_daily += f"<tr class='row-hover'><td class='time-col'>{row['Hora']}</td><td class='status-col {st_class}'>{estado}</td><td class='detail-col'>{row['Detalle']}</td></tr>"
                
            html_daily += "</table></div>"
            st.markdown(html_daily, unsafe_allow_html=True)
        else:
            if ocultar_libres:
                st.info("No hay citas programadas para este día.")
            else:
                st.info("No hay horas disponibles en el rango seleccionado.")

    with sub_semanal:
        st.markdown("#### 🗓️ Cuadrante de Trabajo Semanal (Vista Calendario)")
        c_sem1, c_sem2, _ = st.columns([1, 1, 2])
        with c_sem1:
            dia_referencia = st.date_input("Selecciona una fecha de inicio:", value=pd.Timestamp.now('Atlantic/Canary').date(), key="semana_picker")
        with c_sem2:
            num_semanas = st.selectbox("Semanas a la vista:", [1, 2], index=1)
            
        start_of_week = dia_referencia - timedelta(days=dia_referencia.weekday())
        end_of_period = start_of_week + timedelta(days=(7 * num_semanas) - 1)
        
        st.markdown(f"##### Mostrando del {start_of_week.strftime('%d/%m/%Y')} al {end_of_period.strftime('%d/%m/%Y')}")
        
        dias_semana_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        turnos_semana = get_turnos_ag_cached(client, st.session_state.get('db_version', 0), str(start_of_week), str(end_of_period))
        bloqueos_semana = get_bloqueos_ag_cached(client, st.session_state.get('db_version', 0), str(start_of_week), str(end_of_period))
        ferias_semana = get_ferias_ag_cached(client, st.session_state.get('db_version', 0), str(start_of_week), str(end_of_period))
        
        html_week = '''
        <style>
            .weekly-table { width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 13px; background-color: white; margin-bottom: 20px;}
            .weekly-table th { background-color: #005275; color: white; padding: 8px 5px; text-align: center; font-weight: bold; border: 1px solid #ddd; }
            .weekly-table td { border: 1px solid #ddd; vertical-align: top; padding: 6px; background-color: #fafafa; }
            .day-header-w { font-weight: bold; font-size: 1.05em; color: #333; margin-bottom: 6px; border-bottom: 1px solid #eee; padding-bottom: 4px; display: flex; justify-content: space-between;}
            .festivo-w { color: #d32f2f; font-size: 0.8em; font-weight: normal; text-align: right; max-width: 60%; line-height: 1.1;}
            .cita-card { background-color: white; border-left: 4px solid #4caf50; padding: 6px; margin-bottom: 6px; border-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); font-size: 0.85em; line-height: 1.3; word-wrap: break-word;}
            .turno-card { background-color: #e1f5fe; border-left: 4px solid #0288d1; padding: 4px 6px; margin-bottom: 8px; border-radius: 4px; font-size: 0.8em; word-wrap: break-word; color: #333;}
            .td-today-w { background-color: #fffde7 !important; border: 2px solid #fbc02d !important; }
        </style>
        '''
        
        hoy_str_w = str(pd.Timestamp.now('Atlantic/Canary').date())
        
        for w in range(num_semanas):
            html_week += '<table class="weekly-table"><tr>'
            for dia_n in dias_semana_nombres:
                html_week += f"<th>{dia_n}</th>"
            html_week += "</tr><tr>"
            
            for d_idx in range(7):
                d_obj = start_of_week + timedelta(days=(w*7) + d_idx)
                d_str = str(d_obj)
                festivo = es_festivo(d_obj)
                
                is_today = (d_str == hoy_str_w)
                td_class = "td-today-w" if is_today else ""
                
                html_week += f"<td class='{td_class}'>"
                
                # Header
                header_text = f"<span>{d_obj.strftime('%d/%m')}</span>"
                if festivo:
                    header_text += f"<span class='festivo-w'>{festivo}</span>"
                html_week += f"<div class='day-header-w'>{header_text}</div>"
                
                # Turnos
                t_hoy = [t for t in turnos_semana if t['fecha'] == d_str]
                if t_hoy:
                    t_textos = []
                    for t in t_hoy:
                        nm = t.get('personal_empleados', {}).get('nombre', '') if t.get('personal_empleados') else ''
                        tr = t.get('turno', '')
                        if tr and tr.lower() not in ["", "libre", "vacaciones", "-"]:
                            t_textos.append(f"<b>{nm}</b>: {tr}")
                    if t_textos:
                        html_week += f"<div class='turno-card'>👥 {'<br>'.join(t_textos)}</div>"
                
                # Bloqueos y Reuniones
                b_hoy = [b for b in bloqueos_semana if b['fecha'] == d_str]
                if b_hoy:
                    for b in b_hoy:
                        h_ini = b['hora_inicio'][:5]
                        h_fin = b['hora_fin'][:5]
                        html_week += f"<div class='cita-card' style='border-left-color: #9c27b0; background-color: #f3e5f5;'><b>{h_ini}-{h_fin}</b> ⛔<br>📌 {b['titulo']}<br>👥 Afecta: {b.get('empleado_afectado','Todas')}</div>"
                
                # Ferias y Eventos (NUEVO)
                f_hoy = []
                if ferias_semana:
                    for f in ferias_semana:
                        try:
                            f_ini = pd.to_datetime(f['fecha_inicio']).date()
                            f_fin = pd.to_datetime(f['fecha_fin']).date()
                            if f_ini <= d_obj <= f_fin: f_hoy.append(f)
                        except: pass
                if f_hoy:
                    for f in f_hoy: html_week += f"<div class='cita-card' style='border-left-color: #ffc107; background-color: #fff8e1;'>🎪 <b>{f['titulo']}</b></div>"
                
                # Citas
                citas_hoy = []
                if res_citas.data:
                    for cita in res_citas.data:
                        try:
                            dt_start = pd.to_datetime(cita['fecha_hora'])
                            if dt_start.tzinfo: dt_start = dt_start.tz_localize(None)
                            if dt_start.date() == d_obj:
                                if "[ESTADO: Cancelada]" in cita.get('servicio', '') or "[ESTADO: Anulada]" in cita.get('servicio', '') or "[ESTADO: No presentado]" in cita.get('servicio', '') or "[ESTADO: Cambio" in cita.get('servicio', ''): continue
                                citas_hoy.append((dt_start, cita))
                        except Exception: pass
                
                citas_hoy.sort(key=lambda x: x[0])
                
                if citas_hoy:
                    for dt_start, cita in citas_hoy:
                        duracion = cita.get('duracion_minutos') if cita.get('duracion_minutos') is not None else 60
                        dt_end = dt_start + timedelta(minutes=duracion)
                        
                        masc_info = cita.get('mascotas') or {}
                        cli_info = masc_info.get('clientes') or {}
                        
                        mascota_nombre = masc_info.get('nombre', 'Cita')
                        especie = masc_info.get('especie', '')
                        raza = masc_info.get('raza', '')
                        dueno = cli_info.get('nombre_dueno', 'Sin dueño')
                        tel = cli_info.get('telefono', 'Sin tel')
                        
                        if especie: mascota_nombre += f" ({especie})"
                        if raza: mascota_nombre += f" - {raza}"
                        
                        estado_c, s_clean, assigned_e = parse_cita_estado(cita.get('servicio', ''))
                        emoji = EMOJIS_ESTADO.get(estado_c, "🟢")
                        
                        border_color = "#4caf50"
                        if "Cambio" in estado_c: border_color = "#2196f3"
                        elif "recogida" in estado_c.lower(): border_color = "#9c27b0"
                        elif "Pendiente" in estado_c: border_color = "#ffeb3b"
                        
                        html_week += f"<div class='cita-card' style='border-left-color: {border_color};'><b>{dt_start.strftime('%H:%M')}-{dt_end.strftime('%H:%M')}</b> {emoji}<br>🐾 {mascota_nombre}<br> {dueno} (📱 {tel})<br>✂️ {s_clean} <br>👩‍🦰 {assigned_e}</div>"
                else:
                    html_week += "<div style='color:#bbb; font-size:0.8em; text-align:center; margin-top:10px;'><i>Libre</i></div>"
                    
                html_week += "</td>"
            html_week += "</tr></table>"
            
        st.markdown(html_week, unsafe_allow_html=True)
            
    with sub_mensual:
        st.markdown("#### 📅 Calendario Mensual (Turnos y Volumen de Citas)")
        c_mes1, c_mes2, _ = st.columns([1, 1, 2])
        hoy_mes = pd.Timestamp.now('Atlantic/Canary').date()
        with c_mes1:
            meses_lista = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            mes_sel = st.selectbox("Mes:", range(1, 13), format_func=lambda x: meses_lista[x-1], index=hoy_mes.month-1)
        with c_mes2:
            anio_sel = st.selectbox("Año:", range(hoy_mes.year - 1, hoy_mes.year + 4), index=1)
            
        cal = calendar.monthcalendar(anio_sel, mes_sel)
        f_ini_mes = date(anio_sel, mes_sel, 1)
        _, last_day = calendar.monthrange(anio_sel, mes_sel)
        f_fin_mes = date(anio_sel, mes_sel, last_day)
        
        turnos_mes = get_turnos_ag_cached(client, st.session_state.get('db_version', 0), str(f_ini_mes), str(f_fin_mes))
        bloqueos_mes = get_bloqueos_ag_cached(client, st.session_state.get('db_version', 0), str(f_ini_mes), str(f_fin_mes))
        ferias_mes = get_ferias_ag_cached(client, st.session_state.get('db_version', 0), str(f_ini_mes), str(f_fin_mes))
        res_citas_mes_data = get_citas_mes_ag_cached(client, st.session_state.get('db_version', 0), f_ini_mes, f_fin_mes)
        
        citas_por_dia_mes = {}
        if res_citas_mes_data:
            for c in res_citas_mes_data:
                if "[ESTADO: Cancelada]" not in c.get('servicio', '') and "[ESTADO: No presentado]" not in c.get('servicio', '') and "[ESTADO: Anulada]" not in c.get('servicio', '') and "[ESTADO: Cambio" not in c.get('servicio', ''):
                    try:
                        d_str = c['fecha_hora'][:10]
                        if d_str not in citas_por_dia_mes:
                            citas_por_dia_mes[d_str] = []
                        citas_por_dia_mes[d_str].append(c)
                    except: pass
        
        dias_semana_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        html_cal = '''
        <style>
            .calendar-table { width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 14px; background-color: white; }
            .calendar-table th { background-color: #005275; color: white; padding: 8px; text-align: center; font-weight: bold; border: 1px solid #ddd; }
            .calendar-table td { border: 1px solid #ddd; vertical-align: top; padding: 8px; height: 130px; word-wrap: break-word; }
            .day-header { font-weight: bold; font-size: 1.1em; color: #333; margin-bottom: 8px; border-bottom: 1px solid #eee; padding-bottom: 4px; display: flex; justify-content: space-between; align-items: flex-start; }
            .day-header.festivo { color: #d32f2f; }
            .festivo-text { font-size: 0.7em; font-weight: normal; text-align: right; max-width: 60%; line-height: 1.1; }
            .turnos-bloque { font-size: 0.85em; color: #444; margin-bottom: 10px; line-height: 1.4; }
            .citas-bloque { font-size: 0.9em; font-weight: bold; color: #2e7d32; background-color: #e8f5e9; padding: 4px; border-radius: 4px; text-align: center; display: block; }
            .citas-vacio { font-size: 0.9em; color: #9e9e9e; background-color: #f5f5f5; padding: 4px; border-radius: 4px; text-align: center; display: block; }
            .td-empty { background-color: #f9f9f9; }
            .td-today { background-color: #fffde7; border: 2px solid #fbc02d !important; }
        </style>
        <table class="calendar-table">
            <tr>
        '''
        for dia_n in dias_semana_nombres:
            html_cal += f"<th>{dia_n}</th>"
        html_cal += "</tr>"
        
        hoy_str = str(pd.Timestamp.now('Atlantic/Canary').date())

        for semana in cal:
            html_cal += "<tr>"
            for i, dia in enumerate(semana):
                if dia == 0:
                    html_cal += "<td class='td-empty'></td>"
                else:
                    d_obj = date(anio_sel, mes_sel, dia)
                    d_str = str(d_obj)
                    festivo = es_festivo(d_obj)
                    
                    is_today = (d_str == hoy_str)
                    td_class = "td-today" if is_today else ""
                    
                    html_cal += f"<td class='{td_class}'>"
                    
                    header_class = "day-header festivo" if festivo else "day-header"
                    header_text = f"<span>{dia}</span><span class='festivo-text'>{festivo}</span>" if festivo else f"<span>{dia}</span>"
                    html_cal += f"<div class='{header_class}'>{header_text}</div>"
                        
                    t_hoy = [t for t in turnos_mes if t['fecha'] == d_str]
                    t_textos = []
                    for t in t_hoy:
                        nm = t.get('personal_empleados', {}).get('nombre', '') if t.get('personal_empleados') else ''
                        tr = t.get('turno', '')
                        if tr and tr.lower() not in ["", "libre", "vacaciones", "-"]:
                            t_textos.append(f"👥 <b>{nm}</b>: {tr}")
                    
                    t_bloque = "<br>".join(t_textos) if t_textos else "<i style='color:#bbb;'>Sin turnos</i>"
                    html_cal += f"<div class='turnos-bloque'>{t_bloque}</div>"
                    
                    b_hoy = [b for b in bloqueos_mes if b['fecha'] == d_str]
                    if b_hoy:
                        for b in b_hoy:
                            c_bloque = f"⛔ {b['titulo']} ({b['hora_inicio'][:5]})"
                            html_cal += f"<div class='turnos-bloque' style='color:#880e4f; font-weight:bold; background-color:#fce4ec; padding:2px; border-radius:3px; margin-top:2px;'>{c_bloque}</div>"
                    
                    # Ferias y Eventos (NUEVO)
                    f_hoy_mes = []
                    if ferias_mes:
                        for f in ferias_mes:
                            try:
                                f_ini = pd.to_datetime(f['fecha_inicio']).date()
                                f_fin = pd.to_datetime(f['fecha_fin']).date()
                                if f_ini <= d_obj <= f_fin: f_hoy_mes.append(f)
                            except: pass
                    if f_hoy_mes:
                        for f in f_hoy_mes: html_cal += f"<div class='turnos-bloque' style='color:#e65100; font-weight:bold; background-color:#fff3e0; padding:2px; border-radius:3px; margin-top:2px;'>🎪 {f['titulo']}</div>"

                    citas_hoy = citas_por_dia_mes.get(d_str, [])
                    if citas_hoy:
                        c_bloque = f"📝 {len(citas_hoy)} cita(s)"
                        html_cal += f"<div class='citas-bloque' style='margin-bottom:4px;'>{c_bloque}</div>"
                        
                        citas_hoy.sort(key=lambda x: x['fecha_hora'])
                        for ct in citas_hoy:
                            try:
                                hora_str = ct['fecha_hora'][11:16]
                                m_info = ct.get('mascotas') or {}
                                c_info = m_info.get('clientes') or {}
                                n_m = m_info.get('nombre', 'Mascota')
                                r_m = m_info.get('raza', '')
                                n_d = c_info.get('nombre_dueno', 'Sin dueño')
                                t_d = c_info.get('telefono', '')
                                
                                str_raza = f" ({r_m})" if r_m else ""
                                html_cal += f"<div style='font-size:0.75em; line-height:1.2; margin-top:2px; padding:3px; background-color:#e8f5e9; border-left: 2px solid #4caf50; border-radius:2px;'><b>{hora_str}</b> {n_m}{str_raza}<br><span style='color:#555;'>👤 {n_d} 📱 {t_d}</span></div>"
                            except: pass
                    else:
                        c_bloque = "Libre"
                        html_cal += f"<div class='citas-vacio'>{c_bloque}</div>"
                        
                    html_cal += "</td>"
            html_cal += "</tr>"
            
        html_cal += "</table>"
        st.markdown(html_cal, unsafe_allow_html=True)

    with sub_recordatorios:
        st.markdown("#### 🔔 Centro de Recordatorios (Citas y Mantenimiento)")
        st.info("Espacio centralizado para gestionar las confirmaciones de citas y mantenimientos diarios (vía WhatsApp o llamada telefónica).")
        
        # --- 1. CONFIRMACIONES DEL PRÓXIMO DÍA HÁBIL ---
        hoy_dt = pd.Timestamp.now('Atlantic/Canary').replace(tzinfo=None)
        manana_dt = hoy_dt + pd.Timedelta(days=1)
        
        # Si el próximo día es domingo (6), saltamos automáticamente al lunes
        if manana_dt.weekday() == 6:
            manana_dt += pd.Timedelta(days=1)
            
        dias_es = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}
        meses_es = {1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio", 7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"}
        nombre_dia_obj = dias_es[manana_dt.weekday()]
        
        st.markdown(f"##### 📅 1. Confirmaciones para el {nombre_dia_obj} ({manana_dt.strftime('%d/%m')})")
        
        manana_str_ini = manana_dt.strftime('%Y-%m-%d 00:00:00')
        manana_str_fin = manana_dt.strftime('%Y-%m-%d 23:59:59')
        
        res_manana_data = get_manana_ag_cached(client, st.session_state.get('db_version', 0), manana_str_ini, manana_str_fin)
        
        citas_manana = []
        if res_manana_data:
            for c in res_manana_data:
                estado_c, s_clean, assigned_e = parse_cita_estado(c.get('servicio', ''))
                if estado_c in ["Cancelada", "Anulada", "No presentado", "Asistió"]: continue
                
                obs_raw = c.get('observaciones') or ''
                import re
                m_aviso = re.search(r'\[RECORDATORIO:\s*(.*?)\]', obs_raw)
                aviso_status = m_aviso.group(1).strip() if m_aviso else "Sin avisar"

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
                
                citas_manana.append({
                    "id": c['id'],
                    "Aviso": aviso_status,
                    "Hora": hora_str,
                    "Mascota": nombre_m,
                    "Dueño": dueno + (" 🚚" if domicilio else ""),
                    "Servicio": s_clean,
                    "Canal Pref.": pref_contacto,
                    "WhatsApp": url_wa,
                    "Observaciones_Old": obs_raw
                })
                
        if citas_manana:
            df_manana = pd.DataFrame(citas_manana).sort_values("Hora")
            ed_manana = st.data_editor(
                df_manana[['id', 'Hora', 'Aviso', 'Mascota', 'Dueño', 'Servicio', 'Canal Pref.', 'WhatsApp', 'Observaciones_Old']],
                use_container_width=True, hide_index=True, key="ed_manana_ag",
                column_config={
                    "id": None,
                    "Observaciones_Old": None,
                    "Aviso": st.column_config.SelectboxColumn("🔔 Aviso", options=["Sin avisar", "Avisado"], required=True),
                    "WhatsApp": st.column_config.LinkColumn("📱 Acción Automática", display_text="💬 Recordatorio")
                }
            )
            
            if st.button("💾 Guardar Avisos de Mañana", type="primary"):
                import re
                for _, row in ed_manana.iterrows():
                    new_aviso = row['Aviso']
                    obs_old = row['Observaciones_Old']
                    
                    if '[RECORDATORIO:' in obs_old:
                        new_obs = re.sub(r'\[RECORDATORIO:\s*.*?\]', f'[RECORDATORIO: {new_aviso}]', obs_old)
                    else:
                        new_obs = (obs_old + f" [RECORDATORIO: {new_aviso}]").strip()
                        
                    client.table("citas").update({"observaciones": new_obs}).eq("id", row['id']).execute()
                    
                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                st.success("Avisos actualizados.")
                time.sleep(0.5)
                limpiar_cache_agenda()
                st.rerun()
        else:
            st.success(f"No hay citas para confirmar para el {nombre_dia_obj.lower()}.")

        st.markdown("---")
        
        # --- 2. RECORDATORIOS DE MANTENIMIENTO ---
        st.markdown("##### ✂️ 2. Recordatorios de Mantenimiento")
        st.markdown("<p style='color:gray; font-size:14px;'>Clientes que superan los días sin venir y <b>NO tienen ya una cita futura agendada</b>.</p>", unsafe_allow_html=True)
        
        c_al1, c_al2 = st.columns([1, 2])
        with c_al1:
            dias_aviso = st.slider("Mostrar mascotas sin venir en más de (días):", min_value=15, max_value=180, value=45, step=5)
        
        hoy_str = hoy_dt.strftime('%Y-%m-%d 00:00:00')
        res_futuras_data = get_futuras_ag_cached(client, st.session_state.get('db_version', 0), hoy_str)
        mascotas_con_cita = set()
        if res_futuras_data:
            for c in res_futuras_data:
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
        st.markdown("#### 🚫 Registro de Cancelaciones y Plantones")
        st.info("Aquí aparecen todas las citas que han sido marcadas como 'Cancelada', 'Anulada' o 'No presentado' desde el Directorio. Estas citas liberan su hueco automáticamente en la agenda para que puedas dárselo a otro.")
        canceladas = []
        res_canc_data = get_canc_ag_cached(client, st.session_state.get('db_version', 0))
        if res_canc_data:
            for c in res_canc_data:
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
        
        hoy_str = str(pd.Timestamp.now('Atlantic/Canary').date())
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