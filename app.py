import streamlit as st
import pandas as pd
from postgrest import SyncPostgrestClient
from datetime import datetime, date, timedelta
import time
import json
import urllib.parse
import streamlit.components.v1 as components
import re

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
        with st.form("nuevo_p_separado", clear_on_submit=True, border=True):
            nombre = st.text_input("Nombre del Producto/Servicio *")
            c1, c2, c3 = st.columns(3)
            with c1: sku = st.text_input("SKU (Interno) *")
            with c2: cod_barras = st.text_input("Cód. Barras")
            with c3: cat = st.selectbox("Categoría *", ["Producto", "Servicio"])
            
            c4, c5 = st.columns(2)
            with c4: p_base = st.number_input("Base Compra (€)", min_value=0.0, format="%.2f")
            with c5: igic_tipo = st.selectbox("IGIC %", [7.00, 0.00, 3.00, 15.00])
            
            c6, c7 = st.columns(2)
            with c6: pvp = st.number_input("PVP Venta (€)", min_value=0.0, format="%.2f")
            with c7: stck = st.number_input("Stock Inicial", min_value=0)
            
            provs_sel = st.multiselect("Asociar Proveedores", list(dict_proveedores.keys()))
            
            if st.form_submit_button("💾 REGISTRAR", use_container_width=True, type="primary"):
                if nombre and sku:
                    res_ins = client.table("productos").insert({
                        "sku": sku, "codigo_barras": cod_barras, "nombre": nombre, "categoria": cat,
                        "precio_base": p_base, "igic_tipo": igic_tipo, 
                        "stock_actual": stck if cat == "Producto" else 0, "precio_pvp": pvp
                    }).execute()
                    if res_ins.data and provs_sel:
                        rels = [{"producto_id": res_ins.data[0]['id'], "proveedor_id": dict_proveedores[p], "precio_coste": p_base} for p in provs_sel]
                        client.table("productos_proveedores").insert(rels).execute()
                    st.success("Guardado correctamente"); time.sleep(0.5); st.rerun()

    with col_t:
        res_prod = client.table("productos").select("*").order("nombre").execute()
        
        if res_prod.data:
            df_inv = pd.DataFrame(res_prod.data)
            
            st.markdown("#### 📦 Inventario de Productos")
            df_solo_productos = df_inv[df_inv['categoria'].isin(['Producto', None, ''])].copy()
            
            edit_p = st.data_editor(
                df_solo_productos,
                column_config={
                    "id": None, "categoria": None,
                    "sku": "SKU", "codigo_barras": "Barras", "nombre": "Descripción",
                    "precio_base": st.column_config.NumberColumn("Base (€)", format="%.2f"),
                    "igic_tipo": "IGIC %", "precio_pvp": "PVP (€)", "stock_actual": "Stock"
                },
                column_order=["sku", "codigo_barras", "nombre", "precio_base", "igic_tipo", "precio_pvp", "stock_actual"],
                hide_index=True, use_container_width=True, key="edit_p_sep"
            )
            if st.button("💾 Guardar cambios en Productos", key="btn_save_p_sep"):
                for i, row in edit_p.iterrows():
                    client.table("productos").update(row.to_dict()).eq("id", row['id']).execute()
                st.success("Productos actualizados"); time.sleep(0.5); st.rerun()

            st.markdown("---")

            st.markdown("#### ✂️ Catálogo de Servicios")
            df_solo_servicios = df_inv[df_inv['categoria'] == 'Servicio'].copy()
            
            if not df_solo_servicios.empty:
                edit_s = st.data_editor(
                    df_solo_servicios,
                    column_config={
                        "id": None, "categoria": None, "stock_actual": None, "codigo_barras": None,
                        "sku": "SKU", "nombre": "Servicio",
                        "precio_base": st.column_config.NumberColumn("Base (€)", format="%.2f"),
                        "igic_tipo": "IGIC %", "precio_pvp": "PVP (€)"
                    },
                    column_order=["sku", "nombre", "precio_base", "igic_tipo", "precio_pvp"],
                    hide_index=True, use_container_width=True, key="edit_s_sep"
                )
                if st.button("💾 Guardar cambios en Servicios", key="btn_save_s_sep"):
                    for i, row in edit_s.iterrows():
                        client.table("productos").update(row.to_dict()).eq("id", row['id']).execute()
                    st.success("Servicios actualizados"); time.sleep(0.5); st.rerun()
            else:
                st.info("No hay servicios registrados.")
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
                    .btn-print {{ padding: 10px; background-color: #005275; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%; font-size: 14px; }}
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
                </div>
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
                p_efectivo = 0.0; p_tarjeta = 0.0; p_bizum = 0.0

                if metodo == "Efectivo":
                    c_tot, c_ent, c_cam = st.columns([0.8, 1, 1])
                    with c_tot: st.markdown(f"<p style='margin:0; font-size:11px; color:gray;'>TOTAL</p><h3 style='margin:0; color:#d32f2f;'>{total_f:.2f}€</h3>", unsafe_allow_html=True)
                    with c_ent: entregado = st.number_input("Entregado €", min_value=0.0, value=float(total_f), format="%.2f")
                    with c_cam:
                        cambio = entregado - total_f
                        if cambio >= 0:
                            st.markdown(f"<p style='margin:0; font-size:11px; color:gray;'>CAMBIO</p><h3 style='margin:0; color:green;'>{cambio:.2f}€</h3>", unsafe_allow_html=True)
                            pagado_hoy = total_f
                            p_efectivo = total_f
                        else:
                            st.markdown(f"<p style='margin:0; font-size:11px; color:gray;'>DEUDA</p><h3 style='margin:0; color:orange;'>{-cambio:.2f}€</h3>", unsafe_allow_html=True)
                            pagado_hoy = entregado; pendiente = -cambio
                            p_efectivo = entregado

                elif metodo == "Mixto":
                    st.markdown(f"<h3 style='text-align: right; margin: 0; color: #d32f2f;'>Total: {total_f:.2f}€</h3>", unsafe_allow_html=True)
                    cm1, cm2, cm3 = st.columns(3)
                    with cm1: p_e = st.number_input("Efe.", min_value=0.0, value=0.0)
                    with cm2: p_t = st.number_input("Tar.", min_value=0.0, value=0.0)
                    with cm3: p_b = st.number_input("Biz.", min_value=0.0, value=0.0)
                    pagado_hoy = p_e + p_t + p_b
                    p_efectivo = p_e; p_tarjeta = p_t; p_bizum = p_b
                    pendiente = total_f - pagado_hoy if pagado_hoy < total_f else 0.0
                    metodo_log = f"Mixto (E:{p_e}|T:{p_t}|B:{p_b})"
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
                            # INSERCIÓN CON COLUMNAS EXACTAS CONTABLES
                            client.table("ventas_historial").insert({
                                "total": float(total_f), "pagado": float(pagado_hoy), "pendiente": float(pendiente),
                                "metodo_pago": str(metodo_log), "cliente_deuda": str(nombre_deudor),
                                "descuento_global": float(desc_g), "productos": carrito_limpio, 
                                "estado": "Completado" if pendiente == 0 else "Deuda",
                                "pago_efectivo": float(p_efectivo),
                                "pago_tarjeta": float(p_tarjeta),
                                "pago_bizum": float(p_bizum)
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
# --- TAB 4: HISTORIAL (MEJORADO CON FECHAS Y EDICIÓN) ---
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

            df_vista = df_v[['id', 'Fecha', 'total', 'metodo_pago', 'estado', 'cliente_deuda']].copy()
            
            st.markdown("💡 *Haz doble clic en cualquier celda para corregir Método de Pago, Estado o Deuda.*")
            edited_df = st.data_editor(
                df_vista,
                column_config={
                    "id": st.column_config.NumberColumn("Nº Ticket", disabled=True, width="small"),
                    "Fecha": st.column_config.TextColumn("Fecha", disabled=True),
                    "total": st.column_config.NumberColumn("Total (€)", disabled=True, format="%.2f"),
                    "metodo_pago": st.column_config.SelectboxColumn("Método", options=["Efectivo", "Tarjeta", "Bizum", "Mixto"]),
                    "estado": st.column_config.SelectboxColumn("Estado", options=["Completado", "Deuda", "DEVUELTO"]),
                    "cliente_deuda": st.column_config.TextColumn("Cliente (Si debe)")
                },
                hide_index=True, use_container_width=True, height=200, key="editor_tickets"
            )
            
            if st.button("💾 Guardar Correcciones", type="primary"):
                diferencias = edited_df.compare(df_vista)
                if not diferencias.empty:
                    for idx in diferencias.index.tolist():
                        client.table("ventas_historial").update({
                            "metodo_pago": str(edited_df.loc[idx, 'metodo_pago']),
                            "estado": str(edited_df.loc[idx, 'estado']),
                            "cliente_deuda": str(edited_df.loc[idx, 'cliente_deuda']) if str(edited_df.loc[idx, 'cliente_deuda']) != 'nan' else ""
                        }).eq("id", int(edited_df.loc[idx, 'id'])).execute()
                    st.success("Tickets actualizados."); time.sleep(1); st.rerun()

            st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
            
            t_buscar = st.number_input("Nº Ticket para ver detalle o devolver:", min_value=1, step=1, value=int(df_v['id'].max()))
            t_info = df_v[df_v['id'] == t_buscar]
            if not t_info.empty:
                prods = t_info.iloc[0].get('productos', [])
                if prods:
                    st.dataframe(pd.DataFrame(prods)[['Producto', 'Cantidad', 'Subtotal']], use_container_width=True, hide_index=True)
                    if "DEVUELTO" not in str(t_info.iloc[0].get('estado', '')).upper():
                        if st.button(f"🔄 DEVOLVER TICKET #{t_buscar} Y RESTAURAR STOCK"):
                            for p in prods:
                                if not p.get('Manual', False):
                                    res_p = client.table("productos").select("stock_actual").eq("nombre", p['Producto']).execute()
                                    if res_p.data:
                                        client.table("productos").update({"stock_actual": res_p.data[0]['stock_actual'] + p['Cantidad']}).eq("nombre", p['Producto']).execute()
                            client.table("ventas_historial").update({"estado": "DEVUELTO"}).eq("id", int(t_buscar)).execute()
                            st.success("Devolución completada."); time.sleep(1); st.rerun()
        else: st.info("No hay ventas en este rango de fechas.")

    with sub_h_cajas:
        c_fc1, c_fc2 = st.columns(2)
        with c_fc1: f_inicio_c = st.date_input("Cajas desde:", value=pd.to_datetime('today') - pd.Timedelta(days=7), key="fc1")
        with c_fc2: f_fin_c = st.date_input("Cajas hasta:", value=pd.to_datetime('today'), key="fc2")

        try:
            res_cajas = client.table("control_caja").select("*").eq("estado", "Cerrada").gte("created_at", f"{f_inicio_c}T00:00:00").lte("created_at", f"{f_fin_c}T23:59:59").order("id", desc=True).execute()

            if res_cajas.data:
                df_c = pd.DataFrame(res_cajas.data)
                df_c['Fecha Apertura'] = pd.to_datetime(df_c['created_at']).dt.strftime('%d/%m/%Y %H:%M')
                df_c_vista = df_c[['id', 'Fecha Apertura', 'fondo_inicial', 'total_contado', 'descuadre']]
                df_c_vista.columns = ['Turno Nº', 'Apertura', 'Fondo Inicial (€)', 'Efectivo Final (€)', 'Descuadre (€)']
                st.dataframe(df_c_vista, use_container_width=True, hide_index=True, height=200)
                
                st.markdown("#### 🖨️ Desglose e Impresión de Cierre")
                turno_sel = st.selectbox("Selecciona un Turno para ver su desglose e imprimir el Ticket Z:", [None] + df_c['id'].tolist())
                
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
        with st.form("abrir_caja", border=True):
            st.markdown("<h4 style='margin: 0 0 10px 0;'>🔓 Apertura de Turno</h4>", unsafe_allow_html=True)
            fondo_ini = st.number_input("Fondo Inicial €", min_value=0.0, step=1.0)
            if st.form_submit_button("ABRIR CAJA AHORA", type="primary", use_container_width=True):
                client.table("control_caja").insert({"fondo_inicial": float(fondo_ini), "estado": "Abierta"}).execute()
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
                
                c_f1, c_f2 = st.columns([1, 1])
                with c_f1: efectivo_final = st.number_input("Efectivo Final Real", min_value=0.0, value=float(total_calc), label_visibility="collapsed")
                with c_f2: submit_cierre = st.form_submit_button("CERRAR CAJA DEFINITIVA", type="primary", use_container_width=True)
                    
                if submit_cierre:
                    ingresos = sum(m['cantidad'] for m in res_movs.data if m['tipo'] == 'Ingreso') if res_movs.data else 0.0
                    retiradas = sum(m['cantidad'] for m in res_movs.data if m['tipo'] == 'Retirada') if res_movs.data else 0.0
                    
                    res_ventas = client.table("ventas_historial").select("total, metodo_pago, estado").gte("created_at", fecha_ap_str).execute()
                    
                    t_efe = 0.0; t_tar = 0.0; t_biz = 0.0
                    if res_ventas.data:
                        for v in res_ventas.data:
                            if v['estado'] != 'DEVUELTO':
                                mp = str(v.get('metodo_pago', ''))
                                if mp == 'Efectivo': t_efe += float(v['total'])
                                elif mp == 'Tarjeta': t_tar += float(v['total'])
                                elif mp == 'Bizum': t_biz += float(v['total'])
                                elif 'Mixto' in mp:
                                    try:
                                        t_efe += float(re.search(r'E:([0-9.]+)', mp).group(1))
                                        t_tar += float(re.search(r'T:([0-9.]+)', mp).group(1))
                                        t_biz += float(re.search(r'B:([0-9.]+)', mp).group(1))
                                    except: pass
                    
                    efectivo_teorico_en_caja = fondo_actual + t_efe + ingresos - retiradas
                    descuadre = efectivo_final - efectivo_teorico_en_caja
                    
                    resumen_json = {
                        "Efectivo": round(t_efe, 2), "Tarjeta": round(t_tar, 2), "Bizum": round(t_biz, 2),
                        "Ingresos": round(ingresos, 2), "Retiradas": round(retiradas, 2)
                    }
                    
                    client.table("control_caja").update({
                        "estado": "Cerrada", 
                        "total_contado": float(efectivo_final), 
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
    st.markdown("### 🚚 Gestión de Proveedores y Pagos")
    cp1, cp2 = st.columns([1, 2])
    with cp1:
        with st.form("n_prov_full", clear_on_submit=True):
            n_emp = st.text_input("Nombre Empresa *")
            n_cif = st.text_input("CIF / NIF")
            n_dir = st.text_input("Dirección")
            n_tel = st.text_input("Teléfono")
            n_ema = st.text_input("Email")
            n_iban = st.text_input("Número de Cuenta (IBAN)")
            if st.form_submit_button("➕ Guardar Proveedor", use_container_width=True, type="primary"):
                if n_emp:
                    client.table("proveedores").insert({
                        "nombre_empresa": n_emp,
                        "cif": n_cif,
                        "contacto": f"Tel: {n_tel} | Email: {n_ema} | Dir: {n_dir} | IBAN: {n_iban}"
                    }).execute()
                    st.success("Guardado"); time.sleep(0.5); st.rerun()
    with cp2:
        res_p = client.table("proveedores").select("*").execute()
        if res_p.data:
            st.dataframe(pd.DataFrame(res_p.data)[['nombre_empresa', 'contacto']], use_container_width=True, hide_index=True)

with tab8:
    st.markdown("<h3 style='margin-top: -15px;'>📑 Emisión y Registro de Facturas</h3>", unsafe_allow_html=True)
    
    sub_f_ventas, sub_f_compras = st.tabs(["🛒 Factura a Cliente (Venta)", "🚚 Registro Factura Proveedor (Compra)"])

    # --- 1. FACTURAS DE VENTA (A CLIENTES) ---
    with sub_f_ventas:
        if 'factura_temporal' not in st.session_state: st.session_state.factura_temporal = []
        
        c_cab1, c_cab2, c_cab3 = st.columns(3)
        with c_cab1: f_pago_v = st.selectbox("Forma de Pago", ["Efectivo", "Tarjeta", "Bizum", "Transferencia"], key="fp_v")
        with c_cab2: fecha_emision_v = st.date_input("Fecha Emisión", key="fe_v")
        with c_cab3: fecha_vence_v = st.date_input("Vencimiento", key="fv_v")

        st.markdown("#### 👤 1. Datos del Cliente")
        res_cli = client.table("clientes").select("*").execute()
        df_cli = pd.DataFrame(res_cli.data) if res_cli.data else pd.DataFrame()
        opciones_cli = df_cli.apply(lambda x: f"{x['nombre_dueno']} - CIF: {x.get('cif', 'N/A')}", axis=1).tolist() if not df_cli.empty else []
        f_cliente = st.selectbox("Selecciona Cliente:", opciones_cli, index=None, placeholder="Escribe para buscar...", key="sel_cli_v")

        st.markdown("#### 📦 2. Artículos de la Factura")
        res_inv = client.table("productos").select("*").execute()
        df_inv = pd.DataFrame(res_inv.data) if res_inv.data else pd.DataFrame()
        
        if not df_inv.empty:
            opciones_v = df_inv.apply(lambda x: f"{x['nombre']} | {x['precio_pvp']}€", axis=1).tolist()
            c_v1, c_v2, c_v3, c_v4 = st.columns([2, 1, 1, 1])
            with c_v1: prod_v = st.selectbox("Producto:", opciones_v, index=None, key="busq_v")
            with c_v2: cant_v = st.number_input("Cant.", min_value=1, value=1, key="cant_v")
            with c_v3: desc_v = st.number_input("Desc. %", min_value=0.0, value=0.0, key="desc_v")
            with c_v4:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.button("➕ Añadir", key="btn_add_v"):
                    if prod_v:
                        nombre_p = prod_v.split(" | ")[0]
                        datos_p = df_inv[df_inv['nombre'] == nombre_p].iloc[0]
                        base_u = float(datos_p['precio_pvp']) / (1 + (float(datos_p['igic_tipo'])/100))
                        st.session_state.factura_temporal.append({
                            "id": str(datos_p['id']), "Descripción": datos_p['nombre'], "Cantidad": cant_v, 
                            "Base Ud": base_u, "IGIC %": float(datos_p['igic_tipo']), 
                            "Total Línea": (base_u * cant_v) * (1 - desc_v/100) * (1 + float(datos_p['igic_tipo'])/100)
                        })
                        st.rerun()

        if st.session_state.factura_temporal:
            df_fv = pd.DataFrame(st.session_state.factura_temporal)
            st.dataframe(df_fv, hide_index=True, use_container_width=True)
            t_total = df_fv['Total Línea'].sum()
            
            # --- FACTURA VISUAL E IMPRIMIBLE ---
            cli_datos = df_cli[df_cli['nombre_dueno'] == f_cliente.split(" -")[0]].iloc[0] if f_cliente else None
            html_fac = f"""
            <div id="factura-imprimir" style="border: 1px solid #ccc; padding: 20px; background: white; color: black; font-family: sans-serif;">
                <div style="text-align: right;"><button onclick="window.print()" style="padding: 10px; background: #005275; color: white; border: none; cursor: pointer;">🖨️ IMPRIMIR FACTURA</button></div>
                <div style="display: flex; justify-content: space-between; border-bottom: 2px solid #005275; margin-top: 10px;">
                    <div><h2>ANIMALARIUM</h2><p>Raquel Trujillo Hernández<br>DNI: 78854854K<br>S/C de Tenerife</p></div>
                    <div style="text-align: right;"><h3>FACTURA DE VENTA</h3><p>Fecha: {fecha_emision_v}<br>Vence: {fecha_vence_v}</p></div>
                </div>
                <div style="margin: 15px 0; padding: 10px; background: #f4f4f4;">
                    <b>Cliente:</b> {cli_datos['nombre_dueno'] if cli_datos is not None else '---'}<br>
                    <b>CIF/DNI:</b> {cli_datos['cif'] if cli_datos is not None else '---'}
                </div>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background: #005275; color: white;"><th>Producto</th><th>Cant.</th><th>Total</th></tr>
                    {''.join([f"<tr><td>{i['Descripción']}</td><td>{i['Cantidad']}</td><td style='text-align:right;'>{i['Total Línea']:.2f}€</td></tr>" for i in st.session_state.factura_temporal])}
                </table>
                <h3 style="text-align: right;">TOTAL: {t_total:.2f}€</h3>
            </div>
            """
            components.html(html_fac, height=450, scrolling=True)

            if st.button("🚀 FINALIZAR Y EMITIR FACTURA", type="primary", use_container_width=True):
                if f_cliente:
                    client.table("facturas").insert({
                        "cliente_id": cli_datos['id'], "total_final": float(t_total), 
                        "forma_pago": f_pago_v, "fecha_vencimiento": str(fecha_vence_v),
                        "productos": st.session_state.factura_temporal # Guardamos el listado
                    }).execute()
                    for i in st.session_state.factura_temporal:
                        res = client.table("productos").select("stock_actual").eq("id", i['id']).execute()
                        if res.data:
                            client.table("productos").update({"stock_actual": res.data[0]['stock_actual'] - i['Cantidad']}).eq("id", i['id']).execute()
                    st.session_state.factura_temporal = []; st.success("Factura Guardada"); time.sleep(1); st.rerun()

    # --- 2. FACTURAS DE COMPRA (PROVEEDORES) ---
    with sub_f_compras:
        if 'entrada_temporal' not in st.session_state: st.session_state.entrada_temporal = []
        
        st.markdown("#### 📝 Datos de la Factura de Papel")
        c1, c2, c3 = st.columns(3)
        with c1: n_fac_p = st.text_input("Nº Factura del Proveedor", key="nf_p")
        with c2: f_pago_c = st.selectbox("Forma de Pago", ["Transferencia", "Efectivo", "Tarjeta"], key="fp_p")
        with c3: f_vence_c = st.date_input("Fecha Vencimiento", key="fv_p")

        res_prov = client.table("proveedores").select("*").execute()
        df_prov = pd.DataFrame(res_prov.data) if res_prov.data else pd.DataFrame()
        op_prov = df_prov['nombre_empresa'].tolist() if not df_prov.empty else []
        p_sel = st.selectbox("Proveedor:", op_prov, index=None, placeholder="Selecciona el proveedor...")

        st.markdown("#### 🛒 Artículos Recibidos")
        if not df_inv.empty:
            c_i1, c_i2, c_i3 = st.columns([3, 1, 1])
            with c_i1: prod_c = st.selectbox("Producto:", df_inv.apply(lambda x: f"{x['nombre']} | SKU: {x['sku']}", axis=1).tolist(), index=None, key="p_c")
            with c_i2: cant_c = st.number_input("Cant", min_value=1, key="cant_c")
            with c_i3:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.button("➕ Añadir Item", key="btn_add_c"):
                    if prod_c:
                        sku_c = prod_c.split("SKU: ")[1]
                        datos_p = df_inv[df_inv['sku'] == sku_c].iloc[0]
                        st.session_state.entrada_temporal.append({
                            "id": str(datos_p['id']), "Descripción": datos_p['nombre'], "Cantidad": cant_c,
                            "Base Ud": float(datos_p['precio_base']), "Total": float(datos_p['precio_base']) * cant_c
                        })
                        st.rerun()

        if st.session_state.entrada_temporal:
            df_ec = pd.DataFrame(st.session_state.entrada_temporal)
            st.table(df_ec[['Descripción', 'Cantidad', 'Total']])
            t_compra = df_ec['Total'].sum()
            st.metric("Total a Archivar", f"{t_compra:.2f} €")

            if st.button("📥 ARCHIVAR FACTURA Y SUMAR STOCK", type="primary", use_container_width=True):
                if p_sel and n_fac_p:
                    prov_id = df_prov[df_prov['nombre_empresa'] == p_sel].iloc[0]['id']
                    client.table("compras").insert({
                        "proveedor_id": prov_id, "total": float(t_compra), "estado": "Recibido", 
                        "fecha_vencimiento": str(f_vence_c), "tipo": "Mercadería",
                        "productos": st.session_state.entrada_temporal # Archivo de artículos
                    }).execute()
                    for i in st.session_state.entrada_temporal:
                        res = client.table("productos").select("stock_actual").eq("id", i['id']).execute()
                        if res.data:
                            client.table("productos").update({"stock_actual": res.data[0]['stock_actual'] + i['Cantidad']}).eq("id", i['id']).execute()
                    st.session_state.entrada_temporal = []; st.success("Factura Archivada Correctamente"); time.sleep(1); st.rerun()

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
                st.markdown("#### Registrar Gasto Operativo")
                concepto = st.text_input("Concepto (Luz, Alquiler, Material...)")
                importe = st.number_input("Importe Total (€)", min_value=0.0)
                f_vence = st.date_input("Fecha de Vencimiento")
                estado_g = st.selectbox("Estado", ["Pagado", "Pendiente"])
                if st.form_submit_button("Guardar Gasto"):
                    if importe > 0:
                        client.table("compras").insert({
                            "tipo": "Gasto Operativo", "total": importe, 
                            "estado": estado_g, "fecha_vencimiento": str(f_vence)
                        }).execute()
                        st.success("Gasto registrado exitosamente."); st.rerun()
                    else:
                        st.error("El importe debe ser mayor que 0.")
        
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
        res_c_inf = client.table("compras").select("id, created_at, tipo, total, estado, proveedores(nombre_empresa, cif)").gte("created_at", fecha_inicio_q).lte("created_at", fecha_fin_q).execute()

        # Construir el SUPER INFORME UNIFICADO DE VENTAS
        ventas_unificadas = []
        
        if res_v_inf.data:
            for t in res_v_inf.data:
                ventas_unificadas.append({
                    "Fecha": pd.to_datetime(t['created_at']).strftime('%d/%m/%Y'),
                    "Tipo_Documento": "Ticket de Mostrador",
                    "Nº Documento": f"T-{t['id']}",
                    "Cliente": t.get('cliente_deuda') if t.get('cliente_deuda') else "Mostrador",
                    "Método de Pago": t['metodo_pago'],
                    "Importe Total (€)": t['total']
                })
                
        if res_f_inf.data:
            for f in res_f_inf.data:
                cliente_nom = f['clientes']['nombre_dueno'] if f.get('clientes') else "N/A"
                ventas_unificadas.append({
                    "Fecha": pd.to_datetime(f['created_at']).strftime('%d/%m/%Y'),
                    "Tipo_Documento": "Factura Oficial",
                    "Nº Documento": f"F-{f['numero_factura']}",
                    "Cliente": cliente_nom,
                    "Método de Pago": f['forma_pago'],
                    "Importe Total (€)": f['total_final']
                })

        df_ventas_unificadas = pd.DataFrame(ventas_unificadas)
        if not df_ventas_unificadas.empty:
            df_ventas_unificadas['Fecha_dt'] = pd.to_datetime(df_ventas_unificadas['Fecha'], format='%d/%m/%Y')
            df_ventas_unificadas = df_ventas_unificadas.sort_values(by="Fecha_dt").drop(columns=['Fecha_dt'])

        c_down1, c_down2, c_down3 = st.columns(3)
        
        with c_down1:
            st.info("💶 INFORME GLOBAL DE VENTAS (TICKETS + FACTURAS)")
            if not df_ventas_unificadas.empty:
                csv_unificado = df_ventas_unificadas.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Descargar Ventas Totales", csv_unificado, f"Ventas_Totales_{f_desde_inf}_al_{f_hasta_inf}.csv", "text/csv")
                st.markdown(f"*Total Ventas: {df_ventas_unificadas['Importe Total (€)'].sum():.2f}€*")
            else:
                st.write("Sin ventas en este periodo.")

        with c_down2:
            st.success("📑 SOLO FACTURAS (Para IGIC)")
            if res_f_inf.data:
                df_f = pd.DataFrame(res_f_inf.data)
                df_f['Fecha'] = pd.to_datetime(df_f['created_at']).dt.strftime('%d/%m/%Y')
                df_f['Cliente'] = df_f['clientes'].apply(lambda x: x['nombre_dueno'] if isinstance(x, dict) else "N/A")
                df_asesor_f = df_f[['numero_factura', 'Fecha', 'Cliente', 'total_final', 'forma_pago']]
                csv_f = df_asesor_f.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Descargar Solo Facturas", csv_f, f"Solo_Facturas_{f_desde_inf}_al_{f_hasta_inf}.csv", "text/csv")
            else:
                st.write("Sin facturas emitidas.")

        with c_down3:
            st.warning("🚚 COMPRAS Y GASTOS (Tickets y Proveedores)")
            if res_c_inf.data:
                df_c = pd.DataFrame(res_c_inf.data)
                df_c['Fecha'] = pd.to_datetime(df_c['created_at']).dt.strftime('%d/%m/%Y')
                df_c['Proveedor_Gasto'] = df_c['proveedores'].apply(lambda x: f"{x['nombre_empresa']} ({x['cif']})" if isinstance(x, dict) else "Gasto General")
                df_asesor_c = df_c[['id', 'Fecha', 'tipo', 'Proveedor_Gasto', 'total', 'estado']]
                csv_c = df_asesor_c.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Descargar Compras/Gastos", csv_c, f"Gastos_{f_desde_inf}_al_{f_hasta_inf}.csv", "text/csv")
            else:
                st.write("Sin compras o gastos en estas fechas.")

# ==========================================
# --- TAB 10: AGENDA Y CITAS ---
# ==========================================
with tab10:
    st.markdown("<h3 style='margin-bottom: 5px;'>📅 Agenda Animalarium</h3>", unsafe_allow_html=True)
    
    res_m = client.table("mascotas").select("id, nombre, clientes(nombre_dueno)").execute()
    dict_mascotas = {}
    if res_m.data:
        for m in res_m.data:
            dueno = m['clientes']['nombre_dueno'] if m.get('clientes') else "Desconocido"
            dict_mascotas[f"🐾 {m['nombre']} (De: {dueno})"] = m['id']

    c_agenda1, c_agenda2 = st.columns([1, 2.5], gap="large")
    
    with c_agenda1:
        with st.form("nueva_cita", border=True):
            st.markdown("#### ➕ Nueva Cita")
            mascota_sel = st.selectbox("Selecciona Mascota *", list(dict_mascotas.keys()), index=None)
            fecha_c = st.date_input("Fecha *")
            hora_c = st.time_input("Hora *")
            servicio_sel = st.selectbox("Servicio *", ["Peluquería (Baño y Corte)", "Peluquería (Solo Baño)", "Corte de Uñas", "Revisión Veterinaria", "Otro"])
            
            if st.form_submit_button("Guardar Cita", type="primary", use_container_width=True):
                if mascota_sel:
                    fecha_hora_str = f"{fecha_c} {hora_c}"
                    client.table("citas").insert({
                        "mascotas_id": dict_mascotas[mascota_sel],
                        "fecha_hora": fecha_hora_str,
                        "servicio": servicio_sel
                    }).execute()
                    st.success("Cita agendada correctamente.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Debes seleccionar una mascota.")

    with c_agenda2:
        st.markdown("#### 🗓️ Próximas Citas")
        res_citas = client.table("citas").select("id, fecha_hora, servicio, mascotas(nombre, clientes(nombre_dueno, telefono))").order("fecha_hora", desc=False).execute()
        
        if res_citas.data:
            citas_formateadas = []
            for c in res_citas.data:
                dt_obj = pd.to_datetime(c['fecha_hora'])
                mascota_info = c.get('mascotas', {})
                cliente_info = mascota_info.get('clientes', {}) if mascota_info else {}
                
                citas_formateadas.append({
                    "Día": dt_obj.strftime('%d/%m/%Y'),
                    "Hora": dt_obj.strftime('%H:%M'),
                    "Mascota": mascota_info.get('nombre', 'N/A'),
                    "Servicio": c['servicio'],
                    "Dueño": cliente_info.get('nombre_dueno', 'N/A'),
                    "Teléfono": cliente_info.get('telefono', 'N/A')
                })
                
            df_citas = pd.DataFrame(citas_formateadas)
            st.dataframe(df_citas, use_container_width=True, hide_index=True, height=400)
        else:
            st.info("No hay citas agendadas en el sistema.")