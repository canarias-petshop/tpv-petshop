import streamlit as st
import pandas as pd
from datetime import date, datetime

def render_pestana_estadisticas(client):
    st.markdown("<h3 style='margin-bottom: 5px;'>📈 Estadísticas y Salud Financiera</h3>", unsafe_allow_html=True)
    st.write("Análisis realista del balance: Ingresos por ventas vs Facturas, Proveedores y Gastos Fijos.")
    
    # Filtros de mes y año
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    hoy = date.today()
    
    c_f1, c_f2, c_f3 = st.columns([1, 1, 2])
    with c_f1:
        mes_sel = st.selectbox("Mes a analizar", range(1, 13), format_func=lambda x: meses[x-1], index=hoy.month-1)
    with c_f2:
        anio_sel = st.selectbox("Año", range(2024, hoy.year + 2), index=hoy.year - 2024)
        
    fecha_ini = f"{anio_sel}-{mes_sel:02d}-01T00:00:00"
    if mes_sel == 12:
        fecha_fin = f"{anio_sel+1}-01-01T00:00:00"
    else:
        fecha_fin = f"{anio_sel}-{mes_sel+1:02d}-01T00:00:00"

    try:
        # 1. INGRESOS (Ventas del mes)
        res_ventas = client.table("ventas_historial").select("created_at, total, estado, productos, metodo_pago").gte("created_at", fecha_ini).lt("created_at", fecha_fin).execute()
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
                df_v['Fecha'] = pd.to_datetime(df_v['created_at']).dt.date
                
        # 2. GASTOS VARIABLES Y PROVEEDORES (Compras y Facturas del mes)
        res_compras = client.table("compras").select("created_at, total, tipo").gte("created_at", fecha_ini).lt("created_at", fecha_fin).execute()
        total_compras = 0.0
        if res_compras.data:
            df_c = pd.DataFrame(res_compras.data)
            total_compras = df_c['total'].sum()
            
        # 3. GASTOS FIJOS (Estimación Mensualizada)
        res_fijos = client.table("gastos_recurrentes").select("importe_estimado, frecuencia").eq("activo", True).execute()
        total_fijos_mes = 0.0
        if res_fijos.data:
            for gf in res_fijos.data:
                imp = float(gf.get('importe_estimado', 0.0))
                frec = gf.get('frecuencia', 'Mensual')
                if frec == 'Bimestral': imp = imp / 2
                elif frec == 'Trimestral': imp = imp / 3
                elif frec == 'Anual': imp = imp / 12
                total_fijos_mes += imp
                
        # CÁLCULOS GLOBALES
        gastos_totales = total_compras + total_fijos_mes
        balance_neto = total_ventas - gastos_totales

        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        st.markdown(f"#### 💰 Balance Financiero ({meses[mes_sel-1]} {anio_sel})")
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1: 
            st.metric(label="Ingresos (Ventas TPV)", value=f"{total_ventas:.2f} €")
        with col_m2: 
            st.metric(label="Prov. y Variables (Facturas)", value=f"-{total_compras:.2f} €", help="Facturas de proveedores, mercancía y gastos puntuales registrados este mes.")
        with col_m3: 
            st.metric(label="Gastos Fijos (Prorrateo)", value=f"-{total_fijos_mes:.2f} €", help="Cálculo mensualizado de alquiler, luz, nóminas, préstamos e impuestos trimestrales.")
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
            c_tit, c_sel = st.columns([1.5, 1])
            with c_tit: st.markdown("**📊 Evolución de Ingresos**")
            with c_sel: rango_evo = st.selectbox("Ver por:", ["Mes actual (Diario)", "Últimos 3 meses (Semana)", "Año actual (Mensual)"], label_visibility="collapsed")
            
            if rango_evo == "Mes actual (Diario)":
                if not df_v.empty:
                    ventas_diarias = df_v.groupby('Fecha')['total'].sum().reset_index()
                    ventas_diarias.set_index('Fecha', inplace=True)
                    st.bar_chart(ventas_diarias, color="#005275", height=280)
                else:
                    st.info("Aún no hay ventas registradas en este mes.")
            else:
                if rango_evo == "Últimos 3 meses (Semana)":
                    f_inicio_evo = (pd.to_datetime('today') - pd.Timedelta(days=90)).strftime('%Y-%m-%dT00:00:00')
                else:
                    f_inicio_evo = f"{anio_sel}-01-01T00:00:00"
                    
                res_evo = client.table("ventas_historial").select("created_at, total, estado").gte("created_at", f_inicio_evo).neq("estado", "DEVUELTO").execute()
                if res_evo.data:
                    df_evo = pd.DataFrame(res_evo.data)
                    df_evo['created_at'] = pd.to_datetime(df_evo['created_at'])
                    if rango_evo == "Últimos 3 meses (Semana)":
                        df_evo['Semana'] = df_evo['created_at'].dt.to_period('W').apply(lambda r: r.start_time.strftime('%d/%m'))
                        evo_chart = df_evo.groupby('Semana')['total'].sum()
                    else:
                        meses_es_map = {1:"Ene", 2:"Feb", 3:"Mar", 4:"Abr", 5:"May", 6:"Jun", 7:"Jul", 8:"Ago", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dic"}
                        df_evo['MesNum'] = df_evo['created_at'].dt.month
                        df_evo['Mes'] = df_evo['MesNum'].map(meses_es_map)
                        evo_chart = df_evo.groupby(['MesNum', 'Mes'])['total'].sum().reset_index().set_index('Mes')['total']
                        
                    st.bar_chart(evo_chart, color="#005275", height=280)
                else:
                    st.info("No hay datos para este periodo.")
                
        with col_g2:
            c_tit2, c_sel2 = st.columns([1, 1.2])
            with c_tit2: st.markdown("**💸 Estructura Gastos**")
            with c_sel2: vista_gastos = st.selectbox("Detalle:", ["Resumen Fijos vs Variables", "Desglose Variables"], label_visibility="collapsed")
            
            if vista_gastos == "Resumen Fijos vs Variables":
                if total_compras > 0 or total_fijos_mes > 0:
                    df_gastos_pie = pd.DataFrame({
                        "Categoría": ["Variables/Proveedores", "Fijos Mensualizados"],
                        "Importe": [total_compras, total_fijos_mes]
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
                    st.info("No hay facturas variables este mes.")
                
        st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
        
        # NUEVA FILA DE GRÁFICAS: TOP VENTAS Y MÉTODOS DE PAGO
        col_g3, col_g4 = st.columns([1.5, 1])
        
        with col_g3:
            st.markdown("**⭐ Top 10 Productos y Servicios (Por Ingresos €)**")
            if not df_v.empty and 'productos' in df_v.columns:
                lista_prods = []
                for prods in df_v['productos'].dropna():
                    if isinstance(prods, list):
                        lista_prods.extend(prods)
                
                if lista_prods:
                    df_p = pd.DataFrame(lista_prods)
                    if 'Producto' in df_p.columns and 'Subtotal' in df_p.columns:
                        top_prods = df_p.groupby('Producto')['Subtotal'].sum().sort_values(ascending=False).head(10)
                        st.bar_chart(top_prods, color="#2e7d32", height=350)
                    else:
                        st.info("Formato de productos no compatible en histórico antiguo.")
                else:
                    st.info("No hay detalle de productos en los tickets de este mes.")
            else:
                st.info("Aún no hay ventas para generar el ranking.")
                
        with col_g4:
            st.markdown("**💳 Tesorería: Métodos de Pago**")
            if not df_v.empty and 'metodo_pago' in df_v.columns:
                def simplificar_metodo(m):
                    m = str(m)
                    if "Tarjeta" in m: return "Tarjeta"
                    if "Mixto" in m: return "Pago Mixto"
                    return m
                
                df_v['Metodo Simplificado'] = df_v['metodo_pago'].apply(simplificar_metodo)
                dist_pagos = df_v.groupby('Metodo Simplificado')['total'].sum()
                st.bar_chart(dist_pagos, color="#f9a825", height=350)
            else:
                st.info("No hay datos de métodos de pago este mes.")

    except Exception as e:
        st.error(f"Error al cargar las estadísticas: {e}")