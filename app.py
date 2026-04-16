import streamlit as st
import pandas as pd
from postgrest import SyncPostgrestClient
from datetime import datetime
import time

# --- 1. CONFIGURACIÓN DE PÁGINA (SEGURA) ---
st.set_page_config(page_title="Animalarium TPV", layout="wide")

# CSS Suave: Solo quitamos el exceso de arriba sin romper la app
st.markdown("""
    <style>
        .block-container { padding-top: 2.5rem !important; padding-bottom: 0rem !important; }
        .stSelectbox, .stTextInput, .stNumberInput { max-width: 95% !important; }
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

# --- 5. CABECERA (NATURAL, SIN CORTES) ---
c_logo, c_titulo = st.columns([0.8, 8], vertical_alignment="center")
with c_logo:
    try: st.image("LOGO.jpg", width=60) # Logo restaurado
    except: st.write("🐾")
with c_titulo:
    st.title("Animalarium - TPV")

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

# --- TAB 2: CAJA Y VENTAS (LIMPIA Y ALINEADA) ---
with tab2:
    # Usamos gap="medium" para no agobiar visualmente la pantalla
    col_busqueda, col_carrito = st.columns([1.2, 1], gap="medium")
    
    with col_busqueda:
        # Título principal de la columna izquierda
        st.markdown("### 🛒 Terminal de Venta")
        
        res_inv = client.table("productos_y_servicios").select("*").execute()
        df_inv = pd.DataFrame(res_inv.data) if res_inv.data else pd.DataFrame()
        
        # 1. BUSCADOR
        st.markdown("**🔍 Buscar por Nombre**")
        if not df_inv.empty:
            opciones = df_inv.apply(lambda x: f"{x['nombre']} | {x['precio_pvp']}€", axis=1).tolist()
            prod_sel = st.selectbox("Busca el producto", opciones, index=None, placeholder="Escribe el nombre del producto...", label_visibility="collapsed")
            
            if prod_sel:
                nombre_sel = prod_sel.split(" | ")[0]
                fila_p = df_inv[df_inv['nombre'] == nombre_sel].iloc[0]
                
                # Aviso de stock
                st.caption(f"📦 Stock disponible: **{fila_p['stock_actual']}**")
                
                c1, c2 = st.columns(2)
                with c1: cant = st.number_input("Cantidad_b", min_value=1, value=1, label_visibility="collapsed", key="cant_b")
                with c2: 
                    if st.button("➕ Añadir al carro", use_container_width=True, type="primary", key="btn_b"):
                        st.session_state.carrito.append({
                            "Producto": fila_p['nombre'], "Cantidad": cant, "Precio": fila_p['precio_pvp'],
                            "Subtotal": cant * float(fila_p['precio_pvp']), "IGIC": fila_p.get('tipo_igic', 7), "Manual": False
                        })
                        st.rerun()
        else: st.info("Inventario vacío.")

        st.divider() # Línea separadora segura nativa

        # 2. PISTOLA
        st.markdown("**📇 Escáner de Pistola**")
        if 'limpiar_codigo' in st.session_state and st.session_state.limpiar_codigo:
            st.session_state.input_pistola = ""
            st.session_state.limpiar_codigo = False

        c_cod, c_cant2 = st.columns([2, 1])
        with c_cant2: cant_p = st.number_input("Cantidad_p", min_value=1, value=1, label_visibility="collapsed", key="cant_p")
        with c_cod: cod_leido = st.text_input("Codigo_p", placeholder="Haz clic aquí y pasa la pistola...", label_visibility="collapsed", key="input_pistola")
        
        if cod_leido and not df_inv.empty:
            coincid = df_inv[df_inv['codigo_barras'] == cod_leido]
            if not coincid.empty:
                fila_pist = coincid.iloc[0]
                st.session_state.carrito.append({
                    "Producto": fila_pist['nombre'], "Cantidad": cant_p, "Precio": fila_pist['precio_pvp'],
                    "Subtotal": cant_p * float(fila_pist['precio_pvp']), "IGIC": fila_pist.get('tipo_igic', 7), "Manual": False
                })
                st.session_state.limpiar_codigo = True
                st.rerun()
            else: 
                st.error("⚠️ Código no encontrado.")
                st.session_state.limpiar_codigo = True
                time.sleep(1); st.rerun()

        st.divider()

        # 3. MANUAL
        st.markdown("**✍️ Artículo Manual Suelto**")
        with st.form("f_man", clear_on_submit=True, border=False):
            m_nom = st.text_input("Concepto", placeholder="Nombre del artículo suelto...", label_visibility="collapsed")
            c_m1, c_m2 = st.columns([2, 1])
            with c_m1: m_pre = st.number_input("Precio final €", min_value=0.0, step=0.1)
            with c_m2: m_can = st.number_input("Cantidad_m", min_value=1, value=1, label_visibility="collapsed")
            
            if st.form_submit_button("➕ Añadir manual", use_container_width=True):
                if m_nom and m_pre > 0:
                    st.session_state.carrito.append({
                        "Producto": m_nom, "Cantidad": m_can, "Precio": m_pre,
                        "Subtotal": m_can * float(m_pre), "IGIC": 0, "Manual": True
                    })
                    st.rerun()
                else: st.error("Faltan datos o el precio es 0.")

    # --- COLUMNA DERECHA: CARRITO ---
    with col_carrito:
        # Usamos el MISMO tamaño de título (###) que en la izquierda para que se alineen solos
        st.markdown("### 🛒 Tu Carrito")
        
        # Para que el cuadro de "vacío" o la tabla empiecen donde el buscador, ponemos un título vacío
        st.markdown("**Resumen de compra**")
        
        if st.session_state.carrito:
            df_car = pd.DataFrame(st.session_state.carrito)
            # Altura ajustada a 150px
            st.dataframe(df_car[['Cantidad', 'Producto', 'Subtotal']], use_container_width=True, hide_index=True, height=150)
            
            total_v = sum(item['Subtotal'] for item in st.session_state.carrito)
            st.markdown(f"### Total a pagar: {total_v:.2f}€", unsafe_allow_html=True)
            
            st.divider()
            
            # Zona de cobro
            metodo = st.radio("Pago:", ["Efectivo", "Tarjeta", "Bizum"], horizontal=True, label_visibility="collapsed")
            c_cob, c_vac = st.columns([2, 1])
            with c_cob: 
                if st.button("🧧 FINALIZAR", use_container_width=True, type="primary"):
                    # (Aquí va tu código de guardar en Supabase, restar stock y hacer el ticket HTML que ya tenías)
                    pass
            with c_vac: 
                if st.button("🗑️ Vaciar", use_container_width=True):
                    st.session_state.carrito = []; st.rerun()
        else:
            st.info("El carrito está vacío. Empieza a añadir productos desde la izquierda.")
            
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