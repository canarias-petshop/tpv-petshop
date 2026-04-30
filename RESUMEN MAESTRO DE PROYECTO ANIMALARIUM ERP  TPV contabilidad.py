import streamlit as st
import pandas as pd
from postgrest import SyncPostgrestClient
from datetime import datetime, date, timedelta
import time
import json
import urllib.parse
import streamlit.components.v1 as components
import re
import hashlib
import io

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="Animalarium TPV", layout="wide")

st.markdown("""
    <style>
        /* 1. Ajuste del contenedor para aprovechar el ancho sin aplastar */
        .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; max-width: 98% !important; }
        
        /* 2. Textos y etiquetas más legibles en tablet */
        p, .stMarkdown, div[data-testid="stMarkdownContainer"] { font-size: 1.1rem !important; }
        label { font-size: 1.15rem !important; font-weight: 500 !important; }
        
        /* 3. Cuadros de texto y números más grandes para escribir fácil */
        input, select { font-size: 1.15rem !important; }
        .stSelectbox, .stTextInput, .stNumberInput { margin-bottom: 5px !important; }
        
        /* 4. Botones grandes, gruesos y fáciles de pulsar con el dedo */
        .stButton > button {
            min-height: 60px !important;
            font-size: 1.2rem !important;
            font-weight: bold !important;
        }

        /* 5. Pestañas principales más grandes */
        button[data-baseweb="tab"] {
            font-size: 1.15rem !important;
            padding-top: 15px !important;
            padding-bottom: 15px !important;
        }
        
        /* 6. Espaciado entre columnas (quitamos el estrechamiento) */
        [data-testid="column"] { padding: 0 12px !important; }
        
        /* Ocultar Streamlit */
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
try:
    # Limpieza extrema por si se han colado espacios, comillas o rutas duplicadas en la nube
    raw_url = st.secrets['url'].strip().strip('"').strip("'").rstrip('/')
    if raw_url.endswith('/rest/v1'):
        api_url = raw_url
    else:
        api_url = f"{raw_url}/rest/v1"
        
    api_key = st.secrets['key'].strip().strip('"').strip("'")

    client = SyncPostgrestClient(
        api_url, 
        headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"}
    )
    # Test de conexión rápido para atrapar fallos de credenciales o tablas faltantes
    client.table("proveedores").select("id").limit(1).execute()
except Exception as e:
    st.error("🚨 **Error de Conexión a la Base de Datos**")
    if "relation" in str(e) and "does not exist" in str(e):
        st.error("🛠️ **Diagnóstico:** Tu app se conectó a Supabase, pero la tabla no existe. Parece que la base de datos está vacía.")
        st.info("💡 **Solución:** Entra en tu panel de Supabase, ve a 'SQL Editor' y ejecuta el código para crear las tablas del proyecto.")
    else:
        st.error(f"Detalle técnico: {e}")
    st.stop()

# --- 4.5. MÓDULO DE SEGURIDAD VERI*FACTU ---
def generar_hash_verifactu(tipo_doc, fecha, importe_total, hash_anterior):
    """Genera el hash SHA-256 encadenado según directrices de la normativa."""
    hash_ant = hash_anterior if hash_anterior else ""
    cadena = f"{tipo_doc}|{fecha}|{importe_total:.2f}|{hash_ant}"
    huella = hashlib.sha256(cadena.encode('utf-8')).hexdigest()
    return huella.upper()

# --- CABECERA COMPACTA ---
c_logo, c_titulo = st.columns([0.08, 0.92], vertical_alignment="center")
with c_logo:
    try: st.image("LOGO.jpg", width=60)
    except: st.markdown("<h2 style='margin:0; padding:0;'>🐾</h2>", unsafe_allow_html=True)
with c_titulo:
    st.markdown("<h1 style='margin: 0; padding: 0; font-size: 1.8rem; line-height: 1;'>Animalarium - TPV</h1>", unsafe_allow_html=True)

# DEFINICIÓN CORRECTA DE LAS 10 PESTAÑAS
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "📦 Inventario", "🛒 Caja", "👥 Clientes", "📜 Historial", 
    "💰 Control Caja", "📈 Estadísticas", "🚚 Proveedores", "📑 Facturación",
    "📊 Contabilidad", "📅 Agenda"
])

# ==========================================
# --- TAB 1: INVENTARIO Y SERVICIOS ---
# ==========================================
with tab1:
    st.markdown("<h3 style='margin-top: -15px;'>📦 Gestión de Inventario y Servicios</h3>", unsafe_allow_html=True)
    
    col_f, col_t = st.columns([1.2, 2.5], gap="large")
    
    res_proveedores = client.table("proveedores").select("id, nombre_empresa").execute()
    dict_proveedores = {p['nombre_empresa']: p['id'] for p in res_proveedores.data} if res_proveedores.data else {}

    with col_f:
        st.markdown("#### 📝 Alta de nuevo ítem")
        cat_item = st.radio("Selecciona qué vas a registrar:", ["Producto", "Servicio"], horizontal=True)
        
        with st.form("nuevo_p_separado", clear_on_submit=True, border=True):
            nombre = st.text_input(f"Nombre del {cat_item} *")
            c1, c2 = st.columns(2)
            with c1: sku = st.text_input("SKU (Interno) *")
            with c2: 
                if cat_item == "Producto":
                    cod_barras = st.text_input("Cód. Barras")
                else:
                    cod_barras = ""
            
            if cat_item == "Producto":
                c4, c5 = st.columns(2, vertical_alignment="bottom")
                with c4: p_base = st.number_input("Coste Compra (€)", min_value=0.0, format="%.2f", value=None)
                with c5: igic_tipo = st.selectbox("IGIC Compra %", [7.00, 0.00, 3.00, 15.00])
                
                c6, c7, c8, c9 = st.columns(4, vertical_alignment="bottom")
                with c6: pvp = st.number_input("PVP Público (€) *", min_value=0.0, format="%.2f", value=None)
                with c7: stck = st.number_input("Stock Inicial", min_value=0, value=None)
                with c8: s_min = st.number_input("Avisar si quedan:", min_value=0, value=2)
                with c9: c_rep = st.number_input("Cant. a pedir:", min_value=1, value=5)
                provs_sel = st.multiselect("Asociar Proveedores", list(dict_proveedores.keys()))
            else:
                c4, c5 = st.columns(2, vertical_alignment="bottom")
                with c4: pvp = st.number_input("Precio Cerrado (€) *", min_value=0.0, format="%.2f", value=None)
                with c5: igic_tipo = st.selectbox("IGIC (%)", [7.00, 0.00, 3.00, 15.00])
                p_base = 0.0
                stck = 0
                provs_sel = []
                st.info("💡 El sistema desglosará automáticamente la Base Imponible y la cuota de IGIC en la tabla.")
            
            if st.form_submit_button("💾 REGISTRAR", use_container_width=True, type="primary"):
                pvp_val = pvp if pvp is not None else 0.0
                p_base_val = p_base if p_base is not None else 0.0
                stck_val = stck if stck is not None else 0
                
                if nombre and sku:
                    if cat_item == "Servicio":
                        p_base_calc = pvp_val / (1 + (igic_tipo / 100))
                    else:
                        p_base_calc = p_base_val

                    res_ins = client.table("productos").insert({
                        "sku": sku, "codigo_barras": cod_barras, "nombre": nombre, "categoria": cat_item,
                        "precio_base": p_base_calc, "igic_tipo": igic_tipo, "stock_actual": stck_val, 
                        "precio_pvp": pvp_val, "stock_minimo": s_min if cat_item == "Producto" else 0,
                        "cantidad_reponer": c_rep if cat_item == "Producto" else 0
                    }).execute()
                    if cat_item == "Producto" and res_ins.data and provs_sel:
                        rels = [{"producto_id": res_ins.data[0]['id'], "proveedor_id": dict_proveedores[p], "precio_coste": p_base_calc} for p in provs_sel]
                        client.table("productos_proveedores").insert(rels).execute()
                    st.success("Guardado correctamente"); time.sleep(0.5); st.rerun()

    with col_t:
            res_prod = client.table("productos").select("*, productos_proveedores(proveedores(nombre_empresa))").order("nombre").execute()
            
            if res_prod.data:
                df_inv = pd.DataFrame(res_prod.data)
                
                def extraer_proveedores(rels):
                    if isinstance(rels, list) and len(rels) > 0:
                        nombres = [r.get('proveedores', {}).get('nombre_empresa', '') for r in rels if isinstance(r, dict) and r.get('proveedores')]
                        return nombres[0] if nombres else "---"
                    return "---"
                    
                if 'productos_proveedores' in df_inv.columns:
                    df_inv['Proveedor'] = df_inv['productos_proveedores'].apply(extraer_proveedores)
                else:
                    df_inv['Proveedor'] = "---"
                
                # --- 1. LIMPIEZA DE DATOS ---
                df_inv['categoria_filt'] = df_inv['categoria'].fillna('Producto').astype(str).str.strip().str.capitalize()

                df_solo_productos = df_inv[df_inv['categoria_filt'] == 'Producto'].copy()

                # Asegurar columnas por si hay productos antiguos
                if 'stock_minimo' not in df_solo_productos.columns: df_solo_productos['stock_minimo'] = 2
                if 'cantidad_reponer' not in df_solo_productos.columns: df_solo_productos['cantidad_reponer'] = 5

                # --- ALERTA DE STOCK BAJO ---
                df_bajo_stock = df_solo_productos[df_solo_productos['stock_actual'] <= df_solo_productos['stock_minimo']].sort_values(by="stock_actual")
                if not df_bajo_stock.empty:
                    st.warning(f"⚠️ **ATENCIÓN: Tienes {len(df_bajo_stock)} producto(s) por debajo de su stock mínimo.**")
                    
                    if st.button("🚀 AUTO-DISTRIBUIR A BORRADORES (Generación Inteligente)", type="primary", use_container_width=True):
                        # 1. Encontrar qué proveedor vende cada cosa
                        res_rels = client.table("productos_proveedores").select("producto_id, proveedor_id").execute()
                        mapa_provs = {r['producto_id']: r['proveedor_id'] for r in res_rels.data} if res_rels.data else {}
                        
                        pedidos_creados = 0
                        pedidos_a_crear = {}
                        # 2. Agrupar por proveedor
                        for _, row in df_bajo_stock.iterrows():
                            prov_id = mapa_provs.get(row['id'])
                            if prov_id:
                                if prov_id not in pedidos_a_crear: pedidos_a_crear[prov_id] = []
                                pedidos_a_crear[prov_id].append({"Producto": row['nombre'], "Cantidad": int(row['cantidad_reponer'])})
                                
                        # 3. Mandar a borradores
                        if pedidos_a_crear:
                            for p_id, prods in pedidos_a_crear.items():
                                res_b = client.table("pedidos_proveedores").select("id, productos").eq("proveedor_id", p_id).eq("estado", "Borrador").execute()
                                if res_b.data: # Si ya hay borrador, actualizamos
                                    draft_id = res_b.data[0]['id']
                                    prods_act = res_b.data[0].get('productos', [])
                                    nombres_act = [p.get('Producto') for p in prods_act]
                                    for np in prods:
                                        if np['Producto'] not in nombres_act: prods_act.append(np)
                                    client.table("pedidos_proveedores").update({"productos": prods_act}).eq("id", draft_id).execute()
                                else: # Si no hay, creamos uno nuevo
                                    client.table("pedidos_proveedores").insert({"proveedor_id": p_id, "estado": "Borrador", "productos": prods}).execute()
                            st.success("✅ ¡Borradores generados automáticamente! Ve a la Pestaña 7 (Proveedores) para revisarlos y enviarlos.")
                        else:
                            st.error("❌ No se pudo automatizar: Ninguno de los productos bajo mínimos tiene un proveedor asociado.")

                    with st.expander("👀 Ver lista manual de reposición"):
                        st.dataframe(df_bajo_stock[['sku', 'nombre', 'stock_actual', 'stock_minimo', 'cantidad_reponer']], hide_index=True, use_container_width=True)
                        
                        # --- INTEGRACIÓN CON PEDIDOS A PROVEEDORES ---
                        res_borradores = client.table("pedidos_proveedores").select("id, proveedores(nombre_empresa)").eq("estado", "Borrador").execute()
                        if res_borradores.data:
                            opciones_borrador = {f"Borrador #{b['id']} - {b['proveedores']['nombre_empresa']}": b['id'] for b in res_borradores.data if b.get('proveedores')}
                            c_ped1, c_ped2 = st.columns([2, 1])
                            with c_ped1: prods_a_pedir = st.multiselect("Selecciona productos para añadir a un pedido:", df_bajo_stock['nombre'].tolist())
                            with c_ped2:
                                borrador_sel = st.selectbox("Selecciona el Borrador:", list(opciones_borrador.keys()))
                                if st.button("➕ Añadir al Borrador", use_container_width=True) and prods_a_pedir and borrador_sel:
                                    draft_id = opciones_borrador[borrador_sel]
                                    prods_actuales = client.table("pedidos_proveedores").select("productos").eq("id", draft_id).execute().data[0].get('productos', [])
                                    for p_nom in prods_a_pedir:
                                        if not any(item.get('Producto') == p_nom for item in prods_actuales):
                                            prods_actuales.append({"Producto": p_nom, "Cantidad": 1})
                                    client.table("pedidos_proveedores").update({"productos": prods_actuales}).eq("id", draft_id).execute()
                                    st.success("¡Añadidos al borrador! Ve a la Pestaña 7 para gestionarlo.")
                        else:
                            st.info("💡 Ve a la Pestaña 7 (Proveedores) para crear un Borrador de Pedido y añadir estos productos.")

                # --- TABLA DE PRODUCTOS MEJORADA ---
                st.markdown("#### 📦 Inventario de Productos")

                # Ahora permitimos borrar filas con num_rows="dynamic"
                edit_p = st.data_editor(
                    df_solo_productos,
                    column_config={
                        "id": None, "categoria": None, "categoria_filt": None, "productos_proveedores": None,
                        "sku": "SKU", "codigo_barras": "Barras", "nombre": "Descripción",
                        "Proveedor": st.column_config.SelectboxColumn("Proveedor", options=["---"] + list(dict_proveedores.keys())),
                        "precio_base": st.column_config.NumberColumn("Coste (€)", format="%.2f"),
                        "igic_tipo": "IGIC %", "precio_pvp": "PVP (€)", "stock_actual": "Stock",
                        "stock_minimo": st.column_config.NumberColumn("Avisar en", step=1),
                        "cantidad_reponer": st.column_config.NumberColumn("Reponer Ud", step=1)
                    },
                    column_order=["sku", "codigo_barras", "nombre", "Proveedor", "precio_base", "igic_tipo", "precio_pvp", "stock_actual", "stock_minimo", "cantidad_reponer"],
                    hide_index=True, 
                    use_container_width=True, 
                    num_rows="dynamic", # <--- ESTO PERMITE BORRAR FILAS
                    key="edit_p_sep"
                )

                if st.button("💾 Guardar cambios en Productos", key="btn_save_p_sep"):
                    # 1. Detectar si alguna fila ha sido borrada
                    ids_actuales = edit_p['id'].dropna().tolist()
                    ids_originales = df_solo_productos['id'].tolist()
                    ids_a_borrar = [id_orig for id_orig in ids_originales if id_orig not in ids_actuales]

                    # 2. Borrar de Supabase los que ya no están en la tabla
                    for id_del in ids_a_borrar:
                        client.table("productos").delete().eq("id", id_del).execute()

                    # 3. Actualizar los que se han quedado (por si cambiaste precios o stock)
                    for i, row in edit_p.iterrows():
                        if pd.notna(row['id']): # Solo actualizamos si el producto ya existía
                            datos = row.to_dict()
                            
                            # --- Gestión del proveedor ---
                            prov_nombre = datos.get('Proveedor', '---')
                            
                            for col_eliminar in ['categoria_filt', 'Proveedor', 'productos_proveedores']:
                                if col_eliminar in datos: del datos[col_eliminar]
                            client.table("productos").update(datos).eq("id", row['id']).execute()
                            
                            # Actualizar la relación principal del proveedor
                            client.table("productos_proveedores").delete().eq("producto_id", row['id']).execute()
                            if prov_nombre != "---" and prov_nombre in dict_proveedores:
                                client.table("productos_proveedores").insert({
                                    "producto_id": row['id'], "proveedor_id": dict_proveedores[prov_nombre], "precio_coste": float(datos.get('precio_base', 0.0))
                                }).execute()

                    st.success("Inventario sincronizado correctamente")
                    st.rerun() # Recargamos para ver los cambios [cite: 9]

                st.markdown("---")

                # --- TABLA DE SERVICIOS MEJORADA ---
                st.markdown("#### ✂️ Catálogo de Servicios")
                df_solo_servicios = df_inv[df_inv['categoria_filt'] == 'Servicio'].copy()
                
                # Añadimos la columna calculada de Cuota de IGIC para mostrar el desglose
                df_solo_servicios['Cuota IGIC (€)'] = df_solo_servicios['precio_pvp'] - df_solo_servicios['precio_base']

                # Habilitamos num_rows="dynamic" para que puedas borrar servicios
                edit_s = st.data_editor(
                    df_solo_servicios,
                    column_config={
                        "id": None, "categoria": None, "categoria_filt": None,
                        "sku": "Código", "nombre": "Descripción del Servicio",
                        "precio_base": st.column_config.NumberColumn("Base Real sin IGIC (€)", format="%.2f", disabled=True),
                        "igic_tipo": st.column_config.SelectboxColumn("IGIC %", options=[7.0, 0.0, 3.0, 15.0]),
                        "Cuota IGIC (€)": st.column_config.NumberColumn("Cuota IGIC (€)", format="%.2f", disabled=True),
                        "precio_pvp": st.column_config.NumberColumn("Precio Cerrado (PVP) (€)", format="%.2f")
                    },
                    column_order=["sku", "nombre", "precio_base", "igic_tipo", "Cuota IGIC (€)", "precio_pvp"],
                    hide_index=True, 
                    use_container_width=True, 
                    num_rows="dynamic", # <--- PERMITE BORRAR FILAS DE SERVICIOS
                    key="edit_s_sep"
                )

                if st.button("💾 Guardar cambios en Servicios", key="btn_save_s_sep"):
                    # 1. Identificar si algún servicio fue eliminado de la tabla
                    ids_s_actuales = edit_s['id'].dropna().tolist()
                    ids_s_originales = df_solo_servicios['id'].tolist()
                    ids_s_a_borrar = [id_orig for id_orig in ids_s_originales if id_orig not in ids_s_actuales]

                    # 2. Borrar de la base de datos los servicios eliminados
                    for id_del in ids_s_a_borrar:
                        client.table("productos").delete().eq("id", id_del).execute()

                    # 3. Actualizar o guardar los cambios en los servicios que quedan
                    for i, row in edit_s.iterrows():
                        if pd.notna(row['id']):
                            # Recalculamos la base real de forma automática si cambiaste el PVP o el IGIC en la tabla
                            nuevo_pvp = float(row['precio_pvp'])
                            nuevo_igic = float(row['igic_tipo'])
                            nueva_base = nuevo_pvp / (1 + (nuevo_igic / 100))
                            
                            client.table("productos").update({
                                "sku": str(row['sku']), "nombre": str(row['nombre']),
                                "precio_pvp": nuevo_pvp, "igic_tipo": nuevo_igic, "precio_base": nueva_base
                            }).eq("id", row['id']).execute()

                    st.success("Catálogo de servicios actualizado")
                    st.rerun()
            else:
                st.info("Inventario vacío.")

# ==========================================
# --- TAB 2: CAJA Y TERMINAL DE VENTA ---
# ==========================================
with tab2:
    st.markdown("""
        <div style='display: flex; justify-content: space-between; margin-top: 10px; margin-bottom: 10px; padding: 0 5px;'>
            <h4 style='margin:0; color: #333; white-space: nowrap;'>🛒 Terminal de Venta</h4>
            <h4 style='margin:0; color: #333; white-space: nowrap; padding-right: 10px;'>🛒 Tu Carrito</h4>
        </div>
    """, unsafe_allow_html=True)

    col_busqueda, col_carrito = st.columns([1, 1.4], gap="small")
    
    with col_busqueda:
        res_inv = client.table("productos").select("*").execute()
        df_inv = pd.DataFrame(res_inv.data) if res_inv.data else pd.DataFrame()
        
        st.markdown("<p style='margin: 0; font-weight: bold; font-size: 13px;'>🔍 Buscar producto o servicio</p>", unsafe_allow_html=True)
        if not df_inv.empty:
            opciones = df_inv.apply(lambda x: f"{x['nombre']} | {x['precio_pvp']}€", axis=1).tolist()
            prod_sel = st.selectbox("s1", opciones, index=None, placeholder="Escribe para buscar...", label_visibility="collapsed", key="sb_n")
            if prod_sel:
                nombre_sel = prod_sel.split(" | ")[0]
                fila_p = df_inv[df_inv['nombre'] == nombre_sel].iloc[0]
                st.markdown(f"<p style='margin:0; font-size:11px; color:green;'>Stock: {fila_p['stock_actual']}</p>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1: cant = st.number_input("c1", min_value=1, value=1, label_visibility="collapsed", key="cant_b")
                with c2: 
                    if st.button("➕ Añadir", use_container_width=True, type="primary", key="btn_b"):
                        st.session_state.carrito.append({
                            "id": str(fila_p['id']), "Producto": fila_p['nombre'], "Cantidad": cant, "Precio": fila_p['precio_pvp'],
                            "Subtotal": cant * float(fila_p['precio_pvp']), "IGIC": fila_p.get('igic_tipo', 7), "Manual": False
                        })
                        st.rerun()
        
        st.markdown("<hr style='margin: 5px 0px; border: none; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

        st.markdown("<p style='margin: 0; font-weight: bold; font-size: 13px;'>📇 Escáner de Pistola</p>", unsafe_allow_html=True)
        if 'limpiar_codigo' in st.session_state and st.session_state.limpiar_codigo:
            st.session_state.input_pistola = ""
            st.session_state.limpiar_codigo = False

        cp1, cp2 = st.columns([2, 1])
        with cp1: cod_leido = st.text_input("p1", placeholder="Esperando escaneo...", label_visibility="collapsed", key="input_pistola")
        with cp2: cant_p = st.number_input("p2", min_value=1, value=1, label_visibility="collapsed", key="cant_p")
        
        if cod_leido and not df_inv.empty:
            coincid = df_inv[df_inv['sku'] == cod_leido]
            if not coincid.empty:
                fila_pist = coincid.iloc[0]
                st.session_state.carrito.append({
                    "id": str(fila_pist['id']), "Producto": fila_pist['nombre'], "Cantidad": cant_p, "Precio": fila_pist['precio_pvp'],
                    "Subtotal": cant_p * float(fila_pist['precio_pvp']), "IGIC": fila_pist.get('igic_tipo', 7), "Manual": False
                })
                st.session_state.limpiar_codigo = True; st.rerun()

        st.markdown("<hr style='margin: 5px 0px; border: none; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

        st.markdown("<p style='margin: 0; font-weight: bold; font-size: 13px;'>✍️ Artículo manual</p>", unsafe_allow_html=True)
        with st.form("f_man", clear_on_submit=True, border=False):
            cm1, cm2, cm3 = st.columns([1.3, 1, 1]) 
            with cm1: m_nom = st.text_input("Artículo", placeholder="Nombre...", label_visibility="visible")
            with cm2: m_pre = st.number_input("Precio €", min_value=0.0, step=0.1, format="%.2f", value=None, label_visibility="visible")
            with cm3: m_can = st.number_input("Cant.", min_value=1, value=1, label_visibility="visible")
            if st.form_submit_button("➕ Añadir Manual al Carrito", use_container_width=True):
                if m_nom and m_pre is not None and m_pre >= 0:
                    st.session_state.carrito.append({
                        "Producto": m_nom, "Cantidad": m_can, "Precio": m_pre,
                        "Subtotal": m_can * float(m_pre), "IGIC": 0, "Manual": True
                    })
                    st.rerun()

    with col_carrito:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        if st.session_state.get('ticket_actual'):
            t = st.session_state.ticket_actual
            st.success("✅ Venta realizada con éxito")
            
           # --- TICKET PARA STAR MICRONICS PASS-PRNT ---
            html_ticket = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                body {{ margin: 0; padding: 0; font-family: sans-serif; }}
                #ticket-impresion {{ display: none; }} /* Se oculta en la pantalla de la tablet */
                #pantalla {{ text-align: center; }}
                .btn-print {{ 
                    padding: 12px; background-color: #005275; color: white; 
                    border: none; border-radius: 5px; cursor: pointer; 
                    font-weight: bold; width: 100%; font-size: 15px;
                }}
            </style>
            </head>
            <body>
            
            <div id="pantalla">
                <button class="btn-print" onclick="imprimirConStar()">🖨️ IMPRIMIR EN STAR MICRONICS</button>
            </div>

            <div id="ticket-impresion">
                <div style="text-align: center; font-family: monospace; width: 100%; font-size: 22px; color: black; font-weight: bold;">
                    <b style="font-size: 34px;">ANIMALARIUM</b><br>
                    Raquel Trujillo Hernández<br>
                    DNI: 78854854K<br>
                    C/ José Hernández Alfonso, 26<br>
                    38009 S/C de Tenerife
                    <br><br>
                    <div style="text-align: left; font-size: 22px;">Fecha: {t['fecha']}</div>
                    <hr style="border-top: 2px dashed #000; margin: 10px 0px;">
                    <table style="width: 100%; font-size: 22px; text-align: left; font-weight: bold;">
            """
            
            # Bucle para meter los productos (No tocar la identación aquí)
            for p in t['productos']:
                desc_item = p.get('Desc %', 0.0)
                if desc_item > 0:
                    html_ticket += f"<tr><td style='padding-bottom: 0px;'>{p['Cantidad']}x {p['Producto']}</td><td style='text-align: right; padding-bottom: 0px;'>{p['Subtotal']:.2f}€</td></tr>"
                    html_ticket += f"<tr><td colspan='2' style='font-size: 16px; padding-bottom: 5px; color: #555;'>  ↳ Dto. {desc_item}% aplicado</td></tr>"
                else:
                    html_ticket += f"<tr><td style='padding-bottom: 5px;'>{p['Cantidad']}x {p['Producto']}</td><td style='text-align: right; padding-bottom: 5px;'>{p['Subtotal']:.2f}€</td></tr>"

            html_ticket += f"""
                    </table>
                    <hr style="border-top: 2px dashed #000; margin: 10px 0px;">
            """
            
            desc_global = t.get('descuento_global', 0.0)
            if desc_global > 0:
                subtotal_sin_desc = t['total'] / (1 - desc_global / 100) if (1 - desc_global / 100) > 0 else t['total']
                html_ticket += f"<div style='text-align: right; font-size: 22px;'>Subtotal: {subtotal_sin_desc:.2f}€</div>"
                html_ticket += f"<div style='text-align: right; font-size: 22px;'><b>Dto. Global: -{desc_global}%</b></div>"

            html_ticket += f"""
                    <div style="text-align: right; font-size: 28px;"><b>TOTAL: {t['total']:.2f}€</b></div>
"""
            if t.get('cliente_fidel'):
                html_ticket += f"<div style='font-size:18px; text-align:center; margin-top:15px; border: 1px solid #000; padding: 5px;'><b>🌟 CLIENTE VIP: {t['cliente_fidel']}</b><br>Has ganado +{t['puntos_ganados']} puntos hoy!</div>"

            html_ticket += f"""
                    
                    <div style="font-size: 18px; color: #000; margin-top: 30px; text-align: center;">
                        <b>POLÍTICA DE DEVOLUCIÓN</b><br>
                        Plazo de 14 días con ticket y<br>
                        embalaje original en perfecto estado.
                    </div>
                </div>
            </div>

            <script>
            function imprimirConStar() {{
                // 1. Obtenemos el diseño del ticket
                var ticketHTML = document.getElementById('ticket-impresion').innerHTML;
                
                // 1.5. ENVOLVEMOS EL TICKET EN UN HTML COMPLETO PARA EVITAR ERROR 011
                var fullHTML = "<!DOCTYPE html><html><head><meta charset='utf-8'></head><body style='margin:0; padding:0; background-color:white;'>" + ticketHTML + "</body></html>";
                
                // 2. Lo codificamos para que pueda viajar por la URL
                var htmlCodificado = encodeURIComponent(fullHTML);
                
                // 3. Obtenemos la URL REAL de tu TPV usando un "ancla" (#) para evitar la recarga de Streamlit
                var urlRetorno = "https://google.com"; // Retorno de emergencia para evitar error E002
                try {{
                    if (window.top.location.href && window.top.location.href !== "about:blank") {{
                        var baseUrl = window.top.location.href.split('#')[0];
                        urlRetorno = baseUrl + "#impreso";
                    }}
                }} catch(e) {{}}
                
                // 4. Creamos el enlace añadiendo el parámetro 'back' obligatorio
                var starURL = "starpassprnt://v1/print/nopreview?back=" + encodeURIComponent(urlRetorno) + "&html=" + htmlCodificado;
                
                // 5. Lanzamos la App de Star
                window.location.href = starURL;
            }}
            </script>
            
            </body>
            </html>
            """
            components.html(html_ticket, height=50)
            
            c_nv = st.columns(1)[0]
            with c_nv:
                if st.button("🛒 Nueva Venta", use_container_width=True, type="primary"):
                    st.session_state.ticket_actual = None
                    st.rerun()

        else:
            if st.session_state.carrito:
                df_car = pd.DataFrame(st.session_state.carrito)
                if 'Desc. %' not in df_car.columns: df_car['Desc. %'] = 0.0

                edited_df = st.data_editor(
                    df_car,
                    column_order=("Cantidad", "Producto", "Precio", "Desc. %", "Subtotal"),
                    column_config={
                        "Cantidad": st.column_config.NumberColumn("Cant.", min_value=1, step=1, width="small"),
                        "Producto": st.column_config.TextColumn("Producto", disabled=True),
                        "Precio": st.column_config.NumberColumn("Precio €", format="%.2f"),
                        "Desc. %": st.column_config.NumberColumn("Desc. %", min_value=0, max_value=100, format="%d%%"),
                        "Subtotal": st.column_config.NumberColumn("Total", format="%.2f", disabled=True),
                    },
                    hide_index=True, use_container_width=True, num_rows="dynamic", height=250, key="ed_car_ticket"
                )
                
                if not edited_df.equals(df_car):
                    edited_df["Subtotal"] = (edited_df["Cantidad"] * edited_df["Precio"]) * (1 - edited_df["Desc. %"] / 100)
                    st.session_state.carrito = json.loads(edited_df.to_json(orient='records'))
                    st.rerun()

                st.markdown("<hr style='margin: 2px 0px; border: none; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

                sub_antes = edited_df["Subtotal"].sum()
                
                # --- FIDELIZACIÓN ---
                res_cli_puntos = client.table("clientes").select("id, nombre_dueno, puntos").execute()
                opc_cli = ["Ninguno (Venta Anónima)"] + [f"{c['nombre_dueno']} (Puntos: {c.get('puntos') or 0})" for c in res_cli_puntos.data] if res_cli_puntos.data else ["Ninguno (Venta Anónima)"]
                
                c_desc, c_fid = st.columns(2)
                with c_desc: desc_g = st.number_input("🎁 Descuento Global (%)", min_value=0, max_value=100, value=None, step=1)
                with c_fid: cliente_fidelidad = st.selectbox("🌟 Asociar Cliente (Puntos)", opc_cli)
                
                desc_g_val = float(desc_g or 0.0)
                total_f = sub_antes * (1 - desc_g_val / 100)
                
                # --- LÓGICA DE CANJEO DE PUNTOS ---
                desc_puntos_eur = 0.0
                puntos_a_descontar = 0
                if "Ninguno" not in cliente_fidelidad:
                    pts_str = cliente_fidelidad.split("(Puntos: ")[1].replace(")", "")
                    puntos_disp = int(pts_str) if pts_str.isdigit() else 0
                    if puntos_disp > 0:
                        max_descuento_eur = total_f * 0.50
                        max_puntos_permitidos = int(max_descuento_eur / 0.10)
                        puntos_a_usar = min(puntos_disp, max_puntos_permitidos)
                        eur_a_descontar = puntos_a_usar * 0.10
                        if puntos_a_usar > 0:
                            if st.checkbox(f"💳 Canjear {puntos_a_usar} puntos por -{eur_a_descontar:.2f}€ (Límite 50%)", value=False):
                                desc_puntos_eur = eur_a_descontar
                                puntos_a_descontar = puntos_a_usar
                
                total_f = total_f - desc_puntos_eur
                if total_f < 0: total_f = 0.0
                
                st.markdown("<hr style='margin: 2px 0px; border: none; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

                metodo = st.radio("p", ["Efectivo", "Tarjeta", "Bizum", "Mixto"], horizontal=True, label_visibility="collapsed")
                pagado_hoy = 0.0; pendiente = 0.0; metodo_log = metodo
                p_efectivo = 0.0; p_tarjeta = 0.0; p_bizum = 0.0

                if metodo == "Efectivo":
                    c_tot, c_ent, c_cam = st.columns([0.8, 1, 1])
                    with c_tot: st.markdown(f"<p style='margin:0; font-size:11px; color:gray;'>TOTAL</p><h3 style='margin:0; color:#d32f2f;'>{total_f:.2f}€</h3>", unsafe_allow_html=True)
                    with c_ent: entregado = st.number_input("Entregado € (Intro)", min_value=0.0, value=float(total_f), format="%.2f")
                    with c_cam:
                        ent_val = float(entregado)
                        cambio = ent_val - total_f
                        if cambio >= 0:
                            st.markdown(f"<p style='margin:0; font-size:11px; color:gray;'>CAMBIO AL CLIENTE</p><h3 style='margin:0; color:green;'>{cambio:.2f}€</h3>", unsafe_allow_html=True)
                            pagado_hoy = total_f
                            p_efectivo = total_f
                        else:
                            st.markdown(f"<p style='margin:0; font-size:11px; color:gray;'>DEUDA PENDIENTE</p><h3 style='margin:0; color:orange;'>{-cambio:.2f}€</h3>", unsafe_allow_html=True)
                            pagado_hoy = ent_val; pendiente = -cambio
                            p_efectivo = ent_val

                elif metodo == "Mixto":
                    st.markdown(f"<h3 style='text-align: right; margin: 0; color: #d32f2f;'>Total: {total_f:.2f}€</h3>", unsafe_allow_html=True)
                    cm1, cm2, cm3 = st.columns(3)
                    with cm1: p_e = st.number_input("Efe. (Intro)", min_value=0.0, value=None)
                    with cm2: p_t = st.number_input("Tar. (Intro)", min_value=0.0, value=None)
                    with cm3: p_b = st.number_input("Biz. (Intro)", min_value=0.0, value=None)
                    
                    p_e_val = float(p_e or 0.0)
                    p_t_val = float(p_t or 0.0)
                    p_b_val = float(p_b or 0.0)
                    
                    pagado_hoy = p_e_val + p_t_val + p_b_val
                    p_efectivo = p_e_val; p_tarjeta = p_t_val; p_bizum = p_b_val
                    pendiente = total_f - pagado_hoy if pagado_hoy < total_f else 0.0
                    metodo_log = f"Mixto (E:{p_e_val}|T:{p_t_val}|B:{p_b_val})"
                    if pendiente > 0: st.warning(f"Pendiente: {pendiente:.2f}€")
                
                else:
                    st.markdown(f"<h3 style='text-align: right; margin: 0; color: #d32f2f;'>Total: {total_f:.2f}€</h3>", unsafe_allow_html=True)
                    pagado_hoy = total_f
                    if metodo == "Tarjeta": p_tarjeta = total_f
                    if metodo == "Bizum": p_bizum = total_f

                nombre_deudor = ""
                if pendiente > 0:
                    nombre_deudor = st.text_input("👤 Nombre para la deuda:", placeholder="¿Quién debe?")

                st.markdown("<div style='height: 2px;'></div>", unsafe_allow_html=True)
                c_cob, c_vac = st.columns([2, 1])
                with c_cob:
                    bloqueo = (pendiente > 0 and not nombre_deudor)
                    if st.button("🧧 FINALIZAR COBRO", use_container_width=True, type="primary", disabled=bloqueo):
                        carrito_limpio = json.loads(edited_df.to_json(orient='records'))
                        
                        try:
                            # ASIGNACIÓN DE PUNTOS
                            cliente_fidel_nombre = ""
                            puntos_ganados = 0
                            nuevo_saldo = 0
                            if "Ninguno" not in cliente_fidelidad:
                                cliente_fidel_nombre = cliente_fidelidad.split(" (Puntos:")[0]
                                cliente_info = next(c for c in res_cli_puntos.data if c['nombre_dueno'] == cliente_fidel_nombre)
                                puntos_ganados = int(total_f // 10) # 1 punto por cada 10€
                                nuevo_saldo = cliente_info.get('puntos', 0) - puntos_a_descontar + puntos_ganados
                                client.table("clientes").update({"puntos": nuevo_saldo}).eq("id", cliente_info['id']).execute()

                            # INSERCIÓN CON COLUMNAS EXACTAS CONTABLES
                            client.table("ventas_historial").insert({
                                "total": float(total_f), "pagado": float(pagado_hoy), "pendiente": float(pendiente),
                                "metodo_pago": str(metodo_log), "cliente_deuda": str(nombre_deudor),
                                "descuento_global": float(desc_g_val), "productos": carrito_limpio, 
                                "estado": "Completado" if pendiente == 0 else "Deuda",
                                "pago_efectivo": float(p_efectivo),
                                "pago_tarjeta": float(p_tarjeta),
                                "pago_bizum": float(p_bizum)
                            }).execute()
                            
                            for i in carrito_limpio:
                                if not i.get('Manual', False) and 'id' in i:
                                    res = client.table("productos").select("stock_actual").eq("id", i['id']).execute()
                                    if res.data:
                                        n_stock = int(res.data[0]['stock_actual']) - int(i['Cantidad'])
                                        client.table("productos").update({"stock_actual": n_stock}).eq("id", i['id']).execute()
                            
                            st.session_state.ticket_actual = {
                                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "productos": carrito_limpio, "total": total_f, "metodo": metodo_log,
                                "cliente_fidel": cliente_fidel_nombre, "puntos_ganados": puntos_ganados,
                                "puntos_descontados": puntos_a_descontar, "nuevo_saldo": nuevo_saldo,
                                "descuento_global": desc_g_val
                            }
                            st.session_state.carrito = []
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"🚨 Error de Supabase: {e}")
                            
                with c_vac:
                    if st.button("🗑️ Vaciar", use_container_width=True):
                        st.session_state.carrito = []; st.rerun()
            else:
                st.markdown("<div style='background-color: #f8f9fa; padding: 10px; border-radius: 5px; color: #666; border: 1px solid #ddd;'>🛒 Carrito vacío.</div>", unsafe_allow_html=True)
        st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)


# ==========================================
# --- TAB 3: CLIENTES Y MASCOTAS (CRM) ---
# ==========================================
with tab3:
    st.markdown("<h3 style='margin-bottom: 5px;'>👥 Gestión de Clientes y Mascotas</h3>", unsafe_allow_html=True)
    col_c1, col_c2 = st.columns([1.2, 2.5])

    with col_c1:
        st.markdown("#### 👤 Nuevo Cliente")
        with st.form("nuevo_cliente", clear_on_submit=True):
            c_nom = st.text_input("Nombre y Apellidos *")
            c_tel = st.text_input("Teléfono")
            c_ema = st.text_input("Email")
            c_nac = st.date_input("F. Nacimiento", value=None)
            c_rgpd = st.checkbox("📝 Acepta LOPD/RGPD (Envío info y promos)", value=True)
            
            st.markdown("<hr style='margin: 5px 0px; border: none; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)
            st.markdown("<p style='margin: 0; font-size: 13px; color: gray;'>🐾 Añadir mascota (Deja en blanco si es solo cliente de tienda)</p>", unsafe_allow_html=True)
            
            m_nom = st.text_input("Nombre de la mascota")
            cm1, cm2, cm3 = st.columns(3)
            with cm1: m_esp = st.selectbox("Especie", ["", "Perro", "Gato", "Ave", "Roedor", "Reptil", "Otro"])
            with cm2: m_raz = st.text_input("Raza")
            with cm3: m_nac = st.date_input("Nac. Mascota", value=None)
            m_obs = st.text_input("Observaciones (Alergias, carácter...)")

            if st.form_submit_button("💾 Guardar Ficha", type="primary", use_container_width=True):
                if c_nom:
                    res_cli = client.table("clientes").insert({
                        "nombre_dueno": c_nom, "telefono": c_tel, "email": c_ema, "fecha_nacimiento": str(c_nac) if c_nac else "",
                        "rgpd_consent": c_rgpd, "puntos": 0
                    }).execute()

                    if res_cli.data and m_nom:
                        cli_id = res_cli.data[0]['id']
                        client.table("mascotas").insert({
                            "cliente_id": cli_id, "nombre": m_nom, "especie": m_esp, 
                            "raza": m_raz, "observaciones": m_obs, "fecha_nacimiento": str(m_nac) if m_nac else ""
                        }).execute()

                    st.success("Cliente guardado correctamente"); time.sleep(0.5); st.rerun()
                else:
                    st.warning("El nombre del dueño es obligatorio.")

    with col_c2:
        # Función para calcular la edad visualmente
        def calcular_edad(fecha_str):
            try:
                nac = pd.to_datetime(fecha_str)
                hoy = pd.to_datetime("today")
                anios = hoy.year - nac.year - ((hoy.month, hoy.day) < (nac.month, nac.day))
                if anios == 0:
                    meses = hoy.month - nac.month - ((hoy.day) < (nac.day))
                    if meses < 0: meses += 12
                    return f"{meses} meses"
                return f"{anios} años"
            except: return ""

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
            """Renderiza la ficha clínica, el historial y el sistema inteligente de reservas."""
            st.markdown(f"#### 📖 Ficha e Historial Clínico/Peluquería: **{m_nombre}**")
            
            historial = m_data.get('historial_trabajos')
            if not isinstance(historial, list): historial = []
            
            df_hist = pd.DataFrame(historial)
            for col in ["Fecha", "Trabajo / Servicio", "Duración (min)", "Importe (€)"]:
                if col not in df_hist.columns: df_hist[col] = None
                
            df_hist = df_hist[["Fecha", "Trabajo / Servicio", "Duración (min)", "Importe (€)"]]
            
            df_hist["Fecha"] = pd.to_datetime(df_hist["Fecha"], format="%d/%m/%Y", errors="coerce")
            df_hist["Duración (min)"] = pd.to_numeric(df_hist["Duración (min)"], errors="coerce")
            df_hist["Importe (€)"] = pd.to_numeric(df_hist["Importe (€)"], errors="coerce")
            
            ed_hist = st.data_editor(
                df_hist, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"ed_hist_{prefix}_{m_id}",
                column_config={
                    "Fecha": st.column_config.DateColumn("Fecha (D/M/A)", format="DD/MM/YYYY"),
                    "Trabajo / Servicio": st.column_config.TextColumn("Servicio Realizado"),
                    "Duración (min)": st.column_config.NumberColumn("Duración (min)", min_value=0, step=5),
                    "Importe (€)": st.column_config.NumberColumn("Importe Cobrado (€)", format="%.2f", min_value=0.0)
                }
            )
            
            if st.button(f"💾 Guardar Historial de {m_nombre}", type="primary", key=f"btn_hist_{prefix}_{m_id}"):
                df_save = ed_hist.copy()
                df_save['Fecha'] = pd.to_datetime(df_save['Fecha']).dt.strftime('%d/%m/%Y').fillna("")
                df_save = df_save.fillna("")
                client.table("mascotas").update({"historial_trabajos": df_save.to_dict(orient='records')}).eq("id", m_id).execute()
                st.success("Historial actualizado correctamente."); time.sleep(0.5); st.rerun()
                
            st.markdown("---")
            st.markdown(f"#### 📅 Agendar Cita Inteligente para **{m_nombre}**")
            st.markdown("<p style='color: gray; font-size: 13px;'>El sistema calcula automáticamente los huecos libres (09:00 a 21:00) para la fecha y duración seleccionadas.</p>", unsafe_allow_html=True)
            
            c_cal1, c_cal2 = st.columns([1, 1])
            with c_cal1: f_fecha = st.date_input("1. Selecciona la fecha de la cita:", value=date.today(), key=f"fcita_{prefix}_{m_id}")
            with c_cal2: f_dur = st.number_input("2. Duración del servicio (minutos)", min_value=5, max_value=300, value=60, step=5, key=f"fdur_{prefix}_{m_id}")
            
            res_citas = client.table("citas").select("fecha_hora, duracion_minutos").gte("fecha_hora", f"{f_fecha} 00:00:00").lte("fecha_hora", f"{f_fecha} 23:59:59").execute()
            citas_dia = res_citas.data if res_citas.data else []
            
            # --- CÁLCULO DE TRAMOS LIBRES CONTINUOS ---
            bloques_libres = []
            hora_actual = pd.to_datetime(f"{f_fecha} 09:00")
            fin_jornada = pd.to_datetime(f"{f_fecha} 21:00")
            
            citas_ordenadas = []
            for c in citas_dia:
                dt_ini = pd.to_datetime(c['fecha_hora'])
                dt_fin = dt_ini + pd.Timedelta(minutes=c.get('duracion_minutos') or 60)
                citas_ordenadas.append({"ini": dt_ini, "fin": dt_fin})
            citas_ordenadas.sort(key=lambda x: x["ini"])
            
            for c in citas_ordenadas:
                if hora_actual < c["ini"]:
                    if (c["ini"] - hora_actual).total_seconds() / 60 >= f_dur:
                        bloques_libres.append(f"{hora_actual.strftime('%H:%M')} a {c['ini'].strftime('%H:%M')}")
                hora_actual = max(hora_actual, c["fin"])
                
            if hora_actual < fin_jornada and (fin_jornada - hora_actual).total_seconds() / 60 >= f_dur:
                bloques_libres.append(f"{hora_actual.strftime('%H:%M')} a {fin_jornada.strftime('%H:%M')}")
                
            if bloques_libres:
                st.success(f"🟢 **Tramos libres para {f_dur} min:** " + " | ".join(bloques_libres))
            else:
                st.error(f"🔴 No hay tramos continuos de {f_dur} minutos libres en este día.")

            # --- CÁLCULO DE HUECOS SELECCIONABLES (Cada 5 min) ---
            huecos = []
            for h in range(9, 21):
                for m in range(0, 60, 5):
                    dt_ini = pd.to_datetime(f"{f_fecha} {h:02d}:{m:02d}")
                    dt_fin = dt_ini + pd.Timedelta(minutes=f_dur)
                    if dt_fin > pd.to_datetime(f"{f_fecha} 21:00"): continue
                    
                    solapa = False
                    for c in citas_dia:
                        c_ini = pd.to_datetime(c['fecha_hora'])
                        c_fin = c_ini + pd.Timedelta(minutes=c.get('duracion_minutos') or 60)
                        if dt_ini < c_fin and dt_fin > c_ini:
                            solapa = True; break
                    if not solapa: huecos.append(f"{h:02d}:{m:02d}")
                    
            if not huecos:
                st.warning("⚠️ No hay horas de inicio disponibles este día para esa duración.")
            else:
                with st.form(f"form_cita_{prefix}_{m_id}", border=True):
                    fc_1, fc_2 = st.columns([1, 2])
                    with fc_1: f_hora = st.selectbox("3. Hora de inicio:", huecos)
                    with fc_2: f_serv = st.selectbox("4. Servicio:", ["Peluquería (Baño y Corte)", "Peluquería (Solo Baño)", "Corte de Uñas", "Revisión Veterinaria", "Otro"])
                    if st.form_submit_button("➕ Confirmar Cita", type="primary", use_container_width=True):
                        client.table("citas").insert({"mascotas_id": m_id, "fecha_hora": f"{f_fecha} {f_hora}", "servicio": f_serv, "duracion_minutos": int(f_dur)}).execute()
                        st.success("¡Cita reservada con éxito!"); time.sleep(1); st.rerun()

        sub_cli, sub_masc, sub_alertas, sub_encargos = st.tabs(["👤 Directorio de Clientes", "🐾 Fichas de Mascotas", "🔔 Alertas y Recordatorios", "🛍️ Encargos de Clientes"])
        
        with sub_cli:
            res_clientes = client.table("clientes").select("*, mascotas(*)").order("created_at", desc=True).execute()
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

                b_cli = st.text_input("🔍 Buscar cliente (Nombre o Teléfono):", placeholder="Escribe para filtrar...", key="b_cli").strip().lower()
                
                if 'fecha_nacimiento' not in df_cli.columns: df_cli['fecha_nacimiento'] = ""
                df_cli['Tipo Cliente'] = df_cli['mascotas'].apply(lambda x: "🐾 Con mascota" if isinstance(x, list) and len(x) > 0 else "🛍️ Solo tienda")
                df_cli_vista = df_cli[['id', 'nombre_dueno', 'telefono', 'email', 'fecha_nacimiento', 'Tipo Cliente']].copy()
                
                if b_cli:
                    df_cli_vista = df_cli_vista[
                        df_cli_vista['nombre_dueno'].str.lower().str.contains(b_cli, na=False) |
                        df_cli_vista['telefono'].astype(str).str.contains(b_cli, na=False)
                    ]
                
                # Aseguramos columnas nuevas por si acaban de ejecutarse en SQL
                if 'rgpd_consent' not in df_cli.columns: df_cli['rgpd_consent'] = True
                if 'puntos' not in df_cli.columns: df_cli['puntos'] = 0
                
                df_cli_vista['RGPD'] = df_cli['rgpd_consent']
                df_cli_vista['Puntos'] = df_cli['puntos']

                df_cli_vista.insert(0, "Ver", False)
                st.markdown("💡 *Marca la casilla **'👁️ Ver'** para abrir la ficha del cliente y ver sus mascotas.*")
                
                ed_cli = st.data_editor(
                    df_cli_vista,
                    column_config={
                        "Ver": st.column_config.CheckboxColumn("👁️ Ver", default=False), 
                        "id": None, "nombre_dueno": "Nombre Cliente", "telefono": "Tel.", 
                        "email": "Email", "fecha_nacimiento": "F. Nac",
                        "RGPD": st.column_config.CheckboxColumn("LOPD"),
                        "Puntos": st.column_config.NumberColumn("🌟 Ptos"),
                        "Tipo Cliente": st.column_config.TextColumn("Perfil", disabled=True)
                    },
                    use_container_width=True, hide_index=True, num_rows="dynamic", key="ed_clientes", height=250
                )
                if st.button("💾 Guardar Cambios en Clientes", type="primary"):
                    ed_cli_clean = ed_cli.drop(columns=["Ver", "Tipo Cliente"])
                    ids_actuales = ed_cli_clean['id'].dropna().tolist()
                    ids_orig = df_cli_vista['id'].tolist()
                    for id_b in [i for i in ids_orig if i not in ids_actuales]: client.table("clientes").delete().eq("id", id_b).execute()
                    
                    for _, row in ed_cli_clean.iterrows():
                        if pd.notna(row['id']):
                            client.table("clientes").update({
                                "nombre_dueno": str(row['nombre_dueno']), "telefono": str(row['telefono']),
                                "email": str(row['email']), "fecha_nacimiento": str(row['fecha_nacimiento']),
                                "rgpd_consent": bool(row.get('RGPD', True)), "puntos": int(row.get('Puntos', 0))
                            }).eq("id", row['id']).execute()
                    st.success("Directorio de clientes actualizado."); time.sleep(0.5); st.rerun()
                    
                st.markdown("---")
                
                # --- FICHA COMPLETA DEL DUEÑO Y SUS MASCOTAS ---
                filas_c_marcadas = ed_cli[ed_cli["Ver"] == True]
                if not filas_c_marcadas.empty:
                    c_id = filas_c_marcadas.iloc[0]['id']
                    c_data = df_cli[df_cli['id'] == c_id].iloc[0]
                    c_nombre = c_data['nombre_dueno']
                    
                    st.markdown(f"#### 📖 Ficha de Cliente: **{c_nombre}**")
                    
                    mascotas_lista = c_data.get('mascotas', [])
                    if isinstance(mascotas_lista, list) and len(mascotas_lista) > 0:
                        df_mc = pd.DataFrame(mascotas_lista)
                        if 'fecha_nacimiento' not in df_mc.columns: df_mc['fecha_nacimiento'] = ""
                        df_mc['Edad'] = df_mc['fecha_nacimiento'].apply(calcular_edad)
                        if 'historial_trabajos' not in df_mc.columns: df_mc['historial_trabajos'] = [[] for _ in range(len(df_mc))]
                        df_mc['Duración Media'] = df_mc['historial_trabajos'].apply(calcular_duracion_media)
                        
                        cols_ok = ['id', 'nombre', 'especie', 'raza', 'fecha_nacimiento', 'Edad', 'Duración Media', 'observaciones']
                        for col in cols_ok:
                            if col not in df_mc.columns: df_mc[col] = ""
                            
                        df_mc_show = df_mc[cols_ok].rename(columns={
                            "nombre": "Nombre Mascota", "especie": "Especie", "raza": "Raza", 
                            "fecha_nacimiento": "F. Nacimiento", "observaciones": "Observaciones"
                        })
                        
                        df_mc_show.insert(0, "Ver Ficha", False)
                        st.markdown("💡 *Edita los datos directamente. Para eliminar, selecciona la fila y pulsa 'Supr'. Marca **'👁️ Ver Ficha'** para abrir el historial y agendar.*")
                        ed_mc = st.data_editor(
                            df_mc_show, use_container_width=True, hide_index=True, num_rows="dynamic", key=f"ed_mc_{c_id}",
                            column_config={
                                "Ver Ficha": st.column_config.CheckboxColumn("👁️ Ver Ficha", default=False),
                                "id": None, "Edad": st.column_config.TextColumn(disabled=True), "Duración Media": st.column_config.TextColumn(disabled=True)
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
                                if pd.notna(ru['id']):
                                    client.table("mascotas").update({
                                        "nombre": str(ru['Nombre Mascota']), "especie": str(ru['Especie']),
                                        "raza": str(ru['Raza']), "fecha_nacimiento": str(ru['F. Nacimiento']),
                                        "observaciones": str(ru['Observaciones'])
                                    }).eq("id", ru['id']).execute()
                                else:
                                    if pd.notna(ru['Nombre Mascota']) and str(ru['Nombre Mascota']).strip():
                                        client.table("mascotas").insert({
                                            "cliente_id": c_id, "nombre": str(ru['Nombre Mascota']),
                                            "especie": str(ru['Especie']) if pd.notna(ru['Especie']) else "",
                                            "raza": str(ru['Raza']) if pd.notna(ru['Raza']) else "",
                                            "fecha_nacimiento": str(ru['F. Nacimiento']) if pd.notna(ru['F. Nacimiento']) else "",
                                            "observaciones": str(ru['Observaciones']) if pd.notna(ru['Observaciones']) else ""
                                        }).execute()
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
                sel_cli = st.selectbox("Selecciona el cliente:", list(dict_cli.keys()))
                c_m1, c_m2, c_m3 = st.columns([1.5, 1, 1])
                with c_m1: nx_nom = st.text_input("Nombre mascota", key="nx_nom")
                with c_m2: nx_esp = st.selectbox("Especie", ["Perro", "Gato", "Ave", "Roedor", "Otro"], key="nx_esp")
                with c_m3: nx_raz = st.text_input("Raza", key="nx_raz")
                
                if st.form_submit_button("Añadir Mascota", use_container_width=True):
                    if nx_nom and sel_cli:
                        client.table("mascotas").insert({
                            "cliente_id": dict_cli[sel_cli], "nombre": nx_nom, "especie": nx_esp, "raza": nx_raz
                        }).execute()
                        st.success("Mascota añadida a la familia"); time.sleep(0.5); st.rerun()
                    else:
                        st.warning("Falta el nombre de la mascota.")
                        
        with sub_masc:
            res_mascotas = client.table("mascotas").select("*, clientes(nombre_dueno)").order("id", desc=True).execute()
            if res_mascotas.data:
                df_m = pd.DataFrame(res_mascotas.data)
                
                b_masc = st.text_input("🔍 Buscar mascota por nombre:", placeholder="Escribe para filtrar...", key="b_masc").strip().lower()
                
                df_m['Dueño'] = df_m['clientes'].apply(lambda x: x.get('nombre_dueno', '') if isinstance(x, dict) else '')
                if 'fecha_nacimiento' not in df_m.columns: df_m['fecha_nacimiento'] = ""
                df_m['Edad'] = df_m['fecha_nacimiento'].apply(calcular_edad)
                if 'historial_trabajos' not in df_m.columns:
                    df_m['historial_trabajos'] = [[] for _ in range(len(df_m))]
                df_m['Duración Media'] = df_m['historial_trabajos'].apply(calcular_duracion_media)
                
                df_m_vista = df_m[['id', 'nombre', 'Dueño', 'especie', 'raza', 'fecha_nacimiento', 'Edad', 'Duración Media', 'observaciones']].copy()
                
                if b_masc:
                    df_m_vista = df_m_vista[df_m_vista['nombre'].str.lower().str.contains(b_masc, na=False)]
                    
                df_m_vista.insert(0, "Ver", False)
                
                st.markdown("💡 *Marca la casilla **'👁️ Ver'** para abrir la ficha completa y el historial de la mascota.*")
                
                ed_m = st.data_editor(
                    df_m_vista,
                    column_config={"Ver": st.column_config.CheckboxColumn("👁️ Ver", default=False), "id": None, "Dueño": st.column_config.TextColumn(disabled=True), "Edad": st.column_config.TextColumn(disabled=True), "nombre": "Mascota", "fecha_nacimiento": "F. Nacimiento", "observaciones": "Observaciones Generales", "Duración Media": st.column_config.TextColumn("T. Medio", disabled=True, help="Tiempo medio de servicio calculado del historial.")},
                    use_container_width=True, hide_index=True, num_rows="dynamic", key="ed_mascotas", height=400
                )
                if st.button("💾 Guardar Cambios en Mascotas", type="primary"):
                    ed_m_clean = ed_m.drop(columns=["Ver"])
                    ids_actuales = ed_m_clean['id'].dropna().tolist()
                    ids_orig = df_m_vista['id'].tolist()
                    for id_b in [i for i in ids_orig if i not in ids_actuales]: client.table("mascotas").delete().eq("id", id_b).execute()
                    
                    for _, row in ed_m_clean.iterrows():
                        if pd.notna(row['id']):
                            client.table("mascotas").update({
                                "nombre": str(row['nombre']), "especie": str(row['especie']),
                                "raza": str(row['raza']), "fecha_nacimiento": str(row['fecha_nacimiento']),
                                "observaciones": str(row['observaciones'])
                            }).eq("id", row['id']).execute()
                    st.success("Fichas de mascotas actualizadas."); time.sleep(0.5); st.rerun()
                    
                st.markdown("---")
                
                # --- FICHA COMPLETA E HISTORIAL DE LA MASCOTA ---
                filas_m_marcadas = ed_m[ed_m["Ver"] == True]
                if not filas_m_marcadas.empty:
                    m_id = filas_m_marcadas.iloc[0]['id']
                    m_data = df_m[df_m['id'] == m_id].iloc[0]
                    m_nombre = m_data['nombre']
                    mostrar_ficha_clinica(m_id, m_nombre, m_data, prefix="ind")
            else: st.info("No hay mascotas registradas.")

        with sub_alertas:
            st.markdown("#### 🔔 Alertas de Mantenimiento Inteligentes")
            st.markdown("<p style='color:gray; font-size:14px;'>El sistema escanea el historial de las mascotas y te avisa de las que llevan tiempo sin venir, generándote un enlace directo para enviarles un WhatsApp pre-escrito con un solo toque.</p>", unsafe_allow_html=True)
            
            c_al1, c_al2 = st.columns([1, 2])
            with c_al1:
                dias_aviso = st.slider("Mostrar mascotas que no hayan venido en más de (días):", min_value=15, max_value=180, value=45, step=5)
            
            res_m_alertas = client.table("mascotas").select("*, clientes(nombre_dueno, telefono)").execute()
            
            if res_m_alertas.data:
                alertas = []
                hoy_dt = pd.to_datetime('today')
                
                for m in res_m_alertas.data:
                    hist = m.get('historial_trabajos', [])
                    if isinstance(hist, list) and len(hist) > 0:
                        try:
                            fechas = [pd.to_datetime(h['Fecha'], format='%d/%m/%Y', errors='coerce') for h in hist if h.get('Fecha')]
                            fechas = [f for f in fechas if pd.notna(f)]
                            if fechas:
                                ultima_visita = max(fechas)
                                dias_transcurridos = (hoy_dt - ultima_visita).days
                                
                                if dias_transcurridos >= dias_aviso:
                                    dueno = m['clientes']['nombre_dueno'] if m.get('clientes') else 'Dueño'
                                    telefono = m['clientes']['telefono'] if m.get('clientes') else ''
                                    
                                    # Preparar el número para WhatsApp (+34 España)
                                    tel_limpio = ''.join(filter(str.isdigit, str(telefono)))
                                    if tel_limpio and len(tel_limpio) == 9 and not tel_limpio.startswith('34'):
                                        tel_limpio = '34' + tel_limpio
                                        
                                    # Mensaje de marketing amistoso
                                    mensaje = f"¡Hola {dueno}! 🐾 Soy Raquel de Animalarium. Te escribo porque he visto en la ficha de {m['nombre']} que ya le toca su sesión de mantenimiento (hace {dias_transcurridos} días de su última visita). ¿Te gustaría que le busquemos un huequito en la agenda para estos días? ¡Un saludo! 🐶✂️"
                                    url_wa = f"https://wa.me/{tel_limpio}?text={urllib.parse.quote(mensaje)}" if tel_limpio else None
                                    
                                    alertas.append({
                                        "Mascota": m['nombre'], "Dueño": dueno,
                                        "Última Visita": ultima_visita.strftime('%d/%m/%Y'),
                                        "Días Sin Venir": dias_transcurridos, "WhatsApp": url_wa
                                    })
                        except Exception as e: pass
                
                if alertas:
                    df_alertas = pd.DataFrame(alertas).sort_values(by="Días Sin Venir", ascending=False)
                    st.warning(f"⚠️ Tienes **{len(alertas)}** clientes pendientes de contactar para mantenimiento.")
                    st.dataframe(df_alertas, use_container_width=True, hide_index=True, column_config={"WhatsApp": st.column_config.LinkColumn("📱 Acción Automática", display_text="💬 Enviar WhatsApp")})
                else:
                    st.success("✨ ¡Genial! Tienes la agenda al día. Ninguna mascota supera los días de alerta.")

        with sub_encargos:
            col_en1, col_en2 = st.columns([1, 2])
            with col_en1:
                st.markdown("#### 📝 Registrar Encargo")
                with st.form("n_encargo", clear_on_submit=True):
                    opc_cli_enc = ["👤 Cliente no registrado (Escribir a mano)"]
                    if res_clientes.data:
                        opc_cli_enc += [f"{c['nombre_dueno']} | {c['telefono']}" for c in res_clientes.data]
                    
                    sel_cli_enc = st.selectbox("1. Buscar Cliente:", opc_cli_enc)
                    
                    st.markdown("<p style='font-size:12px; color:gray; margin:0;'>O rellenar si no está registrado:</p>", unsafe_allow_html=True)
                    c_nom_man, c_tel_man = st.columns(2)
                    with c_nom_man: e_cli_man = st.text_input("Nombre", key="e_cli_man")
                    with c_tel_man: e_tel_man = st.text_input("Teléfono", key="e_tel_man")
                    
                    st.markdown("---")
                    e_prod = st.text_input("2. Producto que pide *")
                    e_cant = st.number_input("3. Cantidad *", min_value=1, value=1)
                    e_obs = st.text_area("4. Observaciones")
                    
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
                                client.table("encargos_clientes").insert({
                                    "nombre_cliente": final_cli, "telefono": final_tel, 
                                    "detalle_pedido": f"{e_cant}x {e_prod}",
                                    "notas": e_obs, "estado": "Pendiente"
                                }).execute()
                                st.success("Encargo guardado."); time.sleep(0.5); st.rerun()
                            except Exception as e:
                                st.error("Error al guardar en la base de datos.")
                        else:
                            st.warning("Debes indicar un cliente y el producto a pedir.")
            
            with col_en2:
                st.markdown("#### 📌 Encargos Pendientes")
                try:
                    res_e = client.table("encargos_clientes").select("*").order("created_at", desc=True).execute()
                    if res_e.data:
                        df_e = pd.DataFrame(res_e.data)
                        df_e['Fecha'] = pd.to_datetime(df_e['created_at']).dt.strftime('%d/%m/%Y')
                        if 'notas' not in df_e.columns: df_e['notas'] = ""
                        
                        hoy_date = pd.to_datetime('today')
                        for idx, row in df_e.iterrows():
                            dias = (hoy_date - pd.to_datetime(row['created_at']).dt.tz_localize(None)).days
                            if dias >= 2 and row['estado'] == 'Pendiente':
                                st.warning(f"⚠️ **RETRASO:** El encargo de {row['nombre_cliente']} lleva {dias} días en estado Pendiente.")
                        
                        df_e_vista = df_e[['id', 'Fecha', 'nombre_cliente', 'telefono', 'detalle_pedido', 'notas', 'estado']]
                        ed_e = st.data_editor(
                            df_e_vista, hide_index=True, use_container_width=True, num_rows="dynamic", height=300,
                            column_config={
                                "id": None, "Fecha": "Día", "nombre_cliente": "Cliente", "telefono": "Tel.",
                                "detalle_pedido": "Producto y Cant.", "notas": "Observaciones",
                                "estado": st.column_config.SelectboxColumn("Estado", options=["Pendiente", "Pedido", "Recibido", "Entregado"])
                            }
                        )
                        if st.button("💾 Guardar Cambios en Encargos"):
                            for _, r in ed_e.iterrows():
                                if pd.notna(r['id']):
                                    client.table("encargos_clientes").update({
                                        "estado": str(r['estado']), "notas": str(r['notas'])
                                    }).eq("id", r['id']).execute()
                            st.rerun()
                    else: st.info("No hay encargos activos.")
                except: st.warning("Por favor, revisa la conexión con la tabla encargos_clientes.")

# ==========================================
# --- TAB 4: HISTORIAL (VERSIÓN CON CASILLA DE VER) ---
# ==========================================
with tab4:
    st.markdown("<h3 style='margin-top: -15px;'>📜 Historial de Ventas y Cajas</h3>", unsafe_allow_html=True)
    sub_h_ventas, sub_h_cajas = st.tabs(["🛒 Tickets y Ventas", "🔒 Cierres de Caja"])
    
    with sub_h_ventas:
        c_f1, c_f2, c_f3 = st.columns([1,1,1])
        with c_f1: preset = st.selectbox("Filtro rápido:", ["Esta semana", "Este mes", "Trimestre Actual", "Todo el año"])
        
        hoy = date.today()
        if preset == "Esta semana": f_ini = hoy - timedelta(days=hoy.weekday())
        elif preset == "Este mes": f_ini = hoy.replace(day=1)
        elif preset == "Trimestre Actual": f_ini = hoy.replace(month=((hoy.month-1)//3)*3+1, day=1)
        else: f_ini = hoy.replace(month=1, day=1)

        with c_f2: f_inicio_v = st.date_input("Desde:", value=f_ini)
        with c_f3: f_fin_v = st.date_input("Hasta:", value=hoy)

        res_v = client.table("ventas_historial").select("*").gte("created_at", f"{f_inicio_v}T00:00:00").lte("created_at", f"{f_fin_v}T23:59:59").order("id", desc=True).execute()
        
        if res_v.data:
            df_v = pd.DataFrame(res_v.data)
            try: df_v['Fecha'] = pd.to_datetime(df_v['created_at']).dt.strftime('%d/%m/%Y %H:%M')
            except: df_v['Fecha'] = "---"
            
            for col in ['metodo_pago', 'estado', 'cliente_deuda']:
                if col not in df_v.columns: df_v[col] = "N/A"

            # 1. PREPARAMOS EL DATAFRAME
            df_vista = df_v[['id', 'Fecha', 'total', 'metodo_pago', 'estado', 'cliente_deuda']].copy()
            
            # --- MAGIA TÁCTIL: Añadimos la columna Checkbox ---
            df_vista.insert(0, "Borrar", False)
            df_vista.insert(0, "Ver", False)
            
            st.markdown("💡 *Marca **'👁️ Ver'** para abrir el desglose. Marca **'🗑️ Borrar'** para eliminar. Haz doble clic en las celdas normales para corregirlas.*")
            
            # 2. TABLA EDITABLE CON CASILLA
            edited_df = st.data_editor(
                df_vista,
                column_config={
                    "Ver": st.column_config.CheckboxColumn("👁️ Ver", default=False),
                    "Borrar": st.column_config.CheckboxColumn("🗑️ Borrar", default=False),
                    "id": st.column_config.NumberColumn("Nº", disabled=True, width="small"),
                    "Fecha": st.column_config.TextColumn("Fecha", disabled=True),
                    "total": st.column_config.NumberColumn("Total (€)", disabled=True, format="%.2f"),
                    "metodo_pago": st.column_config.SelectboxColumn("Método", options=["Efectivo", "Tarjeta", "Bizum", "Mixto"]),
                    "estado": st.column_config.SelectboxColumn("Estado", options=["Completado", "Deuda", "DEVUELTO"]),
                    "cliente_deuda": st.column_config.TextColumn("Cliente (Si debe)")
                },
                hide_index=True, 
                use_container_width=True, 
                height=250, 
                key="editor_tickets"
            )
            
            # 2.5 SISTEMA DE BORRADO DE TICKETS (PARA PRUEBAS)
            filas_borrar_tk = edited_df[edited_df["Borrar"] == True]
            if not filas_borrar_tk.empty:
                st.error(f"⚠️ Has marcado {len(filas_borrar_tk)} ticket(s) para eliminar. El stock se restaurará automáticamente (excepto artículos manuales).")
                if st.button("🚨 CONFIRMAR ELIMINACIÓN", type="primary", use_container_width=True):
                    for idx, row in filas_borrar_tk.iterrows():
                        tk_id = row['id']
                        tk_data = df_v[df_v['id'] == tk_id].iloc[0]
                        # Devolver stock solo si el ticket no estaba ya DEVUELTO
                        if str(tk_data.get('estado', '')).upper() != "DEVUELTO":
                            for p in tk_data.get('productos', []):
                                if not p.get('Manual', False) and 'id' in p:
                                    res_p = client.table("productos").select("stock_actual").eq("id", p['id']).execute()
                                    if res_p.data:
                                        client.table("productos").update({"stock_actual": res_p.data[0]['stock_actual'] + p['Cantidad']}).eq("id", p['id']).execute()
                        # Eliminar registro
                        client.table("ventas_historial").delete().eq("id", tk_id).execute()
                    st.success("Ticket(s) eliminado(s) correctamente."); time.sleep(1); st.rerun()

            # 3. GUARDAR CORRECCIONES EN SUPABASE
            if st.button("💾 Guardar Correcciones de la Tabla", type="primary"):
                # Ignoramos las columnas de acción para que no afecten a la base de datos
                df_original = df_vista.drop(columns=["Ver", "Borrar"])
                df_editado = edited_df.drop(columns=["Ver", "Borrar"])
                diferencias = df_editado.compare(df_original)
                if not diferencias.empty:
                    for idx in diferencias.index.tolist():
                        client.table("ventas_historial").update({
                            "metodo_pago": str(edited_df.loc[idx, 'metodo_pago']),
                            "estado": str(edited_df.loc[idx, 'estado']),
                            "cliente_deuda": str(edited_df.loc[idx, 'cliente_deuda']) if str(edited_df.loc[idx, 'cliente_deuda']) != 'nan' else ""
                        }).eq("id", int(edited_df.loc[idx, 'id'])).execute()
                    st.success("Tickets actualizados."); time.sleep(0.8); st.rerun()

            st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
            
           # --- 4. DETALLE DINÁMICO (CON DESCUENTO EDITABLE) ---
            filas_marcadas = edited_df[edited_df["Ver"] == True]
            
            if not filas_marcadas.empty:
                t_id = filas_marcadas.iloc[0]['id']
                t_info = df_v[df_v['id'] == t_id].iloc[0]
                
                st.markdown(f"#### 🔎 Detalle y Edición del Ticket #{t_id}")
                prods = t_info.get('productos', [])
                
                if prods:
                    df_prods = pd.DataFrame(prods)
                    
                    # 1. Tabla de productos editable
                    edit_prods = st.data_editor(
                        df_prods, 
                        column_config={
                            "Subtotal": st.column_config.NumberColumn("Subtotal (€)", format="%.2f", disabled=True),
                            "Manual": None,
                            "IGIC": None,
                            "Precio": st.column_config.NumberColumn("Precio (€)", format="%.2f"),
                            "Desc. %": st.column_config.NumberColumn("Desc. Ud (%)", format="%d%%")
                        },
                        use_container_width=True, 
                        hide_index=True, 
                        num_rows="dynamic",
                        key=f"edit_det_{t_id}"
                    )
                    
                    # Recalcular subtotal de la lista por si hubo cambios en la tabla
                    if 'Cantidad' in edit_prods.columns and 'Precio' in edit_prods.columns:
                        edit_prods['Subtotal'] = (edit_prods['Cantidad'] * edit_prods['Precio']) * (1 - edit_prods.get('Desc. %', 0) / 100)
                    
                    suma_articulos = edit_prods['Subtotal'].sum()

                    st.markdown("---")
                    # 2. SECCIÓN DE TOTALES CON DESCUENTO EDITABLE
                    c_tot1, c_tot2, c_tot3 = st.columns(3)
                    
                    with c_tot1:
                        st.metric("Suma Artículos", f"{suma_articulos:.2f}€")
                    
                    with c_tot2:
                        # Nuevo: Cuadro para cambiar el descuento global del ticket
                        nuevo_desc_global = st.number_input(
                            "Corregir Dto. Global (%)", 
                            min_value=0, 
                            max_value=100, 
                            value=int(t_info.get('descuento_global', 0)),
                            key=f"desc_glob_{t_id}"
                        )
                    
                    # Calculamos el total final aplicando el descuento que haya en el cuadro
                    total_final_calculado = suma_articulos * (1 - nuevo_desc_global / 100)
                    
                    with c_tot3:
                        st.metric("TOTAL FINAL", f"{total_final_calculado:.2f}€", 
                                  delta=f"-{(suma_articulos - total_final_calculado):.2f}€" if nuevo_desc_global > 0 else None)

                    # 3. BOTONES DE ACCIÓN
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if st.button(f"💾 Guardar Todo (Productos + Descuento)", use_container_width=True, type="primary"):
                            nuevo_json = json.loads(edit_prods.to_json(orient='records'))
                            
                            # Actualizamos Supabase con la nueva lista de productos, el nuevo descuento y el nuevo total
                            client.table("ventas_historial").update({
                                "productos": nuevo_json,
                                "descuento_global": float(nuevo_desc_global),
                                "total": float(total_final_calculado)
                            }).eq("id", int(t_id)).execute()
                            st.success(f"Ticket #{t_id} actualizado correctamente.")
                            time.sleep(0.8)
                            st.rerun()
                    
                    with c2:
                        if "DEVUELTO" not in str(t_info.get('estado', '')).upper():
                            if st.button(f"↩️ Devolver y Restaurar Stock", use_container_width=True):
                                # Lógica de devolución (la que ya tenías)
                                for p in prods:
                                    if not p.get('Manual', False) and 'id' in p:
                                        res_p = client.table("productos").select("stock_actual").eq("id", p['id']).execute()
                                        if res_p.data:
                                            client.table("productos").update({"stock_actual": res_p.data[0]['stock_actual'] + p['Cantidad']}).eq("id", p['id']).execute()
                                client.table("ventas_historial").update({"estado": "DEVUELTO"}).eq("id", int(t_id)).execute()
                                st.success("Venta anulada."); time.sleep(0.8); st.rerun()
                                
                    with c3:
                        try:
                            fecha_t_print = pd.to_datetime(t_info['created_at']).strftime('%d/%m/%Y %H:%M')
                        except:
                            fecha_t_print = "Fecha desconocida"
                            
                        html_reprint = f"""
                        <!DOCTYPE html><html><head><meta charset='utf-8'>
                        <style>
                            body {{ margin: 0; padding: 0; font-family: sans-serif; text-align: center; }}
                            .btn-print {{ padding: 12px; background-color: #005275; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%; font-size: 15px; }}
                            #ticket-impresion-re {{ display: none; }}
                        </style>
                        </head><body>
                        <button class="btn-print" onclick="reimprimirConStar()">🖨️ IMPRIMIR COPIA TICKET</button>
                        <div id="ticket-impresion-re">
                            <div style="text-align: center; font-family: monospace; width: 100%; font-size: 22px; color: black; font-weight: bold;">
                                <b style="font-size: 34px;">ANIMALARIUM</b><br>
                                Raquel Trujillo Hernández<br>DNI: 78854854K<br>C/ José Hernández Alfonso, 26<br>38009 S/C de Tenerife<br><br>
                                <div style="text-align: left; font-size: 22px;">Fecha: {fecha_t_print}<br>COPIA DE TICKET #{t_id}</div>
                                <hr style="border-top: 2px dashed #000; margin: 10px 0px;">
                                <table style="width: 100%; font-size: 22px; text-align: left; font-weight: bold;">
                        """
                        for p in prods:
                            desc_item = p.get('Desc %', 0.0)
                            if desc_item > 0:
                                html_reprint += f"<tr><td style='padding-bottom: 0px;'>{p['Cantidad']}x {p['Producto']}</td><td style='text-align: right; padding-bottom: 0px;'>{p['Subtotal']:.2f}€</td></tr>"
                                html_reprint += f"<tr><td colspan='2' style='font-size: 16px; padding-bottom: 5px; color: #555;'>  ↳ Dto. {desc_item}% aplicado</td></tr>"
                            else:
                                html_reprint += f"<tr><td style='padding-bottom: 5px;'>{p['Cantidad']}x {p['Producto']}</td><td style='text-align: right; padding-bottom: 5px;'>{p['Subtotal']:.2f}€</td></tr>"
                        html_reprint += f"""
                                </table>
                                <hr style="border-top: 2px dashed #000; margin: 10px 0px;">
                        """
                        desc_g_re = float(t_info.get('descuento_global', 0.0))
                        if desc_g_re > 0:
                            subt_re = total_final_calculado / (1 - desc_g_re / 100) if (1 - desc_g_re / 100) > 0 else total_final_calculado
                            html_reprint += f"<div style='text-align: right; font-size: 22px;'>Subtotal: {subt_re:.2f}€</div>"
                            html_reprint += f"<div style='text-align: right; font-size: 22px;'><b>Dto. Global: -{desc_g_re}%</b></div>"
                        
                        html_reprint += f"""
                                <div style="text-align: right; font-size: 28px;"><b>TOTAL: {total_final_calculado:.2f}€</b></div>
                                <div style="font-size: 18px; color: #000; margin-top: 30px; text-align: center;"><b>POLÍTICA DE DEVOLUCIÓN</b><br>Plazo de 14 días con ticket y<br>embalaje original en perfecto estado.</div>
                            </div>
                        </div>
                        <script>
                        function reimprimirConStar() {{
                            var ticketHTML = document.getElementById('ticket-impresion-re').innerHTML;
                            var fullHTML = "<!DOCTYPE html><html><head><meta charset='utf-8'></head><body style='margin:0; padding:0; background-color:white;'>" + ticketHTML + "</body></html>";
                            var htmlCodificado = encodeURIComponent(fullHTML);
                            var urlRetorno = "https://google.com";
                            try {{ if (window.top.location.href && window.top.location.href !== "about:blank") {{ urlRetorno = window.top.location.href.split('#')[0] + "#impreso"; }} }} catch(e) {{}}
                            window.location.href = "starpassprnt://v1/print/nopreview?back=" + encodeURIComponent(urlRetorno) + "&html=" + htmlCodificado;
                        }}
                        </script>
                        </body></html>
                        """
                        components.html(html_reprint, height=55)
                else:
                    st.info("Este ticket no tiene productos registrados.")
            else:
                st.info("👆 Marca la casilla '👁️ Ver' de un ticket arriba para editarlo.")
                
        else: st.info("No hay ventas en este rango de fechas.")

    # --- SUB-PESTAÑA CAJAS (MANTENEMOS TU CÓDIGO ORIGINAL INTACTO) ---
    with sub_h_cajas:
        c_fc1, c_fc2 = st.columns(2)
        with c_fc1: f_inicio_c = st.date_input("Cajas desde:", value=pd.to_datetime('today') - pd.Timedelta(days=7), key="fc1")
        with c_fc2: f_fin_c = st.date_input("Cajas hasta:", value=pd.to_datetime('today'), key="fc2")

        try:
            res_cajas = client.table("control_caja").select("*").eq("estado", "Cerrada").gte("created_at", f"{f_inicio_c}T00:00:00").lte("created_at", f"{f_fin_c}T23:59:59").order("id", desc=True).execute()

            if res_cajas.data:
                df_c = pd.DataFrame(res_cajas.data)
                df_c['Fecha Apertura'] = pd.to_datetime(df_c['created_at']).dt.strftime('%d/%m/%Y %H:%M')
                df_c_vista = df_c[['id', 'Fecha Apertura', 'fondo_inicial', 'total_contado', 'descuadre']].copy()
                df_c_vista.insert(0, "Seleccionar", False)
                
                st.markdown("💡 *Marca la casilla **'🖨️ Seleccionar'** para ver el desglose e imprimir el Cierre Z.*")
                
                ed_c = st.data_editor(
                    df_c_vista,
                    column_config={
                        "Seleccionar": st.column_config.CheckboxColumn("🖨️ Seleccionar", default=False),
                        "id": None,
                        "Fecha Apertura": "Apertura",
                        "fondo_inicial": st.column_config.NumberColumn("Fondo Inicial (€)", format="%.2f"),
                        "total_contado": st.column_config.NumberColumn("Efectivo Final (€)", format="%.2f"),
                        "descuadre": st.column_config.NumberColumn("Descuadre (€)", format="%.2f")
                    },
                    hide_index=True, use_container_width=True, height=200
                )

                st.markdown("#### 🖨️ Desglose e Impresión de Cierre")
                filas_sel = ed_c[ed_c["Seleccionar"] == True]
                turno_sel = filas_sel.iloc[0]['id'] if not filas_sel.empty else None
                
                if turno_sel:
                    caja_seleccionada = df_c[df_c['id'] == turno_sel].iloc[0]
                    resumen = caja_seleccionada.get('resumen_pagos', {})
                    if not resumen or pd.isna(resumen): resumen = {"Efectivo": 0, "Tarjeta": 0, "Bizum": 0, "Ingresos": 0, "Retiradas": 0}
                    
                    html_cierre = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                    <style>
                        @media screen {{
                            #ticket-z {{ display: none; }}
                            .btn-print-z {{ background-color: #d32f2f; color: white; border: none; padding: 10px; border-radius: 5px; width: 100%; font-weight: bold; cursor: pointer; }}
                        }}
                        @media print {{
                            #btn-area {{ display: none; }}
                            #ticket-z {{ display: block; font-family: monospace; font-size: 12px; width: 300px; color: black; }}
                        }}
                    </style>
                    </head>
                    <body>
                        <div id="btn-area">
                            <button class="btn-print-z" onclick="window.print()">🖨️ IMPRIMIR CIERRE Z (TURNO #{turno_sel})</button>
                        </div>
                        <div id="ticket-z">
                            <div style="text-align: center; font-weight: bold; font-size: 16px;">CIERRE DE CAJA Z</div>
                            <div style="text-align: center;">ANIMALARIUM</div>
                            <hr style="border-top: 1px dashed black;">
                            Turno Nº: {turno_sel}<br>
                            Apertura: {caja_seleccionada['Fecha Apertura']}<br>
                            Fondo Inicial: {caja_seleccionada['fondo_inicial']:.2f} €<br>
                            <hr style="border-top: 1px dashed black;">
                            <b>VENTAS POR MÉTODO:</b><br>
                            Efectivo: {resumen.get('Efectivo', 0):.2f} €<br>
                            Tarjeta: {resumen.get('Tarjeta', 0):.2f} €<br>
                            Bizum: {resumen.get('Bizum', 0):.2f} €<br>
                            <hr style="border-top: 1px dashed black;">
                            <b>MOVIMIENTOS DE CAJA:</b><br>
                            Ingresos Extra: +{resumen.get('Ingresos', 0):.2f} €<br>
                            Retiradas/Pagos: -{resumen.get('Retiradas', 0):.2f} €<br>
                            <hr style="border-top: 1px dashed black;">
                            <b>RESULTADO DEL ARQUEO:</b><br>
                            Efectivo Contado: {caja_seleccionada['total_contado']:.2f} €<br>
                            <b>DESCUADRE: {caja_seleccionada['descuadre']:.2f} €</b><br>
                            <hr style="border-top: 1px dashed black;">
                            <div style="text-align: center;">Firma Responsable</div>
                            <br><br><br>
                        </div>
                    </body>
                    </html>
                    """
                    components.html(html_cierre, height=50)

                    res_movs = client.table("movimientos_caja").select("*").eq("id_caja", turno_sel).execute()
                    if res_movs.data:
                        st.markdown("<p style='font-size:12px; color:gray;'>Detalle de Entradas/Salidas de este turno:</p>", unsafe_allow_html=True)
                        df_m = pd.DataFrame(res_movs.data)
                        df_m['Hora'] = pd.to_datetime(df_m['created_at']).dt.strftime('%H:%M')
                        st.dataframe(df_m[['Hora', 'tipo', 'cantidad', 'motivo']], use_container_width=True, hide_index=True)
                    else: st.info("No hubo Entradas o Salidas manuales en este turno.")
            else: st.warning("No hay registros de cajas cerradas en este rango.")
        except Exception as e: st.error(f"Error cargando cajas: {e}")

# ==========================================
# --- TAB 5: CONTROL DE CAJA FUERTE ---
# ==========================================
with tab5:
    try:
        res_caja = client.table("control_caja").select("*").eq("estado", "Abierta").execute()
        caja_actual = res_caja.data[0] if res_caja.data else None
    except:
        caja_actual = None

    if not caja_actual:
        st.info("😴 La caja está actualmente CERRADA.")
        
        try:
            res_ult_caja = client.table("control_caja").select("*").eq("estado", "Cerrada").order("id", desc=True).limit(1).execute()
            if res_ult_caja.data:
                ult_caja = res_ult_caja.data[0]
                resumen = ult_caja.get('resumen_pagos', {})
                if not resumen: resumen = {"Efectivo": 0, "Tarjeta": 0, "Bizum": 0, "Ingresos": 0, "Retiradas": 0}
                f_apertura = pd.to_datetime(ult_caja['created_at']).strftime('%d/%m/%Y %H:%M')
                
                st.markdown(f"#### 🖨️ Último Cierre de Caja Registrado (Apertura: {f_apertura})")
                
                html_cierre_ult = f"""
                <!DOCTYPE html>
                <html>
                <head>
                <style>
                    @media screen {{
                        #ticket-z {{ display: block; border: 1px solid #ccc; padding: 15px; margin-top: 15px; background-color: #fffaf0; width: 300px; margin-left: auto; margin-right: auto; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }}
                        .btn-print-z {{ background-color: #005275; color: white; border: none; padding: 10px; border-radius: 5px; width: 100%; font-weight: bold; cursor: pointer; margin-bottom: 15px; }}
                    }}
                    @media print {{
                        #btn-area {{ display: none; }}
                        #ticket-z {{ display: block; font-family: monospace; font-size: 12px; width: 300px; color: black; }}
                    }}
                </style>
                </head>
                <body>
                    <div id="btn-area">
                        <button class="btn-print-z" onclick="window.print()">🖨️ IMPRIMIR ÚLTIMO CIERRE Z</button>
                    </div>
                    <div id="ticket-z">
                        <div style="text-align: center; font-weight: bold; font-size: 16px;">CIERRE DE CAJA Z</div>
                        <div style="text-align: center;">ANIMALARIUM</div>
                        <hr style="border-top: 1px dashed black;">
                        Apertura: {f_apertura}<br>
                        Fondo Inicial: {ult_caja['fondo_inicial']:.2f} €<br>
                        <hr style="border-top: 1px dashed black;">
                        <b>VENTAS POR MÉTODO:</b><br>
                        Efectivo: {resumen.get('Efectivo', 0):.2f} €<br>
                        Tarjeta (Caixa): {resumen.get('Tarjeta Caixa', 0):.2f} €<br>
                        Tarjeta (C.Siete): {resumen.get('Tarjeta Caja Siete', 0):.2f} €<br>
                        Bizum: {resumen.get('Bizum', 0):.2f} €<br>
                        <hr style="border-top: 1px dashed black;">
                        <b>MOVIMIENTOS DE CAJA:</b><br>
                        Ingresos Extra: +{resumen.get('Ingresos', 0):.2f} €<br>
                        Retiradas/Pagos: -{resumen.get('Retiradas', 0):.2f} €<br>
                        <hr style="border-top: 1px dashed black;">
                        <b>RESULTADO DEL ARQUEO:</b><br>
                        Efectivo Contado: {ult_caja['total_contado']:.2f} €<br>
                        <b>DESCUADRE: {ult_caja['descuadre']:.2f} €</b><br>
                        <hr style="border-top: 1px dashed black;">
                        <div style="text-align: center;">Firma Responsable</div>
                        <br><br><br>
                    </div>
                </body>
                </html>
                """
                components.html(html_cierre_ult, height=550)
        except: pass
        
        with st.form("abrir_caja", border=True):
            st.markdown("<h4 style='margin: 0 0 10px 0;'>🔓 Apertura de Turno</h4>", unsafe_allow_html=True)
            fondo_ini = st.number_input("Fondo Inicial €", min_value=0.0, step=1.0, value=None)
            if st.form_submit_button("ABRIR CAJA AHORA", type="primary", use_container_width=True):
                fondo_val = fondo_ini or 0.0
                client.table("control_caja").insert({"fondo_inicial": float(fondo_val), "estado": "Abierta"}).execute()
                st.success("¡Caja abierta!"); time.sleep(1); st.rerun()
    else:
        id_caja = caja_actual['id']
        fondo_actual = caja_actual['fondo_inicial']
        fecha_ap_str = caja_actual['created_at']
        fecha_ap_visual = pd.to_datetime(fecha_ap_str).strftime('%d/%m/%Y %H:%M')
        
        st.success(f"🔓 **CAJA ABIERTA** | Inicio: {fecha_ap_visual} | Fondo: **{fondo_actual:.2f}€**")
        st.markdown("<div style='margin-top: -30px;'></div>", unsafe_allow_html=True) 
        
        c_tit1, c_tit2 = st.columns([1, 1.2], gap="large")
        with c_tit1: st.markdown("<h4 style='margin: 0 0 5px 0;'>💸 Entradas y Salidas</h4>", unsafe_allow_html=True)
        with c_tit2: st.markdown("<h4 style='margin: 0 0 5px 0;'>⚖️ Arqueo y Cierre</h4>", unsafe_allow_html=True)

        col_izq, col_der = st.columns([1, 1.2], gap="large")
        
        with col_izq:
            with st.form("form_movimientos", clear_on_submit=True, border=True):
                c_tipo, c_cant = st.columns([1, 1])
                with c_tipo: tipo_mov = st.selectbox("Tipo", ["Retirada 🔻", "Ingreso 🔺"])
                with c_cant: cant_mov = st.number_input("Euros €", min_value=0.01, step=1.0, value=None)
                motivo_mov = st.text_input("Motivo", placeholder="Ej: Pago proveedor, cambio...")
                if st.form_submit_button("Registrar Movimiento", use_container_width=True):
                    if motivo_mov and cant_mov is not None:
                        tipo_limpio = "Retirada" if "Retirada" in tipo_mov else "Ingreso"
                        client.table("movimientos_caja").insert({"id_caja": id_caja, "tipo": tipo_limpio, "cantidad": float(cant_mov), "motivo": motivo_mov}).execute()
                        st.rerun()
            
            res_movs = client.table("movimientos_caja").select("*").eq("id_caja", id_caja).execute()
            if res_movs.data:
                df_m = pd.DataFrame(res_movs.data)[['tipo', 'cantidad', 'motivo']]
                df_m['tipo'] = df_m['tipo'].apply(lambda x: '🔻' if x == 'Retirada' else '🔺')
                st.dataframe(df_m, use_container_width=True, hide_index=True, height=150)

        with col_der:
            with st.container(border=True):
                st.markdown("<p style='font-size: 11px; font-weight: bold; color: gray; margin:0;'>💵 BILLETES</p>", unsafe_allow_html=True)
                cb1, cb2, cb3, cb4, cb5, cb6 = st.columns(6)
                with cb1: b200 = st.number_input("200", 0, step=1, key="b200", value=None)
                with cb2: b100 = st.number_input("100", 0, step=1, key="b100", value=None)
                with cb3: b50 = st.number_input("50", 0, step=1, key="b50", value=None)
                with cb4: b20 = st.number_input("20", 0, step=1, key="b20", value=None)
                with cb5: b10 = st.number_input("10", 0, step=1, key="b10", value=None)
                with cb6: b5 = st.number_input("5", 0, step=1, key="b5", value=None)

                st.markdown("<p style='font-size: 11px; font-weight: bold; color: gray; margin:0; padding-top: 5px;'>🪙 MONEDAS</p>", unsafe_allow_html=True)
                cm1, cm2, cm3, cm4, cm5, cm6, cm7, cm8 = st.columns(8)
                with cm1: m2 = st.number_input("2€", 0, step=1, key="m2", value=None)
                with cm2: m1 = st.number_input("1€", 0, step=1, key="m1", value=None)
                with cm3: m50c = st.number_input("50¢", 0, step=1, key="m50c", value=None)
                with cm4: m20c = st.number_input("20¢", 0, step=1, key="m20c", value=None)
                with cm5: m10c = st.number_input("10¢", 0, step=1, key="m10c", value=None)
                with cm6: m5c = st.number_input("5¢", 0, step=1, key="m5c", value=None)
                with cm7: m2c = st.number_input("2¢", 0, step=1, key="m2c", value=None)
                with cm8: m1c = st.number_input("1¢", 0, step=1, key="m1c", value=None)
                
                total_calc = ((b200 or 0)*200) + ((b100 or 0)*100) + ((b50 or 0)*50) + ((b20 or 0)*20) + ((b10 or 0)*10) + ((b5 or 0)*5) + \
                             ((m2 or 0)*2) + ((m1 or 0)*1) + ((m50c or 0)*0.50) + ((m20c or 0)*0.20) + ((m10c or 0)*0.10) + ((m5c or 0)*0.05) + \
                             ((m2c or 0)*0.02) + ((m1c or 0)*0.01)
                st.info(f"**Total Contado: {total_calc:.2f}€**")

            with st.form("form_cierre_final", border=True):
                st.markdown("<p style='margin: 0 0 5px 0; font-weight: bold;'>🔒 Confirmar Cierre</p>", unsafe_allow_html=True)
                
                c_f1, c_f2 = st.columns([1, 1])
                with c_f1: efectivo_final = st.number_input("Efectivo Final Real", min_value=0.0, value=None, placeholder=f"{total_calc:.2f}", label_visibility="collapsed")
                with c_f2: submit_cierre = st.form_submit_button("CERRAR CAJA DEFINITIVA", type="primary", use_container_width=True)
                    
                if submit_cierre:
                    ef_val = efectivo_final if efectivo_final is not None else total_calc
                    ingresos = sum(m['cantidad'] for m in res_movs.data if m['tipo'] == 'Ingreso') if res_movs.data else 0.0
                    retiradas = sum(m['cantidad'] for m in res_movs.data if m['tipo'] == 'Retirada') if res_movs.data else 0.0
                    
                    # --- NUEVO CÁLCULO DE CIERRE (Suma los pagos reales de tus columnas) ---
                    res_ventas = client.table("ventas_historial").select("pago_efectivo, pago_tarjeta, pago_bizum, estado, metodo_pago").gte("created_at", fecha_ap_str).execute()

                    t_efe = 0.0; t_tar = 0.0; t_biz = 0.0
                    t_tar_caixa = 0.0; t_tar_cajasiete = 0.0
                    
                    if res_ventas.data:
                        for v in res_ventas.data:
                            # Solo sumamos el dinero si el ticket no ha sido devuelto
                            if v.get('estado') != 'DEVUELTO':
                                t_efe += float(v.get('pago_efectivo') or 0.0)
                                t_biz += float(v.get('pago_bizum') or 0.0)
                                
                                val_tarjeta = float(v.get('pago_tarjeta') or 0.0)
                                t_tar += val_tarjeta
                                
                                mp = v.get('metodo_pago', '')
                                if 'Caixa' in mp:
                                    t_tar_caixa += val_tarjeta
                                elif 'Caja Siete' in mp:
                                    t_tar_cajasiete += val_tarjeta
                                else:
                                    # Por defecto si hay tarjetas previas sin especificar
                                    t_tar_caixa += val_tarjeta
                    # ----------------------------------------------------------------------
                        
                    efectivo_teorico_en_caja = fondo_actual + t_efe + ingresos - retiradas
                    descuadre = ef_val - efectivo_teorico_en_caja
                    
                    resumen_json = {
                        "Efectivo": round(t_efe, 2), "Tarjeta": round(t_tar, 2), 
                        "Tarjeta Caixa": round(t_tar_caixa, 2), "Tarjeta Caja Siete": round(t_tar_cajasiete, 2),
                        "Bizum": round(t_biz, 2),
                        "Ingresos": round(ingresos, 2), "Retiradas": round(retiradas, 2)
                    }
                    
                    client.table("control_caja").update({
                        "estado": "Cerrada", 
                        "total_contado": float(ef_val), 
                        "descuadre": float(descuadre),
                        "resumen_pagos": resumen_json
                    }).eq("id", id_caja).execute()
                    
                    st.success(f"Caja Cerrada. Descuadre: {descuadre:.2f}€")
                    time.sleep(1.5); st.rerun()

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
        if 'res_p' in locals() and res_p.data:
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
    st.markdown("<h3 style='margin-top: -15px;'> 📑  Gestión Integral de Facturación</h3>", unsafe_allow_html=True)

    sub_emitir, sub_registrar, sub_archivo = st.tabs([
        " 🧾  Emitir Factura (Venta)", 
        " 📥  Registrar Compra (Proveedor)", 
        " 📂  Archivo de Documentos"
    ])
    
    res_inv = client.table("productos").select("*").execute()
    df_inv = pd.DataFrame(res_inv.data) if res_inv.data else pd.DataFrame()
    res_cli = client.table("clientes").select("*").execute()
    df_cli = pd.DataFrame(res_cli.data) if res_cli.data else pd.DataFrame()
    res_prov = client.table("proveedores").select("*").execute()
    df_prov = pd.DataFrame(res_prov.data) if res_prov.data else pd.DataFrame()

    # ==========================================
    # SUB-TAB 1: EMITIR FACTURA DE VENTA (PVP LIMPIO)
    # ==========================================
    with sub_emitir:
        if 'factura_v_temp' not in st.session_state: st.session_state.factura_v_temp = []
        if 'llave_busqueda_v' not in st.session_state: st.session_state.llave_busqueda_v = 0
        
        c_h1, c_h2, c_h3 = st.columns(3)
        with c_h1: f_pago = st.selectbox("Forma de Pago", ["Efectivo", "Tarjeta", "Bizum", "Transferencia"], key="fv_p_sel")
        with c_h2: f_emision = st.date_input("Fecha Emisión", key="fv_f_sel")
        with c_h3: f_vence = st.date_input("Vencimiento", key="fv_v_sel")
        
        with st.expander(" 👤  Seleccionar / Crear Cliente"):
            c_opc = df_cli.apply(lambda x: f"{x['nombre_dueno']} | CIF: {x.get('cif','-')}", axis=1).tolist() if not df_cli.empty else []
            sel_c = st.selectbox("Cliente:", c_opc, index=None, placeholder="Busca un cliente...")
            with st.form("n_cli_rap", clear_on_submit=True):
                nc1, nc2 = st.columns(2); n_n = nc1.text_input("Nombre*"); n_c = nc2.text_input("CIF*")
                if st.form_submit_button("Crear Cliente"):
                    if n_n and n_c: client.table("clientes").insert({"nombre_dueno": n_n, "cif": n_c}).execute(); st.rerun()
        
        st.markdown("####  📦  Añadir Artículos a la Venta")
        if not df_inv.empty:
            opciones_v = df_inv.apply(lambda x: f"{x['nombre']} | SKU: {x['sku']}", axis=1).tolist()
            prod_v = st.selectbox("🔍 Buscar producto en almacén:", opciones_v, index=None, key=f"search_v_alta_{st.session_state.llave_busqueda_v}", placeholder="Escribe para filtrar...")
            
            if prod_v:
                sku_v = prod_v.split(" | SKU: ")[1]
                it_v = df_inv[df_inv['sku'] == sku_v].iloc[0]
                st.session_state.factura_v_temp.append({
                    "id": str(it_v['id']), "Código": it_v['sku'], "Descripción": it_v['nombre'],
                    "Cantidad": 1, "Precio Venta": float(it_v['precio_pvp']), "Desc %": 0.0
                })
                st.session_state.llave_busqueda_v += 1 
                st.rerun()
                
        with st.expander("✨ ¿Artículo manual o nuevo producto?"):
            with st.form("form_nuevo_art_venta", clear_on_submit=True):
                st.markdown("<p style='font-size:13px; color:gray;'>Añade un artículo manual a la factura. Si dejas marcada la casilla, también se guardará permanentemente en el Inventario.</p>", unsafe_allow_html=True)
                col_m1, col_m2 = st.columns(2)
                with col_m1: m_nom = st.text_input("Nombre del Artículo *")
                with col_m2: m_sku = st.text_input("SKU / Ref (Opcional si no se guarda)")
                
                col_m3, col_m4, col_m5 = st.columns(3)
                with col_m3: m_pvp = st.number_input("Precio Venta Público (€) *", min_value=0.0, format="%.2f")
                with col_m4: m_igic = st.selectbox("IGIC %", [7.0, 0.0, 3.0, 15.0])
                with col_m5: m_cant = st.number_input("Cantidad a facturar", min_value=1, value=1)
                
                add_to_stock = st.checkbox("💾 Guardar permanentemente en Inventario", value=True)
                
                if st.form_submit_button("➕ Añadir a la Factura", type="primary", use_container_width=True):
                    if m_nom and m_pvp >= 0:
                        nuevo_id = "0"
                        if add_to_stock:
                            if not m_sku:
                                st.warning("⚠️ Para guardarlo en el inventario necesitas ponerle un SKU / Ref.")
                            else:
                                m_base = m_pvp / (1 + (m_igic / 100))
                                res_new = client.table("productos").insert({
                                    "nombre": m_nom, "sku": m_sku, "precio_base": m_base, "igic_tipo": m_igic, 
                                    "precio_pvp": m_pvp, "categoria": "Producto", "stock_actual": 0, "stock_minimo": 2, "cantidad_reponer": 5
                                }).execute()
                                if res_new.data:
                                    nuevo_id = str(res_new.data[0]['id'])
                        
                        if not add_to_stock or (add_to_stock and m_sku):
                            st.session_state.factura_v_temp.append({
                                "id": str(nuevo_id), "Código": m_sku if m_sku else "---", "Descripción": m_nom,
                                "Cantidad": m_cant, "Precio Venta": m_pvp, "Desc %": 0.0
                            })
                            st.success("Artículo añadido a la factura."); time.sleep(0.5); st.rerun()
                    else:
                        st.error("El nombre y el precio de venta son obligatorios.")
        
        if st.session_state.factura_v_temp:
            # Parche anti-fantasmas
            if 'Precio Venta' not in st.session_state.factura_v_temp[0]:
                st.session_state.factura_v_temp = []; st.rerun()

            df_v = pd.DataFrame(st.session_state.factura_v_temp)
            df_v['Total Línea'] = (df_v['Precio Venta'] * df_v['Cantidad']) * (1 - df_v['Desc %']/100)
            df_v['Total Línea'] = df_v['Total Línea'].round(2)

            df_v_edit = st.data_editor(
                df_v, hide_index=True, use_container_width=True, key="ed_v_final",
                num_rows="dynamic",
                column_config={
                    "id": None, "Código": st.column_config.TextColumn(disabled=True),
                    "Descripción": st.column_config.TextColumn(disabled=True),
                    "Cantidad": st.column_config.NumberColumn("Cant.", min_value=1),
                    "Precio Venta": st.column_config.NumberColumn("Precio Venta (€)", format="%.2f"),
                    "Desc %": st.column_config.NumberColumn("Desc. %", min_value=0.0),
                    "Total Línea": st.column_config.NumberColumn("Total Línea (€)", disabled=True, format="%.2f")
                }
            )

            nuevos_datos_v = df_v_edit[['id', 'Código', 'Descripción', 'Cantidad', 'Precio Venta', 'Desc %']].to_dict('records')
            if nuevos_datos_v != st.session_state.factura_v_temp:
                st.session_state.factura_v_temp = nuevos_datos_v
                st.rerun()

            suma_articulos_v = df_v['Total Línea'].sum()
            st.markdown("---")
            col_v1, col_v2 = st.columns([1, 2])
            with col_v1:
                desc_g_v = st.number_input(" 🎁  Dto. Global (%)", 0.0, 100.0, value=None, key="desc_v_alta")
            
            total_v_final = suma_articulos_v * (1 - (desc_g_v or 0.0) / 100)

            with col_v2:
                st.markdown(f"""
                <div style="background-color: #f0f7f9; padding: 15px; border-radius: 10px; border-left: 5px solid #005275; text-align: right;">
                <p style="margin:0; font-size: 14px;">Suma artículos: {suma_articulos_v:.2f}€</p>
                <h2 style="margin:0; color: #005275;">TOTAL FACTURA: {total_v_final:.2f}€</h2>
                </div>
                """, unsafe_allow_html=True)
            
            if st.button(" 🚀  EMITIR FACTURA", type="primary", use_container_width=True):
                if sel_c:
                    c_id = df_cli[df_cli['nombre_dueno'] == sel_c.split(" | ")[0]].iloc[0]['id']
                    
                    client.table("facturas").insert({
                        "cliente_id": c_id, "total_neto": float(total_v_final), "total_igic": 0.0, "total_final": float(total_v_final),
                        "descuento_global": float(desc_g_v or 0.0), "forma_pago": f_pago, "fecha_vencimiento": str(f_vence), "productos": st.session_state.factura_v_temp
                    }).execute()
                    for i in st.session_state.factura_v_temp:
                        if str(i.get('id', '0')) != '0' and str(i.get('id')) != 'None':
                            res = client.table("productos").select("stock_actual").eq("id", i['id']).execute()
                            if res.data: client.table("productos").update({"stock_actual": res.data[0]['stock_actual'] - i['Cantidad']}).eq("id", i['id']).execute()
                    st.session_state.factura_v_temp = []; st.success("Factura guardada correctamente."); time.sleep(1); st.rerun()
                else:
                    st.error("Debes seleccionar un cliente para emitir la factura.")

    # ==========================================
    # SUB-TAB 2: REGISTRAR COMPRA (PROVEEDOR)
    # ==========================================
    with sub_registrar:
        if 'compra_temp' not in st.session_state: st.session_state.compra_temp = []
        if 'llave_busqueda_c' not in st.session_state: st.session_state.llave_busqueda_c = 0
        if 'pedido_vinculado' not in st.session_state: st.session_state.pedido_vinculado = None
            
        c_c1, c_c2, c_c3 = st.columns(3)
        with c_c1: n_fac = st.text_input("Nº Factura Proveedor", key="fac_prov_n")
        with c_c2: f_fac = st.date_input("Fecha Factura", key="fac_prov_f")
        with c_c3: f_ven = st.date_input("Vencimiento", key="fac_prov_v")
        
        with st.expander(" 🚚  Seleccionar / Crear Proveedor", expanded=True):
            p_opc = df_prov['nombre_empresa'].tolist() if not df_prov.empty else []
            sel_p = st.selectbox("Selecciona el Proveedor:", p_opc, index=None, placeholder="Escribe el nombre del proveedor...")
            with st.form("form_nuevo_proveedor_rapido", clear_on_submit=True):
                np1, np2 = st.columns(2); n_emp_new = np1.text_input("Nombre Empresa*"); n_cif_new = np2.text_input("CIF")
                if st.form_submit_button("➕ Crear Nuevo Proveedor"):
                    if n_emp_new: client.table("proveedores").insert({"nombre_empresa": n_emp_new, "cif": n_cif_new}).execute(); st.rerun()
                        
        st.markdown("---")
        
        with st.expander("📥 Cargar desde Pedido a Proveedor (Automatización)", expanded=False):
            res_pedidos_p = client.table("pedidos_proveedores").select("id, estado, proveedores(nombre_empresa)").in_("estado", ["Borrador", "Enviado"]).execute()
            if res_pedidos_p.data:
                opc_ped = {f"Pedido #{p['id']} - {p['proveedores']['nombre_empresa']} ({p['estado']})": p['id'] for p in res_pedidos_p.data if p.get('proveedores')}
                p_sel_str = st.selectbox("Selecciona un pedido pendiente:", [""] + list(opc_ped.keys()))
                if st.button("⬇️ Cargar Artículos del Pedido"):
                    if p_sel_str:
                        ped_id = opc_ped[p_sel_str]
                        st.session_state.pedido_vinculado = ped_id
                        ped_data = client.table("pedidos_proveedores").select("productos").eq("id", ped_id).execute().data[0]
                        st.session_state.compra_temp = []
                        for art in ped_data.get('productos', []):
                            res_match = client.table("productos").select("id, sku, nombre, precio_base, igic_tipo, precio_pvp").eq("nombre", art['Producto']).execute()
                            if res_match.data:
                                item = res_match.data[0]
                                st.session_state.compra_temp.append({
                                    "id": str(item['id']), "Código": item['sku'], "Descripción": item['nombre'],
                                    "Cantidad": art['Cantidad'], "Base Ud": float(item['precio_base']), "IGIC %": float(item['igic_tipo']), "Desc %": 0.0, "PVP (€)": float(item.get('precio_pvp', 0.0))
                                })
                        st.success("Artículos cargados en la tabla inferior."); time.sleep(1); st.rerun()
            else:
                st.info("No hay pedidos pendientes.")

        st.markdown("####  📦  Añadir Artículos a la Compra")
        
        if not df_inv.empty:
            opciones_inv = df_inv.apply(lambda x: f"{x['nombre']} | SKU: {x['sku']}", axis=1).tolist()
            prod_buscado = st.selectbox("🔍 Buscar producto en almacén:", opciones_inv, index=None, key=f"sel_c_doc_{st.session_state.llave_busqueda_c}", placeholder="Escribe para filtrar...")
            if prod_buscado:
                sku_extraido = prod_buscado.split(" | SKU: ")[1]
                item = df_inv[df_inv['sku'] == sku_extraido].iloc[0]
                st.session_state.compra_temp.append({
                    "id": str(item['id']), "Código": item['sku'], "Descripción": item['nombre'],
                    "Cantidad": 1, "Base Ud": float(item['precio_base']), "IGIC %": float(item['igic_tipo']), "Desc %": 0.0, "PVP (€)": float(item.get('precio_pvp', 0.0))
                })
                st.session_state.llave_busqueda_c += 1; st.rerun()

        with st.expander("✨ ¿Artículo manual o nuevo producto?"):
            with st.form("form_nuevo_art_compra", clear_on_submit=True):
                st.markdown("<p style='font-size:13px; color:gray;'>Añade un artículo manual a la factura. Si dejas marcada la casilla, también se guardará permanentemente en el Inventario.</p>", unsafe_allow_html=True)
                col_m1, col_m2 = st.columns(2)
                with col_m1: m_nom = st.text_input("Nombre del Artículo *")
                with col_m2: m_sku = st.text_input("SKU / Ref (Opcional)")
                
                col_m3, col_m4, col_m5 = st.columns(3)
                with col_m3: m_base = st.number_input("Precio Base Compra (€) *", min_value=0.0, format="%.2f")
                with col_m4: m_igic = st.selectbox("IGIC %", [7.0, 0.0, 3.0, 15.0])
                with col_m5: m_cant = st.number_input("Cantidad a registrar", min_value=1, value=1)
                
                col_m6, col_m7 = st.columns(2)
                with col_m6: m_pvp = st.number_input("PVP Venta Público (€) (Solo si se guarda)", min_value=0.0, format="%.2f")
                with col_m7:
                    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                    add_to_stock = st.checkbox("💾 Guardar permanentemente en Inventario", value=True)
                
                if st.form_submit_button("➕ Añadir a la Compra", type="primary", use_container_width=True):
                    m_base_val = float(m_base or 0.0)
                    m_pvp_val = float(m_pvp or 0.0)
                    
                    if m_nom and m_base_val >= 0:
                        nuevo_id = "0"
                        if add_to_stock:
                            res_new = client.table("productos").insert({
                                "nombre": m_nom, "sku": m_sku if m_sku else "", "precio_base": float(m_base_val), "igic_tipo": float(m_igic), 
                                "precio_pvp": float(m_pvp_val), "categoria": "Producto", "stock_actual": 0, "stock_minimo": 2, "cantidad_reponer": 5
                            }).execute()
                            if res_new.data:
                                nuevo_id = str(res_new.data[0]['id'])
                                if sel_p:
                                    try:
                                        p_id_sel = df_prov[df_prov['nombre_empresa'] == sel_p].iloc[0]['id']
                                        client.table("productos_proveedores").insert({"producto_id": int(nuevo_id), "proveedor_id": p_id_sel, "precio_coste": float(m_base_val)}).execute()
                                    except: pass
                        
                        st.session_state.compra_temp.append({
                            "id": str(nuevo_id), "Código": m_sku if m_sku else "---", "Descripción": m_nom,
                            "Cantidad": m_cant, "Base Ud": float(m_base_val), "IGIC %": float(m_igic), "Desc %": 0.0, "PVP (€)": float(m_pvp_val)
                        })
                        st.success("Artículo añadido a la factura."); time.sleep(0.5); st.rerun()
                    else:
                        st.error("El nombre y el precio base son obligatorios.")

        if st.session_state.compra_temp:
            # Protección por si hay carritos guardados antes de esta actualización
            for x in st.session_state.compra_temp:
                if 'PVP (€)' not in x: x['PVP (€)'] = 0.0
                
            df_c = pd.DataFrame(st.session_state.compra_temp)
            df_c['Coste Ud'] = (df_c['Base Ud'] * (1 + df_c['IGIC %']/100)).round(2)
            df_c['Base Neta'] = (df_c['Base Ud'] * df_c['Cantidad']) * (1 - df_c['Desc %']/100)
            df_c['IGIC €'] = (df_c['Base Neta'] * (df_c['IGIC %']/100)).round(2)
            df_c['Total Línea'] = (df_c['Base Neta'] + df_c['IGIC €']).round(2)
            
            df_c_edit = st.data_editor(
                df_c, hide_index=True, use_container_width=True, num_rows="dynamic",
                column_config={
                    "id": None, "Base Neta": None, "IGIC €": None,
                    "Código": st.column_config.TextColumn(disabled=True),
                    "Descripción": st.column_config.TextColumn(disabled=True),
                    "PVP (€)": st.column_config.NumberColumn("PVP Público (€)", format="%.2f"),
                    "Coste Ud": st.column_config.NumberColumn("Coste Ud c/IGIC", disabled=True),
                    "Total Línea": st.column_config.NumberColumn("Total c/IGIC", disabled=True)
                }
            )
            
            nuevos_datos = df_c_edit[['id', 'Código', 'Descripción', 'Cantidad', 'Base Ud', 'IGIC %', 'Desc %', 'PVP (€)']].to_dict('records')
            if nuevos_datos != st.session_state.compra_temp:
                st.session_state.compra_temp = nuevos_datos; st.rerun()
                
            t_base_c = df_c['Base Neta'].sum()
            t_igic_c = df_c['IGIC €'].sum()
            suma_articulos_c = df_c['Total Línea'].sum()
            desc_pp = st.number_input(" 🎁  Dto. Pronto Pago (%)", 0.0, 100.0, value=None)
            
            desc_pp_val = float(desc_pp or 0.0)
            total_con_pp = suma_articulos_c * (1 - desc_pp_val / 100)
            
            st.markdown(f"""
            <div style="background-color: #fff5f5; padding: 15px; border-radius: 10px; border-left: 5px solid #d32f2f; text-align: right;">
            <p style="margin:0;">Base: {t_base_c * (1-desc_pp_val/100):.2f}€ | IGIC: {t_igic_c * (1-desc_pp_val/100):.2f}€</p>
            <h2 style="margin:0; color: #d32f2f;">TOTAL COMPRA: {total_con_pp:.2f}€</h2>
            </div>
            """, unsafe_allow_html=True)
                
            if st.button(" 📥  ARCHIVAR COMPRA Y SUMAR STOCK", type="primary", use_container_width=True):
                if sel_p and n_fac:
                    p_id = df_prov[df_prov['nombre_empresa'] == sel_p].iloc[0]['id']
                    client.table("compras").insert({
                        "proveedor_id": p_id, "total": float(total_con_pp), "descuento_pp": float(desc_pp or 0.0),
                        "estado": "Recibido", "tipo": f"Factura: {n_fac}", "fecha_vencimiento": str(f_ven),
                        "productos": st.session_state.compra_temp
                    }).execute()
                    for i in st.session_state.compra_temp:
                        if str(i.get('id', '0')) != '0' and str(i.get('id')) != 'None':
                            res_s = client.table("productos").select("stock_actual").eq("id", i['id']).execute()
                            if res_s.data: 
                                # Actualizamos stock, el PRECIO DE COSTE general y el PVP PÚBLICO
                                client.table("productos").update({
                                    "stock_actual": (res_s.data[0]['stock_actual'] or 0) + i['Cantidad'],
                                    "precio_base": float(i['Base Ud']),
                                    "precio_pvp": float(i.get('PVP (€)', 0.0))
                                }).eq("id", i['id']).execute()
                                # Actualizamos el precio de coste del proveedor específico
                                client.table("productos_proveedores").update({"precio_coste": float(i['Base Ud'])}).eq("producto_id", i['id']).eq("proveedor_id", p_id).execute()
                    
                    if st.session_state.pedido_vinculado:
                        client.table("pedidos_proveedores").update({"estado": "Recibido"}).eq("id", st.session_state.pedido_vinculado).execute()
                        st.session_state.pedido_vinculado = None
                        
                    st.session_state.compra_temp = []; st.success("Compra archivada y precios actualizados."); time.sleep(1); st.rerun()

    # ==========================================
    # SUB-TAB 3: ARCHIVO Y GESTIÓN (EDICIÓN Y BORRADO DIRECTO)
    # ==========================================
    with sub_archivo:
        st.markdown("####  🔍  Archivo Histórico")
        tipo_doc = st.radio("Documento:", ["Facturas Emitidas (Ventas)", "Facturas Recibidas (Compras)"], horizontal=True)
        c_f1, c_f2 = st.columns(2)
        f_ini = c_f1.date_input("Desde:", pd.to_datetime('today') - pd.Timedelta(days=30), key="a_i")
        f_fin = c_f2.date_input("Hasta:", pd.to_datetime('today'), key="a_f")

        # --- ARCHIVO DE VENTAS ---
        if "Ventas" in tipo_doc:
            res_fac = client.table("facturas").select("*, clientes(nombre_dueno)").gte("created_at", f"{f_ini}T00:00:00").lte("created_at", f"{f_fin}T23:59:59").order("id", desc=True).execute()
            if res_fac.data:
                df_fac = pd.DataFrame(res_fac.data)
                df_fac['Cliente'] = df_fac['clientes'].apply(lambda x: x['nombre_dueno'] if x else '---')
                df_vista = df_fac[['id', 'numero_factura', 'total_final', 'Cliente', 'forma_pago']].copy()
                
                # 🚨 LEY ANTIFRAUDE (VERI*FACTU): Prohibido borrar facturas emitidas
                df_vista.insert(0, "Borrar", False)
                df_vista.insert(0, "Ver", False)
                
                ed_fac = st.data_editor(
                    df_vista, hide_index=True, use_container_width=True, key="ed_h_f", 
                    column_config={
                        "Ver": st.column_config.CheckboxColumn("👁️ Ver"), 
                        "Borrar": st.column_config.CheckboxColumn("🗑️ Borrar"), 
                        "id": None
                    }
                )
                
                # 1. SISTEMA DE BORRADO DIRECTO DESDE LA TABLA
                filas_borrar_v = ed_fac[ed_fac["Borrar"] == True]
                if not filas_borrar_v.empty:
                    st.error(f"⚠️ Has marcado {len(filas_borrar_v)} factura(s) para eliminar. El stock de los artículos se devolverá automáticamente a la tienda.")
                    if st.button("🚨 CONFIRMAR ELIMINACIÓN DE FACTURA(S)", type="primary", use_container_width=True):
                        for idx, row in filas_borrar_v.iterrows():
                            f_id = row['id']
                            f_data = df_fac[df_fac['id'] == f_id].iloc[0]
                            # Devolver stock
                            for p in f_data.get('productos', []):
                                if str(p.get('id', '0')) != '0' and str(p.get('id')) != 'None':
                                    res_p = client.table("productos").select("stock_actual").eq("id", p['id']).execute()
                                    if res_p.data: client.table("productos").update({"stock_actual": res_p.data[0]['stock_actual'] + p['Cantidad']}).eq("id", p['id']).execute()
                            # Eliminar registro
                            client.table("facturas").delete().eq("id", f_id).execute()
                        st.success("Factura(s) eliminada(s) correctamente."); time.sleep(1); st.rerun()
                
                st.markdown("---")
                
                # 2. SISTEMA DE GUARDADO DE CABECERA (Forma de pago)
                if st.button(" 💾  Guardar Cambios en Forma de Pago"):
                    filas_validas = ed_fac[ed_fac["Borrar"] == False]
                    for idx, row in filas_validas.iterrows():
                        client.table("facturas").update({"forma_pago": str(row['forma_pago'])}).eq("id", row['id']).execute()
                    st.success("Formas de pago actualizadas."); time.sleep(0.5); st.rerun()

                # 3. SISTEMA DE DESGLOSE
                filas = ed_fac[(ed_fac["Ver"] == True) & (ed_fac["Borrar"] == False)]
                if not filas.empty:
                    f_id = filas.iloc[0]['id']
                    f_data = df_fac[df_fac['id'] == f_id].iloc[0]
                    prods = pd.DataFrame(f_data['productos'])
                    if 'Precio Venta' not in prods.columns: prods['Precio Venta'] = (prods.get('Base Ud',0)*(1+prods.get('IGIC %',0)/100)).round(2)
                    prods['Total Línea'] = (prods['Precio Venta']*prods['Cantidad'])*(1-prods.get('Desc %',0)/100)
                    
                    st.markdown(f"#### 📝 Editando Factura {f_data['numero_factura']}")
                    ed_ph = st.data_editor(prods, hide_index=True, use_container_width=True, num_rows="dynamic", key=f"ed_v_{f_id}", column_config={"id": None, "Base Ud": None, "IGIC %": None, "Base Neta": None, "IGIC €": None})
                    
                    new_total = ed_ph['Total Línea'].sum() * (1 - st.number_input("Dto. Global (%)", 0.0, 100.0, float(f_data.get('descuento_global',0)), key=f"dg_{f_id}")/100)
                    st.metric("NUEVO TOTAL FACTURA", f"{new_total:.2f} €")
                    
                    if st.button("💾 SINCRONIZAR CAMBIOS DE ESTA FACTURA"):
                        client.table("facturas").update({"productos": json.loads(ed_ph.to_json(orient='records')), "total_final": float(new_total)}).eq("id", f_id).execute()
                        st.success("Guardado."); st.rerun()

        # --- ARCHIVO DE COMPRAS ---
        else: 
            res_comp = client.table("compras").select("*, proveedores(nombre_empresa)").gte("created_at", f"{f_ini}T00:00:00").lte("created_at", f"{f_fin}T23:59:59").order("id", desc=True).execute()
            if res_comp.data:
                df_comp = pd.DataFrame(res_comp.data)
                df_comp['Proveedor'] = df_comp['proveedores'].apply(lambda x: x['nombre_empresa'] if x else '---')
                df_vista = df_comp[['id', 'tipo', 'total', 'Proveedor', 'estado']].copy()
                
                # Insertamos las dos casillas
                df_vista.insert(0, "Borrar", False)
                df_vista.insert(0, "Ver", False)
                
                ed_comp = st.data_editor(
                    df_vista, hide_index=True, use_container_width=True, key="ed_h_c", 
                    column_config={
                        "Ver": st.column_config.CheckboxColumn("👁️ Ver"), 
                        "Borrar": st.column_config.CheckboxColumn("🗑️ Borrar"),
                        "id": None, "tipo": "Nº Factura"
                    }
                )

                # 1. SISTEMA DE BORRADO DIRECTO DESDE LA TABLA
                filas_borrar_c = ed_comp[ed_comp["Borrar"] == True]
                if not filas_borrar_c.empty:
                    st.error(f"⚠️ Has marcado {len(filas_borrar_c)} compra(s) para eliminar. El stock de estos artículos se restará automáticamente de la tienda.")
                    if st.button("🚨 CONFIRMAR ELIMINACIÓN DE COMPRA(S)", type="primary", use_container_width=True):
                        for idx, row in filas_borrar_c.iterrows():
                            c_id = row['id']
                            c_data = df_comp[df_comp['id'] == c_id].iloc[0]
                            # Restar stock (corrección)
                            for p in c_data.get('productos', []):
                                res_p = client.table("productos").select("stock_actual").eq("id", p['id']).execute()
                                if res_p.data: client.table("productos").update({"stock_actual": res_p.data[0]['stock_actual'] - p['Cantidad']}).eq("id", p['id']).execute()
                            # Eliminar registro
                            client.table("compras").delete().eq("id", c_id).execute()
                        st.success("Compra(s) eliminada(s) correctamente."); time.sleep(1); st.rerun()

                st.markdown("---")

                # 2. SISTEMA DE GUARDADO DE CABECERA (Estado)
                if st.button(" 💾  Guardar Cambios en Estado/Referencia"):
                    filas_validas = ed_comp[ed_comp["Borrar"] == False]
                    for idx, row in filas_validas.iterrows():
                        client.table("compras").update({"estado": str(row['estado']), "tipo": str(row['tipo'])}).eq("id", row['id']).execute()
                    st.success("Cabeceras actualizadas."); time.sleep(0.5); st.rerun()

                # 3. SISTEMA DE DESGLOSE
                filas = ed_comp[(ed_comp["Ver"] == True) & (ed_comp["Borrar"] == False)]
                if not filas.empty:
                    c_id = filas.iloc[0]['id']
                    c_data = df_comp[df_comp['id'] == c_id].iloc[0]
                    prods = pd.DataFrame(c_data['productos'])
                    prods['Total Línea'] = (prods['Base Ud']*prods['Cantidad'])*(1+prods.get('IGIC %',0)/100)
                    
                    st.markdown(f"#### 🛒 Editando Compra {c_data['tipo']}")
                    ed_pc = st.data_editor(prods, hide_index=True, use_container_width=True, num_rows="dynamic", key=f"ed_c_{c_id}", column_config={"id": None})
                    
                    new_total = ed_pc['Total Línea'].sum() * (1 - st.number_input("Dto. Pronto Pago (%)", 0.0, 100.0, float(c_data.get('descuento_pp',0)), key=f"pp_{c_id}")/100)
                    st.metric("NUEVO TOTAL COMPRA", f"{new_total:.2f} €")

                    if st.button("💾 SINCRONIZAR CAMBIOS DE ESTA COMPRA"):
                        client.table("compras").update({"productos": json.loads(ed_pc.to_json(orient='records')), "total": float(new_total)}).eq("id", c_id).execute()
                        st.success("Compra actualizada."); st.rerun()

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
