import streamlit as st
import pandas as pd
import time
import json
import urllib.parse
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re

def parsear_dias_reparto(texto):
    if not texto: return []
    texto = texto.lower()
    if "demanda" in texto or "sin especificar" in texto: return []
    dias = []
    if "lunes a viernes" in texto: return [0, 1, 2, 3, 4]
    if "lunes" in texto: dias.append(0)
    if "martes" in texto: dias.append(1)
    if "miercoles" in texto or "miércoles" in texto: dias.append(2)
    if "jueves" in texto: dias.append(3)
    if "viernes" in texto: dias.append(4)
    if "sabado" in texto or "sábado" in texto: dias.append(5)
    if "domingo" in texto: dias.append(6)
    return dias

def get_alertas_manuales(proveedores_data):
    ahora = datetime.now(ZoneInfo("Atlantic/Canary"))
    alertas = {"urgentes": [], "bajo_demanda": []}
    
    for p in proveedores_data:
        freq = p.get('frecuencia_reparto', '')
        dias_entrega = parsear_dias_reparto(freq)
        
        contacto = p.get('contacto', '')
        ultimo_manual_dt = None
        metodo_pedido = "Email"
        if contacto and contacto.strip():
            try:
                data = json.loads(contacto)
                if 'ultimo_manual' in data:
                    ultimo_manual_dt = datetime.fromisoformat(data['ultimo_manual'])
                    if ultimo_manual_dt.tzinfo is None:
                        ultimo_manual_dt = ultimo_manual_dt.replace(tzinfo=ZoneInfo("Atlantic/Canary"))
                if 'metodo_pedido' in data:
                    metodo_pedido = data['metodo_pedido']
            except: pass

        if not dias_entrega:
            alertas["bajo_demanda"].append({
                "id": p['id'], "proveedor": p.get('nombre_empresa', 'Desconocido'),
                "corte_dt": None, "ultimo_manual": ultimo_manual_dt, "frecuencia": freq,
                "metodo_pedido": metodo_pedido
            })
            continue
            
        hora_corte_str = p.get('hora_limite', '')
        m = re.search(r'(\d{1,2})', str(hora_corte_str))
        hora = 12
        if m: hora = int(m.group(1))
            
        for i in range(1, 8):
            dia_futuro = ahora + timedelta(days=i)
            if dia_futuro.weekday() in dias_entrega:
                dia_corte = dia_futuro - timedelta(days=1)
                while dia_corte.weekday() > 4:
                    dia_corte -= timedelta(days=1)
                
                corte_dt = dia_corte.replace(hour=hora, minute=0, second=0, microsecond=0)
                
                tiempo_hasta_corte = (corte_dt - ahora).total_seconds() / 3600
                
                # Show if within 30h of cutoff or up to 14h after cutoff
                if -14 <= tiempo_hasta_corte <= 30:
                    if ultimo_manual_dt and (ahora - ultimo_manual_dt).total_seconds() / 3600 < 48:
                        break
                    alertas["urgentes"].append({
                        "id": p['id'], "proveedor": p.get('nombre_empresa', 'Desconocido'),
                        "corte_dt": corte_dt, "ultimo_manual": ultimo_manual_dt,
                        "metodo_pedido": metodo_pedido
                    })
                break
    return alertas


@st.cache_data(show_spinner=False, ttl=300)
def fetch_proveedores(_client):
    return _client.table("proveedores").select("*").execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_pedidos_borrador_alertas(_client):
    return _client.table("pedidos_proveedores").select("id, proveedores(nombre_empresa, email, movil, frecuencia_reparto, hora_limite, contacto), productos").eq("estado", "Borrador").execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_productos_paginados(_client, offset):
    return _client.table("productos").select("id, sku, nombre, stock_actual, stock_minimo, cantidad_reponer, categoria").eq("categoria", "Producto").range(offset, offset + 999).execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_productos_proveedores_rels(_client):
    return _client.table("productos_proveedores").select("producto_id, proveedor_id, precio_coste").execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_pedidos_proveedor_borrador(_client, prov_id):
    return _client.table("pedidos_proveedores").select("id, productos").eq("proveedor_id", prov_id).eq("estado", "Borrador").execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_proveedores_id_nombre_reparto(_client):
    return _client.table("proveedores").select("id, nombre_empresa, frecuencia_reparto").execute()

@st.cache_data(show_spinner=False, ttl=300)
def fetch_pedidos_proveedores_desc(_client):
    return _client.table("pedidos_proveedores").select("*, proveedores(nombre_empresa, frecuencia_reparto, hora_limite, email, pedido_minimo)").order("created_at", desc=True).execute()

def limpiar_cache_proveedores():
    fetch_proveedores.clear()
    fetch_pedidos_borrador_alertas.clear()
    fetch_productos_paginados.clear()
    fetch_productos_proveedores_rels.clear()
    fetch_pedidos_proveedor_borrador.clear()
    fetch_proveedores_id_nombre_reparto.clear()
    fetch_pedidos_proveedores_desc.clear()

def render_pestana_proveedores(client):
    if 'llave_n_prov' not in st.session_state:
        st.session_state.llave_n_prov = 0
    if 'llave_n_art_ped' not in st.session_state:
        st.session_state.llave_n_art_ped = 0

    st.markdown("<h3 style='margin-top:-15px;'> Gestión de Proveedores y Pedidos</h3>", unsafe_allow_html=True)
    sub_prov, sub_pedidos = st.tabs(["🏢 Directorio de Proveedores", "📦 Gestión de Pedidos y Borradores"])
    
    with sub_prov:
        cp1, cp2 = st.columns([1, 2])
        with cp1:
            st.markdown("#### ➕ Nuevo Proveedor")
            with st.form("n_prov_full", clear_on_submit=True):
                st.markdown("**Datos Principales**")
                n_emp = st.text_input("Nombre Proveedor *", key=f"np_emp_{st.session_state.llave_n_prov}")
                c_np1, c_np2 = st.columns(2)
                with c_np1: n_cif = st.text_input("CIF / NIF", key=f"np_cif_{st.session_state.llave_n_prov}")
                with c_np2: n_tel = st.text_input("Teléfono Fijo", key=f"np_tel_{st.session_state.llave_n_prov}")
                
                c_np3, c_np4 = st.columns(2)
                with c_np3: n_mov = st.text_input("Móvil", key=f"np_mov_{st.session_state.llave_n_prov}")
                with c_np4: n_ema = st.text_input("Email", key=f"np_ema_{st.session_state.llave_n_prov}")
                
                st.markdown("**Ubicación Rápida**")
                n_dir = st.text_input("Dirección", key=f"np_dir_{st.session_state.llave_n_prov}")
                c_np5, c_np6 = st.columns(2)
                with c_np5: n_pob = st.text_input("Población", key=f"np_pob_{st.session_state.llave_n_prov}")
                with c_np6: n_pais = st.text_input("País", value="España - Islas Canarias", key=f"np_pais_{st.session_state.llave_n_prov}")
                
                n_frec = st.text_input("Días de Reparto", placeholder="Ej: Todos los días, Los martes, Bajo demanda...", value="Bajo demanda", key=f"np_frec_{st.session_state.llave_n_prov}")
                n_hora_input = st.time_input("Hora límite de pedido", value=None, key=f"np_hora_{st.session_state.llave_n_prov}")
                n_hora = n_hora_input.strftime('%H:%M') if n_hora_input else "Sin límite"
                
                c_np7, c_np8 = st.columns(2)
                with c_np7: n_min = st.number_input("Pedido Mínimo (€) portes", min_value=0.0, format="%.2f", step=0.01, key=f"np_min_{st.session_state.llave_n_prov}")
                with c_np8: n_metodo = st.selectbox("Método Pedido Preferido", ["Email", "WhatsApp", "Web/Plataforma B2B", "Llamada Telefónica", "Otro"], key=f"np_met_{st.session_state.llave_n_prov}")
                
                if st.form_submit_button("Guardar Proveedor", use_container_width=True, type="primary"):
                    if n_emp:
                        client.table("proveedores").insert({
                            "nombre_empresa": n_emp, "cif": n_cif,
                            "telefono": n_tel, "movil": n_mov, "email": n_ema,
                            "direccion": n_dir, "poblacion": n_pob, "pais": n_pais,
                            "frecuencia_reparto": n_frec, "hora_limite": n_hora,
                            "pedido_minimo": float(n_min),
                            "contacto": json.dumps({"metodo_pedido": n_metodo})
                        }).execute()
                        st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                        st.session_state.llave_n_prov += 1
                        st.success("Guardado"); time.sleep(0.5); limpiar_cache_proveedores(); st.rerun()
        with cp2:
            st.markdown("#### 📋 Directorio")
            res_p = fetch_proveedores(client)
            df_p = None
            ed_p = None
            if res_p.data:
                df_p = pd.DataFrame(res_p.data)
                
                # Aseguramos que las nuevas columnas existan en el DataFrame (por si no has corrido el SQL aún)
                for col in ['telefono', 'movil', 'email', 'direccion', 'poblacion', 'codigo_postal', 'provincia', 'pais', 'codigo_pais', 'idioma', 'forma_pago', 'persona_contacto', 'iban', 'swift', 'notas', 'contacto', 'pedido_minimo']:
                    if col not in df_p.columns: df_p[col] = ""
                    
                df_p_vista = df_p[['id', 'nombre_empresa', 'telefono', 'movil', 'email']].copy()
                df_p_vista.insert(0, "Borrar", False)
                df_p_vista.insert(0, "Ver Ficha", False)
                
                st.markdown("💡 *Marca **'👁️ Ver Ficha'** para acceder a los datos. Marca **'🗑️ Borrar'** para eliminar el proveedor.*")
                
                ed_p = st.data_editor(
                    df_p_vista, hide_index=True, use_container_width=True, key="ed_prov", height=250,
                    column_config={
                        "Ver Ficha": st.column_config.CheckboxColumn("👁️ Ver Ficha", default=False),
                        "Borrar": st.column_config.CheckboxColumn("🗑️ Borrar", default=False),
                        "id": None, "nombre_empresa": "Proveedor", "movil": "Móvil",
                        "telefono": "Teléfono Fijo", "email": "Email"
                    }
                )
                
                filas_borrar = ed_p[ed_p["Borrar"] == True]
                if not filas_borrar.empty:
                    st.error(f"⚠️ Has marcado {len(filas_borrar)} proveedor(es) para eliminar.")
                    if st.button("🚨 CONFIRMAR ELIMINACIÓN", type="primary", use_container_width=True):
                        errores = []
                        for _, row in filas_borrar.iterrows():
                            try:
                                client.table("productos_proveedores").delete().eq("proveedor_id", row['id']).execute()
                                client.table("pedidos_proveedores").delete().eq("proveedor_id", row['id']).execute()
                                client.table("proveedores").delete().eq("id", row['id']).execute()
                            except Exception as e:
                                errores.append(str(row['nombre_empresa']))
                        
                        if errores:
                            st.error(f"⚠️ No se pudieron eliminar los siguientes proveedores porque tienen compras o pedidos asociados en el historial: {', '.join(errores)}. Por favor, elimine los registros vinculados primero o edite el proveedor en su lugar.")
                        else:
                            st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                            st.success("Proveedor(es) eliminado(s) correctamente."); time.sleep(1.5); limpiar_cache_proveedores(); st.rerun()

                if st.button("💾 Guardar Cambios Rápidos", type="primary"):
                    filas_validas = ed_p[ed_p["Borrar"] == False]
                    for _, row in filas_validas.iterrows():
                        if pd.notna(row['id']):
                            client.table("proveedores").update({
                                "nombre_empresa": str(row['nombre_empresa']),
                                "telefono": str(row['telefono']), "movil": str(row.get('movil', '')), "email": str(row['email'])
                            }).eq("id", row['id']).execute()
                    st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                    st.success("Directorio actualizado."); time.sleep(0.5); limpiar_cache_proveedores(); st.rerun()
                    
        # --- FICHA COMPLETA DEL PROVEEDOR ---
        if df_p is not None and ed_p is not None:
            filas_ver = ed_p[ed_p["Ver Ficha"] == True]
            if not filas_ver.empty:
                p_id = filas_ver.iloc[0]['id']
                p_data = df_p[df_p['id'] == p_id].iloc[0]
                
                st.markdown("---")
                st.markdown(f"#### 🏢 Ficha Completa: **{p_data['nombre_empresa']}**")
                
                # Mostrar datos antiguos si existen para que el usuario pueda copiarlos
                if p_data.get('contacto') and str(p_data['contacto']).strip() and str(p_data['contacto']).strip() != "nan":
                    st.caption(f"💾 *Información antigua registrada:* {p_data['contacto']}")
                
                with st.form(f"ficha_prov_{p_id}", border=True):
                    st.markdown("**1. Información Fiscal y de Contacto**")
                    cf1, cf2, cf3 = st.columns([1.5, 1, 1])
                    with cf1: f_nom = st.text_input("Nombre Proveedor *", value=p_data.get('nombre_empresa',''))
                    with cf2: f_cif = st.text_input("CIF / NIF", value=p_data.get('cif',''))
                    with cf3: f_per = st.text_input("Persona de Contacto", value=p_data.get('persona_contacto',''))
                    
                    cf4, cf5, cf6 = st.columns(3)
                    with cf4: f_tel = st.text_input("Teléfono Fijo", value=p_data.get('telefono',''))
                    with cf5: f_mov = st.text_input("Móvil", value=p_data.get('movil',''))
                    with cf6: f_ema = st.text_input("Email", value=p_data.get('email',''))
                    
                    st.markdown("**2. Ubicación**")
                    f_dir = st.text_input("Dirección Completa", value=p_data.get('direccion',''))
                    
                    cf7, cf8, cf9 = st.columns(3)
                    with cf7: f_pob = st.text_input("Población", value=p_data.get('poblacion',''))
                    with cf8: f_cp = st.text_input("Código Postal", value=p_data.get('codigo_postal',''))
                    with cf9: f_prov = st.text_input("Provincia", value=p_data.get('provincia',''))
                    
                    cf10, cf11, cf12, cf16, cf17 = st.columns(5)
                    with cf10: f_pais = st.text_input("País", value=p_data.get('pais',''))
                    with cf11: f_cod_pais = st.text_input("Cód. País", value=p_data.get('codigo_pais',''))
                    with cf12: f_idioma = st.text_input("Idioma", value=p_data.get('idioma',''))
                    with cf16: f_frec = st.text_input("Días de Envío", value=p_data.get('frecuencia_reparto','Bajo demanda'))
                    with cf17: f_hora = st.text_input("Hora de Corte", value=p_data.get('hora_limite','Sin límite'))
                    
                    metodo_actual = "Email"
                    contacto_json = {}
                    if p_data.get('contacto') and str(p_data['contacto']).strip() and str(p_data['contacto']).strip() != "nan":
                        try:
                            contacto_json = json.loads(str(p_data['contacto']))
                            metodo_actual = contacto_json.get("metodo_pedido", "Email")
                        except: pass
                        
                    st.markdown("**3. Facturación y Notas**")
                    cf13, cf14, cf15, cf18, cf19 = st.columns([1, 1.5, 1, 1, 1.5])
                    with cf13: f_fpago = st.text_input("Forma de Pago", value=p_data.get('forma_pago',''))
                    with cf14: f_iban = st.text_input("IBAN", value=p_data.get('iban',''))
                    with cf15: f_swift = st.text_input("SWIFT", value=p_data.get('swift',''))
                    with cf18: f_min = st.number_input("Pedido Mínimo (€)", value=float(p_data.get('pedido_minimo', 0.0) if pd.notna(p_data.get('pedido_minimo')) else 0.0), step=0.01, format="%.2f")
                    with cf19: 
                        opciones_metodo = ["Email", "WhatsApp", "Web/Plataforma B2B", "Llamada Telefónica", "Otro"]
                        idx_met = opciones_metodo.index(metodo_actual) if metodo_actual in opciones_metodo else 0
                        f_metodo = st.selectbox("Método Pedido", opciones_metodo, index=idx_met)
                    
                    f_not = st.text_area("Fax / Otras Notas / Observaciones", value=p_data.get('notas',''))
                    
                    if st.form_submit_button("💾 Guardar Ficha Completa", type="primary", use_container_width=True):
                        if f_nom:
                            contacto_json["metodo_pedido"] = f_metodo
                            client.table("proveedores").update({
                                "nombre_empresa": f_nom, "cif": f_cif, "persona_contacto": f_per,
                                "telefono": f_tel, "movil": f_mov, "email": f_ema, "direccion": f_dir,
                                "poblacion": f_pob, "codigo_postal": f_cp, "provincia": f_prov,
                                "pais": f_pais, "frecuencia_reparto": f_frec, "hora_limite": f_hora,
                                "forma_pago": f_fpago, "iban": f_iban, "swift": f_swift, "notas": f_not,
                                "pedido_minimo": float(f_min),
                                "contacto": json.dumps(contacto_json)
                            }).eq("id", p_id).execute()
                            st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                            st.success("Ficha del proveedor actualizada correctamente."); time.sleep(0.5); limpiar_cache_proveedores(); st.rerun()
                        else:
                            st.error("El nombre de la empresa es obligatorio.")

    with sub_pedidos:
        st.markdown("#### ⏰ Alertas de Pedidos Manuales")
        st.info("Recordatorios calculados automáticamente en base a los días de reparto y horas de corte de cada proveedor. No interfiere con los borradores automáticos.")
        
        res_provs_alertas = fetch_proveedores(client)
        if res_provs_alertas.data:
            alertas = get_alertas_manuales(res_provs_alertas.data)
            
            if alertas["urgentes"]:
                for a in alertas["urgentes"]:
                    corte_str = a['corte_dt'].strftime('%d/%m/%Y a las %H:%M')
                    ult = a['ultimo_manual'].strftime('%d/%m/%Y %H:%M') if a['ultimo_manual'] else "Nunca registrado"
                    
                    st.error(f"⚠️ **{a['proveedor']}** (Vía: {a['metodo_pedido']}) - ⏳ Límite para pedir: **{corte_str}**")
                    ca1, ca2 = st.columns([2, 1], vertical_alignment="center")
                    with ca1:
                        st.caption(f"Último pedido registrado: {ult}")
                    with ca2:
                        if st.button(f"✅ Marcar Pedido Realizado", key=f"btn_manual_urg_{a['id']}", use_container_width=True):
                            nuevo_contacto = json.dumps({
                                "ultimo_manual": datetime.now(ZoneInfo("Atlantic/Canary")).isoformat(),
                                "metodo_pedido": a['metodo_pedido']
                            })
                            client.table("proveedores").update({"contacto": nuevo_contacto}).eq("id", a['id']).execute()
                            st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                            st.success("¡Registrado!")
                            time.sleep(0.5)
                            limpiar_cache_proveedores()
                            st.rerun()
            else:
                st.success("✨ No hay alertas de pedidos manuales urgentes para hoy o mañana.")
                
            if alertas["bajo_demanda"]:
                with st.expander("📦 Proveedores Bajo Demanda / Sin Día Fijo", expanded=False):
                    for a in alertas["bajo_demanda"]:
                        ult = a['ultimo_manual'].strftime('%d/%m/%Y %H:%M') if a['ultimo_manual'] else "Nunca registrado"
                        col1, col2 = st.columns([2, 1], vertical_alignment="center")
                        with col1:
                            st.markdown(f"**{a['proveedor']}** (Vía: {a['metodo_pedido']}) - _{a['frecuencia']}_")
                            st.caption(f"Último pedido registrado: {ult}")
                        with col2:
                            if st.button(f"✅ Registrar Pedido Libre", key=f"btn_manual_bd_{a['id']}", use_container_width=True):
                                nuevo_contacto = json.dumps({
                                    "ultimo_manual": datetime.now(ZoneInfo("Atlantic/Canary")).isoformat(),
                                    "metodo_pedido": a['metodo_pedido']
                                })
                                client.table("proveedores").update({"contacto": nuevo_contacto}).eq("id", a['id']).execute()
                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                st.success("¡Registrado!")
                                time.sleep(0.5)
                                limpiar_cache_proveedores()
                                st.rerun()
        st.markdown("---")

        st.markdown("#### 📧 Centro de Envíos (Borradores Automáticos)")
        st.info("Revisa aquí rápidamente los borradores pendientes de enviar a tus proveedores y su hora de corte.")
        try:
            res_alertas = fetch_pedidos_borrador_alertas(client)
            if res_alertas.data:
                alertas_list = []
                for p in res_alertas.data:
                    prov_info = p.get('proveedores', {}) or {}
                    nombre_prov = prov_info.get('nombre_empresa', 'Desconocido')
                    email_prov = prov_info.get('email', '')
                    hora_corte = prov_info.get('hora_limite', 'Sin límite')
                    dias_rep = prov_info.get('frecuencia_reparto', 'Bajo demanda')
                    
                    prods = p.get('productos', [])
                    num_arts = len(prods) if isinstance(prods, list) else 0
                    
                    texto_pedido = f"Estimado/a comercial de {nombre_prov},\n\nNos ponemos en contacto desde Animalarium para remitirles nuestro nuevo pedido de reposición.\n\nA continuación, detallamos los artículos y cantidades solicitadas:\n\n"
                    if isinstance(prods, list):
                        for art in prods:
                            texto_pedido += f"• {art.get('Cantidad', 1)} uds. - {art.get('Producto', '')}\n"
                    texto_pedido += "\nQuedamos a la espera de su confirmación y de la fecha estimada de entrega.\n\nAtentamente,\nEl equipo de Animalarium\nC/ José Hernández Alfonso, 26\n38009 S/C de Tenerife"
                    
                    prov_contacto = prov_info.get('contacto', '')
                    metodo_pedido = "Email"
                    if prov_contacto and str(prov_contacto).strip() and str(prov_contacto).strip() != "nan":
                        try:
                            metodo_pedido = json.loads(str(prov_contacto)).get("metodo_pedido", "Email")
                        except: pass
                        
                    movil_prov = str(prov_info.get('movil', '')).strip()

                    link_envio = None
                    if metodo_pedido == "WhatsApp" and movil_prov and movil_prov != "nan":
                        num = re.sub(r'\D', '', movil_prov)
                        if len(num) == 9 and (num.startswith('6') or num.startswith('7')): num = "34" + num
                        link_envio = f"https://wa.me/{num}?text={urllib.parse.quote(texto_pedido)}"
                    elif email_prov and str(email_prov) != "nan" and metodo_pedido != "Llamada Telefónica":
                        link_envio = f"mailto:{email_prov}?subject=Pedido%20Animalarium&body={urllib.parse.quote(texto_pedido)}"
                    elif metodo_pedido == "Llamada Telefónica" and movil_prov and movil_prov != "nan":
                        link_envio = f"tel:{movil_prov}"
                        
                    alertas_list.append({
                        "Borrador Nº": p['id'],
                        "Proveedor": f"{nombre_prov} ({metodo_pedido})",
                        "Días Envío": dias_rep,
                        "Hora Límite": hora_corte,
                        "Artículos": num_arts,
                        "Acción Rápida": link_envio
                    })
                    
                df_alertas_ped = pd.DataFrame(alertas_list)
                st.warning(f"⚠️ Tienes **{len(alertas_list)}** borrador(es) pendiente(s) de revisar y enviar.")
                st.dataframe(
                    df_alertas_ped, use_container_width=True, hide_index=True,
                    column_config={"Acción Rápida": st.column_config.LinkColumn("🚀 Enviar Pedido", display_text="Abrir Envío")}
                )
            else:
                st.success("✨ ¡Todo al día! No tienes borradores pendientes de enviar a proveedores.")
        except Exception as e: pass
        st.markdown("---")

        # --- ALERTA DE STOCK BAJO E INTELIGENCIA DE REPOSICIÓN ---
        all_prods = []
        offset = 0
        while True:
            r_prod = fetch_productos_paginados(client, offset)
            if r_prod.data:
                all_prods.extend(r_prod.data)
                if len(r_prod.data) < 1000: break
                offset += 1000
            else: break
        df_solo_productos = pd.DataFrame(all_prods) if all_prods else pd.DataFrame()
        if not df_solo_productos.empty:
            if 'stock_minimo' not in df_solo_productos.columns: df_solo_productos['stock_minimo'] = 2
            if 'cantidad_reponer' not in df_solo_productos.columns: df_solo_productos['cantidad_reponer'] = 5
            
            # Forzamos conversión a número por seguridad y aplicamos la regla: Ignorar si cantidad_reponer es 0
            df_solo_productos['cantidad_reponer'] = pd.to_numeric(df_solo_productos['cantidad_reponer'], errors='coerce').fillna(0)
            df_bajo_stock = df_solo_productos[(df_solo_productos['cantidad_reponer'] > 0) & (df_solo_productos['stock_actual'] <= df_solo_productos['stock_minimo'])].sort_values(by="stock_actual")
            
            if not df_bajo_stock.empty:
                st.warning(f"⚠️ **ATENCIÓN: Tienes {len(df_bajo_stock)} producto(s) por debajo de su stock mínimo.**")
                with st.expander("👀 Ver y editar lista de reposición sugerida", expanded=False):
                    df_bajo_stock_vista = df_bajo_stock[['id', 'sku', 'nombre', 'stock_actual', 'stock_minimo', 'cantidad_reponer']].copy()
                    df_bajo_stock_vista.insert(0, "Pedir", True)
                    st.markdown("<p style='font-size:14px;'>Revisa los productos sugeridos. <b>Desmarca</b> aquellos que no quieras mandar a pedir en este momento.</p>", unsafe_allow_html=True)
                    ed_bajo_stock = st.data_editor(
                        df_bajo_stock_vista, hide_index=True, use_container_width=True,
                        column_config={
                            "Pedir": st.column_config.CheckboxColumn("✅ Pedir", default=True),
                            "id": None, "sku": "SKU", "nombre": "Producto", "stock_actual": "Stock",
                            "stock_minimo": "Mínimo", "cantidad_reponer": "Cant. Reponer"
                        }, key="ed_bajo_stock_prov"
                    )
                    if st.button("🚀 AUTO-DISTRIBUIR SELECCIONADOS A BORRADORES", type="primary", use_container_width=True):
                        prods_a_pedir_auto = ed_bajo_stock[ed_bajo_stock["Pedir"] == True]
                        if not prods_a_pedir_auto.empty:
                            res_rels = fetch_productos_proveedores_rels(client)
                            mapa_provs = {}
                            if res_rels.data:
                                for r in res_rels.data:
                                    p_id = r['producto_id']
                                    coste = float(r.get('precio_coste') or 0.0)
                                    if p_id not in mapa_provs or coste < mapa_provs[p_id]['coste']:
                                        mapa_provs[p_id] = {'prov_id': r['proveedor_id'], 'coste': coste}
                            pedidos_a_crear = {}
                            for _, row in prods_a_pedir_auto.iterrows():
                                best_prov = mapa_provs.get(row['id'])
                                if best_prov:
                                    prov_id = best_prov['prov_id']
                                    if prov_id not in pedidos_a_crear: pedidos_a_crear[prov_id] = []
                                    pedidos_a_crear[prov_id].append({"Producto": row['nombre'], "Cantidad": int(row['cantidad_reponer'])})
                            if pedidos_a_crear:
                                for p_id, prods in pedidos_a_crear.items():
                                    res_b = fetch_pedidos_proveedor_borrador(client, p_id)
                                    if res_b.data:
                                        draft_id = res_b.data[0]['id']
                                        prods_act = res_b.data[0].get('productos', [])
                                        nombres_act = [p.get('Producto') for p in prods_act]
                                        for np in prods:
                                            if np['Producto'] not in nombres_act: prods_act.append(np)
                                        client.table("pedidos_proveedores").update({"productos": prods_act}).eq("id", draft_id).execute()
                                    else:
                                        client.table("pedidos_proveedores").insert({"proveedor_id": p_id, "estado": "Borrador", "productos": prods}).execute()
                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                st.success("✅ ¡Borradores generados con éxito! Revísalos abajo."); time.sleep(1.5); limpiar_cache_proveedores(); st.rerun()
                            else:
                                st.error("❌ Ninguno de los productos seleccionados tiene un proveedor asociado.")
                        else:
                            st.warning("No has seleccionado ningún producto.")
            st.markdown("---")

        st.markdown("#### 📦 Borrador de Pedidos a Proveedores")
        st.info("💡 **SISTEMA AUTOMÁTICO ACTIVO:** Cuando pulsas 'Auto-Distribuir' en la alerta superior, los productos viajan directamente aquí. Una vez cambies el estado del borrador a 'Enviado', el sistema creará un borrador nuevo la próxima vez que falte stock.")
        try:
            res_provs_p = fetch_proveedores_id_nombre_reparto(client)
            dict_pp = {p['nombre_empresa']: p['id'] for p in res_provs_p.data} if res_provs_p.data else {}
            
            cp_a, cp_b = st.columns([1, 2])
            with cp_a:
                sel_prov_ped = st.selectbox("Selecciona Proveedor para abrir pedido", list(dict_pp.keys()))
                if st.button("Crear Nuevo Borrador", use_container_width=True):
                    client.table("pedidos_proveedores").insert({"proveedor_id": dict_pp[sel_prov_ped], "estado": "Borrador", "productos": []}).execute()
                    st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                    limpiar_cache_proveedores(); st.rerun()
                    
            with cp_b:
                res_ped = fetch_pedidos_proveedores_desc(client)
                if res_ped.data:
                    df_ped = pd.DataFrame(res_ped.data)
                    df_ped['Proveedor'] = df_ped['proveedores'].apply(lambda x: x.get('nombre_empresa', ''))
                    df_ped['Reparto'] = df_ped['proveedores'].apply(lambda x: x.get('frecuencia_reparto', 'Bajo demanda'))
                    df_ped['Corte'] = df_ped['proveedores'].apply(lambda x: x.get('hora_limite', 'Sin límite'))
                    dt_ped = pd.to_datetime(df_ped['created_at'])
                    if dt_ped.dt.tz is None:
                        dt_ped = dt_ped.dt.tz_localize('UTC')
                    df_ped['Fecha'] = dt_ped.dt.tz_convert('Atlantic/Canary').dt.strftime('%d/%m/%Y')
                    
                    df_ped_vista = df_ped[['id', 'Fecha', 'Proveedor', 'Reparto', 'Corte', 'estado']].copy()
                    df_ped_vista.insert(0, "Borrar", False)
                    df_ped_vista.insert(0, "Ver/Editar", False)
                    
                    ed_ped = st.data_editor(
                        df_ped_vista,
                        hide_index=True, use_container_width=True,
                        column_config={
                            "Ver/Editar": st.column_config.CheckboxColumn("👁️ Ver"),
                            "Borrar": st.column_config.CheckboxColumn("🗑️ Borrar"),
                            "Reparto": st.column_config.TextColumn("Días Envío", disabled=True),
                            "Corte": st.column_config.TextColumn("Hora Límite", disabled=True),
                            "id": None, "estado": st.column_config.SelectboxColumn("Estado", options=["Borrador", "Enviado", "Recibido"])
                        }
                    )
                    
                    # --- LÓGICA DE BORRADO ---
                    filas_borrar = ed_ped[ed_ped["Borrar"] == True]
                    if not filas_borrar.empty:
                        st.error(f"⚠️ Has marcado {len(filas_borrar)} pedido(s) para eliminar.")
                        if st.button("🚨 CONFIRMAR ELIMINACIÓN", type="primary", use_container_width=True):
                            errores = False
                            for idx, row in filas_borrar.iterrows():
                                try:
                                    client.table("pedidos_proveedores").delete().eq("id", row['id']).execute()
                                except Exception as e:
                                    errores = True
                                    st.error(f"Error al eliminar el pedido {row['id']}: es posible que tenga registros asociados.")
                            if not errores:
                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                st.success("Pedido(s) eliminado(s) correctamente."); time.sleep(1); limpiar_cache_proveedores(); st.rerun()
                            
                    if st.button("💾 Guardar Estados de Pedidos"):
                        filas_validas = ed_ped[ed_ped["Borrar"] == False]
                        for _, r in filas_validas.iterrows():
                            client.table("pedidos_proveedores").update({"estado": str(r['estado'])}).eq("id", r['id']).execute()
                        st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                        limpiar_cache_proveedores()
                        st.success("Estados guardados correctamente."); time.sleep(0.5); st.rerun()
                        
                    # Mostrar detalle del pedido marcado
                    filas_ped = ed_ped[(ed_ped["Ver/Editar"] == True) & (ed_ped["Borrar"] == False)]
                    if not filas_ped.empty:
                        st.markdown("---")
                        ped_id = filas_ped.iloc[0]['id']
                        ped_data = df_ped[df_ped['id'] == ped_id].iloc[0]
                        st.markdown(f"#### 🛒 Contenido del Borrador #{ped_id} ({ped_data['Proveedor']})")
                        minimo = float(ped_data.get('proveedores', {}).get('pedido_minimo', 0.0)) if isinstance(ped_data.get('proveedores'), dict) else 0.0
                        if minimo > 0:
                            st.info(f"🚚 **Recuerda:** Este proveedor exige un pedido mínimo de **{minimo:.2f} €** para portes gratis. Hora de corte: {ped_data['Corte']}.")
                        else:
                            st.info(f"🚚 Hora de corte para este proveedor: {ped_data['Corte']}.")
                        lista_prods_ped = ped_data.get('productos', [])
                        df_prods_ped = pd.DataFrame(lista_prods_ped) if lista_prods_ped else pd.DataFrame(columns=["Producto", "Cantidad"])
                        if 'Producto' not in df_prods_ped.columns: df_prods_ped['Producto'] = ""
                        if 'Cantidad' not in df_prods_ped.columns: df_prods_ped['Cantidad'] = 1
                        
                        ed_prods_ped = st.data_editor(
                            df_prods_ped, use_container_width=True, hide_index=True, num_rows="dynamic",
                            column_config={"Producto": st.column_config.TextColumn("Producto a pedir"), "Cantidad": st.column_config.NumberColumn("Cant.", min_value=1)}
                        )
                        
                        c_pbtn1, c_pbtn2 = st.columns(2)
                        with c_pbtn1:
                            if st.button("💾 Guardar Cambios del Borrador", type="primary", use_container_width=True):
                                df_clean = ed_prods_ped.dropna(subset=['Producto'])
                                df_clean = df_clean[df_clean['Producto'].astype(str).str.strip() != ""]
                                client.table("pedidos_proveedores").update({"productos": json.loads(df_clean.to_json(orient='records'))}).eq("id", ped_id).execute()
                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                st.success("Borrador actualizado"); time.sleep(0.5); limpiar_cache_proveedores(); st.rerun()
                        with c_pbtn2:
                            df_clean_email = ed_prods_ped.dropna(subset=['Producto'])
                            df_clean_email = df_clean_email[df_clean_email['Producto'].astype(str).str.strip() != ""]
                            texto_pedido = f"Estimado/a comercial de {ped_data['Proveedor']},\n\nNos ponemos en contacto desde Animalarium para remitirles nuestro nuevo pedido de reposición.\n\nA continuación, detallamos los artículos y cantidades solicitadas:\n\n"
                            for _, r_ped in df_clean_email.iterrows():
                                texto_pedido += f"• {r_ped['Cantidad']} uds. - {r_ped['Producto']}\n"
                            texto_pedido += "\nQuedamos a la espera de su confirmación y de la fecha estimada de entrega.\n\nAtentamente,\nEl equipo de Animalarium\nC/ José Hernández Alfonso, 26\n38009 S/C de Tenerife"
                            prov_email = ped_data.get('proveedores', {}).get('email', '') if isinstance(ped_data.get('proveedores'), dict) else ''
                            st.markdown(f"<a href='mailto:{prov_email}?subject=Pedido Animalarium&body={urllib.parse.quote(texto_pedido)}' target='_blank'><button style='width:100%; padding:11px; background-color:#005275; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;'>✉️ Generar Email</button></a>", unsafe_allow_html=True)
                            
                        st.markdown("---")
                        st.markdown("##### 🛒 Añadir más Artículos al Pedido")
                        t_cat, t_man = st.tabs(["📚 Desde el Catálogo", "✍️ Artículo Manual (Encargos)"])
                        
                        with t_cat:
                            if not df_solo_productos.empty:
                                c_cat1, c_cat2 = st.columns([3, 1], vertical_alignment="bottom")
                                with c_cat1: prods_a_pedir = st.multiselect("Selecciona productos del inventario:", df_solo_productos['nombre'].tolist(), key=f"ms_cat_{ped_id}")
                                with c_cat2:
                                    if st.button("Añadir Selección", use_container_width=True, key=f"btn_cat_{ped_id}"):
                                        if prods_a_pedir:
                                            for p_nom in prods_a_pedir:
                                                if not any(item.get('Producto') == p_nom for item in lista_prods_ped):
                                                    lista_prods_ped.append({"Producto": p_nom, "Cantidad": 1})
                                            client.table("pedidos_proveedores").update({"productos": lista_prods_ped}).eq("id", ped_id).execute()
                                            st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                            st.success("¡Añadidos!"); time.sleep(1); limpiar_cache_proveedores(); st.rerun()
                                        else:
                                            st.warning("Selecciona algún producto.")
                        
                        with t_man:
                            with st.form(f"add_manual_ped_{ped_id}", clear_on_submit=True, border=False):
                                cm1, cm2, cm3 = st.columns([2, 1, 1])
                                with cm1: m_prod = st.text_input("Nombre del producto", placeholder="Ej: Correa roja...", key=f"am_nom_{ped_id}_{st.session_state.llave_n_art_ped}")
                                with cm2: m_cant = st.number_input("Cantidad", min_value=1, value=1, key=f"am_can_{ped_id}_{st.session_state.llave_n_art_ped}")
                                with cm3: 
                                    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                                    submit_manual = st.form_submit_button("Añadir Manual", use_container_width=True)
                                
                                if submit_manual:
                                    if m_prod:
                                        lista_prods_ped.append({"Producto": m_prod, "Cantidad": m_cant})
                                        client.table("pedidos_proveedores").update({"productos": lista_prods_ped}).eq("id", ped_id).execute()
                                        st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                        st.session_state.llave_n_art_ped += 1
                                        st.success("Añadido."); time.sleep(0.5); limpiar_cache_proveedores(); st.rerun()
                                    else:
                                        st.warning("Escribe el nombre.")
        except:
            pass