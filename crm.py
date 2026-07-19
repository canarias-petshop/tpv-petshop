import streamlit as st
import pandas as pd
import time
from datetime import date
import urllib.parse
import base64
import streamlit.components.v1 as components
from core_crm import crear_cliente, crear_mascota, actualizar_cliente, anonimizar_cliente, crear_encargo, agendar_cita

@st.cache_data(show_spinner=False, ttl=300)
def fetch_empleados_crm(_client):
    return _client.table("personal_empleados").select("id, nombre").eq("activo", True).execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_servicios_crm(_client):
    return _client.table("productos").select("nombre, precio_pvp, precio_base").eq("categoria", "Servicio").order("nombre").execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_citas_dia_crm(_client, fecha_inicio_q, fecha_fin_q):
    return _client.table("citas").select("fecha_hora, duracion_minutos, servicio").gte("fecha_hora", fecha_inicio_q).lte("fecha_hora", fecha_fin_q).execute()

class CRMResult: pass

@st.cache_data(show_spinner=False, ttl=300)
def fetch_turnos_dia_crm(_client, f_fecha_str):
    turnos = _client.table("personal_cuadrantes").select("*").eq("fecha", f_fecha_str).execute().data or []
    empleados = fetch_empleados_crm(_client).data or []
    emp_dict = {e['id']: e for e in empleados}
    for t in turnos: t['personal_empleados'] = emp_dict.get(t.get('empleado_id'))
    res = CRMResult()
    res.data = turnos
    return res

@st.cache_data(show_spinner=False, ttl=300)
def fetch_encargos_crm(_client):
    _all = []
    _off = 0
    while True:
        _r = _client.table("encargos_clientes").select("id, created_at, nombre_cliente, telefono, detalle_pedido, notas, estado, origen").order("created_at", desc=True).range(_off, _off + 999).execute()
        if _r.data:
            _all.extend(_r.data)
            if len(_r.data) < 1000: break
            _off += 1000
        else: break
    return _all

@st.cache_data(show_spinner=False, ttl=300)
def fetch_deudas_crm(_client):
    return _client.table("ventas_historial").select("id, created_at, cliente_deuda, pendiente, total, pagado").eq("estado", "Deuda").execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_clientes_deuda_crm(_client):
    _all_cli_d = []
    offset = 0
    while True:
        r_cli_d = _client.table("clientes").select("nombre_dueno, telefono").range(offset, offset + 999).execute()
        if r_cli_d.data:
            _all_cli_d.extend(r_cli_d.data)
            if len(r_cli_d.data) < 1000: break
            offset += 1000
        else: break
    return _all_cli_d

@st.cache_data(show_spinner=False, ttl=300)
def fetch_bancos_crm(_client):
    return _client.table("cuentas_bancarias").select("id, nombre_banco, saldo_actual").execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_caja_abierta_crm(_client):
    return _client.table("control_caja").select("id").eq("estado", "Abierta").execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_cliente_puntos_crm(_client, cli_saldar):
    return _client.table("clientes").select("id, puntos").eq("nombre_dueno", cli_saldar).execute()

@st.cache_data(show_spinner=False, ttl=300)
def get_cli_crm(_client):
    _all = []
    _off = 0
    while True:
        _r = _client.table("clientes").select("*").order("created_at", desc=True).range(_off, _off + 999).execute()
        if _r.data:
            _all.extend(_r.data)
            if len(_r.data) < 1000: break
            _off += 1000
        else: break
        
    try:
        from collections import defaultdict
        masc_dict = defaultdict(list)
        m_all = []
        m_off = 0
        while True:
            m_r = _client.table("mascotas").select("*").range(m_off, m_off + 999).execute()
            if m_r.data:
                m_all.extend(m_r.data)
                if len(m_r.data) < 1000: break
                m_off += 1000
            else: break
            
        for m in m_all:
            if 'cliente_id' in m:
                masc_dict[m['cliente_id']].append(m)
                
        for cli in _all:
            cli['mascotas'] = masc_dict.get(cli.get('id'), [])
    except Exception as e:
        # Fallback in case of error: initialize empty mascotas
        for cli in _all:
            cli['mascotas'] = []
            
    return _all

@st.cache_data(show_spinner=False, ttl=300)
def get_masc_crm(_client):
    _all = []
    _off = 0
    while True:
        _r = _client.table("mascotas").select("*").order("id", desc=True).range(_off, _off + 999).execute()
        if _r.data:
            _all.extend(_r.data)
            if len(_r.data) < 1000: break
            _off += 1000
        else: break
        
    _c_all = []
    _c_off = 0
    while True:
        _c_r = _client.table("clientes").select("id, nombre_dueno, telefono").range(_c_off, _c_off + 999).execute()
        if _c_r.data:
            _c_all.extend(_c_r.data)
            if len(_c_r.data) < 1000: break
            _c_off += 1000
        else: break
        
    c_dict = {c['id']: c for c in _c_all}
    for m in _all: m['clientes'] = c_dict.get(m.get('cliente_id'))
    return _all

def limpiar_cache_crm():
    fetch_empleados_crm.clear()
    fetch_servicios_crm.clear()
    fetch_citas_dia_crm.clear()
    fetch_turnos_dia_crm.clear()
    fetch_encargos_crm.clear()
    fetch_deudas_crm.clear()
    fetch_clientes_deuda_crm.clear()
    fetch_bancos_crm.clear()
    fetch_caja_abierta_crm.clear()
    fetch_cliente_puntos_crm.clear()
    get_cli_crm.clear()
    get_masc_crm.clear()

def render_pestana_crm(client):
    if 'crm_toast' in st.session_state:
        st.toast(st.session_state.pop('crm_toast'), icon="✅")
    if 'llave_crm_cli' not in st.session_state: st.session_state.llave_crm_cli = 0
    if 'llave_crm_masc' not in st.session_state: st.session_state.llave_crm_masc = 0
    if 'llave_crm_enc' not in st.session_state: st.session_state.llave_crm_enc = 0
    if 'llave_crm_dom' not in st.session_state: st.session_state.llave_crm_dom = 0

    st.markdown("<h3 style='margin-bottom: 5px;'>👥 Gestión de Clientes y Mascotas</h3>", unsafe_allow_html=True)
    
    try:
        emp_res = fetch_empleados_crm(client)
        empleados_lista = [e['nombre'] for e in emp_res.data] if emp_res.data else []
    except:
        empleados_lista = []
            
    try:
        serv_res = fetch_servicios_crm(client)
        if serv_res.data:
            servicios_lista = [s['nombre'] for s in serv_res.data] + ["Otro"]
            precios_servicios = {s['nombre']: float(s.get('precio_pvp') or s.get('precio_base') or 0.0) for s in serv_res.data}
        else:
            servicios_lista = ["Peluquería", "Otro"]
            precios_servicios = {}
    except:
        servicios_lista = ["Otro"]
        precios_servicios = {}

    col_c1, col_c2 = st.columns([1.2, 2.5])

    with col_c1:
        st.markdown("#### 👤 Nuevo Cliente")
        with st.form("nuevo_cliente", clear_on_submit=True):
            c_nom = st.text_input("Nombre del Contacto Principal *", key=f"nc_nom_{st.session_state.llave_crm_cli}")
            c_t1, c_t2 = st.columns(2)
            with c_t1: c_tel = st.text_input("Tel. Principal (Avisos) *", key=f"nc_tel_{st.session_state.llave_crm_cli}")
            with c_t2: c_cont = st.selectbox("Canal Preferido", ["WhatsApp", "Llamada", "SMS"], key=f"nc_cont_{st.session_state.llave_crm_cli}")
            
            st.markdown("<p style='margin: 0; font-size: 13px; color: gray;'>Segundo contacto (Opcional)</p>", unsafe_allow_html=True)
            c_t3, c_t4 = st.columns(2)
            with c_t3: c_nom2 = st.text_input("Nombre Contacto Alt.", key=f"nc_nom2_{st.session_state.llave_crm_cli}")
            with c_t4: c_tel2 = st.text_input("Teléfono Alt.", key=f"nc_tel2_{st.session_state.llave_crm_cli}")
            c_ema = st.text_input("Email", key=f"nc_ema_{st.session_state.llave_crm_cli}")
            
            c_d1, c_d2 = st.columns(2)
            with c_d1: c_dir = st.text_input("Dirección (Para recogidas a domicilio)", key=f"nc_dir_{st.session_state.llave_crm_cli}")
            with c_d2: c_nac = st.date_input("F. Nacimiento", value=None, key=f"nc_nac_{st.session_state.llave_crm_cli}")
            
            c_domicilio = st.checkbox("🚚 Recogida a Domicilio", key=f"nc_dom_{st.session_state.llave_crm_cli}")
            c_rgpd = st.checkbox("📝 Acepta LOPD/RGPD (Envío info y promos)", value=True, key=f"nc_rgpd_{st.session_state.llave_crm_cli}")
            
            st.markdown("<hr style='margin: 5px 0px; border: none; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)
            st.markdown("<p style='margin: 0; font-size: 13px; color: gray;'>🐾 Añadir mascota (Deja en blanco si es solo cliente de tienda)</p>", unsafe_allow_html=True)
            
            cm1, cm2, cm3 = st.columns([2, 1.5, 1.5])
            with cm1: m_nom = st.text_input("Nombre de la mascota", key=f"nm_nom_{st.session_state.llave_crm_cli}")
            with cm2: m_esp = st.selectbox("Especie", ["", "Perro", "Gato", "Ave", "Roedor", "Reptil", "Otro"], key=f"nm_esp_{st.session_state.llave_crm_cli}")
            with cm3: m_sexo = st.selectbox("Sexo", ["", "Macho", "Hembra"], key=f"nm_sexo_{st.session_state.llave_crm_cli}")
            
            cm4, cm5, cm6 = st.columns([2, 1.5, 1.5])
            with cm4: m_raz = st.text_input("Raza", key=f"nm_raz_{st.session_state.llave_crm_cli}")
            with cm5: m_nac = st.date_input("Nacimiento Mascota", value=None, key=f"nm_nac_{st.session_state.llave_crm_cli}")
            with cm6: m_peso = st.text_input("Peso", placeholder="Ej: 15 kg", key=f"nm_peso_{st.session_state.llave_crm_cli}")
            
            c_obs1, c_obs2 = st.columns([2.5, 1.5])
            with c_obs1: m_obs = st.text_input("Observaciones (Alergias, carácter...)", key=f"nm_obs_{st.session_state.llave_crm_cli}")
            with c_obs2: m_pref = st.selectbox("Peluquero/a Pref.", ["Cualquiera"] + empleados_lista, key=f"nm_pref_{st.session_state.llave_crm_cli}")

            if st.form_submit_button("💾 Guardar Ficha", type="primary", use_container_width=True):
                if c_nom:
                    nuevo_cli = crear_cliente(
                        client, c_nom, c_tel, c_nom2, c_tel2, c_ema, c_cont, 
                        str(c_nac) if c_nac else "", c_rgpd, c_dir, c_domicilio
                    )

                    if nuevo_cli and m_nom:
                        final_obs = f"[Pref: {m_pref}] {m_obs}".strip() if m_pref != "Cualquiera" else m_obs
                        crear_mascota(
                            client, nuevo_cli['id'], m_nom, m_esp, m_sexo, m_raz, m_peso, 
                            final_obs, str(m_nac) if m_nac else ""
                        )

                    st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                    st.session_state.llave_crm_cli += 1
                    limpiar_cache_crm()
                    st.success("Cliente guardado correctamente"); time.sleep(0.5); st.rerun()
                else:
                    st.warning("El nombre del dueño es obligatorio.")

    with col_c2:
        # Función para calcular la edad visualmente
        def calcular_edad(fecha_str):
            try:
                nac = pd.to_datetime(fecha_str)
                hoy = pd.Timestamp.now('Atlantic/Canary')
                anios = hoy.year - nac.year - ((hoy.month, hoy.day) < (nac.month, nac.day))
                if anios == 0:
                    meses = hoy.month - nac.month - ((hoy.day) < (nac.day))
                    if meses < 0: meses += 12
                    return f"{meses} meses"
                return f"{anios} años"
            except: return ""

        def aproximar_fecha_desde_edad(edad_str, fecha_actual):
            if not edad_str: return fecha_actual
            try:
                import re
                edad_str = str(edad_str).strip().lower()
                match = re.search(r'\d+', edad_str)
                if not match: return fecha_actual
                num = int(match.group())
                hoy = pd.Timestamp.now('Atlantic/Canary')
                if "mes" in edad_str:
                    return (hoy - pd.DateOffset(months=num)).strftime('%Y-%m-%d')
                else:
                    return (hoy - pd.DateOffset(years=num)).strftime('%Y-%m-%d')
            except:
                return fecha_actual

        def get_pref(obs):
            import re
            m = re.search(r'\[Pref:\s*(.*?)\]', str(obs))
            return m.group(1) if m else "Cualquiera"

        def strip_pref(obs):
            import re
            return re.sub(r'\[Pref:\s*.*?\]\s*', '', str(obs)).strip()

        def calcular_duracion_media(historial):
            """Calcula la duración media de los servicios a partir del historial JSON."""
            if not isinstance(historial, list) or not historial:
                return "N/A"
            
            duraciones = [t['Duración (min)'] for t in historial if isinstance(t, dict) and isinstance(t.get('Duración (min)'), (int, float))]
            
            if not duraciones:
                return "N/A"
                
            media = sum(duraciones) / len(duraciones)
            return f"{int(media)} min"

        def mostrar_ficha_clinica(m_id, m_nombre, m_data, prefix):
            from ficha_clinica import mostrar_ficha_clinica as render_ficha_base
            render_ficha_base(m_id, m_nombre, m_data, prefix, client, servicios_lista, empleados_lista, precios_servicios)
            
            st.markdown(f"#### 📅 Agendar Cita Inteligente para **{m_nombre}**")
            st.markdown("<p style='color: gray; font-size: 13px;'>El sistema calcula automáticamente los huecos libres (09:00 a 21:00) para la fecha y duración seleccionadas.</p>", unsafe_allow_html=True)
            
            c_cal1, c_cal2, c_cal3 = st.columns([1, 1, 1])
            with c_cal1: f_fecha = st.date_input("1. Fecha de cita:", value=pd.Timestamp.now('Atlantic/Canary').date(), key=f"fcita_{prefix}_{m_id}")
            with c_cal2: f_dur = st.number_input("2. Duración (min)", min_value=5, max_value=300, value=60, step=5, key=f"fdur_{prefix}_{m_id}")
            
            pref_actual = get_pref(m_data.get('observaciones', ''))
            opciones_emp = ["Cualquiera"] + empleados_lista
            def_index = opciones_emp.index(pref_actual) if pref_actual in opciones_emp else 0
            
            with c_cal3: f_emp = st.selectbox("3. Peluquera/o:", opciones_emp, index=def_index, key=f"femp_{prefix}_{m_id}")
            
            fecha_inicio_q = f"{f_fecha}T00:00:00"
            fecha_fin_q = f"{f_fecha}T23:59:59"
            res_citas = fetch_citas_dia_crm(client, fecha_inicio_q, fecha_fin_q)
            citas_dia = res_citas.data if res_citas.data else []
            
            from ficha_clinica import fetch_ficha_alerts_cached
            _, r_canc = fetch_ficha_alerts_cached(client, st.session_state.get('db_version', 0), m_id, str(pd.Timestamp.now('Atlantic/Canary').date()))
            strikes = len(r_canc) if r_canc else 0
            
            # Obtener todos los turnos del día
            res_turnos = fetch_turnos_dia_crm(client, str(f_fecha))
            turnos_dict = {}
            if res_turnos.data:
                for t in res_turnos.data:
                    if t.get('personal_empleados'):
                        turnos_dict[t['personal_empleados']['nombre']] = t['turno'].lower()
                        
            empleados_a_revisar = [f_emp] if f_emp != "Cualquiera" else empleados_lista
            huecos_obj = []
            
            for emp_nombre in empleados_a_revisar:
                turno_str = turnos_dict.get(emp_nombre, "")
                if not turno_str or "libre" in turno_str or "vacaciones" in turno_str:
                    continue
                    
                import re
                times = re.findall(r'(\d{1,2}:\d{2})', turno_str)
                if len(times) >= 2:
                    h_ini = pd.to_datetime(f"{f_fecha} {times[0]}")
                    h_fin = pd.to_datetime(f"{f_fecha} {times[1]}")
                else:
                    if f_fecha.weekday() < 5:
                        h_ini = pd.to_datetime(f"{f_fecha} 09:00")
                        h_fin = pd.to_datetime(f"{f_fecha} 21:00")
                    else:
                        h_ini = pd.to_datetime(f"{f_fecha} 10:00")
                        h_fin = pd.to_datetime(f"{f_fecha} 14:00")
                    
                for h in range(0, 24):
                    for m in range(0, 60, 5):
                        dt_ini = pd.to_datetime(f"{f_fecha} {h:02d}:{m:02d}")
                        if dt_ini < h_ini: continue
                        dt_fin = dt_ini + pd.Timedelta(minutes=f_dur)
                        if dt_fin > h_fin: continue
                        
                        solapa = False
                        for c in citas_dia:
                            if "[ESTADO: Cancelada]" in c.get('servicio', '') or "[ESTADO: Anulada]" in c.get('servicio', '') or "[ESTADO: No presentado]" in c.get('servicio', ''): continue
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
                        if not solapa:
                            huecos_obj.append({"dt": dt_ini, "hora": f"{h:02d}:{m:02d}", "emp": emp_nombre})
            
            huecos_obj.sort(key=lambda x: x["dt"])
            huecos_formateados = [f"{x['hora']} (Con {x['emp']})" for x in huecos_obj]
            huecos_formateados.append("Asignación Manual")

            if len(huecos_formateados) == 1:
                st.error("🔴 No hay huecos disponibles para esta selección o están de descanso.")
                
            with st.form(f"form_cita_{prefix}_{m_id}", border=True):
                fc_1, fc_2 = st.columns([1, 2])
                with fc_1: 
                    f_hora_sel = st.selectbox("4. Hora de inicio:", huecos_formateados)
                    f_hora_manual = None
                    if f_hora_sel == "Asignación Manual":
                        f_hora_manual = st.time_input("Hora manual")
                with fc_2: 
                    f_serv = st.selectbox("5. Servicio:", servicios_lista)
                
                solapa_manual = False
                motivo_solape = ""
                motivo_extra = ""
                
                if f_hora_sel == "Asignación Manual" and f_hora_manual:
                    dt_ini_man = pd.to_datetime(f"{f_fecha} {f_hora_manual.strftime('%H:%M')}")
                    dt_fin_man = dt_ini_man + pd.Timedelta(minutes=f_dur)
                    for c in citas_dia:
                        if "[ESTADO: Cancelada]" in c.get('servicio', '') or "[ESTADO: Anulada]" in c.get('servicio', '') or "[ESTADO: No presentado]" in c.get('servicio', ''): continue
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
                        st.warning("⚠️ La hora seleccionada ya está ocupada o hay citas sin asignar.")
                        motivo_solape = st.selectbox("Motivo para forzar la cita: *", ["", "Tenemos otro peluquero disponible", "Se va a ayudar con la peluquería", "Se puede hacer a la vez", "Otro motivo"], key=f"mot_{prefix}_{m_id}")
                        if motivo_solape == "Otro motivo":
                            motivo_extra = st.text_input("Especificar otro motivo: *", key=f"mote_{prefix}_{m_id}")

                if strikes >= 2:
                    st.error(f"🚨 **CLIENTE REINCIDENTE ({strikes} faltas):** Por política, es obligatorio cobrar fianza o pago por adelantado para agendar.")
                    fianza_pagada = st.checkbox("✅ Confirmo cobro de fianza o pago por adelantado", key=f"fianza_{prefix}_{m_id}")
                else:
                    fianza_pagada = False

                if st.form_submit_button("➕ Confirmar Cita", type="primary", use_container_width=True):
                    if solapa_manual and (not motivo_solape or (motivo_solape == "Otro motivo" and not motivo_extra)):
                        st.error("Debes indicar un motivo para forzar la cita en una hora ocupada.")
                    elif strikes >= 2 and not fianza_pagada:
                        st.error("Debes confirmar el cobro de la fianza para poder agendar a este cliente.")
                    else:
                        if f_hora_sel == "Asignación Manual":
                            hora_final_str = f_hora_manual.strftime('%H:%M')
                            emp_final = f_emp if f_emp != "Cualquiera" else ""
                        else:
                            hora_final_str = f_hora_sel.split(" (")[0]
                            emp_final = f_hora_sel.split("(Con ")[1].replace(")", "")
                            
                        servicio_final = f"{f_serv} ({emp_final})" if emp_final else f_serv
                        if solapa_manual:
                            motivo_final = motivo_extra if motivo_solape == "Otro motivo" else motivo_solape
                            servicio_final += f" [Forzado: {motivo_final}]"
                            
                        if fianza_pagada:
                            servicio_final = f"[ESTADO: Pendiente] [💰 FIANZA PAGADA] {servicio_final}"
                        else:
                            servicio_final = f"[ESTADO: Pendiente] {servicio_final}"
                            
                        agendar_cita(
                            client, m_id, str(f_fecha), hora_final_str, 
                            f_serv, int(f_dur), emp_final, 
                            solapa_manual, motivo_final if solapa_manual else "", 
                            fianza_pagada
                        )
                        st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                        limpiar_cache_crm()
                        st.success("¡Cita reservada con éxito!"); time.sleep(1); st.rerun()

        seccion_crm = st.radio("Sección CRM:", ["👤 Directorio de Clientes", "🐾 Mascotas", "🛍️ Encargos", "💸 Pagos Pendientes"], horizontal=True, label_visibility="collapsed")
        
        all_cli = get_cli_crm(client)
        class DummyRes: pass
        res_clientes = DummyRes()
        res_clientes.data = all_cli
        
        if "Directorio de Clientes" in seccion_crm:
            
            if res_clientes.data:
                df_cli = pd.DataFrame(res_clientes.data)
                
                # --- MÉTRICAS DE CLIENTES ---
                total_clientes = len(df_cli)
                clientes_con_mascota = sum(1 for c in res_clientes.data if c.get('mascotas') and len(c['mascotas']) > 0)
                clientes_sin_mascota = total_clientes - clientes_con_mascota
                
                c_met1, c_met2, c_met3 = st.columns(3)
                with c_met1: st.metric("👥 Total Clientes", total_clientes)
                with c_met2: st.metric("🐾 Con Mascota", clientes_con_mascota)
                with c_met3: st.metric("🛍️ Solo Tienda", clientes_sin_mascota)
                st.markdown("<hr style='margin: 5px 0px 15px 0px; border: none; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

                c_busqc1, c_busqc2 = st.columns([2, 1])
                with c_busqc1:
                    b_cli = st.text_input("🔍 Buscar cliente (Nombre o Teléfono):", placeholder="Escribe para filtrar...", key="b_cli").strip().lower()
                with c_busqc2:
                    ord_cli = st.selectbox("↕️ Ordenar por:", ["Más recientes", "Nombre (A-Z)", "Mayor saldo de puntos"], key="ord_cli")
                
                if 'fecha_nacimiento' not in df_cli.columns: df_cli['fecha_nacimiento'] = ""
                if 'metodo_contacto' not in df_cli.columns: df_cli['metodo_contacto'] = "WhatsApp"
                
                if 'nombre_dueno_2' not in df_cli.columns: df_cli['nombre_dueno_2'] = ""
                if 'telefono_2' not in df_cli.columns: df_cli['telefono_2'] = ""
                if 'direccion' not in df_cli.columns: df_cli['direccion'] = ""
                if 'servicio_domicilio' not in df_cli.columns: df_cli['servicio_domicilio'] = False
                
                if 'created_at' in df_cli.columns:
                    # Parseo robusto: Lee formatos mixtos y si alguna celda está 100% vacía por la importación, le asigna la fecha actual para no perder el dato.
                    fechas_dt = pd.to_datetime(df_cli['created_at'], utc=True, format='mixed', errors='coerce')
                    df_cli['Fecha Creación'] = fechas_dt.fillna(pd.Timestamp('today', tz='UTC')).dt.date
                else:
                    df_cli['Fecha Creación'] = None
                
                df_cli['Tipo Cliente'] = df_cli['mascotas'].apply(lambda x: "🐾 Con mascota" if isinstance(x, list) and len(x) > 0 else "🛍️ Solo tienda")
                df_cli_vista = df_cli[['id', 'nombre_dueno', 'telefono', 'nombre_dueno_2', 'telefono_2', 'email', 'metodo_contacto', 'direccion', 'fecha_nacimiento', 'Fecha Creación', 'Tipo Cliente']].copy()
                
                if b_cli:
                    df_cli_vista = df_cli_vista[
                        df_cli_vista['nombre_dueno'].str.lower().str.contains(b_cli, na=False) |
                        df_cli_vista['telefono'].astype(str).str.contains(b_cli, na=False) |
                        df_cli_vista['nombre_dueno_2'].str.lower().str.contains(b_cli, na=False) |
                        df_cli_vista['telefono_2'].astype(str).str.contains(b_cli, na=False)
                    ]
                
                # Aseguramos columnas nuevas por si acaban de ejecutarse en SQL
                if 'rgpd_consent' not in df_cli.columns: df_cli['rgpd_consent'] = True
                if 'puntos' not in df_cli.columns: df_cli['puntos'] = 0
                
                df_cli_vista['RGPD'] = df_cli['rgpd_consent']
                df_cli_vista['Puntos'] = df_cli['puntos']
                df_cli_vista['Domicilio'] = df_cli['servicio_domicilio']

                if ord_cli == "Nombre (A-Z)":
                    df_cli_vista = df_cli_vista.sort_values(by="nombre_dueno", key=lambda col: col.fillna('').astype(str).str.lower())
                elif ord_cli == "Mayor saldo de puntos":
                    df_cli_vista = df_cli_vista.sort_values(by="Puntos", ascending=False)

                df_cli_vista.insert(0, "Ver", False)
                st.markdown("💡 *Marca la casilla **'👁️ Ver'** para abrir la ficha del cliente y ver sus mascotas.*")
                
                ed_cli = st.data_editor(
                    df_cli_vista,
                    column_config={
                        "Ver": st.column_config.CheckboxColumn("👁️ Ver", default=False), 
                        "id": None, "nombre_dueno": "Contacto Principal", "telefono": "Tel. Principal", 
                        "nombre_dueno_2": "Contacto Alt.", "telefono_2": "Tel. Alt.",
                        "email": "Email", "metodo_contacto": st.column_config.SelectboxColumn("Canal Pref.", options=["WhatsApp", "Llamada", "SMS"]), "fecha_nacimiento": "F. Nac",
                        "direccion": "Dirección",
                        "Fecha Creación": st.column_config.DateColumn("F. Alta", format="DD/MM/YYYY"),
                        "RGPD": st.column_config.CheckboxColumn("LOPD"),
                        "Puntos": st.column_config.NumberColumn("🌟 Ptos"),
                        "Domicilio": st.column_config.CheckboxColumn("🚚 Domicilio"),
                        "Tipo Cliente": st.column_config.TextColumn("Perfil", disabled=True)
                    },
                    use_container_width=True, hide_index=True, num_rows="dynamic", key=f"ed_clientes_{st.session_state.get('db_version', 0)}", height=250
                )
                if st.button("💾 Guardar Cambios en Clientes", type="primary"):
                    ed_cli_clean = ed_cli.drop(columns=["Ver", "Tipo Cliente"])
                    ids_actuales = ed_cli_clean['id'].dropna().tolist()
                    ids_orig = df_cli_vista['id'].tolist()
                    for id_b in [i for i in ids_orig if i not in ids_actuales]: client.table("clientes").delete().eq("id", id_b).execute()
                    
                    for _, row in ed_cli_clean.iterrows():
                        if pd.notna(row['id']):
                            orig_match = df_cli_vista[df_cli_vista['id'] == row['id']]
                            if not orig_match.empty:
                                orig_row = orig_match.iloc[0]
                                cambiado = False
                                for col in ['nombre_dueno', 'telefono', 'email', 'fecha_nacimiento', 'direccion', 'RGPD', 'Puntos', 'Domicilio']:
                                    if col in row and col in orig_row:
                                        if str(row.get(col, '')).strip() != str(orig_row.get(col, '')).strip():
                                            cambiado = True
                                            break
                                if not cambiado:
                                    continue
                                    
                            datos_update = {
                                "nombre_dueno": str(row['nombre_dueno']), "telefono": str(row['telefono']),
                                "nombre_dueno_2": str(row.get('nombre_dueno_2', '')), "telefono_2": str(row.get('telefono_2', '')),
                                "email": str(row['email']), "metodo_contacto": str(row.get('metodo_contacto', 'WhatsApp')), 
                                "fecha_nacimiento": str(row['fecha_nacimiento']),
                                "direccion": str(row.get('direccion', '')),
                                "rgpd_consent": bool(row.get('RGPD', True)), "puntos": int(row.get('Puntos', 0)),
                                "servicio_domicilio": bool(row.get('Domicilio', False))
                            }
                            if pd.notna(row.get('Fecha Creación')):
                                datos_update["created_at"] = str(row['Fecha Creación'])
                                
                            client.table("clientes").update(datos_update).eq("id", row['id']).execute()
                    st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                    limpiar_cache_crm()
                    st.session_state["crm_toast"] = "Directorio de clientes actualizado."; time.sleep(0.5); st.rerun()
                    
                st.markdown("---")
                
                # --- FICHA COMPLETA DEL DUEÑO Y SUS MASCOTAS ---
                filas_c_marcadas = ed_cli[ed_cli["Ver"] == True]
                if not filas_c_marcadas.empty:
                    c_id = filas_c_marcadas.iloc[0]['id']
                    c_data = df_cli[df_cli['id'] == c_id].iloc[0]
                    c_nombre = c_data['nombre_dueno']

                    mascotas_lista = c_data.get('mascotas', [])
                    ahorro_total = 0.0
                    import re
                    if isinstance(mascotas_lista, list):
                        for m in mascotas_lista:
                            hist = m.get('historial_trabajos')
                            if isinstance(hist, list):
                                for t in hist:
                                    nota = str(t.get('Nota Sesión', ''))
                                    # Detecta el ahorro tanto en el formato antiguo como en el nuevo
                                    m_ahorro = re.search(r'Ahorro:\s*([\d.]+)€\]', nota)
                                    if m_ahorro:
                                        try: ahorro_total += float(m_ahorro.group(1))
                                        except: pass

                    col_ficha1, col_ficha2 = st.columns([3, 1])
                    with col_ficha1:
                        st.markdown(f"#### 📖 Ficha de Cliente: **{c_nombre}**")
                        if ahorro_total > 0:
                            st.success(f"💰 **Ahorro Acumulado:** Este cliente ha ahorrado un total de **{ahorro_total:.2f}€** en mantenimientos.")
                            c_tel = ''.join(filter(str.isdigit, str(c_data.get('telefono', ''))))
                            if c_tel:
                                if len(c_tel) == 9 and not c_tel.startswith('34'): c_tel = '34' + c_tel
                                msg_ahorro = f"¡Hola {c_nombre}! 🐾 Te escribimos de Animalarium para agradecerte tu confianza. Gracias a traer a tu mascota a sus citas de mantenimiento a tiempo, ya llevas acumulado un ahorro total de {ahorro_total:.2f}€. ¡Sigue así! Un saludo."
                                url_wa = f"https://api.whatsapp.com/send?phone={c_tel}&text={urllib.parse.quote(msg_ahorro)}"
                                st.markdown(f"<a href='{url_wa}' target='_blank' style='text-decoration:none;'><div style='background-color:#25D366; color:white; padding:6px 12px; border-radius:6px; display:inline-block; font-size:14px; font-weight:bold;'>📱 Enviar WhatsApp de Ahorro</div></a>", unsafe_allow_html=True)

                    with col_ficha2:
                        if st.button("🗑️ Anonimizar Cliente (RGPD)", help="Borra los datos personales manteniendo el historial de ventas", type="secondary", key=f"anon_cli_{c_id}"):
                            anonimizar_cliente(client, c_id)
                            st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                            limpiar_cache_crm()
                            st.success("Cliente anonimizado con éxito según la ley de protección de datos."); time.sleep(1.5); st.rerun()
                    
                    mascotas_lista = c_data.get('mascotas', [])
                    if isinstance(mascotas_lista, list) and len(mascotas_lista) > 0:
                        df_mc = pd.DataFrame(mascotas_lista)
                        if 'fecha_nacimiento' not in df_mc.columns: df_mc['fecha_nacimiento'] = ""
                        df_mc['Edad'] = df_mc['fecha_nacimiento'].apply(calcular_edad)
                        if 'historial_trabajos' not in df_mc.columns: df_mc['historial_trabajos'] = [[] for _ in range(len(df_mc))]
                        df_mc['Duración Media'] = df_mc['historial_trabajos'].apply(calcular_duracion_media)
                        
                        cols_ok = ['id', 'nombre', 'especie', 'sexo', 'raza', 'peso', 'fecha_nacimiento', 'Edad', 'Duración Media', 'observaciones']
                        for col in cols_ok:
                            if col not in df_mc.columns: df_mc[col] = ""
                            
                        df_mc['Pref'] = df_mc['observaciones'].apply(get_pref)
                        df_mc['observaciones'] = df_mc['observaciones'].apply(strip_pref)
                        cols_ok.insert(9, 'Pref')
                            
                        df_mc_show = df_mc[cols_ok].rename(columns={
                            "nombre": "Nombre Mascota", "especie": "Especie", "sexo": "Sexo", "raza": "Raza", 
                            "peso": "Peso", "fecha_nacimiento": "F. Nacimiento", "observaciones": "Observaciones"
                        })
                        
                        df_mc_show.insert(0, "Ver Ficha", False)
                        st.markdown("💡 *Edita los datos directamente. Para eliminar, selecciona la fila y pulsa 'Supr'. Marca **'👁️ Ver Ficha'** para abrir el historial y agendar.*")
                        ed_mc = st.data_editor(
                            df_mc_show, use_container_width=True, hide_index=True, num_rows="dynamic", key=f"ed_mc_{c_id}_{st.session_state.get('db_version', 0)}",
                            column_config={
                                "Ver Ficha": st.column_config.CheckboxColumn("👁️ Ver Ficha", default=False),
                                "Pref": st.column_config.SelectboxColumn("Peluquero/a Pref.", options=["Cualquiera"] + empleados_lista),
                                "Sexo": st.column_config.SelectboxColumn("Sexo", options=["", "Macho", "Hembra"]),
                                "id": None, "Edad": st.column_config.TextColumn("Edad (Editable)", disabled=False, help="Escribe '5 años' o '6 meses' si no conoces la fecha exacta."), "Duración Media": st.column_config.TextColumn(disabled=True)
                            }
                        )
                        
                        if st.button("💾 Guardar Cambios en Mascotas de esta Familia", key=f"btn_save_mc_{c_id}"):
                            # 1. Detectar si el usuario ha borrado filas con la papelera o Supr
                            ids_actuales = ed_mc['id'].dropna().tolist()
                            ids_orig = df_mc_show['id'].dropna().tolist()
                            ids_a_borrar = [i for i in ids_orig if i not in ids_actuales]
                            for id_del in ids_a_borrar:
                                client.table("mascotas").delete().eq("id", id_del).execute()
                                
                            # 2. Actualizar mascotas existentes o insertar las nuevas
                            for _, ru in ed_mc.iterrows():
                                nueva_fecha_mc = str(ru['F. Nacimiento']) if pd.notna(ru['F. Nacimiento']) else ""
                                if pd.notna(ru['id']):
                                    orig_match = df_mc_show[df_mc_show['id'] == ru['id']]
                                    if not orig_match.empty:
                                        orig_ru = orig_match.iloc[0]
                                        if str(ru.get('Edad', '')) != str(orig_ru.get('Edad', '')) and str(ru.get('F. Nacimiento', '')) == str(orig_ru.get('F. Nacimiento', '')):
                                            nueva_fecha_mc = aproximar_fecha_desde_edad(ru.get('Edad', ''), nueva_fecha_mc)
                                elif ru.get('Edad', '') and not nueva_fecha_mc:
                                    nueva_fecha_mc = aproximar_fecha_desde_edad(ru.get('Edad', ''), nueva_fecha_mc)

                                final_obs_edit = f"[Pref: {ru['Pref']}] {ru['Observaciones']}".strip() if pd.notna(ru.get('Pref')) and str(ru.get('Pref')) != "Cualquiera" else str(ru['Observaciones'])
                                if pd.notna(ru['id']):
                                    client.table("mascotas").update({
                                        "nombre": str(ru['Nombre Mascota']), "especie": str(ru['Especie']), "sexo": str(ru.get('Sexo', '')),
                                        "raza": str(ru['Raza']), "peso": str(ru.get('Peso', '')), "fecha_nacimiento": nueva_fecha_mc,
                                        "observaciones": final_obs_edit
                                    }).eq("id", ru['id']).execute()
                                else:
                                    if pd.notna(ru['Nombre Mascota']) and str(ru['Nombre Mascota']).strip():
                                        client.table("mascotas").insert({
                                            "cliente_id": c_id, "nombre": str(ru['Nombre Mascota']),
                                            "especie": str(ru['Especie']) if pd.notna(ru['Especie']) else "",
                                            "sexo": str(ru.get('Sexo', '')) if pd.notna(ru.get('Sexo')) else "",
                                            "raza": str(ru['Raza']) if pd.notna(ru['Raza']) else "",
                                            "peso": str(ru.get('Peso', '')),
                                            "fecha_nacimiento": nueva_fecha_mc,
                                            "observaciones": final_obs_edit
                                        }).execute()
                            st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                            limpiar_cache_crm()
                            st.success("Datos de la familia actualizados."); time.sleep(0.5); st.rerun()
                            
                        filas_ver_mc = ed_mc[ed_mc["Ver Ficha"] == True]
                        if not filas_ver_mc.empty:
                            st.markdown("---")
                            m_id_sel = filas_ver_mc.iloc[0]['id']
                            m_data_sel = next(item for item in mascotas_lista if item["id"] == m_id_sel)
                            mostrar_ficha_clinica(m_id_sel, m_data_sel['nombre'], m_data_sel, prefix="fam")
                    else:
                        st.info("Este cliente no tiene mascotas registradas.")
                        
            else: st.info("No hay clientes registrados.")

            st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

            st.markdown("#### ➕ Añadir otra mascota a un cliente")
            dict_cli = {f"{c['nombre_dueno']} ({c['telefono']})": c['id'] for c in res_clientes.data} if res_clientes.data else {}
            
            with st.form("nueva_mascota_extra", clear_on_submit=True, border=False):
                sel_cli = st.selectbox("Selecciona el cliente:", list(dict_cli.keys()), key=f"nx_sel_{st.session_state.llave_crm_masc}")
                
                c_m1, c_m2, c_m3 = st.columns([2, 1.5, 1.5], vertical_alignment="bottom")
                with c_m1: nx_nom = st.text_input("Nombre mascota", key=f"nx_nom_{st.session_state.llave_crm_masc}")
                with c_m2: nx_esp = st.selectbox("Especie", ["Perro", "Gato", "Ave", "Roedor", "Otro"], key=f"nx_esp_{st.session_state.llave_crm_masc}")
                with c_m3: nx_sexo = st.selectbox("Sexo", ["", "Macho", "Hembra"], key=f"nx_sexo_{st.session_state.llave_crm_masc}")
                
                c_m4, c_m5, c_m6 = st.columns([2, 1.5, 1.5], vertical_alignment="bottom")
                with c_m4: nx_raz = st.text_input("Raza", key=f"nx_raz_{st.session_state.llave_crm_masc}")
                with c_m5: nx_peso = st.text_input("Peso (kg)", key=f"nx_peso_{st.session_state.llave_crm_masc}")
                with c_m6: nx_pref = st.selectbox("Peluquero/a Pref.", ["Cualquiera"] + empleados_lista, key=f"nx_pref_{st.session_state.llave_crm_masc}")
                
                if st.form_submit_button("Añadir Mascota", use_container_width=True):
                    if nx_nom and sel_cli:
                        final_obs_extra = f"[Pref: {nx_pref}]" if nx_pref != "Cualquiera" else ""
                        client.table("mascotas").insert({
                            "cliente_id": dict_cli[sel_cli], "nombre": nx_nom, "especie": nx_esp, "sexo": nx_sexo, "raza": nx_raz, "peso": nx_peso, "observaciones": final_obs_extra
                        }).execute()
                        st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                        st.session_state.llave_crm_masc += 1
                        limpiar_cache_crm()
                        st.success("Mascota añadida a la familia"); time.sleep(0.5); st.rerun()
                    else:
                        st.warning("Falta el nombre de la mascota.")
                        
        elif "Mascotas" in seccion_crm:
            all_masc = get_masc_crm(client)
            class DummyRes: pass
            res_mascotas = DummyRes()
            res_mascotas.data = all_masc
            
            if res_mascotas.data:
                df_m = pd.DataFrame(res_mascotas.data)
                
                c_busqm1, c_busqm2 = st.columns([2, 1])
                with c_busqm1:
                    b_masc = st.text_input("🔍 Buscar mascota por nombre:", placeholder="Escribe para filtrar...", key="b_masc").strip().lower()
                with c_busqm2:
                    ord_masc = st.selectbox("↕️ Ordenar por:", ["Más recientes", "Nombre (A-Z)", "Especie", "Dueño (A-Z)"], key="ord_masc")
                
                df_m['Dueño'] = df_m['clientes'].apply(lambda x: x.get('nombre_dueno', '') if isinstance(x, dict) else '')
                df_m['Teléfono'] = df_m['clientes'].apply(lambda x: x.get('telefono', '') if isinstance(x, dict) else '')
                if 'fecha_nacimiento' not in df_m.columns: df_m['fecha_nacimiento'] = ""
                df_m['Edad'] = df_m['fecha_nacimiento'].apply(calcular_edad)
                if 'historial_trabajos' not in df_m.columns:
                    df_m['historial_trabajos'] = [[] for _ in range(len(df_m))]
                df_m['Duración Media'] = df_m['historial_trabajos'].apply(calcular_duracion_media)
                
                if 'observaciones' not in df_m.columns: df_m['observaciones'] = ""
                if 'sexo' not in df_m.columns: df_m['sexo'] = ""
                df_m['Pref'] = df_m['observaciones'].apply(get_pref)
                df_m['observaciones'] = df_m['observaciones'].apply(strip_pref)
                
                df_m_vista = df_m[['id', 'cliente_id', 'nombre', 'Dueño', 'Teléfono', 'especie', 'sexo', 'raza', 'peso', 'fecha_nacimiento', 'Edad', 'Duración Media', 'Pref', 'observaciones']].copy()
                
                if b_masc:
                    df_m_vista = df_m_vista[df_m_vista['nombre'].str.lower().str.contains(b_masc, na=False)]
                    
                if ord_masc == "Nombre (A-Z)":
                    df_m_vista = df_m_vista.sort_values(by="nombre", key=lambda col: col.fillna('').astype(str).str.lower())
                elif ord_masc == "Especie":
                    df_m_vista = df_m_vista.sort_values(by="especie", key=lambda col: col.fillna('').astype(str).str.lower())
                elif ord_masc == "Dueño (A-Z)":
                    df_m_vista = df_m_vista.sort_values(by="Dueño", key=lambda col: col.fillna('').astype(str).str.lower())

                df_m_vista.insert(0, "Ver", False)
                
                st.markdown("💡 *Marca la casilla **'👁️ Ver'** para abrir la ficha completa y el historial de la mascota.*")
                
                ed_m = st.data_editor(
                    df_m_vista,
                    column_config={"Ver": st.column_config.CheckboxColumn("👁️ Ver", default=False), "id": None, "cliente_id": None, "Dueño": st.column_config.TextColumn("Dueño (Editar)", disabled=False), "Teléfono": st.column_config.TextColumn(disabled=True), "Edad": st.column_config.TextColumn("Edad (Editable)", disabled=False, help="Escribe '5 años' o '6 meses' si no conoces la fecha exacta."), "nombre": "Mascota", "sexo": st.column_config.SelectboxColumn("Sexo", options=["", "Macho", "Hembra"]), "peso": "Peso", "fecha_nacimiento": "F. Nacimiento", "Pref": st.column_config.SelectboxColumn("Peluquero/a Pref.", options=["Cualquiera"] + empleados_lista), "observaciones": "Observaciones Generales", "Duración Media": st.column_config.TextColumn("T. Medio", disabled=True, help="Tiempo medio de servicio calculado del historial.")},
                    use_container_width=True, hide_index=True, num_rows="dynamic", key=f"ed_mascotas_{st.session_state.get('db_version', 0)}", height=400
                )
                if st.button("💾 Guardar Cambios en Mascotas", type="primary"):
                    ed_m_clean = ed_m.drop(columns=["Ver"])
                    ids_actuales = ed_m_clean['id'].dropna().tolist()
                    ids_orig = df_m_vista['id'].tolist()
                    for id_b in [i for i in ids_orig if i not in ids_actuales]: client.table("mascotas").delete().eq("id", id_b).execute()
                    
                    for _, row in ed_m_clean.iterrows():
                        if pd.notna(row['id']):
                            nueva_fecha_m = str(row['fecha_nacimiento']) if pd.notna(row['fecha_nacimiento']) else ""
                            orig_match = df_m_vista[df_m_vista['id'] == row['id']]
                            if not orig_match.empty:
                                orig_ru = orig_match.iloc[0]
                                cambiado = False
                                for col in ['nombre', 'especie', 'sexo', 'raza', 'peso', 'fecha_nacimiento', 'observaciones', 'Dueño', 'Edad']:
                                    if col in row and col in orig_ru:
                                        if str(row.get(col, '')).strip() != str(orig_ru.get(col, '')).strip():
                                            cambiado = True
                                            break
                                if not cambiado:
                                    continue

                                if str(row.get('Edad', '')) != str(orig_ru.get('Edad', '')) and str(row.get('fecha_nacimiento', '')) == str(orig_ru.get('fecha_nacimiento', '')):
                                    nueva_fecha_m = aproximar_fecha_desde_edad(row.get('Edad', ''), nueva_fecha_m)

                            final_obs_edit = f"[Pref: {row['Pref']}] {row['observaciones']}".strip() if pd.notna(row.get('Pref')) and str(row.get('Pref')) != "Cualquiera" else str(row['observaciones'])
                            client.table("mascotas").update({
                                "nombre": str(row['nombre']), "especie": str(row['especie']), "sexo": str(row.get('sexo', '')),
                                "raza": str(row['raza']), "peso": str(row.get('peso', '')), "fecha_nacimiento": nueva_fecha_m,
                                "observaciones": final_obs_edit
                            }).eq("id", row['id']).execute()
                            
                            # --- LÓGICA INTELIGENTE DE UNIFICACIÓN DE DUEÑOS ---
                            if pd.notna(row.get('cliente_id')) and pd.notna(row.get('Dueño')):
                                nombre_orig = str(df_m_vista.loc[df_m_vista['id'] == row['id'], 'Dueño'].iloc[0]).strip()
                                nuevo_nombre = str(row['Dueño']).strip()
                                
                                if nuevo_nombre and nuevo_nombre != nombre_orig:
                                    # Buscar si ya existe un cliente con ese nombre exacto
                                    res_existente = client.table("clientes").select("id").eq("nombre_dueno", nuevo_nombre).execute()
                                    
                                    if res_existente.data:
                                        # 1. EXISTE EL CLIENTE: Reasignamos y Unificamos (Merge)
                                        id_existente = res_existente.data[0]['id']
                                        
                                        # Rescatar puntos y teléfono del cliente provisional (viejo) por si tuviera
                                        res_viejo = client.table("clientes").select("puntos, telefono").eq("id", row['cliente_id']).execute()
                                        if res_viejo.data:
                                            puntos_viejos = res_viejo.data[0].get('puntos', 0)
                                            tel_viejo = res_viejo.data[0].get('telefono', '')
                                            
                                            res_nuevo = client.table("clientes").select("puntos, telefono").eq("id", id_existente).execute()
                                            if res_nuevo.data:
                                                puntos_nuevos = res_nuevo.data[0].get('puntos', 0)
                                                tel_nuevo = res_nuevo.data[0].get('telefono', '')
                                                
                                                puntos_finales = puntos_nuevos + puntos_viejos
                                                tel_final = tel_nuevo if tel_nuevo else tel_viejo
                                                client.table("clientes").update({"puntos": puntos_finales, "telefono": tel_final}).eq("id", id_existente).execute()
                                                
                                        # Reasignar TODAS las mascotas del cliente viejo al cliente unificado
                                        client.table("mascotas").update({"cliente_id": id_existente}).eq("cliente_id", row['cliente_id']).execute()
                                        
                                        # Eliminar el cliente viejo que ha quedado vacío
                                        client.table("clientes").delete().eq("id", row['cliente_id']).execute()
                                    else:
                                        # 2. NO EXISTE EL CLIENTE: Simplemente lo renombramos
                                        client.table("clientes").update({"nombre_dueno": nuevo_nombre}).eq("id", row['cliente_id']).execute()
                                        
                                    # 3. Unificamos siempre las referencias en Deudas y Encargos para no dejar registros huérfanos
                                    client.table("ventas_historial").update({"cliente_deuda": nuevo_nombre}).eq("cliente_deuda", nombre_orig).execute()
                                    client.table("encargos_clientes").update({"nombre_cliente": nuevo_nombre}).eq("nombre_cliente", nombre_orig).execute()

                    st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                    limpiar_cache_crm()
                    st.session_state["crm_toast"] = "Fichas de mascotas y dueños actualizados y unificados correctamente."
                    time.sleep(1)
                    st.rerun()
                    
                st.markdown("---")
                
                # --- FICHA COMPLETA E HISTORIAL DE LA MASCOTA ---
                filas_m_marcadas = ed_m[ed_m["Ver"] == True]
                if not filas_m_marcadas.empty:
                    m_id = filas_m_marcadas.iloc[0]['id']
                    m_data = df_m[df_m['id'] == m_id].iloc[0]
                    m_nombre = m_data['nombre']
                    mostrar_ficha_clinica(m_id, m_nombre, m_data, prefix="ind")
            else: st.info("No hay mascotas registradas.")

        elif "Encargos" in seccion_crm:
            col_en1, col_en2 = st.columns([1, 2])
            with col_en1:
                st.markdown("#### 📝 Registrar Encargo")
                with st.form("n_encargo", clear_on_submit=True):
                    opc_cli_enc = ["👤 Cliente no registrado (Escribir a mano)"]
                    if res_clientes.data:
                        opc_cli_enc += [f"{c['nombre_dueno']} | {c['telefono']}" for c in res_clientes.data]
                    
                    sel_cli_enc = st.selectbox("1. Buscar Cliente:", opc_cli_enc, key=f"ne_sel_{st.session_state.llave_crm_enc}")
                    
                    st.markdown("<p style='font-size:12px; color:gray; margin:0;'>O rellenar si no está registrado:</p>", unsafe_allow_html=True)
                    c_nom_man, c_tel_man = st.columns(2)
                    with c_nom_man: e_cli_man = st.text_input("Nombre", key=f"ne_nom_{st.session_state.llave_crm_enc}")
                    with c_tel_man: e_tel_man = st.text_input("Teléfono", key=f"ne_tel_{st.session_state.llave_crm_enc}")
                    
                    st.markdown("---")
                    e_prod = st.text_input("2. Producto que pide *", key=f"ne_prod_{st.session_state.llave_crm_enc}")
                    e_cant = st.number_input("3. Cantidad *", min_value=1, value=1, key=f"ne_cant_{st.session_state.llave_crm_enc}")
                    e_obs = st.text_area("4. Observaciones", key=f"ne_obs_{st.session_state.llave_crm_enc}")
                    
                    if st.form_submit_button("Guardar Encargo", type="primary", use_container_width=True):
                        # Determinar cliente
                        if "Cliente no registrado" not in sel_cli_enc:
                            final_cli = sel_cli_enc.split(" | ")[0]
                            final_tel = sel_cli_enc.split(" | ")[1] if len(sel_cli_enc.split(" | ")) > 1 else ""
                        else:
                            final_cli = e_cli_man
                            final_tel = e_tel_man
                            
                        if final_cli and e_prod:
                            try:
                                crear_encargo(client, final_cli, final_tel, e_prod, e_cant, e_obs)
                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                st.session_state.llave_crm_enc += 1
                                limpiar_cache_crm()
                                st.success("Encargo guardado."); time.sleep(0.5); st.rerun()
                            except Exception as e:
                                st.error("Error al guardar en la base de datos.")
            
            with col_en2:
                st.markdown("#### 📌 Encargos Pendientes")
                
                # --- VISUALIZAR TICKET WEB RECIÉN GENERADO ---
                t_web = st.session_state.get('ticket_web_generado')
                if t_web:
                    with st.expander(f"🎉 TICKET GENERADO #{t_web['id']} PARA {t_web['cliente_fidel']} (WEB)", expanded=True):
                        st.success(f"Venta web confirmada exitosamente. ID de Ticket: {t_web['id']}")
                        
                        logo_html = ""
                        try:
                            with open("LOGO.jpg", "rb") as img_file:
                                b64_string = base64.b64encode(img_file.read()).decode("utf-8")
                                logo_html = f'<img src="data:image/jpeg;base64,{b64_string}" style="max-width: 200px; margin-bottom: 10px;"><br>'
                        except: pass
                        
                        texto_wa = f"¡Hola {t_web['cliente_fidel']}! 🐾 Tu pedido web ya está confirmado y registrado en tienda.\n\nAquí tienes tu resguardo de compra:\n*Ticket #{t_web['id']}*\n*Total: {t_web['total']}€*\n\nSi tienes dudas, contáctanos.\n¡Gracias por tu confianza!"
                        tel_wa = str(t_web.get('telefono', '')).replace(' ', '').replace('+', '')
                        wa_url = f"https://api.whatsapp.com/send?phone={tel_wa}&text={urllib.parse.quote(texto_wa)}"
                        
                        html_t_web = f"""
                        <!DOCTYPE html><html><head><meta charset='utf-8'>
                        <style>
                            .btn-print {{ padding: 12px; background-color: #005275; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%; font-size: 15px; margin-bottom: 8px; }}
                            .btn-wa {{ background-color: #25D366; }}
                        </style>
                        </head><body style='margin:0; padding:10px; background-color:white; font-family: sans-serif;'>
                            <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                                <button class="btn-print" onclick="imprimirWebTicket()">🖨️ IMPRIMIR TICKET</button>
                                <a href="{wa_url}" target="_blank" style="flex: 1; text-decoration: none;">
                                    <button class="btn-print btn-wa">📲 ENVIAR POR WHATSAPP</button>
                                </a>
                            </div>
                            
                            <div id="ticket-web-impresion" style="width: 100%; max-width: 350px; margin: 0 auto; border: 1px solid #ddd; padding: 15px; border-radius: 8px;">
                                <div style="text-align: center; font-family: monospace; width: 100%; font-size: 18px; color: black; font-weight: bold;">
                                    {logo_html}
                                    <b style="font-size: 24px;">ANIMALARIUM</b><br>
                                    Raquel Trujillo Hernández<br>DNI: 78854854K<br>C/ José Hernández Alfonso, 26<br>38009 S/C de Tenerife<br><br>
                                    <div style="text-align: left; font-size: 16px;">Fecha: {t_web['fecha']}<br>TICKET #{t_web['id']} (WEB)</div>
                                    <hr style="border-top: 2px dashed #000; margin: 10px 0px;">
                                    <table style="width: 100%; font-size: 16px; text-align: left; font-weight: bold;">
                        """
                        for p in t_web['productos']:
                            html_t_web += f"<tr><td style='padding-bottom: 5px;'>{p['Cantidad']}x {p['Producto']}<br><span style='font-size: 13px; font-weight: normal;'>A {p['Precio']:.2f}€/ud</span></td><td style='text-align: right; padding-bottom: 5px; vertical-align: top;'>{p['Subtotal']:.2f}€</td></tr>"
                        
                        html_t_web += f"""
                                    </table>
                                    <hr style="border-top: 2px dashed #000; margin: 10px 0px;">
                        """
                        if t_web.get('descuento_global', 0) > 0:
                            html_t_web += f"<div style='text-align: right; font-size: 16px; color: #d32f2f;'><b>DTO. 1ERA COMPRA: -{t_web['descuento_global']:.2f}€</b></div>"
                            
                        if t_web.get('pendiente', 0) > 0:
                            html_t_web += f"""<div style="text-align: right; font-size: 18px; color: black; margin-top: 5px; border: 2px solid black; padding: 3px;"><b>DEUDA PENDIENTE: {t_web['pendiente']:.2f}€</b></div>"""

                        html_t_web += f"""
                                    <div style="text-align: right; font-size: 22px;"><b>TOTAL: {t_web['total']:.2f}€</b></div>
                                    <div style="font-size: 16px; text-align: left; margin-top: 10px;"><b>Método de pago:</b> {t_web['metodo']}</div>
                        """
                        if t_web.get('cliente_fidel'):
                            html_t_web += f"<div style='font-size:14px; text-align:center; margin-top:15px; border: 1px solid #000; padding: 5px;'><b>🌟 CLIENTE VIP: {t_web['cliente_fidel']}</b>"
                            html_t_web += f"<br>Has ganado +{t_web['puntos_ganados']} puntos hoy!<br>Saldo actual disponible: {t_web.get('nuevo_saldo', 0)} puntos<br><span style='font-size:12px; color:#555;'>Ganas 1 pto por cada 10€ de compra.</span></div>"
                        
                        html_t_web += f"""
                                    <div style="text-align: center; margin-top: 25px;">
                                        <img src="https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=TICKET-{t_web['id']}" alt="QR Ticket" />
                                        <div style="font-size: 14px; margin-top: 5px; color: #555;">TICKET #{t_web['id']}</div>
                                    </div>
                                    <div style="font-size: 14px; color: #000; margin-top: 20px; text-align: center;"><b>POLÍTICA DE DEVOLUCIÓN</b><br>Plazo de 14 días con ticket y<br>embalaje original en perfecto estado.</div>
                                </div>
                            </div>
                            <script>
                            function imprimirWebTicket() {{
                                var ticketHTML = document.getElementById('ticket-web-impresion').innerHTML;
                                var fullHTML = "<!DOCTYPE html><html><head><meta charset='utf-8'></head><body style='margin:0; padding:0; background-color:white;'>" + ticketHTML + "</body></html>";
                                var htmlCodificado = encodeURIComponent(fullHTML);
                                var backURL = encodeURIComponent(window.location.href);
                                var iframe = document.createElement('iframe');
                                iframe.style.display = 'none';
                                iframe.src = "starpassprnt://v1/print/nopreview?back=" + backURL + "&html=" + htmlCodificado;
                                document.body.appendChild(iframe);
                            }}
                            </script>
                        </body></html>
                        """
                        components.html(html_t_web, height=550, scrolling=True)
                        
                        if st.button("❌ Cerrar vista del Ticket", use_container_width=True):
                            st.session_state.ticket_web_generado = None
                            st.rerun()
                # --- FIN VISUALIZAR TICKET WEB RECIÉN GENERADO ---

                mostrar_historial = st.toggle("👁️ Mostrar historial (Entregados / Cancelados)", value=False)
                
                try:
                    all_enc = fetch_encargos_crm(client)
                    if all_enc:
                        df_e = pd.DataFrame(all_enc)
                        if not mostrar_historial:
                            df_e = df_e[~df_e['estado'].isin(['Entregado', 'Cancelado'])]
                            if df_e.empty:
                                st.info("No hay encargos pendientes. Activa 'Mostrar historial' para ver los entregados o cancelados.")

                        if not df_e.empty:
                            dt_e = pd.to_datetime(df_e['created_at'], utc=True, format='mixed', errors='coerce').fillna(pd.Timestamp('today', tz='UTC'))
                            if dt_e.dt.tz is None:
                                dt_e = dt_e.dt.tz_localize('UTC')
                            df_e['Fecha'] = dt_e.dt.tz_convert('Atlantic/Canary').dt.strftime('%d/%m/%Y')
                        else:
                            df_e['Fecha'] = ""

                        if 'notas' not in df_e.columns: df_e['notas'] = ""
                        if 'WhatsApp' not in df_e.columns: df_e['WhatsApp'] = None
                        if 'origen' not in df_e.columns: df_e['origen'] = 'Tienda'
                        
                        hoy_date = pd.Timestamp.now('Atlantic/Canary')
                        alertas_encargos = []
                        for idx, row in df_e.iterrows():
                            try:
                                dt_c = dt_e[idx]
                                if dt_c.tzinfo is None: dt_c = dt_c.tz_localize('UTC')
                                dias_desde_creacion = (pd.Timestamp.now('Atlantic/Canary') - dt_c.tz_convert('Atlantic/Canary')).days
                                estado_actual = row.get('estado')
                                notas_texto = str(row.get('notas', ''))
                                
                                import re
                                dias_desde_aviso = 0
                                m_fecha = re.search(r'\[Aviso:\s*(\d{4}-\d{2}-\d{2})\]', notas_texto)
                                if m_fecha:
                                    try:
                                        fecha_aviso = pd.to_datetime(m_fecha.group(1)).tz_localize('Atlantic/Canary')
                                        dias_desde_aviso = (pd.Timestamp.now('Atlantic/Canary') - fecha_aviso).days
                                    except: pass
                                else:
                                    dias_desde_aviso = dias_desde_creacion
                                    
                                # Generar enlace de WhatsApp dinámico contextual
                                tel_enc = str(row.get('telefono', ''))
                                tel_limpio = ''.join(filter(str.isdigit, tel_enc))
                                if tel_limpio:
                                    if len(tel_limpio) == 9 and not tel_limpio.startswith('34'): tel_limpio = '34' + tel_limpio
                                    
                                    if row.get('origen') == 'Web':
                                        
                                        # Extraer metadata para obtener el método de pago y el total
                                        metodo_pago = "Tarjeta"
                                        total_str = ""
                                        detalles_web = str(row.get('detalle_pedido', ''))
                                        
                                        import json
                                        if "[---METADATA---]" in notas_texto:
                                            try:
                                                meta_str = notas_texto.split("[---METADATA---]")[1].split("[---/METADATA---]")[0]
                                                meta = json.loads(meta_str)
                                                if meta.get('metodo_pago'):
                                                    metodo_pago = meta.get('metodo_pago')
                                                if meta.get('total_final'):
                                                    total_str = f"{meta.get('total_final'):.2f}€"
                                                # Opcional: Reconstruir detalle por si se editó y se quiere mostrar de forma más limpia
                                                if meta.get('items'):
                                                    detalles_web = "\n".join([f"• {x['cantidad']}x {x['nombre']}" for x in meta['items']])
                                            except: pass
                                            
                                        if not total_str:
                                            total_str = "(Ver enlace)"
                                            
                                        if estado_actual == 'Avisado sin stock':
                                            mensaje_encargo = f"¡Hola {row['nombre_cliente']}! 🐾 Te escribimos desde Animalarium sobre tu pedido web. Lamentablemente, nos falta stock de ({row['detalle_pedido']}). ¿Te interesaría cambiarlo por alguna de estas opciones similares que sí tenemos? [ELIMINA ESTO Y ESCRIBE AQUÍ LAS OPCIONES]"
                                        elif estado_actual == 'Aviso de servicio a domicilio con enlace de pago':
                                            if "Bizum" in metodo_pago:
                                                mensaje_encargo = f"¡Hola {row['nombre_cliente']}! 🐾 Todo listo para tu envío a domicilio. Tu pedido es:\n{detalles_web}\n\n*Total a pagar: {total_str}*\n\nPor favor, realiza el Bizum a nuestro número indicando tu nombre. En cuanto lo recibamos, prepararemos tu paquete para la entrega."
                                            else:
                                                mensaje_encargo = f"¡Hola {row['nombre_cliente']}! 🐾 Todo listo para tu envío a domicilio. Tu pedido es:\n{detalles_web}\n\n*Total a pagar: {total_str}*\n\nPuedes revisar tu pedido final y pagarlo de forma 100% segura con tu tarjeta aquí: https://animalariumtenerife.es/pago/{row['id']}"
                                        elif estado_actual == 'Aviso de recogida local con enlace de pago':
                                            if "Bizum" in metodo_pago:
                                                mensaje_encargo = f"¡Hola {row['nombre_cliente']}! 🐾 Todo listo. Tu pedido es:\n{detalles_web}\n\n*Total a pagar: {total_str}*\n\nPor favor, realiza el Bizum a nuestro número indicando tu nombre. Podrás recogerlo en nuestro local (9:00 a 21:00 ininterrumpido). Te confirmaremos por esta vía en un plazo de 24 a 48 horas en cuanto el producto esté en el local listo para su entrega."
                                            else:
                                                mensaje_encargo = f"¡Hola {row['nombre_cliente']}! 🐾 Todo listo. Tu pedido es:\n{detalles_web}\n\n*Total a pagar: {total_str}*\n\nPor favor, realiza el pago seguro con tarjeta aquí: https://animalariumtenerife.es/pago/{row['id']}. Podrás recogerlo en nuestro local en horario de 9:00 a 21:00 ininterrumpido. Te confirmaremos por esta vía en un plazo de 24 a 48 horas en cuanto el producto esté en el local listo para su entrega."
                                        elif estado_actual == 'Recibido':
                                            mensaje_encargo = f"¡Hola {row['nombre_cliente']}! 🐾 Hemos recibido tu pedido web. Estamos comprobando el stock y te avisaremos enseguida."
                                        elif "Confirmado" in str(estado_actual):
                                            if "reparto a domicilio" in str(estado_actual):
                                                mensaje_encargo = f"¡Hola {row['nombre_cliente']}! 🐾 Hemos confirmado tu pago correctamente. Aquí tienes tu ticket de compra: https://animalariumtenerife.es/ticket/{row['id']}. ¿A qué hora te viene mejor que te hagamos la entrega a domicilio?"
                                            else:
                                                mensaje_encargo = f"¡Hola {row['nombre_cliente']}! 🐾 Hemos confirmado tu pago correctamente. Aquí tienes tu ticket de compra: https://animalariumtenerife.es/ticket/{row['id']}. Tu pedido ya está esperándote en la tienda. ¡Puedes pasar cuando quieras!"
                                        else:
                                            mensaje_encargo = f"¡Hola {row['nombre_cliente']}! 🐾 Te escribimos sobre tu pedido web ({row['detalle_pedido']})."
                                    else:
                                        mensaje_encargo = f"¡Hola {row['nombre_cliente']}! 🐾 Te escribimos desde Animalarium para avisarte de que tu encargo ({row['detalle_pedido']}) ya está en la tienda listo para recoger. ¡Te esperamos! Un saludo."
                                        if estado_actual == 'Recibido y Avisado' and dias_desde_aviso >= 7:
                                            mensaje_encargo = f"¡Hola {row['nombre_cliente']}! 🐾 Te escribimos desde Animalarium para recordarte que tu encargo ({row['detalle_pedido']}) sigue en la tienda esperándote. Por favor, confírmanos si vas a venir a recogerlo. ¡Un saludo!"
                                        elif estado_actual == 'Confirmación de aviso' and dias_desde_aviso >= 14:
                                            mensaje_encargo = f"¡Hola {row['nombre_cliente']}! 🐾 Lamentamos informarte que ha finalizado el plazo máximo de 14 días para recoger tu encargo ({row['detalle_pedido']}). Procedemos a anular la reserva y liberar el producto. Si tienes cualquier duda, contáctanos. Un saludo."
                                            
                                    df_e.at[idx, 'WhatsApp'] = f"https://api.whatsapp.com/send?phone={tel_limpio}&text={urllib.parse.quote(mensaje_encargo)}"
                                
                                if estado_actual == 'Pendiente' and dias_desde_creacion >= 2:
                                    alertas_encargos.append(("error", f"🚨 **PEDIDO RETRASADO:** El encargo de **{row['nombre_cliente']}** lleva {dias_desde_creacion} días Pendiente de pedir al proveedor."))
                                elif estado_actual == 'Recibido y Avisado' and dias_desde_aviso >= 7:
                                    alertas_encargos.append(("error", f"🚨 **FALTA RESPUESTA:** Hace {dias_desde_aviso} días que avisamos a **{row['nombre_cliente']}**. ¡Mandar recordatorio!"))
                                elif estado_actual == 'Confirmación de aviso' and dias_desde_aviso >= 14:
                                    alertas_encargos.append(("error", f"🚨 **CADUCADO:** El encargo de **{row['nombre_cliente']}** lleva {dias_desde_aviso} días retenido desde el aviso. Anular o consultar con el cliente."))
                            except Exception: pass
                            
                        if alertas_encargos:
                            with st.expander(f"🚨 Tienes {len(alertas_encargos)} avisos de revisión en tus encargos", expanded=False):
                                for tipo, msg in alertas_encargos:
                                    if tipo == "warning":
                                        st.warning(msg)
                                    else:
                                        st.error(msg)
                        
                        df_e_vista = df_e[['id', 'Fecha', 'nombre_cliente', 'telefono', 'detalle_pedido', 'notas', 'estado', 'WhatsApp', 'origen']].copy()
                        df_e_vista['notas'] = df_e_vista['notas'].fillna("")
                        
                        seccion_encargos = st.radio("Sección Encargos:", ["🛍️ Encargos de Tienda", "🌐 Pedidos Web"], horizontal=True, label_visibility="collapsed")
                        
                        if "Encargos de Tienda" in seccion_encargos:
                            df_tnd = df_e_vista[df_e_vista['origen'] != 'Web'].copy()
                            ed_e_tnd = st.data_editor(
                                df_tnd, hide_index=True, use_container_width=True, height=300, key=f"ed_tabla_encargos_tnd_{st.session_state.get('db_version', 0)}",
                                column_config={
                                    "id": None, "origen": None, "Fecha": "Día", "nombre_cliente": "Cliente", "telefono": "Tel.",
                                    "detalle_pedido": "Producto y Cant.", "notas": "Observaciones",
                                    "estado": st.column_config.SelectboxColumn("Estado", options=["Pendiente", "Pedido", "Recibido y Avisado", "Confirmación de aviso", "Retrasado por cliente", "Entregado", "Cancelado"]),
                                    "WhatsApp": st.column_config.LinkColumn("📱 Avisar", display_text="💬 WhatsApp")
                                },
                                num_rows="dynamic"
                            )
                            
                        elif "Pedidos Web" in seccion_encargos:
                            df_web = df_e_vista[df_e_vista['origen'] == 'Web'].copy()
                            ed_e_web = st.data_editor(
                                df_web, hide_index=True, use_container_width=True, height=300, key=f"ed_tabla_encargos_web_{st.session_state.get('db_version', 0)}",
                                column_config={
                                    "id": None, "origen": None, "Fecha": "Día", "nombre_cliente": "Cliente", "telefono": "Tel.",
                                    "detalle_pedido": "Producto y Cant.", "notas": "Observaciones",
                                    "estado": st.column_config.SelectboxColumn("Estado", options=["Recibido", "Avisado sin stock", "Aviso de recogida local con enlace de pago", "Aviso de servicio a domicilio con enlace de pago", "Confirmado con reparto a domicilio", "Confirmado con recogida local", "Entregado", "Cancelado"]),
                                    "WhatsApp": st.column_config.LinkColumn("📱 Avisar", display_text="💬 WhatsApp")
                                },
                                num_rows="dynamic"
                            )

                            st.markdown("#### 🛒 Editar Carrito (Sustituciones)")
                            st.info("Si el cliente acepta cambiar un producto agotado, bórralo de su carrito y añade el nuevo antes de confirmar el pedido.")
                            if not df_web.empty:
                                pd_options = ["---"] + df_web.apply(lambda x: f"{x['nombre_cliente']} - {x['detalle_pedido']} (ID: {x['id']})", axis=1).tolist()
                                enc_sel = st.selectbox("Seleccionar Pedido Web:", pd_options)
                                if enc_sel != "---":
                                    enc_id = int(enc_sel.split("(ID: ")[1].replace(")", ""))
                                    filtro_id = df_web[df_web['id'] == enc_id]
                                    if not filtro_id.empty:
                                        enc_data = filtro_id.iloc[0]
                                        notas_str = enc_data['notas']
                                        if "[---METADATA---]" in notas_str:
                                            import json
                                            meta_str = notas_str.split("[---METADATA---]")[1].split("[---/METADATA---]")[0]
                                            try:
                                                meta = json.loads(meta_str)
                                                st.write("##### Productos Actuales")
                                                items = meta.get('items', [])
                                                
                                                for i, it in enumerate(items):
                                                    col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                                                    with col1: st.write(f"**{it['nombre']}**")
                                                    with col2: st.write(f"{it['cantidad']}x")
                                                    with col3: st.write(f"{float(it['precio']):.2f}€")
                                                    with col4:
                                                        if st.button("🗑️ Borrar", key=f"del_{enc_id}_{i}"):
                                                            items.pop(i)
                                                            meta['items'] = items
                                                            # Recalcular total
                                                            nuevo_tot = sum(float(x['precio']) * int(x['cantidad']) for x in items)
                                                            meta['total_final'] = nuevo_tot
                                                            nuevo_det = " + ".join([f"{x['cantidad']}x {x['nombre']}" for x in items])
                                                            nuevo_meta_str = json.dumps(meta)
                                                            nueva_nota = notas_str.split("[---METADATA---]")[0] + "[---METADATA---]" + nuevo_meta_str + "[---/METADATA---]"
                                                            client.table("encargos_clientes").update({"notas": nueva_nota, "detalle_pedido": nuevo_det}).eq("id", enc_id).execute()
                                                            st.rerun()
                                                
                                                st.write(f"**Total a cobrar:** {meta['total_final']:.2f}€")
                                                
                                                st.markdown("##### ➕ Añadir Sustituto")
                                                res_prod = client.table("productos").select("id, nombre, precio_pvp, codigo_barras").eq("categoria", "Producto").execute()
                                                if res_prod.data:
                                                    opts = [""] + [f"{p['nombre']} - {p['precio_pvp']}€ ({p['codigo_barras']})" for p in res_prod.data]
                                                    p_add = st.selectbox("Buscar producto", opts)
                                                    cant = st.number_input("Cantidad", min_value=1, value=1)
                                                    if st.button("Añadir al carrito"):
                                                        if p_add:
                                                            p_id = res_prod.data[opts.index(p_add)-1]['id']
                                                            p_name = res_prod.data[opts.index(p_add)-1]['nombre']
                                                            p_precio = res_prod.data[opts.index(p_add)-1]['precio_pvp']
                                                            items.append({"id": p_id, "nombre": p_name, "precio": p_precio, "cantidad": cant, "sku": "", "igic": "0%"})
                                                            meta['items'] = items
                                                            nuevo_tot = sum(float(x['precio']) * int(x['cantidad']) for x in items)
                                                            meta['total_final'] = nuevo_tot
                                                            nuevo_det = " + ".join([f"{x['cantidad']}x {x['nombre']}" for x in items])
                                                            nuevo_meta_str = json.dumps(meta)
                                                            nueva_nota = notas_str.split("[---METADATA---]")[0] + "[---METADATA---]" + nuevo_meta_str + "[---/METADATA---]"
                                                            client.table("encargos_clientes").update({"notas": nueva_nota, "detalle_pedido": nuevo_det}).eq("id", enc_id).execute()
                                                            st.success("Añadido")
                                                            st.rerun()
                                            except Exception as e:
                                                st.error(f"Error parseando carrito: {e}")
                                        else:
                                            st.warning("Este pedido web es antiguo y no tiene el carrito estructurado. No se puede editar aquí.")

                        if st.button("💾 Guardar Cambios en Encargos"):
                            ed_e = ed_e_tnd if "Encargos de Tienda" in seccion_encargos else ed_e_web
                            errores = False
                            for _, r in ed_e.iterrows():
                                if pd.notna(r['id']):
                                    orig_match = df_e_vista[df_e_vista['id'] == r['id']]
                                    if not orig_match.empty:
                                        orig_row = orig_match.iloc[0]
                                        if str(r['estado']) == 'Cancelado' and str(orig_row['estado']) != 'Cancelado' and str(r.get('notas', '')).strip() == '':
                                            st.error(f"⚠️ Para cancelar el encargo de **{r['nombre_cliente']}**, debes escribir el motivo en la columna 'Observaciones'.")
                                            errores = True
                                            
                            if not errores:
                                cambios_realizados = 0
                                
                                # 1. Borrar encargos eliminados en la tabla (solo de la sección actual)
                                ids_actuales = [str(i) for i in ed_e['id'].dropna().tolist()]
                                if "Encargos de Tienda" in seccion_encargos:
                                    ids_originales_seccion = [str(i) for i in df_tnd['id'].tolist()]
                                    df_orig_sec = df_tnd
                                else:
                                    ids_originales_seccion = [str(i) for i in df_web['id'].tolist()]
                                    df_orig_sec = df_web
                                
                                ids_a_borrar = [i for i in ids_originales_seccion if i not in ids_actuales]
                                
                                for id_del in ids_a_borrar:
                                    # Tenemos que volver a buscar el ID original porque supabase lo espera numérico
                                    real_id = df_orig_sec[df_orig_sec['id'].astype(str) == id_del]['id'].iloc[0]
                                    client.table("encargos_clientes").delete().eq("id", real_id).execute()
                                    cambios_realizados += 1
                                    
                                # 2. Actualizar encargos existentes
                                for _, r in ed_e.iterrows():
                                    if pd.notna(r['id']):
                                        orig_match = df_e_vista[df_e_vista['id'] == r['id']]
                                        if not orig_match.empty:
                                            orig_row = orig_match.iloc[0]
                                            nuevo_est = str(r['estado'])
                                            viejo_est = str(orig_row['estado'])
                                            nuevas_notas = str(r.get('notas', '')).strip()
                                            nuevo_nombre = str(r.get('nombre_cliente', '')).strip()
                                            nuevo_tel = str(r.get('telefono', '')).strip()
                                            nuevo_det = str(r.get('detalle_pedido', '')).strip()
                                            
                                            # Inyectar etiqueta de aviso
                                            if nuevo_est == 'Recibido y Avisado' and viejo_est != 'Recibido y Avisado':
                                                if "[Aviso:" not in nuevas_notas:
                                                    hoy_str = pd.Timestamp.now('Atlantic/Canary').strftime('%Y-%m-%d')
                                                    etiqueta = f"[Aviso: {hoy_str}]"
                                                    nuevas_notas = f"{nuevas_notas} {etiqueta}".strip()
                                            
                                            if (nuevo_est != viejo_est or 
                                                nuevas_notas != str(orig_row.get('notas', '')).strip() or
                                                nuevo_nombre != str(orig_row.get('nombre_cliente', '')).strip() or
                                                nuevo_tel != str(orig_row.get('telefono', '')).strip() or
                                                nuevo_det != str(orig_row.get('detalle_pedido', '')).strip()):
                                                import json
                                                import hashlib
                                                
                                                if "Confirmado" in nuevo_est and "Confirmado" not in viejo_est and r.get('origen') == 'Web':
                                                    metadata_str = nuevas_notas.split("[---METADATA---]")[1].split("[---/METADATA---]")[0] if "[---METADATA---]" in nuevas_notas else None
                                                    if metadata_str:
                                                        try:
                                                            meta = json.loads(metadata_str)
                                                            
                                                            # 1. Registrar Venta (Deuda)
                                                            hash_ant_res = client.table("ventas_historial").select("hash_actual").order("id", desc=True).limit(1).execute()
                                                            hash_ant = hash_ant_res.data[0]['hash_actual'] if hash_ant_res.data else "GENESIS"
                                                            fecha_str = pd.Timestamp.now('Atlantic/Canary').strftime('%d/%m/%Y, %H:%M')
                                                            str_data = f"{pd.Timestamp.now('Atlantic/Canary').isoformat()}-{meta['total_final']}-{hash_ant}"
                                                            hash_act = hashlib.sha256(str_data.encode()).hexdigest()
                                                            
                                                            # Si el encargo se pasa a Confirmado, se asume pagado
                                                            es_pagado = "reparto a domicilio" in nuevo_est or "recogida local" in nuevo_est
                                                            estado_venta = "Completado" if es_pagado else "Deuda"
                                                            pagado_val = meta['total_final'] if es_pagado else 0
                                                            pendiente_val = 0 if es_pagado else meta['total_final']
                                                            descuento_primera = meta.get('descuento_primera_compra', 0)
                                                            
                                                            res_venta_web = client.table("ventas_historial").insert({
                                                                "fecha": fecha_str, "productos": meta['items'], "total": meta['total_final'],
                                                                "pagado": pagado_val, "pendiente": pendiente_val, "metodo_pago": f"{meta['metodo_pago']} (WEB)",
                                                                "cliente_deuda": r['nombre_cliente'] if not es_pagado else "", "puntos_ganados": meta['puntos_ganados'],
                                                                "puntos_usados": meta['puntos_usados'], "descuento_global": descuento_primera,
                                                                "hash_anterior": hash_ant, "hash_actual": hash_act, "estado": estado_venta,
                                                                "cliente_vip_nombre": r['nombre_cliente']
                                                            }).execute()
                                                            
                                                            ticket_id = res_venta_web.data[0]['id'] if res_venta_web.data else "S/N"
                                                            carrito_ticket = []
                                                            for item in meta['items']:
                                                                c = item.get('cantidad', 1)
                                                                p = item.get('precio_unitario', 0)
                                                                carrito_ticket.append({
                                                                    "Cantidad": c,
                                                                    "Producto": item.get('nombre', item.get('id', 'Producto Web')),
                                                                    "Precio": float(p),
                                                                    "Desc. %": 0,
                                                                    "Subtotal": float(c * p)
                                                                })
                                                                
                                                            if descuento_primera > 0:
                                                                carrito_ticket.append({
                                                                    "Cantidad": 1,
                                                                    "Producto": "DTO. 1ERA COMPRA WEB (10%)",
                                                                    "Precio": -float(descuento_primera),
                                                                    "Desc. %": 0,
                                                                    "Subtotal": -float(descuento_primera)
                                                                })
                                                                
                                                            st.session_state.ticket_web_generado = {
                                                                "id": ticket_id,
                                                                "fecha": fecha_str,
                                                                "productos": carrito_ticket,
                                                                "total": meta['total_final'],
                                                                "pendiente": pendiente_val,
                                                                "descuento_global": descuento_primera,
                                                                "metodo": f"{meta['metodo_pago']} (WEB)",
                                                                "cliente_fidel": r['nombre_cliente'],
                                                                "puntos_ganados": meta['puntos_ganados'],
                                                                "telefono": r['telefono'],
                                                                "nuevo_saldo": 0
                                                            }
                                                            
                                                            # 2. Descontar Stock
                                                            for item in meta['items']:
                                                                if item['id'] != 'ENVIO':
                                                                    prod_res = client.table("productos").select("stock_actual").eq("id", item['id']).execute()
                                                                    if prod_res.data:
                                                                        nuevo_stock = (prod_res.data[0]['stock_actual'] or 0) - item['cantidad']
                                                                        client.table("productos").update({"stock_actual": nuevo_stock}).eq("id", item['id']).execute()
                                                                        
                                                            # 3. Puntos
                                                            if meta.get('cliente_id'):
                                                                cli_res = client.table("clientes").select("puntos").eq("id", meta['cliente_id']).execute()
                                                                if cli_res.data:
                                                                    pts = cli_res.data[0]['puntos'] or 0
                                                                    nuevo_saldo = pts - meta['puntos_usados'] + meta['puntos_ganados']
                                                                    client.table("clientes").update({"puntos": nuevo_saldo}).eq("id", meta['cliente_id']).execute()
                                                                    if 'ticket_web_generado' in st.session_state:
                                                                        st.session_state.ticket_web_generado['nuevo_saldo'] = nuevo_saldo
                                                                    
                                                            # 4. Servicio a Domicilio
                                                            if "reparto a domicilio" in nuevo_est:
                                                                detalle_final = f"{r['detalle_pedido']} \n(Pedido Web Confirmado - Pago: {meta['metodo_pago']})"
                                                                client.table("pedidos_domicilio").insert({
                                                                    "nombre_cliente": r['nombre_cliente'], "telefono": r['telefono'], "direccion": meta['direccion'],
                                                                    "detalle_pedido": detalle_final, "estado": "Pendiente"
                                                                }).execute()
                                                                
                                                        except Exception as e:
                                                            st.error(f"Error procesando confirmación web: {e}")
                                                            errores = True
                                                            
                                                if not errores:
                                                    client.table("encargos_clientes").update({
                                                        "estado": nuevo_est, 
                                                        "notas": nuevas_notas,
                                                        "nombre_cliente": nuevo_nombre,
                                                        "telefono": nuevo_tel,
                                                        "detalle_pedido": nuevo_det
                                                    }).eq("id", r['id']).execute()
                                                    
                                                    if nuevo_tel != str(orig_row.get('telefono', '')).strip():
                                                        try:
                                                            client.table("clientes").update({"telefono": nuevo_tel}).ilike("nombre_dueno", nuevo_nombre).execute()
                                                        except Exception:
                                                            pass
                                                            
                                                    cambios_realizados += 1
                                                
                                if cambios_realizados > 0:
                                    st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                    limpiar_cache_crm()
                                    try:
                                        from historial import limpiar_cache_historial
                                        from contabilidad import limpiar_cache_contabilidad
                                        limpiar_cache_historial()
                                        limpiar_cache_contabilidad()
                                    except Exception: pass
                                    st.success(f"Se han actualizado {cambios_realizados} encargo(s).")
                                    time.sleep(0.8)
                                    st.rerun()
                                else:
                                    st.info("No se han detectado cambios.")
                    else: st.info("No hay encargos activos.")
                except Exception as e: st.warning(f"Error al cargar encargos: {e}")
                
        elif "Pagos Pendientes" in seccion_crm:
            st.markdown("#### 💸 Clientes con Pagos Pendientes (Deudas de Tienda)")
            st.info("Aquí se agrupan automáticamente los clientes que dejaron a deber alguna compra en el TPV.")
            try:
                res_deudas = fetch_deudas_crm(client)
                if res_deudas.data:
                    df_deudas = pd.DataFrame(res_deudas.data)
                    # Recuperación de fechas mixtas y vacías en deudas
                    df_deudas['Fecha'] = pd.to_datetime(df_deudas['created_at'], utc=True, format='mixed', errors='coerce').fillna(pd.Timestamp.now(tz='UTC'))
                    
                    resumen_deudas = []
                    res_cli_d_data = fetch_clientes_deuda_crm(client)
                    mapa_telefonos = {c['nombre_dueno']: c['telefono'] for c in res_cli_d_data} if res_cli_d_data else {}
                    
                    for cliente, group in df_deudas.groupby("cliente_deuda"):
                        if not cliente or str(cliente).strip() == "" or str(cliente) == "nan": continue
                        total_debe = group['pendiente'].sum()
                        fecha_antigua = group['Fecha'].min()
                        if fecha_antigua.tz is None: fecha_antigua = fecha_antigua.tz_localize('UTC')
                        dias_retraso = (pd.Timestamp.now('Atlantic/Canary') - fecha_antigua.tz_convert('Atlantic/Canary')).days
                        
                        tel = mapa_telefonos.get(cliente, '')
                        tel_limpio = ''.join(filter(str.isdigit, str(tel)))
                        url_wa = None
                        if tel_limpio:
                            if len(tel_limpio) == 9 and not tel_limpio.startswith('34'): tel_limpio = '34' + tel_limpio
                            msg = f"¡Hola {cliente}! 👋 Nos ponemos en contacto desde Animalarium para recordarte que tienes un saldo pendiente en la tienda de {total_debe:.2f}€. Cuando te venga bien, puedes pasarte a saldarlo. ¡Muchas gracias y un saludo! 🐾"
                            url_wa = f"https://api.whatsapp.com/send?phone={tel_limpio}&text={urllib.parse.quote(msg)}"
                        
                        alerta = "🔴 Avisar (Más de 15 días)" if dias_retraso >= 15 else "🟡 Reciente"
                        
                        resumen_deudas.append({
                            "Cliente": cliente, "Deuda Acumulada (€)": total_debe, 
                            "Días de retraso": dias_retraso, "Estado": alerta, "WhatsApp": url_wa
                        })
                        
                    if resumen_deudas:
                        df_resumen = pd.DataFrame(resumen_deudas).sort_values("Días de retraso", ascending=False)
                        st.dataframe(
                            df_resumen, use_container_width=True, hide_index=True,
                            column_config={"Deuda Acumulada (€)": st.column_config.NumberColumn("Deuda (€)", format="%.2f"), "WhatsApp": st.column_config.LinkColumn("📱 Recordatorio", display_text="💬 Enviar WhatsApp")}
                        )
                            
                        st.markdown("---")
                        st.markdown("#### 💰 Registrar Pago de Deuda (Por Cliente y Ticket)")
                        
                        clientes_con_deuda = [""] + sorted([c for c in df_deudas['cliente_deuda'].unique() if isinstance(c, str) and c.strip()])
                        cli_saldar = st.selectbox("1. Selecciona el cliente:", clientes_con_deuda)
                        
                        if cli_saldar:
                            deudas_cliente = df_deudas[df_deudas['cliente_deuda'] == cli_saldar].sort_values("Fecha")
                            
                            opciones_tickets = [""]
                            if len(deudas_cliente) > 1:
                                total_deuda_cli = deudas_cliente['pendiente'].sum()
                                opciones_tickets.append(f"Todos los tickets | PENDIENTE TOTAL: {total_deuda_cli:.2f}€")
                                
                            for _, row in deudas_cliente.iterrows():
                                d_str = row['Fecha'].strftime('%d/%m/%Y')
                                opciones_tickets.append(f"Ticket #{row['id']} | PENDIENTE: {row['pendiente']:.2f}€ (Del {d_str})")
                                
                            tk_saldar = st.selectbox("2. Selecciona el ticket a abonar:", opciones_tickets)
                            
                            if tk_saldar:
                                es_multi = "Todos los tickets" in tk_saldar
                                if es_multi:
                                    total_debe = deudas_cliente['pendiente'].sum()
                                    tk_id = None
                                else:
                                    tk_id = int(tk_saldar.split("Ticket #")[1].split(" | ")[0])
                                    row_tk = deudas_cliente[deudas_cliente['id'] == tk_id].iloc[0]
                                    total_debe = float(row_tk['pendiente'])
                            
                                res_b = fetch_bancos_crm(client)
                                opciones_pago = ["💵 Caja Fuerte (Efectivo)"]
                                mapa_bancos = {}
                                if res_b.data:
                                    for b in res_b.data:
                                        etiqueta = f"🏦 Tarjeta ({b['nombre_banco']})"
                                        opciones_pago.append(etiqueta)
                                        mapa_bancos[etiqueta] = b
                                opciones_pago.append("📱 Bizum")
                                
                                with st.form("form_saldar_deuda", border=True):
                                    if es_multi:
                                        st.info(f"Deuda Total de **{cli_saldar}**: **{total_debe:.2f}€**")
                                    else:
                                        st.info(f"Deuda del **Ticket #{tk_id}** ({cli_saldar}): **{total_debe:.2f}€**")
                                        
                                    col_d1, col_d2 = st.columns([1, 1])
                                    with col_d1:
                                        cantidad_abonar = st.number_input("3. Cantidad a abonar (€):", min_value=0.01, max_value=float(total_debe), value=float(total_debe), step=0.01, format="%.2f")
                                    with col_d2:
                                        metodo_saldar = st.selectbox("4. Método de cobro:", opciones_pago)
                                    
                                    btn_saldar = st.form_submit_button("✅ Registrar Abono", type="primary", use_container_width=True)
                                    
                                    if btn_saldar:
                                        pago_exitoso = False
                                        
                                        if "Caja Fuerte" in metodo_saldar:
                                            res_caja = fetch_caja_abierta_crm(client)
                                            if not res_caja.data:
                                                st.error("⚠️ La caja está cerrada. Abre un turno en 'Control Caja' para poder registrar el pago en efectivo.")
                                            else:
                                                id_caja = res_caja.data[0]['id']
                                                motivo_txt = f"Cobro deuda Ticket #{tk_id} ({cli_saldar})" if not es_multi else f"Cobro deuda completa ({cli_saldar})"
                                                client.table("movimientos_caja").insert({
                                                    "id_caja": id_caja, "tipo": "Ingreso", "cantidad": float(cantidad_abonar), 
                                                    "motivo": motivo_txt
                                                }).execute()
                                                pago_exitoso = True
                                        elif "Tarjeta" in metodo_saldar:
                                            banco_data = mapa_bancos[metodo_saldar]
                                            nuevo_saldo = banco_data['saldo_actual'] + cantidad_abonar
                                            client.table("cuentas_bancarias").update({"saldo_actual": nuevo_saldo}).eq("id", banco_data['id']).execute()
                                            pago_exitoso = True
                                        else: # Bizum
                                            pago_exitoso = True
                                            
                                        if pago_exitoso:
                                            puntos_ganados_total = 0
                                            
                                            if es_multi:
                                                cantidad_restante = float(cantidad_abonar)
                                                for _, r_tk in deudas_cliente.iterrows():
                                                    if cantidad_restante <= 0:
                                                        break
                                                        
                                                    tk_id_mult = r_tk['id']
                                                    tk_pendiente = float(r_tk['pendiente'])
                                                    tk_total = float(r_tk['total'])
                                                    tk_pagado_ant = float(r_tk.get('pagado', 0.0) or 0.0)
                                                    
                                                    if cantidad_restante >= tk_pendiente:
                                                        puntos_tk = int(tk_total // 10)
                                                        puntos_ganados_total += puntos_tk
                                                        client.table("ventas_historial").update({"estado": "Completado", "pendiente": 0.0, "pagado": tk_total, "puntos_ganados": puntos_tk}).eq("id", tk_id_mult).execute()
                                                        cantidad_restante -= tk_pendiente
                                                    else:
                                                        nuevo_pendiente = tk_pendiente - cantidad_restante
                                                        nuevo_pagado = tk_pagado_ant + cantidad_restante
                                                        client.table("ventas_historial").update({"estado": "Deuda", "pendiente": round(nuevo_pendiente, 2), "pagado": round(nuevo_pagado, 2)}).eq("id", tk_id_mult).execute()
                                                        cantidad_restante = 0
                                            else:
                                                tk_total = float(row_tk['total'])
                                                tk_pagado_ant = float(row_tk.get('pagado', 0.0) or 0.0)
                                                
                                                nuevo_pendiente = total_debe - cantidad_abonar
                                                nuevo_pagado = tk_pagado_ant + cantidad_abonar
                                                
                                                if nuevo_pendiente <= 0.01:
                                                    puntos_ganados_total = int(tk_total // 10)
                                                    client.table("ventas_historial").update({"estado": "Completado", "pendiente": 0.0, "pagado": tk_total, "puntos_ganados": puntos_ganados_total}).eq("id", tk_id).execute()
                                                else:
                                                    client.table("ventas_historial").update({"estado": "Deuda", "pendiente": round(nuevo_pendiente, 2), "pagado": round(nuevo_pagado, 2)}).eq("id", tk_id).execute()
                                                
                                            if puntos_ganados_total > 0:
                                                res_cli = fetch_cliente_puntos_crm(client, cli_saldar)
                                                if res_cli.data:
                                                    c_id = res_cli.data[0]['id']
                                                    c_pts = res_cli.data[0].get('puntos', 0)
                                                    client.table("clientes").update({"puntos": c_pts + puntos_ganados_total}).eq("id", c_id).execute()
                                                    
                                            st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                            limpiar_cache_crm()
                                            msg_succ = f"¡Abono de {cantidad_abonar:.2f}€ registrado! Puntos ganados: {puntos_ganados_total}."
                                            st.success(msg_succ); time.sleep(2); st.rerun()
                    else:
                        st.success("No hay deudas registradas asociadas a clientes.")
                else:
                    st.success("¡Genial! Ningún cliente tiene pagos pendientes en el TPV.")
            except Exception as e:
                st.error(f"Error al cargar módulo de deudas: {e}")