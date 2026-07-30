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

@st.cache_data(show_spinner=False, ttl=300)
def fetch_ficha_alerts_cached(_client, v, mid, hoy):
    try:
        r1 = _client.table("citas").select("fecha_hora, servicio").eq("mascotas_id", mid).lt("fecha_hora", hoy).or_("servicio.ilike.%[ESTADO: Confirmada]%,servicio.ilike.%[ESTADO: Asistió]%,servicio.ilike.%[ESTADO: Pendiente]%").execute().data
        r2 = _client.table("citas").select("fecha_hora, servicio").eq("mascotas_id", mid).or_("servicio.ilike.%[ESTADO: Cancelada]%,servicio.ilike.%[ESTADO: No presentado]%,servicio.ilike.%[ESTADO: Anulada]%,servicio.ilike.%[ESTADO: Cambio (mismo día)]%").execute().data
        return r1, r2
    except: return [], []

@st.cache_data(show_spinner=False, ttl=300)
def fetch_igic_tipo_cached(_client, nombre):
    try:
        return _client.table("productos").select("igic_tipo").eq("nombre", nombre).execute().data
    except:
        return []

@st.cache_data(show_spinner=False, ttl=300)
def fetch_citas_mascota_cached(_client, mascotas_id):
    try:
        return _client.table("citas").select("fecha_hora, servicio").eq("mascotas_id", mascotas_id).execute().data
    except:
        return []

def limpiar_cache_ficha_clinica():
    fetch_ficha_alerts_cached.clear()
    fetch_igic_tipo_cached.clear()
    fetch_citas_mascota_cached.clear()

def mostrar_ficha_clinica(m_id, m_nombre, m_data, prefix, client, servicios_lista, empleados_lista, precios_servicios):
    """Renderiza la ficha clínica, el historial y el sistema inteligente de reservas."""
    st.markdown(f"#### 📖 Ficha e Historial Clínico/Peluquería: **{m_nombre}**")
    
    # --- ALERTA CITA CONFIRMADA SIN HISTORIAL ---
    hoy_str = str(date.today())
    r_alertas, r_canc = fetch_ficha_alerts_cached(client, st.session_state.get('db_version', 0), m_id, hoy_str)
    
    historial = m_data.get('historial_trabajos')
    if not isinstance(historial, list): historial = []
    
    if r_alertas:
        citas_faltantes = []
        for c in r_alertas:
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
    
    # --- MIGRACIÓN DE COLUMNA ANTIGUA A NUEVAS ---
    if "Importe (€)" in df_hist.columns:
        if "Precio Base (€)" not in df_hist.columns:
            df_hist["Precio Base (€)"] = df_hist["Importe (€)"]
        if "Precio con desc. (€)" not in df_hist.columns:
            df_hist["Precio con desc. (€)"] = df_hist["Importe (€)"]
            
    columnas_hist = ["Fecha", "Trabajo / Servicio", "Tratamiento", "Peluquera/o", "Inicio de sesión", "Fin de sesión", "Duración (min)", "Precio Base (€)", "Precio con desc. (€)", "Nota Sesión", "Extras"]
    
    for col in columnas_hist:
        if col not in df_hist.columns: 
            if col == "Extras":
                df_hist[col] = [[] for _ in range(len(df_hist))]
            else:
                df_hist[col] = None if col in ["Duración (min)", "Precio Base (€)", "Precio con desc. (€)", "Inicio de sesión", "Fin de sesión", "Fecha"] else ""
        
    df_hist = df_hist[columnas_hist]
    
    df_hist["Fecha"] = pd.to_datetime(df_hist["Fecha"], format="%d/%m/%Y", errors="coerce")
    df_hist["Duración (min)"] = pd.to_numeric(df_hist["Duración (min)"], errors="coerce")
    df_hist["Precio Base (€)"] = pd.to_numeric(df_hist["Precio Base (€)"], errors="coerce")
    df_hist["Precio con desc. (€)"] = pd.to_numeric(df_hist["Precio con desc. (€)"], errors="coerce")
    # --- SANITIZACIÓN EXTREMA DE TIPOS PARA PYARROW ---
    df_hist["Fecha"] = pd.to_datetime(df_hist["Fecha"], format="%d/%m/%Y", errors="coerce").dt.date
    df_hist["Fecha"] = df_hist["Fecha"].apply(lambda x: x if pd.notnull(x) else None)
    
    for col in ["Duración (min)", "Precio Base (€)", "Precio con desc. (€)"]:
        df_hist[col] = pd.to_numeric(df_hist[col], errors="coerce").astype("float64")
    
    def parse_time_safe(t):
        if pd.isna(t) or str(t).strip() in ["", "nan", "None", "NaT"]: return None
        try: return pd.to_datetime(str(t)).time()
        except: return None
        
    df_hist["Inicio de sesión"] = df_hist["Inicio de sesión"].apply(parse_time_safe)
    df_hist["Fin de sesión"] = df_hist["Fin de sesión"].apply(parse_time_safe)
    
    for col in ["Trabajo / Servicio", "Tratamiento", "Peluquera/o", "Nota Sesión"]:
        df_hist[col] = df_hist[col].apply(lambda x: str(x).strip() if pd.notnull(x) and str(x).lower() not in ["nan", "none", "nat"] else "")
    
    # --- FIX: Calcular duración automáticamente en la vista si hay horas ---
    for idx, row in df_hist.iterrows():
        ini = row.get('Inicio de sesión')
        fin = row.get('Fin de sesión')
        if pd.notnull(ini) and pd.notnull(fin):
            minutos = (fin.hour * 60 + fin.minute) - (ini.hour * 60 + ini.minute)
            if minutos < 0: minutos += 24 * 60
            df_hist.at[idx, 'Duración (min)'] = minutos
        if ini and fin and hasattr(ini, 'hour') and hasattr(fin, 'hour'):
            try:
                minutos = (fin.hour * 60 + fin.minute) - (ini.hour * 60 + ini.minute)
                if minutos < 0: minutos += 24 * 60
                df_hist.at[idx, 'Duración (min)'] = minutos
            except: pass

    # Evitar que Streamlit oculte servicios antiguos que ya no coinciden con el catálogo
    servicios_usados = [s for s in df_hist["Trabajo / Servicio"].dropna().unique().tolist() if str(s).strip() != ""]
    opciones_seguras = [""] + servicios_lista + [s for s in servicios_usados if s not in servicios_lista]

    st.markdown("💡 *Nota: Si seleccionas un **Servicio**, los Precios se calcularán solos (si pones el precio a 0 se actualizará a la tarifa del catálogo).*")
    
    df_visual = df_hist.drop(columns=["Extras"]) if "Extras" in df_hist.columns else df_hist
    
    ed_hist_visual = st.data_editor(
        df_visual, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"ed_hist_{prefix}_{m_id}",
        column_config={
            "Fecha": st.column_config.DateColumn("Fecha (D/M/A)", format="DD/MM/YYYY"),
            "Trabajo / Servicio": st.column_config.SelectboxColumn("Servicio Realizado", options=opciones_seguras),
            "Tratamiento": st.column_config.TextColumn("Tratamiento"),
            "Peluquera/o": st.column_config.SelectboxColumn("Realizado por", options=[""] + empleados_lista),
            "Inicio de sesión": st.column_config.TimeColumn("Inicio", format="HH:mm"),
            "Fin de sesión": st.column_config.TimeColumn("Fin", format="HH:mm"),
            "Duración (min)": st.column_config.NumberColumn("Duración (Auto)", min_value=0, step=5, disabled=True, help="Se calcula sola al guardar si indicas Inicio y Fin"),
            "Precio Base (€)": st.column_config.NumberColumn("Precio Catálogo (€)", format="%.2f", min_value=0.0),
            "Precio con desc. (€)": st.column_config.NumberColumn("Precio Final (€)", format="%.2f", min_value=0.0),
            "Nota Sesión": st.column_config.TextColumn("Nota Sesión")
        }
    )
    
    # Restaurar la columna Extras sin que PyArrow la dibuje
    ed_hist = ed_hist_visual.copy()
    if "Extras" in df_hist.columns:
        ed_hist["Extras"] = ed_hist.index.map(lambda i: df_hist.at[i, "Extras"] if i in df_hist.index else [])
    else:
        ed_hist["Extras"] = [[] for _ in range(len(ed_hist))]

    with st.expander("✨ Añadir / Ver Extras de la Sesión (Nudos, Mascarillas...)", expanded=False):
        fechas_disponibles = pd.to_datetime(df_hist['Fecha'], errors='coerce').dropna().dt.strftime('%d/%m/%Y').unique().tolist()
        if fechas_disponibles:
            f_sel_extra = st.selectbox("Selecciona la fecha de la sesión:", fechas_disponibles, key=f"f_ext_{prefix}_{m_id}")
            
            idx_obj = df_hist[pd.to_datetime(df_hist['Fecha'], errors='coerce').dt.strftime('%d/%m/%Y') == f_sel_extra].index[-1]
            lista_extras_actual = df_hist.at[idx_obj, 'Extras']
            if not isinstance(lista_extras_actual, list): lista_extras_actual = []
            
            if lista_extras_actual:
                st.markdown("**Extras actuales en esta sesión:**")
                for i, e in enumerate(lista_extras_actual):
                    col_txt, col_btn = st.columns([5, 1], vertical_alignment="center")
                    with col_txt:
                        st.markdown(f"- {e.get('Servicio')} | {e.get('Minutos', 0)} min | {e.get('Precio', 0):.2f}€ (IGIC: {e.get('IGIC', 0)}%)")
                    with col_btn:
                        if st.button("🗑️", key=f"del_ext_{prefix}_{m_id}_{f_sel_extra.replace('/', '')}_{i}"):
                            hist_to_save = ed_hist.copy()
                            idx_to_update = hist_to_save[pd.to_datetime(hist_to_save['Fecha'], errors='coerce').dt.strftime('%d/%m/%Y') == f_sel_extra].index[-1]
                            lista_ext_save = hist_to_save.at[idx_to_update, 'Extras']
                            
                            if isinstance(lista_ext_save, list) and i < len(lista_ext_save):
                                extra_borrado = lista_ext_save.pop(i)
                                precio_restar = float(extra_borrado.get('Precio', 0.0))
                                
                                precio_desc_actual = float(hist_to_save.at[idx_to_update, 'Precio con desc. (€)'] or 0.0)
                                hist_to_save.at[idx_to_update, 'Precio con desc. (€)'] = max(0.0, precio_desc_actual - precio_restar)
                                hist_to_save.at[idx_to_update, 'Extras'] = lista_ext_save
                                
                                hist_to_save['Fecha'] = pd.to_datetime(hist_to_save['Fecha'], errors='coerce').dt.strftime('%d/%m/%Y').fillna("")
                                for ix, r in hist_to_save.iterrows():
                                    for time_col in ['Inicio de sesión', 'Fin de sesión']:
                                        val = r.get(time_col)
                                        val_str = val.strftime('%H:%M') if hasattr(val, 'strftime') else (str(val) if pd.notnull(val) and str(val).strip() not in ["", "None", "NaT"] else "")
                                        hist_to_save.at[ix, time_col] = val_str
                                
                                hist_to_save = hist_to_save.fillna("")
                                client.table("mascotas").update({"historial_trabajos": hist_to_save.to_dict(orient='records')}).eq("id", m_id).execute()
                                
                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                st.success("Extra eliminado."); time.sleep(0.5)
                                limpiar_cache_ficha_clinica()
                                st.rerun()
            
            st.markdown("---")
            c_e1, c_e2, c_e3 = st.columns([2, 1, 1])
            with c_e1: 
                serv_extra = st.selectbox("Extra Aplicado", servicios_lista, key=f"se_ext_{prefix}_{m_id}")
            with c_e2: 
                h_ini_ext = st.time_input("Inicio Extra (Opcional)", value=None, key=f"hi_ext_{prefix}_{m_id}")
            with c_e3: 
                h_fin_ext = st.time_input("Fin Extra (Opcional)", value=None, key=f"hf_ext_{prefix}_{m_id}")
            
            if st.button("➕ Añadir Extra a la Sesión", use_container_width=True, key=f"btn_add_ext_{prefix}_{m_id}"):
                minutos_ext = 0
                if h_ini_ext and h_fin_ext:
                    minutos_ext = (h_fin_ext.hour * 60 + h_fin_ext.minute) - (h_ini_ext.hour * 60 + h_ini_ext.minute)
                    if minutos_ext < 0: minutos_ext += 24 * 60
                
                precio_ext = 0.0
                if serv_extra in precios_servicios:
                    precio_cat = float(precios_servicios[serv_extra])
                    if any(kw in serv_extra.lower() for kw in ["hora", "nudos", "agresivos", "nerviosos"]) and minutos_ext > 0:
                        precio_ext = round((precio_cat / 60) * minutos_ext, 2)
                    else:
                        precio_ext = precio_cat
                
                igic_ext = 7.0
                try:
                    data_igic = fetch_igic_tipo_cached(client, serv_extra)
                    if data_igic: igic_ext = float(data_igic[0].get('igic_tipo', 7.0))
                except: pass
                
                nuevo_extra = {"Servicio": serv_extra, "Minutos": minutos_ext, "Precio": precio_ext, "IGIC": igic_ext}
                
                hist_to_save = ed_hist.copy() # Tomamos lo que hay en el editor
                
                idx_to_update = hist_to_save[pd.to_datetime(hist_to_save['Fecha'], errors='coerce').dt.strftime('%d/%m/%Y') == f_sel_extra].index[-1]
                lista_ext_save = hist_to_save.at[idx_to_update, 'Extras']
                if not isinstance(lista_ext_save, list): lista_ext_save = []
                lista_ext_save.append(nuevo_extra)
                hist_to_save.at[idx_to_update, 'Extras'] = lista_ext_save
                
                # Sumar el precio al total visual
                precio_desc_actual = float(hist_to_save.at[idx_to_update, 'Precio con desc. (€)'] or 0.0)
                hist_to_save.at[idx_to_update, 'Precio con desc. (€)'] = precio_desc_actual + precio_ext
                
                hist_to_save['Fecha'] = pd.to_datetime(hist_to_save['Fecha'], errors='coerce').dt.strftime('%d/%m/%Y').fillna("")
                for i, r in hist_to_save.iterrows():
                    for time_col in ['Inicio de sesión', 'Fin de sesión']:
                        val = r.get(time_col)
                        val_str = val.strftime('%H:%M') if hasattr(val, 'strftime') else (str(val) if pd.notnull(val) and str(val).strip() not in ["", "None", "NaT"] else "")
                        hist_to_save.at[i, time_col] = val_str
                
                hist_to_save = hist_to_save.fillna("")
                client.table("mascotas").update({"historial_trabajos": hist_to_save.to_dict(orient='records')}).eq("id", m_id).execute()
                
                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                st.success(f"Extra añadido."); time.sleep(1)
                limpiar_cache_ficha_clinica()
                st.rerun()
        else:
            st.info("⚠️ No hay sesiones guardadas en esta ficha. Para añadir un extra (nudos, mascarilla...), primero añade una fila en la tabla de arriba, pon la fecha, el servicio, dale a **'Guardar Historial'**, y luego vuelve aquí.")

    st.markdown("#### 📝 Diario y Observaciones Clínicas")
    obs_actuales = strip_pref(m_data.get('observaciones', ''))
    notas_clinicas = st.text_area("Anota aquí alergias, estado de piel, carácter o recordatorios extensos:", value=obs_actuales, height=120, key=f"notas_clinicas_{prefix}_{m_id}")
    
    if st.button(f"💾 Guardar Historial y Notas de {m_nombre}", type="primary", key=f"btn_hist_{prefix}_{m_id}"):
        df_save = ed_hist.copy()
        df_save['Fecha'] = pd.to_datetime(df_save['Fecha'], errors='coerce').dt.strftime('%d/%m/%Y').fillna("")
        
        # Obtener citas de la mascota para comprobar si hay "Oferta / Dto." en la agenda
        fechas_oferta = set()
        try:
            data_cp = fetch_citas_mascota_cached(client, m_id)
            if data_cp:
                for c_pet in data_cp:
                    if "[ESTADO: Oferta / Descuento]" in c_pet.get('servicio', ''):
                        try:
                            dt_str = c_pet['fecha_hora'][:10]
                            fechas_oferta.add(pd.to_datetime(dt_str).strftime('%d/%m/%Y'))
                        except: pass
        except: pass
        
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
            precio_base = row.get('Precio Base (€)')
            precio_desc = row.get('Precio con desc. (€)')
            
            if srv in precios_servicios:
                # Rellenar Precio Base si está vacío
                if pd.isna(precio_base) or str(precio_base).strip() == "" or float(precio_base or 0) == 0.0:
                    precio_cat = float(precios_servicios[srv])
                    minutos_calc = df_save.at[idx, 'Duración (min)']
                    
                    # Cálculo proporcional si el servicio es por hora (incluye palabras clave)
                    es_por_hora = any(kw in str(srv).lower() for kw in ["hora", "agresivos", "nerviosos", "extra nudos"])
                    
                    if es_por_hora and pd.notnull(minutos_calc) and float(minutos_calc) > 0:
                        precio_base = round((precio_cat / 60) * float(minutos_calc), 2)
                        nota_act = str(df_save.at[idx, 'Nota Sesión']).strip()
                        if nota_act == "None" or nota_act == "nan": nota_act = ""
                        nota_tiempo = f"[Calculado: {minutos_calc} min a {precio_cat}€/h]"
                        if nota_tiempo not in nota_act:
                            df_save.at[idx, 'Nota Sesión'] = f"{nota_act} {nota_tiempo}".strip()
                    else:
                        precio_base = precio_cat
                        
                    df_save.at[idx, 'Precio Base (€)'] = precio_base
                else:
                    precio_base = float(precio_base)
                    
        from core_ficha_clinica import aplicar_descuentos_fidelidad
        df_save, mensajes_exito = aplicar_descuentos_fidelidad(df_save, fechas_oferta)
        for msg in mensajes_exito:
            st.success(msg)
                    
        df_save = df_save.where(pd.notnull(df_save), None)
        # JSON-friendly: NaN → None; fechas/horas ya son str
        records = df_save.to_dict(orient='records')
        for rec in records:
            for k, v in list(rec.items()):
                if v is None or (isinstance(v, float) and pd.isna(v)):
                    rec[k] = None if k.startswith("Precio") or k.startswith("Duración") else ""
                elif hasattr(v, "item"):  # numpy scalars
                    try:
                        rec[k] = v.item()
                    except Exception:
                        rec[k] = str(v)
        
        pref_actual = get_pref(m_data.get('observaciones', ''))
        final_obs = f"[Pref: {pref_actual}] {notas_clinicas}".strip() if pref_actual != "Cualquiera" else notas_clinicas
        
        try:
            client.table("mascotas").update({
                "historial_trabajos": records,
                "observaciones": final_obs
            }).eq("id", m_id).execute()
            
            st.session_state.db_version = st.session_state.get('db_version', 0) + 1
            st.success("Historial y notas actualizados correctamente."); time.sleep(0.1)
            limpiar_cache_ficha_clinica()
            st.rerun()
        except Exception as e:
            st.error(f"No se pudo guardar la ficha clínica: {e}")
        
    st.markdown("---")
    st.markdown("#### 🚫 Historial de Cancelaciones y Plantones")
    if r_canc:
        st.warning(f"⚠️ **ALERTA DE POLÍTICA:** Esta mascota tiene **{len(r_canc)}** falta(s) (Cancelaciones / Cambios / Plantones).")
        canc_lista = []
        for cx in r_canc:
            dt_c = pd.to_datetime(cx['fecha_hora'])
            import re
            s_raw = cx.get('servicio', '')
            s_clean = re.sub(r'\[ESTADO:\s*.*?\]\s*', '', s_raw).strip()
            canc_lista.append({
                "Fecha de la Cita": dt_c.strftime('%d/%m/%Y %H:%M'),
                "Servicio Cancelado": s_clean
            })
        st.dataframe(pd.DataFrame(canc_lista), hide_index=True, use_container_width=True)
    else:
        st.info("Esta mascota no tiene cancelaciones. ¡Cliente excelente! ⭐")
    st.markdown("---")
