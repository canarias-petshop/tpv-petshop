import streamlit as st
import pandas as pd
from datetime import date
import time
import urllib.parse

def render_pestana_marketing(client):
    st.markdown("<h3 style='margin-top: -15px;'>🎯 Marketing Automatizado y Planificación</h3>", unsafe_allow_html=True)
    
    tab_anual, tab_eventos, tab_cumples, tab_campanas, tab_recup = st.tabs([
        "📅 Plan Anual (Calendario)", 
        "🎟️ Eventos y Talleres",
        "🎂 Club de Cumpleaños", 
        "📢 Campañas (Email Masivo)", 
        "♻️ Recuperación (Win-back)"
    ])
    
    with tab_anual:
        st.markdown("#### 🗓️ Calendario de Marketing Anual")
        st.info("Programa tus publicaciones de Instagram, correos periódicos y campañas pagadas para anticiparte a las temporadas (Navidad, Verano, Desparasitación...).")
        
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
                    m_fecha = st.date_input("Fecha planificada (Cuándo sale)", value=date.today())
                    m_canal = st.selectbox("Canal / Medio", [
                        "📱 Instagram (Post / Reel / Story)", 
                        "💰 Campaña Pagada (Ads)", 
                        "📧 Email Masivo (Boletín)", 
                        "💬 WhatsApp a Clientes", 
                        "🏬 Promoción Física en Tienda"
                    ])
                    m_tema = st.text_input("Tema / Producto", placeholder="Ej: Lanzamiento pienso natural...")
                    m_contenido = st.text_area("Texto / Copy exacto (Listo para publicar)", placeholder="Escribe aquí el texto del post, hashtags, emojis...", height=100)
                    m_estado = st.selectbox("Estado", ["Idea / Planificado", "En Preparación", "Publicado / Terminado"])
                    
                    if st.form_submit_button("Añadir al Calendario", type="primary", use_container_width=True):
                        if m_tema:
                            try:
                                client.table("marketing_plan").insert({
                                    "fecha_planificada": str(m_fecha), "canal": m_canal, 
                                    "tema": m_tema, "estado": m_estado,
                                    "contenido_detallado": m_contenido
                                }).execute()
                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
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
                    
                    if 'contenido_detallado' not in df_mkt.columns: df_mkt['contenido_detallado'] = ""
                    
                    df_vista_m = df_mkt[['id', 'Mes Visual', 'Fecha_str', 'canal', 'tema', 'contenido_detallado', 'estado']].copy()
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
                            "contenido_detallado": st.column_config.TextColumn("Texto Exacto (Copy)", width="large"),
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
                                "contenido_detallado": str(rv['contenido_detallado'])
                            }).eq("id", rv['id']).execute()
                        st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                        st.success("Plan actualizado."); time.sleep(0.5); st.rerun()
                else:
                    st.info("El calendario de marketing está vacío. ¡Empieza a planificar tus campañas para adelantarte a las ventas!")
            except:
                st.info("🔧 Tabla 'marketing_plan' no encontrada. Créala en Supabase con el SQL proporcionado.")
                
    with tab_eventos:
        st.markdown("#### 🎟️ Gestión de Eventos y Talleres")
        st.info("Organiza cursos de fin de semana (cepillado, nutrición, etc.), controla el aforo y gestiona las reservas de los clientes.")
        
        c_ev1, c_ev2 = st.columns([1, 2.5])
        
        with c_ev1:
            with st.container(border=True):
                st.markdown("##### ➕ Crear Nuevo Evento")
                with st.form("form_nuevo_evento", clear_on_submit=True):
                    e_titulo = st.text_input("Título del Taller *", placeholder="Ej: Taller de cepillado básico")
                    e_fecha = st.date_input("Fecha planificada", value=date.today())
                    e_hora = st.text_input("Hora y Turno", placeholder="Ej: Sábado 10:00 - 12:00")
                    c_e1, c_e2 = st.columns(2)
                    with c_e1: e_plazas = st.number_input("Plazas totales", min_value=1, value=8)
                    with c_e2: e_precio = st.number_input("Precio Reserva (€)", min_value=0.0, format="%.2f", value=15.0, step=0.01)
                    e_desc = st.text_area("Descripción / Temario")
                    
                    if st.form_submit_button("Crear Evento", type="primary", use_container_width=True):
                        if e_titulo:
                            try:
                                client.table("eventos_talleres").insert({
                                    "titulo": e_titulo, "fecha": str(e_fecha), "hora": e_hora,
                                    "plazas_totales": int(e_plazas), "precio": float(e_precio), "descripcion": e_desc
                                }).execute()
                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                st.success("Evento creado en el calendario."); time.sleep(1); st.rerun()
                            except Exception as e:
                                st.error("⚠️ Ejecuta el código SQL en Supabase primero.")
                        else:
                            st.warning("El título es obligatorio.")
                            
        with c_ev2:
            try:
                res_ev = client.table("eventos_talleres").select("*").order("fecha", desc=False).execute()
                if res_ev.data:
                    df_ev = pd.DataFrame(res_ev.data)
                    df_ev['Fecha'] = pd.to_datetime(df_ev['fecha']).dt.strftime('%d/%m/%Y')
                    
                    st.markdown("##### 📅 Panel de Gestión de Inscripciones")
                    opciones_ev = {f"{e['Fecha']} | {e['titulo']} (Reserva: {e['precio']}€)": e['id'] for _, e in df_ev.iterrows()}
                    ev_sel_str = st.selectbox("Selecciona un evento para gestionar su aforo:", list(opciones_ev.keys()))
                    
                    if ev_sel_str:
                        ev_id = opciones_ev[ev_sel_str]
                        ev_data = df_ev[df_ev['id'] == ev_id].iloc[0]
                        
                        res_asi = client.table("eventos_asistentes").select("id, pagado, clientes(nombre_dueno, telefono)").eq("evento_id", ev_id).execute()
                        inscritos = len(res_asi.data) if res_asi.data else 0
                        plazas_libres = ev_data['plazas_totales'] - inscritos
                        
                        st.markdown(f"**Aforo actual:** {inscritos} de {ev_data['plazas_totales']} plazas ocupadas. (<span style='color:green;'>{plazas_libres} libres</span>)", unsafe_allow_html=True)
                        st.progress(inscritos / ev_data['plazas_totales'] if ev_data['plazas_totales'] > 0 else 0)
                        
                        c_asi1, c_asi2 = st.columns([2, 1])
                        with c_asi1:
                            res_cli = client.table("clientes").select("id, nombre_dueno, telefono").execute()
                            dict_cli = {f"{c['nombre_dueno']} ({c.get('telefono','')})": c['id'] for c in res_cli.data} if res_cli.data else {}
                            cli_sel = st.selectbox("Inscribir nuevo cliente al evento:", [""] + list(dict_cli.keys()))
                        with c_asi2:
                            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                            if st.button("➕ Añadir a la Lista", use_container_width=True, disabled=plazas_libres<=0):
                                if cli_sel:
                                    try:
                                        client.table("eventos_asistentes").insert({"evento_id": ev_id, "cliente_id": dict_cli[cli_sel], "pagado": False}).execute()
                                        st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                        st.success("Inscrito correctamente."); time.sleep(0.5); st.rerun()
                                    except: st.error("Este cliente ya estaba inscrito.")
                                    
                        if res_asi.data:
                            df_a = pd.DataFrame([{"id": a['id'], "Cliente": a['clientes']['nombre_dueno'], "Teléfono": a['clientes']['telefono'], "Reserva Pagada": a['pagado']} for a in res_asi.data])
                            df_a_vista = df_a.copy()
                            df_a_vista.insert(0, "Quitar", False)
                            
                            ed_a = st.data_editor(
                                df_a_vista, hide_index=True, use_container_width=True,
                                column_config={
                                    "Quitar": st.column_config.CheckboxColumn("🗑️", width="small"),
                                    "Reserva Pagada": st.column_config.CheckboxColumn("💰 Reserva Pagada"),
                                    "id": None, "Cliente": st.column_config.TextColumn(disabled=True), "Teléfono": st.column_config.TextColumn(disabled=True)
                                }, key=f"ed_asi_{ev_id}"
                            )
                            if st.button("💾 Guardar Cambios en la Lista de Asistentes", type="primary"):
                                for _, rb in ed_a[ed_a["Quitar"] == True].iterrows(): client.table("eventos_asistentes").delete().eq("id", rb['id']).execute()
                                for _, rg in ed_a[ed_a["Quitar"] == False].iterrows(): client.table("eventos_asistentes").update({"pagado": bool(rg['Reserva Pagada'])}).eq("id", rg['id']).execute()
                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                st.rerun()
                else:
                    st.info("No hay eventos programados. Rellena el formulario de la izquierda para crear el primero.")
            except Exception as e:
                st.info("🔧 Ejecuta el código SQL en Supabase para activar la función de Eventos.")

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