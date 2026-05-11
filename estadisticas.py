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
        res_ventas = client.table("ventas_historial").select("created_at, total, estado").gte("created_at", fecha_ini).lt("created_at", fecha_fin).execute()
        total_ventas = 0.0
        df_v = pd.DataFrame()
        if res_ventas.data:
            df_v = pd.DataFrame(res_ventas.data)
            df_v = df_v[df_v['estado'] != 'DEVUELTO']
            if not df_v.empty:
                total_ventas = df_v['total'].sum()
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
            
        st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
        
        col_g1, col_g2 = st.columns([1.5, 1])
        
        with col_g1:
            st.markdown("**📊 Evolución de Ingresos por Día**")
            if not df_v.empty:
                ventas_diarias = df_v.groupby('Fecha')['total'].sum().reset_index()
                ventas_diarias.set_index('Fecha', inplace=True)
                st.bar_chart(ventas_diarias, color="#005275", height=280)
            else:
                st.info("Aún no hay ventas registradas en este mes para generar el gráfico.")
                
        with col_g2:
            st.markdown("**💸 Proporción de Gastos**")
            if total_compras > 0 or total_fijos_mes > 0:
                df_gastos_pie = pd.DataFrame({
                    "Categoría": ["Proveedores y Variables", "Fijos Mensualizados"],
                    "Importe": [total_compras, total_fijos_mes]
                }).set_index("Categoría")
                
                st.bar_chart(df_gastos_pie, color="#d32f2f", height=280)
            else:
                st.info("No hay gastos variables registrados ni fijos activos.")

    except Exception as e:
        st.error(f"Error al cargar las estadísticas: {e}")