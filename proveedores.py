import streamlit as st
import pandas as pd
import time
import json
import urllib.parse

def render_pestana_proveedores(client):
    st.markdown("<h3 style='margin-top:-15px;'>📦 Pedidos a Proveedores</h3>", unsafe_allow_html=True)
    sub_prov, sub_pedidos = st.tabs(["🚚 Directorio Proveedores", "📦 Hacer Pedido a Proveedor"])
    
    with sub_prov:
        cp1, cp2 = st.columns([1, 2])
        with cp1:
            st.markdown("#### ➕ Nuevo Proveedor")
            with st.form("n_prov_full", clear_on_submit=True):
                st.markdown("**Datos Principales**")
                n_emp = st.text_input("Nombre Empresa *")
                c_np1, c_np2 = st.columns(2)
                with c_np1: n_cif = st.text_input("CIF / NIF")
                with c_np2: n_tel = st.text_input("Teléfono Fijo")
                
                c_np3, c_np4 = st.columns(2)
                with c_np3: n_mov = st.text_input("Móvil")
                with c_np4: n_ema = st.text_input("Email")
                
                st.markdown("**Ubicación Rápida**")
                n_dir = st.text_input("Dirección")
                c_np5, c_np6 = st.columns(2)
                with c_np5: n_pob = st.text_input("Población")
                with c_np6: n_pais = st.text_input("País", value="España - Islas Canarias")
                
                n_frec = st.text_input("Días de Reparto", placeholder="Ej: Todos los días, Los martes, Bajo demanda...", value="Bajo demanda")
                n_hora = st.text_input("Hora límite de pedido", placeholder="Ej: 14:00, 20:00, Sin límite...", value="Sin límite")
                
                if st.form_submit_button("Guardar Proveedor", use_container_width=True, type="primary"):
                    if n_emp:
                        client.table("proveedores").insert({
                            "nombre_empresa": n_emp, "cif": n_cif,
                            "telefono": n_tel, "movil": n_mov, "email": n_ema,
                            "direccion": n_dir, "poblacion": n_pob, "pais": n_pais,
                            "frecuencia_reparto": n_frec, "hora_limite": n_hora
                        }).execute()
                        st.success("Guardado"); time.sleep(0.5); st.rerun()
        with cp2:
            st.markdown("#### 📋 Directorio")
            res_p = client.table("proveedores").select("*").execute()
            df_p = None
            ed_p = None
            if res_p.data:
                df_p = pd.DataFrame(res_p.data)
                
                # Aseguramos que las nuevas columnas existan en el DataFrame (por si no has corrido el SQL aún)
                for col in ['telefono', 'movil', 'email', 'direccion', 'poblacion', 'codigo_postal', 'provincia', 'pais', 'codigo_pais', 'idioma', 'forma_pago', 'persona_contacto', 'iban', 'swift', 'notas', 'contacto']:
                    if col not in df_p.columns: df_p[col] = ""
                    
                df_p_vista = df_p[['id', 'nombre_empresa', 'telefono', 'movil', 'email']].copy()
                df_p_vista.insert(0, "Ver Ficha", False)
                
                st.markdown("💡 *Marca **'👁️ Ver Ficha'** para acceder a todos los datos de contacto y facturación.*")
                
                ed_p = st.data_editor(
                    df_p_vista, hide_index=True, use_container_width=True, key="ed_prov", height=250,
                    column_config={
                        "Ver Ficha": st.column_config.CheckboxColumn("👁️ Ver Ficha", default=False),
                        "id": None, "nombre_empresa": "Empresa", "frecuencia_reparto": "Días Reparto", 
                        "telefono": "Teléfono", "email": "Email"
                    }
                )
                
                if st.button("💾 Guardar Cambios Rápidos", type="primary"):
                    for _, row in ed_p.iterrows():
                        if pd.notna(row['id']):
                            client.table("proveedores").update({
                                "nombre_empresa": str(row['nombre_empresa']),
                                "telefono": str(row['telefono']), "frecuencia_reparto": str(row['frecuencia_reparto']), "hora_limite": str(row['hora_limite']), "email": str(row['email'])
                            }).eq("id", row['id']).execute()
                    st.success("Directorio actualizado."); time.sleep(0.5); st.rerun()
                    
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
                    with cf1: f_nom = st.text_input("Nombre Empresa *", value=p_data.get('nombre_empresa',''))
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
                    with cf16: f_frec = st.text_input("Días de Reparto", value=p_data.get('frecuencia_reparto','Bajo demanda'))
                    with cf17: f_hora = st.text_input("Hora Límite", value=p_data.get('hora_limite','Sin límite'))
                    
                    st.markdown("**3. Facturación y Notas**")
                    cf13, cf14, cf15 = st.columns([1, 1.5, 1])
                    with cf13: f_fpago = st.text_input("Forma de Pago", value=p_data.get('forma_pago',''))
                    with cf14: f_iban = st.text_input("IBAN", value=p_data.get('iban',''))
                    with cf15: f_swift = st.text_input("SWIFT", value=p_data.get('swift',''))
                    
                    f_not = st.text_area("Fax / Otras Notas / Observaciones", value=p_data.get('notas',''))
                    
                    if st.form_submit_button("💾 Guardar Ficha Completa", type="primary", use_container_width=True):
                        if f_nom:
                            client.table("proveedores").update({
                                "nombre_empresa": f_nom, "cif": f_cif, "persona_contacto": f_per,
                                "telefono": f_tel, "movil": f_mov, "email": f_ema, "direccion": f_dir,
                                "poblacion": f_pob, "codigo_postal": f_cp, "provincia": f_prov,
                                "pais": f_pais, "frecuencia_reparto": f_frec, "hora_limite": f_hora,
                                "forma_pago": f_fpago, "iban": f_iban, "swift": f_swift, "notas": f_not, 
                                "contacto": "" # Borramos la línea antigua ya que se ha organizado
                            }).eq("id", p_id).execute()
                            st.success("Ficha del proveedor actualizada correctamente."); time.sleep(0.5); st.rerun()
                        else:
                            st.error("El nombre de la empresa es obligatorio.")

    with sub_pedidos:
        st.markdown("#### 📦 Borrador de Pedidos a Proveedores")
        st.info("💡 **SISTEMA AUTOMÁTICO ACTIVO:** Cuando pulsas 'Auto-Distribuir' en la Pestaña 1, los productos viajan directamente aquí. Una vez cambies el estado del borrador a 'Enviado', el sistema creará un borrador nuevo la próxima vez que falte stock.")
        try:
            res_provs_p = client.table("proveedores").select("id, nombre_empresa, frecuencia_reparto").execute()
            dict_pp = {p['nombre_empresa']: p['id'] for p in res_provs_p.data} if res_provs_p.data else {}
            
            cp_a, cp_b = st.columns([1, 2])
            with cp_a:
                sel_prov_ped = st.selectbox("Selecciona Proveedor para abrir pedido", list(dict_pp.keys()))
                if st.button("Crear Nuevo Borrador", use_container_width=True):
                    client.table("pedidos_proveedores").insert({"proveedor_id": dict_pp[sel_prov_ped], "estado": "Borrador", "productos": []}).execute()
                    st.rerun()
                    
            with cp_b:
                res_ped = client.table("pedidos_proveedores").select("*, proveedores(nombre_empresa, frecuencia_reparto, hora_limite, email)").order("created_at", desc=True).execute()
                if res_ped.data:
                    df_ped = pd.DataFrame(res_ped.data)
                    df_ped['Proveedor'] = df_ped['proveedores'].apply(lambda x: x.get('nombre_empresa', ''))
                    df_ped['Reparto'] = df_ped['proveedores'].apply(lambda x: x.get('frecuencia_reparto', 'Bajo demanda'))
                    df_ped['Corte'] = df_ped['proveedores'].apply(lambda x: x.get('hora_limite', 'Sin límite'))
                    df_ped['Fecha'] = pd.to_datetime(df_ped['created_at']).dt.strftime('%d/%m/%Y')
                    
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
                            for idx, row in filas_borrar.iterrows():
                                client.table("pedidos_proveedores").delete().eq("id", row['id']).execute()
                            st.success("Pedido(s) eliminado(s) correctamente."); time.sleep(1); st.rerun()
                            
                    if st.button("💾 Guardar Estados de Pedidos"):
                        filas_validas = ed_ped[ed_ped["Borrar"] == False]
                        for _, r in filas_validas.iterrows():
                            client.table("pedidos_proveedores").update({"estado": str(r['estado'])}).eq("id", r['id']).execute()
                        st.rerun()
                        
                    # Mostrar detalle del pedido marcado
                    filas_ped = ed_ped[(ed_ped["Ver/Editar"] == True) & (ed_ped["Borrar"] == False)]
                    if not filas_ped.empty:
                        st.markdown("---")
                        ped_id = filas_ped.iloc[0]['id']
                        ped_data = df_ped[df_ped['id'] == ped_id].iloc[0]
                        st.markdown(f"#### 🛒 Contenido del Borrador #{ped_id} ({ped_data['Proveedor']})")
                        
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
                                st.success("Borrador actualizado"); time.sleep(0.5); st.rerun()
                        with c_pbtn2:
                            df_clean_email = ed_prods_ped.dropna(subset=['Producto'])
                            df_clean_email = df_clean_email[df_clean_email['Producto'].astype(str).str.strip() != ""]
                            texto_pedido = f"Hola,\\n\\nAdjunto nuestro pedido a {ped_data['Proveedor']}:\\n\\n"
                            for _, r_ped in df_clean_email.iterrows():
                                texto_pedido += f"- {r_ped['Cantidad']}x {r_ped['Producto']}\\n"
                            texto_pedido += "\\nGracias,\\nAnimalarium"
                            prov_email = ped_data.get('proveedores', {}).get('email', '') if isinstance(ped_data.get('proveedores'), dict) else ''
                            st.markdown(f"<a href='mailto:{prov_email}?subject=Pedido Animalarium&body={urllib.parse.quote(texto_pedido)}' target='_blank'><button style='width:100%; padding:11px; background-color:#005275; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;'>✉️ Generar Email</button></a>", unsafe_allow_html=True)
                            
                        st.markdown("---")
                        st.markdown("##### ➕ Añadir Artículo Manual (Fuera de catálogo / Encargos especiales)")
                        with st.form(f"add_manual_ped_{ped_id}", clear_on_submit=True, border=False):
                            cm1, cm2, cm3 = st.columns([2, 1, 1])
                            with cm1: m_prod = st.text_input("Nombre del producto manual", placeholder="Ej: Correa extensible roja...")
                            with cm2: m_cant = st.number_input("Cantidad", min_value=1, value=1)
                            with cm3: 
                                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                                submit_manual = st.form_submit_button("Añadir al Pedido", use_container_width=True)
                            
                            if submit_manual:
                                if m_prod:
                                    lista_prods_ped.append({"Producto": m_prod, "Cantidad": m_cant})
                                    client.table("pedidos_proveedores").update({"productos": lista_prods_ped}).eq("id", ped_id).execute()
                                    st.success("Artículo añadido."); time.sleep(0.5); st.rerun()
                                else:
                                    st.warning("Escribe el nombre del producto.")
        except:
            pass