import streamlit as st
import pandas as pd
import time

def render_pestana_inventario(client):
    st.markdown("<h3 style='margin-top: -15px;'>📦 Gestión de Inventario y Servicios</h3>", unsafe_allow_html=True)
    
    col_f, col_t = st.columns([1.2, 2.5], gap="large")
    
    res_proveedores = client.table("proveedores").select("id, nombre_empresa").execute()
    dict_proveedores = {p['nombre_empresa']: p['id'] for p in res_proveedores.data} if res_proveedores.data else {}

    with col_f:
        st.markdown("#### 📝 Alta de nuevo ítem")
        cat_item = st.radio("Selecciona qué vas a registrar:", ["Producto", "Servicio"], horizontal=True)
        
        with st.form("nuevo_p_separado", clear_on_submit=True, border=True):
            nombre = st.text_input(f"Nombre del {cat_item} *")
            c1, c2 = st.columns(2)
            with c1: sku = st.text_input("SKU (Interno) *")
            with c2: 
                if cat_item == "Producto":
                    cod_barras = st.text_input("Cód. Barras")
                else:
                    cod_barras = ""
            
            if cat_item == "Producto":
                c4, c5 = st.columns(2, vertical_alignment="bottom")
                with c4: p_base = st.number_input("Coste Compra (€)", min_value=0.0, format="%.2f", value=None)
                with c5: igic_tipo = st.selectbox("IGIC Compra %", [7.00, 0.00, 3.00, 15.00])
                
                c6, c7, c8, c9 = st.columns(4, vertical_alignment="bottom")
                with c6: pvp = st.number_input("PVP Público (€) *", min_value=0.0, format="%.2f", value=None)
                with c7: stck = st.number_input("Stock Inicial", min_value=0, value=None)
                with c8: s_min = st.number_input("Avisar si quedan:", min_value=0, value=2)
                with c9: c_rep = st.number_input("Cant. a pedir:", min_value=1, value=5)
                provs_sel = st.multiselect("Asociar Proveedores", list(dict_proveedores.keys()))
            else:
                c4, c5 = st.columns(2, vertical_alignment="bottom")
                with c4: pvp = st.number_input("Precio Cerrado (€) *", min_value=0.0, format="%.2f", value=None)
                with c5: igic_tipo = st.selectbox("IGIC (%)", [7.00, 0.00, 3.00, 15.00])
                p_base = 0.0
                stck = 0
                provs_sel = []
                st.info("💡 El sistema desglosará automáticamente la Base Imponible y la cuota de IGIC en la tabla.")
            
            if st.form_submit_button("💾 REGISTRAR", use_container_width=True, type="primary"):
                pvp_val = pvp if pvp is not None else 0.0
                p_base_val = p_base if p_base is not None else 0.0
                stck_val = stck if stck is not None else 0
                
                if nombre and sku:
                    if cat_item == "Servicio":
                        p_base_calc = pvp_val / (1 + (igic_tipo / 100))
                    else:
                        p_base_calc = p_base_val

                    res_ins = client.table("productos").insert({
                        "sku": sku, "codigo_barras": cod_barras, "nombre": nombre, "categoria": cat_item,
                        "precio_base": p_base_calc, "igic_tipo": igic_tipo, "stock_actual": stck_val, 
                        "precio_pvp": pvp_val, "stock_minimo": s_min if cat_item == "Producto" else 0,
                        "cantidad_reponer": c_rep if cat_item == "Producto" else 0
                    }).execute()
                    if cat_item == "Producto" and res_ins.data and provs_sel:
                        rels = [{"producto_id": res_ins.data[0]['id'], "proveedor_id": dict_proveedores[p], "precio_coste": p_base_calc} for p in provs_sel]
                        client.table("productos_proveedores").insert(rels).execute()
                    st.success("Guardado correctamente"); time.sleep(0.5); st.rerun()

    with col_t:
            res_prod = client.table("productos").select("*, productos_proveedores(proveedores(nombre_empresa))").order("nombre").execute()
            
            if res_prod.data:
                df_inv = pd.DataFrame(res_prod.data)
                
                def extraer_proveedores(rels):
                    if isinstance(rels, list) and len(rels) > 0:
                        nombres = [r.get('proveedores', {}).get('nombre_empresa', '') for r in rels if isinstance(r, dict) and r.get('proveedores')]
                        return nombres[0] if nombres else "---"
                    return "---"
                    
                if 'productos_proveedores' in df_inv.columns:
                    df_inv['Proveedor'] = df_inv['productos_proveedores'].apply(extraer_proveedores)
                else:
                    df_inv['Proveedor'] = "---"
                
                # --- 1. LIMPIEZA DE DATOS ---
                df_inv['categoria_filt'] = df_inv['categoria'].fillna('Producto').astype(str).str.strip().str.capitalize()

                df_solo_productos = df_inv[df_inv['categoria_filt'] == 'Producto'].copy()

                # Asegurar columnas por si hay productos antiguos
                if 'stock_minimo' not in df_solo_productos.columns: df_solo_productos['stock_minimo'] = 2
                if 'cantidad_reponer' not in df_solo_productos.columns: df_solo_productos['cantidad_reponer'] = 5

                # --- ALERTA DE STOCK BAJO ---
                df_bajo_stock = df_solo_productos[df_solo_productos['stock_actual'] <= df_solo_productos['stock_minimo']].sort_values(by="stock_actual")
                if not df_bajo_stock.empty:
                    st.warning(f"⚠️ **ATENCIÓN: Tienes {len(df_bajo_stock)} producto(s) por debajo de su stock mínimo.**")
                    
                    if st.button("🚀 AUTO-DISTRIBUIR A BORRADORES (Generación Inteligente)", type="primary", use_container_width=True):
                        # 1. Encontrar qué proveedor vende cada cosa
                        res_rels = client.table("productos_proveedores").select("producto_id, proveedor_id").execute()
                        mapa_provs = {r['producto_id']: r['proveedor_id'] for r in res_rels.data} if res_rels.data else {}
                        
                        pedidos_creados = 0
                        pedidos_a_crear = {}
                        # 2. Agrupar por proveedor
                        for _, row in df_bajo_stock.iterrows():
                            prov_id = mapa_provs.get(row['id'])
                            if prov_id:
                                if prov_id not in pedidos_a_crear: pedidos_a_crear[prov_id] = []
                                pedidos_a_crear[prov_id].append({"Producto": row['nombre'], "Cantidad": int(row['cantidad_reponer'])})
                                
                        # 3. Mandar a borradores
                        if pedidos_a_crear:
                            for p_id, prods in pedidos_a_crear.items():
                                res_b = client.table("pedidos_proveedores").select("id, productos").eq("proveedor_id", p_id).eq("estado", "Borrador").execute()
                                if res_b.data: # Si ya hay borrador, actualizamos
                                    draft_id = res_b.data[0]['id']
                                    prods_act = res_b.data[0].get('productos', [])
                                    nombres_act = [p.get('Producto') for p in prods_act]
                                    for np in prods:
                                        if np['Producto'] not in nombres_act: prods_act.append(np)
                                    client.table("pedidos_proveedores").update({"productos": prods_act}).eq("id", draft_id).execute()
                                else: # Si no hay, creamos uno nuevo
                                    client.table("pedidos_proveedores").insert({"proveedor_id": p_id, "estado": "Borrador", "productos": prods}).execute()
                            st.success("✅ ¡Borradores generados automáticamente! Ve a la Pestaña 7 (Proveedores) para revisarlos y enviarlos.")
                        else:
                            st.error("❌ No se pudo automatizar: Ninguno de los productos bajo mínimos tiene un proveedor asociado.")

                    with st.expander("👀 Ver lista manual de reposición"):
                        st.dataframe(df_bajo_stock[['sku', 'nombre', 'stock_actual', 'stock_minimo', 'cantidad_reponer']], hide_index=True, use_container_width=True)
                        
                        # --- INTEGRACIÓN CON PEDIDOS A PROVEEDORES ---
                        res_borradores = client.table("pedidos_proveedores").select("id, proveedores(nombre_empresa)").eq("estado", "Borrador").execute()
                        if res_borradores.data:
                            opciones_borrador = {f"Borrador #{b['id']} - {b['proveedores']['nombre_empresa']}": b['id'] for b in res_borradores.data if b.get('proveedores')}
                            c_ped1, c_ped2 = st.columns([2, 1])
                            with c_ped1: prods_a_pedir = st.multiselect("Selecciona productos para añadir a un pedido:", df_bajo_stock['nombre'].tolist())
                            with c_ped2:
                                borrador_sel = st.selectbox("Selecciona el Borrador:", list(opciones_borrador.keys()))
                                if st.button("➕ Añadir al Borrador", use_container_width=True) and prods_a_pedir and borrador_sel:
                                    draft_id = opciones_borrador[borrador_sel]
                                    prods_actuales = client.table("pedidos_proveedores").select("productos").eq("id", draft_id).execute().data[0].get('productos', [])
                                    for p_nom in prods_a_pedir:
                                        if not any(item.get('Producto') == p_nom for item in prods_actuales):
                                            prods_actuales.append({"Producto": p_nom, "Cantidad": 1})
                                    client.table("pedidos_proveedores").update({"productos": prods_actuales}).eq("id", draft_id).execute()
                                    st.success("¡Añadidos al borrador! Ve a la Pestaña 7 para gestionarlo.")
                        else:
                            st.info("💡 Ve a la Pestaña 7 (Proveedores) para crear un Borrador de Pedido y añadir estos productos.")

                # --- TABLA DE PRODUCTOS MEJORADA ---
                st.markdown("#### 📦 Inventario de Productos")

                # Ahora permitimos borrar filas con num_rows="dynamic"
                edit_p = st.data_editor(
                    df_solo_productos,
                    column_config={
                        "id": None, "categoria": None, "categoria_filt": None, "productos_proveedores": None,
                        "sku": "SKU", "codigo_barras": "Barras", "nombre": "Descripción",
                        "Proveedor": st.column_config.SelectboxColumn("Proveedor", options=["---"] + list(dict_proveedores.keys())),
                        "precio_base": st.column_config.NumberColumn("Coste (€)", format="%.2f"),
                        "igic_tipo": "IGIC %", "precio_pvp": "PVP (€)", "stock_actual": "Stock",
                        "stock_minimo": st.column_config.NumberColumn("Avisar en", step=1),
                        "cantidad_reponer": st.column_config.NumberColumn("Reponer Ud", step=1)
                    },
                    column_order=["sku", "codigo_barras", "nombre", "Proveedor", "precio_base", "igic_tipo", "precio_pvp", "stock_actual", "stock_minimo", "cantidad_reponer"],
                    hide_index=True, 
                    use_container_width=True, 
                    num_rows="dynamic", # <--- ESTO PERMITE BORRAR FILAS
                    key="edit_p_sep"
                )

                if st.button("💾 Guardar cambios en Productos", key="btn_save_p_sep"):
                    # 1. Detectar si alguna fila ha sido borrada
                    ids_actuales = edit_p['id'].dropna().tolist()
                    ids_originales = df_solo_productos['id'].tolist()
                    ids_a_borrar = [id_orig for id_orig in ids_originales if id_orig not in ids_actuales]

                    # 2. Borrar de Supabase los que ya no están en la tabla
                    for id_del in ids_a_borrar:
                        client.table("productos").delete().eq("id", id_del).execute()

                    # 3. Actualizar los que se han quedado (por si cambiaste precios o stock)
                    for i, row in edit_p.iterrows():
                        if pd.notna(row['id']): # Solo actualizamos si el producto ya existía
                            datos = row.to_dict()
                            
                            # --- Gestión del proveedor ---
                            prov_nombre = datos.get('Proveedor', '---')
                            
                            for col_eliminar in ['categoria_filt', 'Proveedor', 'productos_proveedores']:
                                if col_eliminar in datos: del datos[col_eliminar]
                            client.table("productos").update(datos).eq("id", row['id']).execute()
                            
                            # Actualizar la relación principal del proveedor
                            client.table("productos_proveedores").delete().eq("producto_id", row['id']).execute()
                            if prov_nombre != "---" and prov_nombre in dict_proveedores:
                                client.table("productos_proveedores").insert({
                                    "producto_id": row['id'], "proveedor_id": dict_proveedores[prov_nombre], "precio_coste": float(datos.get('precio_base', 0.0))
                                }).execute()

                    st.success("Inventario sincronizado correctamente")
                    st.rerun() # Recargamos para ver los cambios [cite: 9]

                st.markdown("---")

                # --- TABLA DE SERVICIOS MEJORADA ---
                st.markdown("#### ✂️ Catálogo de Servicios")
                df_solo_servicios = df_inv[df_inv['categoria_filt'] == 'Servicio'].copy()
                
                # Añadimos la columna calculada de Cuota de IGIC para mostrar el desglose
                df_solo_servicios['Cuota IGIC (€)'] = df_solo_servicios['precio_pvp'] - df_solo_servicios['precio_base']

                # Habilitamos num_rows="dynamic" para que puedas borrar servicios
                edit_s = st.data_editor(
                    df_solo_servicios,
                    column_config={
                        "id": None, "categoria": None, "categoria_filt": None,
                        "sku": "Código", "nombre": "Descripción del Servicio",
                        "precio_base": st.column_config.NumberColumn("Base Real sin IGIC (€)", format="%.2f", disabled=True),
                        "igic_tipo": st.column_config.SelectboxColumn("IGIC %", options=[7.0, 0.0, 3.0, 15.0]),
                        "Cuota IGIC (€)": st.column_config.NumberColumn("Cuota IGIC (€)", format="%.2f", disabled=True),
                        "precio_pvp": st.column_config.NumberColumn("Precio Cerrado (PVP) (€)", format="%.2f")
                    },
                    column_order=["sku", "nombre", "precio_base", "igic_tipo", "Cuota IGIC (€)", "precio_pvp"],
                    hide_index=True, 
                    use_container_width=True, 
                    num_rows="dynamic", # <--- PERMITE BORRAR FILAS DE SERVICIOS
                    key="edit_s_sep"
                )

                if st.button("💾 Guardar cambios en Servicios", key="btn_save_s_sep"):
                    # 1. Identificar si algún servicio fue eliminado de la tabla
                    ids_s_actuales = edit_s['id'].dropna().tolist()
                    ids_s_originales = df_solo_servicios['id'].tolist()
                    ids_s_a_borrar = [id_orig for id_orig in ids_s_originales if id_orig not in ids_s_actuales]

                    # 2. Borrar de la base de datos los servicios eliminados
                    for id_del in ids_s_a_borrar:
                        client.table("productos").delete().eq("id", id_del).execute()

                    # 3. Actualizar o guardar los cambios en los servicios que quedan
                    for i, row in edit_s.iterrows():
                        if pd.notna(row['id']):
                            # Recalculamos la base real de forma automática si cambiaste el PVP o el IGIC en la tabla
                            nuevo_pvp = float(row['precio_pvp'])
                            nuevo_igic = float(row['igic_tipo'])
                            nueva_base = nuevo_pvp / (1 + (nuevo_igic / 100))
                            
                            client.table("productos").update({
                                "sku": str(row['sku']), "nombre": str(row['nombre']),
                                "precio_pvp": nuevo_pvp, "igic_tipo": nuevo_igic, "precio_base": nueva_base
                            }).eq("id", row['id']).execute()

                    st.success("Catálogo de servicios actualizado")
                    st.rerun()
            else:
                st.info("Inventario vacío.")