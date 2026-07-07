import streamlit as st
import pandas as pd
import time

@st.cache_data(show_spinner=False, ttl=300)
def get_proveedores(_client):
    res = _client.table("proveedores").select("id, nombre_empresa").execute()
    return res.data if res.data else []

@st.cache_data(show_spinner=False, ttl=300)
def get_inv_full(_client):
    _all = []
    _off = 0
    while True:
        _r = _client.table("productos").select("*, productos_proveedores(proveedores(nombre_empresa))").order("nombre").range(_off, _off + 999).execute()
        if _r.data:
            _all.extend(_r.data)
            if len(_r.data) < 1000: break
            _off += 1000
        else: break
    return _all

def limpiar_cache_inventario():
    get_proveedores.clear()
    get_inv_full.clear()

def procesar_lote_ia_gemini(productos_lote, client):
    import google.generativeai as genai
    import os
    import json
    import streamlit as st
    
    api_key = st.secrets.get("gemini_api_key")
    if not api_key:
        return {"error": "No se encontró gemini_api_key en secrets"}
        
    genai.configure(api_key=api_key)
    
    prompt = """
Eres un experto en productos para mascotas. 
Se te proporcionará una lista de productos con su ID, Nombre y Marca (si existe).
Tu tarea es categorizarlos devolviendo un JSON estrictamente estructurado como un array de objetos con las siguientes claves y posibles valores (DEBES elegir de las listas provistas si aplica, o dejar vacío si no sabes o no aplica):

OPCIONES PERMITIDAS:
- "familia": ["Alimentación húmeda", "Alimentación seca", "Snack", "Accesorios", "Higiene", "Paseo", "Juguetes", "Descanso", "Farmacia/Cuidados", "Otros"]
- "subcategoria": ["Pienso Seco", "Pienso Húmedo", "Semi-húmedo", "Snacks", "Collares/Arneses", "Champús", "Medicamentos", "Juguetes", "Otros"]
- "gama": ["Grain free", "Low grain", "Wet line", "Atlantic Pet Special Bully", "Classic Supreme", "Classic Supreme gato", "Premium Receta gato", "Premium Receta", "Super Premium Receta", "Super Premium Receta grain free", "Ultra Premium Receta grain free", "Author", "Care", "Classic", "Hipoalergénico", "Just", "Prime", "Ultra"]
- "mascota": ["Perro", "Gato", "Roedor", "Aves", "Reptiles", "Universal"]
- "edad": ["Adulto", "Cachorro/Kitten", "Senior", "Todas las edades"]
- "tamano": ["Grande", "Mediano", "Mini", "Pequeño", "Todas las razas"]
- "necesidad_especial": ["Articulaciones", "Bolas de pelo", "Control de peso", "Esterilizado", "Hipoalergénico", "Paladares exigentes", "Pelo blanco", "Sensible/digestivo", "Urinario", "Renal", "Hepático", "Ninguna"]
- "sabor_principal": ["Atún", "Cerdo", "Ciervo", "Conejo", "Cordero", "Mix de carnes", "Pato", "Pavo", "Pescado", "Pollo", "Salmón", "Sin especificar", "Ternera/Buey"]
- "marca": [Extrae la marca si la ves evidente (ej. Royal Canin, Amanova, etc), sino usa "Generico"]

FORMATO DE SALIDA (JSON array puro):
[
  {
    "id": 123,
    "familia": "...",
    "subcategoria": "...",
    "gama": "...",
    "mascota": "...",
    "edad": "...",
    "tamano": "...",
    "necesidad_especial": "...",
    "sabor_principal": "...",
    "marca": "..."
  }
]

LISTA DE PRODUCTOS:
"""
    for p in productos_lote:
        prompt += f"- ID: {p['id']} | Nombre: {p['nombre']} | Marca actual: {p.get('marca', '')}\n"

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
            )
        )
        data = json.loads(response.text)
        
        for d in data:
            if not isinstance(d, dict) or 'id' not in d: continue
            
            valid = {
                "familia": ["Alimentación húmeda", "Alimentación seca", "Snack", "Accesorios", "Higiene", "Paseo", "Juguetes", "Descanso", "Farmacia/Cuidados", "Otros"],
                "subcategoria": ["Pienso Seco", "Pienso Húmedo", "Semi-húmedo", "Snacks", "Collares/Arneses", "Champús", "Medicamentos", "Juguetes", "Otros"],
                "gama": ["Grain free", "Low grain", "Wet line", "Atlantic Pet Special Bully", "Classic Supreme", "Classic Supreme gato", "Premium Receta gato", "Premium Receta", "Super Premium Receta", "Super Premium Receta grain free", "Ultra Premium Receta grain free", "Author", "Care", "Classic", "Hipoalergénico", "Just", "Prime", "Ultra"],
                "mascota": ["Perro", "Gato", "Roedor", "Aves", "Reptiles", "Universal"],
                "edad": ["Adulto", "Cachorro/Kitten", "Senior", "Todas las edades"],
                "tamano": ["Grande", "Mediano", "Mini", "Pequeño", "Todas las razas"],
                "necesidad_especial": ["Articulaciones", "Bolas de pelo", "Control de peso", "Esterilizado", "Hipoalergénico", "Paladares exigentes", "Pelo blanco", "Sensible/digestivo", "Urinario", "Renal", "Hepático", "Ninguna"],
                "sabor_principal": ["Atún", "Cerdo", "Ciervo", "Conejo", "Cordero", "Mix de carnes", "Pato", "Pavo", "Pescado", "Pollo", "Salmón", "Sin especificar", "Ternera/Buey"]
            }
            
            def check_v(k, v):
                val = str(v).strip() if v else ""
                if k == "familia" and val in ["Alimentación", "Alimento"]: return "Alimentación seca"
                if k == "familia" and val in ["Alimento Húmedo"]: return "Alimentación húmeda"
                if val in valid[k]: return val
                return ""
            
            update_data = {
                "familia": check_v("familia", d.get("familia")),
                "subcategoria": check_v("subcategoria", d.get("subcategoria")),
                "gama": check_v("gama", d.get("gama")),
                "mascota": check_v("mascota", d.get("mascota")),
                "edad": check_v("edad", d.get("edad")),
                "tamano": check_v("tamano", d.get("tamano")),
                "necesidad_especial": check_v("necesidad_especial", d.get("necesidad_especial")),
                "sabor_principal": check_v("sabor_principal", d.get("sabor_principal")),
                "marca": str(d.get("marca", "")).strip()
            }
            if update_data["marca"].lower() == "amv": update_data["marca"] = "AMANOVA"
            if update_data["marca"].lower() == "generico": update_data["marca"] = ""
            
            client.table("productos").update(update_data).eq("id", d['id']).execute()
            
        return {"success": len(data)}
    except Exception as e:
        return {"error": str(e)}

def render_pestana_inventario(client):
    st.markdown("<h3 style='margin-top: -15px;'>📦 Gestión de Inventario y Servicios</h3>", unsafe_allow_html=True)
    if st.session_state.pop("inventario_saved", False):
        st.success("✅ Los cambios se han guardado correctamente.")
    
    col_f, col_t = st.columns([1.2, 2.5], gap="large")
    
    res_proveedores_data = get_proveedores(client)
    dict_proveedores = {p['nombre_empresa']: p['id'] for p in res_proveedores_data} if res_proveedores_data else {}

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
                        "nombre": nombre, "sku": sku, "codigo_barras": cod_barras, "categoria": cat_item,
                        "familia": "Generico", "marca": "Generico", "precio_base": p_base_calc, "igic_tipo": igic_tipo, 
                        "precio_pvp": pvp_val, "stock_actual": stck_val, "stock_minimo": s_min if cat_item == "Producto" else 0,
                        "cantidad_reponer": c_rep if cat_item == "Producto" else 0
                    }).execute()
                    if cat_item == "Producto" and res_ins.data and provs_sel:
                        rels = [{"producto_id": res_ins.data[0]['id'], "proveedor_id": dict_proveedores[p], "precio_coste": p_base_calc} for p in provs_sel]
                        client.table("productos_proveedores").insert(rels).execute()
                    st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                    st.success("Guardado correctamente"); time.sleep(0.5); limpiar_cache_inventario(); st.rerun()

    with col_t:
            all_prods = get_inv_full(client)
            if all_prods:
                df_inv = pd.DataFrame(all_prods)
                
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
                if 'fecha_caducidad' not in df_solo_productos.columns: df_solo_productos['fecha_caducidad'] = None
                if 'familia' not in df_solo_productos.columns: df_solo_productos['familia'] = "Generico"
                if 'marca' not in df_solo_productos.columns: df_solo_productos['marca'] = "Generico"
                if 'subcategoria' not in df_solo_productos.columns: df_solo_productos['subcategoria'] = ""
                if 'gama' not in df_solo_productos.columns: df_solo_productos['gama'] = ""
                if 'mascota' not in df_solo_productos.columns: df_solo_productos['mascota'] = "Universal"
                if 'edad' not in df_solo_productos.columns: df_solo_productos['edad'] = "Todas las edades"
                if 'tamano' not in df_solo_productos.columns: df_solo_productos['tamano'] = "Todas las Razas"
                if 'necesidad_especial' not in df_solo_productos.columns: df_solo_productos['necesidad_especial'] = "Ninguna"
                if 'sabor_principal' not in df_solo_productos.columns: df_solo_productos['sabor_principal'] = "Sin especificar"
                if 'caracteristicas' not in df_solo_productos.columns: df_solo_productos['caracteristicas'] = ""

                seccion_inventario = st.radio("Sección Inventario:", ["📦 Inventario", "🐶 Servicios", "🛠️ Uso Interno"], horizontal=True, label_visibility="collapsed")
                
                if seccion_inventario == "📦 Inventario":
                    st.markdown("#### 📦 Traspaso de Cajas a Unidades (Desempaquetar)")
                    with st.expander("Abrir Caja / Saco"):
                        tc1, tc2, tc3 = st.columns([2, 2, 1])
                        productos_tuplas = [(p['id'], str(p['nombre'])) for _, p in df_solo_productos.iterrows() if pd.notna(p['id']) and pd.notna(p['nombre'])]
                        
                        with tc1:
                            id_caja = st.selectbox("1. Selecciona la Caja Origen", options=[None] + productos_tuplas, format_func=lambda x: x[1] if x else "---", key="sel_caja")
                        with tc2:
                            id_unidad = st.selectbox("2. Selecciona la Unidad Destino", options=[None] + productos_tuplas, format_func=lambda x: x[1] if x else "---", key="sel_unidad")
                        with tc3:
                            cant_cajas = st.number_input("Cajas a abrir", min_value=1, value=1, step=1, key="num_cajas")
                            uds_por_caja = st.number_input("Unidades por caja", min_value=1, value=12, step=1, key="uds_caja")
                        
                        if st.button("🔄 Confirmar Traspaso de Stock", use_container_width=True):
                            if id_caja and id_unidad:
                                try:
                                    caja_data = df_solo_productos[df_solo_productos['id'] == id_caja[0]].iloc[0]
                                    unidad_data = df_solo_productos[df_solo_productos['id'] == id_unidad[0]].iloc[0]
                                    
                                    nuevo_stock_caja = int(float(caja_data.get('stock_actual', 0))) - int(cant_cajas)
                                    nuevo_stock_unidad = int(float(unidad_data.get('stock_actual', 0))) + int(cant_cajas * uds_por_caja)
                                    
                                    client.table("productos").update({"stock_actual": nuevo_stock_caja}).eq("id", id_caja[0]).execute()
                                    client.table("productos").update({"stock_actual": nuevo_stock_unidad}).eq("id", id_unidad[0]).execute()
                                    st.success(f"✅ Traspaso exitoso: Restado {cant_cajas} a [{caja_data['nombre']}]. Sumado {cant_cajas * uds_por_caja} a [{unidad_data['nombre']}].")
                                    st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                    limpiar_cache_inventario()
                                    time.sleep(2)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al traspasar: {e}")
                            else:
                                st.warning("Debes seleccionar la Caja de origen y la Unidad de destino.")
                    st.divider()

                    st.markdown("#### 📦 Inventario de Productos")

                    with st.expander("🤖 Auto-Categorizar con IA (Experimental)"):
                        st.write("Esta herramienta utiliza Gemini para rellenar automáticamente las categorías faltantes basándose en el nombre del producto.")
                        if st.button("🚀 Iniciar Auto-Categorización (Lote de 20)"):
                            def esta_incompleto(p):
                                import pandas as pd
                                def is_empty(val, default):
                                    if pd.isna(val) or val in [default, '', None]: return True
                                    return False
                                    
                                if is_empty(p.get('familia'), 'Generico'): return True
                                if is_empty(p.get('mascota'), 'Universal'): return True
                                if is_empty(p.get('subcategoria'), ''): return True
                                if is_empty(p.get('marca'), 'Generico'): return True
                                return False
                                
                            prods_incompletos = [p for p in df_solo_productos.to_dict('records') if esta_incompleto(p)]
                            if not prods_incompletos:
                                st.success("¡Todos los productos están perfectamente categorizados!")
                            else:
                                st.info(f"Se han encontrado {len(prods_incompletos)} productos sin categorizar. Procesando un lote de hasta 20...")
                                lote = prods_incompletos[:20]
                                res = procesar_lote_ia_gemini(lote, client)
                                if "error" in res:
                                    st.error(f"Error de IA: {res['error']}")
                                else:
                                    st.success(f"¡Se han categorizado {res.get('success', 0)} productos! Recargando...")
                                    time.sleep(2)
                                    limpiar_cache_inventario()
                                    st.rerun()

                    c_busq1, c_busq2 = st.columns([2, 1])
                    with c_busq1:
                        b_inv = st.text_input("🔍 Buscar producto (Nombre o SKU):", key="b_inv_p").strip().lower()
                    with c_busq2:
                        ord_inv = st.selectbox("↕️ Ordenar por:", ["Nombre (A-Z)", "SKU", "Mayor Stock", "Menor Stock", "Mayor Precio"], key="ord_inv_p")

                    if b_inv:
                        df_solo_productos = df_solo_productos[
                            df_solo_productos['nombre'].str.lower().str.contains(b_inv, na=False) |
                            df_solo_productos['sku'].str.lower().str.contains(b_inv, na=False)
                        ]

                    if ord_inv == "Nombre (A-Z)": df_solo_productos = df_solo_productos.sort_values(by="nombre")
                    elif ord_inv == "SKU": df_solo_productos = df_solo_productos.sort_values(by="sku")
                    elif ord_inv == "Mayor Stock": df_solo_productos = df_solo_productos.sort_values(by="stock_actual", ascending=False)
                    elif ord_inv == "Menor Stock": df_solo_productos = df_solo_productos.sort_values(by="stock_actual", ascending=True)
                    elif ord_inv == "Mayor Precio": df_solo_productos = df_solo_productos.sort_values(by="precio_pvp", ascending=False)

                    df_visual_p = df_solo_productos.drop(columns=["productos_proveedores"]) if "productos_proveedores" in df_solo_productos.columns else df_solo_productos
                    edit_p = st.data_editor(
                        df_visual_p,
                        column_config={
                            "id": None, "categoria": None, "categoria_filt": None,
                            "sku": "SKU", "codigo_barras": "Barras", "nombre": "Descripción",
                            "familia": st.column_config.SelectboxColumn("Categoría", options=["", "Alimentación húmeda", "Alimentación seca", "Snack", "Accesorios", "Higiene", "Paseo", "Juguetes", "Descanso", "Farmacia/Cuidados", "Otros"]),
                            "subcategoria": st.column_config.SelectboxColumn("Subcategoría", options=["", "Pienso Seco", "Pienso Húmedo", "Semi-húmedo", "Snacks", "Collares/Arneses", "Champús", "Medicamentos", "Juguetes", "Otros"]),
                            "gama": st.column_config.SelectboxColumn("Gama", options=["", "Grain free", "Low grain", "Wet line", "Atlantic Pet Special Bully", "Classic Supreme", "Classic Supreme gato", "Premium Receta gato", "Premium Receta", "Super Premium Receta", "Super Premium Receta grain free", "Ultra Premium Receta grain free", "Author", "Care", "Classic", "Hipoalergénico", "Just", "Prime", "Ultra"]),
                            "mascota": st.column_config.SelectboxColumn("Mascota", options=["", "Perro", "Gato", "Roedor", "Aves", "Reptiles", "Universal"]),
                            "edad": st.column_config.SelectboxColumn("Edad", options=["", "Adulto", "Cachorro/Kitten", "Senior", "Todas las edades"]),
                            "tamano": st.column_config.SelectboxColumn("Tamaño", options=["", "Grande", "Mediano", "Mini", "Pequeño", "Todas las razas"]),
                            "necesidad_especial": st.column_config.SelectboxColumn("Necesidad", options=["", "Articulaciones", "Bolas de pelo", "Control de peso", "Esterilizado", "Hipoalergénico", "Paladares exigentes", "Pelo blanco", "Sensible/digestivo", "Urinario", "Renal", "Hepático", "Ninguna"]),
                            "sabor_principal": st.column_config.SelectboxColumn("Sabor", options=["", "Atún", "Cerdo", "Ciervo", "Conejo", "Cordero", "Mix de carnes", "Pato", "Pavo", "Pescado", "Pollo", "Salmón", "Sin especificar", "Ternera/Buey"]),
                            "caracteristicas": st.column_config.TextColumn("Extra (Opcional)", help="Escribe separadas por comas. Ej: Grain Free, Monoproteico, Natural..."),
                            "marca": st.column_config.TextColumn("Marca", help="Marca del producto"),
                            "Proveedor": st.column_config.SelectboxColumn("Proveedor", options=["---"] + list(dict_proveedores.keys())),
                            "precio_base": st.column_config.NumberColumn("Costo Base", format="%.2f €"),
                            "igic_tipo": "IGIC %", "precio_pvp": st.column_config.NumberColumn("PVP (€)", format="%.2f", step=0.01), "stock_actual": "Stock",
                            "fecha_caducidad": st.column_config.DateColumn("Caducidad", format="DD/MM/YYYY"),
                            "stock_minimo": st.column_config.NumberColumn("Avisar en", step=1),
                            "cantidad_reponer": st.column_config.NumberColumn("Reponer Ud", step=1)
                        },
                        column_order=["sku", "codigo_barras", "nombre", "familia", "subcategoria", "gama", "mascota", "edad", "tamano", "necesidad_especial", "sabor_principal", "caracteristicas", "marca", "Proveedor", "precio_base", "igic_tipo", "precio_pvp", "stock_actual", "fecha_caducidad", "stock_minimo", "cantidad_reponer"],
                        hide_index=True, 
                        use_container_width=True, 
                        num_rows="dynamic",
                        key="edit_p_sep"
                    )

                    if st.button("💾 Guardar cambios en Productos", key="btn_save_p_sep"):
                        ids_actuales = edit_p['id'].dropna().tolist()
                        ids_originales = df_solo_productos['id'].tolist()
                        ids_a_borrar = [id_orig for id_orig in ids_originales if id_orig not in ids_actuales]

                        errores = []
                        for id_del in ids_a_borrar:
                            try:
                                client.table("productos").delete().eq("id", id_del).execute()
                            except Exception as e:
                                errores.append(f"Error al borrar producto: {e}")

                        for i, row in edit_p.iterrows():
                            if pd.notna(row['id']):
                                datos = row.to_dict()
                                prov_nombre = datos.get('Proveedor', '---')
                                
                                for col_eliminar in ['categoria_filt', 'Proveedor', 'productos_proveedores']:
                                    if col_eliminar in datos: del datos[col_eliminar]
                                    
                                datos = {k: (None if pd.isna(v) else v) for k, v in datos.items()}
                                    
                                if pd.isna(datos.get('fecha_caducidad')) or str(datos.get('fecha_caducidad')).strip() in ["", "None", "NaT"]:
                                    datos['fecha_caducidad'] = None
                                else:
                                    datos['fecha_caducidad'] = str(datos['fecha_caducidad'])
                                    
                                try:
                                    client.table("productos").update(datos).eq("id", row['id']).execute()
                                    
                                    client.table("productos_proveedores").delete().eq("producto_id", row['id']).execute()
                                    if prov_nombre != "---" and prov_nombre in dict_proveedores:
                                        client.table("productos_proveedores").insert({
                                            "producto_id": row['id'], "proveedor_id": dict_proveedores[prov_nombre], "precio_coste": float(datos.get('precio_base', 0.0))
                                        }).execute()
                                except Exception as e:
                                    errores.append(f"Error en '{row['nombre']}': {e}")
                                
                        if errores:
                            for err in errores: st.error(err)
                        else:
                            st.session_state["inventario_saved"] = True
                            st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                            limpiar_cache_inventario()
                            time.sleep(0.5)
                            st.rerun()

                elif seccion_inventario == "🐶 Servicios":
                    # --- TABLA DE SERVICIOS MEJORADA ---
                    st.markdown("#### ✂️ Catálogo de Servicios")
                    df_solo_servicios = df_inv[df_inv['categoria_filt'] == 'Servicio'].copy()
                    
                    c_busqs1, c_busqs2 = st.columns([2, 1])
                    with c_busqs1:
                        b_serv = st.text_input("🔍 Buscar servicio (Nombre o Código):", key="b_inv_s").strip().lower()
                    with c_busqs2:
                        ord_serv = st.selectbox("↕️ Ordenar por:", ["Nombre (A-Z)", "Código", "Mayor Precio", "Menor Precio"], key="ord_inv_s")

                    if b_serv:
                        df_solo_servicios = df_solo_servicios[
                            df_solo_servicios['nombre'].str.lower().str.contains(b_serv, na=False) |
                            df_solo_servicios['sku'].str.lower().str.contains(b_serv, na=False)
                        ]

                    if ord_serv == "Nombre (A-Z)": df_solo_servicios = df_solo_servicios.sort_values(by="nombre")
                    elif ord_serv == "Código": df_solo_servicios = df_solo_servicios.sort_values(by="sku")
                    elif ord_serv == "Mayor Precio": df_solo_servicios = df_solo_servicios.sort_values(by="precio_pvp", ascending=False)
                    elif ord_serv == "Menor Precio": df_solo_servicios = df_solo_servicios.sort_values(by="precio_pvp", ascending=True)

                    # Añadimos la columna calculada de Cuota de IGIC para mostrar el desglose
                    df_solo_servicios['Cuota IGIC (€)'] = df_solo_servicios['precio_pvp'] - df_solo_servicios['precio_base']

                    df_visual_s = df_solo_servicios.drop(columns=["productos_proveedores"]) if "productos_proveedores" in df_solo_servicios.columns else df_solo_servicios
                    # Habilitamos num_rows="dynamic" para que puedas borrar servicios
                    edit_s = st.data_editor(
                        df_visual_s,
                        column_config={
                            "id": None, "categoria": None, "categoria_filt": None,
                            "sku": "Código", "nombre": "Descripción del Servicio",
                            "precio_base": st.column_config.NumberColumn("Base Real sin IGIC (€)", format="%.2f", disabled=True, step=0.01),
                            "igic_tipo": st.column_config.SelectboxColumn("IGIC %", options=[7.0, 0.0, 3.0, 15.0]),
                            "Cuota IGIC (€)": st.column_config.NumberColumn("Cuota IGIC (€)", format="%.2f", disabled=True, step=0.01),
                            "precio_pvp": st.column_config.NumberColumn("Precio Cerrado (PVP) (€)", format="%.2f", step=0.01)
                        },
                        column_order=["sku", "nombre", "precio_base", "igic_tipo", "Cuota IGIC (€)", "precio_pvp"],
                        hide_index=True, 
                        use_container_width=True, 
                        num_rows="dynamic", # <--- PERMITE BORRAR FILAS DE SERVICIOS
                        key="edit_s_sep"
                    )

                    if st.button("💾 Guardar cambios en Servicios", key="btn_save_s_sep"):
                        ids_s_actuales = edit_s['id'].dropna().tolist()
                        ids_s_originales = df_solo_servicios['id'].tolist()
                        ids_s_a_borrar = [id_orig for id_orig in ids_s_originales if id_orig not in ids_s_actuales]

                        errores_s = []
                        for id_del in ids_s_a_borrar:
                            try:
                                client.table("productos").delete().eq("id", id_del).execute()
                            except Exception as e:
                                errores_s.append(f"Error al borrar servicio: {e}")

                        for i, row in edit_s.iterrows():
                            if pd.notna(row['id']):
                                nuevo_pvp = float(row['precio_pvp'])
                                nuevo_igic = float(row['igic_tipo'])
                                nueva_base = nuevo_pvp / (1 + (nuevo_igic / 100))
                                
                                try:
                                    client.table("productos").update({
                                        "sku": str(row['sku']), "nombre": str(row['nombre']),
                                        "precio_pvp": nuevo_pvp, "igic_tipo": nuevo_igic, "precio_base": nueva_base
                                    }).eq("id", row['id']).execute()
                                except Exception as e:
                                    errores_s.append(f"Error en '{row['nombre']}': {e}")

                        if errores_s:
                            for err in errores_s: st.error(err)
                        else:
                            st.session_state["inventario_saved"] = True
                            st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                            limpiar_cache_inventario()
                            time.sleep(0.5)
                            st.rerun()
                        
                elif seccion_inventario == "🛠️ Uso Interno":
                    st.markdown("#### 🏢 Traspaso para Uso Interno (Peluquería)")
                    st.info("💡 Descuenta productos del almacén para uso profesional en la tienda (champús, mascarillas...). Esto ajusta el stock sin generar ingresos en la caja, pero deja registro contable de uso interno a 0€.")
                    
                    c_ui1, c_ui2, c_ui3 = st.columns([2, 1, 1], vertical_alignment="bottom")
                    with c_ui1:
                        opciones_ui = df_solo_productos.apply(lambda x: f"{x['nombre']} | SKU: {x['sku']} (Stock: {x['stock_actual']})", axis=1).tolist()
                        prod_ui = st.selectbox("Selecciona el producto a consumir:", opciones_ui, index=None, placeholder="Busca un producto...")
                    with c_ui2:
                        cant_ui = st.number_input("Cantidad a retirar", min_value=1, value=1, step=1)
                    with c_ui3:
                        if st.button("🔽 Retirar de Stock", type="primary", use_container_width=True):
                            if prod_ui:
                                sku_ui = prod_ui.split(" | SKU: ")[1].split(" (Stock")[0]
                                item_ui = df_solo_productos[df_solo_productos['sku'] == sku_ui].iloc[0]
                                
                                if item_ui['stock_actual'] >= cant_ui:
                                    nuevo_stock = item_ui['stock_actual'] - cant_ui
                                    client.table("productos").update({"stock_actual": int(nuevo_stock)}).eq("id", item_ui['id']).execute()
                                    
                                    # Registro en compras (Traspaso Interno a coste cero)
                                    client.table("compras").insert({
                                        "proveedor_id": None, "total": 0.0, "estado": "Pagado",
                                        "tipo": f"Uso Interno | {item_ui['nombre']}", "fecha_vencimiento": str(pd.Timestamp.today().date()),
                                        "productos": [{"id": str(item_ui['id']), "Código": sku_ui, "Descripción": item_ui['nombre'], "Cantidad": cant_ui, "Base Ud": 0.0, "IGIC %": 0.0, "Desc %": 0.0, "PVP (€)": 0.0}],
                                        "pagado": 0.0, "pendiente": 0.0
                                    }).execute()
                                    
                                    st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                    st.success(f"Se han retirado {cant_ui} unidad(es) de {item_ui['nombre']} para uso interno."); time.sleep(1.5); limpiar_cache_inventario(); st.rerun()
                                else:
                                    st.error("No hay suficiente stock para realizar este traspaso.")
                            else:
                                st.warning("Selecciona un producto primero.")
            else:
                st.info("Inventario vacío.")
