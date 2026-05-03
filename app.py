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
    st.markdown("<h3 style='margin-bottom: 5px;'>📈 Contabilidad y Estadísticas</h3>", unsafe_allow_html=True)
    st.write("Resumen global de la salud financiera de Animalarium.")
    
    try:
        res_ventas = client.table("ventas_historial").select("created_at, total, estado").execute()
        res_movs = client.table("movimientos_caja").select("created_at, tipo, cantidad").execute()
        
        total_ventas = 0.0
        total_gastos = 0.0
        df_v = pd.DataFrame()
        df_m = pd.DataFrame()

        if res_ventas.data:
            df_v = pd.DataFrame(res_ventas.data)
            df_v = df_v[df_v['estado'] != 'DEVUELTO']
            if not df_v.empty:
                total_ventas = df_v['total'].sum()
                df_v['Fecha'] = pd.to_datetime(df_v['created_at']).dt.date
        
        if res_movs.data:
            df_m = pd.DataFrame(res_movs.data)
            df_m_gastos = df_m[df_m['tipo'] == 'Retirada']
            if not df_m_gastos.empty:
                total_gastos = df_m_gastos['cantidad'].sum()
                df_m['Fecha'] = pd.to_datetime(df_m['created_at']).dt.date

        balance_neto = total_ventas - total_gastos

        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1: st.metric(label="Ingresos Totales (Ventas)", value=f"{total_ventas:.2f} €")
        with col_m2: st.metric(label="Gastos de Caja (Retiradas)", value=f"-{total_gastos:.2f} €")
        with col_m3: st.metric(label="Balance Neto", value=f"{balance_neto:.2f} €", delta=f"{balance_neto:.2f} €")
            
        st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
        st.markdown("**📊 Evolución de Ventas por Día**")
        if not df_v.empty:
            ventas_diarias = df_v.groupby('Fecha')['total'].sum().reset_index()
            ventas_diarias.set_index('Fecha', inplace=True)
            st.bar_chart(ventas_diarias, color="#005275", height=250)
        else:
            st.info("Aún no hay suficientes ventas para generar el gráfico.")

    except Exception as e:
        st.error(f"Error al cargar las estadísticas: {e}") 

# ==========================================
# --- TAB 7: PROVEEDORES ---
# ==========================================
with tab7:
    st.markdown("<h3 style='margin-top:-15px;'>📦 Pedidos a Proveedores</h3>", unsafe_allow_html=True)
    sub_prov, sub_pedidos = st.tabs(["🚚 Directorio Proveedores", "📦 Hacer Pedido a Proveedor"])
    
    with sub_prov:
        cp1, cp2 = st.columns([1, 2])
        with cp1:
            st.markdown("#### ➕ Nuevo Proveedor")
            with st.form("n_prov_full", clear_on_submit=True):
                st.markdown("**Datos Principales**")
                n_emp = st.text_input("Nombre Empresa *")
                c_np1, c_np2 = st.columns(2)
                with c_np1: n_cif = st.text_input("CIF / NIF")
                with c_np2: n_tel = st.text_input("Teléfono Fijo")
                
                c_np3, c_np4 = st.columns(2)
                with c_np3: n_mov = st.text_input("Móvil")
                with c_np4: n_ema = st.text_input("Email")
                
                st.markdown("**Ubicación Rápida**")
                n_dir = st.text_input("Dirección")
                c_np5, c_np6 = st.columns(2)
                with c_np5: n_pob = st.text_input("Población")
                with c_np6: n_pais = st.text_input("País", value="España - Islas Canarias")
                
                n_frec = st.text_input("Días de Reparto", placeholder="Ej: Todos los días, Los martes, Bajo demanda...", value="Bajo demanda")
                n_hora = st.text_input("Hora límite de pedido", placeholder="Ej: 14:00, 20:00, Sin límite...", value="Sin límite")
                
                if st.form_submit_button("Guardar Proveedor", use_container_width=True, type="primary"):
                    if n_emp:
                        client.table("proveedores").insert({
                            "nombre_empresa": n_emp, "cif": n_cif,
                            "telefono": n_tel, "movil": n_mov, "email": n_ema,
                            "direccion": n_dir, "poblacion": n_pob, "pais": n_pais,
                            "frecuencia_reparto": n_frec, "hora_limite": n_hora
                        }).execute()
                        st.success("Guardado"); time.sleep(0.5); st.rerun()
        with cp2:
            st.markdown("#### 📋 Directorio")
            res_p = client.table("proveedores").select("*").execute()
            df_p = None
            ed_p = None
            if res_p.data:
                df_p = pd.DataFrame(res_p.data)
                
                # Aseguramos que las nuevas columnas existan en el DataFrame (por si no has corrido el SQL aún)
                for col in ['telefono', 'movil', 'email', 'direccion', 'poblacion', 'codigo_postal', 'provincia', 'pais', 'codigo_pais', 'idioma', 'forma_pago', 'persona_contacto', 'iban', 'swift', 'notas', 'contacto']:
                    if col not in df_p.columns: df_p[col] = ""
                    
                df_p_vista = df_p[['id', 'nombre_empresa', 'telefono', 'movil', 'email']].copy()
                df_p_vista.insert(0, "Ver Ficha", False)
                
                st.markdown("💡 *Marca **'👁️ Ver Ficha'** para acceder a todos los datos de contacto y facturación.*")
                
                ed_p = st.data_editor(
                    df_p_vista, hide_index=True, use_container_width=True, key="ed_prov", height=250,
                    column_config={
                        "Ver Ficha": st.column_config.CheckboxColumn("👁️ Ver Ficha", default=False),
                        "id": None, "nombre_empresa": "Empresa", "frecuencia_reparto": "Días Reparto", 
                        "telefono": "Teléfono", "email": "Email"
                    }
                )
                
                if st.button("💾 Guardar Cambios Rápidos", type="primary"):
                    for _, row in ed_p.iterrows():
                        if pd.notna(row['id']):
                            client.table("proveedores").update({
                                "nombre_empresa": str(row['nombre_empresa']),
                                "telefono": str(row['telefono']), "frecuencia_reparto": str(row['frecuencia_reparto']), "hora_limite": str(row['hora_limite']), "email": str(row['email'])
                            }).eq("id", row['id']).execute()
                    st.success("Directorio actualizado."); time.sleep(0.5); st.rerun()
                    
        # --- FICHA COMPLETA DEL PROVEEDOR ---
        if df_p is not None and ed_p is not None:
            filas_ver = ed_p[ed_p["Ver Ficha"] == True]
            if not filas_ver.empty:
                p_id = filas_ver.iloc[0]['id']
                p_data = df_p[df_p['id'] == p_id].iloc[0]
                
                st.markdown("---")
                st.markdown(f"#### 🏢 Ficha Completa: **{p_data['nombre_empresa']}**")
                
                # Mostrar datos antiguos si existen para que el usuario pueda copiarlos
                if p_data.get('contacto') and str(p_data['contacto']).strip() and str(p_data['contacto']).strip() != "nan":
                    st.caption(f"💾 *Información antigua registrada:* {p_data['contacto']}")
                
                with st.form(f"ficha_prov_{p_id}", border=True):
                    st.markdown("**1. Información Fiscal y de Contacto**")
                    cf1, cf2, cf3 = st.columns([1.5, 1, 1])
                    with cf1: f_nom = st.text_input("Nombre Empresa *", value=p_data.get('nombre_empresa',''))
                    with cf2: f_cif = st.text_input("CIF / NIF", value=p_data.get('cif',''))
                    with cf3: f_per = st.text_input("Persona de Contacto", value=p_data.get('persona_contacto',''))
                    
                    cf4, cf5, cf6 = st.columns(3)
                    with cf4: f_tel = st.text_input("Teléfono Fijo", value=p_data.get('telefono',''))
                    with cf5: f_mov = st.text_input("Móvil", value=p_data.get('movil',''))
                    with cf6: f_ema = st.text_input("Email", value=p_data.get('email',''))
                    
                    st.markdown("**2. Ubicación**")
                    f_dir = st.text_input("Dirección Completa", value=p_data.get('direccion',''))
                    
                    cf7, cf8, cf9 = st.columns(3)
                    with cf7: f_pob = st.text_input("Población", value=p_data.get('poblacion',''))
                    with cf8: f_cp = st.text_input("Código Postal", value=p_data.get('codigo_postal',''))
                    with cf9: f_prov = st.text_input("Provincia", value=p_data.get('provincia',''))
                    
                    cf10, cf11, cf12, cf16, cf17 = st.columns(5)
                    with cf10: f_pais = st.text_input("País", value=p_data.get('pais',''))
                    with cf11: f_cod_pais = st.text_input("Cód. País", value=p_data.get('codigo_pais',''))
                    with cf12: f_idioma = st.text_input("Idioma", value=p_data.get('idioma',''))
                    with cf16: f_frec = st.text_input("Días de Reparto", value=p_data.get('frecuencia_reparto','Bajo demanda'))
                    with cf17: f_hora = st.text_input("Hora Límite", value=p_data.get('hora_limite','Sin límite'))
                    
                    st.markdown("**3. Facturación y Notas**")
                    cf13, cf14, cf15 = st.columns([1, 1.5, 1])
                    with cf13: f_fpago = st.text_input("Forma de Pago", value=p_data.get('forma_pago',''))
                    with cf14: f_iban = st.text_input("IBAN", value=p_data.get('iban',''))
                    with cf15: f_swift = st.text_input("SWIFT", value=p_data.get('swift',''))
                    
                    f_not = st.text_area("Fax / Otras Notas / Observaciones", value=p_data.get('notas',''))
                    
                    if st.form_submit_button("💾 Guardar Ficha Completa", type="primary", use_container_width=True):
                        if f_nom:
                            client.table("proveedores").update({
                                "nombre_empresa": f_nom, "cif": f_cif, "persona_contacto": f_per,
                                "telefono": f_tel, "movil": f_mov, "email": f_ema, "direccion": f_dir,
                                "poblacion": f_pob, "codigo_postal": f_cp, "provincia": f_prov,
                                "pais": f_pais, "frecuencia_reparto": f_frec, "hora_limite": f_hora,
                                "forma_pago": f_fpago, "iban": f_iban, "swift": f_swift, "notas": f_not, 
                                "contacto": "" # Borramos la línea antigua ya que se ha organizado
                            }).eq("id", p_id).execute()
                            st.success("Ficha del proveedor actualizada correctamente."); time.sleep(0.5); st.rerun()
                        else:
                            st.error("El nombre de la empresa es obligatorio.")

    with sub_pedidos:
        st.markdown("#### 📦 Borrador de Pedidos a Proveedores")
        st.info("💡 **SISTEMA AUTOMÁTICO ACTIVO:** Cuando pulsas 'Auto-Distribuir' en la Pestaña 1, los productos viajan directamente aquí. Una vez cambies el estado del borrador a 'Enviado', el sistema creará un borrador nuevo la próxima vez que falte stock.")
        try:
            res_provs_p = client.table("proveedores").select("id, nombre_empresa, frecuencia_reparto").execute()
            dict_pp = {p['nombre_empresa']: p['id'] for p in res_provs_p.data} if res_provs_p.data else {}
            
            cp_a, cp_b = st.columns([1, 2])
            with cp_a:
                sel_prov_ped = st.selectbox("Selecciona Proveedor para abrir pedido", list(dict_pp.keys()))
                if st.button("Crear Nuevo Borrador", use_container_width=True):
                    client.table("pedidos_proveedores").insert({"proveedor_id": dict_pp[sel_prov_ped], "estado": "Borrador", "productos": []}).execute()
                    st.rerun()
                    
            with cp_b:
                res_ped = client.table("pedidos_proveedores").select("*, proveedores(nombre_empresa, frecuencia_reparto, hora_limite, email)").order("created_at", desc=True).execute()
                if res_ped.data:
                    df_ped = pd.DataFrame(res_ped.data)
                    df_ped['Proveedor'] = df_ped['proveedores'].apply(lambda x: x.get('nombre_empresa', ''))
                    df_ped['Reparto'] = df_ped['proveedores'].apply(lambda x: x.get('frecuencia_reparto', 'Bajo demanda'))
                    df_ped['Corte'] = df_ped['proveedores'].apply(lambda x: x.get('hora_limite', 'Sin límite'))
                    df_ped['Fecha'] = pd.to_datetime(df_ped['created_at']).dt.strftime('%d/%m/%Y')
                    
                    df_ped_vista = df_ped[['id', 'Fecha', 'Proveedor', 'Reparto', 'Corte', 'estado']].copy()
                    df_ped_vista.insert(0, "Borrar", False)
                    df_ped_vista.insert(0, "Ver/Editar", False)
                    
                    ed_ped = st.data_editor(
                        df_ped_vista,
                        hide_index=True, use_container_width=True,
                        column_config={
                            "Ver/Editar": st.column_config.CheckboxColumn("👁️ Ver"),
                            "Borrar": st.column_config.CheckboxColumn("🗑️ Borrar"),
                            "Reparto": st.column_config.TextColumn("Días Envío", disabled=True),
                            "Corte": st.column_config.TextColumn("Hora Límite", disabled=True),
                            "id": None, "estado": st.column_config.SelectboxColumn("Estado", options=["Borrador", "Enviado", "Recibido"])
                        }
                    )
                    
                    # --- LÓGICA DE BORRADO ---
                    filas_borrar = ed_ped[ed_ped["Borrar"] == True]
                    if not filas_borrar.empty:
                        st.error(f"⚠️ Has marcado {len(filas_borrar)} pedido(s) para eliminar.")
                        if st.button("🚨 CONFIRMAR ELIMINACIÓN", type="primary", use_container_width=True):
                            for idx, row in filas_borrar.iterrows():
                                client.table("pedidos_proveedores").delete().eq("id", row['id']).execute()
                            st.success("Pedido(s) eliminado(s) correctamente."); time.sleep(1); st.rerun()
                            
                    if st.button("💾 Guardar Estados de Pedidos"):
                        filas_validas = ed_ped[ed_ped["Borrar"] == False]
                        for _, r in filas_validas.iterrows():
                            client.table("pedidos_proveedores").update({"estado": str(r['estado'])}).eq("id", r['id']).execute()
                        st.rerun()
                        
                    # Mostrar detalle del pedido marcado
                    filas_ped = ed_ped[(ed_ped["Ver/Editar"] == True) & (ed_ped["Borrar"] == False)]
                    if not filas_ped.empty:
                        st.markdown("---")
                        ped_id = filas_ped.iloc[0]['id']
                        ped_data = df_ped[df_ped['id'] == ped_id].iloc[0]
                        st.markdown(f"#### 🛒 Contenido del Borrador #{ped_id} ({ped_data['Proveedor']})")
                        
                        lista_prods_ped = ped_data.get('productos', [])
                        df_prods_ped = pd.DataFrame(lista_prods_ped) if lista_prods_ped else pd.DataFrame(columns=["Producto", "Cantidad"])
                        if 'Producto' not in df_prods_ped.columns: df_prods_ped['Producto'] = ""
                        if 'Cantidad' not in df_prods_ped.columns: df_prods_ped['Cantidad'] = 1
                        
                        ed_prods_ped = st.data_editor(
                            df_prods_ped, use_container_width=True, hide_index=True, num_rows="dynamic",
                            column_config={"Producto": st.column_config.TextColumn("Producto a pedir"), "Cantidad": st.column_config.NumberColumn("Cant.", min_value=1)}
                        )
                        
                        c_pbtn1, c_pbtn2 = st.columns(2)
                        with c_pbtn1:
                            if st.button("💾 Guardar Cambios del Borrador", type="primary", use_container_width=True):
                                df_clean = ed_prods_ped.dropna(subset=['Producto'])
                                df_clean = df_clean[df_clean['Producto'].astype(str).str.strip() != ""]
                                client.table("pedidos_proveedores").update({"productos": json.loads(df_clean.to_json(orient='records'))}).eq("id", ped_id).execute()
                                st.success("Borrador actualizado"); time.sleep(0.5); st.rerun()
                        with c_pbtn2:
                            df_clean_email = ed_prods_ped.dropna(subset=['Producto'])
                            df_clean_email = df_clean_email[df_clean_email['Producto'].astype(str).str.strip() != ""]
                            texto_pedido = f"Hola,\\n\\nAdjunto nuestro pedido a {ped_data['Proveedor']}:\\n\\n"
                            for _, r_ped in df_clean_email.iterrows():
                                texto_pedido += f"- {r_ped['Cantidad']}x {r_ped['Producto']}\\n"
                            texto_pedido += "\\nGracias,\\nAnimalarium"
                            prov_email = ped_data.get('proveedores', {}).get('email', '') if isinstance(ped_data.get('proveedores'), dict) else ''
                            st.markdown(f"<a href='mailto:{prov_email}?subject=Pedido Animalarium&body={urllib.parse.quote(texto_pedido)}' target='_blank'><button style='width:100%; padding:11px; background-color:#005275; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;'>✉️ Generar Email</button></a>", unsafe_allow_html=True)
                            
                        st.markdown("---")
                        st.markdown("##### ➕ Añadir Artículo Manual (Fuera de catálogo / Encargos especiales)")
                        with st.form(f"add_manual_ped_{ped_id}", clear_on_submit=True, border=False):
                            cm1, cm2, cm3 = st.columns([2, 1, 1])
                            with cm1: m_prod = st.text_input("Nombre del producto manual", placeholder="Ej: Correa extensible roja...")
                            with cm2: m_cant = st.number_input("Cantidad", min_value=1, value=1)
                            with cm3: 
                                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                                submit_manual = st.form_submit_button("Añadir al Pedido", use_container_width=True)
                            
                            if submit_manual:
                                if m_prod:
                                    lista_prods_ped.append({"Producto": m_prod, "Cantidad": m_cant})
                                    client.table("pedidos_proveedores").update({"productos": lista_prods_ped}).eq("id", ped_id).execute()
                                    st.success("Artículo añadido."); time.sleep(0.5); st.rerun()
                                else:
                                    st.warning("Escribe el nombre del producto.")
        except:
            pass

# ==========================================
# --- TAB 8: FACTURACIÓN LEGAL Y STOCK ---
# ==========================================
with tab8:
    render_pestana_facturacion(client)

# ==========================================
# --- TAB 9: CONTABILIDAD E INFORMES PARA ASESORÍA ---
# ==========================================
with tab9:
    st.markdown("<h3 style='margin-top: -15px;'>📊 Contabilidad e Informes para Asesoría</h3>", unsafe_allow_html=True)
    
    sec_gastos, sec_informes = st.tabs(["💸 Registro de Gastos", "📂 Panel Avanzado de Descargas"])

    with sec_gastos:
        col_g1, col_g2 = st.columns([1, 2])
        with col_g1:
            with st.form("nuevo_gasto"):
                st.markdown("#### Registrar Gasto o Nómina")
                categoria_gasto = st.selectbox("Categoría Contable", [
                    "Gastos de compra (Limpieza, consumibles...)",
                    "Gastos fijos y variables (Alquileres, seguros, luz, agua...)",
                    "Personal y autónomos (Nóminas, SS...)"
                ])
                concepto = st.text_input("Concepto / Proveedor detallado")
                importe = st.number_input("Importe Total (€)", min_value=0.0, value=None)
                f_vence = st.date_input("Fecha de Vencimiento")
                estado_g = st.selectbox("Estado", ["Pagado", "Pendiente"])
                
                if st.form_submit_button("Guardar Gasto"):
                    if importe is not None and importe > 0 and concepto:
                        client.table("compras").insert({
                            "tipo": f"{categoria_gasto} | {concepto}", "total": float(importe), 
                            "estado": estado_g, "fecha_vencimiento": str(f_vence)
                        }).execute()
                        st.success("Gasto registrado exitosamente."); st.rerun()
                    else:
                        st.error("El importe debe ser mayor que 0 y debes escribir un concepto.")
        
        with col_g2:
            st.markdown("#### Alertas de Vencimientos Pendientes")
            res_comp = client.table("compras").select("*, proveedores(nombre_empresa)").eq("estado", "Pendiente").execute()
            if res_comp.data:
                hoy_date = date.today()
                for c in res_comp.data:
                    dias = (pd.to_datetime(c['fecha_vencimiento']).date() - hoy_date).days
                    clase = "vencido" if dias < 0 else "proximo"
                    nombre = c['proveedores']['nombre_empresa'] if c['proveedores'] else c['tipo']
                    st.markdown(f"<p class='{clase}'>⚠️ {nombre} - {c['total']}€ (Vence en {dias} días: {c['fecha_vencimiento']})</p>", unsafe_allow_html=True)
            else:
                st.info("No hay facturas ni gastos pendientes. ¡Todo al día!")

    with sec_informes:
        st.markdown("#### 📥 Selector de Fechas Personalizado")
        
        c_inf1, c_inf2 = st.columns(2)
        with c_inf1: f_desde_inf = st.date_input("📅 Desde la fecha:", value=date.today().replace(day=1))
        with c_inf2: f_hasta_inf = st.date_input("📅 Hasta la fecha:", value=date.today())
        
        st.markdown(f"<p style='color: gray; font-size: 13px;'>Filtrando datos entre el <b>{f_desde_inf.strftime('%d/%m/%Y')}</b> y el <b>{f_hasta_inf.strftime('%d/%m/%Y')}</b>.</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        fecha_inicio_q = f"{f_desde_inf}T00:00:00"
        fecha_fin_q = f"{f_hasta_inf}T23:59:59"

        # Recuperar datos de Tickets
        res_v_inf = client.table("ventas_historial").select("id, created_at, total, metodo_pago, cliente_deuda").gte("created_at", fecha_inicio_q).lte("created_at", fecha_fin_q).execute()
        # Recuperar datos de Facturas Emitidas
        res_f_inf = client.table("facturas").select("numero_factura, created_at, total_final, forma_pago, clientes(nombre_dueno)").gte("created_at", fecha_inicio_q).lte("created_at", fecha_fin_q).execute()
        # Recuperar datos de Compras/Gastos
        res_c_inf = client.table("compras").select("id, created_at, tipo, total, estado, productos, proveedores(nombre_empresa, cif)").gte("created_at", fecha_inicio_q).lte("created_at", fecha_fin_q).execute()

        # Construir el SUPER INFORME UNIFICADO DE VENTAS
        ventas_unificadas = []
        
        if res_v_inf.data:
            for t in res_v_inf.data:
                ventas_unificadas.append({
                    "Fecha": pd.to_datetime(t['created_at']).strftime('%d/%m/%Y'),
                    "Tipo Documento": "Ticket de Caja",
                    "Nº Documento": f"T-{t['id']}",
                    "Cliente": t.get('cliente_deuda') if t.get('cliente_deuda') else "Mostrador",
                    "Base Imponible (€)": float(t['total']),
                    "Cuota IGIC (€)": 0.00,
                    "Importe Total (€)": float(t['total']),
                    "Método de Pago": t['metodo_pago']
                })
                
        if res_f_inf.data:
            for f in res_f_inf.data:
                cliente_nom = f['clientes']['nombre_dueno'] if f.get('clientes') else "N/A"
                tot_f = float(f['total_final'])
                base_f = round(tot_f / 1.07, 2)
                igic_f = round(tot_f - base_f, 2)
                ventas_unificadas.append({
                    "Fecha": pd.to_datetime(f['created_at']).strftime('%d/%m/%Y'),
                    "Tipo Documento": "Factura por Servicios",
                    "Nº Documento": f"F-{f['numero_factura']}",
                    "Cliente": cliente_nom,
                    "Base Imponible (€)": base_f,
                    "Cuota IGIC (€)": igic_f,
                    "Importe Total (€)": tot_f,
                    "Método de Pago": f['forma_pago']
                })

        df_ventas_unificadas = pd.DataFrame(ventas_unificadas)
        if not df_ventas_unificadas.empty:
            df_ventas_unificadas['Fecha_dt'] = pd.to_datetime(df_ventas_unificadas['Fecha'], format='%d/%m/%Y')
            df_ventas_unificadas = df_ventas_unificadas.sort_values(by="Fecha_dt").drop(columns=['Fecha_dt'])
            
        # --- FUNCIÓN MÁGICA PARA CREAR EXCEL CON FORMATO Y FILA DE TOTALES ---
        def generar_excel_formateado(df, nombre_hoja="Datos"):
            # 1. Calculamos y añadimos la fila de TOTALES debajo
            df_calc = df.copy()
            fila_totales = {}
            for col in df_calc.columns:
                if '€' in col:
                    fila_totales[col] = df_calc[col].sum()
                else:
                    fila_totales[col] = ''
            fila_totales[df_calc.columns[0]] = 'TOTALES'
            df_calc = pd.concat([df_calc, pd.DataFrame([fila_totales])], ignore_index=True)

            output = io.BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            df_calc.to_excel(writer, index=False, sheet_name=nombre_hoja)
            
            workbook = writer.book
            worksheet = writer.sheets[nombre_hoja]
            
            # 2. Formatos profesionales (Cabecera, Celdas Normales, Moneda y Totals)
            formato_cabecera = workbook.add_format({
                'bg_color': '#005275', 'font_color': 'white', 'bold': True,
                'border': 1, 'text_wrap': True, 'align': 'center', 'valign': 'vcenter'
            })
            formato_celda = workbook.add_format({'border': 1, 'valign': 'vcenter'})
            formato_moneda = workbook.add_format({'border': 1, 'valign': 'vcenter', 'num_format': '#,##0.00 €'})
            formato_total = workbook.add_format({'bg_color': '#e8f4f8', 'bold': True, 'border': 1, 'valign': 'vcenter'})
            formato_total_moneda = workbook.add_format({'bg_color': '#e8f4f8', 'bold': True, 'border': 1, 'valign': 'vcenter', 'num_format': '#,##0.00 €'})
            
            # Aplicar bordes a las celdas y auto-ajustar el ancho de las columnas
            for col_num, value in enumerate(df_calc.columns.values):
                worksheet.write(0, col_num, value, formato_cabecera)
                
                # Ancho automático inteligente
                max_len = max([len(str(value))] + [len(str(x)) for x in df_calc[value].astype(str)]) + 2
                worksheet.set_column(col_num, col_num, max_len)
                
                is_currency = ('€' in value)
                
                # Pintar las celdas hacia abajo
                for row_num in range(1, len(df_calc) + 1):
                    es_ultima_fila = (row_num == len(df_calc))
                    celda_val = df_calc.iloc[row_num - 1, col_num]
                    
                    fmt = formato_celda
                    if is_currency: fmt = formato_moneda
                    if es_ultima_fila:
                        fmt = formato_total_moneda if is_currency else formato_total
                        
                    if pd.isna(celda_val) or celda_val == '':
                        worksheet.write_string(row_num, col_num, "", fmt)
                    elif isinstance(celda_val, (int, float)):
                        worksheet.write_number(row_num, col_num, celda_val, fmt)
                    else:
                        worksheet.write_string(row_num, col_num, str(celda_val), fmt)
                
            writer.close()
            return output.getvalue()

        c_down1, c_down2, c_down3 = st.columns(3)
        
        with c_down1:
            st.info("💶 INFORME GLOBAL DE VENTAS (TICKETS + FACTURAS)")
            if not df_ventas_unificadas.empty:
                excel_unificado = generar_excel_formateado(df_ventas_unificadas, "Ventas Totales")
                st.download_button("📥 Descargar Ventas Totales", excel_unificado, f"Ventas_Totales_{f_desde_inf}_al_{f_hasta_inf}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                st.markdown(f"*Total Ventas: {df_ventas_unificadas['Importe Total (€)'].sum():.2f}€*")
            else:
                st.write("Sin ventas en este periodo.")

        with c_down2:
            st.success("📑 SOLO FACTURAS (Para IGIC)")
            if not df_ventas_unificadas.empty:
                df_solo_facturas = df_ventas_unificadas[df_ventas_unificadas['Tipo Documento'] == 'Factura por Servicios'].copy()
                df_asesor_f = df_solo_facturas[['Nº Documento', 'Fecha', 'Cliente', 'Base Imponible (€)', 'Cuota IGIC (€)', 'Importe Total (€)', 'Método de Pago']]
                excel_f = generar_excel_formateado(df_asesor_f, "Facturas Emitidas")
                st.download_button("📥 Descargar Solo Facturas", excel_f, f"Solo_Facturas_{f_desde_inf}_al_{f_hasta_inf}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.write("Sin facturas emitidas.")

        with c_down3:
            st.warning("🚚 COMPRAS Y GASTOS (Tickets y Proveedores)")
            if res_c_inf.data:
                compras_list = []
                for c in res_c_inf.data:
                    cat_contable = "Factura de Proveedor (Mercancía)"
                    concepto = c['tipo']
                    
                    # Separar si es un gasto manual o una nómina
                    if "Gastos de compra" in c['tipo']: cat_contable = "Gastos de Compra (Limpieza, Consumibles)"
                    elif "Gastos fijos" in c['tipo']: cat_contable = "Gastos Fijos y Variables"
                    elif "Personal" in c['tipo']: cat_contable = "Personal y Autónomos"
                    
                    if " | " in c['tipo']:
                        concepto = c['tipo'].split(" | ")[1]

                    base_c = float(c['total'])
                    igic_c = 0.0
                    
                    # Si es una factura de proveedor con artículos registrados, escaneamos su Base e IGIC reales
                    if c.get('productos') and cat_contable == "Factura de Proveedor (Mercancía)":
                        try:
                            df_p = pd.DataFrame(c['productos'])
                            if not df_p.empty and 'Base Ud' in df_p.columns and 'Cantidad' in df_p.columns:
                                if 'Desc %' not in df_p.columns: df_p['Desc %'] = 0.0
                                if 'IGIC %' not in df_p.columns: df_p['IGIC %'] = 0.0
                                
                                base_neta_calc = (pd.to_numeric(df_p['Base Ud']) * pd.to_numeric(df_p['Cantidad'])) * (1 - pd.to_numeric(df_p['Desc %'])/100)
                                igic_eur_calc = base_neta_calc * (pd.to_numeric(df_p['IGIC %'])/100)
                                
                                base_b = base_neta_calc.sum()
                                igic_b = igic_eur_calc.sum()
                                ratio = float(c['total']) / (base_b + igic_b) if (base_b + igic_b) > 0 else 1
                                base_c = round(base_b * ratio, 2)
                                igic_c = round(igic_b * ratio, 2)
                        except: pass
                    
                    prov_nombre = f"{c['proveedores']['nombre_empresa']} ({c['proveedores'].get('cif','')})" if isinstance(c.get('proveedores'), dict) else "Acreedor / Gasto General"
                    
                    compras_list.append({
                        "Nº Interno": c['id'],
                        "Fecha": pd.to_datetime(c['created_at']).strftime('%d/%m/%Y'),
                        "Categoría Contable": cat_contable,
                        "Concepto / Referencia": concepto,
                        "Proveedor / Beneficiario": prov_nombre,
                        "Base Imponible (€)": base_c,
                        "Cuota IGIC (€)": igic_c,
                        "Importe Total (€)": float(c['total']),
                        "Estado": c['estado']
                    })
                
                df_asesor_c = pd.DataFrame(compras_list)
                excel_c = generar_excel_formateado(df_asesor_c, "Gastos y Compras")
                st.download_button("📥 Descargar Compras/Gastos", excel_c, f"Gastos_{f_desde_inf}_al_{f_hasta_inf}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.write("Sin compras o gastos en estas fechas.")

# ==========================================
# --- TAB 10: AGENDA Y CITAS ---
# ==========================================
with tab10:
    st.markdown("<h3 style='margin-bottom: 5px;'>📅 Agenda Animalarium</h3>", unsafe_allow_html=True)
    
    # --- DATOS COMUNES PARA TODAS LAS SUB-PESTAÑAS DE AGENDA ---
    res_m = client.table("mascotas").select("id, nombre, clientes(nombre_dueno)").execute()
    dict_mascotas = {}
    if res_m.data:
        for m in res_m.data:
            dueno = m['clientes']['nombre_dueno'] if m.get('clientes') else "Desconocido"
            dict_mascotas[f"🐾 {m['nombre']} (De: {dueno})"] = m['id']
            
    res_citas = client.table("citas").select("id, fecha_hora, servicio, duracion_minutos, mascotas(nombre, clientes(nombre_dueno, telefono))").order("fecha_hora", desc=False).execute()
    
    # --- PESTAÑAS DE VISTAS ---
    sub_agenda, sub_diario, sub_semanal = st.tabs(["📝 Gestión de Citas", "🕒 Vista Diaria", "🗓️ Vista Semanal"])
    
    with sub_agenda:
        c_agenda1, c_agenda2 = st.columns([1, 2.5], gap="large")
        
        with c_agenda1:
            with st.form("nueva_cita", border=True):
                st.markdown("#### ➕ Nueva Cita")
                mascota_sel = st.selectbox("Selecciona Mascota *", list(dict_mascotas.keys()), index=None)
                fecha_c = st.date_input("Fecha *")
                hora_c = st.time_input("Hora de Inicio *")
                duracion_c = st.number_input("Duración estimada (minutos) *", min_value=5, max_value=300, value=60, step=5)
                servicio_sel = st.selectbox("Servicio *", ["Peluquería (Baño y Corte)", "Peluquería (Solo Baño)", "Corte de Uñas", "Revisión Veterinaria", "Otro"])
                
                if st.form_submit_button("Guardar Cita", type="primary", use_container_width=True):
                    if mascota_sel:
                        fecha_hora_str = f"{fecha_c} {hora_c.strftime('%H:%M')}"
                        client.table("citas").insert({
                            "mascotas_id": dict_mascotas[mascota_sel],
                            "fecha_hora": fecha_hora_str,
                            "servicio": servicio_sel,
                            "duracion_minutos": int(duracion_c)
                        }).execute()
                        st.success("Cita agendada.")
                        time.sleep(1); st.rerun()
                    else:
                        st.error("Debes seleccionar una mascota.")

        with c_agenda2:
            st.markdown("#### 🗓️ Directorio de Citas (Editable)")
            if res_citas.data:
                citas_formateadas = []
                for c in res_citas.data:
                    mascota_info = c.get('mascotas', {})
                    cliente_info = mascota_info.get('clientes', {}) if mascota_info else {}
                    dur = c.get('duracion_minutos') if c.get('duracion_minutos') is not None else 60
                    
                    citas_formateadas.append({
                        "id": c['id'],
                        "Día y Hora": c['fecha_hora'],
                        "Duración (min)": dur,
                        "Servicio": c['servicio'],
                        "Mascota": mascota_info.get('nombre', 'N/A'),
                        "Dueño": cliente_info.get('nombre_dueno', 'N/A'),
                        "Teléfono": cliente_info.get('telefono', 'N/A')
                    })
                    
                df_citas = pd.DataFrame(citas_formateadas)
                
                ed_citas = st.data_editor(
                    df_citas[['id', 'Día y Hora', 'Duración (min)', 'Servicio', 'Mascota', 'Dueño', 'Teléfono']],
                    use_container_width=True, hide_index=True, num_rows="dynamic", key="ed_citas_ag", height=400,
                    column_config={
                        "id": None,
                        "Mascota": st.column_config.TextColumn(disabled=True),
                        "Dueño": st.column_config.TextColumn(disabled=True),
                        "Teléfono": st.column_config.TextColumn(disabled=True)
                    }
                )
                
                if st.button("💾 Guardar Cambios en Agenda", type="primary"):
                    ids_actuales = ed_citas['id'].dropna().tolist()
                    ids_orig = df_citas['id'].tolist()
                    ids_borrar = [i for i in ids_orig if i not in ids_actuales]
                    
                    for id_b in ids_borrar: client.table("citas").delete().eq("id", id_b).execute()
                    
                    for _, row in ed_citas.iterrows():
                        if pd.notna(row['id']):
                            client.table("citas").update({
                                "fecha_hora": str(row['Día y Hora']),
                                "duracion_minutos": int(row['Duración (min)']),
                                "servicio": str(row['Servicio'])
                            }).eq("id", row['id']).execute()
                    st.success("Agenda actualizada."); time.sleep(0.8); st.rerun()
            else:
                st.info("No hay citas agendadas en el sistema.")
                
    with sub_diario:
        st.markdown("#### 🕒 Cuadrante de Trabajo Diario (Intervalos de 5 min)")
        dia_ver = st.date_input("Selecciona un día para ver los huecos libres:", value=date.today())
        
        # Creamos una cuadrícula estricta de 5 en 5 minutos (09:00 a 20:55)
        horas_trabajo = [f"{h:02d}:{m:02d}" for h in range(9, 21) for m in range(0, 60, 5)]
        df_cuadrante = pd.DataFrame({"Hora": horas_trabajo})
        df_cuadrante["Estado"] = "🟩 Libre"
        df_cuadrante["Detalle"] = ""
        
        if res_citas.data:
            for c in res_citas.data:
                try:
                    dt_start = pd.to_datetime(c['fecha_hora'])
                    if dt_start.date() == dia_ver:
                        dur = c.get('duracion_minutos') if c.get('duracion_minutos') is not None else 60
                        dt_end = dt_start + pd.Timedelta(minutes=dur)
                        mascota = c.get('mascotas', {}).get('nombre', 'Mascota')
                        detalle_texto = f"{mascota} ({dur} min) - {c['servicio']}"
                        
                        # Recorremos la cuadrícula y rellenamos los huecos afectados
                        for idx, row in df_cuadrante.iterrows():
                            q_time = pd.to_datetime(f"{dia_ver} {row['Hora']}")
                            if dt_start <= q_time < dt_end:
                                df_cuadrante.loc[idx, "Estado"] = "🔴 OCUPADO"
                                df_cuadrante.loc[idx, "Detalle"] = detalle_texto
                except: pass
                
        df_cuadrante = df_cuadrante.sort_values("Hora").reset_index(drop=True)
        st.dataframe(df_cuadrante, use_container_width=True, hide_index=True, height=600)

    with sub_semanal:
        st.markdown("#### 🗓️ Cuadrante de Trabajo Semanal (Vista Flexible)")
        dia_referencia = st.date_input("Selecciona una fecha para ver su semana:", value=date.today(), key="semana_picker")
        
        start_of_week = dia_referencia - timedelta(days=dia_referencia.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        st.markdown(f"##### Semana del {start_of_week.strftime('%d/%m/%Y')} al {end_of_week.strftime('%d/%m/%Y')}")

        dias_semana_dt = [(start_of_week + timedelta(days=i)) for i in range(7)]
        nombres_dias_col = [d.strftime('%A\n%d/%m') for d in dias_semana_dt]

        # Diccionario para agrupar citas por columna (día)
        citas_por_dia = {dia: [] for dia in nombres_dias_col}

        if res_citas.data:
            for cita in res_citas.data:
                try:
                    dt_start = pd.to_datetime(cita['fecha_hora'])
                    if start_of_week <= dt_start.date() <= end_of_week:
                        duracion = cita.get('duracion_minutos') if cita.get('duracion_minutos') is not None else 60
                        dt_end = dt_start + timedelta(minutes=duracion)
                        
                        col_dia = dt_start.strftime('%A\n%d/%m')
                        mascota_nombre = cita.get('mascotas', {}).get('nombre', 'Cita')
                        
                        # Formato visual tipo tarjeta: "09:00 a 10:15 | Bobby"
                        texto_cita = f"🕒 {dt_start.strftime('%H:%M')} a {dt_end.strftime('%H:%M')} | {mascota_nombre} ({cita['servicio']})"
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

# ==========================================
# --- TAB 11: BANCOS Y TESORERÍA ---
# ==========================================
with tab11:
    st.markdown("<h3 style='margin-top: -15px;'>🏦 Cuentas Bancarias y Tesorería</h3>", unsafe_allow_html=True)
    st.info("💡 En este módulo puedes registrar las cuentas bancarias de la empresa, añadir su IBAN y controlar su saldo en tiempo real.")
    
    col_b1, col_b2 = st.columns([1, 2], gap="large")
    
    with col_b1:
        st.markdown("#### ➕ Añadir Cuenta Bancaria")
        with st.form("nueva_cuenta_banco", clear_on_submit=True, border=True):
            b_nom = st.text_input("Nombre del Banco *", placeholder="Ej: CaixaBank, Caja Siete...")
            b_titular = st.text_input("Titular de la cuenta")
            b_iban = st.text_input("IBAN")
            b_saldo = st.number_input("Saldo Actual Real (€)", value=0.0, format="%.2f")
            
            if st.form_submit_button("💾 Guardar Cuenta", use_container_width=True, type="primary"):
                if b_nom:
                    try:
                        client.table("cuentas_bancarias").insert({
                            "nombre_banco": b_nom, "titular": b_titular,
                            "iban": b_iban, "saldo_actual": float(b_saldo)
                        }).execute()
                        st.success("Cuenta registrada correctamente."); time.sleep(0.5); st.rerun()
                    except Exception:
                        st.error("⚠️ Asegúrate de haber ejecutado el código SQL para crear la tabla 'cuentas_bancarias' en Supabase.")
                else:
                    st.warning("El nombre del banco es obligatorio.")
                    
    with col_b2:
        st.markdown("#### 💳 Tus Cuentas Registradas")
        try:
            res_bancos = client.table("cuentas_bancarias").select("*").order("id").execute()
            if res_bancos.data:
                df_bancos = pd.DataFrame(res_bancos.data)
                
                saldo_total = df_bancos['saldo_actual'].sum()
                st.markdown(f"<div style='background-color: #e8f4f8; padding: 15px; border-radius: 10px; border-left: 5px solid #005275; margin-bottom: 15px;'><h3 style='margin:0; color: #005275;'>Saldo Total Consolidado: {saldo_total:.2f}€</h3></div>", unsafe_allow_html=True)
                
                st.markdown("💡 *Puedes editar directamente el titular, el IBAN o ajustar el Saldo Actual si lo necesitas.*")
                ed_bancos = st.data_editor(
                    df_bancos[['id', 'nombre_banco', 'titular', 'iban', 'saldo_actual']],
                    hide_index=True, use_container_width=True,
                    column_config={"id": None, "nombre_banco": "Banco", "titular": "Titular", "iban": "IBAN", "saldo_actual": st.column_config.NumberColumn("Saldo Actual (€)", format="%.2f")}
                )
                
                if st.button("💾 Guardar Cambios en las Cuentas", type="primary"):
                    for _, row in ed_bancos.iterrows():
                        client.table("cuentas_bancarias").update({"nombre_banco": str(row['nombre_banco']), "titular": str(row['titular']), "iban": str(row['iban']), "saldo_actual": float(row['saldo_actual'])}).eq("id", row['id']).execute()
                    st.success("Datos bancarios actualizados."); time.sleep(0.5); st.rerun()
            else:
                st.info("Aún no has registrado ninguna cuenta bancaria.")
        except:
            st.info("🔧 Las cuentas se mostrarán aquí una vez hayas creado la tabla en la base de datos.")

    st.markdown("---")
    st.markdown("#### 🔄 Transferencias Internas")
    st.info("Mueve dinero entre tus cuentas bancarias o ingresa efectivo sobrante de la caja.")
    
    try:
        res_b = client.table("cuentas_bancarias").select("*").execute()
        lista_bancos = res_b.data if res_b.data else []
        opciones_origen = ["Caja Fuerte (Efectivo)"] + [f"🏦 {b['nombre_banco']} ({b['saldo_actual']:.2f} €)" for b in lista_bancos]
        opciones_destino = [f"🏦 {b['nombre_banco']} ({b['saldo_actual']:.2f} €)" for b in lista_bancos]
        
        with st.form("form_transferencia", border=True):
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1: ori_sel = st.selectbox("Origen del Dinero 📤", opciones_origen)
            with col_t2: des_sel = st.selectbox("Destino del Dinero 📥", opciones_destino)
            with col_t3: cant_trans = st.number_input("Cantidad a transferir (€) *", min_value=0.01, step=10.0, value=None)
            
            if st.form_submit_button("🚀 Realizar Transferencia", type="primary", use_container_width=True):
                if cant_trans and ori_sel != des_sel:
                    # 1. Procesar Origen
                    if "Caja Fuerte" in ori_sel:
                        # Comprobar si hay caja abierta
                        res_caja = client.table("control_caja").select("*").eq("estado", "Abierta").execute()
                        if res_caja.data:
                            id_caja_abierta = res_caja.data[0]['id']
                            client.table("movimientos_caja").insert({
                                "id_caja": id_caja_abierta, "tipo": "Retirada", "cantidad": float(cant_trans), 
                                "motivo": f"Ingreso a banco: {des_sel.split(' (')[0]}"
                            }).execute()
                        else:
                            st.warning("⚠️ La caja fuerte está cerrada. El dinero se sumará al banco, pero no se restará del arqueo actual porque no hay turno abierto.")
                    else:
                        # Es un banco, restar saldo
                        nombre_banco_ori = ori_sel.split(" (")[0].replace("🏦 ", "")
                        banco_ori = next((b for b in lista_bancos if b['nombre_banco'] == nombre_banco_ori), None)
                        if banco_ori:
                            nuevo_saldo_ori = banco_ori['saldo_actual'] - cant_trans
                            client.table("cuentas_bancarias").update({"saldo_actual": nuevo_saldo_ori}).eq("id", banco_ori['id']).execute()
                    
                    # 2. Procesar Destino
                    nombre_banco_des = des_sel.split(" (")[0].replace("🏦 ", "")
                    banco_des = next((b for b in lista_bancos if b['nombre_banco'] == nombre_banco_des), None)
                    if banco_des:
                        nuevo_saldo_des = banco_des['saldo_actual'] + cant_trans
                        client.table("cuentas_bancarias").update({"saldo_actual": nuevo_saldo_des}).eq("id", banco_des['id']).execute()
                        
                    st.success(f"Transferencia de {cant_trans:.2f} € completada con éxito."); time.sleep(1.5); st.rerun()
                elif ori_sel == des_sel:
                    st.error("El origen y el destino no pueden ser el mismo.")
                else:
                    st.warning("Introduce una cantidad válida.")
    except Exception as e:
        st.error(f"Error al cargar módulo de transferencias: {e}")