import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import time
import json
import streamlit.components.v1 as components
import random
import string

@st.cache_data(show_spinner=False, ttl=300)
def fetch_caja_abierta_created_at_h(_client):
    return _client.table("control_caja").select("created_at").eq("estado", "Abierta").execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_ventas_historial_por_id_h(_client, b_ticket):
    return _client.table("ventas_historial").select("*").eq("id", b_ticket).execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_ventas_historial_por_fechas_h(_client, f_inicio, f_fin):
    return _client.table("ventas_historial").select("*").gte("created_at", f"{f_inicio}T00:00:00").lte("created_at", f"{f_fin}T23:59:59").order("id", desc=True).execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_cuentas_bancarias_nombres_h(_client):
    return _client.table("cuentas_bancarias").select("nombre_banco").execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_cliente_puntos_h(_client, cliente_str):
    return _client.table("clientes").select("id, puntos").eq("nombre_dueno", cliente_str).execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_cuentas_bancarias_abono_h(_client):
    return _client.table("cuentas_bancarias").select("id, nombre_banco, saldo_actual").execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_producto_stock_h(_client, producto_id):
    return _client.table("productos").select("stock_actual").eq("id", producto_id).execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_caja_abierta_id_h(_client):
    return _client.table("control_caja").select("id").eq("estado", "Abierta").execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_cajas_cerradas_por_fecha_h(_client, f_inicio, f_fin):
    return _client.table("control_caja").select("*").eq("estado", "Cerrada").gte("created_at", f"{f_inicio}T00:00:00").lte("created_at", f"{f_fin}T23:59:59").order("id", desc=True).execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_movimientos_caja_por_turno_h(_client, turno_sel):
    return _client.table("movimientos_caja").select("*").eq("id_caja", turno_sel).execute()

def limpiar_cache_historial():
    fetch_caja_abierta_created_at_h.clear()
    fetch_ventas_historial_por_id_h.clear()
    fetch_ventas_historial_por_fechas_h.clear()
    fetch_cuentas_bancarias_nombres_h.clear()
    fetch_cliente_puntos_h.clear()
    fetch_cuentas_bancarias_abono_h.clear()
    fetch_producto_stock_h.clear()
    fetch_caja_abierta_id_h.clear()
    fetch_cajas_cerradas_por_fecha_h.clear()
    fetch_movimientos_caja_por_turno_h.clear()

def render_pestana_historial(client):
    if 'devolucion_actual' not in st.session_state:
        st.session_state.devolucion_actual = None
    if 'vale_generado' not in st.session_state:
        st.session_state.vale_generado = None

    st.markdown("<h3 style='margin-top: -15px;'>📜 Historial de Ventas y Cajas</h3>", unsafe_allow_html=True)
    sub_h_ventas, sub_h_cajas = st.tabs(["🛒 Tickets y Ventas", "🔒 Cierres de Caja"])
    
    with sub_h_ventas:
        # --- VISTA DE ABONO O VALE ---
        if st.session_state.devolucion_actual:
            d = st.session_state.devolucion_actual
            st.error("✅ DEVOLUCIÓN REALIZADA CON ÉXITO")
            cuerpo_email = (
                "Hola,\n\nAdjuntamos el justificante de su devolución correspondiente al ticket original:\n\n"
                "================================\n"
                "          ANIMALARIUM\n"
                "     Raquel Trujillo Hernández\n"
                "================================\n"
                f"Fecha: {d['fecha']}\n"
                f"ABONO DE TICKET #{d['ticket_original_id']}\n"
                "--------------------------------\n"
            )
            for p in d['productos']:
                cuerpo_email += f"{p['Cantidad']}x {p['Producto']}\n  -> {-p['Subtotal']:.2f}€\n"
            cuerpo_email += "--------------------------------\n"
            cuerpo_email += f"TOTAL ABONADO: {d['total']:.2f}€\n"
            cuerpo_email += f"MÉTODO DE ABONO: {d['metodo']}\n"
            cuerpo_email += "================================\n\nUn saludo."
            import urllib.parse
            import base64
            logo_html = ""
            try:
                with open("LOGO.jpg", "rb") as img_file:
                    logo_html = f'<img src="data:image/jpeg;base64,{base64.b64encode(img_file.read()).decode("utf-8")}" style="max-width: 200px; margin-bottom: 10px;"><br>'
            except: pass
            html_abono = f"""
            <!DOCTYPE html><html><head><meta charset='utf-8'>
            <style>
                body {{ margin: 0; padding: 0; font-family: sans-serif; background-color: #f8f9fa; }}
                #botones-container {{ display: flex; gap: 10px; padding: 10px; max-width: 350px; margin: 0 auto; justify-content: center; }}
                .btn-print {{ flex: 1; padding: 12px 5px; background-color: #d32f2f; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 13px; width: 100%; }}
                .escala-mini {{ zoom: 0.65; -moz-transform: scale(0.65); transform-origin: top center; padding-bottom: 20px; }}
                #ticket-impresion {{ display: block; border: 1px solid #ccc; padding: 15px; background-color: #fff0f0; width: 300px; margin: 0 auto; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }}
            </style>
            </head><body><div id="botones-container">
                <button class="btn-print" onclick="imprimirConStar()">🖨️ IMPRIMIR ABONO</button>
                <a href="mailto:?subject=Justificante%20Devolucion&body={urllib.parse.quote(cuerpo_email)}" target="_blank" style="text-decoration: none; flex: 1;">
                    <button class="btn-print" style="background-color: #2e7d32;">✉️ ENVIAR EMAIL</button></a></div>
            <div class="escala-mini"><div id="ticket-impresion"><div style="text-align: center; font-family: monospace; width: 100%; font-size: 22px; color: black; font-weight: bold;">
                {logo_html}<b style="font-size: 34px;">ABONO / DEVOLUCIÓN</b><br>
                <div style="text-align: left; font-size: 22px;">Fecha: {d['fecha']}<br>Ticket Original: #{d['ticket_original_id']}</div>
                <hr style="border-top: 2px dashed #000; margin: 10px 0px;"><table style="width: 100%; font-size: 22px; text-align: left; font-weight: bold;">
            """
            for p in d['productos']: html_abono += f"<tr><td style='padding-bottom: 5px;'>{p['Cantidad']}x {p['Producto']}</td><td style='text-align: right;'>{-p['Subtotal']:.2f}€</td></tr>"
            html_abono += f"""</table><hr style="border-top: 2px dashed #000; margin: 10px 0px;">
                <div style="text-align: right; font-size: 28px;"><b>TOTAL ABONADO: {d['total']:.2f}€</b></div>
                <div style="font-size: 20px; text-align: left; margin-top: 10px;"><b>Método:</b> {d['metodo']}</div>
                <div style="text-align: center; margin-top: 25px;"><img src="https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=ABONO-{d['ticket_original_id']}" alt="QR" /></div>
                </div></div></div>
            <script>function imprimirConStar() {{ var htmlCodificado = encodeURIComponent("<!DOCTYPE html><html><body style='margin:0; padding:0; background-color:white;'>" + document.getElementById('ticket-impresion').innerHTML + "</body></html>"); var iframe = document.createElement('iframe'); iframe.style.display = 'none'; iframe.src = "starpassprnt://v1/print/nopreview?back=" + encodeURIComponent(window.location.href) + "&html=" + htmlCodificado; document.body.appendChild(iframe); }}</script></body></html>"""
            components.html(html_abono, height=400, scrolling=True)
            if st.button("⬅️ Volver al Historial", use_container_width=True): st.session_state.devolucion_actual = None; st.rerun()
            st.stop()

        if st.session_state.vale_generado:
            v = st.session_state.vale_generado
            st.success("✅ VALE DE TIENDA GENERADO CON ÉXITO")
            import base64
            logo_html = ""
            try:
                with open("LOGO.jpg", "rb") as img_file:
                    logo_html = f'<img src="data:image/jpeg;base64,{base64.b64encode(img_file.read()).decode("utf-8")}" style="max-width: 200px; margin-bottom: 10px;"><br>'
            except: pass
            html_vale = f"""
            <!DOCTYPE html><html><head><meta charset='utf-8'>
            <style>
                body {{ margin: 0; padding: 0; font-family: sans-serif; background-color: #f8f9fa; }}
                #botones-container {{ display: flex; gap: 10px; padding: 10px; max-width: 350px; margin: 0 auto; justify-content: center; }}
                .btn-print {{ flex: 1; padding: 12px 5px; background-color: #4caf50; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 13px; width: 100%; }}
                .escala-mini {{ zoom: 0.65; -moz-transform: scale(0.65); transform-origin: top center; padding-bottom: 20px; }}
                #ticket-impresion {{ display: block; border: 1px solid #ccc; padding: 15px; background-color: #f0fff0; width: 300px; margin: 0 auto; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }}
            </style>
            </head><body><div id="botones-container">
                <button class="btn-print" onclick="imprimirConStar()">🖨️ IMPRIMIR VALE</button></div>
            <div class="escala-mini"><div id="ticket-impresion"><div style="text-align: center; font-family: monospace; width: 100%; font-size: 22px; color: black; font-weight: bold;">
                {logo_html}<b style="font-size: 34px;">VALE DE TIENDA</b><br>
                <div style="text-align: left; font-size: 22px;">Fecha: {v['fecha']}</div>
                <hr style="border-top: 2px dashed #000; margin: 10px 0px;">
                <div style="font-size: 28px; text-align: center; margin: 10px 0;"><b>VALOR: {v['valor']:.2f}€</b></div>
                <div style="font-size: 24px; text-align: center; border: 2px solid black; padding: 5px; margin: 10px 0;"><b>CÓDIGO: {v['codigo']}</b></div>
                <div style="text-align: center; margin-top: 15px;"><img src="https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={v['codigo']}" alt="QR Vale" /></div>
                <div style="font-size: 18px; color: #000; margin-top: 20px; text-align: center;">Guarda este vale para tu próxima compra.<br>No tiene caducidad. No canjeable por dinero.</div>
            </div></div></div>
            <script>function imprimirConStar() {{ var htmlCodificado = encodeURIComponent("<!DOCTYPE html><html><body style='margin:0; padding:0; background-color:white;'>" + document.getElementById('ticket-impresion').innerHTML + "</body></html>"); var iframe = document.createElement('iframe'); iframe.style.display = 'none'; iframe.src = "starpassprnt://v1/print/nopreview?back=" + encodeURIComponent(window.location.href) + "&html=" + htmlCodificado; document.body.appendChild(iframe); }}</script></body></html>"""
            components.html(html_vale, height=400, scrolling=True)
            if st.button("⬅️ Volver al Historial", use_container_width=True): st.session_state.vale_generado = None; st.rerun()
            st.stop()

        # --- CONTROL DE BLOQUEO Z (LEY ANTIFRAUDE) ---
        res_caja_ab = fetch_caja_abierta_created_at_h(client)
        if res_caja_ab.data:
            inicio_caja_actual = pd.to_datetime(res_caja_ab.data[0]['created_at'], utc=True)
        else:
            inicio_caja_actual = pd.to_datetime('2100-01-01', utc=True) # Todo cerrado

        c_f0, c_f1, c_f2, c_f3 = st.columns([1.5, 1.5, 1, 1])
        with c_f0: b_ticket = st.text_input("🔍 Buscar Nº Ticket:", placeholder="Ej: 145 (Ignora fechas)")
        with c_f1: preset = st.selectbox("Filtro rápido:", ["Esta semana", "Este mes", "Trimestre Actual", "Todo el año"])
        
        hoy = pd.Timestamp.now('Atlantic/Canary').date()
        if preset == "Esta semana": f_ini = hoy - timedelta(days=hoy.weekday())
        elif preset == "Este mes": f_ini = hoy.replace(day=1)
        elif preset == "Trimestre Actual": f_ini = hoy.replace(month=((hoy.month-1)//3)*3+1, day=1)
        else: f_ini = hoy.replace(month=1, day=1)

        with c_f2: f_inicio_v = st.date_input("Desde:", value=f_ini, disabled=bool(b_ticket))
        with c_f3: f_fin_v = st.date_input("Hasta:", value=hoy, disabled=bool(b_ticket))

        if b_ticket and b_ticket.strip().isdigit():
            res_v = fetch_ventas_historial_por_id_h(client, int(b_ticket.strip()))
        else:
            res_v = fetch_ventas_historial_por_fechas_h(client, f_inicio_v, f_fin_v)
        
        if res_v.data:
            df_v = pd.DataFrame(res_v.data)
            try: 
                dt_parsed = pd.to_datetime(df_v['created_at'])
                if dt_parsed.dt.tz is None:
                    dt_parsed = dt_parsed.dt.tz_localize('UTC')
                df_v['Fecha'] = dt_parsed.dt.tz_convert('Atlantic/Canary').dt.strftime('%d/%m/%Y %H:%M')
            except: 
                df_v['Fecha'] = "---"
            
            df_v['Es_Cerrado'] = pd.to_datetime(df_v['created_at'], utc=True) < inicio_caja_actual
            df_v['🔒 Candado'] = df_v['Es_Cerrado'].apply(lambda x: "🔒 Cerrado" if x else "🔓 Abierto")

            for col in ['metodo_pago', 'estado', 'cliente_deuda']:
                if col not in df_v.columns: df_v[col] = "N/A"

            # --- MÉTRICAS DE VENTAS ---
            df_validas = df_v[df_v['estado'] != 'DEVUELTO']
            
            # Para comparar fechas, convertimos created_at al timezone de Canarias primero
            dt_val = pd.to_datetime(df_validas['created_at'])
            if dt_val.dt.tz is None:
                dt_val = dt_val.dt.tz_localize('UTC')
            hoy_str = hoy.strftime('%d/%m/%Y')
            try:
                total_hoy = df_validas[dt_val.dt.tz_convert('Atlantic/Canary').dt.strftime('%d/%m/%Y') == hoy_str]['total'].sum()
            except:
                total_hoy = 0.0
            total_periodo = df_validas['total'].sum()

            cm1, cm2, cm3 = st.columns([1, 1, 2])
            with cm1: st.metric("💶 Ventas Hoy", f"{total_hoy:.2f} €")
            with cm2: st.metric("📅 Ventas Periodo", f"{total_periodo:.2f} €")
            st.markdown("<hr style='margin: 0px 0px 15px 0px; border: none; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

            # 1. PREPARAMOS EL DATAFRAME
            df_vista = df_v[['id', 'Fecha', 'total', 'metodo_pago', 'estado', 'cliente_deuda', '🔒 Candado']].copy()
            
            df_vista.insert(0, "Ver", False)
            
            st.markdown("💡 *Marca **'👁️ Ver'** para abrir el desglose. La eliminación de tickets está bloqueada por Ley Antifraude.*")
            
            # Extraer bancos para el historial
            try:
                res_b_radio = fetch_cuentas_bancarias_nombres_h(client)
                if res_b_radio.data:
                    bancos_nombres = [f"Tarjeta ({b['nombre_banco']})" for b in res_b_radio.data]
                    opciones_pago_hist = ["Efectivo"] + bancos_nombres + ["Bizum", "Mixto"]
                    tiene_bancos = True
                else: 
                    opciones_pago_hist = ["Efectivo", "Tarjeta", "Bizum", "Mixto"]
                    tiene_bancos = False
            except: 
                opciones_pago_hist = ["Efectivo", "Tarjeta", "Bizum", "Mixto"]
                tiene_bancos = False
            
            if 'metodo_pago' in df_vista.columns:
                # Si tenemos bancos específicos, prohibimos explícitamente que la "Tarjeta" genérica vuelva a aparecer
                extras = [m for m in df_vista['metodo_pago'].dropna().unique() if m not in opciones_pago_hist and (not tiene_bancos or m != "Tarjeta")]
                opciones_pago_hist.extend(extras)

            # 2. TABLA EDITABLE CON CASILLA
            edited_df = st.data_editor(
                df_vista,
                column_config={
                    "Ver": st.column_config.CheckboxColumn("👁️ Ver", default=False),
                    "🔒 Candado": st.column_config.TextColumn("Z", disabled=True),
                    "id": st.column_config.NumberColumn("Nº", disabled=True, width="small"),
                    "Fecha": st.column_config.TextColumn("Fecha", disabled=True),
                    "total": st.column_config.NumberColumn("Total (€)", disabled=True, format="%.2f", step=0.01),
                    "metodo_pago": st.column_config.SelectboxColumn("Método", options=opciones_pago_hist),
                    "estado": st.column_config.SelectboxColumn("Estado", options=["Completado", "Deuda", "DEVUELTO"]),
                    "cliente_deuda": st.column_config.TextColumn("Cliente (Si debe)")
                },
                hide_index=True, 
                use_container_width=True, 
                height=250, 
                key="editor_tickets"
            )
            
            # 3. GUARDAR CORRECCIONES EN SUPABASE
            if st.button("💾 Guardar Correcciones de la Tabla", type="primary"):
                df_original = df_vista.drop(columns=["Ver"])
                df_editado = edited_df.drop(columns=["Ver"])
                diferencias = df_editado.compare(df_original)
                if not diferencias.empty:
                    for idx in diferencias.index.tolist():
                        tk_id = int(edited_df.loc[idx, 'id'])
                        estado_nuevo = str(edited_df.loc[idx, 'estado'])
                        estado_antiguo = str(df_original.loc[idx, 'estado'])
                        cliente_str = str(edited_df.loc[idx, 'cliente_deuda'])

                        if df_v[df_v['id'] == tk_id].iloc[0]['Es_Cerrado']:
                            st.toast(f"🚫 Modificación del Ticket #{tk_id} ignorada (Cierre Z).")
                            continue
                            
                        # Si se cambia el estado a Completado (Se saldó la deuda), otorgar puntos
                        if estado_antiguo == "Deuda" and estado_nuevo == "Completado" and cliente_str and cliente_str != 'nan':
                            tot_tk = float(df_v[df_v['id'] == tk_id].iloc[0]['total'])
                            pts_ganar = int(tot_tk // 10)
                            if pts_ganar > 0:
                                res_c = fetch_cliente_puntos_h(client, cliente_str)
                                if res_c.data:
                                    c_id = res_c.data[0]['id']
                                    c_pts = res_c.data[0].get('puntos', 0)
                                    client.table("clientes").update({"puntos": c_pts + pts_ganar}).eq("id", c_id).execute()
                                    client.table("ventas_historial").update({"puntos_ganados": pts_ganar}).eq("id", tk_id).execute()

                        client.table("ventas_historial").update({
                            "metodo_pago": str(edited_df.loc[idx, 'metodo_pago']),
                            "estado": estado_nuevo,
                            "cliente_deuda": cliente_str if cliente_str != 'nan' else ""
                        }).eq("id", tk_id).execute()
                    limpiar_cache_historial()
                    st.success("Tickets actualizados."); time.sleep(0.8); st.rerun()

            st.markdown("---")
            
            # 4. DESGLOSE DEL TICKET SELECCIONADO
            filas_marcadas = edited_df[edited_df["Ver"] == True]
            if not filas_marcadas.empty:
                t_id = filas_marcadas.iloc[0]['id']
                t_info = df_v[df_v['id'] == t_id].iloc[0]
                
                st.markdown(f"#### 🔎 Detalle del Ticket #{t_id} (Bloqueo VeriFactu)")
                st.warning("🔒 **TICKET CERRADO Y ENCRIPTADO**: Por normativa antifraude, los tickets emitidos no se pueden modificar ni eliminar. Para corregir un error, debe emitir una Devolución (Abono).")
                    
                prods_raw = t_info.get('productos', [])
                vale_aplicado_meta = None
                desc_vale_eur_meta = 0.0
                prods = []
                
                # --- FIX: Filtro de seguridad y extracción de metadatos del Vale ---
                if isinstance(prods_raw, list):
                    for p in prods_raw:
                        if isinstance(p, dict):
                            if p.get('__meta__'):
                                vale_aplicado_meta = p.get('vale_aplicado')
                                desc_vale_eur_meta = float(p.get('desc_vale_eur', 0.0))
                            elif p.get('Producto') and str(p.get('Producto')).strip() != "" and p.get('Subtotal') is not None:
                                prods.append(p)

                if prods:
                    df_prods = pd.DataFrame(prods)
                    if 'Desc. %' not in df_prods.columns:
                        df_prods['Desc. %'] = df_prods.get('Desc %', 0.0)
                        
                    # 1. Tabla de productos en modo SOLO LECTURA
                    st.dataframe(df_prods, use_container_width=True, hide_index=True)
                    
                    suma_articulos = df_prods['Subtotal'].sum() if 'Subtotal' in df_prods.columns else 0.0

                    st.markdown("---")
                    # 2. SECCIÓN DE TOTALES (SOLO LECTURA)
                    c_tot1, c_tot2, c_tot3 = st.columns(3)
                    
                    with c_tot1:
                        st.metric("Suma Artículos", f"{suma_articulos:.2f}€")
                    
                    with c_tot2:
                        st.metric("Dto. Global (%)", f"{t_info.get('descuento_global', 0)}%")
                    
                    total_raw = t_info.get('total', 0.0)
                    total_final_calculado = float(total_raw) if total_raw is not None else 0.0
                    
                    with c_tot3:
                        st.metric("TOTAL FINAL", f"{total_final_calculado:.2f}€")

                    if desc_vale_eur_meta > 0:
                        st.info(f"🎟️ **Pagado parcial o totalmente con Vale {vale_aplicado_meta}:** -{desc_vale_eur_meta:.2f}€")

                    # 3. BOTONES DE ACCIÓN
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.button("🚫 Edición Bloqueada (VeriFactu)", disabled=True, use_container_width=True)
                    
                    with c2:
                        if "DEVUELTO" not in str(t_info.get('estado', '')).upper():
                            try:
                                dt_tk = pd.to_datetime(t_info['created_at'])
                                if dt_tk.tzinfo is None: dt_tk = dt_tk.tz_localize('UTC')
                                dias_pasados = (pd.Timestamp.now('Atlantic/Canary') - dt_tk.tz_convert('Atlantic/Canary')).days
                            except:
                                dias_pasados = 0
                                
                            # --- CONFIGURACIÓN DEL REEMBOLSO ---
                            try:
                                res_b_abono = fetch_cuentas_bancarias_abono_h(client)
                                bancos_abono = res_b_abono.data if res_b_abono.data else []
                            except:
                                bancos_abono = []
                            
                            opciones_abono = ["💵 Efectivo (Caja Fuerte)"] + [f"💳 Tarjeta ({b['nombre_banco']})" for b in bancos_abono] + ["📱 Bizum"]
                            
                            metodo_orig = str(t_info.get('metodo_pago', ''))
                            idx_abono_def = 0
                            if "Tarjeta" in metodo_orig:
                                for i, op in enumerate(opciones_abono):
                                    if op.replace("💳 Tarjeta (", "").replace(")", "") in metodo_orig:
                                        idx_abono_def = i
                                        break
                            elif "Bizum" in metodo_orig:
                                idx_abono_def = len(opciones_abono) - 1

                            st.markdown("##### ⚙️ Configurar Devolución")
                            sel_metodo_abono = st.selectbox("Método de reembolso (Si se devuelve dinero):", opciones_abono, index=idx_abono_def)
                                
                            if dias_pasados > 14:
                                st.warning(f"⚠️ Han pasado {dias_pasados} días (Límite 14).")
                                c_btn1, c_btn2 = st.columns(2)
                                with c_btn1: btn_abono = st.button("🛡️ Forzar Abono", use_container_width=True)
                                with c_btn2: btn_vale = st.button("🛡️ Forzar Vale", type="primary", use_container_width=True)
                            else:
                                c_btn1, c_btn2 = st.columns(2)
                                with c_btn1: btn_abono = st.button("💸 Devolver Dinero", use_container_width=True)
                                with c_btn2: btn_vale = st.button("🎁 Crear Vale", type="primary", use_container_width=True)
                                
                            if btn_abono or btn_vale:
                                # Lógica de devolución (la que ya tenías)
                                for p in prods:
                                    if not p.get('Manual', False) and 'id' in p:
                                        if str(p['id']).startswith('cita_'):
                                            continue
                                        try:
                                            res_p = fetch_producto_stock_h(client, p['id'])
                                            if res_p.data:
                                                client.table("productos").update({"stock_actual": res_p.data[0]['stock_actual'] + p['Cantidad']}).eq("id", p['id']).execute()
                                        except Exception:
                                            pass
                                
                                # Revertir puntos si era cliente VIP
                                cliente_vip = str(t_info.get('cliente_vip_nombre', ''))
                                if cliente_vip and cliente_vip != "nan" and cliente_vip != "None":
                                    res_cli = fetch_cliente_puntos_h(client, cliente_vip)
                                    if res_cli.data:
                                        cli_id = res_cli.data[0]['id']
                                        p_ganados = int(t_info.get('puntos_ganados', 0))
                                        p_usados = int(t_info.get('puntos_usados', 0))
                                        nuevo_saldo = max(0, res_cli.data[0].get('puntos', 0) - p_ganados + p_usados)
                                        client.table("clientes").update({"puntos": nuevo_saldo}).eq("id", cli_id).execute()
                                        
                                client.table("ventas_historial").update({"estado": "DEVUELTO"}).eq("id", int(t_id)).execute()
                                
                                if btn_abono:
                                    if "Efectivo" in sel_metodo_abono:
                                        res_caja_ab = fetch_caja_abierta_id_h(client)
                                        if res_caja_ab.data:
                                            client.table("movimientos_caja").insert({
                                                "id_caja": res_caja_ab.data[0]['id'],
                                                "tipo": "Retirada",
                                                "cantidad": total_final_calculado,
                                                "motivo": f"Devolución en efectivo Ticket #{t_id}"
                                            }).execute()
                                    elif "Tarjeta" in sel_metodo_abono:
                                        nombre_banco = sel_metodo_abono.replace("💳 Tarjeta (", "").replace(")", "")
                                        banco = next((b for b in bancos_abono if b['nombre_banco'] == nombre_banco), None)
                                        if banco:
                                            client.table("cuentas_bancarias").update({
                                                "saldo_actual": banco['saldo_actual'] - total_final_calculado
                                            }).eq("id", banco['id']).execute()
                                
                                if btn_vale:
                                    codigo_vale = "VALE-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
                                    try:
                                        client.table("vales_tienda").insert({
                                            "codigo_vale": codigo_vale,
                                            "saldo_inicial": total_final_calculado,
                                            "saldo_actual": total_final_calculado,
                                            "id_ticket_origen": int(t_id),
                                            "notas": f"Generado por devolución de ticket #{t_id}"
                                        }).execute()
                                    except: pass
                                    st.session_state.vale_generado = {"fecha": pd.Timestamp.now('Atlantic/Canary').strftime("%d/%m/%Y %H:%M"), "valor": total_final_calculado, "codigo": codigo_vale}
                                else:
                                    st.session_state.devolucion_actual = {
                                        "fecha": pd.Timestamp.now('Atlantic/Canary').strftime("%d/%m/%Y %H:%M"), "productos": prods,
                                        "total": total_final_calculado, "metodo": sel_metodo_abono, "ticket_original_id": t_id
                                    }
                                limpiar_cache_historial()
                                st.rerun()
                                
                    with c3:
                        try:
                            dt_t = pd.to_datetime(t_info['created_at'])
                            if dt_t.tzinfo is None:
                                dt_t = dt_t.tz_localize('UTC')
                            fecha_t_print = dt_t.tz_convert('Atlantic/Canary').strftime('%d/%m/%Y %H:%M')
                        except:
                            fecha_t_print = "Fecha desconocida"
                            
                        # --- LIMPIEZA DE MÉTODO DE PAGO PARA TICKET/EMAIL ---
                        metodo_reprint = str(t_info.get('metodo_pago', 'Desconocido'))
                        if metodo_reprint.startswith("Tarjeta"):
                            metodo_reprint = "Tarjeta"
                        elif metodo_reprint.startswith("Mixto"):
                            import re
                            metodo_reprint = re.sub(r'\s-\s[^|]+', '', metodo_reprint)

                        # --- PREPARACIÓN DEL EMAIL (HISTORIAL) ---
                        cuerpo_email = (
                            "Hola,\n\nAdjuntamos la copia de su ticket de compra:\n\n"
                            "================================\n"
                            "          ANIMALARIUM\n"
                            "     Raquel Trujillo Hernández\n"
                            "          DNI: 78854854K\n"
                            "   C/ José Hernández Alfonso, 26\n"
                            "       38009 S/C de Tenerife\n"
                            "================================\n"
                            f"Fecha: {fecha_t_print}\n"
                            f"COPIA DE TICKET #{t_id}\n"
                            "--------------------------------\n"
                        )
                        for p in prods:
                            desc_item_raw = p.get('Desc. %', p.get('Desc %', 0.0))
                            try:
                                desc_item = float(desc_item_raw) if desc_item_raw is not None else 0.0
                            except (ValueError, TypeError):
                                desc_item = 0.0
                            sub_val = float(p.get('Subtotal', 0.0))
                            if desc_item > 0:
                                motivo = p.get('Motivo_Desc', '')
                                motivo_str = f" (Dto. {desc_item}% por {motivo})" if motivo else f" (Dto. {desc_item}%)"
                                cuerpo_email += f"{p['Cantidad']}x {p['Producto']}\n  -> {sub_val:.2f}€{motivo_str}\n"
                            else:
                                cuerpo_email += f"{p['Cantidad']}x {p['Producto']}\n  -> {sub_val:.2f}€\n"
                        
                        cuerpo_email += "--------------------------------\n"
                        desc_g_re_raw = t_info.get('descuento_global', 0.0)
                        desc_g_re = float(desc_g_re_raw) if desc_g_re_raw is not None else 0.0
                        if desc_g_re > 0:
                            cuerpo_email += f"Descuento global: {desc_g_re}%\n"
                            
                        if desc_vale_eur_meta > 0:
                            cuerpo_email += f"Vale {vale_aplicado_meta} aplicado: -{desc_vale_eur_meta:.2f}€\n"

                        cuerpo_email += f"TOTAL PAGADO: {total_final_calculado:.2f}€\n"
                        cuerpo_email += f"MÉTODO DE PAGO: {metodo_reprint}\n"
                        cuerpo_email += "================================\n"
                        
                        cliente_vip_reprint = str(t_info.get('cliente_vip_nombre', ''))
                        if cliente_vip_reprint and cliente_vip_reprint != 'nan' and cliente_vip_reprint != 'None':
                            saldo_actual_re = 0
                            res_cli_re = fetch_cliente_puntos_h(client, cliente_vip_reprint)
                            if res_cli_re.data: saldo_actual_re = res_cli_re.data[0].get('puntos', 0)
                            cuerpo_email += f"🌟 CLIENTE VIP: {cliente_vip_reprint}\n"
                            cuerpo_email += f"Puntos ganados en este ticket: +{t_info.get('puntos_ganados', 0)}\n"
                            cuerpo_email += f"Saldo actual disponible: {saldo_actual_re} puntos\n"
                            cuerpo_email += "INFO VIP: Ganas 1 pto por cada 10€ de compra.\n"
                            cuerpo_email += "================================\n"
                            
                        cuerpo_email += "\nPOLÍTICA DE DEVOLUCIÓN:\nPlazo de 14 días con ticket y embalaje original en perfecto estado.\n\nUn saludo,\nAnimalarium."
                        
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

                        html_reprint = f"""
                        <!DOCTYPE html><html><head><meta charset='utf-8'>
                        <style>
                            body {{ margin: 0; padding: 0; font-family: sans-serif; background-color: transparent; }}
                            .pantalla {{ padding: 5px; max-width: 400px; margin: 0 auto; text-align: center; }}
                            .btn-print {{ padding: 12px; background-color: #005275; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%; font-size: 15px; margin-bottom: 8px; }}
                            .btn-email {{ background-color: #2e7d32; }}
                            #ticket-impresion-re {{ display: none; }}
                        </style>
                        </head><body>
                        <div class="pantalla">
                            <button class="btn-print" onclick="reimprimirConStar()">🖨️ IMPRIMIR COPIA (TABLET STAR)</button>
                            <a href="mailto:?subject=Copia%20de%20Ticket%20-%20Animalarium&body={body_encoded}" target="_blank" style="text-decoration: none;">
                                <button class="btn-print btn-email">✉️ ENVIAR COPIA POR EMAIL</button>
                            </a>
                        </div>
                        <div id="ticket-impresion-re">
                            <div style="text-align: center; font-family: monospace; width: 100%; font-size: 22px; color: black; font-weight: bold;">
                                {logo_html}
                                <b style="font-size: 34px;">ANIMALARIUM</b><br>
                                Raquel Trujillo Hernández<br>DNI: 78854854K<br>C/ José Hernández Alfonso, 26<br>38009 S/C de Tenerife<br><br>
                                <div style="text-align: left; font-size: 22px;">Fecha: {fecha_t_print}<br>COPIA DE TICKET #{t_id}</div>
                                <hr style="border-top: 2px dashed #000; margin: 10px 0px;">
                                <table style="width: 100%; font-size: 22px; text-align: left; font-weight: bold;">
                        """
                        for p in prods:
                            desc_item_raw = p.get('Desc. %', p.get('Desc %', 0.0))
                            try:
                                desc_item = float(desc_item_raw) if desc_item_raw is not None else 0.0
                            except (ValueError, TypeError):
                                desc_item = 0.0
                                
                            sub_val = float(p.get('Subtotal', 0.0))
                            if desc_item > 0:
                                motivo = p.get('Motivo_Desc', '')
                                motivo_str = f" por {motivo}" if motivo else ""
                                p_precio_raw = p.get('Precio', p.get('Base Ud', 0) * (1 + p.get('IGIC %', 0)/100))
                                precio_orig = float(p_precio_raw) * float(p['Cantidad'])
                                html_reprint += f"<tr><td style='padding-bottom: 0px;'>{p['Cantidad']}x {p['Producto']}</td><td style='text-align: right; padding-bottom: 0px;'><del>{precio_orig:.2f}€</del> {sub_val:.2f}€</td></tr>"
                                html_reprint += f"<tr><td colspan='2' style='font-size: 16px; padding-bottom: 5px; color: #555;'>  ↳ Dto. {desc_item}% aplicado{motivo_str}</td></tr>"
                            else:
                                html_reprint += f"<tr><td style='padding-bottom: 5px;'>{p['Cantidad']}x {p['Producto']}</td><td style='text-align: right; padding-bottom: 5px;'>{sub_val:.2f}€</td></tr>"
                        html_reprint += f"""
                                </table>
                                <hr style="border-top: 2px dashed #000; margin: 10px 0px;">
                        """
                        desc_g_re_raw = t_info.get('descuento_global', 0.0)
                        desc_g_re = float(desc_g_re_raw) if desc_g_re_raw is not None else 0.0
                        if desc_g_re > 0:
                            subt_re = total_final_calculado / (1 - desc_g_re / 100) if (1 - desc_g_re / 100) > 0 else total_final_calculado
                            descuento_eur = subt_re - total_final_calculado
                            html_reprint += f"<div style='text-align: right; font-size: 22px;'>Subtotal: {subt_re:.2f}€</div>"
                            html_reprint += f"<div style='text-align: right; font-size: 22px;'><b>Dto. Global ({desc_g_re}%): -{descuento_eur:.2f}€</b></div>"
                        
                        if desc_vale_eur_meta > 0:
                            html_reprint += f"<div style='text-align: right; font-size: 22px;'><b>Vale {vale_aplicado_meta}: -{desc_vale_eur_meta:.2f}€</b></div>"

                        html_reprint += f"""
                                <div style="text-align: right; font-size: 28px;"><b>TOTAL: {total_final_calculado:.2f}€</b></div>
                                <div style="font-size: 20px; text-align: left; margin-top: 10px;"><b>Método de pago:</b> {metodo_reprint}</div>
                        """
                        if cliente_vip_reprint and cliente_vip_reprint != 'nan' and cliente_vip_reprint != 'None':
                            html_reprint += f"<div style='font-size:18px; text-align:center; margin-top:15px; border: 1px solid #000; padding: 5px;'><b>🌟 CLIENTE VIP: {cliente_vip_reprint}</b>"
                            html_reprint += f"<br>Puntos ganados en este ticket: +{t_info.get('puntos_ganados', 0)}"
                            html_reprint += f"<br>Saldo actual disponible: {saldo_actual_re} puntos"
                            html_reprint += f"<br><span style='font-size:14px; color:#555;'>Ganas 1 pto por cada 10€ de compra. (1 pto = 0.50€ dto)</span></div>"
                        html_reprint += f"""
                                <div style="text-align: center; margin-top: 25px;">
                                    <img src="https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=TICKET-{t_id}" alt="QR Ticket" />
                                    <div style="font-size: 16px; margin-top: 5px; color: #555;">TICKET #{t_id}</div>
                                </div>
                                <div style="font-size: 18px; color: #000; margin-top: 30px; text-align: center;"><b>POLÍTICA DE DEVOLUCIÓN</b><br>Plazo de 14 días con ticket y<br>embalaje original en perfecto estado.</div>
                            </div>
                        </div>
                        <script>
                        function reimprimirConStar() {{
                            var ticketHTML = document.getElementById('ticket-impresion-re').innerHTML;
                            var fullHTML = "<!DOCTYPE html><html><head><meta charset='utf-8'></head><body style='margin:0; padding:0; background-color:white;'>" + ticketHTML + "</body></html>";
                            var htmlCodificado = encodeURIComponent(fullHTML);
                            var backURL = encodeURIComponent(window.location.href);
                            var starURL = "starpassprnt://v1/print/nopreview?back=" + backURL + "&html=" + htmlCodificado;
                            
                            // Usar un iframe oculto evita que Streamlit se reinicie en la tablet
                            var iframe = document.createElement('iframe');
                            iframe.style.display = 'none';
                            iframe.src = starURL;
                            document.body.appendChild(iframe);
                        }}
                        </script>
                        </body></html>
                        """
                        components.html(html_reprint, height=130, scrolling=False)
                else:
                    st.info("Este ticket no tiene productos registrados.")
            else:
                st.info("👆 Marca la casilla '👁️ Ver' de un ticket arriba para editarlo.")
                
        else: st.info("No hay ventas en este rango de fechas.")

    # --- SUB-PESTAÑA CAJAS (MANTENEMOS TU CÓDIGO ORIGINAL INTACTO) ---
    with sub_h_cajas:
        c_fc1, c_fc2 = st.columns(2)
        with c_fc1: f_inicio_c = st.date_input("Cajas desde:", value=pd.Timestamp.now('Atlantic/Canary').date() - pd.Timedelta(days=7), key="fc1")
        with c_fc2: f_fin_c = st.date_input("Cajas hasta:", value=pd.Timestamp.now('Atlantic/Canary').date(), key="fc2")

        try:
            res_cajas = fetch_cajas_cerradas_por_fecha_h(client, f_inicio_c, f_fin_c)

            if res_cajas.data:
                df_c = pd.DataFrame(res_cajas.data)
                dt_parsed = pd.to_datetime(df_c['created_at'])
                if dt_parsed.dt.tz is None:
                    dt_parsed = dt_parsed.dt.tz_localize('UTC')
                df_c['Fecha Apertura'] = dt_parsed.dt.tz_convert('Atlantic/Canary').dt.strftime('%d/%m/%Y %H:%M')
                df_c_vista = df_c[['id', 'Fecha Apertura', 'fondo_inicial', 'total_contado', 'descuadre']].copy()
                df_c_vista.insert(0, "Seleccionar", False)
                
                st.markdown("💡 *Marca la casilla **'🖨️ Seleccionar'** para ver el desglose e imprimir el Cierre Z.*")
                
                ed_c = st.data_editor(
                    df_c_vista,
                    column_config={
                        "Seleccionar": st.column_config.CheckboxColumn("🖨️ Seleccionar", default=False),
                        "id": None,
                        "Fecha Apertura": "Apertura",
                        "fondo_inicial": st.column_config.NumberColumn("Fondo Inicial (€)", format="%.2f", step=0.01),
                        "total_contado": st.column_config.NumberColumn("Efectivo Final (€)", format="%.2f", step=0.01),
                        "descuadre": st.column_config.NumberColumn("Descuadre (€)", format="%.2f", step=0.01)
                    },
                    hide_index=True, use_container_width=True, height=200
                )

                st.markdown("#### 🖨️ Desglose e Impresión de Cierre")
                filas_sel = ed_c[ed_c["Seleccionar"] == True]
                turno_sel = filas_sel.iloc[0]['id'] if not filas_sel.empty else None
                
                if turno_sel:
                    caja_seleccionada = df_c[df_c['id'] == turno_sel].iloc[0]
                    resumen = caja_seleccionada.get('resumen_pagos', {})
                    if not resumen or pd.isna(resumen): resumen = {"Efectivo": 0, "Tarjeta": 0, "Bizum": 0, "Ingresos": 0, "Retiradas": 0}
                    
                    total_ventas_z = resumen.get('Efectivo', 0) + resumen.get('Tarjeta', 0) + resumen.get('Bizum', 0)
                    
                    tarjetas_html = ''.join([f"Tarjeta ({k.replace('Tarjeta ', '')}): {v:.2f} €<br>" for k, v in resumen.items() if k.startswith('Tarjeta ') and k != 'Tarjeta'])
                    if not tarjetas_html:
                        tarjetas_html = f"Tarjeta: {resumen.get('Tarjeta', 0):.2f} €<br>"

                    import base64
                    logo_html = ""
                    try:
                        with open("LOGO.jpg", "rb") as img_file:
                            b64_string = base64.b64encode(img_file.read()).decode('utf-8')
                            logo_html = f'<img src="data:image/jpeg;base64,{b64_string}" style="max-width: 150px; margin-bottom: 10px;"><br>'
                    except:
                        pass

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
                            <div style="text-align: center;">{logo_html}</div>
                            <div style="text-align: center;">ANIMALARIUM</div>
                            <hr style="border-top: 1px dashed black;">
                            Turno Nº: {turno_sel}<br>
                            Apertura: {caja_seleccionada['Fecha Apertura']}<br>
                            Fondo Inicial: {caja_seleccionada['fondo_inicial']:.2f} €<br>
                            <hr style="border-top: 1px dashed black;">
                            <b>VENTAS POR MÉTODO:</b><br>
                            Efectivo: {resumen.get('Efectivo', 0):.2f} €<br>
                            {tarjetas_html}
                            Bizum: {resumen.get('Bizum', 0):.2f} €<br>
                            <div style="border-top: 1px dotted black; margin: 5px 0;"></div>
                            <b>TOTAL VENTAS: {total_ventas_z:.2f} €</b><br>
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

                    res_movs = fetch_movimientos_caja_por_turno_h(client, turno_sel)
                    if res_movs.data:
                        st.markdown("<p style='font-size:12px; color:gray;'>Detalle de Entradas/Salidas de este turno:</p>", unsafe_allow_html=True)
                        df_m = pd.DataFrame(res_movs.data)
                        dt_mov = pd.to_datetime(df_m['created_at'])
                        if dt_mov.dt.tz is None:
                            dt_mov = dt_mov.dt.tz_localize('UTC')
                        df_m['Hora'] = dt_mov.dt.tz_convert('Atlantic/Canary').dt.strftime('%H:%M')
                        st.dataframe(df_m[['Hora', 'tipo', 'cantidad', 'motivo']], use_container_width=True, hide_index=True)
                    else: st.info("No hubo Entradas o Salidas manuales en este turno.")
            else: st.warning("No hay registros de cajas cerradas en este rango.")
        except Exception as e: st.error(f"Error cargando cajas: {e}")