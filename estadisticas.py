import streamlit as st
import pandas as pd

def render_pestana_estadisticas(client):
    st.markdown("<h3 style='margin-bottom: 5px;'>📈 Contabilidad y Estadísticas</h3>", unsafe_allow_html=True)
    st.write("Resumen global de la salud financiera de Animalarium.")
    
    try:
        res_ventas = client.table("ventas_historial").select("created_at, total, estado").execute()
        res_movs = client.table("movimientos_caja").select("created_at, tipo, cantidad").execute()
        
        total_ventas = 0.0
        total_gastos = 0.0
        df_v = pd.DataFrame()
        df_m = pd.DataFrame()

        if res_ventas.data:
            df_v = pd.DataFrame(res_ventas.data)
            df_v = df_v[df_v['estado'] != 'DEVUELTO']
            if not df_v.empty:
                total_ventas = df_v['total'].sum()
                df_v['Fecha'] = pd.to_datetime(df_v['created_at']).dt.date
        
        if res_movs.data:
            df_m = pd.DataFrame(res_movs.data)
            df_m_gastos = df_m[df_m['tipo'] == 'Retirada']
            if not df_m_gastos.empty:
                total_gastos = df_m_gastos['cantidad'].sum()
                df_m['Fecha'] = pd.to_datetime(df_m['created_at']).dt.date

        balance_neto = total_ventas - total_gastos

        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1: st.metric(label="Ingresos Totales (Ventas)", value=f"{total_ventas:.2f} €")
        with col_m2: st.metric(label="Gastos de Caja (Retiradas)", value=f"-{total_gastos:.2f} €")
        with col_m3: st.metric(label="Balance Neto", value=f"{balance_neto:.2f} €", delta=f"{balance_neto:.2f} €")
            
        st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
        st.markdown("**📊 Evolución de Ventas por Día**")
        if not df_v.empty:
            ventas_diarias = df_v.groupby('Fecha')['total'].sum().reset_index()
            ventas_diarias.set_index('Fecha', inplace=True)
            st.bar_chart(ventas_diarias, color="#005275", height=250)
        else:
            st.info("Aún no hay suficientes ventas para generar el gráfico.")

    except Exception as e:
        st.error(f"Error al cargar las estadísticas: {e}")