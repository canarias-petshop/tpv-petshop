import streamlit as st
import pandas as pd
import time
import urllib.parse
from datetime import date

def render_pestana_servicios(client):
    if 'llave_srv_paseo' not in st.session_state: st.session_state.llave_srv_paseo = 0
    if 'llave_srv_adiest' not in st.session_state: st.session_state.llave_srv_adiest = 0
    if 'llave_srv_reco' not in st.session_state: st.session_state.llave_srv_reco = 0
    if 'llave_srv_dom' not in st.session_state: st.session_state.llave_srv_dom = 0

    st.markdown("<h3 style='margin-top: -15px;'>🐶 Servicios Extra de Animalarium</h3>", unsafe_allow_html=True)
    st.info("Gestiona los servicios complementarios: paseos, educación canina y logística a domicilio.")

    # Cargar clientes y mascotas para sugerencias
    try:
        res_clientes = client.table("clientes").select("id, nombre_dueno, telefono, direccion, mascotas(nombre)").execute()
        lista_cli = res_clientes.data if res_clientes.data else []
    except: lista_cli = []

    opc_cli = ["👤 Cliente no registrado (Manual)"]
    mapa_cli = {}
    for c in lista_cli:
        etiqueta = f"{c['nombre_dueno']} | {c.get('telefono','')}"
        opc_cli.append(etiqueta)
        mapa_cli[etiqueta] = c
            
    t_paseos, t_adiestramiento, t_domicilio = st.tabs([
        "🐕 Servicio de Paseo", 
        "🎓 Adiestramiento y Educación", 
        "🚚 Servicios a Domicilio"
    ])
    
    with t_paseos:
        st.markdown("#### 🐕 Registro de Servicio de Paseo")
        col_p1, col_p2 = st.columns([1, 2.2])
        with col_p1:
            with st.form("form_paseo", clear_on_submit=True):
                sel_cli_p = st.selectbox("1. Seleccionar Cliente:", opc_cli, key=f"sp_sel_{st.session_state.llave_srv_paseo}")
                st.markdown("<p style='font-size:12px; color:gray; margin:0;'>O rellénalo a mano:</p>", unsafe_allow_html=True)
                p_cli_man = st.text_input("Nombre Dueño")
                p_tel_man = st.text_input("Teléfono")
                p_masc_man = st.text_input("Nombre Mascota *")
                
                st.markdown("---")
                p_tipo = st.selectbox("2. Tipo de Paseo:", ["Paseo por la ciudad", "Paseo al monte"])
                p_fecha = st.text_input("3. Fecha y Hora", placeholder="Ej: Mañana a las 10:00, Lunes tarde...")
                p_obs = st.text_area("4. Observaciones", placeholder="Carácter, rutas preferidas, duración...")
                
                if st.form_submit_button("Guardar Paseo", type="primary", use_container_width=True):
                    final_cli = p_cli_man
                    final_tel = p_tel_man
                    if "no registrado" not in sel_cli_p:
                        final_cli = mapa_cli[sel_cli_p]['nombre_dueno']
                        final_tel = mapa_cli[sel_cli_p].get('telefono','')
                        
                    if final_cli and p_masc_man:
                        try:
                            client.table("servicios_paseo").insert({
                                "cliente": final_cli, "mascota": p_masc_man, "telefono": final_tel,
                                "tipo_paseo": p_tipo, "fecha": p_fecha, "observaciones": p_obs, "estado": "Pendiente"
                            }).execute()
                            st.session_state.llave_srv_paseo += 1
                            st.success("Paseo registrado."); time.sleep(0.5); st.rerun()
                        except: st.error("⚠️ Crea la tabla 'servicios_paseo' en Supabase.")
                    else: st.warning("Debes indicar el cliente y la mascota.")
        with col_p2:
            st.markdown("#### 📌 Paseos Programados")
            try:
                res_p = client.table("servicios_paseo").select("*").order("created_at", desc=True).execute()
                if res_p.data:
                    df_p = pd.DataFrame(res_p.data)
                    df_p_vista = df_p[['id', 'cliente', 'mascota', 'telefono', 'tipo_paseo', 'fecha', 'observaciones', 'estado']].copy()
                    df_p_vista.insert(0, "Borrar", False)
                    ed_p = st.data_editor(
                        df_p_vista, hide_index=True, use_container_width=True, num_rows="dynamic",
                        column_config={
                            "Borrar": st.column_config.CheckboxColumn("🗑️", width="small"),
                            "id": None, "cliente": "Cliente", "mascota": "Mascota", "telefono": "Tel.",
                            "tipo_paseo": "Tipo", "fecha": "Fecha/Hora", "observaciones": "Obs.",
                            "estado": st.column_config.SelectboxColumn("Estado", options=["Pendiente", "En curso", "Completado", "Cancelado"])
                        }, key="ed_paseos"
                    )
                    if st.button("💾 Guardar Cambios en Paseos", type="primary"):
                        for _, r in ed_p[ed_p["Borrar"] == True].iterrows():
                            if pd.notna(r['id']): client.table("servicios_paseo").delete().eq("id", r['id']).execute()
                        for _, r in ed_p[ed_p["Borrar"] == False].iterrows():
                            if pd.notna(r['id']):
                                client.table("servicios_paseo").update({"estado": str(r['estado'])}).eq("id", r['id']).execute()
                        st.rerun()
                else: st.info("No hay paseos programados.")
            except: st.info("Ejecuta el código SQL para habilitar la tabla de Paseos.")

    with t_adiestramiento:
        st.markdown("#### 🎓 Registro de Adiestramiento y Educación")
        col_a1, col_a2 = st.columns([1, 2.2])
        with col_a1:
            with st.form("form_adiest", clear_on_submit=True):
                sel_cli_a = st.selectbox("1. Seleccionar Cliente:", opc_cli, key=f"sa_sel_{st.session_state.llave_srv_adiest}")
                st.markdown("<p style='font-size:12px; color:gray; margin:0;'>O rellénalo a mano:</p>", unsafe_allow_html=True)
                a_cli_man = st.text_input("Nombre Dueño")
                a_tel_man = st.text_input("Teléfono")
                a_masc_man = st.text_input("Nombre Mascota *")
                
                st.markdown("---")
                a_motivo = st.text_input("2. Nivel / Problema a tratar *", placeholder="Ej: Tirar de la correa, obediencia básica...")
                a_fecha = st.text_input("3. Fecha de Sesión", placeholder="Ej: Sábado por la mañana")
                a_obs = st.text_area("4. Observaciones", placeholder="Detalles de la sesión...")
                
                if st.form_submit_button("Guardar Adiestramiento", type="primary", use_container_width=True):
                    final_cli = a_cli_man
                    final_tel = a_tel_man
                    if "no registrado" not in sel_cli_a:
                        final_cli = mapa_cli[sel_cli_a]['nombre_dueno']
                        final_tel = mapa_cli[sel_cli_a].get('telefono','')
                        
                    if final_cli and a_masc_man and a_motivo:
                        try:
                            client.table("servicios_adiestramiento").insert({
                                "cliente": final_cli, "mascota": a_masc_man, "telefono": final_tel,
                                "motivo": a_motivo, "fecha_sesion": a_fecha, "observaciones": a_obs, "estado": "Pendiente"
                            }).execute()
                            st.session_state.llave_srv_adiest += 1
                            st.success("Sesión registrada."); time.sleep(0.5); st.rerun()
                        except: st.error("⚠️ Crea la tabla 'servicios_adiestramiento' en Supabase.")
                    else: st.warning("Cliente, Mascota y Motivo son obligatorios.")
        with col_a2:
            st.markdown("#### 📌 Sesiones Programadas")
            try:
                res_a = client.table("servicios_adiestramiento").select("*").order("created_at", desc=True).execute()
                if res_a.data:
                    df_a = pd.DataFrame(res_a.data)
                    df_a_vista = df_a[['id', 'cliente', 'mascota', 'telefono', 'motivo', 'fecha_sesion', 'observaciones', 'estado']].copy()
                    df_a_vista.insert(0, "Borrar", False)
                    ed_a = st.data_editor(
                        df_a_vista, hide_index=True, use_container_width=True, num_rows="dynamic",
                        column_config={
                            "Borrar": st.column_config.CheckboxColumn("🗑️", width="small"),
                            "id": None, "cliente": "Cliente", "mascota": "Mascota", "telefono": "Tel.",
                            "motivo": "Motivo", "fecha_sesion": "Fecha/Hora", "observaciones": "Obs.",
                            "estado": st.column_config.SelectboxColumn("Estado", options=["Pendiente", "Evaluación", "En curso", "Completado", "Cancelado"])
                        }, key="ed_adiest"
                    )
                    if st.button("💾 Guardar Cambios en Sesiones", type="primary"):
                        for _, r in ed_a[ed_a["Borrar"] == True].iterrows():
                            if pd.notna(r['id']): client.table("servicios_adiestramiento").delete().eq("id", r['id']).execute()
                        for _, r in ed_a[ed_a["Borrar"] == False].iterrows():
                            if pd.notna(r['id']):
                                client.table("servicios_adiestramiento").update({"estado": str(r['estado'])}).eq("id", r['id']).execute()
                        st.rerun()
                else: st.info("No hay sesiones de adiestramiento programadas.")
            except: st.info("Ejecuta el código SQL para habilitar la tabla de Adiestramiento.")

    with t_domicilio:
        d_reco, d_rep = st.tabs(["🚐 Recogida para Peluquería", "🛵 Reparto a Domicilio (Pedidos)"])
        
        with d_reco:
            col_r1, col_r2 = st.columns([1, 2.2])
            with col_r1:
                st.markdown("#### 🚐 Solicitar Recogida")
                with st.form("form_recogida", clear_on_submit=True):
                    sel_cli_r = st.selectbox("1. Seleccionar Cliente:", opc_cli, key=f"sr_sel_{st.session_state.llave_srv_reco}")
                    st.markdown("<p style='font-size:12px; color:gray; margin:0;'>O rellénalo a mano:</p>", unsafe_allow_html=True)
                    r_cli_man = st.text_input("Nombre Dueño")
                    r_tel_man = st.text_input("Teléfono")
                    r_masc_man = st.text_input("Nombre Mascota *")
                    r_dir_man = st.text_input("Dirección de Recogida")
                    
                    st.markdown("---")
                    r_fecha = st.text_input("2. Día y Hora de Recogida *", placeholder="Ej: Martes a las 11:30")
                    r_obs = st.text_area("3. Observaciones / Instrucciones especiales")
                    
                    if st.form_submit_button("Guardar Recogida", type="primary", use_container_width=True):
                        final_cli = r_cli_man
                        final_tel = r_tel_man
                        final_dir = r_dir_man
                        if "no registrado" not in sel_cli_r:
                            final_cli = mapa_cli[sel_cli_r]['nombre_dueno']
                            final_tel = mapa_cli[sel_cli_r].get('telefono','')
                            if not final_dir: final_dir = mapa_cli[sel_cli_r].get('direccion', '')
                            
                        if final_cli and r_masc_man and r_fecha:
                            try:
                                client.table("servicios_recogida").insert({
                                    "cliente": final_cli, "mascota": r_masc_man, "telefono": final_tel, "direccion": final_dir,
                                    "fecha_recogida": r_fecha, "observaciones": r_obs, "estado": "Pendiente"
                                }).execute()
                                st.session_state.llave_srv_reco += 1
                                st.success("Recogida registrada."); time.sleep(0.5); st.rerun()
                            except: st.error("⚠️ Crea la tabla 'servicios_recogida' en Supabase.")
                        else: st.warning("Cliente, Mascota y Día/Hora son obligatorios.")
            with col_r2:
                st.markdown("#### 📌 Recogidas Programadas")
                try:
                    res_r = client.table("servicios_recogida").select("*").order("created_at", desc=True).execute()
                    if res_r.data:
                        df_r = pd.DataFrame(res_r.data)
                        if 'WhatsApp' not in df_r.columns: df_r['WhatsApp'] = None
                        
                        for idx, row in df_r.iterrows():
                            tel_enc = str(row.get('telefono', ''))
                            tel_limpio = ''.join(filter(str.isdigit, tel_enc))
                            if tel_limpio:
                                if len(tel_limpio) == 9 and not tel_limpio.startswith('34'): tel_limpio = '34' + tel_limpio
                                mensaje_r = f"¡Hola {row['cliente']}! 🐾 Vamos de camino a recoger a {row['mascota']} en {row.get('direccion', 'su domicilio')} para su sesión de peluquería en Animalarium. ¡Nos vemos en unos minutos! 🚐"
                                df_r.at[idx, 'WhatsApp'] = f"https://wa.me/{tel_limpio}?text={urllib.parse.quote(mensaje_r)}"
                                
                        df_r_vista = df_r[['id', 'cliente', 'mascota', 'telefono', 'direccion', 'fecha_recogida', 'estado', 'WhatsApp']].copy()
                        df_r_vista.insert(0, "Borrar", False)
                        ed_r = st.data_editor(
                            df_r_vista, hide_index=True, use_container_width=True, num_rows="dynamic",
                            column_config={
                                "Borrar": st.column_config.CheckboxColumn("🗑️", width="small"),
                                "id": None, "cliente": "Cliente", "mascota": "Mascota", "telefono": "Tel.",
                                "direccion": "Dirección", "fecha_recogida": "Hora Recogida",
                                "estado": st.column_config.SelectboxColumn("Estado", options=["Pendiente", "En camino", "Recogido", "Entregado vuelta", "Cancelado"]),
                                "WhatsApp": st.column_config.LinkColumn("📱 Avisar", display_text="💬 WhatsApp")
                            }, key="ed_reco"
                        )
                        if st.button("💾 Guardar Cambios en Recogidas", type="primary"):
                            for _, r in ed_r[ed_r["Borrar"] == True].iterrows():
                                if pd.notna(r['id']): client.table("servicios_recogida").delete().eq("id", r['id']).execute()
                            for _, r in ed_r[ed_r["Borrar"] == False].iterrows():
                                if pd.notna(r['id']):
                                    client.table("servicios_recogida").update({"estado": str(r['estado'])}).eq("id", r['id']).execute()
                            st.rerun()
                    else: st.info("No hay recogidas programadas.")
                except: st.info("Ejecuta el código SQL para habilitar la tabla de Recogidas.")

        with d_rep:
            col_d1, col_d2 = st.columns([1, 2.2])
            with col_d1:
                st.markdown("#### 🛵 Registrar Pedido a Domicilio")
                with st.form("n_domicilio", clear_on_submit=True):
                    sel_cli_dom = st.selectbox("1. Buscar Cliente:", opc_cli, key=f"nd_sel_{st.session_state.llave_srv_dom}")
                    
                    st.markdown("<p style='font-size:12px; color:gray; margin:0;'>O rellenar si no está registrado/modificar:</p>", unsafe_allow_html=True)
                    c_nom_d, c_tel_d = st.columns(2)
                    with c_nom_d: d_cli_man = st.text_input("Nombre", key=f"nd_nom_{st.session_state.llave_srv_dom}")
                    with c_tel_d: d_tel_man = st.text_input("Teléfono", key=f"nd_tel_{st.session_state.llave_srv_dom}")
                    d_dir_man = st.text_input("Dirección de entrega", key=f"nd_dir_{st.session_state.llave_srv_dom}")
                    
                    st.markdown("---")
                    d_prod = st.text_area("2. Detalle del pedido *", key=f"nd_prod_{st.session_state.llave_srv_dom}")
                    
                    if st.form_submit_button("Guardar Pedido", type="primary", use_container_width=True):
                        final_cli = d_cli_man
                        final_tel = d_tel_man
                        final_dir = d_dir_man
                        
                        if "no registrado" not in sel_cli_dom:
                            final_cli = mapa_cli[sel_cli_dom]['nombre_dueno']
                            final_tel = mapa_cli[sel_cli_dom].get('telefono','')
                            if not final_dir: final_dir = mapa_cli[sel_cli_dom].get('direccion', '')
                                
                        if final_cli and d_prod:
                            try:
                                client.table("pedidos_domicilio").insert({
                                    "nombre_cliente": final_cli, "telefono": final_tel, "direccion": final_dir,
                                    "detalle_pedido": d_prod, "estado": "Pendiente"
                                }).execute()
                                st.session_state.llave_srv_dom += 1
                                st.success("Pedido a domicilio guardado."); time.sleep(0.5); st.rerun()
                            except Exception as e:
                                st.error("⚠️ Error: Asegúrate de haber ejecutado el SQL para crear la tabla 'pedidos_domicilio' en Supabase.")
                        else:
                            st.warning("Debes indicar un cliente y el detalle del pedido.")
            
            with col_d2:
                st.markdown("#### 📌 Pedidos en Curso")
                try:
                    res_d = client.table("pedidos_domicilio").select("id, created_at, nombre_cliente, telefono, direccion, detalle_pedido, estado").order("created_at", desc=True).execute()
                    if res_d.data:
                        df_d = pd.DataFrame(res_d.data)
                        dt_d = pd.to_datetime(df_d['created_at'], utc=True, format='mixed', errors='coerce').fillna(pd.Timestamp('today', tz='UTC'))
                        if dt_d.dt.tz is None: dt_d = dt_d.dt.tz_localize('UTC')
                        df_d['Fecha'] = dt_d.dt.tz_convert('Atlantic/Canary').dt.strftime('%d/%m/%Y')
                        
                        if 'WhatsApp' not in df_d.columns: df_d['WhatsApp'] = None
                        
                        for idx, row in df_d.iterrows():
                            tel_enc = str(row.get('telefono', ''))
                            tel_limpio = ''.join(filter(str.isdigit, tel_enc))
                            if tel_limpio:
                                if len(tel_limpio) == 9 and not tel_limpio.startswith('34'): tel_limpio = '34' + tel_limpio
                                mensaje_dom = f"¡Hola {row['nombre_cliente']}! 🐾 Te escribimos desde Animalarium. Tu pedido a domicilio ya está en camino a la dirección: {row['direccion']}. ¡Un saludo!"
                                df_d.at[idx, 'WhatsApp'] = f"https://wa.me/{tel_limpio}?text={urllib.parse.quote(mensaje_dom)}"
                                
                        df_d_vista = df_d[['id', 'Fecha', 'nombre_cliente', 'telefono', 'direccion', 'detalle_pedido', 'estado', 'WhatsApp']]
                        df_d_vista.insert(0, "Borrar", False)
                        ed_d = st.data_editor(
                            df_d_vista, hide_index=True, use_container_width=True, num_rows="dynamic", height=300, key="ed_tabla_domicilio",
                            column_config={
                                "Borrar": st.column_config.CheckboxColumn("🗑️", width="small"),
                                "id": None, "Fecha": "Día", "nombre_cliente": "Cliente", "telefono": "Tel.",
                                "direccion": "Dirección", "detalle_pedido": "Pedido",
                                "estado": st.column_config.SelectboxColumn("Estado", options=["Pendiente", "En Reparto", "Entregado", "Cancelado"]),
                                "WhatsApp": st.column_config.LinkColumn("📱 Avisar", display_text="💬 WhatsApp")
                            }
                        )
                        if st.button("💾 Guardar Cambios en Pedidos", type="primary"):
                            for _, r in ed_d[ed_d["Borrar"] == True].iterrows():
                                if pd.notna(r['id']): client.table("pedidos_domicilio").delete().eq("id", r['id']).execute()
                            for _, r in ed_d[ed_d["Borrar"] == False].iterrows():
                                if pd.notna(r['id']):
                                    client.table("pedidos_domicilio").update({"estado": str(r['estado'])}).eq("id", r['id']).execute()
                            st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                            st.rerun()
                    else: st.info("No hay pedidos a domicilio activos.")
                except Exception as e: st.warning("⚠️ Debes crear la tabla 'pedidos_domicilio' en Supabase para que funcione este panel.")