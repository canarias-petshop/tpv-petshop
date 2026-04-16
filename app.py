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

# --- TAB 2: CAJA ---
with tab2:
    col_caja1, col_caja2 = st.columns([1, 1])
    with col_caja1:
        st.markdown("### 🛒 Carrito")
        # Aquí iría tu buscador para añadir productos...
        if st.session_state.carrito:
            df_car = pd.DataFrame(st.session_state.carrito)
            st.table(df_car)
            total_v = sum(item['Subtotal'] for item in st.session_state.carrito)
            metodo = st.radio("Pago:", ["Efectivo", "Tarjeta"], horizontal=True)
            
            if st.button("🧧 COBRAR Y GENERAR TICKET", use_container_width=True):
                base = sum(i['Subtotal']/(1+(i.get('IGIC',7)/100)) for i in st.session_state.carrito)
                # GUARDAR EN VENTAS_HISTORIAL
                client.table("ventas_historial").insert({
                    "total": total_v, "metodo_pago": metodo, "productos": st.session_state.carrito, "estado": "Completado"
                }).execute()
                
                # Ticket HTML con tus datos
                ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
                st.session_state.ticket_html = f"""
                <div style="font-family:monospace; width:270px; margin:auto; padding:10px; border:1px solid #ccc; background:white; color:black;">
                    <center><b>ANIMALARIUM</b><br>Raquel Trujillo Hernández<br>78854854K<br>C/ José Hernández 26, Local dcho.<br>{ahora}</center>
                    <hr>
                    {"".join([f"<div>{i['Cantidad']}x {i['Producto'][:15]}... {i['Subtotal']:.2f}€</div>" for i in st.session_state.carrito])}
                    <hr>
                    <b>TOTAL: {total_v:.2f}€</b><br>
                    <small>Base: {base:.2f}€ | IGIC Inc. | Pago: {metodo}</small>
                    <hr>
                    <center><small>30 días para cambios/devoluciones.<br>¡Gracias! 🐾</small></center>
                </div>"""
                st.session_state.carrito = []
                st.success("Cobrado"); st.rerun()

    if st.session_state.ticket_html:
        st.markdown(st.session_state.ticket_html, unsafe_allow_html=True)
        if st.button("Cerrar Ticket"): st.session_state.ticket_html = None; st.rerun()

# --- TAB 4: HISTORIAL COMPACTO Y SEGURO ---
with tab4:
    st.markdown("<h3 style='margin-top: -15px; margin-bottom: 5px;'>📜 Historial</h3>", unsafe_allow_html=True)
    
    res_v = client.table("ventas_historial").select("*").execute()
    
    if res_v.data:
        df_v = pd.DataFrame(res_v.data)
        if not df_v.empty:
            df_v = df_v.sort_values(by="id", ascending=False)
            
            # Formatear fecha y asegurar columnas
            try: df_v['Fecha'] = pd.to_datetime(df_v['created_at']).dt.strftime('%d/%m/%Y %H:%M')
            except: df_v['Fecha'] = "---"
            
            for col in ['metodo_pago', 'estado', 'total']:
                if col not in df_v.columns: df_v[col] = "N/A"

            df_vista = df_v[['id', 'Fecha', 'total', 'metodo_pago', 'estado']].copy()
            df_vista.columns = ['Nº', 'Fecha', 'Total (€)', 'Método', 'Estado']
            
            # Tabla principal compacta
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

                # --- LÓGICA DE CONTROL (FIJADA) ---
                # Convertimos a minúsculas para que no falle por la mayúscula
                estado_actual = str(ticket.get('estado', '')).lower().strip()

                st.markdown("<hr style='margin: 5px 0px;'>", unsafe_allow_html=True)
                
                # Fila 1: Controles
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    if estado_actual == "completado":
                        m_dev = st.radio("Reembolso:", ["Efectivo", "Tarjeta"], horizontal=True, key=f"rd_{id_t}", label_visibility="collapsed")
                    else:
                        st.write(f"Estado: **{estado_actual.upper()}**")
                with col_c2:
                    confirmar = st.checkbox("Confirmar borrar", key=f"chk_{id_t}")

                # Fila 2: Botones
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    # Solo permitimos devolución si está completado
                    if estado_actual == "completado":
                        if st.button("🔄 DEVOLUCIÓN", use_container_width=True):
                            client.table("ventas_historial").update({"estado": "DEVUELTO"}).eq("id", id_t).execute()
                            st.rerun()
                with col_b2:
                    # El botón de BORRAR siempre disponible si confirmas
                    if st.button("🔥 ANULAR TICKET", use_container_width=True, disabled=not confirmar):
                        if prods:
                            for p in prods:
                                res_p = client.table("productos_y_servicios").select("stock_actual").eq("nombre", p['Producto']).execute()
                                if res_p.data:
                                    n_stock = res_p.data[0]['stock_actual'] + p['Cantidad']
                                    client.table("productos_y_servicios").update({"stock_actual": n_stock}).eq("nombre", p['Producto']).execute()
                        client.table("ventas_historial").delete().eq("id", id_t).execute()
                        st.success("Anulado")
                        time.sleep(1); st.rerun()
        else: st.write("Historial vacío.")
    else: st.error("Error de conexión.")