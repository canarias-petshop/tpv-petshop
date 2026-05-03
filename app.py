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
        [data-testid="stToolbar"], #st-viewer-badge, [data-testid="viewerBadge"] 
        {display: none !important;}

        /* Estilo para alertas de vencimiento */
        .vencido { color: #d32f2f; font-weight: bold; background-color: #ffebee; padding: 2px 5px; border-radius: 3px; }
        .proximo { color: #f9a825; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MEMORIA DE LA SESIÓN ---
if 'carrito' not in st.session_state: st.session_state['carrito'] = []
if 'acceso_concedido' not in st.session_state: st.session_state.acceso_concedido = False
if 'ticket_html' not in st.session_state: st.session_state['ticket_html'] = None
if 'ticket_actual' not in st.session_state: st.session_state.ticket_actual = None

# --- 3. SEGURIDAD (CANDADO) ---
if not st.session_state.acceso_concedido:
    st.header("🔒 Acceso Restringido - Animalarium")
    col_c1, col_c2, col_c3 = st.columns([1,2,1])
    with col_c2:
        clave = st.text_input("Contraseña de tienda:", type="password")
        if st.button("Entrar", use_container_width=True):
            if clave == st.secrets["password"]:
                st.session_state.acceso_concedido = True
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
c_logo, c_titulo = st.columns([0.08, 0.92], vertical_alignment="center")
with c_logo:
    try: st.image("LOGO.jpg", width=60)
    except: st.markdown("<h2 style='margin:0; padding:0;'>🐾</h2>", unsafe_allow_html=True)
with c_titulo:
    st.markdown("<h1 style='margin: 0; padding: 0; font-size: 1.8rem; line-height: 1;'>Animalarium - TPV</h1>", unsafe_allow_html=True)

# DEFINICIÓN CORRECTA DE LAS 11 PESTAÑAS
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
    "📦 Inventario", "🛒 Caja", "👥 Clientes", "📜 Historial", 
    "💰 Control Caja", "📈 Estadísticas", "🚚 Proveedores", "📑 Facturación",
    "📊 Contabilidad", "📅 Agenda", "🏦 Bancos"
])

# ==========================================
# --- TAB 1: INVENTARIO Y SERVICIOS ---
# ==========================================
with tab1:
    render_pestana_inventario(client)

# ==========================================
# --- TAB 2: CAJA Y TERMINAL DE VENTA ---
# ==========================================
with tab2:
    render_pestana_tpv(client)


# ==========================================
# --- TAB 3: CLIENTES Y MASCOTAS (CRM) ---
# ==========================================
with tab3:
    render_pestana_crm(client)

# ==========================================
# --- TAB 4: HISTORIAL (VERSIÓN CON CASILLA DE VER) ---
# ==========================================
with tab4:
    render_pestana_historial(client)

# ==========================================
# --- TAB 5: CONTROL DE CAJA FUERTE ---
# ==========================================
with tab5:
    render_pestana_caja(client)

# ==========================================
# --- TAB 6: ESTADÍSTICAS ---
# ==========================================
with tab6:
    render_pestana_estadisticas(client)

# ==========================================
# --- TAB 7: PROVEEDORES ---
# ==========================================
with tab7:
    render_pestana_proveedores(client)

# ==========================================
# --- TAB 8: FACTURACIÓN LEGAL Y STOCK ---
# ==========================================
with tab8:
    render_pestana_facturacion(client)

# ==========================================
# --- TAB 9: CONTABILIDAD E INFORMES PARA ASESORÍA ---
# ==========================================
with tab9:
    render_pestana_contabilidad(client)

# ==========================================
# --- TAB 10: AGENDA Y CITAS ---
# ==========================================
with tab10:
    render_pestana_agenda(client)

# ==========================================
# --- TAB 11: BANCOS Y TESORERÍA ---
# ==========================================
with tab11:
    render_pestana_bancos(client)