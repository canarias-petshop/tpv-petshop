import streamlit as st
import pandas as pd
from datetime import date, timedelta
import time
import urllib.parse

def render_pestana_agenda(client):
    st.markdown("<h3 style='margin-bottom: 5px;'>📅 Agenda Animalarium</h3>", unsafe_allow_html=True)
    
    # --- DATOS COMUNES PARA TODAS LAS SUB-PESTAÑAS DE AGENDA ---
    res_m = client.table("mascotas").select("id, nombre, clientes(nombre_dueno)").execute()
    dict_mascotas = {}
    if res_m.data:
        for m in res_m.data:
            dueno = m['clientes']['nombre_dueno'] if m.get('clientes') else "Desconocido"
            dict_mascotas[f"🐾 {m['nombre']} (De: {dueno})"] = m['id']
            
    res_citas = client.table("citas").select("id, fecha_hora, servicio, duracion_minutos, observaciones, mascotas(nombre, clientes(nombre_dueno, telefono))").order("fecha_hora", desc=False).execute()
    
    # --- DATOS COMUNES ---
    try:
        emp_res = client.table("personal_empleados").select("id, nombre").eq("activo", True).execute()
        empleados_lista = [e['nombre'] for e in emp_res.data] if emp_res.data else []
    except: empleados_lista = []
    
    try:
        serv_res = client.table("productos").select("nombre").eq("categoria", "Servicio").order("nombre").execute()
        servicios_lista = [s['nombre'] for s in serv_res.data] + ["Otro"] if serv_res.data else ["Peluquería", "Otro"]
    except: 
        servicios_lista = ["Otro"]

    ESTADOS_CITA = ["Confirmada", "Cancelada", "Cambio de cita", "Servicio de recogida", "Cambio (día antes)", "Cambio (mismo día)", "Oferta / Descuento", "Pendiente"]
    EMOJIS_ESTADO = {
        "Confirmada": "🟢", "Cancelada": "💖", "Cambio de cita": "🔵", 
        "Servicio de recogida": "🟣", "Cambio (día antes)": "🟠", 
        "Cambio (mismo día)": "⚪", "Oferta / Descuento": "🟩", "Pendiente": "🟡"
    }

    def parse_cita_estado(servicio_raw):
        estado = "Confirmada"
        if "[ESTADO:" in servicio_raw:
            import re
            m_est = re.match(r'\[ESTADO:\s*(.*?)\]\s*(.*)', servicio_raw)
            if m_est:
                estado = m_est.group(1)
                servicio_raw = m_est.group(2)
        emp = "Sin Asignar"
        for e in empleados_lista:
            if f"({e})" in servicio_raw:
                emp = e; servicio_raw = servicio_raw.replace(f"({e})", "").replace("  ", " ").strip(); break
        return estado, servicio_raw.strip(), emp
    
    # --- PESTAÑAS DE VISTAS ---
    sub_agenda, sub_diario, sub_semanal, sub_recordatorios, sub_cancelaciones = st.tabs(["📝 Gestión de Citas", "🕒 Vista Diaria", "🗓️ Vista Semanal", "🔔 Recordatorios", "🚫 Cancelaciones"])
    
    with sub_agenda:
        c_agenda1, c_agenda2 = st.columns([1, 2.5], gap="large")
        
        with c_agenda1:
            with st.container(border=True):
                st.markdown("#### ➕ Nueva Cita")
                
                crear_rapido = st.toggle("🐾 Mascota no registrada (Crear ficha rápida)")
                mascota_sel = None
                n_mascota, n_cliente, n_tel = "", "", ""
                
                if crear_rapido:
                    st.markdown("<p style='font-size: 13px; color: gray; margin-top:-10px;'>Se creará una ficha básica automáticamente en Clientes.</p>", unsafe_allow_html=True)
                    c_nx1, c_nx2, c_nx3 = st.columns([1.5, 1.5, 1])
                    with c_nx1: n_mascota = st.text_input("Nombre Mascota *")
                    with c_nx2: n_cliente = st.text_input("Dueño *")
                    with c_nx3: n_tel = st.text_input("Teléfono")
                else:
                    mascota_sel = st.selectbox("Selecciona Mascota *", list(dict_mascotas.keys()), index=None)
                
                pref_actual = "Cualquiera"
                dur_media = 60
                if mascota_sel:
                    m_id_sel = dict_mascotas[mascota_sel]
                    res_m_info = client.table("mascotas").select("observaciones, historial_trabajos").eq("id", m_id_sel).execute()
                    if res_m_info.data:
                        obs = res_m_info.data[0].get('observaciones', '')
                        import re
                        m_pref = re.search(r'\[Pref:\s*(.*?)\]', str(obs))
                        if m_pref: pref_actual = m_pref.group(1)
                        
                        historial = res_m_info.data[0].get('historial_trabajos', [])
                        duraciones = [t['Duración (min)'] for t in historial if isinstance(t, dict) and isinstance(t.get('Duración (min)'), (int, float))]
                        if duraciones: 
                            dur_media = int(sum(duraciones) / len(duraciones))
                            st.info(f"⏱️ **Info de la mascota:** Tiempo medio de {dur_media} min | Peluquero/a pref: {pref_actual}")
                        else:
                            st.info(f"⏱️ **Info de la mascota:** Sin historial (60 min por defecto) | Peluquero/a pref: {pref_actual}")
                        
                fecha_c = st.date_input("Fecha *", value=date.today())
                duracion_c = st.number_input("Duración estimada (minutos) *", min_value=5, max_value=300, value=dur_media, step=5)
                
                opciones_emp = ["Cualquiera"] + empleados_lista
                def_index = opciones_emp.index(pref_actual) if pref_actual in opciones_emp else 0
                f_emp = st.selectbox("Peluquera/o Preferido:", opciones_emp, index=def_index)
                
                # Buscador inteligente de huecos cruzado con el preferido
                res_turnos = client.table("personal_cuadrantes").select("empleado_id, turno, personal_empleados(nombre)").eq("fecha", str(fecha_c)).execute()
                turnos_dict = {}
                if res_turnos.data:
                    for t in res_turnos.data:
                        if t.get('personal_empleados'): turnos_dict[t['personal_empleados']['nombre']] = t['turno'].lower()
                            
                empleados_a_revisar = [f_emp] if f_emp != "Cualquiera" else empleados_lista
                huecos_obj = []
                
                citas_dia = []
                if res_citas.data:
                    for c in res_citas.data:
                        try:
                            dt_c = pd.to_datetime(c['fecha_hora'])
                            if dt_c.tzinfo: dt_c = dt_c.tz_localize(None)
                            if dt_c.date() == fecha_c: citas_dia.append(c)
                        except: pass
                
                for emp_nombre in empleados_a_revisar:
                    turno_str = turnos_dict.get(emp_nombre, "")
                    if not turno_str or "libre" in turno_str or "vacaciones" in turno_str: continue
                        
                    import re
                    times = re.findall(r'(\d{1,2}:\d{2})', turno_str)
                    if len(times) >= 2:
                        h_ini = pd.to_datetime(f"{fecha_c} {times[0]}")
                        h_fin = pd.to_datetime(f"{fecha_c} {times[1]}")
                    else:
                        if fecha_c.weekday() < 5: # Lunes a Viernes
                            h_ini = pd.to_datetime(f"{fecha_c} 09:00")
                            h_fin = pd.to_datetime(f"{fecha_c} 21:00")
                        else: # Sábados y Domingos
                            h_ini = pd.to_datetime(f"{fecha_c} 10:00")
                            h_fin = pd.to_datetime(f"{fecha_c} 14:00")
                        
                    for h in range(0, 24):
                        for m in range(0, 60, 5):
                            dt_ini = pd.to_datetime(f"{fecha_c} {h:02d}:{m:02d}")
                            if dt_ini < h_ini: continue
                            dt_fin = dt_ini + pd.Timedelta(minutes=duracion_c)
                            if dt_fin > h_fin: continue
                            
                            solapa = False
                            for c in citas_dia:
                                if "[ESTADO: Cancelada]" in c.get('servicio', ''): continue
                                c_ini = pd.to_datetime(c['fecha_hora'])
                                if c_ini.tzinfo: c_ini = c_ini.tz_localize(None)
                                c_fin = c_ini + pd.Timedelta(minutes=c.get('duracion_minutos') or 60)
                                if dt_ini < c_fin and dt_fin > c_ini:
                                    s = c.get('servicio', '')
                                    assigned_e = None
                                    for e in empleados_lista:
                                        if f"({e})" in s: assigned_e = e; break
                                    if assigned_e == emp_nombre or assigned_e is None:
                                        solapa = True; break
                            if not solapa: huecos_obj.append({"dt": dt_ini, "hora": f"{h:02d}:{m:02d}", "emp": emp_nombre})
                
                huecos_obj.sort(key=lambda x: x["dt"])
                huecos_formateados = [f"{x['hora']} (Con {x['emp']})" for x in huecos_obj]
                huecos_formateados.append("Asignación Manual")
                
                if len(huecos_formateados) == 1: st.warning("No hay huecos disponibles en el cuadrante.")
                f_hora_sel = st.selectbox("Hora recomendada:", huecos_formateados)
                    
                hora_manual = None
                solapa_manual = False
                motivo_solape = ""
                motivo_extra = ""
                
                if f_hora_sel == "Asignación Manual":
                    hora_manual = st.time_input("Hora de Inicio *")
                    if hora_manual:
                        dt_ini_man = pd.to_datetime(f"{fecha_c} {hora_manual.strftime('%H:%M')}")
                        dt_fin_man = dt_ini_man + pd.Timedelta(minutes=duracion_c)
                        for c in citas_dia:
                            if "[ESTADO: Cancelada]" in c.get('servicio', ''): continue
                            c_ini = pd.to_datetime(c['fecha_hora'])
                            if c_ini.tzinfo: c_ini = c_ini.tz_localize(None)
                            c_fin = c_ini + pd.Timedelta(minutes=c.get('duracion_minutos') or 60)
                            if dt_ini_man < c_fin and dt_fin_man > c_ini:
                                s = c.get('servicio', '')
                                assigned_e = None
                                for e in empleados_lista:
                                    if f"({e})" in s: assigned_e = e; break
                                if f_emp != "Cualquiera":
                                    if assigned_e == f_emp or assigned_e is None: solapa_manual = True; break
                                else:
                                    solapa_manual = True; break
                        
                        if solapa_manual:
                            st.warning("⚠️ La hora seleccionada ya está ocupada o hay citas sin asignar en esa franja.")
                            motivo_solape = st.selectbox("Motivo para forzar la cita: *", ["", "Tenemos otro peluquero disponible", "Se va a ayudar con la peluquería", "Se puede hacer a la vez", "Otro motivo"])
                            if motivo_solape == "Otro motivo":
                                motivo_extra = st.text_input("Especificar otro motivo: *")
                
                servicio_sel = st.selectbox("Servicio *", servicios_lista)
                f_obs = st.text_input("📝 Observaciones / Petición (Opcional)")
                
                if st.button("Guardar Cita", type="primary", use_container_width=True):
                    m_id_final = None
                    
                    if solapa_manual and (not motivo_solape or (motivo_solape == "Otro motivo" and not motivo_extra)):
                        st.error("Debes indicar un motivo para forzar la cita en una hora ocupada.")
                    else:
                        if crear_rapido:
                            if n_mascota and n_cliente:
                                res_cli = client.table("clientes").insert({
                                    "nombre_dueno": n_cliente, "telefono": n_tel, "puntos": 0
                                }).execute()
                                if res_cli.data:
                                    res_m = client.table("mascotas").insert({
                                        "cliente_id": res_cli.data[0]['id'], "nombre": n_mascota
                                    }).execute()
                                    if res_m.data: m_id_final = res_m.data[0]['id']
                            else:
                                st.error("Debes indicar al menos el nombre de la mascota y del dueño para crear la ficha.")
                        else:
                            if mascota_sel:
                                m_id_final = dict_mascotas[mascota_sel]
                            else:
                                st.error("Debes seleccionar una mascota.")
                                
                        if m_id_final:
                            if f_hora_sel == "Asignación Manual":
                                hora_final_str = hora_manual.strftime('%H:%M')
                                emp_final = f_emp if f_emp != "Cualquiera" else ""
                            else:
                                hora_final_str = f_hora_sel.split(" (")[0]
                                emp_final = f_hora_sel.split("(Con ")[1].replace(")", "")
                                
                            servicio_final = f"{servicio_sel} ({emp_final})" if emp_final else servicio_sel
                            
                            if solapa_manual:
                                motivo_final = motivo_extra if motivo_solape == "Otro motivo" else motivo_solape
                                servicio_final += f" [Forzado: {motivo_final}]"
                                
                            servicio_final = f"[ESTADO: Confirmada] {servicio_final}"
                            fecha_hora_str = f"{fecha_c} {hora_final_str}"
                            
                            client.table("citas").insert({
                                "mascotas_id": m_id_final, "fecha_hora": fecha_hora_str,
                                "servicio": servicio_final, "duracion_minutos": int(duracion_c),
                                "observaciones": str(f_obs)
                            }).execute()
                            st.success("Cita agendada."); time.sleep(1); st.rerun()

        with c_agenda2:
            st.markdown("#### 🗓️ Directorio de Citas (Editable)")
            if res_citas.data:
                citas_formateadas = []
                for c in res_citas.data:
                    mascota_info = c.get('mascotas', {})
                    cliente_info = mascota_info.get('clientes', {}) if mascota_info else {}
                    dur = c.get('duracion_minutos') if c.get('duracion_minutos') is not None else 60
                    
                    dt_obj = pd.to_datetime(c['fecha_hora'])
                    
                    estado_c, s_clean, assigned_e = parse_cita_estado(c.get('servicio', ''))
                    
                    emoji_estado = EMOJIS_ESTADO.get(estado_c, "🟢")
                    estado_con_emoji = f"{emoji_estado} {estado_c}"
                            
                    tel_limpio = ''.join(filter(str.isdigit, str(cliente_info.get('telefono', ''))))
                    url_wa = None
                    if tel_limpio:
                        if len(tel_limpio) == 9 and not tel_limpio.startswith('34'): tel_limpio = '34' + tel_limpio
                        msg_cita = f"¡Hola {cliente_info.get('nombre_dueno', '')}! 🐾 Te escribimos de Animalarium para recordarte la cita de {mascota_info.get('nombre', '')} el día {dt_obj.strftime('%d/%m/%Y')} a las {dt_obj.strftime('%H:%M')}. Por favor, confírmanos tu asistencia. ¡Te esperamos! ✂️"
                        url_wa = f"https://wa.me/{tel_limpio}?text={urllib.parse.quote(msg_cita)}"
                            
                    citas_formateadas.append({
                        "id": c['id'],
                        "Día": dt_obj.strftime('%d/%m/%Y'),
                        "Hora": dt_obj.strftime('%H:%M'),
                        "Estado": estado_con_emoji,
                        "Duración (min)": dur,
                        "Peluquero/a": assigned_e,
                        "Servicio": s_clean,
                        "Mascota": mascota_info.get('nombre', 'N/A'),
                        "Dueño": cliente_info.get('nombre_dueno', 'N/A'),
                        "Teléfono": cliente_info.get('telefono', 'N/A'),
                        "Observaciones": c.get('observaciones', ''),
                        "WhatsApp": url_wa
                    })
                    
                df_citas = pd.DataFrame(citas_formateadas)
                
                ed_citas = st.data_editor(
                    df_citas[['id', 'Día', 'Hora', 'Estado', 'Duración (min)', 'Peluquero/a', 'Servicio', 'Observaciones', 'Mascota', 'Dueño', 'Teléfono', 'WhatsApp']],
                    use_container_width=True, hide_index=True, num_rows="dynamic", key="ed_citas_ag", height=400,
                    column_order=["Día", "Hora", "Estado", "Peluquero/a", "Mascota", "Servicio", "Observaciones", "Duración (min)", "Dueño", "Teléfono", "WhatsApp"],
                    column_config={
                        "id": None,
                        "Día": st.column_config.TextColumn("Día (DD/MM/AAAA)", width="small"),
                        "Hora": st.column_config.TextColumn("Hora", width="small"),
                        "Estado": st.column_config.SelectboxColumn("🎨 Estado", options=[f"{EMOJIS_ESTADO.get(e, '')} {e}" for e in ESTADOS_CITA], required=True),
                        "Peluquero/a": st.column_config.SelectboxColumn("👩‍🦰 Peluquero/a", options=["Sin Asignar"] + empleados_lista, required=True),
                        "Mascota": st.column_config.TextColumn(disabled=True),
                        "Dueño": st.column_config.TextColumn(disabled=True),
                        "Teléfono": st.column_config.TextColumn(disabled=True),
                        "Observaciones": st.column_config.TextColumn("Anotación"),
                        "WhatsApp": st.column_config.LinkColumn("📱 Avisar", display_text="💬 Recordatorio")
                    }
                )
                
                if st.button("💾 Guardar Cambios en Agenda", type="primary"):
                    ids_actuales = ed_citas['id'].dropna().tolist()
                    ids_orig = df_citas['id'].tolist()
                    ids_borrar = [i for i in ids_orig if i not in ids_actuales]
                    
                    for id_b in ids_borrar: client.table("citas").delete().eq("id", id_b).execute()
                    
                    for _, row in ed_citas.iterrows():
                        if pd.notna(row['id']):
                            try:
                                dt_str = pd.to_datetime(f"{row['Día']} {row['Hora']}", format='%d/%m/%Y %H:%M').strftime('%Y-%m-%d %H:%M:%S')
                            except:
                                dt_str = pd.to_datetime(f"{row['Día']} {row['Hora']}").strftime('%Y-%m-%d %H:%M:%S')
                                
                            srv = str(row['Servicio'])
                            pelu = str(row['Peluquero/a'])
                            est_raw = str(row['Estado'])
                            est = est_raw.split(" ", 1)[1] if " " in est_raw else est_raw
                            if pelu != "Sin Asignar":
                                srv_base = f"{srv} ({pelu})"
                            else:
                                srv_base = srv
                                
                            srv_final = f"[ESTADO: {est}] {srv_base}"
                                
                            client.table("citas").update({
                                "fecha_hora": dt_str,
                                "duracion_minutos": int(row['Duración (min)']),
                                "servicio": srv_final,
                                "observaciones": str(row.get('Observaciones', ''))
                            }).eq("id", row['id']).execute()
                    st.success("Agenda actualizada."); time.sleep(0.8); st.rerun()
            else:
                st.info("No hay citas agendadas en el sistema.")
                
    with sub_diario:
        st.markdown("#### 🕒 Cuadrante de Trabajo Diario (Intervalos de 5 min)")
        
        c_diario1, c_diario2, c_diario3 = st.columns([1, 1.5, 1])
        with c_diario1:
            dia_ver = st.date_input("Selecciona un día para ver los huecos libres:", value=date.today())
        with c_diario2:
            rango_defecto = (9, 21) if dia_ver.weekday() < 5 else (10, 14)
            rango_horas = st.slider("⏱️ Rango de horas visible:", min_value=6, max_value=23, value=rango_defecto, format="%d:00")
        with c_diario3:
            st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
            ocultar_libres = st.checkbox("Ocultar tramos libres (Vista compacta)", value=False)
        
        # Creamos una cuadrícula estricta adaptada a la selección
        horas_trabajo = [f"{h:02d}:{m:02d}" for h in range(rango_horas[0], rango_horas[1]) for m in range(0, 60, 5)]
        df_cuadrante = pd.DataFrame({"Hora": horas_trabajo})
        df_cuadrante["Estado"] = "🟩 Libre"
        df_cuadrante["Detalle"] = ""
        
        if res_citas.data:
            for c in res_citas.data:
                try:
                    if "[ESTADO: Cancelada]" in c.get('servicio', ''): continue
                    dt_start = pd.to_datetime(c['fecha_hora'])
                    if dt_start.tzinfo: dt_start = dt_start.tz_localize(None)
                    if dt_start.date() == dia_ver:
                        dur = c.get('duracion_minutos') if c.get('duracion_minutos') is not None else 60
                        dt_end = dt_start + pd.Timedelta(minutes=dur)
                        mascota = c.get('mascotas', {}).get('nombre', 'Mascota')
                        
                        estado_c, s_clean, assigned_e = parse_cita_estado(c.get('servicio', ''))
                        emoji = EMOJIS_ESTADO.get(estado_c, "🟢")
                                
                        detalle_texto = f"{emoji} [{assigned_e}] {mascota} ({dur} min) - {s_clean}"
                        
                        # Recorremos la cuadrícula y rellenamos los huecos afectados
                        primer_bloque = True
                        for idx, row in df_cuadrante.iterrows():
                            q_time = pd.to_datetime(f"{dia_ver} {row['Hora']}")
                            if dt_start <= q_time < dt_end:
                                # Estado dinámico (Soporta múltiples peluqueros a la vez)
                                if df_cuadrante.loc[idx, "Estado"] == "🟩 Libre":
                                    df_cuadrante.loc[idx, "Estado"] = "🔴 Ocupado"
                                elif "Ocupado" in df_cuadrante.loc[idx, "Estado"]:
                                    df_cuadrante.loc[idx, "Estado"] = "⚠️ Múltiple"
                                
                                # Texto compacto si la cita ocupa muchos tramos
                                if primer_bloque:
                                    texto_add = detalle_texto
                                    primer_bloque = False
                                else:
                                    texto_add = f"⏬ (Continúa {mascota})"
                                
                                if df_cuadrante.loc[idx, "Detalle"]:
                                    df_cuadrante.loc[idx, "Detalle"] += "  |  " + texto_add
                                else:
                                    df_cuadrante.loc[idx, "Detalle"] = texto_add
                except: pass
                
        df_cuadrante = df_cuadrante.sort_values("Hora").reset_index(drop=True)
        
        if ocultar_libres:
            df_cuadrante = df_cuadrante[df_cuadrante["Estado"] != "🟩 Libre"]
            if df_cuadrante.empty:
                st.info("No hay citas programadas para este día.")
                
        st.dataframe(df_cuadrante, use_container_width=True, hide_index=True, height=600)

    with sub_semanal:
        st.markdown("#### 🗓️ Cuadrante de Trabajo Semanal (Vista Flexible)")
        dia_referencia = st.date_input("Selecciona una fecha para ver su semana:", value=date.today(), key="semana_picker")
        
        start_of_week = dia_referencia - timedelta(days=dia_referencia.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        st.markdown(f"##### Semana del {start_of_week.strftime('%d/%m/%Y')} al {end_of_week.strftime('%d/%m/%Y')}")

        dias_semana_dt = [(start_of_week + timedelta(days=i)) for i in range(7)]
        nombres_dias_col = [d.strftime('%A\n%d/%m') for d in dias_semana_dt]

        # Diccionario para agrupar citas por columna (día)
        citas_por_dia = {dia: [] for dia in nombres_dias_col}

        if res_citas.data:
            for cita in res_citas.data:
                try:
                    dt_start = pd.to_datetime(cita['fecha_hora'])
                    if dt_start.tzinfo: dt_start = dt_start.tz_localize(None)
                    if start_of_week <= dt_start.date() <= end_of_week:
                        if "[ESTADO: Cancelada]" in cita.get('servicio', ''): continue
                        duracion = cita.get('duracion_minutos') if cita.get('duracion_minutos') is not None else 60
                        dt_end = dt_start + timedelta(minutes=duracion)
                        
                        col_dia = dt_start.strftime('%A\n%d/%m')
                        mascota_nombre = cita.get('mascotas', {}).get('nombre', 'Cita')
                        
                        estado_c, s_clean, assigned_e = parse_cita_estado(cita.get('servicio', ''))
                        emoji = EMOJIS_ESTADO.get(estado_c, "🟢")
                        
                        texto_cita = f"{emoji} {dt_start.strftime('%H:%M')}-{dt_end.strftime('%H:%M')} | {mascota_nombre} ({assigned_e})"
                        citas_por_dia[col_dia].append((dt_start, texto_cita))
                except Exception: pass
        
        # Ordenar cronológicamente y preparar para la tabla
        max_filas = 0
        for dia in nombres_dias_col:
            citas_por_dia[dia].sort(key=lambda x: x[0])  # Ordenar por hora de inicio
            citas_por_dia[dia] = [c[1] for c in citas_por_dia[dia]]  # Quedarnos solo con el texto
            if len(citas_por_dia[dia]) > max_filas:
                max_filas = len(citas_por_dia[dia])
                
        if max_filas == 0:
            df_semana = pd.DataFrame([["" for _ in nombres_dias_col]], columns=nombres_dias_col)
            st.info("Semana completamente libre. No hay citas agendadas.")
        else:
            # Rellenar con blancos las listas más cortas para cuadrar el DataFrame
            for dia in nombres_dias_col:
                while len(citas_por_dia[dia]) < max_filas:
                    citas_por_dia[dia].append("")
            df_semana = pd.DataFrame(citas_por_dia)
            st.dataframe(df_semana, use_container_width=True, hide_index=True)
            
    with sub_recordatorios:
        st.markdown("#### 🔔 Centro de Recordatorios (Citas y Mantenimiento)")
        st.info("Espacio centralizado para gestionar las confirmaciones de citas y mantenimientos diarios (vía WhatsApp o llamada telefónica).")
        
        # --- 1. CONFIRMACIONES DEL PRÓXIMO DÍA HÁBIL ---
        hoy_dt = pd.to_datetime('today')
        manana_dt = hoy_dt + pd.Timedelta(days=1)
        
        # Si el próximo día es domingo (6), saltamos automáticamente al lunes
        if manana_dt.weekday() == 6:
            manana_dt += pd.Timedelta(days=1)
            
        dias_es = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}
        nombre_dia_obj = dias_es[manana_dt.weekday()]
        
        st.markdown(f"##### 📅 1. Confirmaciones para el {nombre_dia_obj} ({manana_dt.strftime('%d/%m')})")
        
        manana_str_ini = manana_dt.strftime('%Y-%m-%dT00:00:00')
        manana_str_fin = manana_dt.strftime('%Y-%m-%dT23:59:59')
        
        res_manana = client.table("citas").select("fecha_hora, servicio, mascotas(nombre, clientes(nombre_dueno, telefono, metodo_contacto))").gte("fecha_hora", manana_str_ini).lte("fecha_hora", manana_str_fin).execute()
        
        citas_manana = []
        if res_manana.data:
            for c in res_manana.data:
                if "[ESTADO: Cancelada]" in c.get('servicio', ''): continue
                mascota_info = c.get('mascotas', {}) or {}
                cliente_info = mascota_info.get('clientes', {}) or {}
                dueno = cliente_info.get('nombre_dueno', 'Dueño')
                telefono = cliente_info.get('telefono', '')
                pref_contacto = cliente_info.get('metodo_contacto') or 'WhatsApp'
                nombre_m = mascota_info.get('nombre', 'tu mascota')
                
                dt_obj = pd.to_datetime(c['fecha_hora'])
                hora_str = dt_obj.strftime('%H:%M')
                
                tel_limpio = ''.join(filter(str.isdigit, str(telefono)))
                url_wa = None
                if tel_limpio:
                    if len(tel_limpio) == 9 and not tel_limpio.startswith('34'): tel_limpio = '34' + tel_limpio
                    
                    dias_diff = (manana_dt.date() - hoy_dt.date()).days
                    texto_dia = "mañana" if dias_diff == 1 else f"el próximo {nombre_dia_obj.lower()}"
                    
                    msg = f"¡Hola {dueno}! 🐾 Nos ponemos en contacto desde Animalarium para recordarte que {texto_dia} a las {hora_str} tenemos una cita reservada para {nombre_m}. Por favor, ¿nos confirmas tu asistencia? ¡Muchas gracias y un saludo! ✂️🐶"
                    url_wa = f"https://wa.me/{tel_limpio}?text={urllib.parse.quote(msg)}"
                    
                import re
                s_raw = c.get('servicio', '')
                s_clean = re.sub(r'\[ESTADO:\s*.*?\]\s*', '', s_raw).strip()
                
                citas_manana.append({
                    "Hora": hora_str,
                    "Mascota": nombre_m,
                    "Dueño": dueno,
                    "Canal Pref.": pref_contacto,
                    "Servicio": s_clean,
                    "WhatsApp": url_wa
                })
                
        if citas_manana:
            df_manana = pd.DataFrame(citas_manana).sort_values("Hora")
            st.dataframe(df_manana, use_container_width=True, hide_index=True, column_config={"WhatsApp": st.column_config.LinkColumn("📱 Acción Automática", display_text="💬 Pedir Confirmación")})
        else:
            st.success(f"No hay citas programadas para el {nombre_dia_obj.lower()} o ya están todas canceladas.")

        st.markdown("---")
        
        # --- 2. RECORDATORIOS DE MANTENIMIENTO ---
        st.markdown("##### ✂️ 2. Recordatorios de Mantenimiento")
        st.markdown("<p style='color:gray; font-size:14px;'>Clientes que superan los días sin venir y <b>NO tienen ya una cita futura agendada</b>.</p>", unsafe_allow_html=True)
        
        c_al1, c_al2 = st.columns([1, 2])
        with c_al1:
            dias_aviso = st.slider("Mostrar mascotas sin venir en más de (días):", min_value=15, max_value=180, value=45, step=5)
        
        hoy_str = hoy_dt.strftime('%Y-%m-%dT00:00:00')
        res_futuras = client.table("citas").select("mascotas_id, servicio").gte("fecha_hora", hoy_str).execute()
        mascotas_con_cita = set()
        if res_futuras.data:
            for c in res_futuras.data:
                if "[ESTADO: Cancelada]" not in c.get("servicio", ""):
                    mascotas_con_cita.add(c["mascotas_id"])
        
        res_m_alertas = client.table("mascotas").select("id, nombre, historial_trabajos, clientes(nombre_dueno, telefono, metodo_contacto)").execute()
        
        if res_m_alertas.data:
            alertas = []
            for m in res_m_alertas.data:
                if m['id'] in mascotas_con_cita: continue
                    
                hist = m.get('historial_trabajos', [])
                if isinstance(hist, list) and len(hist) > 0:
                    try:
                        fechas = [pd.to_datetime(h['Fecha'], format='%d/%m/%Y', errors='coerce') for h in hist if h.get('Fecha')]
                        fechas = [f for f in fechas if pd.notna(f)]
                        if fechas:
                            ultima_visita = max(fechas)
                            dias_transcurridos = (hoy_dt - ultima_visita).days
                            
                            if dias_transcurridos >= dias_aviso:
                                cliente_info = m.get('clientes') or {}
                                dueno = cliente_info.get('nombre_dueno', 'Dueño')
                                telefono = cliente_info.get('telefono', '')
                                pref_contacto = cliente_info.get('metodo_contacto') or 'WhatsApp'
                                
                                tel_limpio = ''.join(filter(str.isdigit, str(telefono)))
                                if tel_limpio and len(tel_limpio) == 9 and not tel_limpio.startswith('34'): tel_limpio = '34' + tel_limpio
                                    
                                mensaje = f"¡Hola {dueno}! 🐾 Nos ponemos en contacto desde Animalarium porque, revisando la ficha de {m['nombre']}, hemos visto que ya le va tocando su sesión de peluquería para mantener el manto perfecto. Recuerda que si reservas antes de que se cumplan los 2 meses de su última visita, te aplicamos un 10% de descuento en el servicio. ¿Te buscamos un huequito para estos días? ¡Un abrazo! 🐶✂️"
                                url_wa = f"https://wa.me/{tel_limpio}?text={urllib.parse.quote(mensaje)}" if tel_limpio else None
                                
                                alertas.append({
                                    "Mascota": m['nombre'], "Dueño": dueno,
                                    "Canal Pref.": pref_contacto,
                                    "Última Visita": ultima_visita.strftime('%d/%m/%Y'),
                                    "Días Sin Venir": dias_transcurridos, "WhatsApp": url_wa
                                })
                    except Exception as e: pass
            
            if alertas:
                df_alertas = pd.DataFrame(alertas).sort_values(by="Días Sin Venir", ascending=False)
                st.warning(f"⚠️ Tienes **{len(alertas)}** clientes pendientes de contactar para mantenimiento.")
                st.dataframe(df_alertas, use_container_width=True, hide_index=True, column_config={"WhatsApp": st.column_config.LinkColumn("📱 Acción Automática", display_text="💬 Enviar WhatsApp")})
            else:
                st.success("✨ ¡Genial! Tienes la agenda al día. Ninguna mascota supera los días de alerta o ya tienen su cita.")

    with sub_cancelaciones:
        st.markdown("#### 🚫 Registro de Cancelaciones")
        st.info("Aquí aparecen todas las citas que han sido marcadas como 'Cancelada' desde el Directorio. Estas citas liberan su hueco automáticamente en la agenda para que puedas dárselo a otro.")
        canceladas = []
        if res_citas.data:
            for c in res_citas.data:
                if "[ESTADO: Cancelada]" in c.get('servicio', ''):
                    mascota_info = c.get('mascotas', {})
                    cliente_info = mascota_info.get('clientes', {}) if mascota_info else {}
                    dt_obj = pd.to_datetime(c['fecha_hora'])
                    _, s_clean, assigned_e = parse_cita_estado(c.get('servicio', ''))

                    canceladas.append({
                        "Fecha": dt_obj.strftime('%d/%m/%Y'),
                        "Hora": dt_obj.strftime('%H:%M'),
                        "Mascota": mascota_info.get('nombre', 'N/A'),
                        "Dueño": cliente_info.get('nombre_dueno', 'N/A'),
                        "Teléfono": cliente_info.get('telefono', 'N/A'),
                        "Peluquero/a": assigned_e,
                        "Servicio Programado": s_clean
                    })
        if canceladas: st.dataframe(pd.DataFrame(canceladas), use_container_width=True, hide_index=True)
        else: st.success("No hay cancelaciones registradas en el sistema.")