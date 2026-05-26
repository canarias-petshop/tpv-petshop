import streamlit as st
import pandas as pd
from datetime import date
import time
import urllib.parse

def render_pestana_marketing(client):
    st.markdown("<h3 style='margin-top: -15px;'>🎯 Marketing Automatizado y Planificación</h3>", unsafe_allow_html=True)
    
    tabs = st.tabs([
        "🎯 Objetivos y Resultados",
        "📅 Plan Maestro y Presupuestos",
        "📢 Gestión por Canales",
        "🚀 Campañas Especiales",
        "♻️ Activas (Win-Back/Cumples)"
    ])
    
    tab_objetivos, tab_maestro, tab_canales, tab_especiales, tab_activas = tabs

    with tab_objetivos:
        st.markdown("#### 🎯 Panel de Control: Objetivos de Marketing")
        st.info("Define las metas claras de tus acciones publicitarias y mide su retorno (ROI).")
        
        try:
            res_obj = client.table("marketing_objetivos").select("*").order("created_at", desc=True).execute()
            objetivos = res_obj.data if res_obj.data else []
        except:
            objetivos = []

        col_obj1, col_obj2 = st.columns([1, 2])
        with col_obj1:
            with st.form("nuevo_objetivo", clear_on_submit=True):
                st.markdown("##### ➕ Crear Nuevo Objetivo")
                o_tit = st.text_input("Título de la Meta (Ej: Aumentar ventas peluquería)")
                o_kpi = st.text_input("Indicador (KPI) (Ej: Nº de tickets, Euros, Clientes nuevos)")
                o_meta = st.number_input("Valor Meta (Objetivo numérico)", min_value=0.0, step=1.0)
                
                c1, c2 = st.columns(2)
                with c1: o_ini = st.date_input("Fecha Inicio")
                with c2: o_fin = st.date_input("Fecha Fin")
                
                if st.form_submit_button("Guardar Objetivo", type="primary", use_container_width=True):
                    if o_tit and o_kpi:
                        client.table("marketing_objetivos").insert({
                            "titulo": o_tit, "kpi_medidor": o_kpi, "meta_cuantitativa": float(o_meta),
                            "fecha_inicio": str(o_ini), "fecha_fin": str(o_fin), "estado": "En progreso",
                            "valor_actual": 0.0
                        }).execute()
                        st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                        st.success("Objetivo creado."); time.sleep(1); st.rerun()
                    else:
                        st.warning("Completa el título y el KPI.")
                        
        with col_obj2:
            st.markdown("##### 📊 Seguimiento de Resultados")
            if objetivos:
                for obj in objetivos:
                    with st.container(border=True):
                        c_m1, c_m2, c_m3 = st.columns([2, 1, 1], vertical_alignment="center")
                        with c_m1:
                            st.markdown(f"**{obj['titulo']}**")
                            st.caption(f"Medidor: {obj['kpi_medidor']} | Fechas: {pd.to_datetime(obj['fecha_inicio']).strftime('%d/%m')} al {pd.to_datetime(obj['fecha_fin']).strftime('%d/%m/%Y')}")
                        with c_m2:
                            st.metric("Progreso", f"{obj['valor_actual']} / {obj['meta_cuantitativa']}")
                        with c_m3:
                            progreso_pct = (obj['valor_actual'] / obj['meta_cuantitativa']) if obj['meta_cuantitativa'] > 0 else 0
                            progreso_pct = min(progreso_pct, 1.0)
                            st.progress(progreso_pct)
                            
                        with st.expander("⚙️ Actualizar Resultados", expanded=False):
                            with st.form(f"upd_obj_{obj['id']}"):
                                c_u1, c_u2 = st.columns(2)
                                with c_u1: n_val = st.number_input("Valor Actualizado", value=float(obj['valor_actual']))
                                with c_u2: n_est = st.selectbox("Estado", ["En progreso", "Completado", "Cancelado"], index=["En progreso", "Completado", "Cancelado"].index(obj['estado']))
                                if st.form_submit_button("Actualizar Progreso", use_container_width=True):
                                    client.table("marketing_objetivos").update({"valor_actual": float(n_val), "estado": str(n_est)}).eq("id", obj['id']).execute()
                                    st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                    st.rerun()
                            if st.button("🗑️ Eliminar Objetivo", key=f"del_obj_{obj['id']}", type="secondary"):
                                client.table("marketing_objetivos").delete().eq("id", obj['id']).execute()
                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                st.rerun()
            else:
                st.info("No hay objetivos definidos en este momento.")
    
    with tab_maestro:
        st.markdown("#### 📅 Plan Maestro y Control de Presupuestos")
        st.info("Programa todas tus publicaciones y acciones publicitarias. Controla el gasto y vincúlalo a tus Objetivos.")
        
        try:
            res_alert = client.table("marketing_plan").select("fecha_planificada").order("fecha_planificada", desc=True).limit(1).execute()
            if res_alert.data:
                ultima_fecha = pd.to_datetime(res_alert.data[0]['fecha_planificada']).date()
                dias_restantes = (ultima_fecha - date.today()).days
                
                if 0 <= dias_restantes <= 30:
                    st.error(f"🚨 **¡ALERTA DE CONTENIDO!** Tu plan de marketing programado se agota el **{ultima_fecha.strftime('%d/%m/%Y')}** (en {dias_restantes} días). ¡Pídele a tu asistente que te redacte y prepare la campaña de la siguiente temporada!")
                elif 30 < dias_restantes <= 45:
                    st.warning(f"⚠️ **Aviso de Temporada:** Tu plan de marketing actual abarca hasta el **{ultima_fecha.strftime('%d/%m/%Y')}**. Recuerda solicitar la redacción de la próxima tanda de publicaciones pronto para no quedarte sin contenido.")
        except Exception:
            pass

        c_m1, c_m2 = st.columns([1, 2.5])
        with c_m1:
            with st.container(border=True):
                st.markdown("##### ➕ Nueva Acción / Campaña")
                with st.form("nuevo_hijo_marketing", clear_on_submit=True):
                    m_fecha = st.date_input("Fecha planificada", value=date.today())
                    m_cat = st.selectbox("Categoría / Soporte", ["Digital (RRSS/Email)", "Físico (Cartelería/Flyers)", "Medios (Radio/Prensa)"])
                    m_canal = st.selectbox("Canal Específico", [
                        "📱 Instagram / Facebook", "💰 Campaña Pagada (Ads)", "📧 Email Masivo", 
                        "💬 WhatsApp a Clientes", "🏬 Cartelería / Diseño Físico", "🎙️ Cuña de Radio", "Otras acciones"
                    ])
                    
                    m_tipo = st.selectbox("Tipo de Campaña", ["Acción Ordinaria (Día a Día)", "Campaña de Evento/Feria", "Iniciativa Innovate"])
                    
                    opciones_obj = {"Ninguno": None}
                    if objetivos: opciones_obj.update({f"{o['titulo']} ({o['estado']})": o['id'] for o in objetivos})
                    m_obj = st.selectbox("Vincular a un Objetivo", list(opciones_obj.keys()))
                    
                    m_tema = st.text_input("Tema / Producto", placeholder="Ej: Lanzamiento pienso natural...")
                    
                    c_pres1, c_pres2 = st.columns(2)
                    with c_pres1: m_pres = st.number_input("Presupuesto Asignado (€)", min_value=0.0, step=10.0, format="%.2f")
                    with c_pres2: m_gast = st.number_input("Gasto Real Ejecutado (€)", min_value=0.0, step=10.0, format="%.2f")
                    
                    m_contenido = st.text_area("Texto / Copy o Detalles", placeholder="Escribe aquí el guion del anuncio, texto del post, instrucciones para carteles...", height=100)
                    m_estado = st.selectbox("Estado", ["Idea / Planificado", "En Preparación", "Publicado / Terminado"])
                    
                    if st.form_submit_button("Añadir al Calendario", type="primary", use_container_width=True):
                        if m_tema:
                            try:
                                client.table("marketing_plan").insert({
                                    "fecha_planificada": str(m_fecha), "canal": m_canal, "tema": m_tema, "estado": m_estado,
                                    "contenido_detallado": m_contenido, "presupuesto": float(m_pres), "gasto_real": float(m_gast),
                                    "tipo_campana": m_tipo, "canal_categoria": m_cat, "objetivo_id": opciones_obj[m_obj]
                                }).execute()
                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                st.success("Añadido al plan anual."); time.sleep(1); st.rerun()
                            except Exception as e:
                                st.error("⚠️ Ejecuta primero el código SQL en Supabase.")
                        else:
                            st.warning("Debes indicar un tema o producto para la campaña.")
        
        with c_m2:
            try:
                res_mkt = client.table("marketing_plan").select("*, marketing_objetivos(titulo)").order("fecha_planificada", desc=False).execute()
                if res_mkt.data:
                    df_mkt = pd.DataFrame(res_mkt.data)
                    df_mkt['Fecha'] = pd.to_datetime(df_mkt['fecha_planificada'])
                    
                    total_presupuesto = df_mkt.get('presupuesto', pd.Series([0.0])).sum()
                    total_gastado = df_mkt.get('gasto_real', pd.Series([0.0])).sum()
                    
                    st.markdown("##### 📈 Dashboard de Inversión Publicitaria")
                    kpi1, kpi2, kpi3 = st.columns(3)
                    kpi1.metric("Presupuesto Total", f"{total_presupuesto:.2f} €")
                    kpi2.metric("Gasto Real Ejecutado", f"{total_gastado:.2f} €")
                    kpi3.metric("Margen Libre", f"{(total_presupuesto - total_gastado):.2f} €", delta_color="normal" if total_presupuesto >= total_gastado else "inverse")
                    st.markdown("---")
                    
                    # Agrupación inteligente por mes y año para crear bloques visuales
                    meses_es = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
                    df_mkt['Mes Visual'] = df_mkt['Fecha'].apply(lambda x: f"{meses_es[x.month]} {x.year}")
                    df_mkt['Fecha_str'] = df_mkt['Fecha'].dt.strftime('%d/%m/%Y')
                    
                    df_vista_m = df_mkt[['id', 'Mes Visual', 'Fecha_str', 'canal', 'tema', 'presupuesto', 'gasto_real', 'estado']].copy()
                    if 'presupuesto' not in df_vista_m.columns: df_vista_m['presupuesto'] = 0.0
                    if 'gasto_real' not in df_vista_m.columns: df_vista_m['gasto_real'] = 0.0
                    
                    df_vista_m.insert(0, "Borrar", False)
                    
                    st.markdown("##### 🗺️ Vista de Proyección de Campañas")
                    ed_mkt = st.data_editor(
                        df_vista_m, hide_index=True, use_container_width=True, height=350,
                        column_config={
                            "Borrar": st.column_config.CheckboxColumn("🗑️"),
                            "Mes Visual": st.column_config.TextColumn("Temporada / Mes", disabled=True),
                            "Fecha_str": "Día",
                            "canal": "Medio / Soporte", 
                            "tema": "Contenido",
                            "presupuesto": st.column_config.NumberColumn("Presup. (€)", format="%.2f"),
                            "gasto_real": st.column_config.NumberColumn("Gasto (€)", format="%.2f"),
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
                                "estado": rv['estado'], "tema": rv['tema'],
                                "presupuesto": float(rv['presupuesto']), "gasto_real": float(rv['gasto_real'])
                            }).eq("id", rv['id']).execute()
                        st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                        st.success("Plan actualizado."); time.sleep(0.5); st.rerun()
                else:
                    st.info("El calendario de marketing está vacío. ¡Empieza a planificar tus campañas para adelantarte a las ventas!")
            except:
                st.info("🔧 Tabla 'marketing_plan' no encontrada. Créala en Supabase con el SQL proporcionado.")
                
    with tab_canales:
        st.markdown("#### 📢 Análisis de Presupuesto por Canales y Soportes")
        st.info("Analiza cómo se distribuye tu inversión publicitaria a través de medios digitales, físicos y tradicionales.")
        try:
            res_canales = client.table("marketing_plan").select("canal_categoria, canal, presupuesto, gasto_real").execute()
            if res_canales.data:
                df_canales = pd.DataFrame(res_canales.data)
                c_can1, c_can2 = st.columns(2)
                with c_can1:
                    st.markdown("##### 💰 Inversión por Categoría Principal")
                    inv_cat = df_canales.groupby('canal_categoria')['gasto_real'].sum().reset_index()
                    st.bar_chart(inv_cat.set_index('canal_categoria'), color="#ff9800")
                with c_can2:
                    st.markdown("##### 📊 Desglose de Gasto por Soporte")
                    inv_soporte = df_canales.groupby('canal').agg({'presupuesto': 'sum', 'gasto_real': 'sum'}).reset_index()
                    st.dataframe(inv_soporte, hide_index=True, use_container_width=True, column_config={"canal": "Soporte", "presupuesto": st.column_config.NumberColumn("Presupuesto Asignado (€)", format="%.2f"), "gasto_real": st.column_config.NumberColumn("Gasto Realizado (€)", format="%.2f")})
            else:
                st.info("No hay datos suficientes para generar estadísticas por canal.")
        except: pass

    with tab_especiales:
        st.markdown("#### 🚀 Gestión de Campañas Especiales (Ferias e Innovate)")
        st.info("Revisa las acciones de marketing que están vinculadas a grandes eventos o a la iniciativa Innovate.")
        try:
            res_esp = client.table("marketing_plan").select("*").in_("tipo_campana", ["Campaña de Evento/Feria", "Iniciativa Innovate"]).order("fecha_planificada", desc=False).execute()
            if res_esp.data:
                df_esp = pd.DataFrame(res_esp.data)
                df_esp['Fecha'] = pd.to_datetime(df_esp['fecha_planificada']).dt.strftime('%d/%m/%Y')
                st.dataframe(df_esp[['Fecha', 'tipo_campana', 'canal', 'tema', 'presupuesto', 'gasto_real', 'estado']], hide_index=True, use_container_width=True, column_config={"tipo_campana": "Macro-Campaña", "canal": "Soporte", "tema": "Acción / Contenido", "presupuesto": st.column_config.NumberColumn("Presupuesto (€)", format="%.2f"), "gasto_real": st.column_config.NumberColumn("Gasto Real (€)", format="%.2f")})
            else:
                st.success("No tienes campañas especiales activas en este momento.")
        except: pass

    with tab_activas:
        st.markdown("#### ♻️ Acciones de Recuperación y Fidelización")
        c_act1, c_act2 = st.columns(2)
        with c_act1:
            st.markdown("##### 🎂 Club de Cumpleaños")
            st.write("Próximamente: El sistema escaneará las fechas de nacimiento de las mascotas para preparar enlaces de WhatsApp automáticos de felicitación.")
            st.image("https://images.unsplash.com/photo-1583337130417-3346a1be7dee?auto=format&fit=crop&w=600&q=80", width=300)
        with c_act2:
            st.markdown("##### ♻️ Recuperación (Win-back) y Emailing")
            st.write("Próximamente: Motor analítico para rastrear clientes sin visitar la tienda en 6 meses y preparar ofertas segmentadas.")