import streamlit as st
import pandas as pd
import time
import json
from datetime import datetime
import streamlit.components.v1 as components

def render_pestana_tpv(client):
    # --- COMPROBACIÓN DE SEGURIDAD: CAJA ABIERTA ---
    res_caja_abierta = client.table("control_caja").select("id").eq("estado", "Abierta").execute()
    
    if not res_caja_abierta.data:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.error("#### 🔒 Terminal Bloqueado\n\n**La caja está actualmente cerrada.** El TPV se encuentra desactivado por seguridad.\n\n👉 Ve a la pestaña **💰 Control Caja** y abre un nuevo turno para poder registrar ventas y emitir tickets.")
        return # Cortamos aquí para que no se renderice absolutamente nada del TPV

    # --- LLAVE DINÁMICA PARA EL RESETEO AUTOMÁTICO ---
    if 'llave_busqueda_tpv' not in st.session_state: 
        st.session_state.llave_busqueda_tpv = 0
        
    st.markdown("""
        <div style='display: flex; justify-content: space-between; margin-top: 10px; margin-bottom: 10px; padding: 0 5px;'>
            <h4 style='margin:0; color: #333; white-space: nowrap;'>🛒 Terminal de Venta</h4>
            <h4 style='margin:0; color: #333; white-space: nowrap; padding-right: 10px;'>🛒 Tu Carrito</h4>
        </div>
    """, unsafe_allow_html=True)

    col_busqueda, col_carrito = st.columns([1, 1.4], gap="small")
    
    with col_busqueda:
        res_inv = client.table("productos").select("id, nombre, precio_pvp, stock_actual, sku, igic_tipo").execute()
        df_inv = pd.DataFrame(res_inv.data) if res_inv.data else pd.DataFrame()
        
        st.markdown("<p style='margin: 0; font-weight: bold; font-size: 13px;'>🔍 Buscar producto o servicio</p>", unsafe_allow_html=True)
        if not df_inv.empty:
            opciones = df_inv.apply(lambda x: f"{x['nombre']} | {x['precio_pvp']}€ (Stock: {x['stock_actual']})", axis=1).tolist()
            prod_sel = st.selectbox("s1", opciones, index=None, placeholder="Escribe para buscar...", label_visibility="collapsed", key=f"sb_n_{st.session_state.llave_busqueda_tpv}")
            if prod_sel:
                nombre_sel = prod_sel.split(" | ")[0]
                fila_p = df_inv[df_inv['nombre'] == nombre_sel].iloc[0]
                
                st.session_state.carrito.append({
                    "id": str(fila_p['id']), "Producto": fila_p['nombre'], "Cantidad": 1, "Precio": fila_p['precio_pvp'],
                    "Subtotal": 1 * float(fila_p['precio_pvp']), "IGIC": fila_p.get('igic_tipo', 7), "Manual": False
                })
                st.session_state.llave_busqueda_tpv += 1
                st.rerun()
        
        st.markdown("<hr style='margin: 5px 0px; border: none; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

        st.markdown("<p style='margin: 0; font-weight: bold; font-size: 13px;'>📇 Escáner de Pistola</p>", unsafe_allow_html=True)

        cp1, cp2 = st.columns([2, 1])
        with cp1: cod_leido = st.text_input("p1", placeholder="Esperando escaneo...", label_visibility="collapsed", key=f"input_pistola_{st.session_state.llave_busqueda_tpv}")
        with cp2: cant_p = st.number_input("p2", min_value=1, value=1, label_visibility="collapsed", key=f"cant_p_{st.session_state.llave_busqueda_tpv}")
        
        if cod_leido and not df_inv.empty:
            coincid = df_inv[df_inv['sku'] == cod_leido]
            if not coincid.empty:
                fila_pist = coincid.iloc[0]
                st.session_state.carrito.append({
                    "id": str(fila_pist['id']), "Producto": fila_pist['nombre'], "Cantidad": cant_p, "Precio": fila_pist['precio_pvp'],
                    "Subtotal": cant_p * float(fila_pist['precio_pvp']), "IGIC": fila_pist.get('igic_tipo', 7), "Manual": False
                })
                st.session_state.llave_busqueda_tpv += 1
                st.rerun()
            else:
                st.error(f"❌ Código no encontrado")
                time.sleep(1)
                st.session_state.llave_busqueda_tpv += 1
                st.rerun()

        st.markdown("<hr style='margin: 5px 0px; border: none; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

        st.markdown("<p style='margin: 0; font-weight: bold; font-size: 13px;'>✍️ Artículo manual</p>", unsafe_allow_html=True)
        with st.form("f_man", clear_on_submit=True, border=False):
            cm1, cm2, cm3 = st.columns([1.3, 1, 1]) 
            with cm1: m_nom = st.text_input("Artículo", placeholder="Nombre...", label_visibility="visible", key=f"m_nom_{st.session_state.llave_busqueda_tpv}")
            with cm2: m_pre = st.number_input("Precio €", min_value=0.0, step=0.1, format="%.2f", value=None, label_visibility="visible", key=f"m_pre_{st.session_state.llave_busqueda_tpv}")
            with cm3: m_can = st.number_input("Cant.", min_value=1, value=1, label_visibility="visible", key=f"m_can_{st.session_state.llave_busqueda_tpv}")
            if st.form_submit_button("➕ Añadir Manual al Carrito", use_container_width=True):
                if m_nom and m_pre is not None and m_pre >= 0:
                    st.session_state.carrito.append({
                        "Producto": m_nom, "Cantidad": m_can, "Precio": m_pre,
                        "Subtotal": m_can * float(m_pre), "IGIC": 0, "Manual": True
                    })
                    st.session_state.llave_busqueda_tpv += 1
                    st.rerun()

    with col_carrito:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        t = st.session_state.get('ticket_actual')
        if t:
            st.success("✅ Venta realizada con éxito")
            
            # --- LIMPIEZA DEL MÉTODO DE PAGO PARA TICKET/EMAIL ---
            metodo_display = t['metodo']
            if metodo_display.startswith("Tarjeta"):
                metodo_display = "Tarjeta"
            elif metodo_display.startswith("Mixto"):
                import re
                metodo_display = re.sub(r'\s-\s[^|]+', '', metodo_display)

            # --- PREPARACIÓN DEL EMAIL ---
            cuerpo_email = "Hola,\n\nGracias por su compra en Animalarium. Adjuntamos el detalle de su ticket:\n\n"
            for p in t['productos']:
                cuerpo_email += f"- {p['Cantidad']}x {p['Producto']}: {p['Subtotal']:.2f}€\n"
            
            desc_global = t.get('descuento_global', 0.0)
            if desc_global > 0:
                cuerpo_email += f"\nDescuento global aplicado: {desc_global}%\n"
                
            cuerpo_email += f"\nTOTAL PAGADO: {t['total']:.2f}€\n"
            cuerpo_email += f"MÉTODO DE PAGO: {metodo_display}\n"
            if t.get('cliente_fidel'):
                cuerpo_email += f"\n🌟 Puntos ganados hoy: +{t['puntos_ganados']}"
                cuerpo_email += f"\n🌟 Saldo actual: {t.get('nuevo_saldo', 0)} puntos\n"
                
            cuerpo_email += "\nPOLÍTICA DE DEVOLUCIÓN:\nPlazo de 14 días con ticket y embalaje original en perfecto estado.\n\nUn saludo."
            import urllib.parse
            body_encoded = urllib.parse.quote(cuerpo_email)

            import base64
            logo_html = ""
            try:
                with open("LOGO.jpg", "rb") as img_file:
                    b64_string = base64.b64encode(img_file.read()).decode('utf-8')
                    logo_html = f'<img src="data:image/jpeg;base64,{b64_string}" style="max-width: 200px; margin-bottom: 10px;"><br>'
            except:
                pass

            # --- TICKET PARA STAR MICRONICS PASS-PRNT ---
            html_ticket = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                body {{ margin: 0; padding: 0; font-family: sans-serif; background-color: #f8f9fa; }}
                #botones-container {{ display: flex; gap: 10px; padding: 10px; max-width: 350px; margin: 0 auto; justify-content: center; }}
                .btn-print {{ 
                    flex: 1; padding: 12px 5px; background-color: #005275; color: white; 
                    border: none; border-radius: 5px; cursor: pointer; 
                    font-weight: bold; font-size: 13px; width: 100%;
                }}
                .btn-email {{ background-color: #2e7d32; }}
                .escala-mini {{ zoom: 0.65; -moz-transform: scale(0.65); -moz-transform-origin: top center; padding-bottom: 20px; }}
                #ticket-impresion {{ display: block; border: 1px solid #ccc; padding: 15px; background-color: #fffaf0; width: 300px; margin: 0 auto; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }}
            </style>
            </head>
            <body>
            
            <div id="botones-container">
                <button class="btn-print" onclick="imprimirConStar()">🖨️ IMPRIMIR TICKET</button>
                <a href="mailto:?subject=Ticket%20de%20Compra%20-%20Animalarium&body={body_encoded}" target="_top" style="text-decoration: none; flex: 1;">
                    <button class="btn-print btn-email">✉️ ENVIAR EMAIL</button>
                </a>
            </div>

            <div class="escala-mini">
                <div id="ticket-impresion">
                <div style="text-align: center; font-family: monospace; width: 100%; font-size: 22px; color: black; font-weight: bold;">
                    {logo_html}
                    <b style="font-size: 34px;">ANIMALARIUM</b><br>
                    Raquel Trujillo Hernández<br>
                    DNI: 78854854K<br>
                    C/ José Hernández Alfonso, 26<br>
                    38009 S/C de Tenerife
                    <br><br>
                    <div style="text-align: left; font-size: 22px;">Fecha: {t['fecha']}</div>
                    <hr style="border-top: 2px dashed #000; margin: 10px 0px;">
                    <table style="width: 100%; font-size: 22px; text-align: left; font-weight: bold;">
            """
            
            for p in t['productos']:
                desc_item = p.get('Desc. %', p.get('Desc %', 0.0))
                if desc_item > 0:
                    precio_orig = p.get('Precio', 0.0) * p['Cantidad']
                    html_ticket += f"<tr><td style='padding-bottom: 0px;'>{p['Cantidad']}x {p['Producto']}</td><td style='text-align: right; padding-bottom: 0px;'><del>{precio_orig:.2f}€</del> {p['Subtotal']:.2f}€</td></tr>"
                    html_ticket += f"<tr><td colspan='2' style='font-size: 16px; padding-bottom: 5px; color: #555;'>  ↳ Dto. {desc_item}% aplicado</td></tr>"
                else:
                    html_ticket += f"<tr><td style='padding-bottom: 5px;'>{p['Cantidad']}x {p['Producto']}</td><td style='text-align: right; padding-bottom: 5px;'>{p['Subtotal']:.2f}€</td></tr>"

            html_ticket += """
                    </table>
                    <hr style="border-top: 2px dashed #000; margin: 10px 0px;">
            """
            
            if t.get('puntos_descontados', 0) > 0:
                descuento_pts_eur = t['puntos_descontados'] * 0.50
                html_ticket += f"<div style='text-align: right; font-size: 22px;'><b>Canjeo Puntos (-{t['puntos_descontados']} pts): -{descuento_pts_eur:.2f}€</b></div>"

            desc_global = t.get('descuento_global', 0.0)
            if desc_global > 0:
                subtotal_sin_desc = t['total'] / (1 - desc_global / 100) if (1 - desc_global / 100) > 0 else t['total']
                descuento_eur = subtotal_sin_desc - t['total']
                html_ticket += f"<div style='text-align: right; font-size: 22px;'>Subtotal: {subtotal_sin_desc:.2f}€</div>"
                html_ticket += f"<div style='text-align: right; font-size: 22px;'><b>Dto. Global ({desc_global}%): -{descuento_eur:.2f}€</b></div>"

            html_ticket += f"""
                    <div style="text-align: right; font-size: 28px;"><b>TOTAL: {t['total']:.2f}€</b></div>
                    <div style="font-size: 20px; text-align: left; margin-top: 10px;"><b>Método de pago:</b> {metodo_display}</div>
            """
            if t.get('cliente_fidel'):
                html_ticket += f"<div style='font-size:18px; text-align:center; margin-top:15px; border: 1px solid #000; padding: 5px;'><b>🌟 CLIENTE VIP: {t['cliente_fidel']}</b>"
                html_ticket += f"<br>Has ganado +{t['puntos_ganados']} puntos hoy!"
                html_ticket += f"<br>Saldo actual: {t.get('nuevo_saldo', 0)} puntos</div>"

            html_ticket += """
                    
                    <div style="font-size: 18px; color: #000; margin-top: 30px; text-align: center;">
                        <b>POLÍTICA DE DEVOLUCIÓN</b><br>
                        Plazo de 14 días con ticket y<br>
                        embalaje original en perfecto estado.
                    </div>
                </div>
            </div>
            </div>

            <script>
            function imprimirConStar() {
                var ticketHTML = document.getElementById('ticket-impresion').innerHTML;
                var fullHTML = "<!DOCTYPE html><html><head><meta charset='utf-8'></head><body style='margin:0; padding:0; background-color:white;'>" + ticketHTML + "</body></html>";
                var htmlCodificado = encodeURIComponent(fullHTML);
                var urlRetorno = window.location.href;
                try { if (window.top.location.href && window.top.location.href !== "about:blank") { urlRetorno = window.top.location.href.split('#')[0].split('?')[0] + '#_'; } } catch(e) {}
                var starURL = "starpassprnt://v1/print/nopreview?back=" + encodeURIComponent(urlRetorno) + "&html=" + htmlCodificado;
                window.location.href = starURL;
            }
            </script>
            
            </body>
            </html>
            """
            components.html(html_ticket, height=450, scrolling=True)
            
            c_nv = st.columns(1)[0]
            with c_nv:
                if st.button("🛒 Nueva Venta", use_container_width=True, type="primary"):
                    st.session_state.ticket_actual = None
                    st.session_state.llave_busqueda_tpv += 1
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
                    hide_index=True, use_container_width=True, num_rows="dynamic", height=250, key="ed_car_ticket"
                )
                
                if not edited_df.equals(df_car):
                    edited_df["Subtotal"] = (edited_df["Cantidad"] * edited_df["Precio"]) * (1 - edited_df["Desc. %"] / 100)
                    st.session_state.carrito = json.loads(edited_df.to_json(orient='records'))
                    st.rerun()

                st.markdown("<hr style='margin: 2px 0px; border: none; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

                sub_antes = edited_df["Subtotal"].sum()
                
                # --- FIDELIZACIÓN ---
                res_cli_puntos = client.table("clientes").select("id, nombre_dueno, puntos").execute()
                opc_cli = ["Ninguno (Venta Anónima)"] + [f"{c['nombre_dueno']} (Puntos: {c.get('puntos') or 0})" for c in res_cli_puntos.data] if res_cli_puntos.data else ["Ninguno (Venta Anónima)"]
                
                c_desc, c_fid = st.columns(2)
                with c_desc: desc_g = st.number_input("🎁 Descuento Global (%)", min_value=0, max_value=100, value=None, step=1)
                with c_fid: cliente_fidelidad = st.selectbox("🌟 Asociar Cliente (Puntos)", opc_cli)
                
                desc_g_val = float(desc_g or 0.0)
                total_f = sub_antes * (1 - desc_g_val / 100)
                
                # --- LÓGICA DE CANJEO DE PUNTOS ---
                desc_puntos_eur = 0.0
                puntos_a_descontar = 0
                if "Ninguno" not in cliente_fidelidad:
                    pts_str = cliente_fidelidad.split("(Puntos: ")[1].replace(")", "")
                    puntos_disp = int(pts_str) if pts_str.isdigit() else 0
                    if puntos_disp > 0:
                        max_descuento_eur = total_f * 0.50
                        max_puntos_permitidos = int(max_descuento_eur / 0.50)
                        puntos_a_usar = min(puntos_disp, max_puntos_permitidos)
                        eur_a_descontar = puntos_a_usar * 0.50
                        if puntos_a_usar > 0:
                            if st.checkbox(f"💳 Canjear {puntos_a_usar} puntos por -{eur_a_descontar:.2f}€ (Límite 50%)", value=False):
                                desc_puntos_eur = eur_a_descontar
                                puntos_a_descontar = puntos_a_usar
                
                total_f = total_f - desc_puntos_eur
                if total_f < 0: total_f = 0.0
                
                st.markdown("<hr style='margin: 2px 0px; border: none; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

                res_b_radio = client.table("cuentas_bancarias").select("id, nombre_banco, saldo_actual").execute()
                lista_bancos = res_b_radio.data if res_b_radio.data else []
                nombres_tarjetas = [f"Tarjeta ({b['nombre_banco']})" for b in lista_bancos] if lista_bancos else ["Tarjeta"]
                
                opciones_pago = ["Efectivo"] + nombres_tarjetas + ["Bizum", "Mixto"]
                metodo = st.radio("p", opciones_pago, horizontal=True, label_visibility="collapsed")
                pagado_hoy = 0.0; pendiente = 0.0; metodo_log = metodo
                p_efectivo = 0.0; p_tarjeta = 0.0; p_bizum = 0.0

                banco_sel_nombre = ""
                banco_sel_id = None
                banco_sel_saldo = 0.0

                if metodo == "Efectivo":
                    c_tot, c_ent, c_cam = st.columns([0.8, 1, 1], vertical_alignment="bottom")
                    with c_tot: st.markdown(f"<p style='margin:0; font-size:11px; color:gray;'>TOTAL</p><h3 style='margin:0; color:#d32f2f;'>{total_f:.2f}€</h3>", unsafe_allow_html=True)
                    with c_ent: entregado = st.number_input("Entregado € (Intro)", min_value=0.0, value=float(total_f), format="%.2f")
                    with c_cam:
                        ent_val = float(entregado)
                        cambio = ent_val - total_f
                        if cambio >= 0:
                            st.markdown(f"<p style='margin:0; font-size:11px; color:gray;'>CAMBIO AL CLIENTE</p><h3 style='margin:0; color:green;'>{cambio:.2f}€</h3>", unsafe_allow_html=True)
                            pagado_hoy = total_f
                            p_efectivo = total_f
                        else:
                            st.markdown(f"<p style='margin:0; font-size:11px; color:gray;'>DEUDA PENDIENTE</p><h3 style='margin:0; color:orange;'>{-cambio:.2f}€</h3>", unsafe_allow_html=True)
                            pagado_hoy = ent_val; pendiente = -cambio
                            p_efectivo = ent_val

                elif metodo == "Mixto":
                    st.markdown(f"<h3 style='text-align: right; margin: 0; color: #d32f2f;'>Total: {total_f:.2f}€</h3>", unsafe_allow_html=True)
                    cm1, cm2, cm3 = st.columns(3)
                    with cm1: p_e = st.number_input("Efe. (Intro)", min_value=0.0, value=None)
                    with cm2: p_t = st.number_input("Tar. (Intro)", min_value=0.0, value=None)
                    with cm3: p_b = st.number_input("Biz. (Intro)", min_value=0.0, value=None)
                    
                    p_e_val = float(p_e or 0.0)
                    p_t_val = float(p_t or 0.0)
                    p_b_val = float(p_b or 0.0)
                    
                    pagado_hoy = p_e_val + p_t_val + p_b_val
                    p_efectivo = p_e_val; p_tarjeta = p_t_val; p_bizum = p_b_val
                    pendiente = total_f - pagado_hoy if pagado_hoy < total_f else 0.0
                    
                    if p_tarjeta > 0 and lista_bancos:
                        banco_sel_nombre = st.selectbox("🏦 Banco para parte en Tarjeta", [b['nombre_banco'] for b in lista_bancos])
                        banco_info = next((b for b in lista_bancos if b['nombre_banco'] == banco_sel_nombre), None)
                        if banco_info:
                            banco_sel_id = banco_info['id']
                            banco_sel_saldo = banco_info['saldo_actual']
                        metodo_log = f"Mixto (E:{p_efectivo}|T:{p_tarjeta} - {banco_sel_nombre}|B:{p_bizum})"
                    else:
                        metodo_log = f"Mixto (E:{p_efectivo}|T:{p_tarjeta}|B:{p_bizum})"
                        
                    if pendiente > 0: st.warning(f"Pendiente: {pendiente:.2f}€")
                
                else:
                    st.markdown(f"<h3 style='text-align: right; margin: 0; color: #d32f2f;'>Total: {total_f:.2f}€</h3>", unsafe_allow_html=True)
                    pagado_hoy = total_f
                    
                    metodo_log = metodo
                    
                    if metodo.startswith("Tarjeta"): 
                        p_tarjeta = total_f
                        banco_sel_nombre = metodo.replace("Tarjeta (", "").replace(")", "") if "(" in metodo else "Tarjeta"
                        if lista_bancos:
                            banco_info = next((b for b in lista_bancos if b['nombre_banco'] == banco_sel_nombre), None)
                            if banco_info:
                                banco_sel_id = banco_info['id']
                                banco_sel_saldo = banco_info['saldo_actual']
                        metodo_log = metodo
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
                            # ASIGNACIÓN DE PUNTOS
                            cliente_fidel_nombre = ""
                            puntos_ganados = 0
                            nuevo_saldo = 0
                            if "Ninguno" not in cliente_fidelidad:
                                cliente_fidel_nombre = cliente_fidelidad.split(" (Puntos:")[0]
                                cliente_info = next(c for c in res_cli_puntos.data if c['nombre_dueno'] == cliente_fidel_nombre)
                                puntos_ganados = int(total_f // 10) # 1 punto por cada 10€
                                nuevo_saldo = cliente_info.get('puntos', 0) - puntos_a_descontar + puntos_ganados
                                client.table("clientes").update({"puntos": nuevo_saldo}).eq("id", cliente_info['id']).execute()

                            # INSERCIÓN CON COLUMNAS EXACTAS CONTABLES
                            client.table("ventas_historial").insert({
                                "total": float(total_f), "pagado": float(pagado_hoy), "pendiente": float(pendiente),
                                "metodo_pago": str(metodo_log), "cliente_deuda": str(nombre_deudor),
                                "descuento_global": float(desc_g_val), "productos": carrito_limpio, 
                                "estado": "Completado" if pendiente == 0 else "Deuda",
                                "pago_efectivo": float(p_efectivo),
                                "pago_tarjeta": float(p_tarjeta),
                                "pago_bizum": float(p_bizum),
                                "cliente_vip_nombre": cliente_fidel_nombre,
                                "puntos_ganados": puntos_ganados,
                                "puntos_usados": puntos_a_descontar
                            }).execute()
                            
                            if banco_sel_id and p_tarjeta > 0:
                                client.table("cuentas_bancarias").update({"saldo_actual": float(banco_sel_saldo + p_tarjeta)}).eq("id", banco_sel_id).execute()
                            
                            for i in carrito_limpio:
                                if not i.get('Manual', False) and 'id' in i:
                                    res = client.table("productos").select("stock_actual").eq("id", i['id']).execute()
                                    if res.data:
                                        n_stock = int(res.data[0]['stock_actual']) - int(i['Cantidad'])
                                        client.table("productos").update({"stock_actual": n_stock}).eq("id", i['id']).execute()
                            
                            st.session_state.ticket_actual = {
                                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "productos": carrito_limpio, "total": total_f, "metodo": metodo_log,
                                "cliente_fidel": cliente_fidel_nombre, "puntos_ganados": puntos_ganados,
                                "puntos_descontados": puntos_a_descontar, "nuevo_saldo": nuevo_saldo,
                                "descuento_global": desc_g_val
                            }
                            st.session_state.carrito = []
                            st.session_state.llave_busqueda_tpv += 1
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"🚨 Error de Supabase: {e}")
                            
                with c_vac:
                    if st.button("🗑️ Vaciar", use_container_width=True):
                        st.session_state.carrito = []
                        st.session_state.llave_busqueda_tpv += 1
                        st.rerun()
            else:
                st.markdown("<div style='background-color: #f8f9fa; padding: 10px; border-radius: 5px; color: #666; border: 1px solid #ddd;'>🛒 Carrito vacío.</div>", unsafe_allow_html=True)
        st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)