import streamlit as st
import pandas as pd
from datetime import date
import time
import urllib.parse

def render_pestana_marketing(client):
    st.markdown("<h3 style='margin-top: -15px;'>🎯 Marketing Automatizado y Planificación</h3>", unsafe_allow_html=True)
    
    tab_anual, tab_cumples, tab_campanas, tab_recup = st.tabs([
        "📅 Plan Anual (Calendario)", 
        "🎂 Club de Cumpleaños", 
        "📢 Campañas (Email Masivo)", 
        "♻️ Recuperación (Win-back)"
    ])
    
    with tab_anual:
        st.markdown("#### 🗓️ Calendario de Marketing Anual")
        st.info("Programa tus publicaciones de Instagram, correos periódicos y campañas pagadas para anticiparte a las temporadas (Navidad, Verano, Desparasitación...).")
        
        c_m1, c_m2 = st.columns([1, 2.5])
        with c_m1:
            with st.container(border=True):
                st.markdown("##### ➕ Nueva Acción / Campaña")
                with st.form("nuevo_hijo_marketing", clear_on_submit=True):
                    m_fecha = st.date_input("Fecha planificada (Cuándo sale)", value=date.today())
                    m_canal = st.selectbox("Canal / Medio", [
                        "📱 Instagram (Post / Reel / Story)", 
                        "💰 Campaña Pagada (Ads)", 
                        "📧 Email Masivo (Boletín)", 
                        "💬 WhatsApp a Clientes", 
                        "🏬 Promoción Física en Tienda"
                    ])
                    m_tema = st.text_input("Tema / Producto", placeholder="Ej: Lanzamiento pienso natural...")
                    m_estado = st.selectbox("Estado", ["Idea / Planificado", "En Preparación", "Publicado / Terminado"])
                    
                    if st.form_submit_button("Añadir al Calendario", type="primary", use_container_width=True):
                        if m_tema:
                            try:
                                client.table("marketing_plan").insert({
                                    "fecha_planificada": str(m_fecha), "canal": m_canal, 
                                    "tema": m_tema, "estado": m_estado
                                }).execute()
                                st.success("Añadido al plan anual."); time.sleep(1); st.rerun()
                            except Exception as e:
                                st.error("⚠️ Ejecuta primero el código SQL en Supabase.")
                        else:
                            st.warning("Debes indicar un tema o producto para la campaña.")
        
        with c_m2:
            try:
                res_mkt = client.table("marketing_plan").select("*").order("fecha_planificada", desc=False).execute()
                if res_mkt.data:
                    df_mkt = pd.DataFrame(res_mkt.data)
                    df_mkt['Fecha'] = pd.to_datetime(df_mkt['fecha_planificada'])
                    
                    # Agrupación inteligente por mes y año para crear bloques visuales
                    meses_es = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
                    df_mkt['Mes Visual'] = df_mkt['Fecha'].apply(lambda x: f"{meses_es[x.month]} {x.year}")
                    df_mkt['Fecha_str'] = df_mkt['Fecha'].dt.strftime('%d/%m/%Y')
                    
                    df_vista_m = df_mkt[['id', 'Mes Visual', 'Fecha_str', 'canal', 'tema', 'estado']].copy()
                    df_vista_m.insert(0, "Borrar", False)
                    
                    st.markdown("##### 🗺️ Vista de Proyección de Campañas")
                    ed_mkt = st.data_editor(
                        df_vista_m, hide_index=True, use_container_width=True, height=400,
                        column_config={
                            "Borrar": st.column_config.CheckboxColumn("🗑️"),
                            "Mes Visual": st.column_config.TextColumn("Temporada / Mes", disabled=True),
                            "Fecha_str": "Día",
                            "canal": "Canal Principal", 
                            "tema": "Contenido / Producto",
                            "estado": st.column_config.SelectboxColumn("Estado", options=["Idea / Planificado", "En Preparación", "Publicado / Terminado"]),
                            "id": None
                        }
                    )
                    
                    if st.button("💾 Guardar Cambios en el Calendario"):
                        filas_borrar = ed_mkt[ed_mkt["Borrar"] == True]
                        for _, rb in filas_borrar.iterrows():
                            client.table("marketing_plan").delete().eq("id", rb['id']).execute()
                            
                        filas_validas = ed_mkt[ed_mkt["Borrar"] == False]
                        for _, rv in filas_validas.iterrows():
                            client.table("marketing_plan").update({
                                "estado": rv['estado'], "tema": rv['tema']
                            }).eq("id", rv['id']).execute()
                        st.success("Plan actualizado."); time.sleep(0.5); st.rerun()
                else:
                    st.info("El calendario de marketing está vacío. ¡Empieza a planificar tus campañas para adelantarte a las ventas!")
            except:
                st.info("🔧 Tabla 'marketing_plan' no encontrada. Créala en Supabase con el SQL proporcionado.")
                
    with tab_cumples:
        st.markdown("#### 🎂 Club de Cumpleaños (Próximamente)")
        st.write("El sistema escaneará las fechas de nacimiento de las mascotas y te preparará enlaces de WhatsApp automáticos para felicitarles e invitarles a la tienda a recoger un regalito o descuento.")
        st.image("https://images.unsplash.com/photo-1583337130417-3346a1be7dee?auto=format&fit=crop&w=600&q=80", width=300)
        
    with tab_campanas:
        st.markdown("#### 📢 Campañas Segmentadas por Email (Próximamente)")
        st.write("Redacta un boletín o promoción mensual aquí. El sistema abrirá tu Gmail con los correos de todos tus clientes colocados en Copia Oculta (CCO) automáticamente para respetar la ley de protección de datos.")
        
    with tab_recup:
        st.markdown("#### ♻️ Recuperación de Clientes 'Win-back' (Próximamente)")
        st.write("Generador de listas de clientes que no han visitado la tienda o la peluquería en los últimos 6 meses para enviarles una promoción de rescate.")