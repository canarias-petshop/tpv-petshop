import streamlit as st
import pandas as pd
from postgrest import SyncPostgrestClient
from datetime import datetime
import time

# --- 1. CONFIGURACIÓN Y ESTILO (ESPACIO SEGURO Y SIN MARCAS DE STREAMLIT) ---
st.set_page_config(page_title="Animalarium TPV", layout="wide")

st.markdown("""
    <style>
        /* 🚀 Ajustes EXTREMOS de espacio para subir toda la aplicación */
        .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
        .stSelectbox, .stTextInput, .stNumberInput { margin-bottom: -10px !important; }
        [data-testid="column"] { padding: 0 5px !important; }
        
        /* Pegar las pestañas (Tabs) más cerca del título */
        [data-testid="stTabs"] { margin-top: -15px !important; }
        
        /* 🪄 MAGIA: OCULTAR ELEMENTOS DE STREAMLIT (Corregido) 🪄 */
        [data-testid="stHeader"] {display: none !important;}
        [data-testid="stFooter"] {display: none !important;}
        footer {visibility: hidden !important;}
        [data-testid="stAppDeployButton"] {display: none !important;}
        .stDeployButton {display: none !important;}
        [data-testid="stToolbar"] {display: none !important;}
        #st-viewer-badge {display: none !important;}
        [data-testid="viewerBadge"] {display: none !important;}
        
        /* 🚨 HEMOS QUITADO LA REGLA QUE OCULTABA EL TICKET HTML 🚨 */
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

# --- CABECERA COMPACTA ---
c_logo, c_titulo = st.columns([0.08, 0.92], vertical_alignment="center")
with c_logo:
    try: st.image("LOGO.jpg", width=60) # Logo un pelín más pequeño
    except: st.markdown("<h2 style='margin:0; padding:0;'>🐾</h2>", unsafe_allow_html=True)
with c_titulo:
    # Título sin márgenes y bien pegadito
    st.markdown("<h1 style='margin: 0; padding: 0; font-size: 1.8rem; line-height: 1;'>Animalarium - TPV</h1>", unsafe_allow_html=True)

# 🚨 AÑADIDA LA PESTAÑA 5: CONTROL CAJA 🚨
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📦 Inventario", "🛒 Caja", "👥 Clientes", "📜 Historial", "💰 Control Caja", "📈 Estadísticas"])

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
            
            # Formato HTML (Magia: visible en papel, oculto en pantalla)
            html_ticket = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                /* 1. ESTO ES LO QUE VES EN LA PANTALLA (Solo el botón) */
                @media screen {{
                    #ticket-impresion {{ display: none; }}
                    #pantalla {{ font-family: sans-serif; text-align: center; }}
                    .btn-print {{ padding: 10px; background-color: #005275; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%; font-size: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    .btn-print:hover {{ background-color: #003d57; }}
                }}
                /* 2. ESTO ES LO QUE VE LA IMPRESORA (El ticket completo) */
                @media print {{
                    #pantalla {{ display: none; }}
                    #ticket-impresion {{ display: block; font-family: 'Courier New', Courier, monospace; width: 100%; max-width: 300px; color: #000; font-size: 12px; }}
                }}
            </style>
            </head>
            <body style="margin: 0; padding: 0;">
                
                <div id="pantalla">
                    <button class="btn-print" onclick="window.print()">🖨️ IMPRIMIR TICKET</button>
                    <p style="font-size: 11px; color: #666; margin-top: 5px;">Ticket oculto en pantalla. Saldrá completo al imprimir.</p>
                </div>

                <div id="ticket-impresion">
                    <div style="text-align: center;">
                        <b style="font-size: 16px;">ANIMALARIUM</b><br>
                        Raquel Trujillo Hernández<br>
                        DNI: 78854854K<br>
                        C/ José Hernández Alfonso, 26<br>
                        38009 S/C de Tenerife
                    </div>
                    <br>
                    <div>Fecha: {t['fecha']}</div>
                    <hr style="border-top: 1px dashed #000; margin: 5px 0px;">
                    <table style="width: 100%; font-size: 12px; text-align: left;">
            """
            # --- CIERRE DE TABLA DE PRODUCTOS ---
            for p in t['productos']:
                html_ticket += f"<tr><td>{p['Cantidad']}x {p['Producto']}</td><td style='text-align: right;'>{p['Subtotal']:.2f}€</td></tr>"
            
            html_ticket += """
                    </table>
                    <hr style="border-top: 1px dashed #000; margin: 5px 0px;">
            """

            # --- 🪄 MAGIA FISCAL CANARIA: DESGLOSE DE IGIC INCLUIDO ---
            base_7 = 0.0
            cuota_7 = 0.0
            total_0 = 0.0

            for p in t['productos']:
                igic_val = float(p.get('IGIC', 0))  # Asume 0% si es manual o no lo encuentra
                subt = float(p['Subtotal'])
                
                if igic_val == 7.0:
                    base = subt / 1.07
                    base_7 += base
                    cuota_7 += (subt - base)
                else:
                    total_0 += subt
            
            # Añadimos el desglose alineado a la izquierda para que quede limpio
            html_ticket += "<div style='font-size: 10px; margin-bottom: 5px; color: #444; text-align: left;'>"
            
            # Solo mostramos el título si hay algún servicio al 7%
            if base_7 > 0:
                html_ticket += "<b>Desglose IGIC (Incluido en precio):</b><br>"
                html_ticket += f"Sujeto 7% -> Base: {base_7:.2f}€ | Cuota: {cuota_7:.2f}€<br>"
            
            # Opcional: mostrar lo exento por comercio minorista
            if total_0 > 0:
                html_ticket += f"Exento 0% (R.E. Minorista) -> Base: {total_0:.2f}€<br>"
            
            html_ticket += "</div>"

            # --- TOTAL DEL TICKET Y TU POLÍTICA DE DEVOLUCIÓN ---
            html_ticket += f"""
                    <div style="text-align: right; font-size: 14px;"><b>TOTAL: {t['total']:.2f}€</b></div>
                    <div style="font-size: 10px; color: #444; margin-top: 10px; text-align: center;">
                        <b>POLÍTICA DE DEVOLUCIÓN</b><br>
                        Plazo de 14 días con ticket y embalaje original.
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 🚨 El cuadro ahora solo mide 75 píxeles de alto, adiós al scroll 🚨
            import streamlit.components.v1 as components
            components.html(html_ticket, height=75)
            
            # Botones de Email y Nueva Venta
            c_em, c_nv = st.columns(2)
            with c_em:
                import urllib.parse
                texto_mail = f"Ticket Animalarium\nTotal: {t['total']:.2f}€\nFecha: {t['fecha']}"
                url_mail = f"mailto:?subject=Ticket Animalarium&body={urllib.parse.quote(texto_mail)}"
                st.markdown(f"<a href='{url_mail}' target='_blank' style='text-decoration:none;'><button style='width:100%; padding:8px; border-radius:5px; border:1px solid #ccc; cursor:pointer; font-weight: bold;'>✉️ Email</button></a>", unsafe_allow_html=True)
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
    # 1. Comprobar estado de caja
    try:
        res_caja = client.table("control_caja").select("*").eq("estado", "Abierta").execute()
        caja_actual = res_caja.data[0] if res_caja.data else None
    except:
        caja_actual = None
        st.error("Error al conectar con las tablas de caja.")

    if not caja_actual:
        # PANTALLA: CAJA CERRADA Y ARCHIVO HISTÓRICO
        st.info("😴 La caja está actualmente CERRADA.")
        
        # Dividimos la pantalla: Izquierda para abrir hoy, Derecha para ver el pasado
        col_abrir, col_historial = st.columns([1, 2.5], gap="large")
        
        with col_abrir:
            with st.form("abrir_caja", border=True):
                st.markdown("<h4 style='margin: 0 0 10px 0;'>🔓 Apertura de Turno</h4>", unsafe_allow_html=True)
                fondo_ini = st.number_input("Fondo Inicial €", min_value=0.0, step=1.0)
                if st.form_submit_button("ABRIR CAJA AHORA", type="primary", use_container_width=True):
                    client.table("control_caja").insert({"fondo_inicial": float(fondo_ini), "estado": "Abierta"}).execute()
                    st.success("¡Caja abierta!"); time.sleep(1); st.rerun()
                    
        with col_historial:
            st.markdown("<h4 style='margin: 0 0 10px 0;'>📚 Archivo de Cajas Cerradas</h4>", unsafe_allow_html=True)
            
            # Pedimos a Supabase todas las cajas que estén cerradas, ordenadas de la más nueva a la más vieja
            res_cajas_cerradas = client.table("control_caja").select("*").eq("estado", "Cerrada").order("id", desc=True).execute()
            
            if res_cajas_cerradas.data and len(res_cajas_cerradas.data) > 0:
                df_cajas = pd.DataFrame(res_cajas_cerradas.data)
                
                # Ponemos la fecha bonita
                try: df_cajas['Fecha'] = pd.to_datetime(df_cajas['created_at']).dt.strftime('%d/%m/%Y %H:%M')
                except: df_cajas['Fecha'] = "---"
                
                # Preparamos las columnas que nos importan para la tabla
                df_vista_cajas = df_cajas[['id', 'Fecha', 'fondo_inicial', 'total_contado', 'descuadre']].copy()
                df_vista_cajas.columns = ['Turno Nº', 'Apertura', 'Fondo Inicial (€)', 'Recuento Final (€)', 'Descuadre (€)']
                
                # Mostramos la tabla interactiva
                st.dataframe(df_vista_cajas, use_container_width=True, hide_index=True, height=200)
            else:
                st.info("📭 Aún no hay registros de cajas cerradas en el historial.")
    else:
        id_caja = caja_actual['id']
        fondo_actual = caja_actual['fondo_inicial']
        fecha_ap = pd.to_datetime(caja_actual['created_at']).strftime('%d/%m/%Y %H:%M')
        
        # Barra de estado superior
        st.success(f"🔓 **CAJA ABIERTA** | Inicio: {fecha_ap} | Fondo: **{fondo_actual:.2f}€**")

        # --- TRUCO MÁGICO: TIRA DE TODO HACIA ARRIBA ---
        st.markdown("<div style='margin-top: -30px;'></div>", unsafe_allow_html=True) 
        
        c_tit1, c_tit2 = st.columns([1, 1.2], gap="large")
        with c_tit1: st.markdown("<h4 style='margin: 0 0 5px 0;'>💸 Entradas y Salidas</h4>", unsafe_allow_html=True)
        with c_tit2: st.markdown("<h4 style='margin: 0 0 5px 0;'>⚖️ Arqueo y Cierre</h4>", unsafe_allow_html=True)

        # --- CUERPO ---
        col_izq, col_der = st.columns([1, 1.2], gap="large")
        
        with col_izq:
            with st.form("form_movimientos", clear_on_submit=True, border=True):
                c_tipo, c_cant = st.columns([1, 1])
                with c_tipo: tipo_mov = st.selectbox("Tipo", ["Retirada 🔻", "Ingreso 🔺"])
                with c_cant: cant_mov = st.number_input("Euros €", min_value=0.01, step=1.0)
                motivo_mov = st.text_input("Motivo", placeholder="Ej: Pago proveedor, cambio...")
                if st.form_submit_button("Registrar Movimiento", use_container_width=True):
                    if motivo_mov:
                        tipo_limpio = "Retirada" if "Retirada" in tipo_mov else "Ingreso"
                        client.table("movimientos_caja").insert({"id_caja": id_caja, "tipo": tipo_limpio, "cantidad": float(cant_mov), "motivo": motivo_mov}).execute()
                        st.rerun()
            
            # Historial de movimientos
            res_movs = client.table("movimientos_caja").select("*").eq("id_caja", id_caja).execute()
            if res_movs.data:
                df_m = pd.DataFrame(res_movs.data)[['tipo', 'cantidad', 'motivo']]
                df_m['tipo'] = df_m['tipo'].apply(lambda x: '🔻' if x == 'Retirada' else '🔺')
                st.dataframe(df_m, use_container_width=True, hide_index=True, height=150)

        with col_der:
            with st.container(border=True):
                st.markdown("<p style='font-size: 11px; font-weight: bold; color: gray; margin:0;'>💵 BILLETES</p>", unsafe_allow_html=True)
                cb1, cb2, cb3, cb4, cb5, cb6 = st.columns(6)
                with cb1: b200 = st.number_input("200", 0, step=1, key="b200")
                with cb2: b100 = st.number_input("100", 0, step=1, key="b100")
                with cb3: b50 = st.number_input("50", 0, step=1, key="b50")
                with cb4: b20 = st.number_input("20", 0, step=1, key="b20")
                with cb5: b10 = st.number_input("10", 0, step=1, key="b10")
                with cb6: b5 = st.number_input("5", 0, step=1, key="b5")

                st.markdown("<p style='font-size: 11px; font-weight: bold; color: gray; margin:0; padding-top: 5px;'>🪙 MONEDAS</p>", unsafe_allow_html=True)
                cm1, cm2, cm3, cm4, cm5, cm6, cm7, cm8 = st.columns(8)
                with cm1: m2 = st.number_input("2€", 0, step=1, key="m2")
                with cm2: m1 = st.number_input("1€", 0, step=1, key="m1")
                with cm3: m50c = st.number_input("50¢", 0, step=1, key="m50c")
                with cm4: m20c = st.number_input("20¢", 0, step=1, key="m20c")
                with cm5: m10c = st.number_input("10¢", 0, step=1, key="m10c")
                with cm6: m5c = st.number_input("5¢", 0, step=1, key="m5c")
                with cm7: m2c = st.number_input("2¢", 0, step=1, key="m2c")
                with cm8: m1c = st.number_input("1¢", 0, step=1, key="m1c")
                
                total_calc = (b200*200) + (b100*100) + (b50*50) + (b20*20) + (b10*10) + (b5*5) + \
                             (m2*2) + (m1*1) + (m50c*0.50) + (m20c*0.20) + (m10c*0.10) + (m5c*0.05) + \
                             (m2c*0.02) + (m1c*0.01)
                st.info(f"**Total Contado: {total_calc:.2f}€**")

            # 2. CIERRE (Formulario nativo con alineación perfecta)
            with st.form("form_cierre_final", border=True):
                st.markdown("<p style='margin: 0 0 5px 0; font-weight: bold;'>🔒 Confirmar Cierre</p>", unsafe_allow_html=True)
                
                # Ponemos el título fuera del número para que no descuadre el botón
                st.markdown("<p style='font-size: 14px; margin-bottom: 2px;'>💵 Introduce el Efectivo Real Total:</p>", unsafe_allow_html=True)
                
                c_f1, c_f2 = st.columns([1, 1])
                with c_f1:
                    # El campo de texto no tiene etiqueta superior ('collapsed'), empieza a la misma altura que el botón
                    efectivo_final = st.number_input("Efectivo", min_value=0.0, value=float(total_calc), label_visibility="collapsed")
                with c_f2:
                    submit_cierre = st.form_submit_button("CERRAR CAJA DEFINITIVA", type="primary", use_container_width=True)
                    
                if submit_cierre:
                    ingresos = sum(m['cantidad'] for m in res_movs.data if m['tipo'] == 'Ingreso') if res_movs.data else 0
                    retiradas = sum(m['cantidad'] for m in res_movs.data if m['tipo'] == 'Retirada') if res_movs.data else 0
                    total_teorico = fondo_actual + ingresos - retiradas
                    descuadre = efectivo_final - total_teorico
                    
                    client.table("control_caja").update({
                        "estado": "Cerrada", "total_contado": float(efectivo_final), "descuadre": float(descuadre)
                    }).eq("id", id_caja).execute()
                    st.success(f"Cerrado. Descuadre: {descuadre:.2f}€")
                    time.sleep(1.5); st.rerun()

# --- TAB 6: ESTADÍSTICAS Y CONTABILIDAD ---
with tab6:
    st.markdown("<h3 style='margin-bottom: 5px;'>📈 Contabilidad y Estadísticas</h3>", unsafe_allow_html=True)
    st.write("Resumen global de la salud financiera de Animalarium.")
    
    try:
        # 1. Obtener datos de Ventas y Movimientos
        res_ventas = client.table("ventas_historial").select("created_at, total, estado").execute()
        res_movs = client.table("movimientos_caja").select("created_at, tipo, cantidad").execute()
        
        # 2. Cálculos rápidos
        total_ventas = 0.0
        total_gastos = 0.0
        
        df_v = pd.DataFrame()
        df_m = pd.DataFrame()

        # Procesar Ventas (Ignoramos las devueltas)
        if res_ventas.data:
            df_v = pd.DataFrame(res_ventas.data)
            df_v = df_v[df_v['estado'] != 'DEVUELTO'] # No sumamos lo devuelto
            if not df_v.empty:
                total_ventas = df_v['total'].sum()
                df_v['Fecha'] = pd.to_datetime(df_v['created_at']).dt.date
        
        # Procesar Gastos (Solo retiradas)
        if res_movs.data:
            df_m = pd.DataFrame(res_movs.data)
            df_m_gastos = df_m[df_m['tipo'] == 'Retirada']
            if not df_m_gastos.empty:
                total_gastos = df_m_gastos['cantidad'].sum()
                df_m['Fecha'] = pd.to_datetime(df_m['created_at']).dt.date

        balance_neto = total_ventas - total_gastos

        # 3. Mostrar Tarjetas de Resumen (Métricas)
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric(label="Ingresos Totales (Ventas)", value=f"{total_ventas:.2f} €")
        with col_m2:
            st.metric(label="Gastos Extra (Retiradas)", value=f"-{total_gastos:.2f} €")
        with col_m3:
            st.metric(label="Balance Neto", value=f"{balance_neto:.2f} €", delta=f"{balance_neto:.2f} €")
            
        st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
        
        # 4. Gráfico Visual Sencillo
        st.markdown("**📊 Evolución de Ventas por Día**")
        if not df_v.empty:
            # Agrupamos las ventas por día para el gráfico
            ventas_diarias = df_v.groupby('Fecha')['total'].sum().reset_index()
            ventas_diarias.set_index('Fecha', inplace=True)
            st.bar_chart(ventas_diarias, color="#005275", height=250)
        else:
            st.info("Aún no hay suficientes ventas para generar el gráfico.")

    except Exception as e:
        st.error(f"Error al cargar las estadísticas: {e}")                   