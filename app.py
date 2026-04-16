import streamlit as st
import pandas as pd
from postgrest import SyncPostgrestClient
from datetime import datetime
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Animalarium TPV", layout="wide")

# --- CSS SEGURO (Sin márgenes negativos que escondan el texto) ---
st.markdown("""
    <style>
        /* Reducimos el espacio superior al mínimo seguro */
        .block-container {
            padding-top: 1.8rem !important;
            padding-bottom: 0rem !important;
        }
        /* Títulos principales más pequeños */
        h1 {
            font-size: 1.8rem !important;
            margin-bottom: 0px !important;
        }
        /* Títulos de las columnas (h3) más compactos */
        h3 {
            font-size: 1.2rem !important;
            margin-top: -10px !important;
            margin-bottom: 5px !important;
        }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MEMORIA DE LA CAJA (SESSION STATE) ---
if 'carrito' not in st.session_state:
    st.session_state['carrito'] = []
if 'paso_final' not in st.session_state:
    st.session_state['paso_final'] = False
if 'ticket_html' not in st.session_state:
    st.session_state['ticket_html'] = None
if "acceso_concedido" not in st.session_state:
    st.session_state.acceso_concedido = False

# --- 3. PUERTA DE SEGURIDAD (CANDADO) ---
if not st.session_state.acceso_concedido:
    # Usamos st.header en lugar de h1 manual para que sea más estable
    st.header("🔒 Acceso Restringido")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        clave = st.text_input("Introduce la contraseña de la tienda:", type="password")
        if st.button("Entrar al TPV", use_container_width=True):
            if clave == st.secrets["password"]:
                st.session_state.acceso_concedido = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
    st.stop()

# --- 4. CONEXIÓN A LA BASE DE DATOS ---
try:
    client = SyncPostgrestClient(
        f"{st.secrets['url']}/rest/v1", 
        headers={
            "apikey": st.secrets['key'],
            "Authorization": f"Bearer {st.secrets['key']}"
        }
    )
except Exception as e:
    st.error("Error en las llaves de los Secrets")
    st.stop()

# --- 5. CABECERA COMPACTA (LOGO Y TÍTULO ALINEADOS) ---
# Creamos las columnas y forzamos que el contenido se alinee al centro verticalmente
col_logo, col_titulo = st.columns([1, 10], vertical_alignment="center")

with col_logo:
    try:
        # Ajustamos el ancho para que no "empuje" al título fuera de la fila
        st.image("LOGO.jpg", width=65) 
    except:
        st.write("🐾")

with col_titulo:
    # Usamos un estilo de título que no tenga márgenes extra
    st.markdown(
        "<h1 style='margin: 0; padding: 0;'>Animalarium - TPV</h1>", 
        unsafe_allow_html=True
    )

# --- 5. PESTAÑAS ---
tab1, tab2, tab3, tab4 = st.tabs(["📦 Productos", "✂️ Servicios", "🛒 Caja de Cobro", "📊 Historial"])

# --- FUNCIONES DE APOYO ---
def enviar_ticket_email(email_destino, contenido_html):
    st.toast(f"📧 Ticket enviado a: {email_destino}", icon="✅")

# --- TAB 1: PRODUCTOS ---
with tab1:
    # Ajustamos proporciones
    col_form, col_tabla = st.columns([1.1, 2.5]) 

    with col_form:
        st.markdown("### 📝 Nuevo Producto") # Título más pequeño
        with st.form("nuevo_prod", clear_on_submit=True):
            nombre = st.text_input("Nombre", placeholder="Producto...")
            
            f2_c1, f2_c2 = st.columns(2)
            with f2_c1:
                cod_barras = st.text_input("📷 Código")
            with f2_c2:
                cat = st.selectbox("Categoría", ["Alimentación", "Higiene", "Accesorios", "Varios"])
            
            f3_c1, f3_c2 = st.columns(2)
            with f3_c1:
                p_compra_neto = st.number_input("Coste Neto", min_value=0.0, step=0.1)
            with f3_c2:
                valor_tipo_igic = st.selectbox("IGIC %", [7, 0, 3, 15])
            
            f4_c1, f4_c2 = st.columns(2)
            with f4_c1:
                p_venda = st.number_input("PVP Final", min_value=0.0, step=0.1)
            with f4_c2:
                stock = st.number_input("Stock", min_value=0)
            
            if st.form_submit_button("🚀 GUARDAR", use_container_width=True):
                client.table("productos_y_servicios").insert({
                    "codigo_barras": cod_barras, 
                    "nombre": nombre, 
                    "categoria": cat, 
                    "precio_compra": p_compra_neto, 
                    "precio_pvp": p_venda, 
                    "tipo_igic": valor_tipo_igic,
                    "stock_actual": stock
                }).execute()
                st.success("✅ Hecho")
                st.rerun()

    with col_tabla:
        st.markdown("### 📦 Inventario")
        res = client.table("productos_y_servicios").select("*").execute()
        
        if res.data:
            df = pd.DataFrame(res.data)
            columnas_visibles = {
                "codigo_barras": "Cód",
                "nombre": "Producto",
                "precio_compra": "Coste",
                "tipo_igic": "%",
                "precio_pvp": "PVP",
                "stock_actual": "Stock"
            }
            df_ver = df[list(columnas_visibles.keys())].rename(columns=columnas_visibles)
            
            # --- CAMBIO CLAVE: Altura reducida a 380 para que no lo tape el botón de Streamlit ---
            st.dataframe(df_ver, use_container_width=True, hide_index=True, height=380)
        else:
            st.info("Vacío")
# --- TAB 2: SERVICIOS ---
with tab2:
    col_s1, col_s2 = st.columns([1, 2])
    with col_s1:
        st.header("Nuevo Servicio")
        with st.form("nuevo_serv", clear_on_submit=True):
            nombre_s = st.text_input("Nombre Servicio")
            precio_f = st.number_input("Precio PVP", min_value=0.0, step=0.1)
            if st.form_submit_button("Guardar Servicio"):
                client.table("productos_y_servicios").insert({"nombre": nombre_s, "categoria": "Peluquería", "precio_pvp": precio_f, "stock_actual": 0, "codigo_barras": "SERVICIO"}).execute()
                st.success("Servicio Guardado.")
    with col_s2:
        res_s = client.table("productos_y_servicios").select("*").eq("categoria", "Peluquería").execute()
        if res_s.data: st.dataframe(pd.DataFrame(res_s.data)[['nombre', 'precio_pvp']])

# --- TAB 3: CAJA DE COBRO ---
with tab3:
    if st.session_state['paso_final']:
        st.balloons()
        st.success("💰 ¡VENTA FINALIZADA CON ÉXITO!")
        c_fin1, c_fin2, c_fin3 = st.columns(3)
        with c_fin1:
            if st.button("🚫 SIN TICKET / SIGUIENTE", use_container_width=True):
                st.session_state['paso_final'] = False
                st.session_state['ticket_html'] = None
                st.session_state['carrito'] = []
                st.rerun()
        with c_fin2:
            st.info("🖨️ Opción Papel")
            if st.session_state['ticket_html']:
                components.html(st.session_state['ticket_html'], height=350, scrolling=True)
            if st.button("Finalizar y Limpiar", use_container_width=True):
                st.session_state['paso_final'] = False
                st.session_state['carrito'] = []
                st.rerun()
        with c_fin3:
            st.info("📧 Opción Digital")
            email_cli = st.text_input("Correo electrónico del cliente")
            if st.button("Enviar por Email"):
                if "@" in email_cli:
                    enviar_ticket_email(email_cli, st.session_state['ticket_html'])
                    st.session_state['paso_final'] = False
                    st.session_state['carrito'] = []
                    st.rerun()
                else:
                    st.error("Introduce un email válido.")
    else:
        try:
            res_cat = client.table("productos_y_servicios").select("*").gt("precio_pvp", 0).order("nombre").execute()
            productos_db = res_cat.data if res_cat.data else []
        except: productos_db = []

        opciones_buscador = [f"{p['nombre']} | {p['precio_pvp']}€" for p in productos_db]
        diccionario_items = {f"{p['nombre']} | {p['precio_pvp']}€": p for p in productos_db}

        col_ticket, col_controles = st.columns([2, 1])

        with col_controles:
            st.markdown("### 🔍 Buscador")
            
            # --- TRUCO DE FOCO AUTOMÁTICO ---
            components.html(
                """
                <script>
                var input = window.parent.document.querySelector('input[aria-label="1️⃣ Escáner (Cód. Barras)"]');
                input.focus();
                input.onblur = function() { setTimeout(function() { input.focus(); }, 100); };
                </script>
                """, height=0,
            )
            
            with st.form("form_omnibox", clear_on_submit=True):
                escaner = st.text_input("1️⃣ Escáner (Cód. Barras)")
                nombre_buscado = st.selectbox("2️⃣ Catálogo", options=[""] + opciones_buscador, index=0)
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1: nombre_manual = st.text_input("3️⃣ Artículo")
                with c2: precio_libre = st.number_input("Precio", min_value=0.0)
                with c3: cant_input = st.number_input("Cant.", min_value=1, value=1)
                
                btn_add = st.form_submit_button("➕ AÑADIR", type="primary", use_container_width=True)

                if btn_add:
                    item_data = None
                    if escaner:
                        res = client.table("productos_y_servicios").select("*").eq("codigo_barras", escaner).gt("precio_pvp", 0).execute()
                        if res.data: item_data = res.data[0]
                    elif nombre_buscado != "": item_data = diccionario_items[nombre_buscado]
                    elif nombre_manual and precio_libre > 0: item_data = {"nombre": f"Manual: {nombre_manual}", "precio_pvp": precio_libre, "categoria": "Venta Libre", "codigo_barras": "MANUAL"}
                    
                    if item_data:
                        st.session_state['carrito'].append({"Artículo": item_data['nombre'], "Precio Un.": float(item_data['precio_pvp']), "Cantidad": int(cant_input), "Desc %": 0.0, "cod": item_data['codigo_barras']})
                        st.rerun()

        with col_ticket:
            st.markdown("### 🧾 Ticket y Cobro")
            if not st.session_state['carrito']:
                st.info("Caja lista para nueva venta.")
            else:
                df_editor = pd.DataFrame(st.session_state['carrito'])
                edited_df = st.data_editor(df_editor, height=150, column_config={"Precio Un.": st.column_config.NumberColumn(format="%.2f €"), "cod": None}, use_container_width=True, num_rows="dynamic")
                st.session_state['carrito'] = edited_df.to_dict('records')
                subtotal = (edited_df['Precio Un.'] * edited_df['Cantidad'] * (1 - edited_df['Desc %']/100)).sum()

                cp_1, cp_2, cp_3, cp_4 = st.columns(4)
                with cp_1: desc_global = st.number_input("Desc. %", min_value=0, max_value=100)
                with cp_2: p_efe = st.number_input("Efectivo €", min_value=0.0, step=5.0)
                with cp_3: p_tar = st.number_input("Tarjeta €", min_value=0.0, step=5.0)
                with cp_4: p_biz = st.number_input("Bizum €", min_value=0.0, step=5.0)
                
                total_final = subtotal * (1 - desc_global/100)
                total_entregado = p_efe + p_tar + p_biz
                diferencia = total_entregado - total_final
                deuda = abs(diferencia) if diferencia < 0 else 0.0

                c_info, c_nota, c_btnok, c_btnno = st.columns([2, 1.5, 1.5, 1], vertical_alignment="bottom")
                with c_info:
                    st.metric("TOTAL", f"{total_final:.2f} €", delta=f"Cambio: {diferencia:.2f}€" if diferencia > 0 else None)
                with c_nota:
                    notas_cliente = st.text_input("Nombre / Notas", placeholder="Cliente")
                with c_btnok:
                    if st.button("✅ COBRAR", type="primary", use_container_width=True):
                        if deuda > 0 and not notas_cliente:
                            st.error("Falta nombre del deudor.")
                        else:
                            client.table("ventas_historial").insert({
                                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"), "resumen": f"{len(edited_df)} art.",
                                "total": total_final, "pago_efectivo": p_efe, "pago_tarjeta": p_tar, "pago_bizum": p_biz,
                                "deuda": deuda, "notas": notas_cliente
                            }).execute()

                            items_html = ""
                            for _, fila in edited_df.iterrows():
                                precio_lin = fila['Cantidad'] * fila['Precio Un.']
                                items_html += f"<tr><td>{fila['Cantidad']}x</td><td>{fila['Artículo'][:18]}</td><td style='text-align:right'>{precio_lin:.2f}€</td></tr>"
                                if fila['cod'] not in ["SERVICIO", "MANUAL"]:
                                    res_st = client.table("productos_y_servicios").select("stock_actual").eq("codigo_barras", fila['cod']).execute()
                                    if res_st.data:
                                        client.table("productos_y_servicios").update({"stock_actual": max(0, res_st.data[0]['stock_actual'] - fila['Cantidad'])}).eq("codigo_barras", fila['cod']).execute()
                            
                            fecha_str = datetime.now().strftime("%d/%m/%Y %H:%M")
                            st.session_state['ticket_html'] = f"""
                            <div style="font-family: 'Courier New'; font-size: 12px; width: 280px; padding: 10px; border: 1px solid #ddd;">
                                <h3 style="text-align:center">PETSHOP CANARIAS</h3>
                                <p style="text-align:center">{fecha_str}</p>
                                <hr>
                                <table style="width:100%">{items_html}</table>
                                <hr>
                                <p style="text-align:right"><b>TOTAL: {total_final:.2f} €</b></p>
                                <p style="text-align:center">¡Gracias por su visita!</p>
                                <button style="width:100%; padding:10px; background:#ad6e73; color:white; border:none; cursor:pointer;" onclick="window.print()">🖨️ IMPRIMIR AHORA</button>
                            </div>
                            """
                            st.session_state['paso_final'] = True
                            st.rerun()
                with c_btnno:
                    if st.button("🗑️ Anular", use_container_width=True):
                        st.session_state['carrito'] = []
                        st.rerun()

# --- TAB 4: HISTORIAL ---
with tab4:
    st.header("📊 Historial y Deudas")
    res_v = client.table("ventas_historial").select("*").execute()
    if res_v.data:
        df_v = pd.DataFrame(res_v.data).iloc[::-1]
        st.dataframe(df_v[['fecha', 'total', 'pago_efectivo', 'pago_tarjeta', 'pago_bizum', 'deuda', 'notas']], use_container_width=True)
        c_tot1, c_tot2 = st.columns(2)
        c_tot1.metric("Total Caja (Efectivo)", f"{df_v['pago_efectivo'].sum():.2f} €")
        c_tot2.metric("Total Deudas", f"{df_v['deuda'].sum():.2f} €", delta_color="inverse")