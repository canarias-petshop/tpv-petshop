import streamlit as st
import pandas as pd
from postgrest import SyncPostgrestClient
from datetime import datetime
import time

# --- 1. CONFIGURACIÓN Y ESTILO (ESPACIO SEGURO Y SIN MARCAS DE STREAMLIT) ---
st.set_page_config(page_title="Animalarium TPV", layout="wide")

st.markdown("""
    <style>
        /* Ajustes de espacio de la aplicación */
        .block-container { padding-top: 2.5rem !important; padding-bottom: 0rem !important; }
        .stSelectbox, .stTextInput, .stNumberInput { margin-bottom: -10px !important; }
        [data-testid="column"] { padding: 0 5px !important; }
        
        /* 🪄 MAGIA: OCULTAR ELEMENTOS DE STREAMLIT (Nivel Extremo) 🪄 */
        #MainMenu {visibility: hidden;} /* Menú de arriba a la derecha */
        footer {visibility: hidden;} /* Pie de página */
        header {visibility: hidden;} /* Cabecera transparente */
        
        /* Ocultar botones de "Deploy" de la barra superior */
        [data-testid="stAppDeployButton"] {display: none !important;}
        [data-testid="stToolbar"] {display: none !important;}
        .stDeployButton {display: none !important;}
        
        /* 🚨 ELIMINAR EL BOTÓN INFERIOR DERECHO "MANAGE APP" EN LA NUBE 🚨 */
        #st-viewer-badge {display: none !important;}
        [data-testid="viewerBadge"] {display: none !important;}
        .viewerBadge_container__1QSob {display: none !important;}
        .viewerBadge_link__1S137 {display: none !important;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. MEMORIA DE LA SESIÓN ---
if 'carrito' not in st.session_state: st.session_state['carrito'] = []
if 'acceso_concedido' not in st.session_state: st.session_state.acceso_concedido = False
if 'ticket_html' not in st.session_state: st.session_state['ticket_html'] = None
if 'ticket_actual' not in st.session_state:
    st.session_state.ticket_actual = None

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

# --- CABECERA (LOGO GRANDE Y TÍTULO SIN CORTES) ---
c_logo, c_titulo = st.columns([0.1, 0.9], vertical_alignment="center")
with c_logo:
    try: st.image("LOGO.jpg", width=75) # Logo más grande
    except: st.write("🐾")
with c_titulo:
    # Letra un poco más pequeña (2rem) y bajada unos milímetros para que no se corte
    st.markdown("<h1 style='margin: 5px 0 0 0; padding:0; font-size: 2rem;'>Animalarium - TPV</h1>", unsafe_allow_html=True)

# 🚨 AÑADIDA LA PESTAÑA 5: CONTROL CAJA 🚨
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📦 Inventario", "🛒 Caja/Ventas", "👥 Clientes", "📜 Historial", "💰 Control Caja"])

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

# --- TAB 2: CAJA Y VENTAS ---
with tab2:
    st.markdown("""
        <div style='display: flex; justify-content: space-between; margin-top: 10px; margin-bottom: 10px; padding: 0 5px;'>
            <h4 style='margin:0; color: #333; white-space: nowrap;'>🛒 Terminal de Venta</h4>
            <h4 style='margin:0; color: #333; white-space: nowrap; padding-right: 10px;'>🛒 Tu Carrito</h4>
        </div>
    """, unsafe_allow_html=True)

    col_busqueda, col_carrito = st.columns([1.1, 1], gap="small")
    
    with col_busqueda:
        res_inv = client.table("productos_y_servicios").select("*").execute()
        df_inv = pd.DataFrame(res_inv.data) if res_inv.data else pd.DataFrame()
        
        # 1. BUSCADOR
        st.markdown("<p style='margin: 0; font-weight: bold; font-size: 13px;'>🔍 Buscar Producto</p>", unsafe_allow_html=True)
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
                            "Producto": fila_p['nombre'], "Cantidad": cant, "Precio": fila_p['precio_pvp'],
                            "Subtotal": cant * float(fila_p['precio_pvp']), "IGIC": fila_p.get('tipo_igic', 7), "Manual": False
                        })
                        st.rerun()
        
        st.markdown("<hr style='margin: 5px 0px; border: none; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

        # 2. PISTOLA
        st.markdown("<p style='margin: 0; font-weight: bold; font-size: 13px;'>📇 Escáner de Pistola</p>", unsafe_allow_html=True)
        if 'limpiar_codigo' in st.session_state and st.session_state.limpiar_codigo:
            st.session_state.input_pistola = ""
            st.session_state.limpiar_codigo = False

        cp1, cp2 = st.columns([2, 1])
        with cp1: cod_leido = st.text_input("p1", placeholder="Esperando escaneo...", label_visibility="collapsed", key="input_pistola")
        with cp2: cant_p = st.number_input("p2", min_value=1, value=1, label_visibility="collapsed", key="cant_p")
        
        if cod_leido and not df_inv.empty:
            coincid = df_inv[df_inv['codigo_barras'] == cod_leido]
            if not coincid.empty:
                fila_pist = coincid.iloc[0]
                st.session_state.carrito.append({
                    "Producto": fila_pist['nombre'], "Cantidad": cant_p, "Precio": fila_pist['precio_pvp'],
                    "Subtotal": cant_p * float(fila_pist['precio_pvp']), "IGIC": fila_pist.get('tipo_igic', 7), "Manual": False
                })
                st.session_state.limpiar_codigo = True; st.rerun()

        st.markdown("<hr style='margin: 5px 0px; border: none; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

        # 3. ARTÍCULO MANUAL
        st.markdown("<p style='margin: 0; font-weight: bold; font-size: 13px;'>✍️ Artículo Manual</p>", unsafe_allow_html=True)
        with st.form("f_man", clear_on_submit=True, border=False):
            cm1, cm2, cm3 = st.columns([1.3, 1, 1]) 
            with cm1: m_nom = st.text_input("Producto", placeholder="Nombre...", label_visibility="visible")
            with cm2: m_pre = st.number_input("Precio €", min_value=0.0, step=0.1, format="%.2f", label_visibility="visible")
            with cm3: m_can = st.number_input("Cant.", min_value=1, value=1, label_visibility="visible")
            
            if st.form_submit_button("➕ Añadir Manual al Carrito", use_container_width=True):
                if m_nom and m_pre > 0:
                    st.session_state.carrito.append({
                        "Producto": m_nom, "Cantidad": m_can, "Precio": m_pre,
                        "Subtotal": m_can * float(m_pre), "IGIC": 0, "Manual": True
                    })
                    st.rerun()

    # --- COLUMNA DERECHA: CARRITO Y TICKET ---
    with col_carrito:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        # 🧾 VISTA 1: SI ACABAMOS DE COBRAR, MOSTRAMOS EL TICKET
        if st.session_state.get('ticket_actual'):
            t = st.session_state.ticket_actual
            st.success("✅ Venta realizada con éxito")
            
            html_ticket = f"""
            <div id="ticket" style="font-family: 'Courier New', Courier, monospace; padding: 20px; border: 1px solid #eee; width: 100%; max-width: 300px; margin: auto; background-color: #fff; color: #000;">
                <div style="text-align: center;">
                    <b style="font-size: 18px;">ANIMALARIUM</b><br>
                    Raquel Trujillo Hernández<br>
                    DNI: 78854854K<br>
                    Calle José Hernández Alfonso, 26<br>
                    38009 Santa Cruz de Tenerife
                </div>
                <br>
                <div style="font-size: 12px;">Fecha: {t['fecha']}</div>
                <hr style="border-top: 1px dashed #000;">
                <table style="width: 100%; font-size: 13px;">
            """
            for p in t['productos']:
                html_ticket += f"<tr><td>{p['Cantidad']}x {p['Producto']}</td><td style='text-align: right;'>{p['Subtotal']:.2f}€</td></tr>"
            
            html_ticket += f"""
                </table>
                <hr style="border-top: 1px dashed #000;">
                <div style="text-align: right; font-size: 16px;"><b>TOTAL: {t['total']:.2f}€</b></div>
                <div style="font-size: 12px; color: #444; margin-top: 10px; text-align: center;">
                    <b>POLÍTICA DE DEVOLUCIÓN</b><br>
                    Plazo de 14 días con ticket y embalaje original.
                </div>
            </div>
            <div style="text-align: center; margin-top: 15px;">
                <button onclick="window.print()" style="padding: 10px 20px; background-color: #005275; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%;">🖨️ IMPRIMIR TICKET</button>
            </div>
            """
            import streamlit.components.v1 as components
            components.html(html_ticket, height=450)
            
            c_em, c_nv = st.columns(2)
            with c_em:
                import urllib.parse
                texto_mail = f"Ticket Animalarium\nTotal: {t['total']:.2f}€\nFecha: {t['fecha']}"
                url_mail = f"mailto:?subject=Ticket Animalarium&body={urllib.parse.quote(texto_mail)}"
                st.markdown(f"<a href='{url_mail}' target='_blank' style='text-decoration:none;'><button style='width:100%; padding:8px; border-radius:5px; border:1px solid #ccc; cursor:pointer;'>✉️ Email</button></a>", unsafe_allow_html=True)
            with c_nv:
                if st.button("🛒 Nueva Venta", use_container_width=True, type="primary"):
                    st.session_state.ticket_actual = None
                    st.rerun()

        # 🛒 VISTA 2: CARRITO
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
                    hide_index=True, use_container_width=True, num_rows="dynamic", height=110, key="ed_car_ticket"
                )
                
                if not edited_df.equals(df_car):
                    import json
                    edited_df["Subtotal"] = (edited_df["Cantidad"] * edited_df["Precio"]) * (1 - edited_df["Desc. %"] / 100)
                    st.session_state.carrito = json.loads(edited_df.to_json(orient='records'))
                    st.rerun()

                st.markdown("<hr style='margin: 2px 0px; border: none; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

                sub_antes = edited_df["Subtotal"].sum()
                desc_g = st.number_input("🎁 Descuento Global (%)", min_value=0, max_value=100, value=0, step=1)
                total_f = sub_antes * (1 - desc_g / 100)
                
                st.markdown("<hr style='margin: 2px 0px; border: none; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

                metodo = st.radio("p", ["Efectivo", "Tarjeta", "Bizum", "Mixto"], horizontal=True, label_visibility="collapsed")
                pagado_hoy = 0.0; pendiente = 0.0; metodo_log = metodo

                if metodo == "Efectivo":
                    c_tot, c_ent, c_cam = st.columns([0.8, 1, 1])
                    with c_tot: st.markdown(f"<p style='margin:0; font-size:11px; color:gray;'>TOTAL</p><h3 style='margin:0; color:#d32f2f;'>{total_f:.2f}€</h3>", unsafe_allow_html=True)
                    with c_ent: entregado = st.number_input("Entregado €", min_value=0.0, value=float(total_f), format="%.2f")
                    with c_cam:
                        cambio = entregado - total_f
                        if cambio >= 0:
                            st.markdown(f"<p style='margin:0; font-size:11px; color:gray;'>CAMBIO</p><h3 style='margin:0; color:green;'>{cambio:.2f}€</h3>", unsafe_allow_html=True)
                            pagado_hoy = total_f
                        else:
                            st.markdown(f"<p style='margin:0; font-size:11px; color:gray;'>DEUDA</p><h3 style='margin:0; color:orange;'>{-cambio:.2f}€</h3>", unsafe_allow_html=True)
                            pagado_hoy = entregado; pendiente = -cambio

                elif metodo == "Mixto":
                    st.markdown(f"<h3 style='text-align: right; margin: 0; color: #d32f2f;'>Total: {total_f:.2f}€</h3>", unsafe_allow_html=True)
                    cm1, cm2, cm3 = st.columns(3)
                    with cm1: p_e = st.number_input("Efe.", min_value=0.0, value=0.0)
                    with cm2: p_t = st.number_input("Tar.", min_value=0.0, value=0.0)
                    with cm3: p_b = st.number_input("Biz.", min_value=0.0, value=0.0)
                    pagado_hoy = p_e + p_t + p_b
                    pendiente = total_f - pagado_hoy if pagado_hoy < total_f else 0.0
                    metodo_log = f"Mixto (E:{p_e}|T:{p_t}|B:{p_b})"
                    if pendiente > 0: st.warning(f"Pendiente: {pendiente:.2f}€")
                
                else:
                    st.markdown(f"<h3 style='text-align: right; margin: 0; color: #d32f2f;'>Total: {total_f:.2f}€</h3>", unsafe_allow_html=True)
                    pagado_hoy = total_f

                nombre_deudor = ""
                if pendiente > 0:
                    nombre_deudor = st.text_input("👤 Nombre para la deuda:", placeholder="¿Quién debe?")

                st.markdown("<div style='height: 2px;'></div>", unsafe_allow_html=True)
                c_cob, c_vac = st.columns([2, 1])
                with c_cob:
                    bloqueo = (pendiente > 0 and not nombre_deudor)
                    if st.button("🧧 FINALIZAR COBRO", use_container_width=True, type="primary", disabled=bloqueo):
                        import json, datetime
                        carrito_limpio = json.loads(edited_df.to_json(orient='records'))
                        
                        try:
                            # 1. Guardar en Supabase
                            client.table("ventas_historial").insert({
                                "total": float(total_f), 
                                "pagado": float(pagado_hoy), 
                                "pendiente": float(pendiente),
                                "metodo_pago": str(metodo_log), 
                                "cliente_deuda": str(nombre_deudor),
                                "descuento_global": float(desc_g),
                                "productos": carrito_limpio, 
                                "estado": "Completado" if pendiente == 0 else "Deuda"
                            }).execute()
                            
                            # 2. Restar Stock
                            for i in carrito_limpio:
                                if not i.get('Manual', False):
                                    res = client.table("productos_y_servicios").select("stock_actual").eq("nombre", i['Producto']).execute()
                                    if res.data:
                                        n_stock = int(res.data[0]['stock_actual']) - int(i['Cantidad'])
                                        client.table("productos_y_servicios").update({"stock_actual": n_stock}).eq("nombre", i['Producto']).execute()
                            
                            # 3. GENERAR DATOS PARA EL TICKET
                            st.session_state.ticket_actual = {
                                "fecha": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "productos": carrito_limpio,
                                "total": total_f,
                                "metodo": metodo_log
                            }
                            
                            # 4. Vaciar carrito y recargar
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

# --- TAB 4: HISTORIAL Y DEVOLUCIONES ---
with tab4:
    st.markdown("<h3 style='margin-top: -15px; margin-bottom: 5px;'>📜 Historial</h3>", unsafe_allow_html=True)
    
    try:
        res_v = client.table("ventas_historial").select("*").execute()
        
        # Comprobamos si la respuesta tiene datos reales
        if res_v.data and len(res_v.data) > 0:
            df_v = pd.DataFrame(res_v.data)
            if not df_v.empty:
                df_v = df_v.sort_values(by="id", ascending=False)
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

                    estado_raw = str(ticket.get('estado', 'Completado')).upper().strip()
                    st.markdown("<hr style='margin: 5px 0px;'>", unsafe_allow_html=True)
                    
                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        if "DEVUELTO" not in estado_raw:
                            m_dev = st.radio("Reembolso:", ["Efectivo", "Tarjeta", "Bizum"], horizontal=True, key=f"rd_{id_t}", label_visibility="collapsed")
                        else: st.error("TICKET YA DEVUELTO")
                    with col_c2:
                        confirmar = st.checkbox("Confirmar borrar registro", key=f"chk_{id_t}")

                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        if "DEVUELTO" not in estado_raw:
                            if st.button("🔄 PROCESAR DEVOLUCIÓN", use_container_width=True):
                                if prods:
                                    for p in prods:
                                        if not p.get('Manual', False):
                                            res_p = client.table("productos_y_servicios").select("stock_actual").eq("nombre", p['Producto']).execute()
                                            if res_p.data:
                                                n_stock = res_p.data[0]['stock_actual'] + p['Cantidad']
                                                client.table("productos_y_servicios").update({"stock_actual": n_stock}).eq("nombre", p['Producto']).execute()
                                client.table("ventas_historial").update({"estado": "DEVUELTO"}).eq("id", id_t).execute()
                                st.success("Devolución realizada y stock restaurado")
                                time.sleep(1); st.rerun()
                    with col_b2:
                        if st.button("🔥 ANULAR Y BORRAR TODO", use_container_width=True, disabled=not confirmar):
                            if prods:
                                for p in prods:
                                    if not p.get('Manual', False):
                                        res_p = client.table("productos_y_servicios").select("stock_actual").eq("nombre", p['Producto']).execute()
                                        if res_p.data:
                                            n_stock = res_p.data[0]['stock_actual'] + p['Cantidad']
                                            client.table("productos_y_servicios").update({"stock_actual": n_stock}).eq("nombre", p['Producto']).execute()
                            client.table("ventas_historial").delete().eq("id", id_t).execute()
                            st.success("Ticket eliminado y stock restaurado")
                            time.sleep(1); st.rerun()
        else:
            # ¡Mensaje amigable si no hay ventas registradas!
            st.info("📭 Aún no hay ventas registradas. ¡El historial está vacío!")
            
    except Exception as e:
        # Solo mostramos error si DE VERDAD la base de datos no responde
        st.error("🔌 Error de conexión con la base de datos.")


# --- TAB 5: CONTROL DE CAJA FUERTE ---
with tab5:
    st.markdown("### 💰 Control de Caja Fuerte")
    
    # 1. Comprobar si hay una caja abierta
    try:
        res_caja = client.table("control_caja").select("*").eq("estado", "Abierta").execute()
        caja_actual = res_caja.data[0] if res_caja.data else None
    except:
        caja_actual = None
        st.error("Error al leer la caja. ¿Has creado la tabla en Supabase?")

    if not caja_actual:
        # PANTALLA: ABRIR CAJA
        st.info("😴 La caja está actualmente CERRADA.")
        col_abrir, vacio = st.columns([1, 2])
        with col_abrir:
            with st.form("abrir_caja"):
                st.markdown("#### 🔓 Apertura de Turno")
                fondo_ini = st.number_input("Fondo Inicial (Monedas/Billetes de cambio) €", min_value=0.0, step=1.0, format="%.2f")
                if st.form_submit_button("Abrir Caja", type="primary", use_container_width=True):
                    client.table("control_caja").insert({
                        "fondo_inicial": fondo_ini,
                        "estado": "Abierta"
                    }).execute()
                    st.success("¡Caja abierta! Que tengas muchas ventas."); time.sleep(1); st.rerun()
    else:
        # PANTALLA: CAJA ABIERTA
        id_caja = caja_actual['id']
        fondo_actual = caja_actual['fondo_inicial']
        fecha_apertura = pd.to_datetime(caja_actual['created_at']).strftime('%d/%m/%Y %H:%M')
        
        st.success(f"🔓 **CAJA ABIERTA** | Abierta el: {fecha_apertura} | Fondo Inicial: **{fondo_actual:.2f}€**")
        
        col_izq, col_der = st.columns([1, 1.2], gap="large")
        
        with col_izq:
            st.markdown("#### 💸 Entradas y Salidas (Extra)")
            with st.form("form_movimientos", clear_on_submit=True):
                c_tipo, c_cant = st.columns([1, 1])
                with c_tipo: tipo_mov = st.selectbox("Tipo", ["Retirada 🔻", "Ingreso 🔺"])
                with c_cant: cant_mov = st.number_input("Cantidad €", min_value=0.01, step=1.0)
                motivo_mov = st.text_input("Motivo (Ej. Pago de agua, cambio traído...)")
                
                if st.form_submit_button("Registrar Movimiento", use_container_width=True):
                    if motivo_mov:
                        tipo_limpio = "Retirada" if "Retirada" in tipo_mov else "Ingreso"
                        client.table("movimientos_caja").insert({
                            "id_caja": id_caja, "tipo": tipo_limpio, "cantidad": cant_mov, "motivo": motivo_mov
                        }).execute()
                        st.success("Movimiento registrado"); st.rerun()
                    else:
                        st.error("Debes escribir un motivo.")
            
            # Mostrar tabla de movimientos
            try:
                # Usamos "*" para traer todo sin fallos de espacios y forzamos que el ID sea un número entero
                res_movs = client.table("movimientos_caja").select("*").eq("id_caja", int(id_caja)).execute()
                
                if res_movs.data:
                    st.markdown("**Movimientos de hoy:**")
                    df_m = pd.DataFrame(res_movs.data)
                    # Filtramos y ordenamos las columnas aquí en Pandas, que es más seguro
                    df_m = df_m[['tipo', 'cantidad', 'motivo']]
                    df_m['tipo'] = df_m['tipo'].apply(lambda x: '🔻 Salida' if x == 'Retirada' else '🔺 Entrada')
                    st.dataframe(df_m, use_container_width=True, hide_index=True)
                else:
                    st.info("No hay movimientos extra registrados en este turno.")
            except Exception as e:
                # Si falla, nuestro propio programa nos chivará el error real
                st.error(f"Error al cargar los movimientos: {e}")

        with col_der:
            st.markdown("#### ⚖️ Arqueo y Cierre de Caja")
            
           # Calculadora de billetes (Expander para que no ocupe tanto espacio si no se usa)
            with st.expander("🧮 Calculadora de Monedas y Billetes"):
                # --- SECCIÓN BILLETES ---
                st.markdown("<p style='font-size: 13px; font-weight: bold; color: gray; margin-bottom: 5px;'>💵 BILLETES</p>", unsafe_allow_html=True)
                cb1, cb2, cb3 = st.columns(3)
                with cb1: 
                    b200 = st.number_input("200€", 0, step=1, key="b200")
                    b100 = st.number_input("100€", 0, step=1, key="b100")
                with cb2: 
                    b50 = st.number_input("50€", 0, step=1, key="b50")
                    b20 = st.number_input("20€", 0, step=1, key="b20")
                with cb3: 
                    b10 = st.number_input("10€", 0, step=1, key="b10")
                    b5 = st.number_input("5€", 0, step=1, key="b5")

                st.markdown("<hr style='margin: 10px 0px; border: none; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)
                
                # --- SECCIÓN MONEDAS ---
                st.markdown("<p style='font-size: 13px; font-weight: bold; color: gray; margin-bottom: 5px;'>🪙 MONEDAS</p>", unsafe_allow_html=True)
                cm1, cm2, cm3, cm4 = st.columns(4)
                with cm1: 
                    m2 = st.number_input("2€", 0, step=1, key="m2")
                    m1 = st.number_input("1€", 0, step=1, key="m1")
                with cm2: 
                    m50c = st.number_input("0.50€", 0, step=1, key="m50c")
                    m20c = st.number_input("0.20€", 0, step=1, key="m20c")
                with cm3: 
                    m10c = st.number_input("0.10€", 0, step=1, key="m10c")
                    m5c = st.number_input("0.05€", 0, step=1, key="m5c")
                with cm4:
                    m2c = st.number_input("0.02€", 0, step=1, key="m2c")
                    m1c = st.number_input("0.01€", 0, step=1, key="m1c")
                
                # --- CÁLCULO TOTAL ---
                total_calc = (b200*200) + (b100*100) + (b50*50) + (b20*20) + (b10*10) + (b5*5) + \
                             (m2*2) + (m1*1) + (m50c*0.50) + (m20c*0.20) + (m10c*0.10) + (m5c*0.05) + \
                             (m2c*0.02) + (m1c*0.01)
                             
                st.success(f"**Total Contado: {total_calc:.2f}€**")

            with st.form("form_cierre"):
                st.markdown("Introduce el dinero real que hay ahora mismo físicamente en el cajón para calcular el descuadre y cerrar la caja.")
                efectivo_real = st.number_input("💵 Total Efectivo en Cajón €", min_value=0.0, step=1.0, value=float(total_calc) if total_calc > 0 else 0.0)
                
                if st.form_submit_button("🔒 Cerrar Caja Definitivamente", type="primary", use_container_width=True):
                    # NOTA PARA RAQUEL: Aquí calcularemos lo que DEBERÍA haber.
                    # Por ahora hacemos una lógica sencilla: Fondo + Ingresos Extra - Retiradas Extra.
                    # Para sumar las VENTAS, idealmente tendríamos que cruzar la fecha de `ventas_historial`
                    # mayores a `caja_actual['created_at']` donde el método sea Efectivo.
                    
                    ingresos = 0; retiradas = 0
                    if res_movs.data:
                        for mov in res_movs.data:
                            if mov['tipo'] == 'Ingreso': ingresos += mov['cantidad']
                            else: retiradas += mov['cantidad']
                    
                    # Lo ideal sería sumar ventas en efectivo aquí, pero como base:
                    total_teorico_base = fondo_actual + ingresos - retiradas
                    descuadre = efectivo_real - total_teorico_base
                    
                    client.table("control_caja").update({
                        "estado": "Cerrada",
                        "total_contado": efectivo_real,
                        "descuadre": descuadre
                    }).eq("id", id_caja).execute()
                    
                    st.success(f"Caja cerrada con éxito. Descuadre registrado: {descuadre:.2f}€"); 
                    time.sleep(1.5); st.rerun()