import streamlit as st
import pandas as pd

@st.cache_data(ttl=300)
def get_configuracion_negocio(_client):
    res = _client.table("configuracion_negocio").select("*").eq("id", 1).execute()
    if res.data:
        return res.data[0]
    return {
        'nombre_tienda': 'Animalarium',
        'envio_gratis_a_partir_de': 110.00,
        'coste_envio_cercania': 5.00,
        'coste_envio_lejos': 10.00,
        'euros_para_un_punto': 10.00,
        'valor_punto_euros': 0.50,
        'limite_descuento_puntos_porcentaje': 50.00,
        'descuento_primera_compra_web_porcentaje': 10.00,
        'descuento_cajas_completas_porcentaje': 7.00,
        'descuento_retorno_tienda_porcentaje': 10.00,
        'dias_maximos_retorno_tienda': 60
    }

def clear_configuracion_cache():
    get_configuracion_negocio.clear()

def render_pestana_configuracion(client):
    st.header("⚙️ Configuración del Negocio (Parametrización)")
    st.write("Desde esta sección puedes ajustar las reglas comerciales del TPV y de la tienda web. "
             "Estos valores determinan los descuentos, puntos y umbrales de envío.")
    
    # 1. Recuperar la configuración actual de la base de datos
    res = client.table("configuracion_negocio").select("*").eq("id", 1).execute()
    
    if not res.data:
        st.error("No se encontró la configuración en la base de datos. Por favor, ejecuta el script de migración SQL en Supabase primero.")
        st.stop()
        
    config = res.data[0]
    
    # Formulario para editar la configuración
    with st.form("form_config_negocio"):
        st.subheader("Datos del Negocio")
        nombre_tienda = st.text_input("Nombre de la Tienda", value=config.get('nombre_tienda', 'Animalarium'))
        
        st.divider()
        
        st.subheader("🌐 Configuración Web (Envíos y Promociones)")
        c1, c2, c3 = st.columns(3)
        with c1:
            envio_gratis = st.number_input("Envío Gratis a partir de (€)", min_value=0.0, value=float(config.get('envio_gratis_a_partir_de', 110.0)), step=5.0)
            dto_primera = st.number_input("Dto. Primera Compra Web (%)", min_value=0.0, max_value=100.0, value=float(config.get('descuento_primera_compra_web_porcentaje', 10.0)), step=1.0)
        with c2:
            envio_cercania = st.number_input("Coste Envío Cercanía (€)", min_value=0.0, value=float(config.get('coste_envio_cercania', 5.0)), step=1.0)
            dto_cajas = st.number_input("Dto. Cajas Completas (%)", min_value=0.0, max_value=100.0, value=float(config.get('descuento_cajas_completas_porcentaje', 7.0)), step=1.0)
        with c3:
            envio_lejos = st.number_input("Coste Envío Larga Distancia (€)", min_value=0.0, value=float(config.get('coste_envio_lejos', 10.0)), step=1.0)
            
        st.divider()
        
        st.subheader("⭐ Fidelización y Puntos (TPV y Web)")
        c4, c5, c6 = st.columns(3)
        with c4:
            eur_punto = st.number_input("¿Cuántos Euros generan 1 Punto?", min_value=0.1, value=float(config.get('euros_para_un_punto', 10.0)), step=1.0)
        with c5:
            valor_punto = st.number_input("¿Cuánto descuenta 1 Punto (€)?", min_value=0.01, value=float(config.get('valor_punto_euros', 0.50)), step=0.05)
        with c6:
            limite_puntos = st.number_input("Límite de canje (% del ticket)", min_value=1.0, max_value=100.0, value=float(config.get('limite_descuento_puntos_porcentaje', 50.0)), step=5.0)
            
        st.divider()
        
        st.subheader("🏪 Retención Tienda Física")
        c7, c8 = st.columns(2)
        with c7:
            dto_retorno = st.number_input("Descuento por retorno (%)", min_value=0.0, max_value=100.0, value=float(config.get('descuento_retorno_tienda_porcentaje', 10.0)), step=1.0)
        with c8:
            dias_retorno = st.number_input("Días máximos para el retorno", min_value=1, value=int(config.get('dias_maximos_retorno_tienda', 60)), step=5)
            
        guardar = st.form_submit_button("💾 Guardar Configuración", type="primary", use_container_width=True)
        
        if guardar:
            payload = {
                "nombre_tienda": nombre_tienda,
                "envio_gratis_a_partir_de": envio_gratis,
                "coste_envio_cercania": envio_cercania,
                "coste_envio_lejos": envio_lejos,
                "descuento_primera_compra_web_porcentaje": dto_primera,
                "descuento_cajas_completas_porcentaje": dto_cajas,
                "euros_para_un_punto": eur_punto,
                "valor_punto_euros": valor_punto,
                "limite_descuento_puntos_porcentaje": limite_puntos,
                "descuento_retorno_tienda_porcentaje": dto_retorno,
                "dias_maximos_retorno_tienda": dias_retorno,
                "actualizado_en": pd.Timestamp.now(tz="Atlantic/Canary").isoformat()
            }
            try:
                client.table("configuracion_negocio").update(payload).eq("id", 1).execute()
                clear_configuracion_cache()
                st.success("Configuración actualizada correctamente. Los cambios ya están activos en el TPV y la Web.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")
