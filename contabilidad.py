import streamlit as st
import pandas as pd
from datetime import date
import io
import time

def render_pestana_contabilidad(client):
    st.markdown("<h3 style='margin-top: -15px;'>📊 Contabilidad e Informes para Asesoría</h3>", unsafe_allow_html=True)
    
    sec_gastos, sec_fijos, sec_informes = st.tabs(["💸 Gastos Puntuales", "🔄 Gastos Fijos y Calendario", "📂 Panel Avanzado de Descargas"])

    with sec_gastos:
        col_g1, col_g2 = st.columns([1, 2])
        with col_g1:
            with st.form("nuevo_gasto"):
                st.markdown("#### Registrar Gasto o Nómina")
                categoria_gasto = st.selectbox("Categoría Contable", [
                    "Gastos de compra (Limpieza, consumibles...)",
                    "Gastos fijos y variables (Alquileres, seguros, luz, agua...)",
                "Personal y autónomos (Nóminas, SS...)",
                "Servicios exteriores (Reparaciones, técnicos, profesionales...)",
                "Impuestos y Tasas (IGIC, IRPF, tributos...)"
                ])
                concepto = st.text_input("Concepto / Proveedor detallado")
                importe = st.number_input("Importe Total (€)", min_value=0.0, value=None)
                f_vence = st.date_input("Fecha de Vencimiento")
                estado_g = st.selectbox("Estado", ["Pagado", "Pendiente"])
                
                if st.form_submit_button("Guardar Gasto"):
                    if importe is not None and importe > 0 and concepto:
                        client.table("compras").insert({
                            "tipo": f"{categoria_gasto} | {concepto}", "total": float(importe), 
                            "estado": estado_g, "fecha_vencimiento": str(f_vence)
                        }).execute()
                        st.success("Gasto registrado exitosamente."); st.rerun()
                    else:
                        st.error("El importe debe ser mayor que 0 y debes escribir un concepto.")
        
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

    with sec_fijos:
        st.markdown("#### 📅 Previsión de Tesorería y Gastos Recurrentes")
        c_fij1, c_fij2 = st.columns([1, 2])
        
        with c_fij1:
            with st.container(border=True):
                st.markdown("##### ➕ Nuevo Gasto Fijo")
                with st.form("nuevo_gasto_fijo", clear_on_submit=True):
                    f_conc = st.text_input("Concepto (Ej: Alquiler, Luz, Préstamo)")
                    f_cat = st.selectbox("Categoría", [
                        "Gastos fijos y variables (Alquileres, seguros, luz, agua...)", 
                        "Personal y autónomos (Nóminas, SS...)", 
                        "Servicios exteriores", 
                        "Impuestos y Tasas"
                    ])
                    f_imp = st.number_input("Importe Estimado/Fijo (€)", min_value=0.0, format="%.2f")
                    f_dia = st.number_input("Día del mes de cargo", min_value=1, max_value=31, value=1)
                    f_frec = st.selectbox("Frecuencia", ["Mensual", "Bimestral", "Trimestral", "Anual"])
                    
                    if st.form_submit_button("Guardar Gasto Fijo", type="primary", use_container_width=True):
                        try:
                            client.table("gastos_recurrentes").insert({
                                "concepto": f_conc, "categoria": f_cat, "importe_estimado": float(f_imp),
                                "dia_cargo": int(f_dia), "frecuencia": f_frec, "activo": True
                            }).execute()
                            st.success("Gasto fijo registrado."); time.sleep(1); st.rerun()
                        except Exception as e:
                            st.error("⚠️ Ejecuta el código SQL en Supabase primero.")

        with c_fij2:
            st.markdown("##### 📋 Tus Gastos Fijos Activos")
            try:
                res_gf = client.table("gastos_recurrentes").select("*").eq("activo", True).execute()
                if res_gf.data:
                    df_gf = pd.DataFrame(res_gf.data)
                    df_gf_vista = df_gf[['id', 'concepto', 'importe_estimado', 'dia_cargo', 'frecuencia']].copy()
                    df_gf_vista.insert(0, "Desactivar", False)
                    ed_gf = st.data_editor(df_gf_vista, hide_index=True, use_container_width=True, height=210,
                        column_config={
                            "Desactivar": st.column_config.CheckboxColumn("🛑 Quitar"),
                            "concepto": "Concepto", "importe_estimado": st.column_config.NumberColumn("Importe (€)", format="%.2f"),
                            "dia_cargo": "Día del Mes", "frecuencia": "Frecuencia", "id": None
                        })
                    if st.button("💾 Guardar Cambios en Gastos Fijos"):
                        filas_desactivar = ed_gf[ed_gf["Desactivar"] == True]
                        for _, r in filas_desactivar.iterrows():
                            client.table("gastos_recurrentes").update({"activo": False}).eq("id", r['id']).execute()
                        st.rerun()
                else:
                    st.info("No hay gastos fijos registrados.")
            except:
                st.info("🔧 Ejecuta el código SQL en Supabase para activar esta función.")

        st.markdown("---")
        st.markdown("#### 📈 Calendario Visual de Previsión (Próximos 60 días)")
        try:
            hoy_dt = pd.Timestamp(date.today())
            futuro_dt = hoy_dt + pd.Timedelta(days=60)
            proyeccion = []
            
            # 1. Proyectar gastos fijos
            if res_gf.data:
                for gf in res_gf.data:
                    for mes_offset in [0, 1, 2]:
                        target_month = hoy_dt.month + mes_offset
                        target_year = hoy_dt.year
                        if target_month > 12:
                            target_month -= 12; target_year += 1
                        dia_c = min(gf['dia_cargo'], pd.Period(year=target_year, month=target_month, freq='M').days_in_month)
                        fecha_cargo = pd.to_datetime(f"{target_year}-{target_month:02d}-{dia_c:02d}")
                        if hoy_dt <= fecha_cargo <= futuro_dt:
                            proyeccion.append({"Fecha Vencimiento": fecha_cargo, "Concepto": gf['concepto'], "Importe": float(gf['importe_estimado']), "Tipo": "Gasto Fijo (Previsión)"})
                            
            if proyeccion:
                df_proy = pd.DataFrame(proyeccion).sort_values("Fecha Vencimiento")
                c_cal1, c_cal2, c_cal3 = st.columns(3)
                with c_cal1: st.metric("🟠 Previsión 7 días", f"{df_proy[(df_proy['Fecha Vencimiento'] >= hoy_dt) & (df_proy['Fecha Vencimiento'] <= hoy_dt + pd.Timedelta(days=7))]['Importe'].sum():.2f} €")
                with c_cal2: st.metric("🟡 Previsión 30 días", f"{df_proy[(df_proy['Fecha Vencimiento'] > hoy_dt + pd.Timedelta(days=7)) & (df_proy['Fecha Vencimiento'] <= hoy_dt + pd.Timedelta(days=30))]['Importe'].sum():.2f} €")
                with c_cal3: st.metric("🟢 Previsión 30-60 días", f"{df_proy[df_proy['Fecha Vencimiento'] > hoy_dt + pd.Timedelta(days=30)]['Importe'].sum():.2f} €")
                
                df_chart = df_proy.copy()
                df_chart['Semana'] = df_chart['Fecha Vencimiento'].dt.to_period('W').apply(lambda r: f"Semana {r.start_time.strftime('%d/%m')}")
                st.bar_chart(df_chart.groupby('Semana')['Importe'].sum().reset_index().set_index('Semana'), color="#d32f2f")
                df_proy['Fecha Vencimiento'] = df_proy['Fecha Vencimiento'].dt.strftime('%d/%m/%Y')
                st.dataframe(df_proy, use_container_width=True, hide_index=True)
            else: st.success("No hay previsiones de gastos fijos para los próximos 60 días.")
        except Exception as e: pass

    with sec_informes:
        st.markdown("#### 📥 Selector de Fechas Personalizado")
        
        c_inf1, c_inf2 = st.columns(2)
        with c_inf1: f_desde_inf = st.date_input("📅 Desde la fecha:", value=date.today().replace(day=1))
        with c_inf2: f_hasta_inf = st.date_input("📅 Hasta la fecha:", value=date.today())
        
        st.markdown(f"<p style='color: gray; font-size: 13px;'>Filtrando datos entre el <b>{f_desde_inf.strftime('%d/%m/%Y')}</b> y el <b>{f_hasta_inf.strftime('%d/%m/%Y')}</b>.</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        fecha_inicio_q = f"{f_desde_inf}T00:00:00"
        fecha_fin_q = f"{f_hasta_inf}T23:59:59"

        # Mapa de categorías de productos para separar la lógica de IGIC
        res_prod = client.table("productos").select("id, categoria").execute()
        mapa_categorias = {str(p['id']): p.get('categoria', 'Producto') for p in res_prod.data} if res_prod.data else {}

        def safe_float(val, default=0.0):
            if val is None or val == "":
                return default
            try:
                if isinstance(val, str):
                    val = val.replace(',', '.')
                return float(val)
            except:
                return default

        # Recuperar datos de Tickets
        res_v_inf = client.table("ventas_historial").select("id, created_at, total, metodo_pago, cliente_deuda, productos, descuento_global").gte("created_at", fecha_inicio_q).lte("created_at", fecha_fin_q).neq("estado", "DEVUELTO").execute()
        # Recuperar datos de Facturas Emitidas
        res_f_inf = client.table("facturas").select("numero_factura, created_at, total_neto, total_igic, total_final, forma_pago, clientes(nombre_dueno), productos, descuento_global").gte("created_at", fecha_inicio_q).lte("created_at", fecha_fin_q).execute()
        # Recuperar datos de Compras/Gastos
        res_c_inf = client.table("compras").select("id, created_at, tipo, total, estado, productos, proveedores(nombre_empresa, cif)").gte("created_at", fecha_inicio_q).lte("created_at", fecha_fin_q).execute()

        # Construir el SUPER INFORME UNIFICADO DE VENTAS
        ventas_unificadas = []
        
        if res_v_inf.data:
            for t in res_v_inf.data:
                # Calcular Base e IGIC real desde los productos del ticket
                base_t = 0.0
                igic_t = 0.0
                if t.get('productos'):
                    prods = t['productos']
                    if isinstance(prods, str):
                        try:
                            import json
                            prods = json.loads(prods)
                        except:
                            prods = []
                    if isinstance(prods, dict):
                        prods = [prods]
                        
                    for p in prods:
                        if not isinstance(p, dict): continue
                        precio_pvp = safe_float(p.get('Precio', 0.0))
                        cant = safe_float(p.get('Cantidad', 1))
                        desc_item = safe_float(p.get('Desc. %', p.get('Desc %', 0.0)))
                        
                        cat_producto = mapa_categorias.get(str(p.get('id', '')), 'Producto')
                        
                        # Si es Producto, IGIC = 0% en la venta
                        if cat_producto == 'Producto' or p.get('Manual', False):
                            igic_porcentaje = 0.0
                        else:
                            # Si es Servicio, se usa su IGIC
                            igic_porcentaje = float(p.get('IGIC', 7.0))
                        
                        pvp_con_desc = (precio_pvp * cant) * (1 - desc_item / 100)
                        base_linea = pvp_con_desc / (1 + igic_porcentaje / 100)
                        igic_linea = pvp_con_desc - base_linea
                        
                        base_t += base_linea
                        igic_t += igic_linea
                
                # Aplicar descuento global del ticket a la base y al IGIC
                desc_global = float(t.get('descuento_global', 0.0))
                base_t = round(base_t * (1 - desc_global / 100), 2)
                igic_t = round(igic_t * (1 - desc_global / 100), 2)
                
                # Parche de Seguridad Contable: Ajuste proporcional si hubo canjeo de puntos (descuento en euros)
                total_calc = base_t + igic_t
                tot_real = float(t['total'])
                if total_calc > 0 and abs(total_calc - tot_real) > 0.01:
                    ratio = tot_real / total_calc
                    base_t = round(base_t * ratio, 2)
                    igic_t = round(igic_t * ratio, 2)
                
                ventas_unificadas.append({
                    "Fecha": pd.to_datetime(t['created_at']).strftime('%d/%m/%Y'),
                    "Tipo Documento": "Ticket de Venta (TPV)",
                    "Nº Documento": f"T-{t['id']}",
                    "Cliente": t.get('cliente_deuda') if t.get('cliente_deuda') else "Mostrador",
                    "Base Imponible (€)": base_t,
                    "Cuota IGIC (€)": igic_t,
                    "Importe Total (€)": float(t['total']),
                    "Método de Pago": t['metodo_pago']
                })
                
        if res_f_inf.data:
            for f in res_f_inf.data:
                cliente_nom = f['clientes']['nombre_dueno'] if f.get('clientes') else "N/A"
                tot_f = float(f.get('total_final', 0))
                
                # Recalculamos la base y el IGIC leyendo los productos de la factura para aplicar la regla Producto = 0% IGIC
                base_f = 0.0
                igic_f = 0.0
                if f.get('productos'):
                    prods = f['productos']
                    if isinstance(prods, str):
                        try:
                            import json
                            prods = json.loads(prods)
                        except:
                            prods = []
                    if isinstance(prods, dict):
                        prods = [prods]
                        
                    for p in prods:
                        if not isinstance(p, dict): continue
                        precio_pvp = float(p.get('Precio Venta', 0.0))
                        cant = float(p.get('Cantidad', 1))
                        desc_item = float(p.get('Desc %', 0.0))
                        
                        cat_producto = mapa_categorias.get(str(p.get('id', '')), 'Producto')
                        
                        if cat_producto == 'Producto':
                            igic_porcentaje = 0.0
                        else:
                            igic_porcentaje = float(p.get('IGIC %', 7.0))
                        
                        pvp_con_desc = (precio_pvp * cant) * (1 - desc_item / 100)
                        base_linea = pvp_con_desc / (1 + igic_porcentaje / 100)
                        igic_linea = pvp_con_desc - base_linea
                        
                        base_f += base_linea
                        igic_f += igic_linea
                        
                    desc_global = float(f.get('descuento_global', 0.0))
                    base_f = round(base_f * (1 - desc_global / 100), 2)
                    igic_f = round(igic_f * (1 - desc_global / 100), 2)
                else:
                    # Si no hay productos (facturas antiguas sin JSON), asumimos fallback a total neto
                    base_f = float(f.get('total_neto', round(tot_f / 1.07, 2)))
                    igic_f = float(f.get('total_igic', round(tot_f - base_f, 2)))

                ventas_unificadas.append({
                    "Fecha": pd.to_datetime(f['created_at']).strftime('%d/%m/%Y'),
                    "Tipo Documento": "Factura Emitida",
                    "Nº Documento": f"F-{f['numero_factura']}",
                    "Cliente": cliente_nom,
                    "Base Imponible (€)": base_f,
                    "Cuota IGIC (€)": igic_f,
                    "Importe Total (€)": tot_f,
                    "Método de Pago": f['forma_pago']
                })

        df_ventas_unificadas = pd.DataFrame(ventas_unificadas)
        if not df_ventas_unificadas.empty:
            df_ventas_unificadas['Fecha_dt'] = pd.to_datetime(df_ventas_unificadas['Fecha'], format='%d/%m/%Y')
            df_ventas_unificadas = df_ventas_unificadas.sort_values(by="Fecha_dt").drop(columns=['Fecha_dt'])
            
        # --- FUNCIÓN MÁGICA PARA CREAR EXCEL CON FORMATO Y FILA DE TOTALES ---
        def generar_excel_formateado(df, nombre_hoja="Datos"):
            # 1. Calculamos y añadimos la fila de TOTALES debajo
            df_calc = df.copy()
            fila_totales = {}
            for col in df_calc.columns:
                if '€' in col:
                    fila_totales[col] = df_calc[col].sum()
                else:
                    fila_totales[col] = ''
            fila_totales[df_calc.columns[0]] = 'TOTALES'
            df_calc = pd.concat([df_calc, pd.DataFrame([fila_totales])], ignore_index=True)

            output = io.BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            df_calc.to_excel(writer, index=False, sheet_name=nombre_hoja)
            
            workbook = writer.book
            worksheet = writer.sheets[nombre_hoja]
            
            # 2. Formatos profesionales (Cabecera, Celdas Normales, Moneda y Totals)
            formato_cabecera = workbook.add_format({
                'bg_color': '#005275', 'font_color': 'white', 'bold': True,
                'border': 1, 'text_wrap': True, 'align': 'center', 'valign': 'vcenter'
            })
            formato_celda = workbook.add_format({'border': 1, 'valign': 'vcenter'})
            formato_moneda = workbook.add_format({'border': 1, 'valign': 'vcenter', 'num_format': '#,##0.00 €'})
            formato_total = workbook.add_format({'bg_color': '#e8f4f8', 'bold': True, 'border': 1, 'valign': 'vcenter'})
            formato_total_moneda = workbook.add_format({'bg_color': '#e8f4f8', 'bold': True, 'border': 1, 'valign': 'vcenter', 'num_format': '#,##0.00 €'})
            
            # Aplicar bordes a las celdas y auto-ajustar el ancho de las columnas
            for col_num, value in enumerate(df_calc.columns.values):
                worksheet.write(0, col_num, value, formato_cabecera)
                
                # Ancho automático inteligente
                max_len = max([len(str(value))] + [len(str(x)) for x in df_calc[value].astype(str)]) + 2
                worksheet.set_column(col_num, col_num, max_len)
                
                is_currency = ('€' in value)
                
                # Pintar las celdas hacia abajo
                for row_num in range(1, len(df_calc) + 1):
                    es_ultima_fila = (row_num == len(df_calc))
                    celda_val = df_calc.iloc[row_num - 1, col_num]
                    
                    fmt = formato_celda
                    if is_currency: fmt = formato_moneda
                    if es_ultima_fila:
                        fmt = formato_total_moneda if is_currency else formato_total
                        
                    if pd.isna(celda_val) or celda_val == '':
                        worksheet.write_string(row_num, col_num, "", fmt)
                    elif isinstance(celda_val, (int, float)):
                        worksheet.write_number(row_num, col_num, celda_val, fmt)
                    else:
                        worksheet.write_string(row_num, col_num, str(celda_val), fmt)
                
            writer.close()
            return output.getvalue()

        c_down1, c_down2, c_down3 = st.columns(3)
        
        with c_down1:
            st.info("💶 INFORME GLOBAL DE VENTAS (TICKETS + FACTURAS)")
            if not df_ventas_unificadas.empty:
                excel_unificado = generar_excel_formateado(df_ventas_unificadas, "Ventas Totales")
                st.download_button("📥 Descargar Ventas Totales", excel_unificado, f"Ventas_Totales_{f_desde_inf}_al_{f_hasta_inf}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                st.markdown(f"*Total Ventas: {df_ventas_unificadas['Importe Total (€)'].sum():.2f}€*")
            else:
                st.write("Sin ventas en este periodo.")

        with c_down2:
            st.success("📑 SOLO FACTURAS (Para IGIC)")
            if not df_ventas_unificadas.empty:
                df_solo_facturas = df_ventas_unificadas[df_ventas_unificadas['Tipo Documento'] == 'Factura Emitida'].copy()
                df_asesor_f = df_solo_facturas[['Nº Documento', 'Fecha', 'Cliente', 'Base Imponible (€)', 'Cuota IGIC (€)', 'Importe Total (€)', 'Método de Pago']]
                excel_f = generar_excel_formateado(df_asesor_f, "Facturas Emitidas")
                st.download_button("📥 Descargar Solo Facturas", excel_f, f"Solo_Facturas_{f_desde_inf}_al_{f_hasta_inf}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.write("Sin facturas emitidas.")

        with c_down3:
            st.warning("🚚 COMPRAS Y GASTOS (Tickets y Proveedores)")
            if res_c_inf.data:
                compras_list = []
                for c in res_c_inf.data:
                    cat_contable = "Factura de Proveedor (Mercancía)"
                    concepto = c['tipo']
                    
                    # Separar si es un gasto manual o una nómina
                    tipo_str = str(c.get('tipo', ''))
                    if "Gastos de compra" in tipo_str: cat_contable = "Gastos de Compra (Limpieza, Consumibles)"
                    elif "Gastos fijos" in tipo_str: cat_contable = "Gastos Fijos y Variables"
                    elif "Personal" in tipo_str: cat_contable = "Personal y Autónomos"
                    elif "Servicios exteriores" in tipo_str: cat_contable = "Servicios Exteriores y Reparaciones"
                    elif "Impuestos y Tasas" in tipo_str: cat_contable = "Impuestos y Tasas"
                    
                    if " | " in tipo_str:
                        concepto = tipo_str.split(" | ")[1]

                    base_c = float(c['total'])
                    igic_c = 0.0
                    
                    # Si es una factura de proveedor con artículos registrados, escaneamos su Base e IGIC reales
                    if c.get('productos') and cat_contable == "Factura de Proveedor (Mercancía)":
                        try:
                            df_p = pd.DataFrame(c['productos'])
                            if not df_p.empty and 'Base Ud' in df_p.columns and 'Cantidad' in df_p.columns:
                                if 'Desc %' not in df_p.columns: df_p['Desc %'] = 0.0
                                if 'IGIC %' not in df_p.columns: df_p['IGIC %'] = 0.0
                                
                                base_neta_calc = (pd.to_numeric(df_p['Base Ud']) * pd.to_numeric(df_p['Cantidad'])) * (1 - pd.to_numeric(df_p['Desc %'])/100)
                                igic_eur_calc = base_neta_calc * (pd.to_numeric(df_p['IGIC %'])/100)
                                
                                base_b = base_neta_calc.sum()
                                igic_b = igic_eur_calc.sum()
                                ratio = float(c['total']) / (base_b + igic_b) if (base_b + igic_b) > 0 else 1
                                base_c = round(base_b * ratio, 2)
                                igic_c = round(igic_b * ratio, 2)
                        except: pass
                    
                    prov_nombre = f"{c['proveedores']['nombre_empresa']} ({c['proveedores'].get('cif','')})" if isinstance(c.get('proveedores'), dict) else "Acreedor / Gasto General"
                    
                    compras_list.append({
                        "Nº Interno": c['id'],
                        "Fecha": pd.to_datetime(c['created_at']).strftime('%d/%m/%Y'),
                        "Categoría Contable": cat_contable,
                        "Concepto / Referencia": concepto,
                        "Proveedor / Beneficiario": prov_nombre,
                        "Base Imponible (€)": base_c,
                        "Cuota IGIC (€)": igic_c,
                        "Importe Total (€)": float(c['total']),
                        "Estado": c['estado']
                    })
                
                df_asesor_c = pd.DataFrame(compras_list)
                excel_c = generar_excel_formateado(df_asesor_c, "Gastos y Compras")
                st.download_button("📥 Descargar Compras/Gastos", excel_c, f"Gastos_{f_desde_inf}_al_{f_hasta_inf}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.write("Sin compras o gastos en estas fechas.")
