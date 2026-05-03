import streamlit as st
import pandas as pd
import time
from datetime import date
import urllib.parse

def render_pestana_crm(client):
    st.markdown("<h3 style='margin-bottom: 5px;'>👥 Gestión de Clientes y Mascotas</h3>", unsafe_allow_html=True)
    col_c1, col_c2 = st.columns([1.2, 2.5])

    with col_c1:
        st.markdown("#### 👤 Nuevo Cliente")
        with st.form("nuevo_cliente", clear_on_submit=True):
            c_nom = st.text_input("Nombre y Apellidos *")
            c_tel = st.text_input("Teléfono")
            c_ema = st.text_input("Email")
            c_nac = st.date_input("F. Nacimiento", value=None)
            c_rgpd = st.checkbox("📝 Acepta LOPD/RGPD (Envío info y promos)", value=True)
            
            st.markdown("<hr style='margin: 5px 0px; border: none; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)
            st.markdown("<p style='margin: 0; font-size: 13px; color: gray;'>🐾 Añadir mascota (Deja en blanco si es solo cliente de tienda)</p>", unsafe_allow_html=True)
            
            m_nom = st.text_input("Nombre de la mascota")
            cm1, cm2, cm3 = st.columns(3)
            with cm1: m_esp = st.selectbox("Especie", ["", "Perro", "Gato", "Ave", "Roedor", "Reptil", "Otro"])
            with cm2: m_raz = st.text_input("Raza")
            with cm3: m_nac = st.date_input("Nac. Mascota", value=None)
            m_obs = st.text_input("Observaciones (Alergias, carácter...)")

            if st.form_submit_button("💾 Guardar Ficha", type="primary", use_container_width=True):
                if c_nom:
                    res_cli = client.table("clientes").insert({
                        "nombre_dueno": c_nom, "telefono": c_tel, "email": c_ema, "fecha_nacimiento": str(c_nac) if c_nac else "",
                        "rgpd_consent": c_rgpd, "puntos": 0
                    }).execute()

                    if res_cli.data and m_nom:
                        cli_id = res_cli.data[0]['id']
                        client.table("mascotas").insert({
                            "cliente_id": cli_id, "nombre": m_nom, "especie": m_esp, 
                            "raza": m_raz, "observaciones": m_obs, "fecha_nacimiento": str(m_nac) if m_nac else ""
                        }).execute()

                    st.success("Cliente guardado correctamente"); time.sleep(0.5); st.rerun()
                else:
                    st.warning("El nombre del dueño es obligatorio.")

    with col_c2:
        # Función para calcular la edad visualmente
        def calcular_edad(fecha_str):
            try:
                nac = pd.to_datetime(fecha_str)
                hoy = pd.to_datetime("today")
                anios = hoy.year - nac.year - ((hoy.month, hoy.day) < (nac.month, nac.day))
                if anios == 0:
                    meses = hoy.month - nac.month - ((hoy.day) < (nac.day))
                    if meses < 0: meses += 12
                    return f"{meses} meses"
                return f"{anios} años"
            except: return ""

        def calcular_duracion_media(historial):
            """Calcula la duración media de los servicios a partir del historial JSON."""
            if not isinstance(historial, list) or not historial:
                return "N/A"
            
            duraciones = [t['Duración (min)'] for t in historial if isinstance(t, dict) and isinstance(t.get('Duración (min)'), (int, float))]
            
            if not duraciones:
                return "N/A"
                
            media = sum(duraciones) / len(duraciones)
            return f"{int(media)} min"

        def mostrar_ficha_clinica(m_id, m_nombre, m_data, prefix):
            """Renderiza la ficha clínica, el historial y el sistema inteligente de reservas."""
            st.markdown(f"#### 📖 Ficha e Historial Clínico/Peluquería: **{m_nombre}**")
            
            historial = m_data.get('historial_trabajos')
            if not isinstance(historial, list): historial = []
            
            df_hist = pd.DataFrame(historial)
            for col in ["Fecha", "Trabajo / Servicio", "Duración (min)", "Importe (€)"]:
                if col not in df_hist.columns: df_hist[col] = None
                
            df_hist = df_hist[["Fecha", "Trabajo / Servicio", "Duración (min)", "Importe (€)"]]
            
            df_hist["Fecha"] = pd.to_datetime(df_hist["Fecha"], format="%d/%m/%Y", errors="coerce")
            df_hist["Duración (min)"] = pd.to_numeric(df_hist["Duración (min)"], errors="coerce")
            df_hist["Importe (€)"] = pd.to_numeric(df_hist["Importe (€)"], errors="coerce")
            
            ed_hist = st.data_editor(
                df_hist, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"ed_hist_{prefix}_{m_id}",
                column_config={
                    "Fecha": st.column_config.DateColumn("Fecha (D/M/A)", format="DD/MM/YYYY"),
                    "Trabajo / Servicio": st.column_config.TextColumn("Servicio Realizado"),
                    "Duración (min)": st.column_config.NumberColumn("Duración (min)", min_value=0, step=5),
                    "Importe (€)": st.column_config.NumberColumn("Importe Cobrado (€)", format="%.2f", min_value=0.0)
                }
            )
            
            if st.button(f"💾 Guardar Historial de {m_nombre}", type="primary", key=f"btn_hist_{prefix}_{m_id}"):
                df_save = ed_hist.copy()
                df_save['Fecha'] = pd.to_datetime(df_save['Fecha']).dt.strftime('%d/%m/%Y').fillna("")
                df_save = df_save.fillna("")
                client.table("mascotas").update({"historial_trabajos": df_save.to_dict(orient='records')}).eq("id", m_id).execute()
                st.success("Historial actualizado correctamente."); time.sleep(0.5); st.rerun()
                
            st.markdown("---")
            st.markdown(f"#### 📅 Agendar Cita Inteligente para **{m_nombre}**")
            st.markdown("<p style='color: gray; font-size: 13px;'>El sistema calcula automáticamente los huecos libres (09:00 a 21:00) para la fecha y duración seleccionadas.</p>", unsafe_allow_html=True)
            
            c_cal1, c_cal2 = st.columns([1, 1])
            with c_cal1: f_fecha = st.date_input("1. Selecciona la fecha de la cita:", value=date.today(), key=f"fcita_{prefix}_{m_id}")
            with c_cal2: f_dur = st.number_input("2. Duración del servicio (minutos)", min_value=5, max_value=300, value=60, step=5, key=f"fdur_{prefix}_{m_id}")
            
            res_citas = client.table("citas").select("fecha_hora, duracion_minutos").gte("fecha_hora", f"{f_fecha} 00:00:00").lte("fecha_hora", f"{f_fecha} 23:59:59").execute()
            citas_dia = res_citas.data if res_citas.data else []
            
            # --- CÁLCULO DE TRAMOS LIBRES CONTINUOS ---
            bloques_libres = []
            hora_actual = pd.to_datetime(f"{f_fecha} 09:00")
            fin_jornada = pd.to_datetime(f"{f_fecha} 21:00")
            
            citas_ordenadas = []
            for c in citas_dia:
                dt_ini = pd.to_datetime(c['fecha_hora'])
                dt_fin = dt_ini + pd.Timedelta(minutes=c.get('duracion_minutos') or 60)
                citas_ordenadas.append({"ini": dt_ini, "fin": dt_fin})
            citas_ordenadas.sort(key=lambda x: x["ini"])
            
            for c in citas_ordenadas:
                if hora_actual < c["ini"]:
                    if (c["ini"] - hora_actual).total_seconds() / 60 >= f_dur:
                        bloques_libres.append(f"{hora_actual.strftime('%H:%M')} a {c['ini'].strftime('%H:%M')}")
                hora_actual = max(hora_actual, c["fin"])
                
            if hora_actual < fin_jornada and (fin_jornada - hora_actual).total_seconds() / 60 >= f_dur:
                bloques_libres.append(f"{hora_actual.strftime('%H:%M')} a {fin_jornada.strftime('%H:%M')}")
                
            if bloques_libres:
                st.success(f"🟢 **Tramos libres para {f_dur} min:** " + " | ".join(bloques_libres))
            else:
                st.error(f"🔴 No hay tramos continuos de {f_dur} minutos libres en este día.")

            # --- CÁLCULO DE HUECOS SELECCIONABLES (Cada 5 min) ---
            huecos = []
            for h in range(9, 21):
                for m in range(0, 60, 5):
                    dt_ini = pd.to_datetime(f"{f_fecha} {h:02d}:{m:02d}")
                    dt_fin = dt_ini + pd.Timedelta(minutes=f_dur)
                    if dt_fin > pd.to_datetime(f"{f_fecha} 21:00"): continue
                    
                    solapa = False
                    for c in citas_dia:
                        c_ini = pd.to_datetime(c['fecha_hora'])
                        c_fin = c_ini + pd.Timedelta(minutes=c.get('duracion_minutos') or 60)
                        if dt_ini < c_fin and dt_fin > c_ini:
                            solapa = True; break
                    if not solapa: huecos.append(f"{h:02d}:{m:02d}")
                    
            if not huecos:
                st.warning("⚠️ No hay horas de inicio disponibles este día para esa duración.")
            else:
                with st.form(f"form_cita_{prefix}_{m_id}", border=True):
                    fc_1, fc_2 = st.columns([1, 2])
                    with fc_1: f_hora = st.selectbox("3. Hora de inicio:", huecos)
                    with fc_2: f_serv = st.selectbox("4. Servicio:", ["Peluquería (Baño y Corte)", "Peluquería (Solo Baño)", "Corte de Uñas", "Revisión Veterinaria", "Otro"])
                    if st.form_submit_button("➕ Confirmar Cita", type="primary", use_container_width=True):
                        client.table("citas").insert({"mascotas_id": m_id, "fecha_hora": f"{f_fecha} {f_hora}", "servicio": f_serv, "duracion_minutos": int(f_dur)}).execute()
                        st.success("¡Cita reservada con éxito!"); time.sleep(1); st.rerun()

        sub_cli, sub_masc, sub_alertas, sub_encargos = st.tabs(["👤 Directorio de Clientes", "🐾 Fichas de Mascotas", "🔔 Alertas y Recordatorios", "🛍️ Encargos de Clientes"])
        
        with sub_cli:
            res_clientes = client.table("clientes").select("*, mascotas(*)").order("created_at", desc=True).execute()
            if res_clientes.data:
                df_cli = pd.DataFrame(res_clientes.data)
                
                # --- MÉTRICAS DE CLIENTES ---
                total_clientes = len(df_cli)
                clientes_con_mascota = sum(1 for c in res_clientes.data if c.get('mascotas') and len(c['mascotas']) > 0)
                clientes_sin_mascota = total_clientes - clientes_con_mascota
                
                c_met1, c_met2, c_met3 = st.columns(3)
                with c_met1: st.metric("👥 Total Clientes", total_clientes)
                with c_met2: st.metric("🐾 Con Mascota", clientes_con_mascota)
                with c_met3: st.metric("🛍️ Solo Tienda", clientes_sin_mascota)
                st.markdown("<hr style='margin: 5px 0px 15px 0px; border: none; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

                b_cli = st.text_input("🔍 Buscar cliente (Nombre o Teléfono):", placeholder="Escribe para filtrar...", key="b_cli").strip().lower()
                
                if 'fecha_nacimiento' not in df_cli.columns: df_cli['fecha_nacimiento'] = ""
                df_cli['Tipo Cliente'] = df_cli['mascotas'].apply(lambda x: "🐾 Con mascota" if isinstance(x, list) and len(x) > 0 else "🛍️ Solo tienda")
                df_cli_vista = df_cli[['id', 'nombre_dueno', 'telefono', 'email', 'fecha_nacimiento', 'Tipo Cliente']].copy()
                
                if b_cli:
                    df_cli_vista = df_cli_vista[
                        df_cli_vista['nombre_dueno'].str.lower().str.contains(b_cli, na=False) |
                        df_cli_vista['telefono'].astype(str).str.contains(b_cli, na=False)
                    ]
                
                # Aseguramos columnas nuevas por si acaban de ejecutarse en SQL
                if 'rgpd_consent' not in df_cli.columns: df_cli['rgpd_consent'] = True
                if 'puntos' not in df_cli.columns: df_cli['puntos'] = 0
                
                df_cli_vista['RGPD'] = df_cli['rgpd_consent']
                df_cli_vista['Puntos'] = df_cli['puntos']

                df_cli_vista.insert(0, "Ver", False)
                st.markdown("💡 *Marca la casilla **'👁️ Ver'** para abrir la ficha del cliente y ver sus mascotas.*")
                
                ed_cli = st.data_editor(
                    df_cli_vista,
                    column_config={
                        "Ver": st.column_config.CheckboxColumn("👁️ Ver", default=False), 
                        "id": None, "nombre_dueno": "Nombre Cliente", "telefono": "Tel.", 
                        "email": "Email", "fecha_nacimiento": "F. Nac",
                        "RGPD": st.column_config.CheckboxColumn("LOPD"),
                        "Puntos": st.column_config.NumberColumn("🌟 Ptos"),
                        "Tipo Cliente": st.column_config.TextColumn("Perfil", disabled=True)
                    },
                    use_container_width=True, hide_index=True, num_rows="dynamic", key="ed_clientes", height=250
                )
                if st.button("💾 Guardar Cambios en Clientes", type="primary"):
                    ed_cli_clean = ed_cli.drop(columns=["Ver", "Tipo Cliente"])
                    ids_actuales = ed_cli_clean['id'].dropna().tolist()
                    ids_orig = df_cli_vista['id'].tolist()
                    for id_b in [i for i in ids_orig if i not in ids_actuales]: client.table("clientes").delete().eq("id", id_b).execute()
                    
                    for _, row in ed_cli_clean.iterrows():
                        if pd.notna(row['id']):
                            client.table("clientes").update({
                                "nombre_dueno": str(row['nombre_dueno']), "telefono": str(row['telefono']),
                                "email": str(row['email']), "fecha_nacimiento": str(row['fecha_nacimiento']),
                                "rgpd_consent": bool(row.get('RGPD', True)), "puntos": int(row.get('Puntos', 0))
                            }).eq("id", row['id']).execute()
                    st.success("Directorio de clientes actualizado."); time.sleep(0.5); st.rerun()
                    
                st.markdown("---")
                
                # --- FICHA COMPLETA DEL DUEÑO Y SUS MASCOTAS ---
                filas_c_marcadas = ed_cli[ed_cli["Ver"] == True]
                if not filas_c_marcadas.empty:
                    c_id = filas_c_marcadas.iloc[0]['id']
                    c_data = df_cli[df_cli['id'] == c_id].iloc[0]
                    c_nombre = c_data['nombre_dueno']
                    
                    st.markdown(f"#### 📖 Ficha de Cliente: **{c_nombre}**")
                    
                    mascotas_lista = c_data.get('mascotas', [])
                    if isinstance(mascotas_lista, list) and len(mascotas_lista) > 0:
                        df_mc = pd.DataFrame(mascotas_lista)
                        if 'fecha_nacimiento' not in df_mc.columns: df_mc['fecha_nacimiento'] = ""
                        df_mc['Edad'] = df_mc['fecha_nacimiento'].apply(calcular_edad)
                        if 'historial_trabajos' not in df_mc.columns: df_mc['historial_trabajos'] = [[] for _ in range(len(df_mc))]
                        df_mc['Duración Media'] = df_mc['historial_trabajos'].apply(calcular_duracion_media)
                        
                        cols_ok = ['id', 'nombre', 'especie', 'raza', 'fecha_nacimiento', 'Edad', 'Duración Media', 'observaciones']
                        for col in cols_ok:
                            if col not in df_mc.columns: df_mc[col] = ""
                            
                        df_mc_show = df_mc[cols_ok].rename(columns={
                            "nombre": "Nombre Mascota", "especie": "Especie", "raza": "Raza", 
                            "fecha_nacimiento": "F. Nacimiento", "observaciones": "Observaciones"
                        })
                        
                        df_mc_show.insert(0, "Ver Ficha", False)
                        st.markdown("💡 *Edita los datos directamente. Para eliminar, selecciona la fila y pulsa 'Supr'. Marca **'👁️ Ver Ficha'** para abrir el historial y agendar.*")
                        ed_mc = st.data_editor(
                            df_mc_show, use_container_width=True, hide_index=True, num_rows="dynamic", key=f"ed_mc_{c_id}",
                            column_config={
                                "Ver Ficha": st.column_config.CheckboxColumn("👁️ Ver Ficha", default=False),
                                "id": None, "Edad": st.column_config.TextColumn(disabled=True), "Duración Media": st.column_config.TextColumn(disabled=True)
                            }
                        )
                        
                        if st.button("💾 Guardar Cambios en Mascotas de esta Familia", key=f"btn_save_mc_{c_id}"):
                            # 1. Detectar si el usuario ha borrado filas con la papelera o Supr
                            ids_actuales = ed_mc['id'].dropna().tolist()
                            ids_orig = df_mc_show['id'].dropna().tolist()
                            ids_a_borrar = [i for i in ids_orig if i not in ids_actuales]
                            for id_del in ids_a_borrar:
                                client.table("mascotas").delete().eq("id", id_del).execute()
                                
                            # 2. Actualizar mascotas existentes o insertar las nuevas
                            for _, ru in ed_mc.iterrows():
                                if pd.notna(ru['id']):
                                    client.table("mascotas").update({
                                        "nombre": str(ru['Nombre Mascota']), "especie": str(ru['Especie']),
                                        "raza": str(ru['Raza']), "fecha_nacimiento": str(ru['F. Nacimiento']),
                                        "observaciones": str(ru['Observaciones'])
                                    }).eq("id", ru['id']).execute()
                                else:
                                    if pd.notna(ru['Nombre Mascota']) and str(ru['Nombre Mascota']).strip():
                                        client.table("mascotas").insert({
                                            "cliente_id": c_id, "nombre": str(ru['Nombre Mascota']),
                                            "especie": str(ru['Especie']) if pd.notna(ru['Especie']) else "",
                                            "raza": str(ru['Raza']) if pd.notna(ru['Raza']) else "",
                                            "fecha_nacimiento": str(ru['F. Nacimiento']) if pd.notna(ru['F. Nacimiento']) else "",
                                            "observaciones": str(ru['Observaciones']) if pd.notna(ru['Observaciones']) else ""
                                        }).execute()
                            st.success("Datos de la familia actualizados."); time.sleep(0.5); st.rerun()
                            
                        filas_ver_mc = ed_mc[ed_mc["Ver Ficha"] == True]
                        if not filas_ver_mc.empty:
                            st.markdown("---")
                            m_id_sel = filas_ver_mc.iloc[0]['id']
                            m_data_sel = next(item for item in mascotas_lista if item["id"] == m_id_sel)
                            mostrar_ficha_clinica(m_id_sel, m_data_sel['nombre'], m_data_sel, prefix="fam")
                    else:
                        st.info("Este cliente no tiene mascotas registradas.")
                        
            else: st.info("No hay clientes registrados.")

            st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

            st.markdown("#### ➕ Añadir otra mascota a un cliente")
            dict_cli = {f"{c['nombre_dueno']} ({c['telefono']})": c['id'] for c in res_clientes.data} if res_clientes.data else {}
            
            with st.form("nueva_mascota_extra", clear_on_submit=True, border=False):
                sel_cli = st.selectbox("Selecciona el cliente:", list(dict_cli.keys()))
                c_m1, c_m2, c_m3 = st.columns([1.5, 1, 1])
                with c_m1: nx_nom = st.text_input("Nombre mascota", key="nx_nom")
                with c_m2: nx_esp = st.selectbox("Especie", ["Perro", "Gato", "Ave", "Roedor", "Otro"], key="nx_esp")
                with c_m3: nx_raz = st.text_input("Raza", key="nx_raz")
                
                if st.form_submit_button("Añadir Mascota", use_container_width=True):
                    if nx_nom and sel_cli:
                        client.table("mascotas").insert({
                            "cliente_id": dict_cli[sel_cli], "nombre": nx_nom, "especie": nx_esp, "raza": nx_raz
                        }).execute()
                        st.success("Mascota añadida a la familia"); time.sleep(0.5); st.rerun()
                    else:
                        st.warning("Falta el nombre de la mascota.")
                        
        with sub_masc:
            res_mascotas = client.table("mascotas").select("*, clientes(nombre_dueno)").order("id", desc=True).execute()
            if res_mascotas.data:
                df_m = pd.DataFrame(res_mascotas.data)
                
                b_masc = st.text_input("🔍 Buscar mascota por nombre:", placeholder="Escribe para filtrar...", key="b_masc").strip().lower()
                
                df_m['Dueño'] = df_m['clientes'].apply(lambda x: x.get('nombre_dueno', '') if isinstance(x, dict) else '')
                if 'fecha_nacimiento' not in df_m.columns: df_m['fecha_nacimiento'] = ""
                df_m['Edad'] = df_m['fecha_nacimiento'].apply(calcular_edad)
                if 'historial_trabajos' not in df_m.columns:
                    df_m['historial_trabajos'] = [[] for _ in range(len(df_m))]
                df_m['Duración Media'] = df_m['historial_trabajos'].apply(calcular_duracion_media)
                
                df_m_vista = df_m[['id', 'nombre', 'Dueño', 'especie', 'raza', 'fecha_nacimiento', 'Edad', 'Duración Media', 'observaciones']].copy()
                
                if b_masc:
                    df_m_vista = df_m_vista[df_m_vista['nombre'].str.lower().str.contains(b_masc, na=False)]
                    
                df_m_vista.insert(0, "Ver", False)
                
                st.markdown("💡 *Marca la casilla **'👁️ Ver'** para abrir la ficha completa y el historial de la mascota.*")
                
                ed_m = st.data_editor(
                    df_m_vista,
                    column_config={"Ver": st.column_config.CheckboxColumn("👁️ Ver", default=False), "id": None, "Dueño": st.column_config.TextColumn(disabled=True), "Edad": st.column_config.TextColumn(disabled=True), "nombre": "Mascota", "fecha_nacimiento": "F. Nacimiento", "observaciones": "Observaciones Generales", "Duración Media": st.column_config.TextColumn("T. Medio", disabled=True, help="Tiempo medio de servicio calculado del historial.")},
                    use_container_width=True, hide_index=True, num_rows="dynamic", key="ed_mascotas", height=400
                )
                if st.button("💾 Guardar Cambios en Mascotas", type="primary"):
                    ed_m_clean = ed_m.drop(columns=["Ver"])
                    ids_actuales = ed_m_clean['id'].dropna().tolist()
                    ids_orig = df_m_vista['id'].tolist()
                    for id_b in [i for i in ids_orig if i not in ids_actuales]: client.table("mascotas").delete().eq("id", id_b).execute()
                    
                    for _, row in ed_m_clean.iterrows():
                        if pd.notna(row['id']):
                            client.table("mascotas").update({
                                "nombre": str(row['nombre']), "especie": str(row['especie']),
                                "raza": str(row['raza']), "fecha_nacimiento": str(row['fecha_nacimiento']),
                                "observaciones": str(row['observaciones'])
                            }).eq("id", row['id']).execute()
                    st.success("Fichas de mascotas actualizadas."); time.sleep(0.5); st.rerun()
                    
                st.markdown("---")
                
                # --- FICHA COMPLETA E HISTORIAL DE LA MASCOTA ---
                filas_m_marcadas = ed_m[ed_m["Ver"] == True]
                if not filas_m_marcadas.empty:
                    m_id = filas_m_marcadas.iloc[0]['id']
                    m_data = df_m[df_m['id'] == m_id].iloc[0]
                    m_nombre = m_data['nombre']
                    mostrar_ficha_clinica(m_id, m_nombre, m_data, prefix="ind")
            else: st.info("No hay mascotas registradas.")

        with sub_alertas:
            st.markdown("#### 🔔 Alertas de Mantenimiento Inteligentes")
            st.markdown("<p style='color:gray; font-size:14px;'>El sistema escanea el historial de las mascotas y te avisa de las que llevan tiempo sin venir, generándote un enlace directo para enviarles un WhatsApp pre-escrito con un solo toque.</p>", unsafe_allow_html=True)
            
            c_al1, c_al2 = st.columns([1, 2])
            with c_al1:
                dias_aviso = st.slider("Mostrar mascotas que no hayan venido en más de (días):", min_value=15, max_value=180, value=45, step=5)
            
            res_m_alertas = client.table("mascotas").select("*, clientes(nombre_dueno, telefono)").execute()
            
            if res_m_alertas.data:
                alertas = []
                hoy_dt = pd.to_datetime('today')
                
                for m in res_m_alertas.data:
                    hist = m.get('historial_trabajos', [])
                    if isinstance(hist, list) and len(hist) > 0:
                        try:
                            fechas = [pd.to_datetime(h['Fecha'], format='%d/%m/%Y', errors='coerce') for h in hist if h.get('Fecha')]
                            fechas = [f for f in fechas if pd.notna(f)]
                            if fechas:
                                ultima_visita = max(fechas)
                                dias_transcurridos = (hoy_dt - ultima_visita).days
                                
                                if dias_transcurridos >= dias_aviso:
                                    dueno = m['clientes']['nombre_dueno'] if m.get('clientes') else 'Dueño'
                                    telefono = m['clientes']['telefono'] if m.get('clientes') else ''
                                    
                                    # Preparar el número para WhatsApp (+34 España)
                                    tel_limpio = ''.join(filter(str.isdigit, str(telefono)))
                                    if tel_limpio and len(tel_limpio) == 9 and not tel_limpio.startswith('34'):
                                        tel_limpio = '34' + tel_limpio
                                        
                                    # Mensaje de marketing amistoso
                                    mensaje = f"¡Hola {dueno}! 🐾 Soy Raquel de Animalarium. Te escribo porque he visto en la ficha de {m['nombre']} que ya le toca su sesión de mantenimiento (hace {dias_transcurridos} días de su última visita). ¿Te gustaría que le busquemos un huequito en la agenda para estos días? ¡Un saludo! 🐶✂️"
                                    url_wa = f"https://wa.me/{tel_limpio}?text={urllib.parse.quote(mensaje)}" if tel_limpio else None
                                    
                                    alertas.append({
                                        "Mascota": m['nombre'], "Dueño": dueno,
                                        "Última Visita": ultima_visita.strftime('%d/%m/%Y'),
                                        "Días Sin Venir": dias_transcurridos, "WhatsApp": url_wa
                                    })
                        except Exception as e: pass
                
                if alertas:
                    df_alertas = pd.DataFrame(alertas).sort_values(by="Días Sin Venir", ascending=False)
                    st.warning(f"⚠️ Tienes **{len(alertas)}** clientes pendientes de contactar para mantenimiento.")
                    st.dataframe(df_alertas, use_container_width=True, hide_index=True, column_config={"WhatsApp": st.column_config.LinkColumn("📱 Acción Automática", display_text="💬 Enviar WhatsApp")})
                else:
                    st.success("✨ ¡Genial! Tienes la agenda al día. Ninguna mascota supera los días de alerta.")

        with sub_encargos:
            col_en1, col_en2 = st.columns([1, 2])
            with col_en1:
                st.markdown("#### 📝 Registrar Encargo")
                with st.form("n_encargo", clear_on_submit=True):
                    opc_cli_enc = ["👤 Cliente no registrado (Escribir a mano)"]
                    if res_clientes.data:
                        opc_cli_enc += [f"{c['nombre_dueno']} | {c['telefono']}" for c in res_clientes.data]
                    
                    sel_cli_enc = st.selectbox("1. Buscar Cliente:", opc_cli_enc)
                    
                    st.markdown("<p style='font-size:12px; color:gray; margin:0;'>O rellenar si no está registrado:</p>", unsafe_allow_html=True)
                    c_nom_man, c_tel_man = st.columns(2)
                    with c_nom_man: e_cli_man = st.text_input("Nombre", key="e_cli_man")
                    with c_tel_man: e_tel_man = st.text_input("Teléfono", key="e_tel_man")
                    
                    st.markdown("---")
                    e_prod = st.text_input("2. Producto que pide *")
                    e_cant = st.number_input("3. Cantidad *", min_value=1, value=1)
                    e_obs = st.text_area("4. Observaciones")
                    
                    if st.form_submit_button("Guardar Encargo", type="primary", use_container_width=True):
                        # Determinar cliente
                        if "Cliente no registrado" not in sel_cli_enc:
                            final_cli = sel_cli_enc.split(" | ")[0]
                            final_tel = sel_cli_enc.split(" | ")[1] if len(sel_cli_enc.split(" | ")) > 1 else ""
                        else:
                            final_cli = e_cli_man
                            final_tel = e_tel_man
                            
                        if final_cli and e_prod:
                            try:
                                client.table("encargos_clientes").insert({
                                    "nombre_cliente": final_cli, "telefono": final_tel, 
                                    "detalle_pedido": f"{e_cant}x {e_prod}",
                                    "notas": e_obs, "estado": "Pendiente"
                                }).execute()
                                st.success("Encargo guardado."); time.sleep(0.5); st.rerun()
                            except Exception as e:
                                st.error("Error al guardar en la base de datos.")
                        else:
                            st.warning("Debes indicar un cliente y el producto a pedir.")
            
            with col_en2:
                st.markdown("#### 📌 Encargos Pendientes")
                try:
                    res_e = client.table("encargos_clientes").select("*").order("created_at", desc=True).execute()
                    if res_e.data:
                        df_e = pd.DataFrame(res_e.data)
                        df_e['Fecha'] = pd.to_datetime(df_e['created_at']).dt.strftime('%d/%m/%Y')
                        if 'notas' not in df_e.columns: df_e['notas'] = ""
                        
                        hoy_date = pd.to_datetime('today')
                        for idx, row in df_e.iterrows():
                            dias = (hoy_date - pd.to_datetime(row['created_at']).dt.tz_localize(None)).days
                            if dias >= 2 and row['estado'] == 'Pendiente':
                                st.warning(f"⚠️ **RETRASO:** El encargo de {row['nombre_cliente']} lleva {dias} días en estado Pendiente.")
                        
                        df_e_vista = df_e[['id', 'Fecha', 'nombre_cliente', 'telefono', 'detalle_pedido', 'notas', 'estado']]
                        ed_e = st.data_editor(
                            df_e_vista, hide_index=True, use_container_width=True, num_rows="dynamic", height=300,
                            column_config={
                                "id": None, "Fecha": "Día", "nombre_cliente": "Cliente", "telefono": "Tel.",
                                "detalle_pedido": "Producto y Cant.", "notas": "Observaciones",
                                "estado": st.column_config.SelectboxColumn("Estado", options=["Pendiente", "Pedido", "Recibido", "Entregado"])
                            }
                        )
                        if st.button("💾 Guardar Cambios en Encargos"):
                            for _, r in ed_e.iterrows():
                                if pd.notna(r['id']):
                                    client.table("encargos_clientes").update({
                                        "estado": str(r['estado']), "notas": str(r['notas'])
                                    }).eq("id", r['id']).execute()
                            st.rerun()
                    else: st.info("No hay encargos activos.")
                except: st.warning("Por favor, revisa la conexión con la tabla encargos_clientes.")