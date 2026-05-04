import streamlit as st
import pandas as pd
from datetime import date, timedelta
import time

def render_pestana_agenda(client):
    st.markdown("<h3 style='margin-bottom: 5px;'>📅 Agenda Animalarium</h3>", unsafe_allow_html=True)
    
    # --- DATOS COMUNES PARA TODAS LAS SUB-PESTAÑAS DE AGENDA ---
    res_m = client.table("mascotas").select("id, nombre, clientes(nombre_dueno)").execute()
    dict_mascotas = {}
    if res_m.data:
        for m in res_m.data:
            dueno = m['clientes']['nombre_dueno'] if m.get('clientes') else "Desconocido"
            dict_mascotas[f"🐾 {m['nombre']} (De: {dueno})"] = m['id']
            
    res_citas = client.table("citas").select("id, fecha_hora, servicio, duracion_minutos, mascotas(nombre, clientes(nombre_dueno, telefono))").order("fecha_hora", desc=False).execute()
    
    # --- PESTAÑAS DE VISTAS ---
    sub_agenda, sub_diario, sub_semanal = st.tabs(["📝 Gestión de Citas", "🕒 Vista Diaria", "🗓️ Vista Semanal"])
    
    with sub_agenda:
        c_agenda1, c_agenda2 = st.columns([1, 2.5], gap="large")
        
        with c_agenda1:
            # Cargar lista de empleados
            try:
                emp_res = client.table("personal_empleados").select("id, nombre").eq("activo", True).execute()
                empleados_lista = [e['nombre'] for e in emp_res.data] if emp_res.data else []
            except: empleados_lista = []
            
            with st.form("nueva_cita", border=True):
                st.markdown("#### ➕ Nueva Cita")
                mascota_sel = st.selectbox("Selecciona Mascota *", list(dict_mascotas.keys()), index=None)
                fecha_c = st.date_input("Fecha *")
                f_emp = st.selectbox("Peluquera/o:", ["Cualquiera"] + empleados_lista)
                hora_c = st.time_input("Hora de Inicio *")
                duracion_c = st.number_input("Duración estimada (minutos) *", min_value=5, max_value=300, value=60, step=5)
                servicio_sel = st.selectbox("Servicio *", ["Peluquería (Baño y Corte)", "Peluquería (Solo Baño)", "Corte de Uñas", "Revisión Veterinaria", "Otro"])
                
                if st.form_submit_button("Guardar Cita", type="primary", use_container_width=True):
                    if mascota_sel:
                        fecha_hora_str = f"{fecha_c} {hora_c.strftime('%H:%M')}"
                        servicio_final = servicio_sel if f_emp == "Cualquiera" else f"{servicio_sel} ({f_emp})"
                        client.table("citas").insert({
                            "mascotas_id": dict_mascotas[mascota_sel],
                            "fecha_hora": fecha_hora_str,
                            "servicio": servicio_final,
                            "duracion_minutos": int(duracion_c)
                        }).execute()
                        st.success("Cita agendada.")
                        time.sleep(1); st.rerun()
                    else:
                        st.error("Debes seleccionar una mascota.")

        with c_agenda2:
            st.markdown("#### 🗓️ Directorio de Citas (Editable)")
            if res_citas.data:
                citas_formateadas = []
                for c in res_citas.data:
                    mascota_info = c.get('mascotas', {})
                    cliente_info = mascota_info.get('clientes', {}) if mascota_info else {}
                    dur = c.get('duracion_minutos') if c.get('duracion_minutos') is not None else 60
                    
                    citas_formateadas.append({
                        "id": c['id'],
                        "Día y Hora": c['fecha_hora'],
                        "Duración (min)": dur,
                        "Servicio": c['servicio'],
                        "Mascota": mascota_info.get('nombre', 'N/A'),
                        "Dueño": cliente_info.get('nombre_dueno', 'N/A'),
                        "Teléfono": cliente_info.get('telefono', 'N/A')
                    })
                    
                df_citas = pd.DataFrame(citas_formateadas)
                
                ed_citas = st.data_editor(
                    df_citas[['id', 'Día y Hora', 'Duración (min)', 'Servicio', 'Mascota', 'Dueño', 'Teléfono']],
                    use_container_width=True, hide_index=True, num_rows="dynamic", key="ed_citas_ag", height=400,
                    column_config={
                        "id": None,
                        "Mascota": st.column_config.TextColumn(disabled=True),
                        "Dueño": st.column_config.TextColumn(disabled=True),
                        "Teléfono": st.column_config.TextColumn(disabled=True)
                    }
                )
                
                if st.button("💾 Guardar Cambios en Agenda", type="primary"):
                    ids_actuales = ed_citas['id'].dropna().tolist()
                    ids_orig = df_citas['id'].tolist()
                    ids_borrar = [i for i in ids_orig if i not in ids_actuales]
                    
                    for id_b in ids_borrar: client.table("citas").delete().eq("id", id_b).execute()
                    
                    for _, row in ed_citas.iterrows():
                        if pd.notna(row['id']):
                            client.table("citas").update({
                                "fecha_hora": str(row['Día y Hora']),
                                "duracion_minutos": int(row['Duración (min)']),
                                "servicio": str(row['Servicio'])
                            }).eq("id", row['id']).execute()
                    st.success("Agenda actualizada."); time.sleep(0.8); st.rerun()
            else:
                st.info("No hay citas agendadas en el sistema.")
                
    with sub_diario:
        st.markdown("#### 🕒 Cuadrante de Trabajo Diario (Intervalos de 5 min)")
        dia_ver = st.date_input("Selecciona un día para ver los huecos libres:", value=date.today())
        
        # Creamos una cuadrícula estricta de 5 en 5 minutos (09:00 a 20:55)
        horas_trabajo = [f"{h:02d}:{m:02d}" for h in range(9, 21) for m in range(0, 60, 5)]
        df_cuadrante = pd.DataFrame({"Hora": horas_trabajo})
        df_cuadrante["Estado"] = "🟩 Libre"
        df_cuadrante["Detalle"] = ""
        
        if res_citas.data:
            for c in res_citas.data:
                try:
                    dt_start = pd.to_datetime(c['fecha_hora'])
                    if dt_start.date() == dia_ver:
                        dur = c.get('duracion_minutos') if c.get('duracion_minutos') is not None else 60
                        dt_end = dt_start + pd.Timedelta(minutes=dur)
                        mascota = c.get('mascotas', {}).get('nombre', 'Mascota')
                        detalle_texto = f"{mascota} ({dur} min) - {c['servicio']}"
                        
                        # Recorremos la cuadrícula y rellenamos los huecos afectados
                        for idx, row in df_cuadrante.iterrows():
                            q_time = pd.to_datetime(f"{dia_ver} {row['Hora']}")
                            if dt_start <= q_time < dt_end:
                                df_cuadrante.loc[idx, "Estado"] = "🔴 OCUPADO"
                                df_cuadrante.loc[idx, "Detalle"] = detalle_texto
                except: pass
                
        df_cuadrante = df_cuadrante.sort_values("Hora").reset_index(drop=True)
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
                    if start_of_week <= dt_start.date() <= end_of_week:
                        duracion = cita.get('duracion_minutos') if cita.get('duracion_minutos') is not None else 60
                        dt_end = dt_start + timedelta(minutes=duracion)
                        
                        col_dia = dt_start.strftime('%A\n%d/%m')
                        mascota_nombre = cita.get('mascotas', {}).get('nombre', 'Cita')
                        
                        # Formato visual tipo tarjeta: "09:00 a 10:15 | Bobby"
                        texto_cita = f"🕒 {dt_start.strftime('%H:%M')} a {dt_end.strftime('%H:%M')} | {mascota_nombre} ({cita['servicio']})"
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