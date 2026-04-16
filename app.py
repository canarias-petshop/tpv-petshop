import streamlit as st
import pandas as pd
from postgrest import SyncPostgrestClient
from datetime import datetime
import time

# --- 1. CONFIGURACIÓN DE DISEÑO PROFESIONAL Y COMPACTO ---
st.set_page_config(page_title="Animalarium TPV", layout="wide")

st.markdown("""
    <style>
        /* Ajuste de márgenes superiores para evitar cortes */
        .block-container { padding-top: 1.5rem !important; padding-bottom: 0rem !important; }
        
        /* Reducir espacio entre todos los elementos (interlineado) */
        .element-container, .stVerticalBlock { gap: 0.3rem !important; margin-bottom: 0.1rem !important; }
        
        /* Títulos más pequeños y juntos */
        h1 { font-size: 1.4rem !important; margin-bottom: 0px !important; padding-bottom: 0px !important; }
        h3 { font-size: 1.1rem !important; margin-top: 0px !important; margin-bottom: 2px !important; }
        
        /* Hacer los buscadores más cortos y estéticos */
        .stSelectbox, .stTextInput, .stNumberInput { max-width: 90% !important; }
        
        /* Ajuste de las pestañas */
        .stTabs [data-baseweb="tab-list"] { gap: 5px; }
        .stTabs [data-baseweb="tab"] { height: 35px; padding-top: 5px; font-size: 14px; }
        
        /* Alineación de avisos (el cuadro azul) */
        .stAlert { padding: 0.5rem !important; margin-top: 0px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MEMORIA DE LA SESIÓN ---
if 'carrito' not in st.session_state: st.session_state['carrito'] = []
if 'acceso_concedido' not in st.session_state: st.session_state.acceso_concedido = False
if 'ticket_html' not in st.session_state: st.session_state['ticket_html'] = None

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
    client = SyncPostgrestClient(
        f"{st.secrets['url']}/rest/v1", 
        headers={"apikey": st.secrets['key'], "Authorization": f"Bearer {st.secrets['key']}"}
    )
except:
    st.error("Error de conexión"); st.stop()

# --- 5. CABECERA ---
# Usamos un contenedor con alineación para que no se corte arriba
header_col1, header_col2 = st.columns([0.1, 0.9], vertical_alignment="center")
with header_col1:
    try: st.image("LOGO.jpg", width=45) 
    except: st.write("🐾")
with header_col2:
    st.markdown("<h1>Animalarium - TPV</h1>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📦 Inventario", "🛒 Caja/Ventas", "👥 Clientes", "📜 Historial"])

# --- TAB 1: PRODUCTOS ---
with tab1:
    col_f, col_t = st.columns([1.2, 2.5])
    with col_f:
        st.markdown("### 📝 Nuevo Producto")
        with st.form("nuevo_p", clear_on_submit=True):
            nombre = st.text_input("Nombre")
            c1, c2 = st.columns(2)
            with c1: cod = st.text_input("Código")
            with c2: cat = st.selectbox("Cat.", ["Alimentación", "Higiene", "Accesorios", "Servicios"])
            
            c3, c4 = st.columns(2)
            with c3: p_compra = st.number_input("Coste Neto", min_value=0.0)
            with c4: igic_tipo = st.selectbox("IGIC %", [7, 0, 3, 15])
            
            c5, c6 = st.columns(2)
            with c5: pvp = st.number_input("PVP Final", min_value=0.0)
            with c6: stck = st.number_input("Stock", min_value=0)
            
            if st.form_submit_button("Guardar", use_container_width=True):
                client.table("productos_y_servicios").insert({
                    "nombre": nombre, "codigo_barras": cod, "categoria": cat,
                    "precio_compra": p_compra, "tipo_igic": igic_tipo, "precio_pvp": pvp, "stock_actual": stck
                }).execute()
                st.success("Añadido"); st.rerun()
    with col_t:
        st.markdown("### 📦 Stock")
        res = client.table("productos_y_servicios").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            st.dataframe(df[['codigo_barras', 'nombre', 'precio_pvp', 'stock_actual']], use_container_width=True, height=380, hide_index=True)

# --- TAB 2: CAJA Y VENTAS (ALINEACIÓN Y COMPACIDAD MÁXIMA) ---
with tab2:
    # Definimos columnas con un gap (espacio) pequeño
    col_busqueda, col_carrito = st.columns([1, 1], gap="small")
    
    with col_busqueda:
        st.markdown("<h3>🛒 Terminal de Venta</h3>", unsafe_allow_html=True)
        
        res_inv = client.table("productos_y_servicios").select("*").execute()
        df_inv = pd.DataFrame(res_inv.data) if res_inv.data else pd.DataFrame()
        
        # 1. BUSCADOR
        st.markdown("<p style='font-weight:bold; font-size:13px; margin:0;'>🔍 Buscar por Nombre</p>", unsafe_allow_html=True)
        if not df_inv.empty:
            opciones = df_inv.apply(lambda x: f"{x['nombre']} | {x['precio_pvp']}€", axis=1).tolist()
            prod_sel = st.selectbox("b", opciones, index=None, placeholder="Escribir...", label_visibility="collapsed", key="sb_n")
            
            if prod_sel:
                # Lógica de extracción de nombre y stock
                nombre_sel = prod_sel.split(" | ")[0]
                fila_p = df_inv[df_inv['nombre'] == nombre_sel].iloc[0]
                st.markdown(f"<p style='margin:0; font-size:10px; color:green;'>Stock: {fila_p['stock_actual']}</p>", unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                with c1: cant = st.number_input("c", min_value=1, value=1, label_visibility="collapsed", key="cant_b")
                with c2: 
                    if st.button("➕ Añadir", use_container_width=True, type="primary"):
                        st.session_state.carrito.append({
                            "Producto": fila_p['nombre'], "Cantidad": cant, "Precio": fila_p['precio_pvp'],
                            "Subtotal": cant * float(fila_p['precio_pvp']), "IGIC": fila_p.get('tipo_igic', 7), "Manual": False
                        })
                        st.rerun()

        st.markdown("<hr style='margin: 4px 0px; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

        # 2. PISTOLA
        st.markdown("<p style='font-weight:bold; font-size:13px; margin:0;'>📇 Escáner de Pistola</p>", unsafe_allow_html=True)
        c_cod, c_cant2 = st.columns([2, 1])
        with c_cant2: cant_p = st.number_input("p", min_value=1, value=1, label_visibility="collapsed", key="cant_p")
        with c_cod: 
            cod_leido = st.text_input("k", placeholder="Pistola...", label_visibility="collapsed", key="input_pistola")
        
        # (Lógica de la pistola igual...)

        st.markdown("<hr style='margin: 4px 0px; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

        # 3. MANUAL
        st.markdown("<p style='font-weight:bold; font-size:13px; margin:0;'>✍️ Artículo Manual</p>", unsafe_allow_html=True)
        with st.form("f_man", clear_on_submit=True, border=False):
            m_nom = st.text_input("n", placeholder="Nombre artículo...", label_visibility="collapsed")
            c_m1, c_m2 = st.columns([2, 1])
            with c_m1: m_pre = st.number_input("€", min_value=0.0, step=0.1)
            with c_m2: m_can = st.number_input("q", min_value=1, value=1)
            st.form_submit_button("➕ Añadir", use_container_width=True)

    # --- COLUMNA DERECHA: CARRITO (SINCRONIZADA) ---
    with col_carrito:
        # Título a la misma altura
        st.markdown("<h3>🛒 Tu Carrito</h3>", unsafe_allow_html=True)
        
        # El espacio antes del carrito se iguala con el buscador
        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
        
        if st.session_state.carrito:
            df_car = pd.DataFrame(st.session_state.carrito)
            st.dataframe(df_car[['Cantidad', 'Producto', 'Subtotal']], use_container_width=True, hide_index=True, height=120)
            
            total_v = sum(item['Subtotal'] for item in st.session_state.carrito)
            st.markdown(f"<p style='text-align: right; font-weight:bold; font-size:18px; margin:0;'>Total: {total_v:.2f}€</p>", unsafe_allow_html=True)
            
            # Zona de cobro compacta
            st.radio("p", ["Efectivo", "Tarjeta", "Bizum"], horizontal=True, label_visibility="collapsed")
            c_cob, c_vac = st.columns([2, 1])
            with c_cob: st.button("🧧 FINALIZAR", use_container_width=True, type="primary")
            with c_vac: st.button("🗑️ Vaciar", use_container_width=True)
        else:
            # Este es el cuadro azul (st.info) que ahora estará alineado con el primer buscador
            st.info("El carrito está vacío. Selecciona productos a la izquierda.")
            
# --- TAB 4: HISTORIAL Y DEVOLUCIONES (VERSIÓN CORREGIDA) ---
with tab4:
    st.markdown("<h3 style='margin-top: -15px; margin-bottom: 5px;'>📜 Historial</h3>", unsafe_allow_html=True)
    
    res_v = client.table("ventas_historial").select("*").execute()
    
    if res_v.data:
        df_v = pd.DataFrame(res_v.data)
        if not df_v.empty:
            df_v = df_v.sort_values(by="id", ascending=False)
            
            # Limpieza de datos para evitar errores visuales
            try: df_v['Fecha'] = pd.to_datetime(df_v['created_at']).dt.strftime('%d/%m/%Y %H:%M')
            except: df_v['Fecha'] = "---"
            
            for col in ['metodo_pago', 'estado', 'total']:
                if col not in df_v.columns: df_v[col] = "N/A"

            df_vista = df_v[['id', 'Fecha', 'total', 'metodo_pago', 'estado']].copy()
            df_vista.columns = ['Nº', 'Fecha', 'Total (€)', 'Método', 'Estado']
            
            evento = st.dataframe(
                df_vista, use_container_width=True, hide_index=True, height=170,
                on_select="rerun", selection_mode="single-row"
            )
            
            if len(evento.selection.rows) > 0:
                fila_idx = evento.selection.rows[0]
                id_t = int(df_vista.iloc[fila_idx]['Nº'])
                ticket = df_v[df_v['id'] == id_t].iloc[0]
                
                st.markdown(f"**🔍 Detalle Ticket #{id_t}**")
                
                prods = ticket.get('productos', [])
                if prods:
                    st.dataframe(pd.DataFrame(prods)[['Producto', 'Cantidad', 'Subtotal']], 
                                 use_container_width=True, hide_index=True, height=110)

                # --- LÓGICA DE CONTROL DE BOTONES ---
                # Forzamos la limpieza del texto del estado
                estado_raw = str(ticket.get('estado', 'Completado')).upper().strip()

                st.markdown("<hr style='margin: 5px 0px;'>", unsafe_allow_html=True)
                
                # Fila 1: Controles y Estado
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    # Si NO está devuelto, permitimos elegir método de reembolso
                    if "DEVUELTO" not in estado_raw:
                        m_dev = st.radio("Reembolso:", ["Efectivo", "Tarjeta", "Bizum"], horizontal=True, key=f"rd_{id_t}", label_visibility="collapsed")
                    else:
                        st.error("TICKET YA DEVUELTO")
                with col_c2:
                    confirmar = st.checkbox("Confirmar borrar registro", key=f"chk_{id_t}")

                # Fila 2: Botones de Acción
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    # El botón de Devolución aparece si el estado NO es devuelto
                    if "DEVUELTO" not in estado_raw:
                        if st.button("🔄 PROCESAR DEVOLUCIÓN", use_container_width=True):
                            # IMPORTANTE: Aquí también sumamos el stock al devolver
                            if prods:
                                for p in prods:
                                    res_p = client.table("productos_y_servicios").select("stock_actual").eq("nombre", p['Producto']).execute()
                                    if res_p.data:
                                        n_stock = res_p.data[0]['stock_actual'] + p['Cantidad']
                                        client.table("productos_y_servicios").update({"stock_actual": n_stock}).eq("nombre", p['Producto']).execute()
                            
                            client.table("ventas_historial").update({"estado": "DEVUELTO"}).eq("id", id_t).execute()
                            st.success("Devolución realizada y stock restaurado")
                            time.sleep(1); st.rerun()
                
                with col_b2:
                    # Botón de Anular SIEMPRE disponible si marcas el check
                    if st.button("🔥 ANULAR Y BORRAR TODO", use_container_width=True, disabled=not confirmar):
                        if prods:
                            for p in prods:
                                res_p = client.table("productos_y_servicios").select("stock_actual").eq("nombre", p['Producto']).execute()
                                if res_p.data:
                                    n_stock = res_p.data[0]['stock_actual'] + p['Cantidad']
                                    client.table("productos_y_servicios").update({"stock_actual": n_stock}).eq("nombre", p['Producto']).execute()
                        
                        client.table("ventas_historial").delete().eq("id", id_t).execute()
                        st.success("Ticket eliminado y stock restaurado")
                        time.sleep(1); st.rerun()
        else: st.write("Historial vacío.")
    else: st.error("Error de conexión.")