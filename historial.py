import streamlit as st
import pandas as pd
from datetime import date, timedelta
import time
import json
import streamlit.components.v1 as components

def render_pestana_historial(client):
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

            # 1. PREPARAMOS EL DATAFRAME
            df_vista = df_v[['id', 'Fecha', 'total', 'metodo_pago', 'estado', 'cliente_deuda']].copy()
            
            # --- MAGIA TÁCTIL: Añadimos la columna Checkbox ---
            df_vista.insert(0, "Borrar", False)
            df_vista.insert(0, "Ver", False)
            
            st.markdown("💡 *Marca **'👁️ Ver'** para abrir el desglose. Marca **'🗑️ Borrar'** para eliminar. Haz doble clic en las celdas normales para corregirlas.*")
            
            # 2. TABLA EDITABLE CON CASILLA
            edited_df = st.data_editor(
                df_vista,
                column_config={
                    "Ver": st.column_config.CheckboxColumn("👁️ Ver", default=False),
                    "Borrar": st.column_config.CheckboxColumn("🗑️ Borrar", default=False),
                    "id": st.column_config.NumberColumn("Nº", disabled=True, width="small"),
                    "Fecha": st.column_config.TextColumn("Fecha", disabled=True),
                    "total": st.column_config.NumberColumn("Total (€)", disabled=True, format="%.2f"),
                    "metodo_pago": st.column_config.SelectboxColumn("Método", options=["Efectivo", "Tarjeta", "Bizum", "Mixto"]),
                    "estado": st.column_config.SelectboxColumn("Estado", options=["Completado", "Deuda", "DEVUELTO"]),
                    "cliente_deuda": st.column_config.TextColumn("Cliente (Si debe)")
                },
                hide_index=True, 
                use_container_width=True, 
                height=250, 
                key="editor_tickets"
            )
            
            # 2.5 SISTEMA DE BORRADO DE TICKETS (PARA PRUEBAS)
            filas_borrar_tk = edited_df[edited_df["Borrar"] == True]
            if not filas_borrar_tk.empty:
                st.error(f"⚠️ Has marcado {len(filas_borrar_tk)} ticket(s) para eliminar. El stock se restaurará automáticamente (excepto artículos manuales).")
                if st.button("🚨 CONFIRMAR ELIMINACIÓN", type="primary", use_container_width=True):
                    for idx, row in filas_borrar_tk.iterrows():
                        tk_id = row['id']
                        tk_data = df_v[df_v['id'] == tk_id].iloc[0]
                        # Devolver stock solo si el ticket no estaba ya DEVUELTO
                        if str(tk_data.get('estado', '')).upper() != "DEVUELTO":
                            for p in tk_data.get('productos', []):
                                if not p.get('Manual', False) and 'id' in p:
                                    res_p = client.table("productos").select("stock_actual").eq("id", p['id']).execute()
                                    if res_p.data:
                                        client.table("productos").update({"stock_actual": res_p.data[0]['stock_actual'] + p['Cantidad']}).eq("id", p['id']).execute()
                        # Eliminar registro
                        client.table("ventas_historial").delete().eq("id", tk_id).execute()
                    st.success("Ticket(s) eliminado(s) correctamente."); time.sleep(1); st.rerun()

            # 3. GUARDAR CORRECCIONES EN SUPABASE
            if st.button("💾 Guardar Correcciones de la Tabla", type="primary"):
                # Ignoramos las columnas de acción para que no afecten a la base de datos
                df_original = df_vista.drop(columns=["Ver", "Borrar"])
                df_editado = edited_df.drop(columns=["Ver", "Borrar"])
                diferencias = df_editado.compare(df_original)
                if not diferencias.empty:
                    for idx in diferencias.index.tolist():
                        client.table("ventas_historial").update({
                            "metodo_pago": str(edited_df.loc[idx, 'metodo_pago']),
                            "estado": str(edited_df.loc[idx, 'estado']),
                            "cliente_deuda": str(edited_df.loc[idx, 'cliente_deuda']) if str(edited_df.loc[idx, 'cliente_deuda']) != 'nan' else ""
                        }).eq("id", int(edited_df.loc[idx, 'id'])).execute()
                    st.success("Tickets actualizados."); time.sleep(0.8); st.rerun()

            st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
            
           # --- 4. DETALLE DINÁMICO (CON DESCUENTO EDITABLE) ---
            filas_marcadas = edited_df[edited_df["Ver"] == True]
            
            if not filas_marcadas.empty:
                t_id = filas_marcadas.iloc[0]['id']
                t_info = df_v[df_v['id'] == t_id].iloc[0]
                
                st.markdown(f"#### 🔎 Detalle y Edición del Ticket #{t_id}")
                prods = t_info.get('productos', [])
                
                if prods:
                    df_prods = pd.DataFrame(prods)
                    
                    # 1. Tabla de productos editable
                    edit_prods = st.data_editor(
                        df_prods, 
                        column_config={
                            "Subtotal": st.column_config.NumberColumn("Subtotal (€)", format="%.2f", disabled=True),
                            "Manual": None,
                            "IGIC": None,
                            "Precio": st.column_config.NumberColumn("Precio (€)", format="%.2f"),
                            "Desc. %": st.column_config.NumberColumn("Desc. Ud (%)", format="%d%%")
                        },
                        use_container_width=True, 
                        hide_index=True, 
                        num_rows="dynamic",
                        key=f"edit_det_{t_id}"
                    )
                    
                    # Recalcular subtotal de la lista por si hubo cambios en la tabla
                    if 'Cantidad' in edit_prods.columns and 'Precio' in edit_prods.columns:
                        edit_prods['Subtotal'] = (edit_prods['Cantidad'] * edit_prods['Precio']) * (1 - edit_prods.get('Desc. %', 0) / 100)
                    
                    suma_articulos = edit_prods['Subtotal'].sum()

                    st.markdown("---")
                    # 2. SECCIÓN DE TOTALES CON DESCUENTO EDITABLE
                    c_tot1, c_tot2, c_tot3 = st.columns(3)
                    
                    with c_tot1:
                        st.metric("Suma Artículos", f"{suma_articulos:.2f}€")
                    
                    with c_tot2:
                        # Nuevo: Cuadro para cambiar el descuento global del ticket
                        nuevo_desc_global = st.number_input(
                            "Corregir Dto. Global (%)", 
                            min_value=0, 
                            max_value=100, 
                            value=int(t_info.get('descuento_global', 0)),
                            key=f"desc_glob_{t_id}"
                        )
                    
                    # Calculamos el total final aplicando el descuento que haya en el cuadro
                    total_final_calculado = suma_articulos * (1 - nuevo_desc_global / 100)
                    
                    with c_tot3:
                        st.metric("TOTAL FINAL", f"{total_final_calculado:.2f}€", 
                                  delta=f"-{(suma_articulos - total_final_calculado):.2f}€" if nuevo_desc_global > 0 else None)

                    # 3. BOTONES DE ACCIÓN
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if st.button(f"💾 Guardar Todo (Productos + Descuento)", use_container_width=True, type="primary"):
                            nuevo_json = json.loads(edit_prods.to_json(orient='records'))
                            
                            # Actualizamos Supabase con la nueva lista de productos, el nuevo descuento y el nuevo total
                            client.table("ventas_historial").update({
                                "productos": nuevo_json,
                                "descuento_global": float(nuevo_desc_global),
                                "total": float(total_final_calculado)
                            }).eq("id", int(t_id)).execute()
                            st.success(f"Ticket #{t_id} actualizado correctamente.")
                            time.sleep(0.8)
                            st.rerun()
                    
                    with c2:
                        if "DEVUELTO" not in str(t_info.get('estado', '')).upper():
                            if st.button(f"↩️ Devolver y Restaurar Stock", use_container_width=True):
                                # Lógica de devolución (la que ya tenías)
                                for p in prods:
                                    if not p.get('Manual', False) and 'id' in p:
                                        res_p = client.table("productos").select("stock_actual").eq("id", p['id']).execute()
                                        if res_p.data:
                                            client.table("productos").update({"stock_actual": res_p.data[0]['stock_actual'] + p['Cantidad']}).eq("id", p['id']).execute()
                                client.table("ventas_historial").update({"estado": "DEVUELTO"}).eq("id", int(t_id)).execute()
                                st.success("Venta anulada."); time.sleep(0.8); st.rerun()
                                
                    with c3:
                        try:
                            fecha_t_print = pd.to_datetime(t_info['created_at']).strftime('%d/%m/%Y %H:%M')
                        except:
                            fecha_t_print = "Fecha desconocida"
                            
                        html_reprint = f"""
                        <!DOCTYPE html><html><head><meta charset='utf-8'>
                        <style>
                            body {{ margin: 0; padding: 0; font-family: sans-serif; text-align: center; }}
                            .btn-print {{ padding: 12px; background-color: #005275; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%; font-size: 15px; }}
                            #ticket-impresion-re {{ display: none; }}
                        </style>
                        </head><body>
                        <button class="btn-print" onclick="reimprimirConStar()">🖨️ IMPRIMIR COPIA TICKET</button>
                        <div id="ticket-impresion-re">
                            <div style="text-align: center; font-family: monospace; width: 100%; font-size: 22px; color: black; font-weight: bold;">
                                <b style="font-size: 34px;">ANIMALARIUM</b><br>
                                Raquel Trujillo Hernández<br>DNI: 78854854K<br>C/ José Hernández Alfonso, 26<br>38009 S/C de Tenerife<br><br>
                                <div style="text-align: left; font-size: 22px;">Fecha: {fecha_t_print}<br>COPIA DE TICKET #{t_id}</div>
                                <hr style="border-top: 2px dashed #000; margin: 10px 0px;">
                                <table style="width: 100%; font-size: 22px; text-align: left; font-weight: bold;">
                        """
                        for p in prods:
                            desc_item = p.get('Desc %', 0.0)
                            if desc_item > 0:
                                html_reprint += f"<tr><td style='padding-bottom: 0px;'>{p['Cantidad']}x {p['Producto']}</td><td style='text-align: right; padding-bottom: 0px;'>{p['Subtotal']:.2f}€</td></tr>"
                                html_reprint += f"<tr><td colspan='2' style='font-size: 16px; padding-bottom: 5px; color: #555;'>  ↳ Dto. {desc_item}% aplicado</td></tr>"
                            else:
                                html_reprint += f"<tr><td style='padding-bottom: 5px;'>{p['Cantidad']}x {p['Producto']}</td><td style='text-align: right; padding-bottom: 5px;'>{p['Subtotal']:.2f}€</td></tr>"
                        html_reprint += f"""
                                </table>
                                <hr style="border-top: 2px dashed #000; margin: 10px 0px;">
                        """
                        desc_g_re = float(t_info.get('descuento_global', 0.0))
                        if desc_g_re > 0:
                            subt_re = total_final_calculado / (1 - desc_g_re / 100) if (1 - desc_g_re / 100) > 0 else total_final_calculado
                            html_reprint += f"<div style='text-align: right; font-size: 22px;'>Subtotal: {subt_re:.2f}€</div>"
                            html_reprint += f"<div style='text-align: right; font-size: 22px;'><b>Dto. Global: -{desc_g_re}%</b></div>"
                        
                        html_reprint += f"""
                                <div style="text-align: right; font-size: 28px;"><b>TOTAL: {total_final_calculado:.2f}€</b></div>
                                <div style="font-size: 18px; color: #000; margin-top: 30px; text-align: center;"><b>POLÍTICA DE DEVOLUCIÓN</b><br>Plazo de 14 días con ticket y<br>embalaje original en perfecto estado.</div>
                            </div>
                        </div>
                        <script>
                        function reimprimirConStar() {{
                            var ticketHTML = document.getElementById('ticket-impresion-re').innerHTML;
                            var fullHTML = "<!DOCTYPE html><html><head><meta charset='utf-8'></head><body style='margin:0; padding:0; background-color:white;'>" + ticketHTML + "</body></html>";
                            var htmlCodificado = encodeURIComponent(fullHTML);
                            var urlRetorno = "https://google.com";
                            try {{ if (window.top.location.href && window.top.location.href !== "about:blank") {{ urlRetorno = window.top.location.href; }} }} catch(e) {{}}
                            window.top.location.href = "starpassprnt://v1/print/nopreview?back=" + encodeURIComponent(urlRetorno) + "&html=" + htmlCodificado;
                        }}
                        </script>
                        </body></html>
                        """
                        components.html(html_reprint, height=55)
                else:
                    st.info("Este ticket no tiene productos registrados.")
            else:
                st.info("👆 Marca la casilla '👁️ Ver' de un ticket arriba para editarlo.")
                
        else: st.info("No hay ventas en este rango de fechas.")

    # --- SUB-PESTAÑA CAJAS (MANTENEMOS TU CÓDIGO ORIGINAL INTACTO) ---
    with sub_h_cajas:
        c_fc1, c_fc2 = st.columns(2)
        with c_fc1: f_inicio_c = st.date_input("Cajas desde:", value=pd.to_datetime('today') - pd.Timedelta(days=7), key="fc1")
        with c_fc2: f_fin_c = st.date_input("Cajas hasta:", value=pd.to_datetime('today'), key="fc2")

        try:
            res_cajas = client.table("control_caja").select("*").eq("estado", "Cerrada").gte("created_at", f"{f_inicio_c}T00:00:00").lte("created_at", f"{f_fin_c}T23:59:59").order("id", desc=True).execute()

            if res_cajas.data:
                df_c = pd.DataFrame(res_cajas.data)
                df_c['Fecha Apertura'] = pd.to_datetime(df_c['created_at']).dt.strftime('%d/%m/%Y %H:%M')
                df_c_vista = df_c[['id', 'Fecha Apertura', 'fondo_inicial', 'total_contado', 'descuadre']].copy()
                df_c_vista.insert(0, "Seleccionar", False)
                
                st.markdown("💡 *Marca la casilla **'🖨️ Seleccionar'** para ver el desglose e imprimir el Cierre Z.*")
                
                ed_c = st.data_editor(
                    df_c_vista,
                    column_config={
                        "Seleccionar": st.column_config.CheckboxColumn("🖨️ Seleccionar", default=False),
                        "id": None,
                        "Fecha Apertura": "Apertura",
                        "fondo_inicial": st.column_config.NumberColumn("Fondo Inicial (€)", format="%.2f"),
                        "total_contado": st.column_config.NumberColumn("Efectivo Final (€)", format="%.2f"),
                        "descuadre": st.column_config.NumberColumn("Descuadre (€)", format="%.2f")
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