import streamlit as st
import pandas as pd
from postgrest import SyncPostgrestClient
from datetime import datetime, date, timedelta
import time
import json
import urllib.parse
import hashlib
import re
from zoneinfo import ZoneInfo
import streamlit.components.v1 as components
from caja import render_pestana_caja
from inventario import render_pestana_inventario
from crm import render_pestana_crm
from historial import render_pestana_historial
from facturacion import render_pestana_facturacion
from tpv import render_pestana_tpv
from estadisticas import render_pestana_estadisticas
from bancos import render_pestana_bancos
from agenda import render_pestana_agenda
from proveedores import render_pestana_proveedores
from contabilidad import render_pestana_contabilidad
from servicios_animalarium import render_pestana_servicios
from personal import render_pestana_personal
from manual import render_pestana_manual
from marketing import render_pestana_marketing
from tareas import render_pestana_tareas
from proyectos_eventos import render_pestana_proyectos_eventos

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="Animalarium TPV", layout="wide")

st.markdown("""
    <style>
        /* 1. Ajuste del contenedor para aprovechar el ancho sin aplastar y subir el contenido */
        .block-container { padding-top: 0rem !important; margin-top: -1rem !important; padding-bottom: 0.5rem !important; max-width: 98% !important; }
        
        /* 2. Espaciado entre columnas (quitamos el estrechamiento) */
        [data-testid="column"] { padding: 0 8px !important; }

        /* 3. Reducir el gap o hueco vertical entre elementos de Streamlit en PC */
        div[data-testid="stVerticalBlock"] > div { gap: 0.5rem !important; }
        div.element-container { margin-bottom: 0.2rem !important; }
        
        /* 4. Ocultar elementos de menú de Streamlit (sin barra lateral no necesitamos cabecera) */
        [data-testid="stHeader"], [data-testid="stFooter"], footer, 
        [data-testid="stAppDeployButton"], .stDeployButton, 
        [data-testid="stToolbar"], #st-viewer-badge, [data-testid="viewerBadge"],
        #MainMenu, .stActionButton, [data-testid="manage-app-button"]
        {display: none !important;}

        /* Estilo para alertas de vencimiento */
        .vencido { color: #d32f2f; font-weight: bold; background-color: #ffebee; padding: 2px 5px; border-radius: 3px; }
        .proximo { color: #f9a825; font-weight: bold; }
        
        /* 5. Textos y etiquetas más legibles en tablet/PC */
        p, .stMarkdown, div[data-testid="stMarkdownContainer"] { font-size: 1.05rem !important; }
        label { font-size: 1.1rem !important; font-weight: 500 !important; margin-bottom: 2px !important; }
        
        /* 6. Cuadros de texto y números más grandes para escribir fácil */
        div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input, select { font-size: 1.1rem !important; padding: 8px !important; }
        div[data-testid="stTimeInput"] input, div[data-testid="stDateInput"] input { font-size: 1.1rem !important; }
        .stSelectbox, .stTextInput, .stNumberInput { margin-bottom: 0px !important; }
        
        /* 7. Botones: tamaño adecuado */
        .stButton > button {
            min-height: 48px !important;
            font-size: 1.1rem !important;
            font-weight: bold !important;
            padding: 0.25rem 0.5rem !important;
        }

        /* 8. Pestañas principales ajustadas */
        button[data-baseweb="tab"] {
            font-size: 1.1rem !important;
            padding-top: 10px !important;
            padding-bottom: 10px !important;
        }
    </style>
    """, unsafe_allow_html=True)

# --- JS GLOBAL PARA DESACTIVAR EL AUTOCORRECTOR EN TABLETS ---
components.html("""
<script>
    const doc = window.parent.document;
    function disableAuto() {
        const inputs = doc.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            if (input.getAttribute('data-autofill-blocked') !== 'true') {
                // Bloqueo agresivo de autocompletado y gestores de contraseñas
                input.setAttribute('autocomplete', 'off-random-string');
                input.setAttribute('data-lpignore', 'true');
                input.setAttribute('data-form-type', 'other');
                input.setAttribute('data-1p-ignore', 'true');
                input.setAttribute('data-bwignore', 'true');
                input.setAttribute('autocorrect', 'off');
                input.setAttribute('autocapitalize', 'off');
                input.setAttribute('spellcheck', 'false');
                
                // Truco para evitar que las contraseñas se autocompleten al cargar la página
                if (input.type === 'password' && !input.hasAttribute('readonly-trick')) {
                    input.setAttribute('readonly', 'readonly');
                    input.addEventListener('focus', function() { this.removeAttribute('readonly'); });
                    input.addEventListener('blur', function() { if (this.value === '') this.setAttribute('readonly', 'readonly'); });
                    input.setAttribute('readonly-trick', 'true');
                }

                if (!input.hasAttribute('data-autoselect')) {
                    if (input.type !== 'time' && input.type !== 'date') {
                        input.addEventListener('focus', function() { try { this.select(); } catch(e){} });
                    }
                    input.setAttribute('data-autoselect', 'true');
                }
                
                input.setAttribute('data-autofill-blocked', 'true');
            }
        });
            
            // Protección Global contra Doble Clic en Botones
            const buttons = doc.querySelectorAll('button');
            buttons.forEach(btn => {
                if (!btn.hasAttribute('data-dblclick-prot')) {
                    btn.setAttribute('data-dblclick-prot', 'true');
                    btn.addEventListener('click', function() {
                        if (this.getAttribute('data-baseweb') === 'tab') return;
                        
                        const text = this.innerText.toUpperCase();
                        const isAction = text.includes('GUARDAR') || text.includes('COBRAR') || 
                                         text.includes('REGISTRAR') || text.includes('CONFIRMAR') || 
                                         text.includes('EMITIR') || text.includes('AÑADIR') || 
                                         text.includes('FINALIZAR') || text.includes('ARCHIVAR') || 
                                         text.includes('ABRIR') || text.includes('CERRAR') ||
                                         text.includes('CREAR');
                                         
                        if (isAction || this.getAttribute('type') === 'submit' || this.getAttribute('kind') === 'primary') {
                            setTimeout(() => {
                                this.style.pointerEvents = 'none';
                                this.style.opacity = '0.5';
                            }, 20);
                            
                            setTimeout(() => {
                                this.style.pointerEvents = 'auto';
                                this.style.opacity = '1';
                            }, 4000);
                        }
                    });
                }
            });
    }
    const observer = new MutationObserver(disableAuto);
    observer.observe(doc.body, { childList: true, subtree: true });
    disableAuto();
</script>
""", height=0)

# --- 2. MEMORIA DE LA SESIÓN ---
if 'carrito' not in st.session_state: st.session_state['carrito'] = []
if 'acceso_concedido' not in st.session_state: st.session_state.acceso_concedido = False
if 'ticket_actual' not in st.session_state: st.session_state.ticket_actual = None
if 'rol' not in st.session_state: st.session_state.rol = None

# --- 3. SEGURIDAD (CANDADO) ---
# --- 3. SEGURIDAD (CANDADO Y ROLES) ---
if not st.session_state.acceso_concedido:
    st.header("🔒 Acceso Restringido - Animalarium")
    col_c1, col_c2, col_c3 = st.columns([1,2,1])
    with col_c2:
        clave = st.text_input("Contraseña de acceso:", type="password")
        if st.button("Entrar", use_container_width=True):
            # Recuperamos las contraseñas de los secretos (con fallback temporal por si no lo has actualizado)
            pass_admin = st.secrets.get("password_admin", st.secrets.get("password", ""))
            pass_emp = st.secrets.get("password_empleado", "empleado123")
            
            if clave == pass_admin:
                st.session_state.acceso_concedido = True
                st.session_state.rol = "Admin"
                st.rerun()
            elif clave == pass_emp:
                st.session_state.acceso_concedido = True
                st.session_state.rol = "Empleado"
                st.rerun()
            else: st.error("Incorrecta")
    st.stop()

# --- 4. CONEXIÓN A SUPABASE ---
def init_supabase() -> SyncPostgrestClient:
    try:
        # Limpieza extrema por si se han colado espacios, comillas o rutas duplicadas en la nube
        raw_url = st.secrets['url'].strip().strip('"').strip("'").rstrip('/')
        if raw_url.endswith('/rest/v1'):
            api_url = raw_url
        else:
            api_url = f"{raw_url}/rest/v1"
            
        api_key = st.secrets['key'].strip().strip('"').strip("'")

        cliente = SyncPostgrestClient(
            api_url, 
            headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"}
        )
        # Test de conexión rápido para atrapar fallos de credenciales o tablas faltantes
        cliente.table("proveedores").select("id").limit(1).execute()
        return cliente
    except Exception as e:
        st.error("🚨 **Error de Conexión a la Base de Datos**")
        if "relation" in str(e) and "does not exist" in str(e):
            st.error("🛠️ **Diagnóstico:** Tu app se conectó a Supabase, pero la tabla no existe. Parece que la base de datos está vacía.")
            st.info("💡 **Solución:** Entra en tu panel de Supabase, ve a 'SQL Editor' y ejecuta el código para crear las tablas del proyecto.")
        else:
            st.error(f"Detalle técnico: {e}")
        st.stop()

client = init_supabase()

# --- 3.5 GUARDIÁN DE FICHAJES (CONTROL DE PRESENCIA) ---
if 'alertas_fichaje_ignoradas' not in st.session_state:
    st.session_state.alertas_fichaje_ignoradas = []

def comprobar_fichajes_pendientes():
    try:
        ahora_dt = datetime.now(ZoneInfo("Atlantic/Canary"))
        hoy_str = ahora_dt.date().isoformat()
        
        res_cuad = client.table("personal_cuadrantes").select("empleado_id, turno, personal_empleados(nombre, pin_fichaje)").eq("fecha", hoy_str).execute()
        if not res_cuad.data: return None
        
        res_fich = client.table("personal_fichajes").select("id, empleado_id, hora_entrada, hora_salida").eq("fecha", hoy_str).execute()
        fichajes_hoy = res_fich.data if res_fich.data else []
        
        for emp_cuad in res_cuad.data:
            turno = str(emp_cuad['turno']).lower()
            if 'libre' in turno or 'vacaciones' in turno: continue
            
            times = re.findall(r'(\d{1,2}:\d{2})', turno)
            if len(times) >= 2:
                for i in range(0, len(times), 2):
                    try:
                        h_ini = datetime.strptime(times[i], "%H:%M").replace(year=ahora_dt.year, month=ahora_dt.month, day=ahora_dt.day, tzinfo=ZoneInfo("Atlantic/Canary"))
                        h_fin = datetime.strptime(times[i+1], "%H:%M").replace(year=ahora_dt.year, month=ahora_dt.month, day=ahora_dt.day, tzinfo=ZoneInfo("Atlantic/Canary"))
                    except: continue
                    
                    f_emp = [f for f in fichajes_hoy if f['empleado_id'] == emp_cuad['empleado_id']]
                    is_clocked_in = any(f['hora_salida'] is None for f in f_emp)
                    has_clocked_in_for_this_shift = False
                    
                    for f in f_emp:
                        try:
                            h_ent = datetime.fromisoformat(f['hora_entrada'])
                            if h_ent.tzinfo is None: h_ent = h_ent.replace(tzinfo=ZoneInfo("Atlantic/Canary"))
                            if h_ini - timedelta(minutes=60) <= h_ent <= h_fin:
                                has_clocked_in_for_this_shift = True
                                break
                        except: pass
                    
                    # 1. BLOQUEO DE ENTRADA
                    if ahora_dt >= h_ini and not has_clocked_in_for_this_shift:
                        alert_id = f"IN_{emp_cuad['empleado_id']}_{h_ini.strftime('%H:%M')}"
                        if alert_id not in st.session_state.alertas_fichaje_ignoradas:
                            return {"tipo": "ENTRADA", "empleado": emp_cuad['personal_empleados']['nombre'], "hora": h_ini, "id": alert_id, "emp_id": emp_cuad['empleado_id'], "pin": emp_cuad['personal_empleados']['pin_fichaje']}
                    
                    # 2. AVISO DE SALIDA
                    if ahora_dt >= h_fin - timedelta(minutes=5) and is_clocked_in:
                        alert_id = f"OUT_{emp_cuad['empleado_id']}_{h_fin.strftime('%H:%M')}"
                        if alert_id not in st.session_state.alertas_fichaje_ignoradas:
                            f_abierto = next(f for f in f_emp if f['hora_salida'] is None)
                            return {"tipo": "SALIDA", "empleado": emp_cuad['personal_empleados']['nombre'], "hora": h_fin, "id": alert_id, "emp_id": emp_cuad['empleado_id'], "pin": emp_cuad['personal_empleados']['pin_fichaje'], "f_abierto": f_abierto}
    except Exception as e: pass
    return None

# El administrador entra libremente sin ser bloqueado por el guardián
bloqueo = None
if st.session_state.get('rol') != "Admin":
    bloqueo = comprobar_fichajes_pendientes()

if bloqueo:
    if bloqueo['tipo'] == "ENTRADA":
        st.error(f"### 🚨 Control de Presencia: Falta Fichaje")
        st.warning(f"El turno de **{bloqueo['empleado']}** comenzaba a las **{bloqueo['hora'].strftime('%H:%M')}** y no consta su entrada en el sistema.")
        c1, c2 = st.columns(2)
        with c1:
            with st.form("f_in"):
                st.write(f"**✔️ Fichar Ahora ({bloqueo['empleado']})**")
                pin_in = st.text_input("Tu PIN de 4 dígitos", type="password", max_chars=4)
                if st.form_submit_button("Registrar Entrada", type="primary", use_container_width=True):
                    if pin_in == bloqueo['pin']:
                        ahora_dt = datetime.now(ZoneInfo("Atlantic/Canary"))
                        ahora_iso = ahora_dt.isoformat()
                        
                        # --- BLOQUEO DE SEGURIDAD DE 30 MINUTOS ---
                        res_ult = client.table("personal_fichajes").select("*").eq("empleado_id", bloqueo['emp_id']).eq("fecha", bloqueo['hora'].date().isoformat()).order("id", desc=True).limit(1).execute()
                        if res_ult.data:
                            bloquear_fichaje = False
                            m_diff = 0
                            str_h = res_ult.data[0].get('hora_salida') or res_ult.data[0].get('hora_entrada')
                            if str_h:
                                try:
                                    h_ult = datetime.fromisoformat(str_h)
                                    if h_ult.tzinfo is None: h_ult = h_ult.replace(tzinfo=ZoneInfo("Atlantic/Canary"))
                                    else: h_ult = h_ult.astimezone(ZoneInfo("Atlantic/Canary"))
                                    m_diff = int((ahora_dt - h_ult).total_seconds() / 60)
                                    bloquear_fichaje = m_diff < 30
                                except Exception:
                                    bloquear_fichaje = False
                                    m_diff = 0
                                    
                            if bloquear_fichaje:
                                st.error(f"⏳ Bloqueo temporal anti-errores. El usuario ya fichó hace {m_diff} minuto(s).")
                                st.stop()
                                
                        res_last = client.table("personal_fichajes").select("hash_actual").order("id", desc=True).limit(1).execute()
                        hash_anterior = res_last.data[0].get("hash_actual", "") if res_last.data else ""
                        data_to_hash = f"FICHAJE|IN|{bloqueo['emp_id']}|{ahora_iso}|{hash_anterior}"
                        hash_actual = hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest().upper()
                        client.table("personal_fichajes").insert({"empleado_id": bloqueo['emp_id'], "fecha": bloqueo['hora'].date().isoformat(), "hora_entrada": ahora_iso, "hash_anterior": hash_anterior, "hash_actual": hash_actual}).execute()
                        st.session_state.alertas_fichaje_ignoradas.append(bloqueo['id'])
                        st.success("Entrada registrada."); time.sleep(1); st.rerun()
                    else: st.error("PIN incorrecto.")
        with c2:
            with st.form("f_in_skip"):
                st.write("**⏭️ Desbloquear Sistema (Compañeros)**")
                st.selectbox("Motivo del retraso/ausencia", ["Aún no ha llegado (Retraso)", "No viene hoy (Baja/Permiso)", "Fichará luego"])
                if st.form_submit_button("Saltar este aviso", use_container_width=True):
                    st.session_state.alertas_fichaje_ignoradas.append(bloqueo['id']); st.rerun()
    else:
        st.warning(f"### 🔔 Recordatorio de Salida")
        st.info(f"El turno de **{bloqueo['empleado']}** finaliza a las **{bloqueo['hora'].strftime('%H:%M')}**. Por favor, no olvides registrar tu salida.")
        c1, c2 = st.columns(2)
        with c1:
            with st.form("f_out"):
                st.write(f"**✔️ Fichar Salida ({bloqueo['empleado']})**")
                pin_out = st.text_input("Tu PIN de 4 dígitos", type="password", max_chars=4)
                if st.form_submit_button("Registrar Salida", type="primary", use_container_width=True):
                    if pin_out == bloqueo['pin']:
                        ahora_dt = datetime.now(ZoneInfo("Atlantic/Canary"))
                        ahora_iso = ahora_dt.isoformat()
                        
                        # --- BLOQUEO DE SEGURIDAD DE 30 MINUTOS ---
                        res_ult = client.table("personal_fichajes").select("*").eq("empleado_id", bloqueo['emp_id']).eq("fecha", bloqueo['hora'].date().isoformat()).order("id", desc=True).limit(1).execute()
                        if res_ult.data:
                            bloquear_fichaje = False
                            m_diff = 0
                            str_h = res_ult.data[0].get('hora_salida') or res_ult.data[0].get('hora_entrada')
                            if str_h:
                                try:
                                    h_ult = datetime.fromisoformat(str_h)
                                    if h_ult.tzinfo is None: h_ult = h_ult.replace(tzinfo=ZoneInfo("Atlantic/Canary"))
                                    else: h_ult = h_ult.astimezone(ZoneInfo("Atlantic/Canary"))
                                    m_diff = int((ahora_dt - h_ult).total_seconds() / 60)
                                    bloquear_fichaje = m_diff < 30
                                except Exception:
                                    bloquear_fichaje = False
                                    m_diff = 0
                                    
                            if bloquear_fichaje:
                                st.error(f"⏳ Bloqueo temporal anti-errores. El usuario ya fichó hace {m_diff} minuto(s).")
                                st.stop()
                                
                        f_abierto = bloqueo['f_abierto']
                        h_ent = datetime.fromisoformat(f_abierto['hora_entrada'])
                        if h_ent.tzinfo is None: h_ent = h_ent.replace(tzinfo=ZoneInfo("Atlantic/Canary"))
                        minutos = int((ahora_dt - h_ent).total_seconds() / 60)
                        res_last = client.table("personal_fichajes").select("hash_anterior").eq("id", f_abierto['id']).execute()
                        hash_ant = res_last.data[0].get("hash_anterior", "") if res_last.data else ""
                        data_to_hash = f"FICHAJE|OUT|{bloqueo['emp_id']}|{f_abierto['hora_entrada']}|{ahora_iso}|{hash_ant}"
                        hash_actual = hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest().upper()
                        client.table("personal_fichajes").update({"hora_salida": ahora_iso, "minutos_trabajados": minutos, "hash_actual": hash_actual}).eq("id", f_abierto['id']).execute()
                        st.session_state.alertas_fichaje_ignoradas.append(bloqueo['id'])
                        st.success("Salida registrada."); time.sleep(1); st.rerun()
                    else: st.error("PIN incorrecto.")
        with c2:
            with st.form("f_out_skip"):
                st.write("**⏭️ Posponer Aviso**")
                st.selectbox("Motivo", ["Sigue atendiendo clientes", "Saldrá más tarde", "Limpiando tienda"])
                if st.form_submit_button("Posponer aviso", use_container_width=True):
                    st.session_state.alertas_fichaje_ignoradas.append(bloqueo['id']); st.rerun()
    st.markdown("---")

# --- CABECERA COMPACTA ---
c_logo, c_titulo, c_rol = st.columns([0.08, 0.82, 0.10], vertical_alignment="center")
with c_logo:
    try: st.image("LOGO.jpg", width=60)
    except: st.markdown("<h2 style='margin:0; padding:0;'>🐾</h2>", unsafe_allow_html=True)
with c_titulo:
    st.markdown("<h1 style='margin: 0; padding: 0; font-size: 1.8rem; line-height: 1;'>Animalarium - TPV</h1>", unsafe_allow_html=True)
with c_rol:
    st.markdown(f"<div style='text-align:right; font-weight:bold; color:#005275; font-size:14px;'>👤 {st.session_state.rol}</div>", unsafe_allow_html=True)
    if st.button("Salir", key="btn_logout", use_container_width=True):
        st.session_state.acceso_concedido = False
        st.session_state.rol = None
        st.rerun()

# --- ALERTA GLOBAL DE PEDIDOS WEB ---
try:
    res_pedidos = client.table("encargos_clientes").select("id").eq("origen", "Web").eq("estado", "Recibido").execute()
    if res_pedidos.data and len(res_pedidos.data) > 0:
        st.error(f"🚨 **¡ATENCIÓN! Tienes {len(res_pedidos.data)} pedido(s) web nuevo(s) sin revisar.** Ve a la pestaña 'Clientes' -> 'Encargos' para gestionarlo(s).")
except:
    pass

# --- ALERTA GLOBAL DE PEDIDOS MANUALES A PROVEEDORES ---
try:
    from proveedores import fetch_proveedores, get_alertas_manuales
    res_provs = fetch_proveedores(client)
    if res_provs.data:
        alertas_pendientes = get_alertas_manuales(res_provs.data)["urgentes"]
        if alertas_pendientes:
            nombres_provs = ", ".join([a['proveedor'] for a in alertas_pendientes])
            st.warning(f"⏰ **ALERTA DE PROVEEDORES:** Tienes {len(alertas_pendientes)} pedido(s) urgente(s) pendiente(s) de realizar ({nombres_provs}). Ve a 'Proveedores y Pedidos' para registrarlo(s).")
except:
    pass

# --- DEFINICIÓN DINÁMICA DE PESTAÑAS SEGÚN ROL ---
if st.session_state.rol == "Admin":
    nombres_pestanas = [
        "💰 Control Caja", "🛒 Caja", "📜 Historial", "👥 Clientes", 
        "📦 Inventario", "🚚 Proveedores y Pedidos", "📅 Agenda", "📑 Facturación", 
        "🐶 Servicios Animalarium", "📊 Contabilidad", "🎯 Marketing y Ofertas", "🗓️ Proyectos y Eventos",
        "📈 Estadísticas", "⏱️ Personal", "🏦 Bancos", "✅ Tareas", "📖 Ayuda"
    ]
else:
    nombres_pestanas = [
        "💰 Control Caja", "🛒 Caja", "📜 Historial", "👥 Clientes", 
        "📦 Inventario", "🚚 Proveedores y Pedidos", "📅 Agenda", 
        "🐶 Servicios Animalarium", "⏱️ Personal", "✅ Tareas", "📖 Ayuda"
    ]

if "seccion_principal_key" not in st.session_state:
    st.session_state.seccion_principal_key = nombres_pestanas[0]

if st.session_state.seccion_principal_key not in nombres_pestanas:
    st.session_state.seccion_principal_key = nombres_pestanas[0]

c_nav1, c_nav2 = st.columns([1, 5])
with c_nav1:
    st.markdown("<div style='padding-top: 10px; font-weight: bold; font-size: 1.1rem;'>🧭 Navegación:</div>", unsafe_allow_html=True)
with c_nav2:
    seccion_principal = st.selectbox("Ir a la sección:", nombres_pestanas, key="seccion_principal_key", label_visibility="collapsed")

if st.session_state.rol == "Admin":
    if seccion_principal == nombres_pestanas[0]: render_pestana_caja(client)
    elif seccion_principal == nombres_pestanas[1]: render_pestana_tpv(client)
    elif seccion_principal == nombres_pestanas[2]: render_pestana_historial(client)
    elif seccion_principal == nombres_pestanas[3]: render_pestana_crm(client)
    elif seccion_principal == nombres_pestanas[4]: render_pestana_inventario(client)
    elif seccion_principal == nombres_pestanas[5]: render_pestana_proveedores(client)
    elif seccion_principal == nombres_pestanas[6]: render_pestana_agenda(client)
    elif seccion_principal == nombres_pestanas[7]: render_pestana_facturacion(client)
    elif seccion_principal == nombres_pestanas[8]: render_pestana_servicios(client)
    elif seccion_principal == nombres_pestanas[9]: render_pestana_contabilidad(client)
    elif seccion_principal == nombres_pestanas[10]: render_pestana_marketing(client)
    elif seccion_principal == nombres_pestanas[11]: render_pestana_proyectos_eventos(client)
    elif seccion_principal == nombres_pestanas[12]: render_pestana_estadisticas(client)
    elif seccion_principal == nombres_pestanas[13]: render_pestana_personal(client)
    elif seccion_principal == nombres_pestanas[14]: render_pestana_bancos(client)
    elif seccion_principal == nombres_pestanas[15]: render_pestana_tareas(client)
    elif seccion_principal == nombres_pestanas[16]: render_pestana_manual()
else:
    if seccion_principal == nombres_pestanas[0]: render_pestana_caja(client)
    elif seccion_principal == nombres_pestanas[1]: render_pestana_tpv(client)
    elif seccion_principal == nombres_pestanas[2]: render_pestana_historial(client)
    elif seccion_principal == nombres_pestanas[3]: render_pestana_crm(client)
    elif seccion_principal == nombres_pestanas[4]: render_pestana_inventario(client)
    elif seccion_principal == nombres_pestanas[5]: render_pestana_proveedores(client)
    elif seccion_principal == nombres_pestanas[6]: render_pestana_agenda(client)
    elif seccion_principal == nombres_pestanas[7]: render_pestana_servicios(client)
    elif seccion_principal == nombres_pestanas[8]: render_pestana_personal(client)
    elif seccion_principal == nombres_pestanas[9]: render_pestana_tareas(client)
    elif seccion_principal == nombres_pestanas[10]: render_pestana_manual()