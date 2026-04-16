import streamlit as st
import pandas as pd
from postgrest import SyncPostgrestClient
from datetime import datetime
import streamlit.components.v1 as components

# --- PUERTA DE SEGURIDAD (CANDADO) ---
if "acceso_concedido" not in st.session_state:
    st.session_state.acceso_concedido = False

if not st.session_state.acceso_concedido:
    st.markdown("<h1 style='text-align: center;'>🔒 Acceso Restringido</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        clave = st.text_input("Introduce la contraseña de la tienda:", type="password")
        if st.button("Entrar al TPV", use_container_width=True):
            if clave == st.secrets["password"]:
                st.session_state.acceso_concedido = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta. Inténtalo de nuevo.")
    st.stop() # Esto es la magia: oculta todo lo de abajo hasta poner la clave correcta
# -------------------------------------

# --- 1. CONFIGURACIÓN ---
url = "https://zpzhsmyyyfxqbjjiuana.supabase.co" 
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwemhzbXl5eWZ4cWJqaml1YW5hIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxMDMwMTYsImV4cCI6MjA5MTY3OTAxNn0.SY-y9w7X6fgXzvIMvQ-t0Ppyyj1b9Gaxu-FRgOgDuD8"

headers = {"apikey": key, "Authorization": f"Bearer {key}"}
client = SyncPostgrestClient(f"{url}/rest/v1", headers=headers)

# --- ESTADOS DE LA SESIÓN ---
if 'carrito' not in st.session_state: st.session_state['carrito'] = []
if 'ticket_html' not in st.session_state: st.session_state['ticket_html'] = None
if 'paso_final' not in st.session_state: st.session_state['paso_final'] = False
if 'datos_ultima_venta' not in st.session_state: st.session_state['datos_ultima_venta'] = {}

st.set_page_config(page_title="PetShop Canarias 2026", layout="wide", page_icon="🐾")

# --- 🌟 MAGIA CSS ---
st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; padding-left: 1rem !important; padding-right: 1rem !important; max-width: 100% !important; }
        header {visibility: hidden;} footer {visibility: hidden;}
        .stTabs [data-baseweb="tab-list"] { margin-bottom: 0rem; }
    </style>
""", unsafe_allow_html=True)

# --- LOGO Y TÍTULO ---
col_logo, col_titulo = st.columns([1, 8], vertical_alignment="center")
with col_logo: st.image("LOGO.jpg", use_container_width=True)
with col_titulo: st.title("TPV Mascotas Pro")

tab1, tab2, tab3, tab4 = st.tabs(["📦 Productos", "✂️ Servicios", "🛒 Caja de Cobro", "📊 Historial"])

# --- FUNCIONES DE APOYO ---
def enviar_ticket_email(email_destino, contenido_html):
    # Aquí es donde conectarías con tu servidor de correo (Gmail, etc.)
    # Por ahora, simulamos el envío para que el flujo funcione.
    st.toast(f"📧 Ticket enviado a: {email_destino}", icon="✅")

# --- TAB 1 y 2 (Gestión) --- (Mantenemos igual para no perder stock)
with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.header("Añadir Producto")
        with st.form("nuevo_prod", clear_on_submit=True):
            cod_barras = st.text_input("📷 Código de Barras")
            nombre = st.text_input("Nombre")
            cat = st.selectbox("Categoría", ["Alimentación", "Higiene", "Accesorios"])
            precio_venda = st.number_input("Precio PVP (€)", min_value=0.0, step=0.1)
            stock = st.number_input("Stock", min_value=0)
            if st.form_submit_button("Guardar"):
                client.table("productos_y_servicios").insert({"codigo_barras": cod_barras, "nombre": nombre, "categoria": cat, "precio_pvp": precio_venda, "stock_actual": stock}).execute()
                st.success("Guardado.")
    with col2:
        res = client.table("productos_y_servicios").select("*").neq("categoria", "Peluquería").execute()
        if res.data: st.dataframe(pd.DataFrame(res.data)[['codigo_barras', 'nombre', 'precio_pvp', 'stock_actual']])

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

# --- TAB 3: CAJA CON ELECCIÓN DE TICKET ---
with tab3:
    # ESCENARIO A: PANTALLA DE ELECCIÓN POST-VENTA
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

    # ESCENARIO B: CAJA NORMAL (FLUJO DE COBRO)
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
                            # 1. Guardar en Supabase
                            client.table("ventas_historial").insert({
                                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"), "resumen": f"{len(edited_df)} art.",
                                "total": total_final, "pago_efectivo": p_efe, "pago_tarjeta": p_tar, "pago_bizum": p_biz,
                                "deuda": deuda, "notas": notas_cliente
                            }).execute()

                            # 2. Bajar stock y preparar HTML del ticket
                            items_html = ""
                            for _, fila in edited_df.iterrows():
                                precio_lin = fila['Cantidad'] * fila['Precio Un.']
                                items_html += f"<tr><td>{fila['Cantidad']}x</td><td>{fila['Artículo'][:18]}</td><td style='text-align:right'>{precio_lin:.2f}€</td></tr>"
                                if fila['cod'] not in ["SERVICIO", "MANUAL"]:
                                    res_st = client.table("productos_y_servicios").select("stock_actual").eq("codigo_barras", fila['cod']).execute()
                                    if res_st.data:
                                        client.table("productos_y_servicios").update({"stock_actual": max(0, res_st.data[0]['stock_actual'] - fila['Cantidad'])}).eq("codigo_barras", fila['cod']).execute()
                            
                            # Generamos el ticket HTML
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
                            st.session_state['paso_final'] = True # Saltamos a la pantalla de opciones
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
