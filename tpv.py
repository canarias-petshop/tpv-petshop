import streamlit as st
import pandas as pd
import time
import json
from datetime import datetime
import streamlit.components.v1 as components
import hashlib

def render_pestana_tpv(client):
    # --- COMPROBACIÓN DE SEGURIDAD: CAJA ABIERTA ---
    res_caja_abierta = client.table("control_caja").select("id").eq("estado", "Abierta").execute()
    
    if not res_caja_abierta.data:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.error("#### 🔒 Terminal Bloqueado\n\n**La caja está actualmente cerrada.** El TPV se encuentra desactivado por seguridad.\n\n👉 Ve a la pestaña **💰 Control Caja** y abre un nuevo turno para poder registrar ventas y emitir tickets.")
        return # Cortamos aquí para que no se renderice absolutamente nada del TPV

    # --- LLAVES DINÁMICAS PARA EL RESETEO AUTOMÁTICO ---
    if 'llave_busqueda_tpv' not in st.session_state: 
        st.session_state.llave_busqueda_tpv = 0
        
    if 'cliente_cobro_tpv' not in st.session_state:
        st.session_state.cliente_cobro_tpv = "Ninguno (Venta Anónima)"
        
    if 'vale_aplicado' not in st.session_state:
        st.session_state.vale_aplicado = None
        
    st.markdown("""
        <div style='display: flex; justify-content: space-between; margin-top: 10px; margin-bottom: 10px; padding: 0 5px;'>
            <h4 style='margin:0; color: #333; white-space: nowrap;'>🛒 Terminal de Venta</h4>
            <h4 style='margin:0; color: #333; white-space: nowrap; padding-right: 10px;'>🛒 Tu Carrito</h4>
        </div>
    """, unsafe_allow_html=True)

    col_busqueda, col_carrito = st.columns([1, 1.4], gap="small")
    
    with col_busqueda:
        @st.cache_data(show_spinner=False, ttl=15)
        def get_inv_tpv(v):
            _all = []
            _off = 0
            while True:
                _r = client.table("productos").select("id, nombre, precio_pvp, stock_actual, sku, igic_tipo").range(_off, _off + 999).execute()
                if _r.data:
                    _all.extend(_r.data)
                    if len(_r.data) < 1000: break
                    _off += 1000
                else: break
            return _all
            
        all_inv = get_inv_tpv(st.session_state.get('db_version', 0))
        df_inv = pd.DataFrame(all_inv) if all_inv else pd.DataFrame()
        
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
            with cm2: m_pre = st.number_input("Precio €", min_value=0.0, step=0.01, format="%.2f", value=None, label_visibility="visible", key=f"m_pre_{st.session_state.llave_busqueda_tpv}")
            with cm3: m_can = st.number_input("Cant.", min_value=1, value=1, label_visibility="visible", key=f"m_can_{st.session_state.llave_busqueda_tpv}")
            if st.form_submit_button("➕ Añadir Manual al Carrito", use_container_width=True):
                if m_nom and m_pre is not None and m_pre >= 0:
                    st.session_state.carrito.append({
                        "Producto": m_nom, "Cantidad": m_can, "Precio": m_pre,
                        "Subtotal": m_can * float(m_pre), "IGIC": 0, "Manual": True
                    })
                    st.session_state.llave_busqueda_tpv += 1
                    st.rerun()

        st.markdown("<hr style='margin: 5px 0px; border: none; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

        with st.expander("📅 Peluquerías de Hoy (Cobro Rápido)", expanded=False):
            hoy_date = datetime.now().date()
            hoy_ini = f"{hoy_date}T00:00:00"
            hoy_fin = f"{hoy_date}T23:59:59"
            res_citas_hoy = client.table("citas").select("id, servicio, mascotas(id, nombre, historial_trabajos, clientes(nombre_dueno, telefono, puntos))").gte("fecha_hora", hoy_ini).lte("fecha_hora", hoy_fin).execute()
            
            try:
                res_emp_tpv = client.table("personal_empleados").select("nombre").execute()
                empleados_tpv = [e['nombre'] for e in res_emp_tpv.data] if res_emp_tpv.data else []
            except:
                empleados_tpv = []

            if res_citas_hoy.data:
                estados_validos = ["[ESTADO: Confirmada]", "[ESTADO: Oferta / Descuento]", "[ESTADO: Asistió]", "[ESTADO: Servicio de recogida"]
                citas_validas = [c for c in res_citas_hoy.data if any(est in c.get('servicio', '') for est in estados_validos)]
                if citas_validas:
                    for c in citas_validas:
                        masc = c.get('mascotas')
                        if not masc: continue
                        cli = masc.get('clientes')
                        if not cli: continue
                        
                        servicio_nom = c.get('servicio', 'Peluquería')
                        import re
                        servicio_nom = re.sub(r'\[ESTADO:\s*.*?\]\s*', '', servicio_nom).strip()
                        servicio_nom = re.sub(r'\[Forzado:\s*.*?\]\s*', '', servicio_nom).strip()
                        
                        s_clean = servicio_nom
                        for emp in empleados_tpv:
                            if f"({emp})" in s_clean:
                                s_clean = s_clean.replace(f"({emp})", "").replace("  ", " ").strip()
                                break
                        
                        # --- EXTRACCIÓN DE PRECIO ANTES DEL BOTÓN ---
                        precio_final = 0.0
                        igic_final = 7.0
                        id_servicio = f"cita_{c['id']}"
                        
                        if not df_inv.empty:
                            term = s_clean.strip().lower()
                            match = df_inv[df_inv['nombre'].astype(str).str.strip().str.lower() == term]
                            if match.empty:
                                match = df_inv[df_inv['nombre'].astype(str).str.lower().str.contains(term, regex=False, na=False)]
                                
                            if match.empty:
                                # Búsqueda inversa: Para citas antiguas largas vs catálogo corto
                                for idx, row in df_inv.iterrows():
                                    cat_nom = str(row['nombre']).strip().lower()
                                    if cat_nom and cat_nom in term:
                                        match = pd.DataFrame([row])
                                        break
                            
                            if not match.empty:
                                pvp_raw = match.iloc[0]['precio_pvp']
                                precio_final = float(pvp_raw) if pd.notna(pvp_raw) and pvp_raw is not None else 0.0
                                igic_final = float(match.iloc[0].get('igic_tipo', 7.0))
                                id_servicio = str(match.iloc[0]['id'])
                                s_clean = match.iloc[0]['nombre'] # Rescata el nombre oficial limpio del catálogo
                        
                        hist = masc.get('historial_trabajos', [])
                        hoy_str_hist = hoy_date.strftime("%d/%m/%Y")
                        
                        hist_hoy = []
                        if isinstance(hist, list):
                            hist_hoy = [t for t in hist if t.get('Fecha') == hoy_str_hist and str(t.get('Trabajo / Servicio')).strip() not in ["", "None"]]
                            
                        if hist_hoy:
                            precio_total_hist = sum(float(t.get('Precio con desc. (€)') or t.get('Precio Base (€)') or 0.0) for t in hist_hoy)
                            btn_label = f"🐾 {masc['nombre']} ➔ 📝 Ficha Completada ({precio_total_hist:.2f}€)"
                            
                            if st.button(btn_label, use_container_width=True, key=f"btn_cita_hist_{c['id']}_{st.session_state.llave_busqueda_tpv}"):
                                for idx_t, t in enumerate(hist_hoy):
                                    srv_hist = str(t.get('Trabajo / Servicio')).strip()
                                    p_base_hist = float(t.get('Precio Base (€)') or 0.0)
                                    p_desc_hist = float(t.get('Precio con desc. (€)') or p_base_hist)
                                    
                                    desc_pct_hist = 0.0
                                    if p_base_hist > 0 and p_desc_hist < p_base_hist:
                                        desc_pct_hist = round((1 - (p_desc_hist / p_base_hist)) * 100, 2)
                                        
                                    igic_hist = 7.0
                                    id_servicio_hist = f"cita_hist_{c['id']}_{idx_t}"
                                    if not df_inv.empty:
                                        term = srv_hist.lower()
                                        match = df_inv[df_inv['nombre'].astype(str).str.strip().str.lower() == term]
                                        if not match.empty:
                                            igic_hist = float(match.iloc[0].get('igic_tipo', 7.0))
                                            id_servicio_hist = str(match.iloc[0]['id'])
                                            srv_hist = match.iloc[0]['nombre']
                                            
                                    nombre_linea_hist = f"{srv_hist} ({masc['nombre']})"
                                    motivo_desc_hist = "Aplicado en ficha" if desc_pct_hist > 0 else ""
                                    
                                    st.session_state.carrito.append({
                                        "id": id_servicio_hist, "Producto": nombre_linea_hist, "Cantidad": 1, 
                                        "Precio": p_base_hist, "Subtotal": p_desc_hist, 
                                        "IGIC": igic_hist, "Manual": False, "Desc. %": desc_pct_hist, "Motivo_Desc": motivo_desc_hist
                                    })
                                    
                                    # --- VOLCAR EXTRAS DE LA FICHA AL CARRITO COMO LÍNEAS INDEPENDIENTES ---
                                    if isinstance(t.get('Extras'), list):
                                        for idx_ext, ext in enumerate(t['Extras']):
                                            ext_nom = str(ext.get('Servicio', 'Extra'))
                                            ext_precio = float(ext.get('Precio', 0.0))
                                            ext_igic = float(ext.get('IGIC', 7.0))
                                            
                                            id_ext_hist = f"cita_hist_ext_{c['id']}_{idx_t}_{idx_ext}"
                                            if not df_inv.empty:
                                                match_ext = df_inv[df_inv['nombre'].astype(str).str.strip().str.lower() == ext_nom.lower()]
                                                if not match_ext.empty:
                                                    id_ext_hist = str(match_ext.iloc[0]['id'])
                                                    ext_nom = match_ext.iloc[0]['nombre']
                                            
                                            st.session_state.carrito.append({
                                                "id": id_ext_hist, "Producto": f"+ {ext_nom} ({masc['nombre']})", "Cantidad": 1,
                                                "Precio": ext_precio, "Subtotal": ext_precio,
                                                "IGIC": ext_igic, "Manual": False, "Desc. %": 0.0, "Motivo_Desc": ""
                                            })
                                            
                                st.session_state.cliente_cobro_tpv = f"{cli['nombre_dueno']} ({cli.get('telefono', '')}) - Puntos: {cli.get('puntos') or 0}"
                                st.session_state.llave_busqueda_tpv += 1
                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                st.rerun()
                        else:
                            aplica_desc = False
                            motivo_desc = ""
                            
                            if "[ESTADO: Oferta / Descuento]" in c.get('servicio', ''):
                                aplica_desc = True
                                motivo_desc = "Oferta en agenda"
                            elif isinstance(hist, list):
                                fechas_previas = []
                                for t in hist:
                                    f_str = t.get('Fecha')
                                    if f_str and f_str != hoy_str_hist:
                                        try: fechas_previas.append(pd.to_datetime(f_str, format="%d/%m/%Y").date())
                                        except: pass
                                if fechas_previas:
                                    ult_visita = max(fechas_previas)
                                    if (hoy_date - ult_visita).days <= 60:
                                        aplica_desc = True
                                        motivo_desc = "Visita < 2 meses"
                                        
                            # REDISEÑO DEL BOTÓN
                            precio_mostrar = precio_final * 0.90 if aplica_desc else precio_final
                            btn_label = f"🐾 {masc['nombre']} ➔ ✂️ {s_clean} ({precio_mostrar:.2f}€)"
                            if aplica_desc: btn_label += " 🎁 Dto 10%"
                            
                            if st.button(btn_label, use_container_width=True, key=f"btn_cita_{c['id']}_{st.session_state.llave_busqueda_tpv}"):
                                desc_pct = 10.0 if aplica_desc else 0.0
                                nombre_linea = f"{s_clean} ({masc['nombre']})"
                                    
                                st.session_state.carrito.append({
                                    "id": id_servicio, "Producto": nombre_linea, "Cantidad": 1, 
                                    "Precio": precio_final, "Subtotal": precio_final * (1 - desc_pct/100), 
                                    "IGIC": igic_final, "Manual": False, "Desc. %": desc_pct, "Motivo_Desc": motivo_desc
                                })
                                st.session_state.cliente_cobro_tpv = f"{cli['nombre_dueno']} ({cli.get('telefono', '')}) - Puntos: {cli.get('puntos') or 0}"
                                st.session_state.llave_busqueda_tpv += 1
                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                st.rerun()
                else: st.info("No hay citas activas hoy.")
            else: st.info("No hay citas hoy.")

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
            cuerpo_email = (
                "Hola,\n\nAdjuntamos el detalle de su ticket de compra:\n\n"
                "================================\n"
                "          ANIMALARIUM\n"
                "     Raquel Trujillo Hernández\n"
                "          DNI: 78854854K\n"
                "   C/ José Hernández Alfonso, 26\n"
                "       38009 S/C de Tenerife\n"
                "================================\n"
                f"Fecha: {t['fecha']}\n"
                "--------------------------------\n"
            )
            for p in t['productos']:
                desc_item = p.get('Desc. %', p.get('Desc %', 0.0))
                motivo = p.get('Motivo_Desc', '')
                if desc_item > 0:
                    motivo_str = f" (Dto. {desc_item}% por {motivo})" if motivo else f" (Dto. {desc_item}%)"
                    cuerpo_email += f"{p['Cantidad']}x {p['Producto']}\n  -> {p['Subtotal']:.2f}€{motivo_str}\n"
                else:
                    cuerpo_email += f"{p['Cantidad']}x {p['Producto']}\n  -> {p['Subtotal']:.2f}€\n"
            
            cuerpo_email += "--------------------------------\n"
            desc_global = t.get('descuento_global', 0.0)
            if desc_global > 0:
                cuerpo_email += f"Descuento global: {desc_global}%\n"
                
            if t.get('desc_vale_eur', 0.0) > 0:
                cuerpo_email += f"Vale {t['vale_aplicado']} aplicado: -{t['desc_vale_eur']:.2f}€\n"

            cuerpo_email += f"TOTAL PAGADO: {t['total']:.2f}€\n"
            cuerpo_email += f"MÉTODO DE PAGO: {metodo_display}\n"
            cuerpo_email += "================================\n"
            
            if t.get('cliente_fidel'):
                cuerpo_email += f"🌟 CLIENTE VIP: {t['cliente_fidel']}\n"
                cuerpo_email += f"Puntos ganados hoy: +{t['puntos_ganados']}\n"
                cuerpo_email += f"Saldo actual: {t.get('nuevo_saldo', 0)} puntos\n"
                cuerpo_email += "INFO VIP: Ganas 1 pto por cada 10€ de compra. (1 pto = 0.50€ dto)\n"
                cuerpo_email += "================================\n"
                
            cuerpo_email += "\nPOLÍTICA DE DEVOLUCIÓN:\nPlazo de 14 días con ticket y embalaje original en perfecto estado.\n\n¡Gracias por su visita!"
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
                <button class="btn-print" onclick="imprimirConStar('ticket-impresion')">🖨️ IMPRIMIR TICKET</button>
                <button class="btn-print" style="background-color: #9c27b0;" onclick="imprimirConStar('ticket-regalo')">🎁 TICKET REGALO</button>
                <a href="mailto:{t.get('email_cliente', '')}?subject=Ticket%20de%20Compra%20-%20Animalarium&body={body_encoded}" target="_blank" style="text-decoration: none; flex: 1;">
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
                motivo = p.get('Motivo_Desc', '')
                motivo_str = f" por {motivo}" if motivo else ""
                
                if desc_item > 0:
                    precio_orig = p.get('Precio', 0.0) * p['Cantidad']
                    html_ticket += f"<tr><td style='padding-bottom: 0px;'>{p['Cantidad']}x {p['Producto']}</td><td style='text-align: right; padding-bottom: 0px;'><del>{precio_orig:.2f}€</del> {p['Subtotal']:.2f}€</td></tr>"
                    html_ticket += f"<tr><td colspan='2' style='font-size: 16px; padding-bottom: 5px; color: #555;'>  ↳ Dto. {desc_item}% aplicado{motivo_str}</td></tr>"
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

            if t.get('desc_vale_eur', 0.0) > 0:
                html_ticket += f"<div style='text-align: right; font-size: 22px;'><b>Vale {t['vale_aplicado']}: -{t['desc_vale_eur']:.2f}€</b></div>"

            if t.get('pendiente', 0) > 0:
                html_ticket += f"<div style='text-align: right; font-size: 24px; color: black; margin-top: 5px; border: 2px solid black; padding: 3px;'><b>DEUDA PENDIENTE: {t['pendiente']:.2f}€</b></div>"

            html_ticket += f"""
                    <div style="text-align: right; font-size: 28px;"><b>TOTAL: {t['total']:.2f}€</b></div>
                    <div style="font-size: 20px; text-align: left; margin-top: 10px;"><b>Método de pago:</b> {metodo_display}</div>
            """
            if t.get('cliente_fidel'):
                html_ticket += f"<div style='font-size:18px; text-align:center; margin-top:15px; border: 1px solid #000; padding: 5px;'><b>🌟 CLIENTE VIP: {t['cliente_fidel']}</b>"
                html_ticket += f"<br>Has ganado +{t['puntos_ganados']} puntos hoy!"
                html_ticket += f"<br>Saldo actual disponible: {t.get('nuevo_saldo', 0)} puntos"
                html_ticket += f"<br><span style='font-size:14px; color:#555;'>Ganas 1 pto por cada 10€ de compra. (1 pto = 0.50€ dto)</span></div>"

            html_ticket += """
                    
                    <div style="font-size: 18px; color: #000; margin-top: 30px; text-align: center;">
                        <b>POLÍTICA DE DEVOLUCIÓN</b><br>
                        Plazo de 14 días con ticket y<br>
                        embalaje original en perfecto estado.
                    </div>
                </div>
            </div>
            
            <div id="ticket-regalo" style="display:none;">
                <div style="text-align: center; font-family: monospace; width: 100%; font-size: 22px; color: black; font-weight: bold;">
                    {logo_html}
                    <b style="font-size: 34px;">ANIMALARIUM</b><br>
                    Raquel Trujillo Hernández<br>
                    DNI: 78854854K<br>
                    C/ José Hernández Alfonso, 26<br>
                    38009 S/C de Tenerife
                    <br><br>
                    <div style="font-size: 24px; border: 2px solid black; margin: 10px 0; padding: 5px;"><b>TICKET REGALO</b></div>
                    <div style="text-align: left; font-size: 22px;">Fecha: {t['fecha']}</div>
                    <hr style="border-top: 2px dashed #000; margin: 10px 0px;">
                    <table style="width: 100%; font-size: 22px; text-align: left; font-weight: bold;">
            """
            for p in t['productos']:
                html_ticket += f"<tr><td style='padding-bottom: 5px;'>{p['Cantidad']}x {p['Producto']}</td></tr>"
                
            html_ticket += """
                    </table>
                    <hr style="border-top: 2px dashed #000; margin: 10px 0px;">
                    <div style="font-size: 18px; color: #000; margin-top: 20px; text-align: center;">
                        <b>IMPRESCINDIBLE PARA CAMBIOS</b><br>
                        Plazo de 14 días con este ticket y<br>
                        embalaje original en perfecto estado.<br>
                        Se emitirá un VALE DE TIENDA,<br>
                        no se devuelve el dinero en efectivo.
                    </div>
                </div>
            </div>
            </div>

            <script>
            function imprimirConStar(elementId) {
                var ticketHTML = document.getElementById(elementId).innerHTML;
                var fullHTML = "<!DOCTYPE html><html><head><meta charset='utf-8'></head><body style='margin:0; padding:0; background-color:white;'>" + ticketHTML + "</body></html>";
                var htmlCodificado = encodeURIComponent(fullHTML);
                var backURL = encodeURIComponent(window.location.href);
                var starURL = "starpassprnt://v1/print/nopreview?back=" + backURL + "&html=" + htmlCodificado;
            
            // Usar un iframe oculto evita que Streamlit se reinicie en la tablet
            var iframe = document.createElement('iframe');
            iframe.style.display = 'none';
            iframe.src = starURL;
            document.body.appendChild(iframe);
            }
            
            // Auto-retorno a Nueva Venta pasados 30 segundos
            setTimeout(function() {
                const btns = window.parent.document.querySelectorAll('button');
                btns.forEach(btn => {
                    if(btn.innerText.includes('Nueva Venta')) {
                        btn.click();
                    }
                });
            }, 30000);
            </script>
            
            </body>
            </html>
            """
            components.html(html_ticket, height=450, scrolling=True)
            
            c_nv = st.columns(1)[0]
            with c_nv:
                if st.button("🛒 Nueva Venta", use_container_width=True, type="primary"):
                    st.session_state.ticket_actual = None
                    st.session_state.vale_aplicado = None
                    st.session_state.cliente_cobro_tpv = "Ninguno (Venta Anónima)"
                    st.session_state.llave_busqueda_tpv += 1
                    st.rerun()

        else:
            if st.session_state.carrito:
                # --- FIX: Normalizar carrito para evitar fallos de PyArrow (Tipos mixtos) ---
                for item in st.session_state.carrito:
                    if 'Desc. %' not in item: item['Desc. %'] = 0.0
                    if 'Motivo_Desc' not in item: item['Motivo_Desc'] = ""
                    if 'id' not in item: item['id'] = "0"
                    if 'Manual' not in item: item['Manual'] = False
                    
                df_car = pd.DataFrame(st.session_state.carrito)

                edited_df = st.data_editor(
                    df_car,
                    column_order=("Cantidad", "Producto", "Precio", "Desc. %", "Subtotal"),
                    column_config={
                        "Cantidad": st.column_config.NumberColumn("Cant.", min_value=1, step=1, width="small"),
                        "Producto": st.column_config.TextColumn("Producto"),
                        "Precio": st.column_config.NumberColumn("Precio €", format="%.2f", step=0.01),
                        "Desc. %": st.column_config.NumberColumn("Desc. %", min_value=0.0, max_value=100.0, format="%.2f%%", step=0.01),
                        "Subtotal": st.column_config.NumberColumn("Total", format="%.2f", disabled=True, step=0.01),
                    },
                    hide_index=True, use_container_width=True, num_rows="dynamic", height=250, key="ed_car_ticket"
                )
                
                if not edited_df.equals(df_car):
                    original_len = len(edited_df)
                    
                    # --- FIX: Eliminar filas vacías añadidas por error con el botón '+' ---
                    edited_df = edited_df.dropna(subset=['Producto'])
                    edited_df = edited_df[edited_df['Producto'].astype(str).str.strip() != '']
                    
                    # --- FIX: Romper el bucle infinito borrando la memoria del widget ---
                    if len(edited_df) < original_len:
                        if "ed_car_ticket" in st.session_state:
                            del st.session_state["ed_car_ticket"]
                    
                    edited_df["Subtotal"] = (edited_df["Cantidad"] * edited_df["Precio"]) * (1 - edited_df["Desc. %"] / 100)
                    st.session_state.carrito = json.loads(edited_df.to_json(orient='records'))
                    st.rerun()

                st.markdown("<hr style='margin: 2px 0px; border: none; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

                sub_antes = edited_df["Subtotal"].sum()
                
                # --- FIDELIZACIÓN ---
                all_cli_puntos = []
                offset = 0
                while True:
                    res_cli = client.table("clientes").select("id, nombre_dueno, puntos, telefono, direccion, email").range(offset, offset + 999).execute()
                    if res_cli.data:
                        all_cli_puntos.extend(res_cli.data)
                        if len(res_cli.data) < 1000: break
                        offset += 1000
                    else: break
                
                class DummyRes: pass
                res_cli_puntos = DummyRes()
                res_cli_puntos.data = all_cli_puntos
                
                mapa_clientes_tpv = {}
                opc_cli = ["Ninguno (Venta Anónima)"]
                if res_cli_puntos.data:
                    for c in res_cli_puntos.data:
                        ptos = c.get('puntos') or 0
                        etiq = f"{c['nombre_dueno']} ({c.get('telefono', '')}) - Puntos: {ptos}"
                        opc_cli.append(etiq)
                        mapa_clientes_tpv[etiq] = c
                
                # --- AUTO-SELECCIÓN DE DUEÑO (Viene desde Cobro Rápido) ---
                idx_cli = 0
                cliente_actual = st.session_state.get('cliente_cobro_tpv', "Ninguno")
                if cliente_actual in opc_cli:
                    idx_cli = opc_cli.index(cliente_actual)
                else:
                    for i, opc in enumerate(opc_cli):
                        if cliente_actual.split(" - Puntos:")[0].strip() in opc:
                            idx_cli = i
                            break
                
                c_desc, c_fid = st.columns(2)
                with c_desc: desc_g = st.number_input("🎁 Descuento Global (%)", min_value=0.0, max_value=100.0, value=None, step=0.01, format="%.2f")
                with c_fid: cliente_fidelidad = st.selectbox("🌟 Asociar Cliente (Puntos)", opc_cli, index=idx_cli)
                st.session_state.cliente_cobro_tpv = cliente_fidelidad
                
                st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
                enviar_domicilio_check = st.checkbox("🚚 Enviar pedido a Domicilio")
                enviar_domicilio = False
                dir_entrega = ""
                
                if enviar_domicilio_check:
                    if "Ninguno" in cliente_fidelidad:
                        st.warning("⚠️ Selecciona un cliente arriba ('Asociar Cliente') para poder enviarlo a domicilio.")
                    else:
                        enviar_domicilio = True
                        cli_data_dom = mapa_clientes_tpv.get(cliente_fidelidad, {})
                        dir_entrega = st.text_input("📍 Dirección de Entrega (Editable):", value=cli_data_dom.get('direccion', ''))
                
                desc_g_val = float(desc_g or 0.0)
                total_f = sub_antes * (1 - desc_g_val / 100)
                
                # --- LÓGICA DE CANJEO DE PUNTOS ---
                desc_puntos_eur = 0.0
                puntos_a_descontar = 0
                if "Ninguno" not in cliente_fidelidad:
                    cli_info = mapa_clientes_tpv.get(cliente_fidelidad, {})
                    cli_check_nombre = cli_info.get('nombre_dueno', '')
                    
                    res_deuda_cli = client.table("ventas_historial").select("id").eq("cliente_deuda", cli_check_nombre).eq("estado", "Deuda").limit(1).execute()
                    tiene_deuda = True if res_deuda_cli.data else False
                    
                    puntos_disp = int(cli_info.get('puntos') or 0)
                    if puntos_disp > 0:
                        if tiene_deuda:
                            st.error(f"⛔ **{cli_check_nombre}** tiene pagos pendientes. No puede canjear puntos hasta saldar su deuda.")
                        else:
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
                
                # --- LÓGICA DE VALES DE TIENDA ---
                if 'vale_aplicado' not in st.session_state:
                    st.session_state.vale_aplicado = None
                    
                c_v1, c_v2 = st.columns([2, 1], vertical_alignment="bottom")
                with c_v1:
                    codigo_vale_input = st.text_input("🎟️ Canjear Vale de Tienda", placeholder="Ej: VALE-X8J2", key=f"vale_input_{st.session_state.llave_busqueda_tpv}")
                with c_v2:
                    if st.button("Validar Vale", use_container_width=True):
                        if codigo_vale_input:
                            vale_valido = False
                            try:
                                res_vale = client.table("vales_tienda").select("*").eq("codigo_vale", codigo_vale_input.strip().upper()).execute()
                                if res_vale.data:
                                    vale_db = res_vale.data[0]
                                    if vale_db['saldo_actual'] > 0:
                                        st.session_state.vale_aplicado = vale_db
                                        st.success(f"Vale válido. Saldo disponible: {vale_db['saldo_actual']:.2f}€")
                                        vale_valido = True
                                    else:
                                        st.error("Este vale ya está agotado.")
                                else:
                                    st.error("Código de vale no encontrado.")
                            except Exception as e:
                                st.error(f"⚠️ Error conectando con la base de datos de vales: {e}")
                                
                            if vale_valido:
                                time.sleep(1); st.rerun()
                                
                desc_vale_eur = 0.0
                if st.session_state.vale_aplicado:
                    saldo_vale = float(st.session_state.vale_aplicado['saldo_actual'])
                    desc_vale_eur = min(saldo_vale, total_f)
                    
                    st.info(f"🎟️ Vale **{st.session_state.vale_aplicado['codigo_vale']}** aplicado: **-{desc_vale_eur:.2f}€**")
                    if st.button("❌ Quitar Vale", key=f"quitar_vale_{st.session_state.llave_busqueda_tpv}"):
                        st.session_state.vale_aplicado = None
                        st.rerun()
                        
                total_f = total_f - desc_vale_eur
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
                    with c_ent: entregado = st.number_input("Entregado € (Intro)", min_value=0.0, value=float(total_f), format="%.2f", step=0.01)
                    with c_cam:
                        ent_val = float(entregado)
                        cambio = ent_val - total_f
                        if cambio >= 0:
                            st.markdown(f"<p style='margin:0; font-size:11px; color:gray;'>CAMBIO AL CLIENTE</p><h3 style='margin:0; color:green;'>{cambio:.2f}€</h3>", unsafe_allow_html=True)
                            pagado_hoy = total_f
                            p_efectivo = total_f
                        else:
                            st.markdown(f"<p style='margin:0; font-size:11px; color:gray;'>FALTA (Se anotará como Deuda al finalizar)</p><h3 style='margin:0; color:orange;'>{-cambio:.2f}€</h3>", unsafe_allow_html=True)
                            pagado_hoy = ent_val; pendiente = -cambio
                            p_efectivo = ent_val

                elif metodo == "Mixto":
                    st.markdown(f"<h3 style='text-align: right; margin: 0; color: #d32f2f;'>Total: {total_f:.2f}€</h3>", unsafe_allow_html=True)
                    cm1, cm2, cm3 = st.columns(3)
                    with cm1: p_e = st.number_input("Efe. (Intro)", min_value=0.0, value=None, step=0.01, format="%.2f")
                    with cm2: p_t = st.number_input("Tar. (Intro)", min_value=0.0, value=None, step=0.01, format="%.2f")
                    with cm3: p_b = st.number_input("Biz. (Intro)", min_value=0.0, value=None, step=0.01, format="%.2f")
                    
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
                        
                    if pendiente > 0: st.warning(f"Falta por cobrar: {pendiente:.2f}€ (Se anotará como deuda al finalizar)")
                
                else:
                    c_tot, c_ent, c_pen = st.columns([0.8, 1, 1], vertical_alignment="bottom")
                    with c_tot: st.markdown(f"<p style='margin:0; font-size:11px; color:gray;'>TOTAL</p><h3 style='margin:0; color:#d32f2f;'>{total_f:.2f}€</h3>", unsafe_allow_html=True)
                    with c_ent: entregado = st.number_input("Cobrado € (Intro)", min_value=0.0, value=float(total_f), format="%.2f", step=0.01)
                    with c_pen:
                        ent_val = float(entregado)
                        if ent_val < total_f:
                            pendiente = total_f - ent_val
                            pagado_hoy = ent_val
                            st.markdown(f"<p style='margin:0; font-size:11px; color:gray;'>FALTA (Se anotará como Deuda al finalizar)</p><h3 style='margin:0; color:orange;'>{pendiente:.2f}€</h3>", unsafe_allow_html=True)
                        else:
                            pendiente = 0.0
                            pagado_hoy = ent_val
                            if ent_val > total_f:
                                st.markdown(f"<p style='margin:0; font-size:11px; color:gray;'>SOBREPAGO</p><h3 style='margin:0; color:green;'>+{ent_val - total_f:.2f}€</h3>", unsafe_allow_html=True)
                    
                    metodo_log = metodo
                    
                    if metodo.startswith("Tarjeta"): 
                        p_tarjeta = pagado_hoy
                        banco_sel_nombre = metodo.replace("Tarjeta (", "").replace(")", "") if "(" in metodo else "Tarjeta"
                        if lista_bancos:
                            banco_info = next((b for b in lista_bancos if b['nombre_banco'] == banco_sel_nombre), None)
                            if banco_info:
                                banco_sel_id = banco_info['id']
                                banco_sel_saldo = banco_info['saldo_actual']
                        metodo_log = metodo
                    if metodo == "Bizum": p_bizum = pagado_hoy

                st.markdown("<div style='height: 2px;'></div>", unsafe_allow_html=True)
                c_cob, c_vac = st.columns([2, 1])
                with c_cob:
                    bloqueo = (pendiente > 0 and "Ninguno" in cliente_fidelidad)
                    if st.button("🧧 FINALIZAR COBRO", use_container_width=True, type="primary", disabled=bloqueo):
                        # --- PROTECCIÓN DOBLE CLIC BACKEND ---
                        import time
                        current_time = time.time()
                        if current_time - st.session_state.get('last_cobro_time', 0) < 3:
                            st.warning("⏳ Procesando cobro, por favor espera...")
                            st.stop()
                        st.session_state['last_cobro_time'] = current_time

                        carrito_limpio = json.loads(edited_df.to_json(orient='records'))
                        
                        # --- FIX: Limpieza final por seguridad antes de guardar ---
                        carrito_limpio = [item for item in carrito_limpio if item.get('Producto') and str(item.get('Producto')).strip() != '']
                        if not carrito_limpio:
                            st.warning("El carrito está vacío o contiene líneas no válidas.")
                            st.stop()
                        
                        try:
                            # ASIGNACIÓN DE PUNTOS
                            cliente_fidel_nombre = ""
                            puntos_ganados = 0
                            nuevo_saldo = 0
                            cliente_email = ""
                            if "Ninguno" not in cliente_fidelidad:
                                cliente_info = mapa_clientes_tpv.get(cliente_fidelidad, {})
                                cliente_fidel_nombre = cliente_info.get('nombre_dueno', '')
                                cliente_email = cliente_info.get('email', '')
                                
                                if pendiente == 0:
                                    puntos_ganados = int(total_f // 10) # 1 punto por cada 10€
                                else:
                                    puntos_ganados = 0 # ❌ No sumar puntos en el ticket si queda deuda
                                    
                                ptos_act = cliente_info.get('puntos') or 0
                                nuevo_saldo = ptos_act - puntos_a_descontar + puntos_ganados
                                client.table("clientes").update({"puntos": nuevo_saldo}).eq("id", cliente_info.get('id')).execute()
                                
                            # GENERACIÓN DE HASH (LEY ANTIFRAUDE / VERIFACTU)
                            res_last = client.table("ventas_historial").select("hash_actual").order("id", desc=True).limit(1).execute()
                            hash_anterior = res_last.data[0].get("hash_actual", "") if res_last.data else ""
                            data_to_hash = f"TICKET|{datetime.now().isoformat()}|{total_f:.2f}|{hash_anterior}"
                            hash_actual = hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest().upper()

                            carrito_db = carrito_limpio.copy()
                            metodo_final_log = str(metodo_log)
                            
                            if st.session_state.vale_aplicado and desc_vale_eur > 0:
                                carrito_db.append({
                                    "__meta__": True,
                                    "vale_aplicado": st.session_state.vale_aplicado['codigo_vale'],
                                    "desc_vale_eur": desc_vale_eur
                                })
                                if float(pagado_hoy) == 0:
                                    metodo_final_log = f"Vale ({st.session_state.vale_aplicado['codigo_vale']})"
                                else:
                                    metodo_final_log += f" + Vale ({st.session_state.vale_aplicado['codigo_vale']})"

                            # INSERCIÓN CON COLUMNAS EXACTAS CONTABLES
                            client.table("ventas_historial").insert({
                                "total": float(total_f), "pagado": float(pagado_hoy), "pendiente": float(pendiente),
                                "metodo_pago": metodo_final_log, "cliente_deuda": str(cliente_fidel_nombre) if pendiente > 0 else "",
                                "descuento_global": float(desc_g_val), "productos": carrito_db, 
                                "estado": "Completado" if pendiente == 0 else "Deuda",
                                "pago_efectivo": float(p_efectivo),
                                "pago_tarjeta": float(p_tarjeta),
                                "pago_bizum": float(p_bizum),
                                "cliente_vip_nombre": cliente_fidel_nombre,
                                "puntos_ganados": puntos_ganados,
                                "puntos_usados": puntos_a_descontar,
                                "hash_anterior": hash_anterior,
                                "hash_actual": hash_actual
                            }).execute()
                            
                            if banco_sel_id and p_tarjeta > 0:
                                client.table("cuentas_bancarias").update({"saldo_actual": float(banco_sel_saldo + p_tarjeta)}).eq("id", banco_sel_id).execute()
                                
                            if st.session_state.vale_aplicado and desc_vale_eur > 0:
                                nuevo_saldo_vale = float(st.session_state.vale_aplicado['saldo_actual']) - desc_vale_eur
                                client.table("vales_tienda").update({"saldo_actual": nuevo_saldo_vale}).eq("id", st.session_state.vale_aplicado['id']).execute()
                                
                            # --- CREACIÓN AUTOMÁTICA DE PEDIDO A DOMICILIO ---
                            if enviar_domicilio and cliente_fidel_nombre:
                                detalle_pedido = "\n".join([f"• {p['Cantidad']}x {p['Producto']}" for p in carrito_limpio])
                                try:
                                    client.table("pedidos_domicilio").insert({
                                        "nombre_cliente": cliente_fidel_nombre,
                                        "telefono": cliente_info.get('telefono', ''),
                                        "direccion": dir_entrega,
                                        "detalle_pedido": detalle_pedido,
                                        "estado": "Pendiente"
                                    }).execute()
                                except Exception as e: pass
                            
                            for i in carrito_limpio:
                                if not i.get('Manual', False) and 'id' in i:
                                    if str(i['id']).startswith('cita_'):
                                        continue
                                    try:
                                        res = client.table("productos").select("stock_actual").eq("id", i['id']).execute()
                                        if res.data:
                                            n_stock = int(res.data[0]['stock_actual']) - int(i['Cantidad'])
                                            client.table("productos").update({"stock_actual": n_stock}).eq("id", i['id']).execute()
                                    except Exception:
                                        pass
                            
                            st.session_state.ticket_actual = {
                                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "productos": carrito_limpio, "total": total_f, "metodo": metodo_log,
                                "cliente_fidel": cliente_fidel_nombre, "puntos_ganados": puntos_ganados,
                                "puntos_descontados": puntos_a_descontar, "nuevo_saldo": nuevo_saldo,
                                "descuento_global": desc_g_val, "pendiente": pendiente,
                                "vale_aplicado": st.session_state.vale_aplicado['codigo_vale'] if st.session_state.vale_aplicado else None,
                                "desc_vale_eur": desc_vale_eur if st.session_state.vale_aplicado else 0.0,
                                "email_cliente": cliente_email if "Ninguno" not in cliente_fidelidad else ""
                            }
                            st.session_state.carrito = []
                            st.session_state.vale_aplicado = None
                            st.session_state.cliente_cobro_tpv = "Ninguno (Venta Anónima)"
                            st.session_state.llave_busqueda_tpv += 1
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"🚨 Error de Supabase: {e}")
                            
                with c_vac:
                    if st.button("🗑️ Vaciar", use_container_width=True):
                        st.session_state.carrito = []
                        st.session_state.cliente_cobro_tpv = "Ninguno (Venta Anónima)"
                        st.session_state.vale_aplicado = None
                        st.session_state.llave_busqueda_tpv += 1
                        st.rerun()
            else:
                st.markdown("<div style='background-color: #f8f9fa; padding: 10px; border-radius: 5px; color: #666; border: 1px solid #ddd;'>🛒 Carrito vacío.</div>", unsafe_allow_html=True)
        st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)