import streamlit as st
import pandas as pd
from datetime import date, timedelta
import io
import time

@st.cache_data(show_spinner=False, ttl=300)
def fetch_compras_pendientes(_client):
    return _client.table("compras").select("*, proveedores(nombre_empresa)").eq("estado", "Pendiente").execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_gastos_recurrentes_activos(_client):
    return _client.table("gastos_recurrentes").select("*").eq("activo", True).execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_compras_gastos_fijos(_client):
    return _client.table("compras").select("tipo").ilike("tipo", "Gastos Fijos | %").execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_compras_no_pagadas(_client):
    return _client.table("compras").select("*, proveedores(nombre_empresa)").neq("estado", "Pagado").order("created_at").execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_cuentas_bancarias(_client):
    return _client.table("cuentas_bancarias").select("id, nombre_banco, saldo_actual").execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_caja_abierta(_client):
    return _client.table("control_caja").select("*").eq("estado", "Abierta").execute()

class PostgrestResult:
    def __init__(self, data):
        self.data = data

@st.cache_data(show_spinner=False, ttl=300)
def fetch_compras_archivo(_client, f_ini_arc, f_fin_arc):
    all_data = []
    limit = 1000
    offset = 0
    while True:
        res = _client.table("compras").select("*, proveedores(nombre_empresa)").gte("created_at", f"{f_ini_arc}T00:00:00").lte("created_at", f"{f_fin_arc}T23:59:59").range(offset, offset + limit - 1).order("id", desc=True).execute()
        if not res.data: break
        all_data.extend(res.data)
        if len(res.data) < limit: break
        offset += limit
    return PostgrestResult(all_data)

def fetch_producto_stock(_client, p_id):
    return _client.table("productos").select("stock_actual").eq("id", p_id).execute()

def fetch_productos_categorias(_client):
    # También paginamos los productos porque el inventario puede tener más de 1000 artículos
    all_data = []
    limit = 1000
    offset = 0
    while True:
        res = _client.table("productos").select("id, nombre, categoria").range(offset, offset + limit - 1).order("id").execute()
        if not res.data: break
        all_data.extend(res.data)
        if len(res.data) < limit: break
        offset += limit
    return PostgrestResult(all_data)

@st.cache_data(show_spinner=False, ttl=300)
def fetch_ventas_informe(_client, fecha_inicio_q, fecha_fin_q):
    all_data = []
    limit = 1000
    offset = 0
    while True:
        res = _client.table("ventas_historial").select("id, created_at, total, metodo_pago, estado, cliente_deuda, productos, descuento_global").gte("created_at", fecha_inicio_q).lte("created_at", fecha_fin_q).range(offset, offset + limit - 1).order("id").execute()
        if not res.data: break
        all_data.extend(res.data)
        if len(res.data) < limit: break
        offset += limit
    return PostgrestResult(all_data)

@st.cache_data(show_spinner=False, ttl=300)
def fetch_facturas_informe(_client, fecha_inicio_q, fecha_fin_q):
    all_data = []
    limit = 1000
    offset = 0
    while True:
        res = _client.table("facturas").select("numero_factura, created_at, total_neto, total_igic, total_final, forma_pago, clientes(nombre_dueno, cif), productos, descuento_global").gte("created_at", fecha_inicio_q).lte("created_at", fecha_fin_q).range(offset, offset + limit - 1).order("id").execute()
        if not res.data: break
        all_data.extend(res.data)
        if len(res.data) < limit: break
        offset += limit
    return PostgrestResult(all_data)

@st.cache_data(show_spinner=False, ttl=300)
def fetch_compras_informe(_client, fecha_inicio_q, fecha_fin_q):
    all_data = []
    limit = 1000
    offset = 0
    while True:
        res = _client.table("compras").select("id, created_at, fecha_factura, tipo, total, estado, productos, proveedores(nombre_empresa, cif)").gte("created_at", fecha_inicio_q).lte("created_at", fecha_fin_q).range(offset, offset + limit - 1).order("id").execute()
        if not res.data: break
        all_data.extend(res.data)
        if len(res.data) < limit: break
        offset += limit
    return PostgrestResult(all_data)

@st.cache_data(show_spinner=False, ttl=300)
def fetch_gastos_recurrentes_cat(_client):
    return _client.table("gastos_recurrentes").select("concepto, categoria").execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_gastos_recurrentes_inf(_client):
    return _client.table("gastos_recurrentes").select("concepto, categoria, importe_estimado, dia_cargo, frecuencia").eq("activo", True).execute()

def limpiar_cache_contabilidad():
    fetch_compras_pendientes.clear()
    fetch_gastos_recurrentes_activos.clear()
    fetch_compras_gastos_fijos.clear()
    fetch_compras_no_pagadas.clear()
    fetch_cuentas_bancarias.clear()
    fetch_caja_abierta.clear()
    fetch_compras_archivo.clear()
    fetch_producto_stock.clear()
    fetch_productos_categorias.clear()
    fetch_ventas_informe.clear()
    fetch_facturas_informe.clear()
    fetch_compras_informe.clear()
    fetch_gastos_recurrentes_cat.clear()
    fetch_gastos_recurrentes_inf.clear()

def render_pestana_contabilidad(client):
    if 'llave_cont_pago_venc' not in st.session_state: st.session_state.llave_cont_pago_venc = 0
    if 'llave_cont_pago' not in st.session_state: st.session_state.llave_cont_pago = 0

    st.markdown("<h3 style='margin-top: -15px;'>📊 Contabilidad e Informes para Asesoría</h3>", unsafe_allow_html=True)
    
    sec_gastos, sec_fijos, sec_calendario, sec_pagos, sec_archivo, sec_informes = st.tabs([
        "💸 Gastos Puntuales", "🔄 Configurar Gastos Fijos", "📅 Calendarios y Vencimientos", 
        "💰 Pagos Pendientes", "📖 Archivo Contable", "📂 Descargas"
    ])

    with sec_gastos:
        col_g1, col_g2 = st.columns([1, 2])
        with col_g1:
            with st.form("nuevo_gasto"):
                st.markdown("#### Registrar Gasto")
                categoria_gasto = st.selectbox("Categoría Contable", [
                    "Gastos de compra (Limpieza, consumibles...)",
                    "Servicios exteriores (Reparaciones, técnicos, profesionales...)",
                    "Impuestos y Tasas",  # Añadir esta opción para los pagos del asesor
                    "Personal y Profesionales (Nóminas, SS...)" # Para pagos de SS del autónomo, etc.
                ])
                concepto = st.text_input("Concepto / Proveedor detallado")
                importe = st.number_input("Importe Total (€)", min_value=0.0, value=None, step=0.01, format="%.2f")
                f_vence = st.date_input("Fecha de Vencimiento")
                estado_g = st.selectbox("Estado", ["Pagado", "Pendiente"])
                
                if st.form_submit_button("Guardar Gasto"):
                    tipo_final = f"{categoria_gasto} | {concepto}"
                    if importe is not None and importe > 0 and concepto:
                        client.table("compras").insert({
                            "tipo": tipo_final, "total": float(importe), 
                            "estado": estado_g, "fecha_vencimiento": str(f_vence)
                        }).execute()
                        limpiar_cache_contabilidad()
                        st.success("Gasto registrado exitosamente."); st.rerun()
                    else:
                        st.error("El importe debe ser mayor que 0 y debes escribir un concepto.")
        
        with col_g2:
            st.markdown("#### Alertas de Vencimientos (Gastos Puntuales)")
            st.info("Si registras un gasto puntual como 'Pendiente', su alerta aparecerá aquí.")
            res_comp = fetch_compras_pendientes(client)
            
            # Filtrar de forma segura en Python
            datos_alertas = [c for c in (res_comp.data or []) if "Factura:" not in str(c.get('tipo', ''))]
            
            if datos_alertas:
                hoy_date = pd.Timestamp.now('Atlantic/Canary').date()
                for c in datos_alertas:
                    dias = (pd.to_datetime(c['fecha_vencimiento']).date() - hoy_date).days
                    clase = "vencido" if dias < 0 else "proximo"
                    nombre = c['tipo']
                    st.markdown(f"<p class='{clase}'>⚠️ {nombre} - {c['total']}€ (Vence en {dias} días: {c['fecha_vencimiento']})</p>", unsafe_allow_html=True)
            else:
                st.info("No hay gastos puntuales pendientes. ¡Todo al día!")

    with sec_fijos:
        st.markdown("#### ➕ Registrar/Editar Gastos Fijos Recurrentes")
        c_fij1, c_fij2 = st.columns([1, 2])
        
        with c_fij1:
            with st.container(border=True):
                st.markdown("##### ➕ Nuevo Gasto Fijo")
                with st.form("nuevo_gasto_fijo", clear_on_submit=True):
                    f_conc = st.text_input("Concepto (Ej: Alquiler, Luz, Préstamo)")
                    f_cat = st.selectbox("Categoría", [
                        "Gastos de Tienda y Suministros (Alquiler, Luz, Agua, Teléfono, Alarma, Software, Garaje...)",
                        "Personal y Profesionales (Nóminas, SS, Autónomo, Asesoría/Gestoría...)",
                        "Financiación y Seguros (Préstamos, Tarjetas, Pólizas, Comisiones...)",
                        "Publicidad y Marketing (Redes sociales, Promociones, Web...)",
                        "Impuestos y Tasas (IGIC, IRPF, Tributos...)"
                    ])
                    f_imp = st.number_input("Importe Estimado/Fijo (€)", min_value=0.0, format="%.2f", step=0.01)
                    f_dia = st.number_input("Día del mes de cargo", min_value=1, max_value=31, value=1, help="Pon 31 si quieres que se cobre el último día del mes (el programa lo ajustará a 28 o 30 según corresponda automáticamente).")
                    f_frec = st.selectbox("Frecuencia", ["Mensual", "Bimestral", "Trimestral", "Anual"])
                    
                    if st.form_submit_button("Guardar Gasto Fijo", type="primary", use_container_width=True):
                        try:
                            client.table("gastos_recurrentes").insert({
                                "concepto": f_conc, "categoria": f_cat, "importe_estimado": float(f_imp),
                                "dia_cargo": int(f_dia), "frecuencia": f_frec, "activo": True
                            }).execute()
                            limpiar_cache_contabilidad()
                            st.success("Gasto fijo registrado."); time.sleep(1); st.rerun()
                        except Exception as e:
                            st.error("⚠️ Ejecuta el código SQL en Supabase primero.")

        with c_fij2:
            st.markdown("##### 📋 Tus Gastos Fijos Activos")
            try:
                res_gf = fetch_gastos_recurrentes_activos(client)
                if res_gf.data:
                    df_gf = pd.DataFrame(res_gf.data)
                    df_gf_vista = df_gf[['id', 'concepto', 'categoria', 'importe_estimado', 'dia_cargo', 'frecuencia']].copy()
                    df_gf_vista.insert(0, "Desactivar", False)
                    ed_gf = st.data_editor(df_gf_vista, hide_index=True, use_container_width=True, height=210,
                        column_config={
                            "Desactivar": st.column_config.CheckboxColumn("🛑 Quitar"),
                            "concepto": "Concepto", 
                            "categoria": st.column_config.SelectboxColumn("Categoría", options=[
                                "Gastos de Tienda y Suministros (Alquiler, Luz, Agua, Teléfono, Alarma, Software, Garaje...)",
                                "Personal y Profesionales (Nóminas, SS, Autónomo, Asesoría/Gestoría...)",
                                "Financiación y Seguros (Préstamos, Tarjetas, Pólizas, Comisiones...)",
                                "Publicidad y Marketing (Redes sociales, Promociones, Web...)",
                                "Impuestos y Tasas (IGIC, IRPF, Tributos...)"
                            ]),
                            "importe_estimado": st.column_config.NumberColumn("Importe (€)", format="%.2f", step=0.01),
                            "dia_cargo": st.column_config.NumberColumn("Día del Mes", min_value=1, max_value=31, step=1), 
                            "frecuencia": st.column_config.SelectboxColumn("Frecuencia", options=["Mensual", "Bimestral", "Trimestral", "Anual"]), 
                            "id": None
                        })
                    if st.button("💾 Guardar Cambios en Gastos Fijos"):
                        # Procesar eliminaciones
                        filas_desactivar = ed_gf[ed_gf["Desactivar"] == True]
                        for _, r in filas_desactivar.iterrows():
                            client.table("gastos_recurrentes").update({"activo": False}).eq("id", r['id']).execute()
                        
                        # Procesar modificaciones del resto de filas activas
                        filas_mantener = ed_gf[ed_gf["Desactivar"] == False]
                        for _, r in filas_mantener.iterrows():
                            client.table("gastos_recurrentes").update({
                                "concepto": str(r['concepto']),
                                "categoria": str(r['categoria']),
                                "importe_estimado": float(r['importe_estimado']),
                                "dia_cargo": int(r['dia_cargo']),
                                "frecuencia": str(r['frecuencia'])
                            }).eq("id", r['id']).execute()
                            
                        limpiar_cache_contabilidad()
                        st.success("Cambios en gastos fijos actualizados correctamente.")
                        time.sleep(0.5)
                        st.rerun()
                else:
                    st.info("No hay gastos fijos registrados.")
            except Exception as e:
                st.error(f"🔧 Error al cargar o guardar gastos fijos: {e}")

    with sec_calendario:
        st.markdown("#### 📅 Calendarios de Vencimientos (Operativos e Impuestos)")
        st.info("Visualiza y gestiona tus pagos programados. Al confirmarlos aquí, se registrarán en tu Libro Mayor (Archivo Contable).")
        
        dias_alerta = st.slider("🔔 Mostrar alarmas para vencimientos dentro de los próximos (días):", min_value=1, max_value=30, value=15)
            
        try:
            res_gf = fetch_gastos_recurrentes_activos(client)
            res_compras_gf = fetch_compras_gastos_fijos(client)
            pagos_registrados = [c['tipo'] for c in res_compras_gf.data] if res_compras_gf.data else []
            
            hoy_dt = pd.Timestamp.now('Atlantic/Canary').normalize().tz_localize(None)
            futuro_dt = hoy_dt + pd.Timedelta(days=60)
            pasado_dt = hoy_dt - pd.Timedelta(days=30) # Miramos también un mes atrás para ver los atrasados
            proyeccion = []
            
            if res_gf.data:
                for gf in res_gf.data:
                    for mes_offset in [-1, 0, 1, 2]:
                        target_month = hoy_dt.month + mes_offset
                        target_year = hoy_dt.year
                        if target_month > 12:
                            target_month -= 12; target_year += 1
                        elif target_month < 1:
                            target_month += 12; target_year -= 1
                            
                        dia_c = min(gf['dia_cargo'], pd.Period(year=target_year, month=target_month, freq='M').days_in_month)
                        fecha_cargo = pd.to_datetime(f"{target_year}-{target_month:02d}-{dia_c:02d}")

                        if pasado_dt <= fecha_cargo <= futuro_dt:
                            tipo_id = f"Gastos Fijos | {gf['concepto']} - {target_month:02d}/{target_year}"
                            estado_pago = "Pagado ✅" if tipo_id in pagos_registrados else "Pendiente ❌"
                            
                            proyeccion.append({
                                "Fecha Vencimiento": fecha_cargo,
                                "Concepto": gf['concepto'],
                                "Categoría": gf['categoria'],
                                "Importe": float(gf['importe_estimado']),
                                "Estado": estado_pago,
                                "ID_Pago": tipo_id
                            })
                            
            if proyeccion:
                df_proy = pd.DataFrame(proyeccion).sort_values("Fecha Vencimiento")
                
                # --- NUEVA GRÁFICA VISUAL DE VENCIMIENTOS ---
                st.markdown("##### 📊 Concentración de Pagos (Próximos 60 días)")
                df_chart_cal = df_proy.copy()
                df_chart_cal['Día'] = df_chart_cal['Fecha Vencimiento'].dt.strftime('%d/%m')
                chart_data_cal = df_chart_cal[df_chart_cal['Estado'] == 'Pendiente ❌'].groupby('Día')['Importe'].sum().reset_index().set_index('Día')
                st.bar_chart(chart_data_cal, color="#d32f2f", height=200)

                # --- SISTEMA DE ALERTAS UNIFICADO ---
                df_alarmas = df_proy[(df_proy['Estado'] == "Pendiente ❌") & (df_proy['Fecha Vencimiento'] <= (hoy_dt + pd.Timedelta(days=dias_alerta)))]
                if not df_alarmas.empty:
                    with st.expander(f"🚨 ALERTA DE PAGOS: Tienes {len(df_alarmas)} vencimiento(s) atrasados o muy próximos", expanded=False):
                        for _, r in df_alarmas.iterrows():
                            dias_diff = (r['Fecha Vencimiento'] - hoy_dt).days
                            texto_dias = "HOY" if dias_diff == 0 else (f"VENCIDO hace {abs(dias_diff)} días" if dias_diff < 0 else f"en {dias_diff} días")
                            icono = "🏛️" if "Impuestos" in r['Categoría'] else "🏢"
                            st.markdown(f"<span style='color:#d32f2f; font-size:15px; font-weight:bold;'>{icono} {r['Concepto']} - {r['Importe']:.2f}€ ({texto_dias})</span>", unsafe_allow_html=True)
                else:
                    st.success(f"✅ Todo al día. No hay ningún Gasto Fijo o Impuesto pendiente en los próximos {dias_alerta} días.")
                        
                st.markdown("---")
                
                df_impuestos = df_proy[df_proy['Categoría'].str.contains('Impuestos', case=False, na=False)]
                df_operativos = df_proy[~df_proy['Categoría'].str.contains('Impuestos', case=False, na=False)]
                
                # --- VISTA DIVIDIDA: OPERATIVOS VS IMPUESTOS ---
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    st.markdown("##### 🏢 Gastos Operativos (Fijos)")
                    st.caption("Alquiler, Nóminas, Seguros Sociales, Luz, Seguros, etc.")
                    if not df_operativos.empty:
                        df_op_v = df_operativos[['Fecha Vencimiento', 'Concepto', 'Importe', 'Estado']].copy()
                        df_op_v['Fecha Vencimiento'] = df_op_v['Fecha Vencimiento'].dt.strftime('%d/%m/%Y')
                        st.dataframe(df_op_v, hide_index=True, use_container_width=True)
                    else:
                        st.info("No hay gastos fijos operativos configurados.")
                with col_c2:
                    st.markdown("##### 🏛️ Calendario de Impuestos")
                    st.caption("Trimestrales, IGIC, IRPF, Retenciones (Mod. 115)...")
                    if not df_impuestos.empty:
                        df_imp_v = df_impuestos[['Fecha Vencimiento', 'Concepto', 'Importe', 'Estado']].copy()
                        df_imp_v['Fecha Vencimiento'] = df_imp_v['Fecha Vencimiento'].dt.strftime('%d/%m/%Y')
                        st.dataframe(df_imp_v, hide_index=True, use_container_width=True)
                    else:
                        st.info("No hay impuestos configurados.")
                        
                st.markdown("---")
                
                # Formulario para marcar pagos
                pendientes_list = df_proy[df_proy['Estado'] == "Pendiente ❌"]
                if not pendientes_list.empty:
                    with st.expander("💸 **Confirmar Pago de Vencimiento (Tachar del calendario)**", expanded=False):
                        with st.form("form_pagar_gf"):
                            opciones_pago = [f"{r['ID_Pago']} ({r['Importe']}€)" for _, r in pendientes_list.iterrows()]
                            sel_pago = st.selectbox("Selecciona el gasto a marcar como pagado:", opciones_pago, key=f"cp_sel_{st.session_state.llave_cont_pago_venc}")
                            if st.form_submit_button("✅ Registrar Pago y Archivar", type="primary"):
                                partes = sel_pago.rsplit(" (", 1)
                                id_sel = partes[0]
                                importe_sel = float(partes[1].replace("€)", ""))
                                client.table("compras").insert({
                                    "tipo": id_sel, "total": importe_sel,
                                    "estado": "Pagado", "fecha_vencimiento": str(pd.Timestamp.now('Atlantic/Canary').date())
                                }).execute()
                                limpiar_cache_contabilidad()
                                st.session_state.llave_cont_pago_venc += 1
                                st.success("¡Vencimiento saldado! Se ha guardado automáticamente en el Archivo Contable."); time.sleep(1.5); st.rerun()

            else: st.success("No hay previsiones de gastos fijos.")
        except Exception as e:
            st.error(f"Error al cargar calendario: {e}")

    with sec_pagos:
        st.markdown("#### 💰 Control de Pagos Pendientes (Gastos Puntuales)")
        st.info("💡 **IMPORTANTE:** Aquí SOLO aparecen los **Gastos Puntuales** (reparaciones, compras extra) que registraste manualmente con el estado **'Pendiente'**. Los vencimientos de tus Gastos Fijos e Impuestos se gestionan desde la pestaña '📅 Calendarios'.")
        
        res_deudas_g = fetch_compras_no_pagadas(client)
        
        # Filtrar descartando facturas y abonos de proveedor de forma segura
        datos_filtrados_g = [d for d in (res_deudas_g.data or []) if "Factura:" not in str(d.get('tipo', '')) and "Abono:" not in str(d.get('tipo', ''))]
        
        if datos_filtrados_g:
            df_deudas = pd.DataFrame(datos_filtrados_g)
            df_deudas['Concepto'] = df_deudas['tipo']
            df_deudas['Fecha Vencimiento'] = pd.to_datetime(df_deudas['fecha_vencimiento'], errors='coerce')
            
            df_deudas['pagado'] = pd.to_numeric(df_deudas.get('pagado', 0.0)).fillna(0.0)
            df_deudas['pendiente'] = df_deudas.apply(
                lambda r: float(r['total']) - r['pagado'] if 'pendiente' not in df_deudas.columns or pd.isna(r.get('pendiente')) else float(r.get('pendiente', 0.0)), 
                axis=1
            )
            df_deudas['pendiente'] = df_deudas['pendiente'].apply(lambda x: max(0.0, x))
            
            hoy_date = pd.Timestamp.now('Atlantic/Canary').normalize().tz_localize(None)
            
            def calc_estado_venc(fecha):
                if pd.isna(fecha): return "⚪ Sin fecha"
                dias = (fecha - hoy_date).days
                if dias < 0: return f"🔴 CADUCADO (hace {abs(dias)} días)"
                elif dias <= 3: return f"⚠️ Vence pronto (en {dias} días)"
                else: return f"🟢 En plazo (en {dias} días)"

            df_deudas['Estado Vencimiento'] = df_deudas['Fecha Vencimiento'].apply(calc_estado_venc)
            df_deudas['Vence'] = df_deudas['Fecha Vencimiento'].dt.strftime('%d/%m/%Y').fillna('-')
            
            st.markdown(f"<h3 style='color: #d32f2f;'>Deuda Total en Gastos Puntuales: {df_deudas['pendiente'].sum():.2f} €</h3>", unsafe_allow_html=True)
            
            df_vista_p = df_deudas[['id', 'Concepto', 'total', 'pendiente', 'Vence', 'Estado Vencimiento']].copy()
            df_vista_p.insert(0, "A Pagar Hoy (€)", 0.0)
            df_vista_p = df_vista_p.sort_values(by='Estado Vencimiento', ascending=False)
            
            def highlight_vencidos(val):
                if isinstance(val, str):
                    if 'CADUCADO' in val: return 'color: red; font-weight: bold'
                    elif 'Vence pronto' in val: return 'color: orange; font-weight: bold'
                return ''

            ed_deudas = st.data_editor(
                df_vista_p.style.map(highlight_vencidos, subset=['Estado Vencimiento']), 
                hide_index=True, use_container_width=True, key="ed_deudas_contabilidad",
                column_config={
                    "A Pagar Hoy (€)": st.column_config.NumberColumn("A Pagar Hoy (€)", min_value=0.0, format="%.2f", step=0.01), 
                    "id": None, "Concepto": "Documento", 
                    "total": st.column_config.NumberColumn("Total (€)", format="%.2f", disabled=True, step=0.01),
                    "pendiente": st.column_config.NumberColumn("Pendiente (€)", format="%.2f", disabled=True, step=0.01)
                }
            )
            
            filas_pagar = ed_deudas[ed_deudas["A Pagar Hoy (€)"] > 0]
            if not filas_pagar.empty:
                errores_exceso = filas_pagar[filas_pagar["A Pagar Hoy (€)"] > filas_pagar["pendiente"]]
                if not errores_exceso.empty:
                    st.error("⚠️ Has introducido un importe a pagar superior a la deuda pendiente en algún gasto. Por favor, corrígelo antes de continuar.")
                else:
                    total_a_pagar = filas_pagar['A Pagar Hoy (€)'].sum()
                    st.markdown("---")
                    st.markdown(f"**Has indicado pagos para {len(filas_pagar)} gasto(s) por un total de <span style='color: #005275; font-size: 1.2em;'>{total_a_pagar:.2f} €</span>**", unsafe_allow_html=True)
                    
                    res_b = fetch_cuentas_bancarias(client)
                    opciones_pago = ["💵 Caja Fuerte (Efectivo de la tienda)"]
                    mapa_bancos = {}
                    if res_b.data:
                        for b in res_b.data:
                            etiqueta = f"🏦 {b['nombre_banco']} ({b['saldo_actual']:.2f} €)"
                            opciones_pago.append(etiqueta)
                            mapa_bancos[etiqueta] = b['id']
                    opciones_pago.append("🤷‍♂️ No registrar origen (Ajuste antiguo)")

                    sel_origen = st.selectbox("💳 Selecciona el origen de los fondos para el pago:", [""] + opciones_pago, key=f"sel_origen_cont_{st.session_state.llave_cont_pago}")
                    
                    if sel_origen and st.button("✅ Confirmar Pago de Gastos", type="primary", use_container_width=True, key="btn_pago_cont"):
                        current_time = time.time()
                        if current_time - st.session_state.get('last_pago_cont_time', 0) < 3: st.stop()
                        st.session_state['last_pago_cont_time'] = current_time

                        nombres_pagados = ", ".join(filas_pagar['Concepto'].unique()[:2])
                        if len(filas_pagar['Concepto'].unique()) > 2: nombres_pagados += " y otros..."
                        
                        pago_exitoso = False
                        if "Caja Fuerte" in sel_origen:
                            res_caja = fetch_caja_abierta(client)
                            if res_caja.data:
                                client.table("movimientos_caja").insert({"id_caja": res_caja.data[0]['id'], "tipo": "Retirada", "cantidad": float(total_a_pagar), "motivo": f"Pago gastos: {nombres_pagados}"}).execute()
                                pago_exitoso = True
                            else:
                                st.error("⚠️ No puedes pagar con la caja porque no hay ningún turno abierto.")
                        elif "No registrar origen" in sel_origen:
                            pago_exitoso = True
                        else:
                            banco_id = mapa_bancos[sel_origen]
                            banco_data = [b for b in res_b.data if b['id'] == banco_id][0]
                            client.table("cuentas_bancarias").update({"saldo_actual": banco_data['saldo_actual'] - total_a_pagar}).eq("id", banco_id).execute()
                            pago_exitoso = True
                            
                        if pago_exitoso:
                            for _, row in filas_pagar.iterrows():
                                c_id = row['id']
                                pago_hoy = float(row['A Pagar Hoy (€)'])
                                actual_row = df_deudas[df_deudas['id'] == c_id].iloc[0]
                                nuevo_pagado = float(actual_row['pagado']) + pago_hoy
                                nuevo_pendiente = float(actual_row['pendiente']) - pago_hoy
                                nuevo_estado = "Pagado" if nuevo_pendiente <= 0.01 else "Pago Parcial"
                                client.table("compras").update({"estado": nuevo_estado, "pagado": nuevo_pagado, "pendiente": nuevo_pendiente}).eq("id", c_id).execute()
                            limpiar_cache_contabilidad()
                            st.session_state.llave_cont_pago += 1
                            st.success(f"¡Pago de {total_a_pagar:.2f} € registrado correctamente!"); time.sleep(1.5); st.rerun()
        else:
            st.success("¡Genial! No tienes gastos puntuales pendientes.")

    with sec_archivo:
        st.markdown("#### 📖 Archivo Contable (Libro Mayor)")
        st.info("💡 Este es el **Libro Mayor**. Muestra el historial inalterable de **todos** los movimientos contables registrados (pagados y pendientes). Usa los filtros para localizar cualquier documento.")
        
        c_f0_arc, c_f1_arc, c_f2_arc = st.columns(3)
        with c_f0_arc:
            preset_arc = st.selectbox("📅 Filtro rápido:", ["Esta semana", "Este mes", "1º Trimestre", "2º Trimestre", "3º Trimestre", "4º Trimestre", "Trimestre Actual", "Todo el año", "Personalizado"], index=1, key="preset_arc")
        
        hoy = pd.Timestamp.now('Atlantic/Canary').date()
        if preset_arc == "Esta semana":
            f_ini_arc_val = hoy - timedelta(days=hoy.weekday())
            f_fin_arc_val = hoy
        elif preset_arc == "Este mes":
            f_ini_arc_val = hoy.replace(day=1)
            f_fin_arc_val = hoy
        elif preset_arc == "1º Trimestre":
            f_ini_arc_val = date(hoy.year, 1, 1)
            f_fin_arc_val = date(hoy.year, 3, 31)
        elif preset_arc == "2º Trimestre":
            f_ini_arc_val = date(hoy.year, 4, 1)
            f_fin_arc_val = date(hoy.year, 6, 30)
        elif preset_arc == "3º Trimestre":
            f_ini_arc_val = date(hoy.year, 7, 1)
            f_fin_arc_val = date(hoy.year, 9, 30)
        elif preset_arc == "4º Trimestre":
            f_ini_arc_val = date(hoy.year, 10, 1)
            f_fin_arc_val = date(hoy.year, 12, 31)
        elif preset_arc == "Trimestre Actual":
            f_ini_arc_val = hoy.replace(month=((hoy.month-1)//3)*3+1, day=1)
            f_fin_arc_val = hoy
        elif preset_arc == "Todo el año":
            f_ini_arc_val = hoy.replace(month=1, day=1)
            f_fin_arc_val = hoy
        else: # Personalizado
            f_ini_arc_val = st.session_state.get("arc_i", hoy - timedelta(days=30))
            f_fin_arc_val = st.session_state.get("arc_f", hoy)

        if preset_arc != "Personalizado":
            st.session_state["arc_i"] = f_ini_arc_val
            st.session_state["arc_f"] = f_fin_arc_val

        with c_f1_arc:
            f_ini_arc = st.date_input("Desde:", value=f_ini_arc_val, disabled=(preset_arc != "Personalizado"), key="arc_i")
        with c_f2_arc:
            f_fin_arc = st.date_input("Hasta:", value=f_fin_arc_val, disabled=(preset_arc != "Personalizado"), key="arc_f")

        res_comp_arc = fetch_compras_archivo(client, str(f_ini_arc), str(f_fin_arc))
        if res_comp_arc.data:
            df_comp_arc = pd.DataFrame(res_comp_arc.data)
            df_comp_arc['Proveedor'] = df_comp_arc['proveedores'].apply(lambda x: x['nombre_empresa'] if x else '---')
            dt_comp_arc = pd.to_datetime(df_comp_arc['created_at'])
            if dt_comp_arc.dt.tz is None:
                dt_comp_arc = dt_comp_arc.dt.tz_localize('UTC')
            df_comp_arc['Fecha'] = dt_comp_arc.dt.tz_convert('Atlantic/Canary').dt.strftime('%d/%m/%Y %H:%M')
            df_comp_arc['Fecha Factura'] = pd.to_datetime(df_comp_arc['fecha_factura']).dt.strftime('%d/%m/%Y').fillna('---')
            
            st.markdown("##### 🗂️ Clasificación de Documentos")
            filtro_cat_arc = st.selectbox(
                "Filtro:",
                [
                    "Todos los registros", 
                    "📦 Facturas de Proveedores (Mercancía)", 
                        "🔄 Abonos de Proveedores",
                    "🧹 Gastos de Tienda (Limpieza, consumibles...)", 
                    "🏢 Gastos Fijos (Alquiler, Luz...)", 
                    "👥 Personal y Nóminas", 
                    "🛠️ Servicios Exteriores (Técnicos...)", 
                    "🏛️ Impuestos y Tasas"
                ],
                label_visibility="collapsed",
                key="filtro_arc"
            )
            
            df_filtrado_arc = df_comp_arc.copy()
            if "Facturas de Proveedores" in filtro_cat_arc: df_filtrado_arc = df_filtrado_arc[df_filtrado_arc['tipo'].str.contains('Factura', case=False, na=False)]
            elif "Gastos de Tienda" in filtro_cat_arc: df_filtrado_arc = df_filtrado_arc[df_filtrado_arc['tipo'].str.contains('Gastos de compra', case=False, na=False)]
            elif "Gastos Fijos" in filtro_cat_arc: df_filtrado_arc = df_filtrado_arc[df_filtrado_arc['tipo'].str.contains('Gastos fijos', case=False, na=False)]
            elif "Personal y Nóminas" in filtro_cat_arc: df_filtrado_arc = df_filtrado_arc[df_filtrado_arc['tipo'].str.contains('Personal', case=False, na=False)]
            elif "Servicios Exteriores" in filtro_cat_arc: df_filtrado_arc = df_filtrado_arc[df_filtrado_arc['tipo'].str.contains('exterior', case=False, na=False)]
            elif "Impuestos y Tasas" in filtro_cat_arc: df_filtrado_arc = df_filtrado_arc[df_filtrado_arc['tipo'].str.contains('Impuestos', case=False, na=False)]
            
            if df_filtrado_arc.empty:
                st.info("No hay registros en esta categoría para las fechas seleccionadas.")
            else:
                df_vista_arc = df_filtrado_arc[['id', 'Fecha', 'Fecha Factura', 'tipo', 'total', 'Proveedor', 'estado']].copy()
                df_vista_arc.insert(0, "Borrar", False)
                
                ed_comp_arc = st.data_editor(
                    df_vista_arc, hide_index=True, use_container_width=True, key="ed_h_c_arc", 
                    column_config={
                        "Borrar": st.column_config.CheckboxColumn("🗑️ Borrar"),
                        "id": None, "tipo": "Documento / Concepto",
                        "Fecha": "Fecha Reg.",
                        "Fecha Factura": "F. Factura/Emisión"
                    }
                )

                filas_borrar_c_arc = ed_comp_arc[ed_comp_arc["Borrar"] == True]
                if not filas_borrar_c_arc.empty:
                    st.error(f"⚠️ Has marcado {len(filas_borrar_c_arc)} documento(s) para eliminar. Si era una factura de compra, el stock se restará del inventario.")
                    if st.button("🚨 CONFIRMAR ELIMINACIÓN DE DOCUMENTO(S)", type="primary", use_container_width=True, key="btn_del_arc"):
                        for idx, row in filas_borrar_c_arc.iterrows():
                            c_id = row['id']
                            c_data = df_comp_arc[df_comp_arc['id'] == c_id].iloc[0]
                            prods_raw = c_data.get('productos', [])
                            if isinstance(prods_raw, list):
                                for p in prods_raw:
                                    p_id = p.get('id') if isinstance(p, dict) else None
                                    if p_id and str(p_id).strip() not in ["", "None", "0"]:
                                        try:
                                            res_p = fetch_producto_stock(client, p_id)
                                            if res_p.data: client.table("productos").update({"stock_actual": res_p.data[0]['stock_actual'] - p['Cantidad']}).eq("id", p_id).execute()
                                        except: pass
                            client.table("compras").delete().eq("id", c_id).execute()
                        limpiar_cache_contabilidad()
                        st.success("Documento(s) eliminado(s) correctamente."); time.sleep(1); st.rerun()

                st.markdown("---")

                if st.button(" 💾  Guardar Cambios en Estado/Referencia", key="btn_save_arc"):
                    filas_validas_arc = ed_comp_arc[ed_comp_arc["Borrar"] == False]
                    for _, row in filas_validas_arc.iterrows():
                        client.table("compras").update({"estado": str(row['estado']), "tipo": str(row['tipo'])}).eq("id", row['id']).execute()
                    limpiar_cache_contabilidad()
                    st.success("Documentos actualizados."); time.sleep(0.5); st.rerun()
        else:
            st.info("No hay gastos ni compras registradas en este periodo.")

    with sec_informes:
        st.markdown("#### 📥 Selector de Fechas Personalizado")
        
        c_inf_pres, c_inf1, c_inf2 = st.columns(3)
        with c_inf_pres:
            preset_inf = st.selectbox("📅 Filtro rápido:", ["Esta semana", "Este mes", "1º Trimestre", "2º Trimestre", "3º Trimestre", "4º Trimestre", "Trimestre Actual", "Todo el año", "Personalizado"], index=1, key="preset_inf")
        
        hoy = pd.Timestamp.now('Atlantic/Canary').date()
        if preset_inf == "Esta semana":
            f_ini_val = hoy - timedelta(days=hoy.weekday())
            f_fin_val = hoy
        elif preset_inf == "Este mes":
            f_ini_val = hoy.replace(day=1)
            f_fin_val = hoy
        elif preset_inf == "1º Trimestre":
            f_ini_val = date(hoy.year, 1, 1)
            f_fin_val = date(hoy.year, 3, 31)
        elif preset_inf == "2º Trimestre":
            f_ini_val = date(hoy.year, 4, 1)
            f_fin_val = date(hoy.year, 6, 30)
        elif preset_inf == "3º Trimestre":
            f_ini_val = date(hoy.year, 7, 1)
            f_fin_val = date(hoy.year, 9, 30)
        elif preset_inf == "4º Trimestre":
            f_ini_val = date(hoy.year, 10, 1)
            f_fin_val = date(hoy.year, 12, 31)
        elif preset_inf == "Trimestre Actual":
            f_ini_val = hoy.replace(month=((hoy.month-1)//3)*3+1, day=1)
            f_fin_val = hoy
        elif preset_inf == "Todo el año":
            f_ini_val = hoy.replace(month=1, day=1)
            f_fin_val = hoy
        else: # Personalizado
            f_ini_val = st.session_state.get("f_desde_inf", hoy.replace(day=1))
            f_fin_val = st.session_state.get("f_hasta_inf", hoy)

        if preset_inf != "Personalizado":
            st.session_state["f_desde_inf"] = f_ini_val
            st.session_state["f_hasta_inf"] = f_fin_val

        with c_inf1:
            f_desde_inf = st.date_input("📅 Desde la fecha:", value=f_ini_val, disabled=(preset_inf != "Personalizado"), key="f_desde_inf")
        with c_inf2:
            f_hasta_inf = st.date_input("📅 Hasta la fecha:", value=f_fin_val, disabled=(preset_inf != "Personalizado"), key="f_hasta_inf")
        
        st.markdown(f"<p style='color: gray; font-size: 13px;'>Filtrando datos entre el <b>{f_desde_inf.strftime('%d/%m/%Y')}</b> y el <b>{f_hasta_inf.strftime('%d/%m/%Y')}</b>.</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        fecha_inicio_q = f"{f_desde_inf}T00:00:00"
        fecha_fin_q = f"{f_hasta_inf}T23:59:59"

        # Mapa de categorías de productos para separar la lógica de IGIC
        res_prod = fetch_productos_categorias(client)
        mapa_categorias = {}
        nombres_servicios_db = []
        if res_prod.data:
            for p in res_prod.data:
                mapa_categorias[str(p['id'])] = p.get('categoria', 'Producto')
                if p.get('categoria') == 'Servicio' and p.get('nombre'):
                    n_serv = str(p['nombre']).strip().lower()
                    # Filtramos nombres muy cortos por seguridad
                    if len(n_serv) > 3: nombres_servicios_db.append(n_serv)
                    
        palabras_clave_serv = ['peluquer', 'corte', 'baño', 'lavado', 'arreglo', 'servicio', 'spa'] + nombres_servicios_db

        def safe_float(val, default=0.0):
            if val is None or val == "":
                return default
            try:
                if isinstance(val, str):
                    val = val.replace(',', '.')
                return float(val)
            except:
                return default

        def calcular_bases_e_igic_y_lineas(productos_raw, desc_global, is_factura, doc_id_str, fecha_str, cliente_nom):
            b_prod, b_serv, i_serv = 0.0, 0.0, 0.0
            l_prod, l_serv = [], []
            if not productos_raw: return b_prod, b_serv, i_serv, l_prod, l_serv
            if isinstance(productos_raw, str):
                try:
                    import json; productos_raw = json.loads(productos_raw)
                except: return b_prod, b_serv, i_serv, l_prod, l_serv
            if isinstance(productos_raw, dict): productos_raw = [productos_raw]
                
            factor_desc = (1 - safe_float(desc_global) / 100)
            
            for p in productos_raw:
                if not isinstance(p, dict): continue
                precio_pvp = safe_float(p.get('Precio Venta' if is_factura else 'Precio', p.get('Precio', 0.0)))
                cant = safe_float(p.get('Cantidad', 1))
                desc_item = safe_float(p.get('Desc %', p.get('Desc. %', 0.0)))
                id_item = str(p.get('id', ''))
                cat_db = mapa_categorias.get(id_item, 'Desconocido')
                
                es_servicio = False
                if cat_db == 'Servicio' or id_item.startswith('cita_'): es_servicio = True
                elif cat_db == 'Producto': es_servicio = False
                else:
                    nombre_item = str(p.get('Producto', p.get('Descripción', ''))).lower()
                    if any(kw in nombre_item for kw in palabras_clave_serv):
                        es_servicio = True
                        if any(ex in nombre_item for ex in ['cepillo', 'peine', 'champú', 'champu', 'mascarilla', 'tijera', 'carda', 'cortaúñas', 'cortauñas', 'colonia', 'perfume']):
                            es_servicio = False

                pvp_con_desc = (precio_pvp * cant) * (1 - desc_item / 100)
                pvp_final_linea = pvp_con_desc * factor_desc
                nombre_prod = str(p.get('Producto', p.get('Descripción', '')))

                if es_servicio:
                    igic_porcentaje = safe_float(p.get('IGIC %', p.get('IGIC', 7.0)))
                    base_linea = pvp_con_desc / (1 + igic_porcentaje / 100)
                    
                    base_final_linea = base_linea * factor_desc
                    igic_final_linea = pvp_final_linea - base_final_linea
                    
                    b_serv += base_linea
                    i_serv += (pvp_con_desc - base_linea)
                    
                    l_serv.append({
                        "Fecha": fecha_str, "Documento": doc_id_str, "Cliente": cliente_nom,
                        "Servicio": nombre_prod, "Cantidad": cant, "Precio Unit. Final (€)": round(pvp_final_linea/cant if cant>0 else 0, 2),
                        "Base Imponible (€)": round(base_final_linea, 2), "IGIC %": igic_porcentaje,
                        "Cuota IGIC (€)": round(igic_final_linea, 2), "Total (€)": round(pvp_final_linea, 2)
                    })
                else:
                    b_prod += pvp_con_desc
                    l_prod.append({
                        "Fecha": fecha_str, "Documento": doc_id_str, "Cliente": cliente_nom,
                        "Producto": nombre_prod, "Cantidad": cant, "Precio Unit. Final (€)": round(pvp_final_linea/cant if cant>0 else 0, 2),
                        "Total (0% IGIC) (€)": round(pvp_final_linea, 2)
                    })
                    
            return round(b_prod * factor_desc, 2), round(b_serv * factor_desc, 2), round(i_serv * factor_desc, 2), l_prod, l_serv

        # Recuperar datos de Tickets
        res_v_inf = fetch_ventas_informe(client, fecha_inicio_q, fecha_fin_q)
        # Recuperar datos de Facturas Emitidas
        res_f_inf = fetch_facturas_informe(client, fecha_inicio_q, fecha_fin_q)
        # Recuperar datos de Compras/Gastos
        res_c_inf = fetch_compras_informe(client, fecha_inicio_q, fecha_fin_q)

        # Construir el SUPER INFORME UNIFICADO DE VENTAS
        ventas_unificadas = []
        devoluciones_unificadas = []
        todas_lineas_prod = []
        todas_lineas_serv = []
        
        if res_v_inf.data:
            for t in res_v_inf.data:
                estado_doc = t.get('estado', 'Completado')
                desc_global = float(t.get('descuento_global', 0.0))
                
                dt_t = pd.to_datetime(t['created_at'])
                if dt_t.tzinfo is None: dt_t = dt_t.tz_localize('UTC')
                fecha_str = dt_t.tz_convert('Atlantic/Canary').strftime('%d/%m/%Y')
                doc_id_str = f"T-{t['id']}"
                cliente_nom = t.get('cliente_deuda') if t.get('cliente_deuda') else "Mostrador"
                
                base_prod, base_serv, igic_serv, l_p, l_s = calcular_bases_e_igic_y_lineas(
                    t.get('productos'), desc_global, False, doc_id_str, fecha_str, cliente_nom
                )
                
                # Parche de Seguridad Contable: Ajuste proporcional si hubo canjeo de puntos (descuento en euros)
                total_calc = base_prod + base_serv + igic_serv
                tot_real = float(t['total'])
                if total_calc > 0 and abs(total_calc - tot_real) > 0.01:
                    ratio = tot_real / total_calc
                    base_prod = round(base_prod * ratio, 2)
                    base_serv = round(base_serv * ratio, 2)
                    igic_serv = round(igic_serv * ratio, 2)
                    for lp in l_p: lp["Total (0% IGIC) (€)"] = round(lp["Total (0% IGIC) (€)"] * ratio, 2)
                    for ls in l_s:
                        ls["Base Imponible (€)"] = round(ls["Base Imponible (€)"] * ratio, 2)
                        ls["Cuota IGIC (€)"] = round(ls["Cuota IGIC (€)"] * ratio, 2)
                        ls["Total (€)"] = round(ls["Total (€)"] * ratio, 2)
                
                ticket_dict = {
                    "Fecha": fecha_str,
                    "Tipo Documento": "Ticket de Venta (TPV)",
                    "Nº Documento": doc_id_str,
                    "Cliente": cliente_nom,
                    "CIF Cliente": "",
                    "Ventas Productos (0% IGIC) (€)": base_prod,
                    "Base Servicios (€)": base_serv,
                    "Cuota IGIC Servicios (€)": igic_serv,
                    "Importe Total (€)": float(t['total']),
                    "Método de Pago": t['metodo_pago']
                }
                
                if estado_doc == 'DEVUELTO':
                    ticket_dict["Estado"] = "DEVUELTO (Anulado)"
                    devoluciones_unificadas.append(ticket_dict)
                else:
                    ticket_dict["Estado"] = estado_doc
                    ventas_unificadas.append(ticket_dict)
                    todas_lineas_prod.extend(l_p)
                    todas_lineas_serv.extend(l_s)
                
        if res_f_inf.data:
            for f in res_f_inf.data:
                cliente_nom = f['clientes']['nombre_dueno'] if f.get('clientes') else "N/A"
                cliente_cif = f['clientes'].get('cif', '') if f.get('clientes') else ""
                tot_f = float(f.get('total_final', 0))
                
                dt_f = pd.to_datetime(f['created_at'])
                if dt_f.tzinfo is None: dt_f = dt_f.tz_localize('UTC')
                fecha_str = dt_f.tz_convert('Atlantic/Canary').strftime('%d/%m/%Y')
                doc_id_str = f"F-{f['numero_factura']}"
                
                if f.get('productos'):
                    base_prod, base_serv, igic_serv, l_p, l_s = calcular_bases_e_igic_y_lineas(
                        f.get('productos'), desc_global, True, doc_id_str, fecha_str, cliente_nom
                    )
                else:
                    # Si no hay productos (facturas antiguas sin JSON), asumimos fallback a total neto (en Servicios)
                    base_serv = float(f.get('total_neto', round(tot_f / 1.07, 2)))
                    igic_serv = float(f.get('total_igic', round(tot_f - base_serv, 2)))
                    base_prod = 0.0
                    l_p, l_s = [], []
                    l_s.append({
                        "Fecha": fecha_str, "Documento": doc_id_str, "Cliente": cliente_nom,
                        "Servicio": "Servicios Varios (Sin desglose)", "Cantidad": 1, "Precio Unit. Final (€)": tot_f,
                        "Base Imponible (€)": base_serv, "IGIC %": 7.0,
                        "Cuota IGIC (€)": igic_serv, "Total (€)": tot_f
                    })

                ventas_unificadas.append({
                    "Fecha": fecha_str,
                    "Tipo Documento": "Factura Emitida",
                    "Nº Documento": doc_id_str,
                    "Cliente": cliente_nom,
                    "CIF Cliente": cliente_cif,
                    "Ventas Productos (0% IGIC) (€)": base_prod,
                    "Base Servicios (€)": base_serv,
                    "Cuota IGIC Servicios (€)": igic_serv,
                    "Importe Total (€)": tot_f,
                    "Método de Pago": f['forma_pago'],
                    "Estado": "Completado"
                })
                todas_lineas_prod.extend(l_p)
                todas_lineas_serv.extend(l_s)

        df_ventas_unificadas = pd.DataFrame(ventas_unificadas)
        if not df_ventas_unificadas.empty:
            df_ventas_unificadas['Fecha_dt'] = pd.to_datetime(df_ventas_unificadas['Fecha'], format='%d/%m/%Y')
            df_ventas_unificadas = df_ventas_unificadas.sort_values(by="Fecha_dt").drop(columns=['Fecha_dt'])
            
        df_devoluciones = pd.DataFrame(devoluciones_unificadas)
        if not df_devoluciones.empty:
            df_devoluciones['Fecha_dt'] = pd.to_datetime(df_devoluciones['Fecha'], format='%d/%m/%Y')
            df_devoluciones = df_devoluciones.sort_values(by="Fecha_dt").drop(columns=['Fecha_dt'])
            
        df_lineas_prod = pd.DataFrame(todas_lineas_prod)
        df_lineas_serv = pd.DataFrame(todas_lineas_serv)

        # --- PROCESAR COMPRAS Y GASTOS (Separando Facturas de Tickets) ---
        res_gf_cat = fetch_gastos_recurrentes_cat(client)
        mapa_gf_cat = {g['concepto']: g['categoria'] for g in res_gf_cat.data} if res_gf_cat.data else {}
        
        compras_list = []
        if res_c_inf.data:
            for c in res_c_inf.data:
                tipo_str = str(c.get('tipo', ''))
                concepto = tipo_str
                cat_contable = "Otros Gastos Fijos"
                
                es_factura = False
                es_abono = False
                
                if "Factura:" in tipo_str:
                    es_factura = True
                    cat_contable = "Factura de Proveedor (Mercancía)"
                elif "Abono:" in tipo_str:
                    es_abono = True
                    cat_contable = "Abono de Proveedor"
                elif "Gastos de compra" in tipo_str:
                    cat_contable = "Gastos de Compra (Limpieza, Consumibles)"
                else:
                    t_low = tipo_str.lower()
                    if "gastos fijos |" in t_low:
                        concepto_puro = tipo_str.split(" | ")[1].rsplit(" - ", 1)[0].strip() # [cite: L543]
                        cat_bd = str(mapa_gf_cat.get(concepto_puro, "") if 'mapa_gf_cat' in locals() else "")
                        if "Tienda" in cat_bd or "Suministros" in cat_bd: cat_contable = "Gastos de Tienda y Suministros (Alquiler, Luz, Agua, Teléfono, Alarma, Software, Garaje...)"
                        elif "Personal" in cat_bd or "Autónomo" in cat_bd or "Profesionales" in cat_bd: cat_contable = "Personal y Profesionales (Nóminas, SS, Autónomo, Asesoría/Gestoría...)"
                        elif "Financiación" in cat_bd or "Seguros" in cat_bd: cat_contable = "Financiación y Seguros (Préstamos, Tarjetas, Pólizas, Comisiones...)"
                        elif "Publicidad" in cat_bd or "Marketing" in cat_bd: cat_contable = "Publicidad y Marketing (Redes sociales, Promociones, Web...)"
                        elif "Impuestos" in cat_bd or "Tasas" in cat_bd: cat_contable = "Impuestos y Tasas (IGIC, IRPF, Tributos...)"
                        elif "Servicios exteriores" in cat_bd: cat_contable = "Servicios Exteriores y Reparaciones"
                        else:
                            c_low = concepto_puro.lower()
                            if "préstamo" in c_low or "prestamo" in c_low or "cuota" in c_low or "seguro" in c_low or "datáfono" in c_low or "datafono" in c_low: cat_contable = "Financiación y Seguros (Préstamos, Tarjetas, Pólizas, Comisiones...)"
                            elif "nómina" in c_low or "nomina" in c_low or "seguridad" in c_low or "asesor" in c_low: cat_contable = "Personal y Profesionales (Nóminas, SS, Autónomo, Asesoría/Gestoría...)"
                            elif "igic" in c_low or "irpf" in c_low or "tributo" in c_low or "impuesto" in c_low: cat_contable = "Impuestos y Tasas (IGIC, IRPF, Tributos...)"
                            elif "publicidad" in c_low or "marketing" in c_low: cat_contable = "Publicidad y Marketing (Redes sociales, Promociones, Web...)"
                            else: cat_contable = "Gastos de Tienda y Suministros (Alquiler, Luz, Agua, Teléfono, Alarma, Software, Garaje...)"
                    elif "personal" in t_low: cat_contable = "Personal y Profesionales (Nóminas, SS, Autónomo, Asesoría/Gestoría...)"
                    elif "impuestos" in t_low: cat_contable = "Impuestos y Tasas (IGIC, IRPF, Tributos...)"
                    elif "servicios exteriores" in t_low: cat_contable = "Servicios Exteriores y Reparaciones"
                    else:
                        if "nómina" in t_low or "nomina" in t_low or "seguridad social" in t_low or "asesor" in t_low: cat_contable = "Personal y Profesionales (Nóminas, SS, Autónomo, Asesoría/Gestoría...)"
                        elif "datáfono" in t_low or "datafono" in t_low or "préstamo" in t_low or "prestamo" in t_low or "cuota" in t_low or "seguro" in t_low or "comisión" in t_low: cat_contable = "Financiación y Seguros (Préstamos, Tarjetas, Pólizas, Comisiones...)"
                        elif "publicidad" in t_low or "marketing" in t_low: cat_contable = "Publicidad y Marketing (Redes sociales, Promociones, Web...)"
                        elif "alquiler" in t_low or "luz" in t_low or "agua" in t_low or "garaje" in t_low: cat_contable = "Gastos de Tienda y Suministros (Alquiler, Luz, Agua, Teléfono, Alarma, Software, Garaje...)"
                
                if " | " in tipo_str:
                    concepto = tipo_str.split(" | ")[1]

                base_c = float(c['total'])
                igic_c = 0.0
                
                if c.get('productos') and (es_factura or es_abono):
                    try:
                        df_p = pd.DataFrame(c['productos'])
                        if not df_p.empty and 'Base Ud' in df_p.columns and 'Cantidad' in df_p.columns:
                            if 'Desc %' not in df_p.columns: df_p['Desc %'] = 0.0
                            if 'IGIC %' not in df_p.columns: df_p['IGIC %'] = 0.0
                            
                            base_neta_calc = (pd.to_numeric(df_p['Base Ud']) * pd.to_numeric(df_p['Cantidad'])) * (1 - pd.to_numeric(df_p['Desc %'])/100)
                            igic_eur_calc = base_neta_calc * (pd.to_numeric(df_p['IGIC %'])/100)
                            
                            base_b = base_neta_calc.sum()
                            igic_b = igic_eur_calc.sum()
                            ratio = abs(float(c['total'])) / (base_b + igic_b) if (base_b + igic_b) > 0 else 1
                            base_c = round(base_b * ratio, 2)
                            igic_c = round(igic_b * ratio, 2)
                            if es_abono:
                                base_c = -abs(base_c)
                                igic_c = -abs(igic_c)
                    except: pass
                
                prov_nombre = c['proveedores']['nombre_empresa'] if isinstance(c.get('proveedores'), dict) else "Acreedor / Gasto General"
                prov_cif = c['proveedores'].get('cif', '') if isinstance(c.get('proveedores'), dict) else ""
                
                dt_c = pd.to_datetime(c['created_at'])
                if dt_c.tzinfo is None: dt_c = dt_c.tz_localize('UTC')
                
                compras_list.append({
                    "Nº Interno": c['id'], "Fecha": dt_c.tz_convert('Atlantic/Canary').strftime('%d/%m/%Y'),
                    "Categoría Contable": cat_contable, "Concepto / Referencia": concepto, "Proveedor / Beneficiario": prov_nombre,
                    "CIF Proveedor": prov_cif,
                    "Base Imponible (€)": base_c, "Cuota IGIC (€)": igic_c, "Importe Total (€)": float(c['total']),
                    "Estado": c['estado'], "Es_Factura": es_factura, "Es_Abono": es_abono
                })

        df_todas_compras = pd.DataFrame(compras_list)
        df_facturas_rec = pd.DataFrame()
        df_abonos_rec = pd.DataFrame()
        df_tickets_gastos = pd.DataFrame()
        df_fijos_pagados = pd.DataFrame()
        if not df_todas_compras.empty:
            df_facturas_rec = df_todas_compras[df_todas_compras['Es_Factura'] == True].drop(columns=['Es_Factura', 'Es_Abono'])
            df_abonos_rec = df_todas_compras[df_todas_compras['Es_Abono'] == True].drop(columns=['Es_Factura', 'Es_Abono'])
            
            mask_tickets = df_todas_compras['Categoría Contable'] == "Gastos de Compra (Limpieza, Consumibles)"
            df_tickets_gastos = df_todas_compras[(df_todas_compras['Es_Factura'] == False) & (df_todas_compras['Es_Abono'] == False) & mask_tickets].drop(columns=['Es_Factura', 'Es_Abono'])
            
            categorias_fijos = [
                "Gastos de Tienda y Suministros (Alquiler, Luz, Agua, Teléfono, Alarma, Software, Garaje...)",
                "Personal y Profesionales (Nóminas, SS, Autónomo, Asesoría/Gestoría...)",
                "Financiación y Seguros (Préstamos, Tarjetas, Pólizas, Comisiones...)",
                "Publicidad y Marketing (Redes sociales, Promociones, Web...)",
                "Impuestos y Tasas (IGIC, IRPF, Tributos...)",
                "Servicios Exteriores y Reparaciones",
                "Otros Gastos Fijos"
            ]
            mask_fijos_pagados = df_todas_compras['Categoría Contable'].isin(categorias_fijos)
            df_fijos_pagados = df_todas_compras[(df_todas_compras['Es_Factura'] == False) & (df_todas_compras['Es_Abono'] == False) & mask_fijos_pagados & (df_todas_compras['Estado'] == 'Pagado')].drop(columns=['Es_Factura', 'Es_Abono'])

        # --- EXTRACCIÓN DE GASTOS FIJOS ---
        res_gf_inf = fetch_gastos_recurrentes_inf(client)
        df_gf_inf = pd.DataFrame(res_gf_inf.data) if res_gf_inf.data else pd.DataFrame(columns=["concepto", "categoria", "importe_estimado", "dia_cargo", "frecuencia"])
        if not df_gf_inf.empty:
            df_gf_inf = df_gf_inf.rename(columns={"concepto": "Concepto", "categoria": "Categoría Contable", "importe_estimado": "Importe Mensual (€)", "dia_cargo": "Día del Mes", "frecuencia": "Frecuencia"})

        # --- FUNCIÓN MÁGICA PARA CREAR EXCEL (CON MÚLTIPLES PESTAÑAS) ---
        def generar_excel_formateado(df_o_dict, nombre_hoja="Datos"):
            if isinstance(df_o_dict, pd.DataFrame): dict_dfs = {nombre_hoja: df_o_dict}
            else: dict_dfs = df_o_dict

            output = io.BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            workbook = writer.book
            
            formato_cabecera = workbook.add_format({
                'bg_color': '#005275', 'font_color': 'white', 'bold': True,
                'border': 1, 'text_wrap': True, 'align': 'center', 'valign': 'vcenter'
            })
            formato_celda = workbook.add_format({'border': 1, 'valign': 'vcenter'})
            formato_moneda = workbook.add_format({'border': 1, 'valign': 'vcenter', 'num_format': '#,##0.00 €'})
            formato_total = workbook.add_format({'bg_color': '#e8f4f8', 'bold': True, 'border': 1, 'valign': 'vcenter'})
            formato_total_moneda = workbook.add_format({'bg_color': '#e8f4f8', 'bold': True, 'border': 1, 'valign': 'vcenter', 'num_format': '#,##0.00 €'})
            
            for sheet_name, df_calc in dict_dfs.items():
                if df_calc.empty:
                    df_calc.to_excel(writer, index=False, sheet_name=sheet_name)
                    continue
                    
                df_c = df_calc.copy()
                fila_totales = {}
                for col in df_c.columns:
                    if '€' in col: fila_totales[col] = df_c[col].sum()
                    else: fila_totales[col] = ''
                fila_totales[df_c.columns[0]] = 'TOTALES'
                df_final = pd.concat([df_c, pd.DataFrame([fila_totales])], ignore_index=True)

                df_final.to_excel(writer, index=False, sheet_name=sheet_name)
                worksheet = writer.sheets[sheet_name]
                
                for col_num, value in enumerate(df_final.columns.values):
                    worksheet.write(0, col_num, value, formato_cabecera)
                    max_len = max([len(str(value))] + [len(str(x)) for x in df_final[value].astype(str)]) + 2
                    worksheet.set_column(col_num, col_num, max_len)
                    
                    is_currency = ('€' in value)
                    for row_num in range(1, len(df_final) + 1):
                        es_ultima_fila = (row_num == len(df_final))
                        celda_val = df_final.iloc[row_num - 1, col_num]
                        fmt = formato_celda
                        if is_currency: fmt = formato_moneda
                        if es_ultima_fila: fmt = formato_total_moneda if is_currency else formato_total
                            
                        if pd.isna(celda_val) or celda_val == '': worksheet.write_string(row_num, col_num, "", fmt)
                        elif isinstance(celda_val, (int, float)): worksheet.write_number(row_num, col_num, celda_val, fmt)
                        else: worksheet.write_string(row_num, col_num, str(celda_val), fmt)
                        
            writer.close()
            return output.getvalue()

        c_down1, c_down2, c_down3, c_down4 = st.columns(4)
        
        with c_down1:
            st.info("💶 VENTAS TOTALES")
            if not df_ventas_unificadas.empty:
                # Crear desglose y resumen por método de pago
                df_resumen = df_ventas_unificadas.copy()
                
                def simplificar_metodo(m):
                    m = str(m)
                    if "Tarjeta" in m: return "Tarjeta"
                    if "Mixto" in m: return "Pago Mixto"
                    return m
                    
                df_resumen['Método Simplificado'] = df_resumen['Método de Pago'].apply(simplificar_metodo)
                resumen_pagos = df_resumen.groupby('Método Simplificado').agg({
                    'Ventas Productos (0% IGIC) (€)': 'sum',
                    'Base Servicios (€)': 'sum',
                    'Cuota IGIC Servicios (€)': 'sum',
                    'Importe Total (€)': 'sum'
                }).reset_index().rename(columns={'Método Simplificado': 'Método de Pago'})
                
                df_solo_facturas_v = df_ventas_unificadas[df_ventas_unificadas['Tipo Documento'] == 'Factura Emitida'].copy()
                
                dict_exportacion = {
                    "Resumen por Método de Pago": resumen_pagos,
                    "Ventas Confirmadas": df_ventas_unificadas
                }
                if not df_solo_facturas_v.empty:
                    dict_exportacion["Facturas Emitidas"] = df_solo_facturas_v
                if not df_devoluciones.empty:
                    dict_exportacion["Devoluciones (Anuladas)"] = df_devoluciones
                if not df_lineas_serv.empty:
                    dict_exportacion["Desglose Servicios"] = df_lineas_serv
                if not df_lineas_prod.empty:
                    dict_exportacion["Desglose Productos"] = df_lineas_prod
                
                excel_unificado = generar_excel_formateado(dict_exportacion)
                st.download_button("📥 Descargar Ventas", excel_unificado, f"Ventas_{f_desde_inf}_al_{f_hasta_inf}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                st.markdown(f"<p style='font-size:12px;'>*Total de Ventas Válidas: {df_ventas_unificadas['Importe Total (€)'].sum():.2f}€*</p>", unsafe_allow_html=True)
            else: st.write("Sin ventas.")

        with c_down2:
            st.success("📑 FACTURAS Y ABONOS")
            
            if not df_facturas_rec.empty or not df_abonos_rec.empty:
                dict_facturas = {}
                if not df_facturas_rec.empty: dict_facturas["Facturas de Compra"] = df_facturas_rec
                if not df_abonos_rec.empty: dict_facturas["Abonos"] = df_abonos_rec
                excel_f = generar_excel_formateado(dict_facturas)
                st.download_button("📥 Descargar Documentos", excel_f, f"Facturas_Abonos_{f_desde_inf}_al_{f_hasta_inf}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else: st.write("Sin facturas ni abonos.")

        with c_down3:
            st.warning("🎫 TICKETS / GASTOS")
            if not df_tickets_gastos.empty:
                excel_c = generar_excel_formateado(df_tickets_gastos, "Tickets y Gastos")
                st.download_button("📥 Descargar Tickets", excel_c, f"Tickets_Gastos_{f_desde_inf}_al_{f_hasta_inf}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else: st.write("Sin tickets o gastos.")

        with c_down4:
            st.error("🏢 GASTOS FIJOS")
            if not df_fijos_pagados.empty:
                dict_gf = {}
                for cat, group in df_fijos_pagados.groupby("Categoría Contable"):
                    short_cat = cat.split(" (")[0][:31] # Límite de caracteres para pestañas Excel
                    dict_gf[short_cat] = group
                    
                excel_gf = generar_excel_formateado(dict_gf)
                st.download_button("📥 Descargar G. Fijos", excel_gf, f"Gastos_Fijos_Pagados_{f_desde_inf}_al_{f_hasta_inf}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else: st.write("Sin pagos registrados.")
