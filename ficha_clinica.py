import streamlit as st
import pandas as pd
import time
from datetime import date

def get_pref(obs):
    import re
    m = re.search(r'\[Pref:\s*(.*?)\]', str(obs))
    return m.group(1) if m else "Cualquiera"

def strip_pref(obs):
    import re
    return re.sub(r'\[Pref:\s*.*?\]\s*', '', str(obs)).strip()

def calcular_duracion_media(historial):
    """Calcula la duración media de los servicios a partir del historial JSON."""
    if not isinstance(historial, list) or not historial:
        return "N/A"
    
    duraciones = [t['Duración (min)'] for t in historial if isinstance(t, dict) and isinstance(t.get('Duración (min)'), (int, float))]
    
    if not duraciones:
        return "N/A"
        
    media = sum(duraciones) / len(duraciones)
    return f"{int(media)} min"

def mostrar_ficha_clinica(m_id, m_nombre, m_data, prefix, client, servicios_lista, empleados_lista, precios_servicios):
    """Renderiza la ficha clínica, el historial y el sistema inteligente de reservas."""
    st.markdown(f"#### 📖 Ficha e Historial Clínico/Peluquería: **{m_nombre}**")
    
    # --- ALERTA CITA CONFIRMADA SIN HISTORIAL ---
    hoy_str = str(date.today())
    res_alertas = client.table("citas").select("fecha_hora, servicio").eq("mascotas_id", m_id).lt("fecha_hora", hoy_str).like("servicio", "%[ESTADO: Confirmada]%").execute()
    
    historial = m_data.get('historial_trabajos')
    if not isinstance(historial, list): historial = []
    
    if res_alertas.data:
        citas_faltantes = []
        for c in res_alertas.data:
            try:
                dt_c_raw = pd.to_datetime(c['fecha_hora'])
                dt_c_date = dt_c_raw.date()
                encontrado = False
                for t in historial:
                    try:
                        if t.get('Fecha'):
                            dt_t = pd.to_datetime(t['Fecha'], format="%d/%m/%Y").date()
                            if dt_t == dt_c_date:
                                encontrado = True; break
                    except: pass
                if not encontrado:
                    citas_faltantes.append(dt_c_date.strftime("%d/%m/%Y"))
            except: pass
        
        if citas_faltantes:
            fechas_str = ", ".join(citas_faltantes)
            st.error(f"🚨 **¡ATENCIÓN!** Hay cita(s) confirmada(s) los días: **{fechas_str}** pero no se ha cerrado la ficha. Rellena el historial abajo y añade el importe para que las estadísticas sean correctas y desaparezca este aviso.")
    
    df_hist = pd.DataFrame(historial)
    columnas_hist = ["Fecha", "Trabajo / Servicio", "Tratamiento", "Peluquera/o", "Inicio de sesión", "Fin de sesión", "Duración (min)", "Importe (€)", "Nota Sesión"]
    
    for col in columnas_hist:
        if col not in df_hist.columns: 
            df_hist[col] = None if col in ["Duración (min)", "Importe (€)", "Inicio de sesión", "Fin de sesión", "Fecha"] else ""
        
    df_hist = df_hist[columnas_hist]
    
    df_hist["Fecha"] = pd.to_datetime(df_hist["Fecha"], format="%d/%m/%Y", errors="coerce")
    df_hist["Duración (min)"] = pd.to_numeric(df_hist["Duración (min)"], errors="coerce")
    df_hist["Importe (€)"] = pd.to_numeric(df_hist["Importe (€)"], errors="coerce")
    
    def parse_time_safe(t):
        if pd.isna(t) or str(t).strip() in ["", "nan", "None", "NaT"]: return None
        try: return pd.to_datetime(str(t)).time()
        except: return None
        
    df_hist["Inicio de sesión"] = df_hist["Inicio de sesión"].apply(parse_time_safe)
    df_hist["Fin de sesión"] = df_hist["Fin de sesión"].apply(parse_time_safe)
    
    # --- FIX: Calcular duración automáticamente en la vista si hay horas ---
    for idx, row in df_hist.iterrows():
        ini = row.get('Inicio de sesión')
        fin = row.get('Fin de sesión')
        if pd.notnull(ini) and pd.notnull(fin):
            minutos = (fin.hour * 60 + fin.minute) - (ini.hour * 60 + ini.minute)
            if minutos < 0: minutos += 24 * 60
            df_hist.at[idx, 'Duración (min)'] = minutos

    st.markdown("💡 *Nota: Si indicas **Inicio** y **Fin**, la **Duración** se calculará sola al guardar. El **Importe** se rellenará automáticamente al guardar si seleccionas un Servicio y lo dejas vacío.*")
    
    ed_hist = st.data_editor(
        df_hist, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"ed_hist_{prefix}_{m_id}",
        column_config={
            "Fecha": st.column_config.DateColumn("Fecha (D/M/A)", format="DD/MM/YYYY"),
            "Trabajo / Servicio": st.column_config.SelectboxColumn("Servicio Realizado", options=[""] + servicios_lista),
            "Tratamiento": st.column_config.TextColumn("Tratamiento"),
            "Peluquera/o": st.column_config.SelectboxColumn("Realizado por", options=[""] + empleados_lista),
            "Inicio de sesión": st.column_config.TimeColumn("Inicio", format="HH:mm"),
            "Fin de sesión": st.column_config.TimeColumn("Fin", format="HH:mm"),
            "Duración (min)": st.column_config.NumberColumn("Duración (Auto)", min_value=0, step=5, help="Se calcula automáticamente al guardar si indicas Inicio y Fin"),
            "Importe (€)": st.column_config.NumberColumn("Importe Cobrado (€)", format="%.2f", min_value=0.0),
            "Nota Sesión": st.column_config.TextColumn("Nota Sesión")
        }
    )
    
    st.markdown("#### 📝 Diario y Observaciones Clínicas")
    obs_actuales = strip_pref(m_data.get('observaciones', ''))
    notas_clinicas = st.text_area("Anota aquí alergias, estado de piel, carácter o recordatorios extensos:", value=obs_actuales, height=120, key=f"notas_clinicas_{prefix}_{m_id}")
    
    if st.button(f"💾 Guardar Historial y Notas de {m_nombre}", type="primary", key=f"btn_hist_{prefix}_{m_id}"):
        df_save = ed_hist.copy()
        df_save['Fecha'] = pd.to_datetime(df_save['Fecha'], errors='coerce').dt.strftime('%d/%m/%Y').fillna("")
        
        for idx, row in df_save.iterrows():
            ini = row.get('Inicio de sesión')
            fin = row.get('Fin de sesión')
            
            ini_str = ini.strftime('%H:%M') if hasattr(ini, 'strftime') else (str(ini) if pd.notnull(ini) and str(ini).strip() not in ["", "None", "NaT"] else "")
            fin_str = fin.strftime('%H:%M') if hasattr(fin, 'strftime') else (str(fin) if pd.notnull(fin) and str(fin).strip() not in ["", "None", "NaT"] else "")
            
            df_save.at[idx, 'Inicio de sesión'] = ini_str
            df_save.at[idx, 'Fin de sesión'] = fin_str
            
            if ini_str and fin_str:
                try:
                    h_i, m_i = map(int, ini_str.split(':')[:2])
                    h_f, m_f = map(int, fin_str.split(':')[:2])
                    minutos = (h_f * 60 + m_f) - (h_i * 60 + m_i)
                    if minutos < 0: minutos += 24 * 60
                    df_save.at[idx, 'Duración (min)'] = minutos
                except:
                    pass
                    
            # AUTO PRECIO Y DESCUENTO MANTENIMIENTO
            srv = row.get('Trabajo / Servicio')
            imp = row.get('Importe (€)')
            if srv in precios_servicios and (pd.isna(imp) or str(imp).strip() == "" or float(imp) == 0.0):
                precio_base = float(precios_servicios[srv])
                
                # Detectar si aplica descuento por mantenimiento (< 60 días desde última cita)
                if srv != "Otro":
                    fecha_actual_str = df_save.at[idx, 'Fecha']
                    try:
                        if fecha_actual_str:
                            fecha_actual_dt = pd.to_datetime(fecha_actual_str, format='%d/%m/%Y')
                            prev_dates = []
                            for i, r in df_save.iterrows():
                                if i != idx and str(r.get('Trabajo / Servicio')).strip() not in ["", "Otro", "None"]:
                                    f_str = str(r.get('Fecha')).strip()
                                    if f_str:
                                        fd = pd.to_datetime(f_str, format='%d/%m/%Y')
                                        if fd < fecha_actual_dt:
                                            prev_dates.append(fd)
                            
                            if prev_dates:
                                last_visit = max(prev_dates)
                                days_diff = (fecha_actual_dt - last_visit).days
                                if 0 < days_diff <= 60:
                                    precio_base = round(precio_base * 0.90, 2)
                                    ahorro = round(float(precios_servicios[srv]) - precio_base, 2)
                                    
                                    nota_act = str(df_save.at[idx, 'Nota Sesión']).strip()
                                    if nota_act == "None" or nota_act == "nan": nota_act = ""
                                    nota_desc = f"[Desc. 10% (Visita < 2 meses) aplicado. Ahorro: {ahorro}€]"
                                    if nota_desc not in nota_act:
                                        df_save.at[idx, 'Nota Sesión'] = f"{nota_act} {nota_desc}".strip()
                                        st.success(f"🎉 ¡Descuento por Visita Frecuente (< 2 meses) del 10% aplicado automáticamente a la sesión del {fecha_actual_str}! Ahorro: {ahorro}€")
                    except Exception as e:
                        pass
                
                df_save.at[idx, 'Importe (€)'] = precio_base
                    
        df_save = df_save.fillna("")
        
        pref_actual = get_pref(m_data.get('observaciones', ''))
        final_obs = f"[Pref: {pref_actual}] {notas_clinicas}".strip() if pref_actual != "Cualquiera" else notas_clinicas
        
        client.table("mascotas").update({
            "historial_trabajos": df_save.to_dict(orient='records'),
            "observaciones": final_obs
        }).eq("id", m_id).execute()
        
        st.success("Historial y notas actualizados correctamente."); time.sleep(0.5); st.rerun()
        
    st.markdown("---")
    st.markdown("#### 🚫 Historial de Cancelaciones")
    res_canc = client.table("citas").select("fecha_hora, servicio").eq("mascotas_id", m_id).like("servicio", "%[ESTADO: Cancelada]%").execute()
    if res_canc.data:
        st.warning(f"⚠️ **ALERTA DE POLÍTICA:** Esta mascota tiene **{len(res_canc.data)}** cancelación(es) registrada(s).")
        canc_lista = []
        for cx in res_canc.data:
            dt_c = pd.to_datetime(cx['fecha_hora'])
            import re
            s_raw = cx.get('servicio', '')
            s_clean = re.sub(r'\[ESTADO:\s*Cancelada\]\s*', '', s_raw).strip()
            canc_lista.append({
                "Fecha de la Cita": dt_c.strftime('%d/%m/%Y %H:%M'),
                "Servicio Cancelado": s_clean
            })
        st.dataframe(pd.DataFrame(canc_lista), hide_index=True, use_container_width=True)
    else:
        st.info("Esta mascota no tiene cancelaciones. ¡Cliente excelente! ⭐")
    st.markdown("---")
