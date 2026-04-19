import streamlit as st
import pandas as pd
from postgrest import SyncPostgrestClient
from datetime import datetime
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

# 🚨 DEFINICIÓN CORRECTA DE LAS 11 PESTAÑAS 🚨
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
    "📦 Inventario", "🛒 Caja", "👥 Clientes", "📜 Historial", 
    "💰 Control Caja", "📈 Estadísticas", "🚚 Proveedores", "📑 Facturación", "⚙️ Admin",
    "📊 Contabilidad", "📅 Agenda"
])

# ==========================================
# --- TAB 1: INVENTARIO MULTI-PROVEEDOR ---
# ==========================================
with tab1:
    col_f, col_t = st.columns([1.2, 2.5])
    
    # 1. Obtenemos los proveedores
    res_proveedores = client.table("proveedores").select("id, nombre_empresa").execute()
    dict_proveedores = {p['nombre_empresa']: p['id'] for p in res_proveedores.data} if res_proveedores.data else {}
    lista_nombres_prov = list(dict_proveedores.keys())

    with col_f:
        st.markdown("### 📝 Nuevo Producto")
        # El bloque WITH ST.FORM empieza aquí
        with st.form("nuevo_p", clear_on_submit=True):
            nombre = st.text_input("Nombre *")
            c1, c2 = st.columns(2)
            with c1: sku = st.text_input("SKU / Código *")
            with c2: cat = st.selectbox("Categoría", ["Producto", "Servicio"])
            
            c3, c4 = st.columns(2)
            with c3: p_base = st.number_input("Coste Neto Base (€)", min_value=0.0, format="%.2f")
            with c4: igic_tipo = st.selectbox("IGIC %", [7.00, 0.00, 3.00, 15.00])
            
            # Cálculo visual de coste (se actualiza al procesar)
            coste_con_igic = p_base * (1 + (igic_tipo / 100))
            st.markdown(f"<p style='margin:0; color:#005275; font-size: 13px;'><b>💰 Coste Total (Neto + IGIC): {coste_con_igic:.2f} €</b></p>", unsafe_allow_html=True)
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            
            c5, c6 = st.columns(2)
            with c5: pvp = st.number_input("PVP Final (€)", min_value=0.0, format="%.2f")
            with c6: stck = st.number_input("Stock Inicial", min_value=0)
            
            provs_seleccionados = st.multiselect("Proveedor/es", lista_nombres_prov, placeholder="Elige uno o varios...")
            
            # ESTE BOTÓN AHORA ESTÁ PERFECTAMENTE INDENTADO DENTRO DEL FORMULARIO
            if st.form_submit_button("💾 Guardar Producto", use_container_width=True):
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
                    st.warning("Faltan datos obligatorios (Nombre o SKU)")

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
            
            # Mostramos las columnas ordenadas
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
# --- TAB 4: HISTORIAL OPERATIVO (VENTAS Y CAJAS) ---
# ==========================================
with tab4:
    st.markdown("<h3 style='margin-top: -15px; margin-bottom: 5px;'>📜 Historial de Operaciones</h3>", unsafe_allow_html=True)
    
    sub_h_ventas, sub_h_cajas = st.tabs(["🛒 Tickets y Ventas", "🔒 Cierres de Caja"])
    
    # --- 1. HISTORIAL DE VENTAS Y TICKETS ---
    with sub_h_ventas:
        c_fv1, c_fv2 = st.columns(2)
        with c_fv1: f_inicio_v = st.date_input("Ventas desde:", value=pd.to_datetime('today') - pd.Timedelta(days=7), key="fv1")
        with c_fv2: f_fin_v = st.date_input("Ventas hasta:", value=pd.to_datetime('today'), key="fv2")

        try:
            res_v = client.table("ventas_historial").select("*").gte("created_at", f"{f_inicio_v}T00:00:00").lte("created_at", f"{f_fin_v}T23:59:59").order("id", desc=True).execute()
            
            if res_v.data:
                df_v = pd.DataFrame(res_v.data)
                try: df_v['Fecha'] = pd.to_datetime(df_v['created_at']).dt.strftime('%d/%m/%Y %H:%M')
                except: df_v['Fecha'] = "---"
                
                for col in ['metodo_pago', 'estado', 'cliente_deuda']:
                    if col not in df_v.columns: df_v[col] = "N/A"

                df_vista = df_v[['id', 'Fecha', 'total', 'metodo_pago', 'estado', 'cliente_deuda']].copy()
                
                st.markdown("💡 *Puedes editar Método, Estado o Cliente haciendo doble clic.*")
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
                
                if st.button("💾 Guardar Cambios en Tickets", type="primary"):
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
        except Exception as e: st.error(f"Error cargando ventas: {e}")

    # --- 2. HISTORIAL DE CAJAS Y CIERRES Z ---
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
                    
                    # Generar Ticket HTML para imprimir
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

                    # Mostrar tabla de movimientos abajo para ver los motivos
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
                    # 1. Calcular Ingresos y Salidas manuales
                    ingresos = sum(m['cantidad'] for m in res_movs.data if m['tipo'] == 'Ingreso') if res_movs.data else 0.0
                    retiradas = sum(m['cantidad'] for m in res_movs.data if m['tipo'] == 'Retirada') if res_movs.data else 0.0
                    
                    # 2. Calcular Ventas por Método desde la apertura de esta caja
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
                                    except: pass # Evita cuelgues si el texto mixto es raro
                    
                    # 3. Calcular el Descuadre (Lo que debería haber vs Lo que contaste)
                    efectivo_teorico_en_caja = fondo_actual + t_efe + ingresos - retiradas
                    descuadre = efectivo_final - efectivo_teorico_en_caja
                    
                    # 4. Preparar el JSON con el desglose para guardarlo
                    resumen_json = {
                        "Efectivo": round(t_efe, 2), "Tarjeta": round(t_tar, 2), "Bizum": round(t_biz, 2),
                        "Ingresos": round(ingresos, 2), "Retiradas": round(retiradas, 2)
                    }
                    
                    # 5. Guardar en Supabase
                    client.table("control_caja").update({
                        "estado": "Cerrada", 
                        "total_contado": float(efectivo_final), 
                        "descuadre": float(descuadre),
                        "resumen_pagos": resumen_json
                    }).eq("id", id_caja).execute()
                    
                    st.success(f"Caja Cerrada. Descuadre: {descuadre:.2f}€")
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

# --- TAB 7: PROVEEDORES (AMPLIADO) ---
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
                        "nombre_empresa": n_emp, "contacto": f"Tel: {n_tel} | Email: {n_ema} | Dir: {n_dir} | CIF: {n_cif} | IBAN: {n_iban}"
                    }).execute()
                    st.success("Guardado"); time.sleep(0.5); st.rerun()
    with cp2:
        res_p = client.table("proveedores").select("*").execute()
        if res_p.data:
            st.dataframe(pd.DataFrame(res_p.data)[['nombre_empresa', 'contacto']], use_container_width=True, hide_index=True)

# ==========================================
# --- TAB 8: FACTURACIÓN Y GESTIÓN DE STOCK ---
# ==========================================
with tab8:
    st.markdown("<h3 style='margin-top: -15px;'>📑 Gestión de Facturas y Stock</h3>", unsafe_allow_html=True)
    
    # Creamos las dos sub-pestañas internas
    sub_f_ventas, sub_f_compras = st.tabs(["🛒 Emitir Venta (Cliente)", "🚚 Registrar Compra (Proveedor)"])

    # Obtenemos los productos una sola vez para ambas secciones
    res_inv = client.table("productos").select("*").execute()
    df_inv = pd.DataFrame(res_inv.data) if res_inv.data else pd.DataFrame()

    # --- 1. SUB-PESTAÑA: VENTAS (Para Clientes) ---
    with sub_f_ventas:
        st.markdown("#### 🔍 1. Crear Factura para Cliente")
        
        if 'factura_temporal' not in st.session_state: st.session_state.factura_temporal = []

        if not df_inv.empty:
            opciones_v = df_inv.apply(lambda x: f"{x['nombre']} | SKU: {x['sku']} | {x['precio_pvp']}€", axis=1).tolist()
            
            c_v1, c_v2, c_v3 = st.columns([2, 1, 1])
            with c_v1: 
                prod_v = st.selectbox("Buscar producto:", opciones_v, index=None, placeholder="Escribe o escanea...", key="busq_v_f")
            with c_v2: 
                cant_v = st.number_input("Cantidad", min_value=1, value=1, key="cant_v_f")
            with c_v3:
                if st.button("➕ Añadir a Factura", use_container_width=True, key="btn_v_f"):
                    if prod_v:
                        sku_f = prod_v.split("SKU: ")[1].split(" | ")[0]
                        datos_p = df_inv[df_inv['sku'] == sku_f].iloc[0]
                        st.session_state.factura_temporal.append({
                            "id": datos_p['id'], "Producto": datos_p['nombre'], "SKU": sku_f,
                            "Cantidad": cant_v, "Precio_PVP": float(datos_p['precio_pvp']),
                            "IGIC_Tipo": float(datos_p['igic_tipo']), "Subtotal": cant_v * float(datos_p['precio_pvp'])
                        })
                        st.rerun()

        # Detalle de la factura de venta
        if st.session_state.factura_temporal:
            st.markdown("---")
            df_fv = pd.DataFrame(st.session_state.factura_temporal)
            st.dataframe(df_fv[['Producto', 'Cantidad', 'Subtotal']], use_container_width=True, hide_index=True)
            
            total_v = df_fv['Subtotal'].sum()
            base_v = sum(item['Subtotal'] / (1 + (item['IGIC_Tipo']/100)) for item in st.session_state.factura_temporal)
            igic_v = total_v - base_v
            
            st.info(f"**Base:** {base_v:.2f}€ | **IGIC:** {igic_v:.2f}€ | **TOTAL VENTA:** {total_v:.2f}€")

            res_cli = client.table("clientes").select("id, nombre_dueno, telefono").execute()
            dict_cli = {f"{c['nombre_dueno']} ({c['telefono']})": c['id'] for c in res_cli.data} if res_cli.data else {}
            f_cliente = st.selectbox("Facturar a:", list(dict_cli.keys()), placeholder="Selecciona cliente...")

            if st.button("🚀 EMITIR FACTURA Y RESTAR STOCK", type="primary", use_container_width=True):
                if f_cliente:
                    # 1. Guardar factura
                    client.table("facturas").insert({
                        "cliente_id": dict_cli[f_cliente], "total_neto": float(base_v),
                        "total_igic": float(igic_v), "total_final": float(total_v)
                    }).execute()
                    # 2. Restar Stock
                    for item in st.session_state.factura_temporal:
                        res_st = client.table("productos").select("stock_actual").eq("id", item['id']).execute()
                        n_st = res_st.data[0]['stock_actual'] - item['Cantidad']
                        client.table("productos").update({"stock_actual": n_st}).eq("id", item['id']).execute()
                    
                    st.session_state.factura_temporal = []
                    st.success("Factura emitida y stock descontado."); time.sleep(1); st.rerun()
        else:
            st.write("El borrador de venta está vacío.")

    # --- 2. SUB-PESTAÑA: COMPRAS (Para Proveedores y Entradas) ---
    with sub_f_compras:
        st.markdown("#### 📥 2. Entrada de Mercadería (Suma Stock)")
        
        if 'entrada_temporal' not in st.session_state: st.session_state.entrada_temporal = []

        # Escáner/Buscador para compras
        col_c1, col_c2, col_c3 = st.columns([2, 1, 1])
        with col_c1:
            prod_c = st.selectbox("Escribe o Escanea para COMPRA:", 
                                 df_inv.apply(lambda x: f"{x['nombre']} | SKU: {x['sku']}", axis=1).tolist() if not df_inv.empty else [],
                                 index=None, placeholder="Pistola lista...", key="scan_c_f")
        with col_c2:
            cant_c = st.number_input("Cantidad Recibida", min_value=1, value=1, key="cant_c_f")
        with col_c3:
            if st.button("➕ Añadir a Entrada", use_container_width=True, key="btn_c_f"):
                if prod_c:
                    sku_c = prod_c.split("SKU: ")[1]
                    datos_p = df_inv[df_inv['sku'] == sku_c].iloc[0]
                    st.session_state.entrada_temporal.append({
                        "id": datos_p['id'], "Producto": datos_p['nombre'], "SKU": sku_c,
                        "Cantidad": cant_c, "Coste_Base": float(datos_p['precio_base']),
                        "Subtotal": cant_c * float(datos_p['precio_base'])
                    })
                    st.rerun()

        # Crear producto "Al Vuelo"
        with st.expander("✨ ¿Producto nuevo que no tienes en inventario? Créalo aquí"):
            with st.form("nuevo_p_express", clear_on_submit=True):
                st.write("Rellena para añadirlo a la factura y al inventario a la vez:")
                en_nom = st.text_input("Nombre *")
                en_sku = st.text_input("SKU / Código *")
                ec1, ec2, ec3 = st.columns(3)
                with ec1: en_coste = st.number_input("Coste Neto (€)", min_value=0.0)
                with ec2: en_igic = st.selectbox("IGIC %", [7.0, 0.0, 3.0, 15.0])
                with ec3: en_pvp = st.number_input("PVP Venta (€)", min_value=0.0)
                
                if st.form_submit_button("💾 Crear y añadir a esta factura"):
                    if en_nom and en_sku:
                        res_new = client.table("productos").insert({
                            "nombre": en_nom, "sku": en_sku, "precio_base": en_coste, 
                            "igic_tipo": en_igic, "precio_pvp": en_pvp, "stock_actual": 0
                        }).execute()
                        if res_new.data:
                            st.session_state.entrada_temporal.append({
                                "id": res_new.data[0]['id'], "Producto": en_nom, "SKU": en_sku,
                                "Cantidad": 1, "Coste_Base": en_coste, "Subtotal": en_coste
                            })
                            st.success("Producto creado."); time.sleep(1); st.rerun()

        # Detalle de la entrada de stock
        if st.session_state.entrada_temporal:
            st.markdown("---")
            df_ec = pd.DataFrame(st.session_state.entrada_temporal)
            st.dataframe(df_ec[['Producto', 'Cantidad', 'Subtotal']], use_container_width=True, hide_index=True)
            
            res_p = client.table("proveedores").select("id, nombre_empresa").execute()
            dict_p = {p['nombre_empresa']: p['id'] for p in res_p.data} if res_p.data else {}
            prov_sel = st.selectbox("Proveedor de esta compra:", list(dict_p.keys()), key="prov_c_f")

            if st.button("🚀 REGISTRAR COMPRA Y SUMAR STOCK", type="primary", use_container_width=True, key="btn_final_c"):
                if prov_sel:
                    # 1. Guardar en compras (Contabilidad)
                    total_c = df_ec['Subtotal'].sum()
                    client.table("compras").insert({
                        "proveedor_id": dict_p[prov_sel], "tipo": "Mercadería",
                        "total": float(total_c), "estado": "Pagado"
                    }).execute()
                    # 2. Sumar Stock
                    for item in st.session_state.entrada_temporal:
                        res_curr = client.table("productos").select("stock_actual").eq("id", item['id']).execute()
                        n_st = res_curr.data[0]['stock_actual'] + item['Cantidad']
                        client.table("productos").update({"stock_actual": n_st}).eq("id", item['id']).execute()
                    
                    st.session_state.entrada_temporal = []
                    st.success("¡Stock aumentado y factura registrada!"); time.sleep(1); st.rerun()

# --- TAB 9: ADMIN (EDICIÓN ACTIVA) ---
with tab9:
    st.markdown("### ⚙️ Editor Maestro de Datos")
    t_sel = st.selectbox("Tabla:", ["productos", "clientes", "proveedores", "facturas"])
    
    res = client.table(t_sel).select("*").execute()
    if res.data:
        df_admin = pd.DataFrame(res.data)
        
        # CONFIGURACIÓN ESPECIAL PARA PRODUCTOS
        col_config = {}
        if t_sel == "productos":
            col_config = {
                "igic_tipo": st.column_config.SelectboxColumn("IGIC %", options=[0, 3, 7, 15], required=True),
                "precio_base": st.column_config.NumberColumn("Base (€)", format="%.2f"),
                "precio_pvp": st.column_config.NumberColumn("PVP (€)", format="%.2f"),
                "stock_actual": st.column_config.NumberColumn("Stock", step=1)
            }

        edited_db = st.data_editor(df_admin, use_container_width=True, hide_index=True, column_config=col_config, key="db_editor")

        if st.button("💾 GUARDAR CAMBIOS EN LA BASE DE DATOS"):
            # Aquí va la lógica que compara y actualiza en Supabase
            for index, row in edited_db.iterrows():
                client.table(t_sel).update(row.to_dict()).eq("id", row["id"]).execute()
            st.success("Base de datos actualizada correctamente")

# ==========================================
# --- TAB 10: CONTABILIDAD Y ARCHIVO ---
# ==========================================
with tab10:
    st.markdown("<h3 style='margin-bottom: 5px;'>📊 Contabilidad y Archivo Documental</h3>", unsafe_allow_html=True)
    
    sub_fungible, sub_archivo, sub_balance = st.tabs(["🧾 Gastos Fungibles", "🗄️ Archivo de Facturas", "⚖️ Balance Global"])

    # --- 1. GESTIÓN DE GASTOS FUNGIBLES (Lo que ya teníamos) ---
    with sub_fungible:
        # (Aquí mantienes el código de los gastos operativos/limpieza que pusimos antes)
        pass

    # --- 2. ARCHIVO DOCUMENTAL (NUEVO: El corazón de tus documentos) ---
    with sub_archivo:
        st.markdown("#### 📂 Buscador de Facturas Emitidas y Recibidas")
        
        c_af1, c_af2, c_af3 = st.columns([1, 1, 1])
        with c_af1: tipo_doc = st.selectbox("Tipo de documento:", ["Facturas de Venta (Clientes)", "Facturas de Compra (Proveedores)"])
        with c_af2: f_desde = st.date_input("Desde:", value=pd.to_datetime('today') - pd.Timedelta(days=30))
        with c_af3: f_hasta = st.date_input("Hasta:", value=pd.to_datetime('today'))

        try:
            if tipo_doc == "Facturas de Venta (Clientes)":
                res_docs = client.table("facturas").select("*, clientes(nombre_dueno, email, telefono)").gte("created_at", f"{f_desde}T00:00:00").lte("created_at", f"{f_hasta}T23:59:59").order("id", desc=True).execute()
                nombre_col_entidad = "Cliente"
            else:
                res_docs = client.table("compras").select("*, proveedores(nombre_empresa)").gte("created_at", f"{f_desde}T00:00:00").lte("created_at", f"{f_hasta}T23:59:59").order("id", desc=True).execute()
                nombre_col_entidad = "Proveedor"

            if res_docs.data:
                df_docs = pd.DataFrame(res_docs.data)
                df_docs['Fecha'] = pd.to_datetime(df_docs['created_at']).dt.strftime('%d/%m/%Y')
                
                # Extraer nombre del cliente o proveedor
                if tipo_doc == "Facturas de Venta (Clientes)":
                    df_docs['Entidad'] = df_docs['clientes'].apply(lambda x: x['nombre_dueno'] if x else "N/A")
                    df_docs['Importe'] = df_docs['total_final']
                else:
                    df_docs['Entidad'] = df_docs['proveedores'].apply(lambda x: x['nombre_empresa'] if x else "Gasto General")
                    df_docs['Importe'] = df_docs['total']

                st.markdown("---")
                # Selector de factura para ver detalle
                doc_sel_id = st.selectbox("Selecciona una factura para gestionar:", df_docs['id'].tolist(), format_func=lambda x: f"Factura #{x} - {df_docs[df_docs['id']==x]['Entidad'].values[0]} ({df_docs[df_docs['id']==x]['Importe'].values[0]}€)")
                
                if doc_sel_id:
                    doc_data = df_docs[df_docs['id'] == doc_sel_id].iloc[0]
                    
                    # Panel de acciones
                    c_act1, c_act2 = st.columns(2)
                    
                    with c_act1:
                        # Botón de Impresión
                        html_factura = f"""
                        <script>
                        function imprimir() {{
                            var win = window.open('', '', 'height=700,width=700');
                            win.document.write('<html><head><title>Factura {doc_sel_id}</title></head><body>');
                            win.document.write('<h1>ANIMALARIUM</h1>');
                            win.document.write('<p><b>Factura Nº:</b> {doc_sel_id}</p>');
                            win.document.write('<p><b>Fecha:</b> {doc_data['Fecha']}</p>');
                            win.document.write('<p><b>{nombre_col_entidad}:</b> {doc_data['Entidad']}</p>');
                            win.document.write('<hr><h3>TOTAL: {doc_data['Importe']:.2f}€</h3>');
                            win.document.write('</body></html>');
                            win.document.close();
                            win.print();
                        }}
                        </script>
                        <button onclick="imprimir()" style="width:100%; padding:10px; background-color:#005275; color:white; border:none; border-radius:5px; cursor:pointer;">🖨️ Imprimir Factura</button>
                        """
                        components.html(html_factura, height=50)
                    
                    with c_act2:
                        # Botón de Email (Mailto)
                        email_dest = doc_data['clientes']['email'] if tipo_doc == "Facturas de Venta (Clientes)" and doc_data['clientes'] else ""
                        asunto = f"Factura {doc_sel_id} - Animalarium"
                        cuerpo = f"Hola {doc_data['Entidad']},\n\nAdjuntamos los detalles de su factura por importe de {doc_data['Importe']:.2f}€.\n\nSaludos,\nAnimalarium."
                        url_mail = f"mailto:{email_dest}?subject={urllib.parse.quote(asunto)}&body={urllib.parse.quote(cuerpo)}"
                        st.markdown(f'<a href="{url_mail}" target="_blank" style="text-decoration:none;"><button style="width:100%; padding:10px; background-color:#2e7d32; color:white; border:none; border-radius:5px; cursor:pointer;">✉️ Enviar por Email</button></a>', unsafe_allow_html=True)
            else:
                st.info("No se encontraron documentos en este rango.")
        except Exception as e:
            st.error(f"Error al consultar el archivo: {e}")

    # --- 3. BALANCE GLOBAL (Lo que ya teníamos) ---
    with sub_balance:
        # (Mantienes el código del balance de salud financiera que pusimos antes)
        pass

# ==========================================
# --- TAB 11: AGENDA Y CITAS ---
# ==========================================
with tab11:
    st.markdown("<h3 style='margin-bottom: 5px;'>📅 Agenda Animalarium</h3>", unsafe_allow_html=True)
    
    # Traemos las mascotas y sus dueños
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
                    # Combinamos fecha y hora para Supabase
                    fecha_hora_str = f"{fecha_c} {hora_c}"
                    client.table("citas").insert({
                        "mascota_id": dict_mascotas[mascota_sel],
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
        # Traemos las citas futuras ordenadas por fecha
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