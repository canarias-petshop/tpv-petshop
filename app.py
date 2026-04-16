import streamlit as st
import pandas as pd
from postgrest import SyncPostgrestClient
from datetime import datetime
import time

# --- 1. CONFIGURACIÓN DE PÁGINA Y DISEÑO ---
st.set_page_config(page_title="Animalarium TPV", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 3.5rem !important; padding-bottom: 0rem !important; }
        h1 { font-size: 1.8rem !important; margin: 0px !important; }
        h3 { font-size: 1.1rem !important; margin-top: 5px !important; }
        .stButton>button { border-radius: 5px; }
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
c_logo, c_titulo = st.columns([0.8, 8], vertical_alignment="center")
with c_logo:
    try: st.image("LOGO.jpg", width=70)
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

# --- TAB 2: CAJA Y VENTAS (ALINEADO Y ULTRA-COMPACTO) ---
with tab2:
    # Subimos el título general para aprovechar el espacio en blanco de arriba
    st.markdown("<h3 style='margin-top: -25px; margin-bottom: 10px;'>🛒 Terminal de Venta</h3>", unsafe_allow_html=True)
    
    col_busqueda, col_carrito = st.columns([1.2, 1])
    
    # --- COLUMNA IZQUIERDA: BÚSQUEDA ---
    with col_busqueda:
        res_inv = client.table("productos_y_servicios").select("*").execute()
        df_inv = pd.DataFrame(res_inv.data) if res_inv.data else pd.DataFrame()
        
        # 1. BUSCADOR POR NOMBRE
        st.markdown("**🔍 Buscar por Nombre**") # Este título alinea con el del carrito
        if not df_inv.empty:
            opciones = df_inv.apply(lambda x: f"{x['nombre']} | Cod: {x['codigo_barras']} | {x['precio_pvp']}€", axis=1).tolist()
            prod_sel = st.selectbox("Buscar:", opciones, index=None, placeholder="Escribe para buscar...", label_visibility="collapsed", key="sb_n")
            
            if prod_sel:
                cod_sel = prod_sel.split(" | Cod: ")[1].split(" | ")[0]
                fila_p = df_inv[df_inv['codigo_barras'] == cod_sel].iloc[0]
                
                st.markdown(f"<p style='margin:0; font-size:12px; color:{'green' if fila_p['stock_actual']>0 else 'red'};'>Stock: {fila_p['stock_actual']}</p>", unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                with c1: cant = st.number_input("Cant.", min_value=1, value=1, label_visibility="collapsed", key="cant_b")
                with c2: 
                    if st.button("➕ Añadir", use_container_width=True, type="primary", key="btn_b"):
                        st.session_state.carrito.append({
                            "Producto": fila_p['nombre'], "Cantidad": cant, "Precio": fila_p['precio_pvp'],
                            "Subtotal": cant * float(fila_p['precio_pvp']), "IGIC": fila_p.get('tipo_igic', 7), "Manual": False
                        })
                        st.rerun()
        else: st.info("Inventario vacío.")

        st.markdown("<hr style='margin: 8px 0px; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

        # 2. CÓDIGO DE BARRAS
        st.markdown("**📇 Escáner de Pistola**")
        if 'limpiar_codigo' in st.session_state and st.session_state.limpiar_codigo:
            st.session_state.input_pistola = ""
            st.session_state.limpiar_codigo = False

        c_cod, c_cant2 = st.columns([2, 1])
        with c_cant2: cant_p = st.number_input("Cant.", min_value=1, value=1, label_visibility="collapsed", key="cant_p")
        with c_cod: cod_leido = st.text_input("Código", placeholder="Pistola aquí...", label_visibility="collapsed", key="input_pistola")
        
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
                st.error("No existe.")
                st.session_state.limpiar_codigo = True
                time.sleep(1); st.rerun()

        st.markdown("<hr style='margin: 8px 0px; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

        # 3. ARTÍCULO MANUAL (SIN IGIC)
        st.markdown("**✍️ Artículo Manual Suelto**")
        with st.form("f_man", clear_on_submit=True, border=False):
            m_nom = st.text_input("Concepto", placeholder="Ej: Correa suelta", label_visibility="collapsed")
            # Ahora solo 2 columnas porque hemos quitado el IGIC
            c_m1, c_m2 = st.columns([2, 1])
            with c_m1: m_pre = st.number_input("Precio final €", min_value=0.0, step=0.1)
            with c_m2: m_can = st.number_input("Cantidad", min_value=1, value=1)
            
            if st.form_submit_button("➕ Añadir Manual", use_container_width=True):
                if m_nom and m_pre > 0:
                    st.session_state.carrito.append({
                        "Producto": m_nom, "Cantidad": m_can, "Precio": m_pre,
                        "Subtotal": m_can * float(m_pre), 
                        "IGIC": 0, # IGIC a cero por defecto como pediste
                        "Manual": True
                    })
                    st.rerun()
                else: st.error("Faltan datos.")

    # --- COLUMNA DERECHA: CARRITO Y COBRO ---
    with col_carrito:
        # Añadido este título para que alinee a la perfección con el de la izquierda
        st.markdown("**🛒 Tu Carrito**") 
        
        if st.session_state.carrito:
            df_car = pd.DataFrame(st.session_state.carrito)
            # Altura reducida a 150 para evitar empujar la pantalla
            st.dataframe(df_car[['Cantidad', 'Producto', 'Subtotal']], use_container_width=True, hide_index=True, height=150)
            
            total_v = sum(item['Subtotal'] for item in st.session_state.carrito)
            st.markdown(f"<h3 style='text-align: right; margin-top: -10px; margin-bottom: 5px;'>Total: {total_v:.2f}€</h3>", unsafe_allow_html=True)
            
            st.markdown("<hr style='margin: 0px 0px 5px 0px;'>", unsafe_allow_html=True)
            metodo = st.radio("Pago:", ["Efectivo", "Tarjeta", "Bizum"], horizontal=True, label_visibility="collapsed")
            
            c_cobrar, c_vaciar = st.columns([2, 1])
            with c_cobrar:
                if st.button("🧧 FINALIZAR VENTA", use_container_width=True, type="primary"):
                    with st.spinner("💳"):
                        base = sum(i['Subtotal']/(1+(i.get('IGIC',7)/100)) for i in st.session_state.carrito)
                        client.table("ventas_historial").insert({
                            "total": total_v, "metodo_pago": metodo, "productos": st.session_state.carrito, "estado": "Completado"
                        }).execute()
                        
                        for i in st.session_state.carrito:
                            if not i.get('Manual', False):
                                res_s = client.table("productos_y_servicios").select("stock_actual").eq("nombre", i['Producto']).execute()
                                if res_s.data:
                                    n_stock = res_s.data[0]['stock_actual'] - i['Cantidad']
                                    client.table("productos_y_servicios").update({"stock_actual": n_stock}).eq("nombre", i['Producto']).execute()
                        
                        ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
                        st.session_state.ticket_html = f"""
                        <div style="font-family:monospace; width:260px; margin:auto; padding:10px; border:1px solid #ccc; background:white; color:black;">
                            <center><b>ANIMALARIUM</b><br>Raquel Trujillo Hernández<br>78854854K<br>C/ José Hernández 26, Local dcho.<br>{ahora}</center>
                            <hr style="border-top: 1px dashed black;">
                            {"".join([f"<div style='display:flex; justify-content:space-between;'><span style='font-size:11px;'>{i['Cantidad']}x {i['Producto'][:15]}</span> <span style='font-size:11px;'>{i['Subtotal']:.2f}€</span></div>" for i in st.session_state.carrito])}
                            <hr style="border-top: 1px dashed black;">
                            <div style='display:flex; justify-content:space-between; font-weight:bold;'><span>TOTAL:</span> <span>{total_v:.2f}€</span></div>
                            <div style='font-size:10px; margin-top:5px;'>Base: {base:.2f}€ | Pago: {metodo}</div>
                            <hr style="border-top: 1px dashed black;">
                            <center><small>30 días para cambios/devoluciones.<br>¡Gracias por su visita! 🐾</small></center>
                        </div>"""
                        st.session_state.carrito = [] 
                        st.rerun()
            with c_vaciar:
                if st.button("🗑️ Vaciar", use_container_width=True):
                    st.session_state.carrito = []; st.rerun()
        else:
            st.info("🛒 El carrito está vacío.")

    # --- TICKET EMERGENTE ---
    if st.session_state.ticket_html:
        st.markdown(st.session_state.ticket_html, unsafe_allow_html=True)
        if st.button("Cerrar Ticket", use_container_width=True):
            st.session_state.ticket_html = None; st.rerun()

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