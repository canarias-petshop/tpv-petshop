import streamlit as st
import pandas as pd
from postgrest import SyncPostgrestClient
from datetime import datetime, date, timedelta
import time
import json
import urllib.parse
import streamlit.components.v1 as components
import io
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
from personal import render_pestana_personal

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="Animalarium TPV", layout="wide")

st.markdown("""
    <style>
        /* 1. Ajuste del contenedor para aprovechar el ancho sin aplastar */
        .block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; max-width: 98% !important; }
        
        /* 2. Textos y etiquetas más legibles en tablet */
        p, .stMarkdown, div[data-testid="stMarkdownContainer"] { font-size: 1.05rem !important; }
        label { font-size: 1.1rem !important; font-weight: 500 !important; margin-bottom: 2px !important; }
        
        /* 3. Cuadros de texto y números más grandes para escribir fácil */
        input, select { font-size: 1.1rem !important; padding: 8px !important; }
        .stSelectbox, .stTextInput, .stNumberInput { margin-bottom: 0px !important; }
        
        /* 4. Botones: tamaño adecuado para uso táctil sin ser excesivos */
        .stButton > button {
            min-height: 48px !important;
            font-size: 1.1rem !important;
            font-weight: bold !important;
            padding: 0.25rem 0.5rem !important;
        }

        /* 5. Pestañas principales ajustadas */
        button[data-baseweb="tab"] {
            font-size: 1.1rem !important;
            padding-top: 10px !important;
            padding-bottom: 10px !important;
        }
        
        /* 6. Espaciado entre columnas (quitamos el estrechamiento) */
        [data-testid="column"] { padding: 0 8px !important; }

        /* 7. Reducir el gap o hueco vertical entre elementos de Streamlit */
        div[data-testid="stVerticalBlock"] > div { gap: 0.5rem !important; }
        div.element-container { margin-bottom: 0.2rem !important; }
        
        /* Ocultar elementos de Streamlit */
        [data-testid="stHeader"], [data-testid="stFooter"], footer, 
        [data-testid="stAppDeployButton"], .stDeployButton, 
        [data-testid="stToolbar"], #st-viewer-badge, [data-testid="viewerBadge"],
        #MainMenu, .stActionButton, [data-testid="manage-app-button"]
        {display: none !important;}

        /* Estilo para alertas de vencimiento */
        .vencido { color: #d32f2f; font-weight: bold; background-color: #ffebee; padding: 2px 5px; border-radius: 3px; }
        .proximo { color: #f9a825; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

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

# --- DEFINICIÓN DINÁMICA DE PESTAÑAS SEGÚN ROL ---
nombres_pestanas = [
    "📦 Inventario", "🛒 Caja", "👥 Clientes", "📜 Historial", 
    "💰 Control Caja", "📈 Estadísticas", "🚚 Proveedores", "📑 Facturación",
    "📅 Agenda", "⏱️ Personal"
]

# Si es Administrador, inyectamos las pestañas sensibles
if st.session_state.rol == "Admin":
    nombres_pestanas.insert(8, "📊 Contabilidad")
    nombres_pestanas.append("🏦 Bancos")

tabs = st.tabs(nombres_pestanas)

# Renderizamos las pestañas comunes (las primeras 8 siempre son las mismas)
with tabs[0]: render_pestana_inventario(client)
with tabs[1]: render_pestana_tpv(client)
with tabs[2]: render_pestana_crm(client)
with tabs[3]: render_pestana_historial(client)
with tabs[4]: render_pestana_caja(client)
with tabs[5]: render_pestana_estadisticas(client)
with tabs[6]: render_pestana_proveedores(client)
with tabs[7]: render_pestana_facturacion(client)

# Las últimas pestañas cambian de posición/existencia según el rol
if st.session_state.rol == "Admin":
    with tabs[8]: render_pestana_contabilidad(client)
    with tabs[9]: render_pestana_agenda(client)
    with tabs[10]: render_pestana_personal(client)
    with tabs[11]: render_pestana_bancos(client)
else:
    # El empleado no tiene Contabilidad ni Bancos, por lo que la pestaña 8 ahora es Agenda
    with tabs[8]: render_pestana_agenda(client)
    with tabs[9]: render_pestana_personal(client)