import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta


@st.cache_data(show_spinner=False, ttl=300)
def fetch_personal_empleados_nombres(_client):
    return _client.table("personal_empleados").select("nombre").execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_ventas_historial_prev(_client, fecha_ini_prev, fecha_fin_prev):
    return _client.table("ventas_historial").select("total, estado").gte("created_at", fecha_ini_prev).lt("created_at", fecha_fin_prev).execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_ventas_historial(_client, fecha_ini, fecha_fin):
    return _client.table("ventas_historial").select("created_at, total, estado, productos, metodo_pago").gte("created_at", fecha_ini).lt("created_at", fecha_fin).execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_compras(_client, fecha_ini, fecha_fin):
    return _client.table("compras").select("created_at, total, tipo").gte("created_at", fecha_ini).lt("created_at", fecha_fin).execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_gastos_recurrentes(_client):
    return _client.table("gastos_recurrentes").select("importe_estimado, frecuencia").eq("activo", True).execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_personal_empleados_activos(_client):
    return _client.table("personal_empleados").select("nombre").eq("activo", True).execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_citas_roi(_client, fecha_ini, fecha_fin):
    return _client.table("citas").select("fecha_hora, servicio, mascotas(id, historial_trabajos)").gte("fecha_hora", fecha_ini).lt("fecha_hora", fecha_fin).execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_citas_est(_client):
    return _client.table("citas").select("fecha_hora, servicio, duracion_minutos").execute()

def limpiar_cache_estadisticas():
    fetch_personal_empleados_nombres.clear()
    fetch_ventas_historial_prev.clear()
    fetch_ventas_historial.clear()
    fetch_compras.clear()
    fetch_gastos_recurrentes.clear()
    fetch_personal_empleados_activos.clear()
    fetch_citas_roi.clear()
    fetch_citas_est.clear()

def render_pestana_estadisticas(client):
    st.markdown("<h3 style='margin-bottom: 5px;'>📈 Estadísticas y Salud Financiera</h3>", unsafe_allow_html=True)
    st.write("Análisis realista del balance: Ingresos por ventas vs Facturas, Proveedores y Gastos Fijos.")
    
    # Cargar lista de empleados reales para evitar errores de lectura
    try:
        res_emp_est = fetch_personal_empleados_nombres(client)
        empleados_reales = [e['nombre'] for e in res_emp_est.data] if res_emp_est.data else []
    except:
        empleados_reales = []
    try:
        hoy = date.today()
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        tipo_periodo = st.selectbox("🗓️ Selecciona el periodo de análisis:", ["Hoy", "Ayer", "Semanal", "Mensual", "Trimestral", "Semestral", "Anual", "Personalizado"], index=3)
        
        c_f1, c_f2 = st.columns(2)
        
        if tipo_periodo == "Hoy":
            fecha_ini_dt = hoy
            fecha_fin_dt = hoy + timedelta(days=1)
            fecha_ini_prev_dt = hoy - timedelta(days=1)
            fecha_fin_prev_dt = hoy
            label_prev = "vs Ayer"
            factor_fijos = 1.0 / 30.416
        elif tipo_periodo == "Ayer":
            fecha_ini_dt = hoy - timedelta(days=1)
            fecha_fin_dt = hoy
            fecha_ini_prev_dt = hoy - timedelta(days=2)
            fecha_fin_prev_dt = hoy - timedelta(days=1)
            label_prev = "vs Día Ant."
            factor_fijos = 1.0 / 30.416
        elif tipo_periodo == "Mensual":
            mes_sel = c_f1.selectbox("Mes", range(1, 13), format_func=lambda x: meses[x-1], index=hoy.month-1)
            anio_sel = c_f2.selectbox("Año", range(2024, hoy.year + 2), index=hoy.year - 2024)
            fecha_ini_dt = date(anio_sel, mes_sel, 1)
            if mes_sel == 12: fecha_fin_dt = date(anio_sel+1, 1, 1)
            else: fecha_fin_dt = date(anio_sel, mes_sel+1, 1)
            fecha_ini_prev_dt = date(anio_sel - 1, 12, 1) if mes_sel == 1 else date(anio_sel, mes_sel - 1, 1)
            fecha_fin_prev_dt = fecha_ini_dt
            label_prev = "vs Mes Ant."
            factor_fijos = 1.0
        elif tipo_periodo == "Semanal":
            sem_ref = c_f1.date_input("Semana del:", value=hoy - timedelta(days=hoy.weekday()))
            if isinstance(sem_ref, tuple):
                sem_ref = sem_ref[0] if sem_ref else hoy
            if not sem_ref:
                sem_ref = hoy
            fecha_ini_dt = sem_ref - timedelta(days=sem_ref.weekday())
            fecha_fin_dt = fecha_ini_dt + timedelta(days=7)
            fecha_ini_prev_dt = fecha_ini_dt - timedelta(days=7)
            fecha_fin_prev_dt = fecha_ini_dt
            label_prev = "vs Sem Ant."
            factor_fijos = 7.0 / 30.416
        elif tipo_periodo == "Trimestral":
            trim_sel = c_f1.selectbox("Trimestre", [1, 2, 3, 4], format_func=lambda x: f"T{x}")
            anio_sel = c_f2.selectbox("Año", range(2024, hoy.year + 2), index=hoy.year - 2024)
            mes_ini = (trim_sel - 1) * 3 + 1
            fecha_ini_dt = date(anio_sel, mes_ini, 1)
            mes_fin = mes_ini + 3
            if mes_fin > 12: fecha_fin_dt = date(anio_sel+1, 1, 1)
            else: fecha_fin_dt = date(anio_sel, mes_fin, 1)
            trim_prev = 4 if trim_sel == 1 else trim_sel - 1
            anio_prev = anio_sel - 1 if trim_sel == 1 else anio_sel
            mes_ini_prev = (trim_prev - 1) * 3 + 1
            fecha_ini_prev_dt = date(anio_prev, mes_ini_prev, 1)
            fecha_fin_prev_dt = fecha_ini_dt
            label_prev = "vs Trim Ant."
            factor_fijos = 3.0
        elif tipo_periodo == "Semestral":
            semestre = c_f1.selectbox("Semestre", [1, 2], format_func=lambda x: "S1 (Ene-Jun)" if x == 1 else "S2 (Jul-Dic)")
            anio_sel = c_f2.selectbox("Año", range(2024, hoy.year + 2), index=hoy.year - 2024)
            if semestre == 1:
                fecha_ini_dt = date(anio_sel, 1, 1)
                fecha_fin_dt = date(anio_sel, 7, 1)
                fecha_ini_prev_dt = date(anio_sel - 1, 7, 1)
            else:
                fecha_ini_dt = date(anio_sel, 7, 1)
                fecha_fin_dt = date(anio_sel+1, 1, 1)
                fecha_ini_prev_dt = date(anio_sel, 1, 1)
            fecha_fin_prev_dt = fecha_ini_dt
            label_prev = "vs Semestre Ant."
            factor_fijos = 6.0
        elif tipo_periodo == "Anual":
            anio_sel = c_f1.selectbox("Año", range(2024, hoy.year + 2), index=hoy.year - 2024)
            fecha_ini_dt = date(anio_sel, 1, 1)
            fecha_fin_dt = date(anio_sel + 1, 1, 1)
            fecha_ini_prev_dt = date(anio_sel - 1, 1, 1)
            fecha_fin_prev_dt = fecha_ini_dt
            label_prev = "vs Año Ant."
            factor_fijos = 12.0
        else: # Personalizado
            rango = c_f1.date_input("Selecciona rango:", [hoy - timedelta(days=30), hoy])
            if isinstance(rango, tuple) and len(rango) == 2:
                fecha_ini_dt, fecha_fin_dt_raw = rango
                fecha_fin_dt = fecha_fin_dt_raw + timedelta(days=1)
                delta = fecha_fin_dt - fecha_ini_dt
                fecha_ini_prev_dt = fecha_ini_dt - delta
                fecha_fin_prev_dt = fecha_ini_dt
                factor_fijos = delta.days / 30.416
            else:
                fecha_ini_dt = hoy
                fecha_fin_dt = hoy + timedelta(days=1)
                fecha_ini_prev_dt = hoy - timedelta(days=1)
                fecha_fin_prev_dt = hoy
                factor_fijos = 1.0 / 30.416
            label_prev = "vs Período Ant."

        fecha_ini = fecha_ini_dt.strftime("%Y-%m-%dT00:00:00")
        fecha_fin = fecha_fin_dt.strftime("%Y-%m-%dT00:00:00")
        fecha_ini_prev = fecha_ini_prev_dt.strftime("%Y-%m-%dT00:00:00")
        fecha_fin_prev = fecha_fin_prev_dt.strftime("%Y-%m-%dT00:00:00")

        # CÁLCULO PERIODO ANTERIOR (Comparativa)
        res_ventas_prev = fetch_ventas_historial_prev(client, fecha_ini_prev, fecha_fin_prev)
        total_ventas_prev = 0.0
        if res_ventas_prev.data:
            df_vp = pd.DataFrame(res_ventas_prev.data)
            total_ventas_prev = df_vp[df_vp['estado'] != 'DEVUELTO']['total'].sum() if not df_vp.empty else 0.0

        # 1. INGRESOS (Ventas del mes)
        res_ventas = fetch_ventas_historial(client, fecha_ini, fecha_fin)
        total_ventas = 0.0
        num_operaciones = 0
        ticket_medio = 0.0
        df_v = pd.DataFrame()
        if res_ventas.data:
            df_v = pd.DataFrame(res_ventas.data)
            df_v = df_v[df_v['estado'] != 'DEVUELTO']
            if not df_v.empty:
                total_ventas = df_v['total'].sum()
                num_operaciones = len(df_v)
                ticket_medio = total_ventas / num_operaciones if num_operaciones > 0 else 0.0
                dt_v = pd.to_datetime(df_v['created_at'])
                if dt_v.dt.tz is None:
                    dt_v = dt_v.dt.tz_localize('UTC')
                df_v['Fecha'] = dt_v.dt.tz_convert('Atlantic/Canary').dt.date
                
        # 2. GASTOS VARIABLES Y PROVEEDORES (Compras y Facturas del mes)
        res_compras = fetch_compras(client, fecha_ini, fecha_fin)
        total_compras = 0.0
        if res_compras.data:
            df_c = pd.DataFrame(res_compras.data)
            total_compras = df_c['total'].sum()
            
        # 3. GASTOS FIJOS (Estimación Proporcional al periodo)
        res_fijos = fetch_gastos_recurrentes(client)
        total_fijos_mes = 0.0
        if res_fijos.data:
            for gf in res_fijos.data:
                imp_raw = gf.get('importe_estimado', 0.0)
                imp = float(imp_raw) if imp_raw is not None else 0.0
                frec = gf.get('frecuencia', 'Mensual')
                if frec == 'Bimestral': imp = imp / 2
                elif frec == 'Trimestral': imp = imp / 3
                elif frec == 'Anual': imp = imp / 12
                total_fijos_mes += imp
                
        total_fijos_periodo = total_fijos_mes * factor_fijos
                
        # CÁLCULOS GLOBALES
        gastos_totales = total_compras + total_fijos_periodo
        balance_neto = total_ventas - gastos_totales

        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        # BUGFIX: Streamlit tiene un bug grave con pestañas anidadas que se actualizan dinámicamente, lo cambiamos a st.radio
        seccion_estad = st.radio("Sección:", ["💰 1. Salud Financiera", "📊 2. Estadísticas Comerciales y Operativas"], horizontal=True, label_visibility="collapsed")
        
        if seccion_estad == "💰 1. Salud Financiera":
            st.markdown(f"#### 💰 Balance Financiero")
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1: 
                crecimiento_mom = ((total_ventas - total_ventas_prev) / total_ventas_prev) * 100 if total_ventas_prev > 0 else 0.0
                delta_str_mom = f"{crecimiento_mom:.1f}% {label_prev}" if total_ventas_prev > 0 else None
                st.metric(label="Ingresos (Ventas TPV)", value=f"{total_ventas:.2f} €", delta=delta_str_mom)
            with col_m2: 
                st.metric(label="Prov. y Variables (Facturas)", value=f"-{total_compras:.2f} €", help="Facturas de proveedores, mercancía y gastos puntuales registrados en este periodo.")
            with col_m3: 
                st.metric(label="Gastos Fijos (Prorrateo)", value=f"-{total_fijos_periodo:.2f} €", help="Cálculo proporcional de alquiler, luz, nóminas, préstamos e impuestos trimestrales para este rango de fechas.")
            with col_m4: 
                delta_str = f"{balance_neto:.2f} €" if balance_neto >= 0 else f"{balance_neto:.2f} €"
                st.metric(label="Beneficio Neto Estimado", value=f"{balance_neto:.2f} €", delta=delta_str)
                
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            
            # NUEVA FILA DE KPIS COMERCIALES
            st.markdown(f"#### 🎯 KPIs de Rendimiento Comercial")
            kpi1, kpi2, kpi3 = st.columns(3)
            with kpi1:
                st.metric(label="N.º de Ventas (Tráfico)", value=f"{num_operaciones} tickets")
            with kpi2:
                st.metric(label="Ticket Medio (Gasto por cliente)", value=f"{ticket_medio:.2f} €", help="Es vital que este número crezca. Intenta ofrecer siempre un 'chuche' o producto cruzado en la caja para aumentarlo.")
            with kpi3:
                gasto_total = total_compras + total_fijos_mes
                margen = ((total_ventas - gasto_total) / total_ventas * 100) if total_ventas > 0 else 0.0
                st.metric(label="Margen de Rentabilidad", value=f"{margen:.1f} %", help="Porcentaje limpio que te queda de cada 100€ que entran en la caja.")
                
            st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
            
            col_g1, col_g2 = st.columns([1.5, 1])
            
            with col_g1:
                st.markdown("**📊 Evolución de Ingresos en el Periodo**")
                
                if not df_v.empty:
                    delta_days = (fecha_fin_dt - fecha_ini_dt).days
                    
                    if delta_days <= 35:
                        ventas_evo = df_v.groupby('Fecha')['total'].sum()
                        ventas_evo.index = pd.to_datetime(ventas_evo.index).strftime('%d/%m')
                    elif delta_days <= 180:
                        df_v['Semana'] = df_v['Fecha'].apply(lambda x: x - timedelta(days=x.weekday()))
                        ventas_evo = df_v.groupby('Semana')['total'].sum()
                        ventas_evo.index = pd.to_datetime(ventas_evo.index).strftime('%d/%m')
                    else:
                        df_v['Mes'] = df_v['Fecha'].apply(lambda x: x.replace(day=1))
                        ventas_evo = df_v.groupby('Mes')['total'].sum()
                        ventas_evo.index = pd.to_datetime(ventas_evo.index).strftime('%m/%Y')
                        
                    st.area_chart(ventas_evo, color="#005275", height=280)
                else:
                    st.info("Aún no hay ventas registradas en este periodo.")
                    
            with col_g2:
                c_tit2, c_sel2 = st.columns([1, 1.2])
                with c_tit2: st.markdown("**💸 Estructura Gastos**")
                with c_sel2: vista_gastos = st.selectbox("Detalle:", ["Fijos vs Variables", "Desglose Variables"], label_visibility="collapsed")
                
                if vista_gastos == "Fijos vs Variables":
                    if total_compras > 0 or total_fijos_periodo > 0:
                        df_gastos_pie = pd.DataFrame({
                            "Categoría": ["Variables/Proveedores", "Fijos (Prorrateo)"],
                            "Importe": [total_compras, total_fijos_periodo]
                        }).set_index("Categoría")
                        st.bar_chart(df_gastos_pie, color="#d32f2f", height=280)
                    else:
                        st.info("No hay gastos registrados.")
                else:
                    if not df_c.empty:
                        df_c['Categoria'] = df_c['tipo'].apply(lambda x: str(x).split(" | ")[0] if " | " in str(x) else "Otros")
                        gastos_cat = df_c.groupby('Categoria')['total'].sum()
                        st.bar_chart(gastos_cat, color="#e57373", height=280)
                    else:
                        st.info("No hay facturas variables en este periodo.")
                    
        elif seccion_estad == "📊 2. Estadísticas Comerciales y Operativas":
            def limpiar_producto(n):

                n = str(n)
                n = re.sub(r'(?i)^producto\s+', '', n)
                # Eliminar notas de peluqueros o estados entre paréntesis/corchetes para unificar el nombre real del producto/servicio
                n = re.sub(r'\s*\([^)]*\)', '', n).strip()
                n = re.sub(r'\s*\[.*?\]', '', n).strip()
                n_low = n.lower()
                if n_low in ['venta', 'venta manual', 'artículo manual', 'desc.', 'varios', 'kiko', 'auna']: return 'Venta Manual (Genérica)'
                return n.capitalize()

            col_g3, col_g4 = st.columns([1.5, 1])
            
            with col_g3:
                st.markdown("**⭐ Top 10 Productos y Servicios**")
                if not df_v.empty and 'productos' in df_v.columns:
                    lista_prods = []
                    
                    for prods in df_v['productos'].dropna():
                        if isinstance(prods, list):
                            for p in prods:
                                if not isinstance(p, dict): continue
                                p_clean = p.copy()
                                p_clean['Artículo'] = limpiar_producto(p.get('Producto', 'Desc.'))
                                lista_prods.append(p_clean)
                    
                    if lista_prods:
                        df_p = pd.DataFrame(lista_prods)
                        if 'Artículo' in df_p.columns and 'Subtotal' in df_p.columns:
                            df_p['Subtotal'] = pd.to_numeric(df_p['Subtotal'], errors='coerce').fillna(0.0)
                            top_prods = df_p.groupby('Artículo')['Subtotal'].sum().sort_values(ascending=False).head(10)
                            
                            df_top = top_prods.reset_index()
                            df_top.columns = ["Servicio / Producto", "Facturación (€)"]
                            max_val = df_top["Facturación (€)"].max() if not df_top.empty else 100
                            st.dataframe(
                                df_top,
                                column_config={
                                    "Facturación (€)": st.column_config.ProgressColumn("Ingresos (€)", format="%.2f €", min_value=0, max_value=max_val)
                                },
                                hide_index=True, use_container_width=True
                            )
                        else:
                            st.info("Formato de productos no compatible.")
                    else:
                        st.info("No hay detalle de productos en los tickets de este periodo.")
                else:
                    st.info("Aún no hay ventas para generar el ranking.")
                    
            with col_g4:
                st.markdown("**💳 Tesorería: Métodos de Pago**")
                if not df_v.empty and 'metodo_pago' in df_v.columns:
                    def simplificar_metodo(m):
                        m = str(m)
                        if "Tarjeta" in m: return "Tarjeta"
                        if "Mixto" in m: return "Pago Mixto"
                        if "Vale" in m: return "Vale de Tienda"
                        return m
                    
                    df_v['Metodo Simplificado'] = df_v['metodo_pago'].apply(simplificar_metodo)
                    dist_pagos = df_v.groupby('Metodo Simplificado')['total'].sum()
                    st.bar_chart(dist_pagos, color="#f9a825", height=350)
                else:
                    st.info("No hay datos de métodos de pago.")

            st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
            
            # === NUEVO CÁLCULO DE ROI LABORAL CRUZANDO AGENDA CON HISTORIAL CLÍNICO ===
            st.markdown("#### 👩‍💼 Rendimiento y ROI Laboral (Agenda + Historial Clínico)")
            st.markdown("<p style='font-size: 13px; color: gray;'>Ingresos reales por empleado basados en las citas agendadas y el importe final cobrado en la ficha.</p>", unsafe_allow_html=True)
            
            fecha_ini_dt = pd.to_datetime(fecha_ini).date()
            fecha_fin_dt = pd.to_datetime(fecha_fin).date()

            res_emp = fetch_personal_empleados_activos(client)
            empleados_lista = [str(e['nombre']).strip() for e in res_emp.data] if res_emp.data else []
            rendimiento_empleados = {emp: {"Ingresos": 0.0, "Citas": 0} for emp in empleados_lista}

            # Extraemos las citas del mes (que no estén canceladas)
            res_citas_roi = fetch_citas_roi(client, fecha_ini, fecha_fin)

            if res_citas_roi.data:

                for c in res_citas_roi.data:
                    servicio_raw = c.get('servicio', '')
                    if "[ESTADO: Cancelada]" in servicio_raw or "[ESTADO: Anulada]" in servicio_raw or "[ESTADO: No presentado]" in servicio_raw or "[ESTADO: Cambio" in servicio_raw: continue
                    
                    # Averiguar a qué empleado pertenece la cita según la agenda
                    emp_cita = None
                    for e in empleados_lista:
                        if f"({e})" in servicio_raw:
                            emp_cita = e; break
                    
                    if not emp_cita: continue # Si no tiene empleado asignado, la saltamos

                    rendimiento_empleados[emp_cita]["Citas"] += 1

                    try:
                        dt_c_raw = pd.to_datetime(c['fecha_hora'])
                        dt_c = dt_c_raw.date()
                        
                        masc = c.get('mascotas')
                        if not isinstance(masc, dict): continue
                        
                        hist = masc.get('historial_trabajos')
                        if isinstance(hist, list):
                            # Buscamos en el historial una entrada con esa misma fecha
                            for t in hist:
                                try:
                                    f_str = str(t.get('Fecha', ''))
                                    if f_str:
                                        dt_t = pd.to_datetime(f_str, format="%d/%m/%Y").date()
                                        if dt_t == dt_c:
                                            # ¡Match! Extraemos el dinero de esta sesión y se lo sumamos al empleado de la cita
                                            imp_base = float(t.get('Precio con desc. (€)') or t.get('Precio Base (€)') or t.get('Importe (€)') or 0.0)
                                            imp_extras = 0.0
                                            if isinstance(t.get('Extras'), list):
                                                imp_extras = sum(float(ext.get('Precio', 0.0)) for ext in t['Extras'] if isinstance(ext, dict))
                                            
                                            imp_total = imp_base + imp_extras
                                            if imp_total > 0:
                                                rendimiento_empleados[emp_cita]["Ingresos"] += imp_total
                                            break # Ya encontramos el importe de este día, paramos de buscar en el historial
                                except: pass
                    except: pass
            
            if rendimiento_empleados:
                lista_roi = [{"Empleado": emp, "Ingresos Generados (€)": data["Ingresos"], "Citas Realizadas": data["Citas"]} for emp, data in rendimiento_empleados.items() if data["Citas"] > 0 or data["Ingresos"] > 0]
                
                if lista_roi:
                    df_roi = pd.DataFrame(lista_roi).sort_values(by='Ingresos Generados (€)', ascending=False)
                    c_roi1, c_roi2 = st.columns([1, 1.5])
                    with c_roi1: 
                        max_roi = df_roi['Ingresos Generados (€)'].max() if not df_roi.empty else 100
                        st.dataframe(
                            df_roi, 
                            column_config={
                                "Ingresos Generados (€)": st.column_config.ProgressColumn("Ingresos (€)", format="%.2f €", min_value=0, max_value=max_roi),
                                "Citas Realizadas": st.column_config.NumberColumn("Citas", format="%d")
                            },
                            hide_index=True, use_container_width=True
                        )
                    with c_roi2: 
                        st.bar_chart(df_roi.set_index('Empleado')['Ingresos Generados (€)'], color="#9c27b0", height=200)
                else:
                    st.info("No hay datos de rendimiento registrados para este periodo.")
            else:
                st.info("No hay importes registrados en los historiales de las mascotas para este periodo.")

            st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
            st.markdown("#### 📊 Análisis y Rendimiento de la Agenda")
            res_citas_est = fetch_citas_est(client)
            
            if res_citas_est.data:
                datos_est = []
                for c in res_citas_est.data:
                    try:
                        dt_obj = pd.to_datetime(c['fecha_hora'])
                        if dt_obj.tzinfo: dt_obj = dt_obj.tz_localize(None)
                        
                        servicio_raw = c.get('servicio', '')
                        estado_c = "Confirmada"

                        m_est = re.search(r'\[ESTADO:\s*(.*?)\]', servicio_raw)
                        if m_est:
                            estado_c = m_est.group(1).strip()
                            servicio_raw = re.sub(r'\[ESTADO:\s*.*?\]\s*', '', servicio_raw)
                        
                        emp_c = "Sin Asignar"
                        for e in empleados_reales:
                            if f"({e})" in servicio_raw:
                                emp_c = e; servicio_raw = servicio_raw.replace(f"({e})", "").replace("  ", " ").strip(); break
                                
                        s_clean = servicio_raw.strip()
                        dur = c.get('duracion_minutos') if c.get('duracion_minutos') is not None else 60
                        
                        datos_est.append({
                            "Fecha": dt_obj.date(),
                            "Estado": estado_c,
                            "Servicio": s_clean,
                            "Peluquero/a": emp_c,
                            "Duración (min)": dur
                        })
                    except: pass
                    
                df_est = pd.DataFrame(datos_est)
                
                if not df_est.empty:
                    st.markdown(f"<p style='font-size: 14px; color: gray;'>Mostrando datos de agenda desde el <b>{fecha_ini_dt.strftime('%d/%m/%Y')}</b> hasta el <b>{fecha_fin_dt.strftime('%d/%m/%Y')}</b> (Periodo global seleccionado arriba).</p>", unsafe_allow_html=True)
                    
                    df_filtrado = df_est[(df_est["Fecha"] >= fecha_ini_dt) & (df_est["Fecha"] <= fecha_fin_dt)]
                    
                    if not df_filtrado.empty:
                        total_citas = len(df_filtrado)
                        canceladas = len(df_filtrado[df_filtrado["Estado"] == "Cancelada"])
                        tasa_cancelacion = (canceladas / total_citas) * 100 if total_citas > 0 else 0
                        horas_totales = df_filtrado[df_filtrado["Estado"] != "Cancelada"]["Duración (min)"].sum() / 60
                            
                        st.markdown("##### 📌 Resumen de Rendimiento")
                        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                        kpi1.metric("Citas Agendadas", total_citas)
                        kpi2.metric("Cancelaciones", canceladas)
                        kpi3.metric("Tasa de Cancelación", f"{tasa_cancelacion:.1f}%")
                        kpi4.metric("Horas de Trabajo (Aprox.)", f"{horas_totales:.1f} h")
                        st.markdown("<hr style='margin: 15px 0px; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)
                        
                        col_graf1, col_graf2 = st.columns(2, gap="large")
                        with col_graf1:
                            st.markdown("**📈 Volumen de Citas por Día**")
                            citas_dia = df_filtrado.groupby("Fecha").size().reset_index(name="Citas").set_index("Fecha")
                            st.line_chart(citas_dia)
                            
                            st.markdown("**💈 Carga por Peluquero/a (Sin canceladas)**")
                            df_validas = df_filtrado[df_filtrado["Estado"] != "Cancelada"]
                            citas_emp = df_validas.groupby("Peluquero/a").size().reset_index(name="Citas").set_index("Peluquero/a")
                            st.bar_chart(citas_emp)
                            
                        with col_graf2:
                            st.markdown("**✂️ Top 5 Servicios Más Demandados**")
                            top_serv = df_validas.groupby("Servicio").size().sort_values(ascending=False).head(5).reset_index(name="Citas").set_index("Servicio")
                            st.bar_chart(top_serv)
                            
                            st.markdown("**🚦 Distribución de Estados**")
                            estados_dist = df_filtrado.groupby("Estado").size().reset_index(name="Cantidad").set_index("Estado")
                            st.bar_chart(estados_dist)
                    else:
                        st.info("No hay datos en el rango de fechas seleccionado.")
                else:
                    st.info("Datos insuficientes para generar gráficas.")
            else:
                st.info("Aún no hay citas registradas en el sistema para analizar.")

    except Exception as e:
        st.error(f"Error al cargar las estadísticas: {e}")
