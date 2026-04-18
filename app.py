import streamlit as st
import pandas as pd
from postgrest import SyncPostgrestClient
from datetime import datetime
import time
import json
import urllib.parse
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="Animalarium TPV", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
        .stSelectbox, .stTextInput, .stNumberInput { margin-bottom: -10px !important; }
        [data-testid="column"] { padding: 0 5px !important; }
        [data-testid="stTabs"] { margin-top: -15px !important; }
        
        /* Ocultar Streamlit */
        [data-testid="stHeader"], [data-testid="stFooter"], footer, 
        [data-testid="stAppDeployButton"], .stDeployButton, 
        [data-testid="stToolbar"], #st-viewer-badge, [data-testid="viewerBadge"] 
        {display: none !important;}
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
    client = SyncPostgrestClient(
        f"{st.secrets['url']}/rest/v1", 
        headers={"apikey": st.secrets['key'], "Authorization": f"Bearer {st.secrets['key']}"}
    )
except Exception as e:
    st.error("Error de conexión"); st.stop()

# --- CABECERA COMPACTA ---
c_logo, c_titulo = st.columns([0.08, 0.92], vertical_alignment="center")
with c_logo:
    try: st.image("LOGO.jpg", width=60)
    except: st.markdown("<h2 style='margin:0; padding:0;'>🐾</h2>", unsafe_allow_html=True)
with c_titulo:
    st.markdown("<h1 style='margin: 0; padding: 0; font-size: 1.8rem; line-height: 1;'>Animalarium - TPV</h1>", unsafe_allow_html=True)

# 🚨 DEFINICIÓN CORRECTA DE LAS 9 PESTAÑAS 🚨
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📦 Inventario", "🛒 Caja", "👥 Clientes", "📜 Historial", 
    "💰 Control Caja", "📈 Estadísticas", "🚚 Proveedores", "📑 Facturación", "⚙️ Admin"
])

# ==========================================
# --- TAB 1: INVENTARIO MULTI-PROVEEDOR ---
# ==========================================
with tab1:
    col_f, col_t = st.columns([1.2, 2.5])
    
    res_proveedores = client.table("proveedores").select("id, nombre_empresa").execute()
    dict_proveedores = {p['nombre_empresa']: p['id'] for p in res_proveedores.data} if res_proveedores.data else {}
    lista_nombres_prov = list(dict_proveedores.keys())

    with col_f:
        st.markdown("### 📝 Nuevo Producto")
        with st.form("nuevo_p", clear_on_submit=True):
            nombre = st.text_input("Nombre")
            c1, c2 = st.columns(2)
            with c1: sku = st.text_input("SKU / Código")
            with c2: cat = st.selectbox("Categoría", ["Producto", "Servicio"])
            
            c3, c4 = st.columns(2)
            with c3: p_base = st.number_input("Coste Medio (€)", min_value=0.0, format="%.2f")
            with c4: igic_tipo = st.selectbox("IGIC %", [7.00, 0.00, 3.00, 15.00])
            
            c5, c6 = st.columns(2)
            with c5: pvp = st.number_input("PVP Final (€)", min_value=0.0, format="%.2f")
            with c6: stck = st.number_input("Stock", min_value=0)
            
            provs_seleccionados = st.multiselect("Proveedor/es", lista_nombres_prov, placeholder="Elige uno o varios...")
            
            if st.form_submit_button("Guardar Producto", use_container_width=True):
                if nombre and sku:
                    res_insert = client.table("productos").insert({
                        "sku": sku, "nombre": nombre, "categoria": cat,
                        "precio_base": p_base, "igic_tipo": igic_tipo, 
                        "stock_actual": stck, "precio_pvp": pvp
                    }).execute()
                    
                    if res_insert.data:
                        nuevo_producto_id = res_insert.data[0]['id']
                        if provs_seleccionados:
                            relaciones = []
                            for prov_nombre in provs_seleccionados:
                                relaciones.append({
                                    "producto_id": nuevo_producto_id,
                                    "proveedor_id": dict_proveedores[prov_nombre],
                                    "precio_coste": p_base
                                })
                            client.table("productos_proveedores").insert(relaciones).execute()
                        st.success("Añadido correctamente"); time.sleep(0.5); st.rerun()
                else:
                    st.warning("Faltan datos (Nombre o SKU)")

    with col_t:
        st.markdown("### 📦 Stock Actual")
        res_prod = client.table("productos").select("sku, nombre, precio_base, precio_pvp, stock_actual, productos_proveedores(proveedores(nombre_empresa))").execute()
        if res_prod.data:
            df_p = pd.DataFrame(res_prod.data)
            def extraer_proveedores(relaciones):
                if isinstance(relaciones, list) and len(relaciones) > 0:
                    nombres = [r['proveedores']['nombre_empresa'] for r in relaciones if r.get('proveedores')]
                    return ", ".join(nombres)
                return "Sin proveedor"
            df_p['Proveedores'] = df_p['productos_proveedores'].apply(extraer_proveedores)
            st.dataframe(df_p[['sku', 'nombre', 'precio_base', 'precio_pvp', 'stock_actual', 'Proveedores']], 
                         use_container_width=True, height=450, hide_index=True)
        else:
            st.info("Inventario vacío. Añade el primer producto a la izquierda.")


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

    col_busqueda, col_carrito = st.columns([1.1, 1], gap="small")
    
    with col_busqueda:
        res_inv = client.table("productos").select("*").execute()
        df_inv = pd.DataFrame(res_inv.data) if res_inv.data else pd.DataFrame()
        
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
                    "Producto": fila_pist['nombre'], "Cantidad": cant_p, "Precio": fila_pist['precio_pvp'],
                    "Subtotal": cant_p * float(fila_pist['precio_pvp']), "IGIC": fila_pist.get('igic_tipo', 7), "Manual": False
                })
                st.session_state.limpiar_codigo = True; st.rerun()

        st.markdown("<hr style='margin: 5px 0px; border: none; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

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

    with col_carrito:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        if st.session_state.get('ticket_actual'):
            t = st.session_state.ticket_actual
            st.success("✅ Venta realizada con éxito")
            
            html_ticket = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                @media screen {{
                    #ticket-impresion {{ display: none; }}
                    #pantalla {{ font-family: sans-serif; text-align: center; }}
                    .btn-print {{ padding: 10px; background-color: #005275; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%; font-size: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    .btn-print:hover {{ background-color: #003d57; }}
                }}
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
            for p in t['productos']:
                html_ticket += f"<tr><td>{p['Cantidad']}x {p['Producto']}</td><td style='text-align: right;'>{p['Subtotal']:.2f}€</td></tr>"
            
            html_ticket += f"""
                    </table>
                    <hr style="border-top: 1px dashed #000; margin: 5px 0px;">
                    <div style="text-align: right; font-size: 14px;"><b>TOTAL: {t['total']:.2f}€</b></div>
                    <div style="font-size: 10px; color: #444; margin-top: 10px; text-align: center;">
                        <b>POLÍTICA DE DEVOLUCIÓN</b><br>
                        Plazo de 14 días con ticket y embalaje original.
                    </div>
                </div>
            </body>
            </html>
            """
            components.html(html_ticket, height=75)
            
            c_em, c_nv = st.columns(2)
            with c_em:
                texto_mail = f"Ticket Animalarium\nTotal: {t['total']:.2f}€\nFecha: {t['fecha']}"
                url_mail = f"mailto:?subject=Ticket Animalarium&body={urllib.parse.quote(texto_mail)}"
                st.markdown(f"<a href='{url_mail}' target='_blank' style='text-decoration:none;'><button style='width:100%; padding:8px; border-radius:5px; border:1px solid #ccc; cursor:pointer; font-weight: bold;'>✉️ Email</button></a>", unsafe_allow_html=True)
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
                    hide_index=True, use_container_width=True, num_rows="dynamic", height=110, key="ed_car_ticket"
                )
                
                if not edited_df.equals(df_car):
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
                        carrito_limpio = json.loads(edited_df.to_json(orient='records'))
                        
                        try:
                            client.table("ventas_historial").insert({
                                "total": float(total_f), "pagado": float(pagado_hoy), "pendiente": float(pendiente),
                                "metodo_pago": str(metodo_log), "cliente_deuda": str(nombre_deudor),
                                "descuento_global": float(desc_g), "productos": carrito_limpio, 
                                "estado": "Completado" if pendiente == 0 else "Deuda"
                            }).execute()
                            
                            for i in carrito_limpio:
                                if not i.get('Manual', False):
                                    res = client.table("productos").select("stock_actual").eq("nombre", i['Producto']).execute()
                                    if res.data:
                                        n_stock = int(res.data[0]['stock_actual']) - int(i['Cantidad'])
                                        client.table("productos").update({"stock_actual": n_stock}).eq("nombre", i['Producto']).execute()
                            
                            st.session_state.ticket_actual = {
                                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "productos": carrito_limpio, "total": total_f, "metodo": metodo_log
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
            
            st.markdown("<hr style='margin: 5px 0px; border: none; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)
            st.markdown("<p style='margin: 0; font-size: 13px; color: gray;'>🐾 Añadir mascota principal (Opcional)</p>", unsafe_allow_html=True)
            
            m_nom = st.text_input("Nombre de la mascota")
            cm1, cm2 = st.columns(2)
            with cm1: m_esp = st.selectbox("Especie", ["", "Perro", "Gato", "Ave", "Roedor", "Reptil", "Otro"])
            with cm2: m_raz = st.text_input("Raza")
            m_obs = st.text_input("Observaciones (Alergias, carácter...)")

            if st.form_submit_button("💾 Guardar Ficha", type="primary", use_container_width=True):
                if c_nom:
                    res_cli = client.table("clientes").insert({
                        "nombre_dueno": c_nom, "telefono": c_tel, "email": c_ema
                    }).execute()

                    if res_cli.data and m_nom:
                        cli_id = res_cli.data[0]['id']
                        client.table("mascotas").insert({
                            "cliente_id": cli_id, "nombre": m_nom, "especie": m_esp, 
                            "raza": m_raz, "observaciones": m_obs
                        }).execute()

                    st.success("Cliente guardado correctamente"); time.sleep(0.5); st.rerun()
                else:
                    st.warning("El nombre del dueño es obligatorio.")

    with col_c2:
        st.markdown("#### 📋 Directorio de Clientes")
        res_clientes = client.table("clientes").select("id, nombre_dueno, telefono, email, mascotas(nombre, especie)").order("created_at", desc=True).execute()

        if res_clientes.data:
            df_cli = pd.DataFrame(res_clientes.data)
            def formatear_mascotas(lista_mascotas):
                if isinstance(lista_mascotas, list) and len(lista_mascotas) > 0:
                    return ", ".join([f"{m['nombre']} ({m['especie']})" for m in lista_mascotas])
                return "Sin mascotas"

            df_cli['Mascotas Registradas'] = df_cli['mascotas'].apply(formatear_mascotas)
            st.dataframe(df_cli[['nombre_dueno', 'telefono', 'email', 'Mascotas Registradas']],
                         use_container_width=True, hide_index=True, height=250)

            st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

            st.markdown("#### ➕ Añadir otra mascota a un cliente")
            dict_cli = {f"{c['nombre_dueno']} ({c['telefono']})": c['id'] for c in res_clientes.data}
            
            with st.form("nueva_mascota_extra", clear_on_submit=True, border=False):
                sel_cli = st.selectbox("Selecciona el dueño:", list(dict_cli.keys()))
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
        else:
            st.info("📭 Aún no tienes clientes registrados. ¡Empieza a añadir fichas a la izquierda!")        


# ==========================================
# --- TAB 4: HISTORIAL Y DEVOLUCIONES ---
# ==========================================
with tab4:
    st.markdown("<h3 style='margin-top: -15px; margin-bottom: 5px;'>📜 Historial</h3>", unsafe_allow_html=True)
    
    try:
        res_v = client.table("ventas_historial").select("*").execute()
        
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
                                            res_p = client.table("productos").select("stock_actual").eq("nombre", p['Producto']).execute()
                                            if res_p.data:
                                                n_stock = res_p.data[0]['stock_actual'] + p['Cantidad']
                                                client.table("productos").update({"stock_actual": n_stock}).eq("nombre", p['Producto']).execute()
                                client.table("ventas_historial").update({"estado": "DEVUELTO"}).eq("id", id_t).execute()
                                st.success("Devolución realizada y stock restaurado")
                                time.sleep(1); st.rerun()
                    with col_b2:
                        if st.button("🔥 ANULAR Y BORRAR", use_container_width=True, disabled=not confirmar):
                            if prods:
                                for p in prods:
                                    if not p.get('Manual', False):
                                        res_p = client.table("productos").select("stock_actual").eq("nombre", p['Producto']).execute()
                                        if res_p.data:
                                            n_stock = res_p.data[0]['stock_actual'] + p['Cantidad']
                                            client.table("productos").update({"stock_actual": n_stock}).eq("nombre", p['Producto']).execute()
                            client.table("ventas_historial").delete().eq("id", id_t).execute()
                            st.success("Ticket eliminado y stock restaurado")
                            time.sleep(1); st.rerun()
        else:
            st.info("📭 Aún no hay ventas registradas. ¡El historial está vacío!")
            
    except Exception as e:
        st.error("🔌 Error de conexión con la base de datos.")


# ==========================================
# --- TAB 5: CONTROL DE CAJA FUERTE ---
# ==========================================
with tab5:
    try:
        res_caja = client.table("control_caja").select("*").eq("estado", "Abierta").execute()
        caja_actual = res_caja.data[0] if res_caja.data else None
    except:
        caja_actual = None
        st.error("Error al conectar con las tablas de caja.")

    if not caja_actual:
        st.info("😴 La caja está actualmente CERRADA.")
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
            res_cajas_cerradas = client.table("control_caja").select("*").eq("estado", "Cerrada").order("id", desc=True).execute()
            
            if res_cajas_cerradas.data and len(res_cajas_cerradas.data) > 0:
                df_cajas = pd.DataFrame(res_cajas_cerradas.data)
                try: df_cajas['Fecha'] = pd.to_datetime(df_cajas['created_at']).dt.strftime('%d/%m/%Y %H:%M')
                except: df_cajas['Fecha'] = "---"
                df_vista_cajas = df_cajas[['id', 'Fecha', 'fondo_inicial', 'total_contado', 'descuadre']].copy()
                df_vista_cajas.columns = ['Turno Nº', 'Apertura', 'Fondo Inicial (€)', 'Recuento Final (€)', 'Descuadre (€)']
                st.dataframe(df_vista_cajas, use_container_width=True, hide_index=True, height=200)
            else:
                st.info("📭 Aún no hay registros de cajas cerradas en el historial.")
    else:
        id_caja = caja_actual['id']
        fondo_actual = caja_actual['fondo_inicial']
        fecha_ap = pd.to_datetime(caja_actual['created_at']).strftime('%d/%m/%Y %H:%M')
        
        st.success(f"🔓 **CAJA ABIERTA** | Inicio: {fecha_ap} | Fondo: **{fondo_actual:.2f}€**")
        st.markdown("<div style='margin-top: -30px;'></div>", unsafe_allow_html=True) 
        
        c_tit1, c_tit2 = st.columns([1, 1.2], gap="large")
        with c_tit1: st.markdown("<h4 style='margin: 0 0 5px 0;'>💸 Entradas y Salidas</h4>", unsafe_allow_html=True)
        with c_tit2: st.markdown("<h4 style='margin: 0 0 5px 0;'>⚖️ Arqueo y Cierre</h4>", unsafe_allow_html=True)

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

            with st.form("form_cierre_final", border=True):
                st.markdown("<p style='margin: 0 0 5px 0; font-weight: bold;'>🔒 Confirmar Cierre</p>", unsafe_allow_html=True)
                st.markdown("<p style='font-size: 14px; margin-bottom: 2px;'>💵 Introduce el Efectivo Real Total:</p>", unsafe_allow_html=True)
                
                c_f1, c_f2 = st.columns([1, 1])
                with c_f1:
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

# ==========================================
# --- TAB 6: ESTADÍSTICAS Y CONTABILIDAD ---
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
    st.markdown("<h3 style='margin-bottom: 5px;'>🚚 Gestión de Proveedores</h3>", unsafe_allow_html=True)
    c_p1, c_p2 = st.columns([1, 2])
    
    with c_p1:
        with st.form("n_prov", clear_on_submit=True):
            st.markdown("**Nuevo Proveedor**")
            nombre_emp = st.text_input("Nombre Empresa")
            contacto = st.text_input("Datos de Contacto (Tel/Email)")
            
            if st.form_submit_button("➕ Añadir Proveedor", use_container_width=True, type="primary"):
                if nombre_emp:
                    client.table("proveedores").insert({
                        "nombre_empresa": nombre_emp, "contacto": contacto
                    }).execute()
                    st.success("Proveedor guardado"); time.sleep(0.5); st.rerun()
                else:
                    st.warning("El nombre de la empresa es obligatorio")
                
    with c_p2:
        res_prov = client.table("proveedores").select("*").execute()
        if res_prov.data:
            df_prov = pd.DataFrame(res_prov.data)
            st.dataframe(df_prov[['nombre_empresa', 'contacto']], use_container_width=True, hide_index=True)
        else:
            st.info("No hay proveedores registrados aún.")

# ==========================================
# --- TAB 8: FACTURACIÓN LEGAL CON STOCK ---
# ==========================================
with tab8:
    st.markdown("### 📑 Facturación Oficial (Veri*Factu)")
    st.caption("Añade productos, emite la factura legal y el stock se descontará automáticamente.")
    
    # Memoria temporal para la factura que estamos montando
    if 'factura_temporal' not in st.session_state: st.session_state.factura_temporal = []

    # --- 1. SECCIÓN DE BUSCADOR (Arriba) ---
    st.markdown("#### 🔍 1. Añadir Productos")
    res_inv = client.table("productos").select("*").execute()
    df_inv = pd.DataFrame(res_inv.data) if res_inv.data else pd.DataFrame()
    
    if not df_inv.empty:
        opciones = df_inv.apply(lambda x: f"{x['nombre']} | SKU: {x['sku']} | {x['precio_pvp']}€", axis=1).tolist()
        
        # Minicolumnas solo para alinear el buscador y el botón de añadir
        c_busq, c_cant, c_btn = st.columns([2, 1, 1])
        with c_busq: 
            prod_f = st.selectbox("Buscar producto:", opciones, index=None, placeholder="Escribe o escanea...", label_visibility="collapsed", key="busq_fact")
        with c_cant: 
            c_f_cant = st.number_input("Cantidad", min_value=1, value=1, label_visibility="collapsed", key="cant_fact")
        with c_btn:
            if st.button("➕ Añadir", use_container_width=True):
                if prod_f:
                    nombre_f = prod_f.split(" | ")[0]
                    sku_f = prod_f.split("SKU: ")[1].split(" | ")[0]
                    datos_p = df_inv[df_inv['sku'] == sku_f].iloc[0]
                    
                    st.session_state.factura_temporal.append({
                        "id": datos_p['id'], "Producto": nombre_f, "SKU": sku_f,
                        "Cantidad": c_f_cant, "Precio_PVP": float(datos_p['precio_pvp']),
                        "IGIC_Tipo": float(datos_p['igic_tipo']),
                        "Subtotal": c_f_cant * float(datos_p['precio_pvp'])
                    })
                    st.rerun()

    st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)

    # --- 2. SECCIÓN DE CARRITO Y EMISIÓN (Abajo) ---
    st.markdown("#### 📝 2. Detalle de la Factura en curso")
    
    if st.session_state.factura_temporal:
        # Botón para limpiar si nos equivocamos
        if st.button("🗑️ Vaciar Factura", size="small"):
            st.session_state.factura_temporal = []; st.rerun()

        df_temp = pd.DataFrame(st.session_state.factura_temporal)
        
        # Mostramos la tabla a lo ancho
        st.dataframe(df_temp[['Producto', 'Cantidad', 'Subtotal']], use_container_width=True, hide_index=True)
        
        # Cálculos Legales Automáticos
        total_factura = df_temp['Subtotal'].sum()
        df_temp['Base'] = df_temp['Subtotal'] / (1 + (df_temp['IGIC_Tipo']/100))
        base_total = df_temp['Base'].sum()
        igic_total = total_factura - base_total
        
        st.info(f"**Base Imponible:** {base_total:.2f}€ | **IGIC Total:** {igic_total:.2f}€ | **TOTAL FINAL:** {total_factura:.2f}€")

        # Selección de Cliente
        res_clientes = client.table("clientes").select("id, nombre_dueno, telefono").execute()
        dict_clientes = {f"{c['nombre_dueno']} ({c['telefono']})": c['id'] for c in res_clientes.data} if res_clientes.data else {}
        f_cliente = st.selectbox("Facturar a nombre de:", list(dict_clientes.keys()), placeholder="Selecciona un cliente de tu CRM...")

        # Botón Final
        if st.button("🚀 EMITIR FACTURA Y ACTUALIZAR STOCK", type="primary", use_container_width=True):
            try:
                # 1. Guardar Factura en BBDD
                client.table("facturas").insert({
                    "cliente_id": dict_clientes[f_cliente], "total_neto": float(base_total),
                    "total_igic": float(igic_total), "total_final": float(total_factura),
                    "hash_actual": "FIRMA_PENDIENTE_ST_V1"
                }).execute()
                
                # 2. Sincronizar Stock (Descontar del inventario real)
                for _, item in df_temp.iterrows():
                    res_st = client.table("productos").select("stock_actual").eq("id", item['id']).execute()
                    if res_st.data:
                        nuevo_stock = int(res_st.data[0]['stock_actual']) - int(item['Cantidad'])
                        client.table("productos").update({"stock_actual": nuevo_stock}).eq("id", item['id']).execute()
                
                st.success("✅ Factura legal emitida y Stock actualizado automáticamente.")
                st.session_state.factura_temporal = []
                time.sleep(1.5); st.rerun()
            except Exception as e:
                st.error(f"Error al emitir: {e}")
    else:
        st.warning("El borrador de la factura está vacío. Añade productos desde el buscador superior.")

# ==========================================
# --- TAB 9: PANEL ADMIN ---
# ==========================================
with tab9:
    st.markdown("<h3 style='margin-bottom: 5px; color: #d32f2f;'>⚙️ Modo Administrador BBDD</h3>", unsafe_allow_html=True)
    st.warning("⚠️ Cuidado: Desde aquí tienes acceso directo y sin filtros a toda la base de datos.")
    
    tablas_disponibles = [
        "productos", "productos_proveedores", "proveedores", "ventas_historial", 
        "control_caja", "movimientos_caja", "facturas", "clientes", "mascotas", "citas"
    ]
    t_sel = st.selectbox("Selecciona la tabla a inspeccionar:", tablas_disponibles)
    
    try:
        res_adm = client.table(t_sel).select("*").order("id", desc=False).limit(50).execute()
        if res_adm.data:
            df_adm = pd.DataFrame(res_adm.data)
            st.dataframe(df_adm, use_container_width=True, hide_index=True)
            
            st.markdown("#### 🗑️ Borrado de Emergencia")
            c_del1, c_del2 = st.columns([1, 3])
            with c_del1:
                id_borrar = st.text_input("ID a eliminar")
            with c_del2:
                st.write("") 
                if st.button("Eliminar Registro", type="primary"):
                    if id_borrar:
                        client.table(t_sel).delete().eq("id", id_borrar).execute()
                        st.success("Registro eliminado."); time.sleep(1); st.rerun()
        else:
            st.info(f"La tabla {t_sel} está vacía.")
    except Exception as e:
        st.error(f"Error al leer la tabla: {e}")