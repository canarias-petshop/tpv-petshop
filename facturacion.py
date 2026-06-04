import streamlit as st
import pandas as pd
import time
from datetime import date, datetime
import json
import hashlib
from zoneinfo import ZoneInfo

def render_pestana_facturacion(client):
    if 'llave_fac_cli' not in st.session_state: st.session_state.llave_fac_cli = 0
    if 'llave_fac_art_v' not in st.session_state: st.session_state.llave_fac_art_v = 0
    if 'llave_fac_prov' not in st.session_state: st.session_state.llave_fac_prov = 0
    if 'llave_fac_art_c' not in st.session_state: st.session_state.llave_fac_art_c = 0

    st.markdown("<h3 style='margin-top: -15px;'> 📑  Gestión Integral de Facturación</h3>", unsafe_allow_html=True)

    sub_emitir, sub_registrar, sub_archivo, sub_pagos = st.tabs([
        " 🧾  Emitir Factura (Venta)", 
        " 📥  Registrar Compra (Proveedor)", 
        " 📂  Archivo de Documentos",
        " 💸  Pagos Pendientes"
    ])
    
    @st.cache_data(show_spinner=False, ttl=15)
    def get_inv_fac(v):
        _all = []
        _off = 0
        while True:
            _r = client.table("productos").select("id, sku, nombre, precio_base, igic_tipo, precio_pvp, stock_actual").range(_off, _off + 999).execute()
            if _r.data:
                _all.extend(_r.data)
                if len(_r.data) < 1000: break
                _off += 1000
            else: break
        return _all
        
    all_inv = get_inv_fac(st.session_state.get('db_version', 0))
    df_inv = pd.DataFrame(all_inv) if all_inv else pd.DataFrame()
    
    @st.cache_data(show_spinner=False, ttl=15)
    def get_cli_fac(v):
        _all = []
        _off = 0
        while True:
            _r = client.table("clientes").select("id, nombre_dueno, cif").range(_off, _off + 999).execute()
            if _r.data:
                _all.extend(_r.data)
                if len(_r.data) < 1000: break
                _off += 1000
            else: break
        return _all
        
    all_cli = get_cli_fac(st.session_state.get('db_version', 0))
    df_cli = pd.DataFrame(all_cli) if all_cli else pd.DataFrame()
    
    res_prov = client.table("proveedores").select("id, nombre_empresa, cif").execute()
    df_prov = pd.DataFrame(res_prov.data) if res_prov.data else pd.DataFrame()

    # ==========================================
    # SUB-TAB 1: EMITIR FACTURA DE VENTA (PVP LIMPIO)
    # ==========================================
    with sub_emitir:
        if 'factura_v_temp' not in st.session_state: st.session_state.factura_v_temp = []
        if 'llave_busqueda_v' not in st.session_state: st.session_state.llave_busqueda_v = 0
        
        c_h1, c_h2, c_h3 = st.columns(3)
        with c_h1: f_pago = st.selectbox("Forma de Pago", ["Efectivo", "Tarjeta", "Bizum", "Transferencia"], key="fv_p_sel")
        with c_h2: f_emision = st.date_input("Fecha Emisión", key="fv_f_sel")
        with c_h3: f_vence = st.date_input("Vencimiento", key="fv_v_sel")
        
        with st.expander(" 👤  Seleccionar / Crear Cliente"):
            c_opc = df_cli.apply(lambda x: f"{x['nombre_dueno']} | CIF: {x.get('cif','-')}", axis=1).tolist() if not df_cli.empty else []
            sel_c = st.selectbox("Cliente:", c_opc, index=None, placeholder="Busca un cliente...")
            with st.form("n_cli_rap", clear_on_submit=True):
                nc1, nc2 = st.columns(2); n_n = nc1.text_input("Nombre*", key=f"fac_nn_{st.session_state.llave_fac_cli}"); n_c = nc2.text_input("CIF*", key=f"fac_nc_{st.session_state.llave_fac_cli}")
                if st.form_submit_button("Crear Cliente"):
                    if n_n and n_c: 
                        client.table("clientes").insert({"nombre_dueno": n_n, "cif": n_c}).execute()
                        st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                        st.session_state.llave_fac_cli += 1
                        st.rerun()
        
        st.markdown("####  📦  Añadir Artículos a la Venta")
        if not df_inv.empty:
            opciones_v = df_inv.apply(lambda x: f"{x['nombre']} | SKU: {x['sku']}", axis=1).tolist()
            prod_v = st.selectbox("🔍 Buscar producto en almacén:", opciones_v, index=None, key=f"search_v_alta_{st.session_state.llave_busqueda_v}", placeholder="Escribe para filtrar...")
            
            if prod_v:
                sku_v = prod_v.split(" | SKU: ")[1]
                it_v = df_inv[df_inv['sku'] == sku_v].iloc[0]
                st.session_state.factura_v_temp.append({
                    "id": str(it_v['id']), "Código": it_v['sku'], "Descripción": it_v['nombre'],
                    "Cantidad": 1, "Base Ud": float(it_v.get('precio_base', float(it_v['precio_pvp'])/1.07)), "IGIC %": float(it_v.get('igic_tipo', 7.0)), "Precio Venta": float(it_v['precio_pvp']), "Desc %": 0.0
                })
                st.session_state.llave_busqueda_v += 1 
                st.rerun()
                
        with st.expander("✨ ¿Artículo manual o nuevo producto?"):
            with st.form("form_nuevo_art_venta", clear_on_submit=True):
                st.markdown("<p style='font-size:13px; color:gray;'>Añade un artículo manual a la factura. Si dejas marcada la casilla, también se guardará permanentemente en el Inventario.</p>", unsafe_allow_html=True)
                col_m1, col_m2 = st.columns(2)
                with col_m1: m_nom = st.text_input("Nombre del Artículo *", key=f"fav_nom_{st.session_state.llave_fac_art_v}")
                with col_m2: m_sku = st.text_input("SKU / Ref (Opcional si no se guarda)", key=f"fav_sku_{st.session_state.llave_fac_art_v}")
                
                col_m3, col_m4, col_m5 = st.columns(3)
                with col_m3: m_pvp = st.number_input("Precio Venta Público (€) *", min_value=0.0, format="%.2f", step=0.01, key=f"fav_pvp_{st.session_state.llave_fac_art_v}")
                with col_m4: m_igic = st.selectbox("IGIC %", [7.0, 0.0, 3.0, 15.0], key=f"fav_igic_{st.session_state.llave_fac_art_v}")
                with col_m5: m_cant = st.number_input("Cantidad a facturar", min_value=1, value=1, key=f"fav_can_{st.session_state.llave_fac_art_v}")
                
                add_to_stock = st.checkbox("💾 Guardar permanentemente en Inventario", value=True)
                
                if st.form_submit_button("➕ Añadir a la Factura", type="primary", use_container_width=True):
                    if m_nom and m_pvp >= 0:
                        nuevo_id = "0"
                        if add_to_stock:
                            if not m_sku:
                                st.warning("⚠️ Para guardarlo en el inventario necesitas ponerle un SKU / Ref.")
                            else:
                                m_base = m_pvp / (1 + (m_igic / 100))
                                res_new = client.table("productos").insert({
                                    "nombre": m_nom, "sku": m_sku, "precio_base": m_base, "igic_tipo": m_igic, 
                                    "precio_pvp": m_pvp, "categoria": "Producto", "stock_actual": 0, "stock_minimo": 2, "cantidad_reponer": 5
                                }).execute()
                                if res_new.data:
                                    nuevo_id = str(res_new.data[0]['id'])
                        
                        m_base_val = m_pvp / (1 + (m_igic / 100))
                        if not add_to_stock or (add_to_stock and m_sku):
                            st.session_state.factura_v_temp.append({
                                "id": str(nuevo_id), "Código": m_sku if m_sku else "---", "Descripción": m_nom,
                                "Cantidad": m_cant, "Base Ud": m_base_val, "IGIC %": m_igic, "Precio Venta": m_pvp, "Desc %": 0.0
                            })
                            st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                            st.session_state.llave_fac_art_v += 1
                            st.success("Artículo añadido a la factura."); time.sleep(0.5); st.rerun()
                    else:
                        st.error("El nombre y el precio de venta son obligatorios.")
        
        if st.session_state.factura_v_temp:
            # Parche anti-fantasmas
            if 'Precio Venta' not in st.session_state.factura_v_temp[0]:
                st.session_state.factura_v_temp = []; st.rerun()
                
            for item in st.session_state.factura_v_temp:
                if 'Base Ud' not in item:
                    item['Base Ud'] = item['Precio Venta'] / 1.07
                    item['IGIC %'] = 7.0

            df_v = pd.DataFrame(st.session_state.factura_v_temp)
            df_v['Base Ud'] = df_v['Precio Venta'] / (1 + df_v['IGIC %'] / 100)
            df_v['Base Neta'] = (df_v['Base Ud'] * df_v['Cantidad']) * (1 - df_v['Desc %']/100)
            df_v['IGIC €'] = (df_v['Base Neta'] * (df_v['IGIC %']/100)).round(2)
            df_v['Total Línea'] = (df_v['Precio Venta'] * df_v['Cantidad']) * (1 - df_v['Desc %']/100)
            df_v['Total Línea'] = df_v['Total Línea'].round(2)

            df_v_edit = st.data_editor(
                df_v, hide_index=True, use_container_width=True, key="ed_v_final",
                num_rows="dynamic",
                column_config={
                    "id": None, "Base Ud": None, "IGIC %": None, "Base Neta": None, "IGIC €": None,
                    "Código": st.column_config.TextColumn(disabled=True),
                    "Descripción": st.column_config.TextColumn(disabled=True),
                    "Cantidad": st.column_config.NumberColumn("Cant.", min_value=1),
                    "Precio Venta": st.column_config.NumberColumn("Precio Venta (€)", format="%.2f", step=0.01),
                    "Desc %": st.column_config.NumberColumn("Desc. %", min_value=0.0, step=0.01, format="%.2f"),
                    "Total Línea": st.column_config.NumberColumn("Total Línea (€)", disabled=True, format="%.2f", step=0.01)
                }
            )
            
            df_v_edit['IGIC %'] = df_v_edit['IGIC %'].fillna(7.0)
            df_v_edit['Base Ud'] = df_v_edit['Precio Venta'] / (1 + df_v_edit['IGIC %'] / 100)

            nuevos_datos_v = df_v_edit[['id', 'Código', 'Descripción', 'Cantidad', 'Base Ud', 'IGIC %', 'Precio Venta', 'Desc %']].to_dict('records')
            if nuevos_datos_v != st.session_state.factura_v_temp:
                st.session_state.factura_v_temp = nuevos_datos_v
                st.rerun()

            suma_base_v = df_v['Base Neta'].sum()
            suma_igic_v = df_v['IGIC €'].sum()
            suma_articulos_v = df_v['Total Línea'].sum()
            st.markdown("---")
            col_v1, col_v2 = st.columns([1, 2])
            with col_v1:
                desc_g_v = st.number_input(" 🎁  Dto. Global (%)", 0.0, 100.0, value=None, key="desc_v_alta", step=0.01, format="%.2f")
            
            desc_g_val = float(desc_g_v or 0.0)
            total_base_final = suma_base_v * (1 - desc_g_val / 100)
            total_igic_final = suma_igic_v * (1 - desc_g_val / 100)
            total_v_final = suma_articulos_v * (1 - desc_g_val / 100)

            with col_v2:
                st.markdown(f"""
                <div style="background-color: #f0f7f9; padding: 15px; border-radius: 10px; border-left: 5px solid #005275; text-align: right;">
                <p style="margin:0; font-size: 14px;">Base Neta: {total_base_final:.2f}€ | IGIC: {total_igic_final:.2f}€</p>
                <h2 style="margin:0; color: #005275;">TOTAL FACTURA: {total_v_final:.2f}€</h2>
                </div>
                """, unsafe_allow_html=True)
            
            if st.button(" 🚀  EMITIR FACTURA", type="primary", use_container_width=True):
                # --- PROTECCIÓN DOBLE CLIC BACKEND ---
                current_time = time.time()
                if current_time - st.session_state.get('last_fac_time', 0) < 3:
                    st.stop()
                st.session_state['last_fac_time'] = current_time

                if sel_c:
                    c_id = df_cli[df_cli['nombre_dueno'] == sel_c.split(" | ")[0]].iloc[0]['id']
                    
                    # GENERACIÓN DE HASH (LEY ANTIFRAUDE / VERIFACTU)
                    res_last_f = client.table("facturas").select("hash_actual").order("id", desc=True).limit(1).execute()
                    hash_ant_f = res_last_f.data[0].get("hash_actual", "") if res_last_f.data else ""
                    data_to_hash_f = f"FACTURA|{datetime.now(ZoneInfo('Atlantic/Canary')).isoformat()}|{total_v_final:.2f}|{hash_ant_f}"
                    hash_act_f = hashlib.sha256(data_to_hash_f.encode('utf-8')).hexdigest().upper()

                    client.table("facturas").insert({
                        "cliente_id": c_id, "total_neto": float(total_base_final), "total_igic": float(total_igic_final), "total_final": float(total_v_final),
                        "descuento_global": float(desc_g_val), "forma_pago": f_pago, "fecha_vencimiento": str(f_vence), "productos": st.session_state.factura_v_temp,
                        "hash_anterior": hash_ant_f, "hash_actual": hash_act_f
                    }).execute()
                    for i in st.session_state.factura_v_temp:
                        if str(i.get('id', '0')) != '0' and str(i.get('id')) != 'None':
                            if str(i['id']).startswith('cita_'):
                                continue
                            try:
                                res = client.table("productos").select("stock_actual").eq("id", i['id']).execute()
                                if res.data: client.table("productos").update({"stock_actual": res.data[0]['stock_actual'] - i['Cantidad']}).eq("id", i['id']).execute()
                            except Exception:
                                pass
                    
                    st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                    st.session_state.factura_v_temp = []; st.success("Factura guardada correctamente."); time.sleep(1); st.rerun()
                else:
                    st.error("Debes seleccionar un cliente para emitir la factura.")

    # ==========================================
    # SUB-TAB 2: REGISTRAR COMPRA (PROVEEDOR)
    # ==========================================
    with sub_registrar:
        if 'compra_temp' not in st.session_state: st.session_state.compra_temp = []
        if 'llave_busqueda_c' not in st.session_state: st.session_state.llave_busqueda_c = 0
        if 'pedido_vinculado' not in st.session_state: st.session_state.pedido_vinculado = None
            
        c_tit1, c_tit2 = st.columns([2, 1], vertical_alignment="bottom")
        with c_tit1:
            st.markdown("#### 🤖 Escáner de Facturas con IA")
        with c_tit2:
            if st.button("📂 Abrir Carpeta de Facturas", use_container_width=True):
                import os
                import platform
                import subprocess
                
                es_wsl = (platform.system() == "Linux" and "microsoft" in platform.uname().release.lower())
                
                if es_wsl:
                    ruta_base = "/mnt/c/Users/truji/OneDrive/Documentos/ANIMALARIUM/TPV ANIMALARIUM/CONTABILIDAD/Facturas digitales"
                else:
                    ruta_base = r"C:\Users\truji\OneDrive\Documentos\ANIMALARIUM\TPV ANIMALARIUM\CONTABILIDAD\Facturas digitales"
                    
                carpeta_mes = os.path.join(ruta_base, str(datetime.now().year), f"{datetime.now().month:02d}")
                if not es_wsl:
                    carpeta_mes = carpeta_mes.replace("/", "\\")
                
                try: 
                    os.makedirs(carpeta_mes, exist_ok=True)
                    if es_wsl:
                        win_path = f"C:\\Users\\truji\\OneDrive\\Documentos\\ANIMALARIUM\\TPV ANIMALARIUM\\CONTABILIDAD\\Facturas digitales\\{datetime.now().year}\\{datetime.now().month:02d}"
                        subprocess.Popen(["explorer.exe", win_path])
                    elif platform.system() == "Windows" and hasattr(os, 'startfile'): 
                        os.startfile(carpeta_mes.replace("/", "\\"))
                    elif hasattr(os, 'startfile'): 
                        os.startfile(carpeta_mes)
                    elif platform.system() == "Darwin": subprocess.Popen(["open", carpeta_mes])
                    else:
                        import shutil
                        if shutil.which("explorer.exe"): subprocess.Popen(["explorer.exe", carpeta_mes])
                        else: st.info(f"📁 Carpeta lista: {carpeta_mes}")
                except Exception: st.info(f"📁 Carpeta lista: {carpeta_mes}")
                
        with st.container(border=True):
            col_ia1, col_ia2 = st.columns([2, 1], vertical_alignment="bottom")
            with col_ia1:
                t_subir, t_cam = st.tabs(["📂 Subir Archivo", "📷 Usar Cámara"])
                with t_subir:
                    archs_subidos = st.file_uploader("📸 Sube una o varias fotos (o PDF)", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True, key="file_ia_compra")
                with t_cam:
                    arch_cam = st.camera_input("Toma la foto con tu cámara", label_visibility="collapsed", key="cam_ia_compra")
                
                archivos_factura = archs_subidos if archs_subidos else ([arch_cam] if arch_cam else [])
            with col_ia2:
                if st.button("✨ Auto-completar con IA", use_container_width=True, type="primary"):
                    if archivos_factura:
                        with st.spinner("🧠 Leyendo documento con Gemini IA... esto puede tardar unos segundos."):
                            try:
                                import google.generativeai as genai
                                from PIL import Image
                                import os
                                
                                if "gemini_api_key" not in st.secrets:
                                    st.error("🔑 Falta la clave 'gemini_api_key' en secrets.toml")
                                    st.stop()
                                    
                                genai.configure(api_key=st.secrets["gemini_api_key"])
                                
                                prompt = """
                                Eres un contable experto y un sistema de lectura OCR de máxima precisión.
                                
                                REGLAS ESTRICTAS ANTI-INVENCIÓN:
                                1. NUNCA INVENTES DATOS. Si la imagen está borrosa o un texto no se lee perfectamente, sáltalo o déjalo en cero.
                                2. Escribe EXACTAMENTE el nombre del producto que aparece en el papel. No inventes marcas ni añadas productos que no estén explícitamente escritos ahí.
                                3. Extrae exactamente las cantidades y precios unitarios. NO pongas descuentos si no vienen indicados en el papel claramente.
                                4. El 'precio_base' debe ser estrictamente el precio unitario SIN impuestos. El 'igic_porcentaje' debe ser el % de IGIC aplicado a esa línea (ej: 3.0, 7.0).
                                5. Devuelve los datos ESTRICTAMENTE en este formato JSON, sin texto adicional ni markdown:
                                {
                                  "numero_factura": "12345",
                                  "fecha_factura": "YYYY-MM-DD",
                                  "nombre_proveedor": "Nombre de la Empresa (Busca en logotipos, emails o webs impresas si no hay texto claro)",
                                  "descuento_pronto_pago_porcentaje": 0.0,
                                  "articulos": [
                                    {
                                      "descripcion": "Nombre EXACTO del articulo tal cual aparece",
                                      "codigo_referencia_o_barras": "12345678",
                                      "cantidad": 1,
                                      "precio_base": 12.50,
                                      "igic_porcentaje": 7.0,
                                      "descuento_porcentaje": 0.0,
                                      "precio_pvp": 15.50,
                                      "lote": "L-1234",
                                      "fecha_caducidad": "YYYY-MM-DD"
                                    }
                                  ]
                                }
                                Si no encuentras un dato o IGIC, pon 0 o déjalo vacío (""). Si no hay caducidad explícita, usa null.
                                """
                                
                                payload = [prompt]
                                for arch in archivos_factura:
                                    arch.seek(0) # Reinicia la memoria del archivo por seguridad
                                    if arch.name.lower().endswith(".pdf"):
                                        payload.append({"mime_type": "application/pdf", "data": arch.read()})
                                    else:
                                        payload.append(Image.open(arch))
                                
                                response = None
                                ultimo_error = None
                                
                                # 1. Lista oficial de modelos estables y seguros
                                modelos_a_probar = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.5-flash-latest']
                                
                                # 2. Preguntar a Google qué más hay, esquivando modelos experimentales o retirados
                                try:
                                    for m in genai.list_models():
                                        if 'generateContent' in m.supported_generation_methods:
                                            m_name = m.name.replace('models/', '')
                                            m_low = m_name.lower()
                                            # Filtrar nombres peligrosos o en pruebas (como el robotics)
                                            if 'preview' not in m_low and 'robotics' not in m_low and 'experimental' not in m_low:
                                                if ('1.5' in m_low or 'vision' in m_low or 'gemini' in m_low):
                                                    if m_name not in modelos_a_probar:
                                                        modelos_a_probar.append(m_name)
                                except Exception:
                                    pass
                                
                                # 3. Escanear con el modelo correcto
                                errores_lista = []
                                for m_name in modelos_a_probar:
                                    try:
                                        model = genai.GenerativeModel(m_name)
                                        response = model.generate_content(payload)
                                        break
                                    except Exception as e:
                                        ultimo_error = e
                                        errores_lista.append(f"[{m_name} falló]")
                                        continue
                                        
                                if not response:
                                    raise Exception(f"Fallaron todos los modelos. Detalles: {' '.join(errores_lista)} | Último error: {ultimo_error}")
                                
                                res_text = response.text.strip()
                                if res_text.startswith("```json"): res_text = res_text[7:]
                                elif res_text.startswith("```"): res_text = res_text[3:]
                                if res_text.endswith("```"): res_text = res_text[:-3]
                                
                                datos_ia = json.loads(res_text.strip())
                                
                                def parse_float_ia(val):
                                    try:
                                        if isinstance(val, str): val = val.replace(',', '.')
                                        return float(val)
                                    except: return 0.0
                                
                                # Auto-completar campos de cabecera
                                if datos_ia.get("numero_factura"): st.session_state["fac_prov_n"] = datos_ia["numero_factura"]
                                try:
                                    if datos_ia.get("fecha_factura"): st.session_state["fac_prov_f"] = datetime.strptime(datos_ia["fecha_factura"], "%Y-%m-%d").date()
                                except: pass
                                
                                st.session_state["ia_dto_pp"] = parse_float_ia(datos_ia.get("descuento_pronto_pago_porcentaje", 0.0))
                                
                                # Intentar enlazar Proveedor inteligente
                                prov_ia = datos_ia.get("nombre_proveedor", "").lower()
                                if prov_ia:
                                    for p_oficial in df_prov['nombre_empresa'].tolist():
                                        if prov_ia in p_oficial.lower() or p_oficial.lower() in prov_ia:
                                            st.session_state["sel_prov_ia_tmp"] = p_oficial
                                            break
                                
                                # Volcar artículos a la tabla
                                st.session_state.compra_temp = []
                                for art in datos_ia.get("articulos", []):
                                    desc = art.get("descripcion", "Artículo desconocido")
                                    cant = int(parse_float_ia(art.get("cantidad", 1)) or 1)
                                    p_base = parse_float_ia(art.get("precio_base", 0.0))
                                    igic = parse_float_ia(art.get("igic_porcentaje", 0.0))
                                    desc_linea = parse_float_ia(art.get("descuento_porcentaje", 0.0))
                                    pvp_ia = parse_float_ia(art.get("precio_pvp", 0.0))
                                    ref_barras = art.get("codigo_referencia_o_barras", "")
                                    lote = art.get("lote", "")
                                    cad = art.get("fecha_caducidad")
                                    
                                    # Intentar cruzar con Inventario
                                    if not df_inv.empty: match = df_inv[df_inv['nombre'].astype(str).str.lower() == desc.lower()]
                                    if not df_inv.empty: 
                                        term = desc.lower().strip()
                                        match = df_inv[df_inv['nombre'].astype(str).str.lower() == term]
                                        if match.empty:
                                            match = df_inv[df_inv['nombre'].astype(str).str.lower().str.contains(term, regex=False, na=False)]
                                    else: match = pd.DataFrame()
                                        
                                    if not match.empty:
                                        item = match.iloc[0]
                                        pvp_final = float(item.get('precio_pvp', 0.0))
                                        if pvp_final == 0.0 and pvp_ia > 0.0: pvp_final = pvp_ia
                                            
                                        st.session_state.compra_temp.append({
                                            "id": str(item['id']), "Código": item['sku'], "Descripción": item['nombre'],
                                            "Cantidad": cant, "Base Ud": p_base, "IGIC %": igic, "Desc %": desc_linea, "PVP (€)": pvp_final,
                                            "Lote": lote,
                                            "Caducidad": cad if cad else None
                                        })
                                    else:
                                        # AUTO-CREACIÓN INTELIGENTE DE PRODUCTO CON SKU CORRELATIVO (2 LETRAS)
                                        letras = ''.join([c for c in desc if c.isalpha()]).upper()
                                        prefijo = letras[:2] if len(letras) >= 2 else (letras + "X" if letras else "XX")
                                        
                                        res_sku = client.table("productos").select("sku").like("sku", f"{prefijo}-%").execute()
                                        max_num = 0
                                        if res_sku.data:
                                            for s in res_sku.data:
                                                try:
                                                    num = int(s['sku'].split("-")[1])
                                                    if num > max_num: max_num = num
                                                except: pass
                                        nuevo_sku = f"{prefijo}-{max_num + 1:03d}"
                                        
                                        res_new = client.table("productos").insert({
                                            "nombre": desc, "sku": nuevo_sku, "codigo_barras": ref_barras,
                                            "precio_base": p_base, "igic_tipo": igic, "precio_pvp": pvp_ia,
                                            "categoria": "Producto", "stock_actual": 0, "stock_minimo": 2, "cantidad_reponer": 5
                                        }).execute()
                                        
                                        nuevo_id = "0"
                                        if res_new.data:
                                            nuevo_id = str(res_new.data[0]['id'])
                                            if "sel_prov_ia_tmp" in st.session_state and st.session_state["sel_prov_ia_tmp"]:
                                                try:
                                                    p_id_sel = df_prov[df_prov['nombre_empresa'] == st.session_state["sel_prov_ia_tmp"]].iloc[0]['id']
                                                    client.table("productos_proveedores").insert({
                                                        "producto_id": int(nuevo_id), "proveedor_id": p_id_sel, "precio_coste": p_base
                                                    }).execute()
                                                except: pass
                                                
                                        st.session_state.compra_temp.append({
                                            "id": nuevo_id, "Código": nuevo_sku, "Descripción": desc,
                                            "Cantidad": cant, "Base Ud": p_base, "IGIC %": igic, "Desc %": desc_linea, "PVP (€)": pvp_ia,
                                            "Lote": lote,
                                            "Caducidad": cad if cad else None
                                        })
                                        
                                # Archivo Fiscal Físico (Guardar foto en local)
                                mensaje_archivo = ""
                                try:
                                    import platform
                                    es_wsl = (platform.system() == "Linux" and "microsoft" in platform.uname().release.lower())
                                    
                                    if es_wsl: RUTA_BASE_FACTURAS = "/mnt/c/Users/truji/OneDrive/Documentos/ANIMALARIUM/TPV ANIMALARIUM/CONTABILIDAD/Facturas digitales"
                                    else: RUTA_BASE_FACTURAS = r"C:\Users\truji\OneDrive\Documentos\ANIMALARIUM\TPV ANIMALARIUM\CONTABILIDAD\Facturas digitales"
                                        
                                    carpeta_facturas = os.path.join(RUTA_BASE_FACTURAS, str(datetime.now().year), f"{datetime.now().month:02d}")
                                    if not es_wsl:
                                        carpeta_facturas = carpeta_facturas.replace("/", "\\")
                                        
                                    os.makedirs(carpeta_facturas, exist_ok=True)
                                    
                                    import re
                                    n_prov_archivo = re.sub(r'[\\/*?:"<>|]', "", str(datos_ia.get("nombre_proveedor", "Acreedor"))).replace(" ", "_")
                                    n_fac_archivo = re.sub(r'[\\/*?:"<>|]', "", str(datos_ia.get("numero_factura", "SinNum"))).replace(" ", "_")
                                    
                                    for idx, arch in enumerate(archivos_factura):
                                        ext = "pdf" if arch.name.lower().endswith(".pdf") else "jpg"
                                        ruta_archivo = os.path.join(carpeta_facturas, f"{n_prov_archivo}_{n_fac_archivo}_{int(time.time())}_{idx}.{ext}")
                                        with open(ruta_archivo, "wb") as f:
                                            f.write(arch.getvalue())
                                            
                                    mensaje_archivo = f"(📁 Guardadas en: {carpeta_facturas})"
                                except Exception as e:
                                    pass # Fallo silencioso si no hay permisos de disco
                                    mensaje_archivo = f"(⚠️ Error al guardar foto: {e})"
                                    
                                # ====== GUARDAR COMO BORRADOR AUTOMÁTICAMENTE ======
                                prov_id_final = None
                                if "sel_prov_ia_tmp" in st.session_state and st.session_state["sel_prov_ia_tmp"]:
                                    try: prov_id_final = df_prov[df_prov['nombre_empresa'] == st.session_state["sel_prov_ia_tmp"]].iloc[0]['id']
                                    except: pass
                                
                                if not prov_id_final:
                                    nombre_prov_nuevo = datos_ia.get("nombre_proveedor", "Proveedor Desconocido").strip()
                                    res_new_prov = client.table("proveedores").insert({"nombre_empresa": nombre_prov_nuevo, "cif": ""}).execute()
                                    if res_new_prov.data: prov_id_final = res_new_prov.data[0]['id']

                                total_compra = 0.0
                                for art in st.session_state.compra_temp:
                                    base_neta = (art['Base Ud'] * art['Cantidad']) * (1 - art['Desc %'] / 100)
                                    total_compra += base_neta * (1 + art['IGIC %'] / 100)
                                
                                dto_pp_val = parse_float_ia(datos_ia.get("descuento_pronto_pago_porcentaje", 0.0))
                                total_compra = total_compra * (1 - dto_pp_val / 100)
                                
                                num_fac = datos_ia.get("numero_factura", "S/N")
                                fecha_fac = datos_ia.get("fecha_factura", str(datetime.now().date()))
                                
                                client.table("compras").insert({
                                    "proveedor_id": prov_id_final, "total": round(total_compra, 2), "descuento_pp": dto_pp_val,
                                    "estado": "Borrador", "tipo": f"Factura: {num_fac}", "fecha_vencimiento": fecha_fac,
                                    "productos": st.session_state.compra_temp,
                                    "pagado": 0.0, "pendiente": round(total_compra, 2)
                                }).execute()
                                
                                st.session_state.compra_temp = []
                                for key in ["fac_prov_n", "fac_prov_f", "ia_dto_pp", "sel_prov_ia_tmp"]:
                                    if key in st.session_state: del st.session_state[key]
                                # ===================================================

                                st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                                st.success(f"✅ ¡Factura escaneada y guardada en BORRADOR! Ve a 'Archivo de Documentos' para validarla. {mensaje_archivo}")
                                time.sleep(2.5)
                                st.rerun()
                            except ImportError:
                                st.error("🚨 Faltan librerías. Abre tu consola y ejecuta: pip install google-generativeai pillow")
                            except Exception as e:
                                st.error(f"❌ Error leyendo factura: {e}")
                    else:
                        st.warning("⚠️ Sube una imagen o PDF primero.")
        
        st.markdown("---")

        c_c1, c_c2, c_c3 = st.columns(3)
        with c_c1: n_fac = st.text_input("Nº Factura Proveedor", key="fac_prov_n")
        with c_c2: f_fac = st.date_input("Fecha Factura", key="fac_prov_f")
        with c_c3: f_ven = st.date_input("Vencimiento", key="fac_prov_v")
        
        with st.expander(" 🚚  Seleccionar / Crear Proveedor", expanded=True):
            p_opc = df_prov['nombre_empresa'].tolist() if not df_prov.empty else []
            
            def_prov_idx = None
            if "sel_prov_ia_tmp" in st.session_state and st.session_state["sel_prov_ia_tmp"] in p_opc:
                def_prov_idx = p_opc.index(st.session_state["sel_prov_ia_tmp"])
                
            sel_p = st.selectbox("Selecciona el Proveedor:", p_opc, index=def_prov_idx, placeholder="Escribe el nombre del proveedor...")
            with st.form("form_nuevo_proveedor_rapido", clear_on_submit=True):
                np1, np2 = st.columns(2); n_emp_new = np1.text_input("Nombre Empresa*", key=f"fnp_emp_{st.session_state.llave_fac_prov}"); n_cif_new = np2.text_input("CIF", key=f"fnp_cif_{st.session_state.llave_fac_prov}")
                if st.form_submit_button("➕ Crear Nuevo Proveedor"):
                    if n_emp_new: 
                        client.table("proveedores").insert({"nombre_empresa": n_emp_new, "cif": n_cif_new}).execute()
                        st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                        st.session_state.llave_fac_prov += 1
                        st.rerun()
                        
        st.markdown("---")
        
        with st.expander("📥 Cargar desde Pedido a Proveedor (Automatización)", expanded=False):
            res_pedidos_p = client.table("pedidos_proveedores").select("id, estado, proveedores(nombre_empresa)").in_("estado", ["Borrador", "Enviado"]).execute()
            if res_pedidos_p.data:
                opc_ped = {f"Pedido #{p['id']} - {p['proveedores']['nombre_empresa']} ({p['estado']})": p['id'] for p in res_pedidos_p.data if p.get('proveedores')}
                p_sel_str = st.selectbox("Selecciona un pedido pendiente:", [""] + list(opc_ped.keys()))
                if st.button("⬇️ Cargar Artículos del Pedido"):
                    if p_sel_str:
                        ped_id = opc_ped[p_sel_str]
                        st.session_state.pedido_vinculado = ped_id
                        ped_data = client.table("pedidos_proveedores").select("productos").eq("id", ped_id).execute().data[0]
                        st.session_state.compra_temp = []
                        for art in ped_data.get('productos', []):
                            res_match = client.table("productos").select("id, sku, nombre, precio_base, igic_tipo, precio_pvp").eq("nombre", art['Producto']).execute()
                            if res_match.data:
                                item = res_match.data[0]
                                st.session_state.compra_temp.append({
                                    "id": str(item['id']), "Código": item['sku'], "Descripción": item['nombre'],
                                    "Cantidad": art['Cantidad'], "Base Ud": float(item['precio_base']), "IGIC %": float(item['igic_tipo']), "Desc %": 0.0, "PVP (€)": float(item.get('precio_pvp', 0.0)),
                                    "Caducidad": None
                                })
                        st.success("Artículos cargados en la tabla inferior."); time.sleep(1); st.rerun()
            else:
                st.info("No hay pedidos pendientes.")

        st.markdown("####  📦  Añadir Artículos a la Compra")
        
        if not df_inv.empty:
            opciones_inv = df_inv.apply(lambda x: f"{x['nombre']} | SKU: {x['sku']}", axis=1).tolist()
            prod_buscado = st.selectbox("🔍 Buscar producto en almacén:", opciones_inv, index=None, key=f"sel_c_doc_{st.session_state.llave_busqueda_c}", placeholder="Escribe para filtrar...")
            if prod_buscado:
                sku_extraido = prod_buscado.split(" | SKU: ")[1]
                item = df_inv[df_inv['sku'] == sku_extraido].iloc[0]
                st.session_state.compra_temp.append({
                    "id": str(item['id']), "Código": item['sku'], "Descripción": item['nombre'],
                    "Cantidad": 1, "Base Ud": float(item['precio_base']), "IGIC %": float(item['igic_tipo']), "Desc %": 0.0, "PVP (€)": float(item.get('precio_pvp', 0.0)),
                    "Caducidad": None
                })
                st.session_state.llave_busqueda_c += 1; st.rerun()

        with st.expander("✨ ¿Artículo manual o nuevo producto?"):
            with st.form("form_nuevo_art_compra", clear_on_submit=True):
                st.markdown("<p style='font-size:13px; color:gray;'>Añade un artículo manual a la factura. Si dejas marcada la casilla, también se guardará permanentemente en el Inventario.</p>", unsafe_allow_html=True)
                col_m1, col_m2 = st.columns(2)
                with col_m1: m_nom = st.text_input("Nombre del Artículo *", key=f"fac_nom_{st.session_state.llave_fac_art_c}")
                with col_m2: m_sku = st.text_input("SKU / Ref (Opcional)", key=f"fac_sku_{st.session_state.llave_fac_art_c}")
                
                col_m3, col_m4, col_m5 = st.columns(3)
                with col_m3: m_base = st.number_input("Precio Base Compra (€) *", min_value=0.0, format="%.2f", step=0.01, key=f"fac_bas_{st.session_state.llave_fac_art_c}")
                with col_m4: m_igic = st.selectbox("IGIC %", [7.0, 0.0, 3.0, 15.0], key=f"fac_igic_{st.session_state.llave_fac_art_c}")
                with col_m5: m_cant = st.number_input("Cantidad a registrar", min_value=1, value=1, key=f"fac_can_{st.session_state.llave_fac_art_c}")
                
                col_m6, col_m7, col_m8 = st.columns([1, 1, 1.2])
                with col_m6: m_pvp = st.number_input("PVP Público (€)", min_value=0.0, format="%.2f", step=0.01, key=f"fac_pvp_{st.session_state.llave_fac_art_c}")
                with col_m7: m_cad = st.date_input("Caducidad (Opc)", value=None, key=f"fac_cad_{st.session_state.llave_fac_art_c}")
                with col_m8:
                    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                    add_to_stock = st.checkbox("💾 Guardar en Inventario", value=True)
                
                if st.form_submit_button("➕ Añadir a la Compra", type="primary", use_container_width=True):
                    m_base_val = float(m_base or 0.0)
                    m_pvp_val = float(m_pvp or 0.0)
                    
                    if m_nom and m_base_val >= 0:
                        nuevo_id = "0"
                        if add_to_stock:
                            res_new = client.table("productos").insert({
                                "nombre": m_nom, "sku": m_sku if m_sku else "", "precio_base": float(m_base_val), "igic_tipo": float(m_igic), 
                                "precio_pvp": float(m_pvp_val), "categoria": "Producto", "stock_actual": 0, "stock_minimo": 2, "cantidad_reponer": 5
                            }).execute()
                            if res_new.data:
                                nuevo_id = str(res_new.data[0]['id'])
                                if sel_p:
                                    try:
                                        p_id_sel = df_prov[df_prov['nombre_empresa'] == sel_p].iloc[0]['id']
                                        client.table("productos_proveedores").insert({"producto_id": int(nuevo_id), "proveedor_id": p_id_sel, "precio_coste": float(m_base_val)}).execute()
                                    except: pass
                        
                        st.session_state.compra_temp.append({
                            "id": str(nuevo_id), "Código": m_sku if m_sku else "---", "Descripción": m_nom,
                            "Cantidad": m_cant, "Base Ud": float(m_base_val), "IGIC %": float(m_igic), "Desc %": 0.0, "PVP (€)": float(m_pvp_val),
                            "Lote": "", "Caducidad": str(m_cad) if m_cad else None
                        })
                        st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                        st.session_state.llave_fac_art_c += 1
                        st.success("Artículo añadido a la factura."); time.sleep(0.5); st.rerun()
                    else:
                        st.error("El nombre y el precio base son obligatorios.")

        if st.session_state.compra_temp:
            # Protección por si hay carritos guardados antes de esta actualización
            for x in st.session_state.compra_temp:
                if 'PVP (€)' not in x: x['PVP (€)'] = 0.0
                if 'Lote' not in x: x['Lote'] = ""
                if 'Caducidad' not in x: x['Caducidad'] = None
                
            df_c = pd.DataFrame(st.session_state.compra_temp)
            df_c['Coste Ud'] = (df_c['Base Ud'] * (1 + df_c['IGIC %']/100)).round(2)
            df_c['Base Neta'] = ((df_c['Base Ud'] * df_c['Cantidad']) * (1 - df_c['Desc %']/100)).round(2)
            df_c['IGIC €'] = (df_c['Base Neta'] * (df_c['IGIC %']/100)).round(2)
            df_c['Total Línea'] = (df_c['Base Neta'] + df_c['IGIC €']).round(2)
            
            df_c_edit = st.data_editor(
                df_c, hide_index=True, use_container_width=True, num_rows="dynamic",
                column_config={
                    "id": None, "IGIC €": None, "Coste Ud": None, "Total Línea": None,
                    "Código": st.column_config.TextColumn(disabled=True),
                    "Descripción": st.column_config.TextColumn(disabled=True),
                    "PVP (€)": st.column_config.NumberColumn("PVP Público (€)", format="%.2f", step=0.01),
                    "Lote": st.column_config.TextColumn("Lote"),
                    "Caducidad": st.column_config.DateColumn("F. Caducidad", format="DD/MM/YYYY"),
                    "Base Neta": st.column_config.NumberColumn("Importe (Sin IGIC)", disabled=True, format="%.2f", step=0.01)
                }
            )
            
            nuevos_datos = df_c_edit[['id', 'Código', 'Descripción', 'Cantidad', 'Base Ud', 'IGIC %', 'Desc %', 'PVP (€)', 'Lote', 'Caducidad']].to_dict('records')
            if nuevos_datos != st.session_state.compra_temp:
                st.session_state.compra_temp = nuevos_datos; st.rerun()
                
            t_base_c = df_c['Base Neta'].sum()
            t_igic_c = df_c['IGIC €'].sum()
            suma_articulos_c = df_c['Total Línea'].sum()
            val_pp_ia = st.session_state.get("ia_dto_pp", None)
            desc_pp = st.number_input(" 🎁  Dto. Pronto Pago (%)", 0.0, 100.0, value=val_pp_ia, step=0.01, format="%.2f")
            
            desc_pp_val = float(desc_pp or 0.0)
            total_con_pp = suma_articulos_c * (1 - desc_pp_val / 100)
            
            st.markdown(f"""
            <div style="background-color: #fff5f5; padding: 15px; border-radius: 10px; border-left: 5px solid #d32f2f; text-align: right;">
            <p style="margin:0;">Base: {t_base_c * (1-desc_pp_val/100):.2f}€ | IGIC: {t_igic_c * (1-desc_pp_val/100):.2f}€</p>
            <h2 style="margin:0; color: #d32f2f;">TOTAL COMPRA: {total_con_pp:.2f}€</h2>
            </div>
            """, unsafe_allow_html=True)
                
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                btn_borrador = st.button("📝 GUARDAR COMO BORRADOR (No suma stock)", use_container_width=True)
            with col_btn2:
                btn_archivar = st.button("📥 ARCHIVAR Y SUMAR STOCK", type="primary", use_container_width=True)

            if btn_borrador or btn_archivar:
                # --- PROTECCIÓN DOBLE CLIC BACKEND ---
                current_time = time.time()
                if current_time - st.session_state.get('last_compra_time', 0) < 3:
                    st.stop()
                st.session_state['last_compra_time'] = current_time

                if sel_p and n_fac:
                    p_id = df_prov[df_prov['nombre_empresa'] == sel_p].iloc[0]['id']
                    nuevo_estado = "Borrador" if btn_borrador else "Recibido"
                    
                    client.table("compras").insert({
                        "proveedor_id": p_id, "total": float(total_con_pp), "descuento_pp": float(desc_pp or 0.0),
                        "estado": nuevo_estado, "tipo": f"Factura: {n_fac}", "fecha_vencimiento": str(f_ven),
                        "productos": st.session_state.compra_temp,
                        "pagado": 0.0, "pendiente": float(total_con_pp)
                    }).execute()
                    
                    if btn_archivar:
                        for i in st.session_state.compra_temp:
                            if str(i.get('id', '0')) != '0' and str(i.get('id')) != 'None':
                                res_s = client.table("productos").select("stock_actual").eq("id", i['id']).execute()
                                if res_s.data: 
                                    # Actualizamos stock, el PRECIO DE COSTE general y el PVP PÚBLICO
                                    datos_update = {
                                        "stock_actual": (res_s.data[0]['stock_actual'] or 0) + i['Cantidad'],
                                        "precio_base": float(i['Base Ud']),
                                        "precio_pvp": float(i.get('PVP (€)', 0.0))
                                    }
                                    if i.get('Caducidad') and str(i['Caducidad']).strip() not in ["None", ""]:
                                        datos_update["fecha_caducidad"] = str(i['Caducidad'])
                                    if i.get('Lote') and str(i['Lote']).strip() not in ["None", ""]:
                                        datos_update["lote"] = str(i['Lote'])
                                        
                                    client.table("productos").update(datos_update).eq("id", i['id']).execute()
                                    # Actualizamos el precio de coste del proveedor específico
                                    client.table("productos_proveedores").update({"precio_coste": float(i['Base Ud'])}).eq("producto_id", i['id']).eq("proveedor_id", p_id).execute()
                        
                        if st.session_state.pedido_vinculado:
                            client.table("pedidos_proveedores").update({"estado": "Recibido"}).eq("id", st.session_state.pedido_vinculado).execute()
                            st.session_state.pedido_vinculado = None
                            
                    st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                    st.session_state.compra_temp = []
                    
                    if btn_borrador:
                        st.success("Borrador guardado. Podrás validarlo en el Archivo para sumar el stock."); time.sleep(1.5); st.rerun()
                    else:
                        st.success("Compra archivada y precios actualizados."); time.sleep(1.5); st.rerun()
                else:
                    st.error("⚠️ Debes seleccionar un proveedor y escribir el número de factura para guardar.")

    # ==========================================
    # SUB-TAB 3: ARCHIVO Y GESTIÓN (EDICIÓN Y BORRADO DIRECTO)
    # ==========================================
    with sub_archivo:
        st.markdown("####  🔍  Archivo de Facturas de Compra (Mercancía)")
        tipo_doc = st.radio("Documento:", ["Facturas Emitidas (Ventas)", "Facturas Recibidas (Proveedores)"], horizontal=True)
        c_f1, c_f2 = st.columns(2)
        f_ini = c_f1.date_input("Desde:", pd.to_datetime('today') - pd.Timedelta(days=30), key="a_i")
        f_fin = c_f2.date_input("Hasta:", pd.to_datetime('today'), key="a_f")

        # --- ARCHIVO DE VENTAS ---
        if "Ventas" in tipo_doc:
            res_fac = client.table("facturas").select("*, clientes(nombre_dueno)").gte("created_at", f"{f_ini}T00:00:00").lte("created_at", f"{f_fin}T23:59:59").order("id", desc=True).execute()
            if res_fac.data:
                df_fac = pd.DataFrame(res_fac.data)
                df_fac['Cliente'] = df_fac['clientes'].apply(lambda x: x['nombre_dueno'] if x else '---')
                dt_fac = pd.to_datetime(df_fac['created_at'])
                if dt_fac.dt.tz is None:
                    dt_fac = dt_fac.dt.tz_localize('UTC')
                df_fac['Fecha'] = dt_fac.dt.tz_convert('Atlantic/Canary').dt.strftime('%d/%m/%Y %H:%M')
                df_vista = df_fac[['id', 'Fecha', 'numero_factura', 'total_final', 'Cliente', 'forma_pago']].copy()
                
                # 🚨 LEY ANTIFRAUDE (VERI*FACTU): Prohibido borrar facturas emitidas
                df_vista.insert(0, "Ver", False)
                
                ed_fac = st.data_editor(
                    df_vista, hide_index=True, use_container_width=True, key="ed_h_f", 
                    column_config={
                        "Ver": st.column_config.CheckboxColumn("👁️ Ver"), 
                        "id": None,
                        "Fecha": "Fecha Emisión"
                    }
                )
                
                # 2. SISTEMA DE GUARDADO DE CABECERA (Forma de pago)
                if st.button(" 💾  Guardar Cambios en Forma de Pago"):
                    filas_validas = ed_fac
                    for idx, row in filas_validas.iterrows():
                        client.table("facturas").update({"forma_pago": str(row['forma_pago'])}).eq("id", row['id']).execute()
                    st.success("Formas de pago actualizadas."); time.sleep(0.5); st.rerun()

                # 3. SISTEMA DE DESGLOSE
                filas = ed_fac[ed_fac["Ver"] == True]
                if not filas.empty:
                    f_id = filas.iloc[0]['id']
                    f_data = df_fac[df_fac['id'] == f_id].iloc[0]
                    prods = pd.DataFrame(f_data['productos'])
                    
                    if 'Precio Venta' not in prods.columns: 
                        prods['Precio Venta'] = (prods.get('Base Ud',0)*(1+prods.get('IGIC %',0)/100)).round(2)
                    
                    if 'Base Ud' not in prods.columns:
                        prods['IGIC %'] = 7.0
                        prods['Base Ud'] = prods['Precio Venta'] / 1.07
                    
                    prods['Base Neta'] = (prods['Base Ud'] * prods['Cantidad']) * (1 - prods.get('Desc %',0)/100)
                    prods['IGIC €'] = (prods['Base Neta'] * (prods['IGIC %']/100)).round(2)
                    prods['Total Línea'] = (prods['Precio Venta']*prods['Cantidad'])*(1-prods.get('Desc %',0)/100)
                    
                    st.markdown(f"#### 📝 Editando Factura {f_data['numero_factura']}")
                    ed_ph = st.data_editor(prods, hide_index=True, use_container_width=True, num_rows="dynamic", key=f"ed_v_{f_id}", column_config={"id": None, "Base Ud": None, "IGIC %": None, "Base Neta": None, "IGIC €": None})
                    
                    # Si se añaden filas dinámicas, rellenamos datos
                    ed_ph['IGIC %'] = ed_ph.get('IGIC %', pd.Series()).fillna(7.0)
                    ed_ph['Base Ud'] = ed_ph['Precio Venta'] / (1 + ed_ph['IGIC %'] / 100)
                    ed_ph['Base Neta'] = (ed_ph['Base Ud'] * ed_ph['Cantidad']) * (1 - ed_ph.get('Desc %',0)/100)
                    ed_ph['IGIC €'] = (ed_ph['Base Neta'] * (ed_ph['IGIC %']/100)).round(2)
                    ed_ph['Total Línea'] = (ed_ph['Precio Venta'] * ed_ph['Cantidad']) * (1 - ed_ph.get('Desc %',0)/100)
                    
                    desc_g_val = st.number_input("Dto. Global (%)", 0.0, 100.0, float(f_data.get('descuento_global',0)), key=f"dg_{f_id}", step=0.01, format="%.2f")
                    
                    new_base = ed_ph['Base Neta'].sum() * (1 - desc_g_val/100)
                    new_igic = ed_ph['IGIC €'].sum() * (1 - desc_g_val/100)
                    new_total = ed_ph['Total Línea'].sum() * (1 - desc_g_val/100)
                    
                    st.metric("NUEVO TOTAL FACTURA", f"{new_total:.2f} €")
                    
                    st.button("🚫 Edición de líneas y totales bloqueada (Ley Antifraude / VeriFactu)", disabled=True, use_container_width=True)

        # --- ARCHIVO DE COMPRAS ---
        else: 
            # Filtramos para mostrar solo facturas de proveedores, no gastos generales
            res_comp = client.table("compras").select("*, proveedores(nombre_empresa)").gte("created_at", f"{f_ini}T00:00:00").lte("created_at", f"{f_fin}T23:59:59").ilike("tipo", "Factura:%").order("id", desc=True).execute()
            if res_comp.data:
                df_comp = pd.DataFrame(res_comp.data)
                df_comp['Proveedor'] = df_comp['proveedores'].apply(lambda x: x['nombre_empresa'] if x else '---')
                dt_comp = pd.to_datetime(df_comp['created_at'])
                if dt_comp.dt.tz is None:
                    dt_comp = dt_comp.dt.tz_localize('UTC')
                df_comp['Fecha'] = dt_comp.dt.tz_convert('Atlantic/Canary').dt.strftime('%d/%m/%Y %H:%M')
                
                df_vista = df_comp[['id', 'Fecha', 'tipo', 'total', 'Proveedor', 'estado']].copy()
                df_vista.insert(0, "Borrar", False)
                df_vista.insert(0, "Ver", False)
                
                ed_comp = st.data_editor(
                    df_vista, hide_index=True, use_container_width=True, key="ed_h_c", 
                    column_config={
                        "Ver": st.column_config.CheckboxColumn("👁️ Ver"), 
                        "Borrar": st.column_config.CheckboxColumn("🗑️ Borrar"),
                        "id": None, "tipo": "Documento / Concepto",
                        "Fecha": "Fecha Reg."
                    }
                )

                # 1. SISTEMA DE BORRADO DIRECTO DESDE LA TABLA
                filas_borrar_c = ed_comp[ed_comp["Borrar"] == True]
                if not filas_borrar_c.empty:
                    st.error(f"⚠️ Has marcado {len(filas_borrar_c)} compra(s) para eliminar. El stock de estos artículos se restará automáticamente de la tienda.")
                    if st.button("🚨 CONFIRMAR ELIMINACIÓN DE COMPRA(S)", type="primary", use_container_width=True):
                        for idx, row in filas_borrar_c.iterrows():
                            c_id = row['id']
                            c_data = df_comp[df_comp['id'] == c_id].iloc[0]
                            # Restar stock (corrección)
                            prods_raw = c_data.get('productos', [])
                            if not isinstance(prods_raw, list):
                                prods_raw = []
                            for p in prods_raw:
                                res_p = client.table("productos").select("stock_actual").eq("id", p['id']).execute()
                                if res_p.data: client.table("productos").update({"stock_actual": res_p.data[0]['stock_actual'] - p['Cantidad']}).eq("id", p['id']).execute()
                            # Eliminar registro
                            client.table("compras").delete().eq("id", c_id).execute()
                        st.success("Compra(s) eliminada(s) correctamente."); time.sleep(1); st.rerun()

                st.markdown("---")

                # 2. SISTEMA DE GUARDADO DE CABECERA (Estado)
                if st.button(" 💾  Guardar Cambios en Estado/Referencia"):
                    filas_validas = ed_comp[ed_comp["Borrar"] == False]
                    for _, row in filas_validas.iterrows():
                        client.table("compras").update({"estado": str(row['estado']), "tipo": str(row['tipo'])}).eq("id", row['id']).execute()
                    st.success("Cabeceras actualizadas."); time.sleep(0.5); st.rerun()

                # 3. SISTEMA DE DESGLOSE
                filas = ed_comp[(ed_comp["Ver"] == True) & (ed_comp["Borrar"] == False)]
                if not filas.empty:
                    c_id = filas.iloc[0]['id']
                    c_data = df_comp[df_comp['id'] == c_id].iloc[0]
                    
                    prods_raw = c_data.get('productos')
                    if not isinstance(prods_raw, list): prods_raw = []
                    prods = pd.DataFrame(prods_raw)
                    
                    if not prods.empty:
                        if 'Base Ud' not in prods.columns: prods['Base Ud'] = 0.0
                        if 'Cantidad' not in prods.columns: prods['Cantidad'] = 1
                        if 'IGIC %' not in prods.columns: prods['IGIC %'] = 0.0
                        if 'Desc %' not in prods.columns: prods['Desc %'] = 0.0
                        
                        # Cálculos correctos respetando descuentos
                        prods['Base Neta'] = ((prods['Base Ud'] * prods['Cantidad']) * (1 - prods['Desc %']/100)).round(2)
                        prods['IGIC €'] = (prods['Base Neta'] * (prods['IGIC %']/100)).round(2)
                        prods['Total Línea'] = (prods['Base Neta'] + prods['IGIC €']).round(2)
                    else:
                        prods = pd.DataFrame(columns=['id', 'Código', 'Descripción', 'Cantidad', 'Base Ud', 'IGIC %', 'Desc %', 'PVP (€)', 'Base Neta', 'IGIC €', 'Total Línea'])
                    
                    st.markdown(f"#### 🛒 Editando Compra {c_data['tipo']}")
                    
                    ed_pc = st.data_editor(
                        prods, hide_index=True, use_container_width=True, num_rows="dynamic", key=f"ed_c_{c_id}", 
                        column_config={
                            "id": None, "Base Neta": st.column_config.NumberColumn("Base Neta (€)", disabled=True, format="%.2f"),
                            "IGIC €": st.column_config.NumberColumn("IGIC (€)", disabled=True, format="%.2f"),
                            "Total Línea": st.column_config.NumberColumn("Total Línea (€)", disabled=True, format="%.2f")
                        }
                    )
                    
                    val_pp = c_data.get('descuento_pp', 0.0)
                    val_pp = float(val_pp) if pd.notna(val_pp) and val_pp is not None and str(val_pp).strip() != "" else 0.0
                    dto_pp = st.number_input("Dto. Pronto Pago (%)", 0.0, 100.0, val_pp, key=f"pp_{c_id}", step=0.01, format="%.2f")
                    
                    if not ed_pc.empty:
                        ed_pc['Base Neta'] = ((ed_pc['Base Ud'] * ed_pc['Cantidad']) * (1 - ed_pc['Desc %']/100)).round(2)
                        ed_pc['IGIC €'] = (ed_pc['Base Neta'] * (ed_pc['IGIC %']/100)).round(2)
                        ed_pc['Total Línea'] = (ed_pc['Base Neta'] + ed_pc['IGIC €']).round(2)
                        
                        t_base = ed_pc['Base Neta'].sum()
                        t_igic = ed_pc['IGIC €'].sum()
                        new_total = ed_pc['Total Línea'].sum() * (1 - dto_pp/100)
                        
                        st.markdown(f"""
                        <div style="background-color: #fff5f5; padding: 15px; border-radius: 10px; border-left: 5px solid #d32f2f; text-align: right;">
                        <p style="margin:0;">Base Neta: {t_base * (1-dto_pp/100):.2f}€ | IGIC: {t_igic * (1-dto_pp/100):.2f}€</p>
                        <h2 style="margin:0; color: #d32f2f;">NUEVO TOTAL COMPRA: {new_total:.2f}€</h2>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        new_total = float(c_data['total'])
                        st.metric("NUEVO TOTAL COMPRA", f"{new_total:.2f} €")
                    
                    if str(c_data.get('estado', '')) == 'Borrador':
                        st.warning("⚠️ Esta factura está en estado de BORRADOR. El stock aún no se ha sumado al inventario.")
                        if st.button("🚀 VALIDAR FACTURA Y SUMAR STOCK", type="primary", use_container_width=True):
                            for p in ed_pc.to_dict('records'):
                                if str(p.get('id', '0')) != '0' and str(p.get('id')) != 'None':
                                    res_p = client.table("productos").select("stock_actual").eq("id", p['id']).execute()
                                    if res_p.data:
                                        client.table("productos").update({
                                            "stock_actual": (res_p.data[0]['stock_actual'] or 0) + p.get('Cantidad', 1),
                                            "precio_base": float(p.get('Base Ud', 0)),
                                            "precio_pvp": float(p.get('PVP (€)', 0.0))
                                        }).eq("id", p['id']).execute()
                                        if c_data.get('proveedor_id'):
                                            res_link = client.table("productos_proveedores").select("id").eq("producto_id", p['id']).eq("proveedor_id", c_data['proveedor_id']).execute()
                                            if not res_link.data:
                                                client.table("productos_proveedores").insert({"producto_id": p['id'], "proveedor_id": c_data['proveedor_id'], "precio_coste": float(p.get('Base Ud', 0))}).execute()
                                            else:
                                                client.table("productos_proveedores").update({"precio_coste": float(p.get('Base Ud', 0))}).eq("producto_id", p['id']).eq("proveedor_id", c_data['proveedor_id']).execute()
                            
                            pagado_actual = float(c_data.get('pagado') or 0.0)
                            nuevo_pendiente = max(0.0, float(new_total) - pagado_actual)
                            nuevo_estado = "Pagado" if nuevo_pendiente <= 0.01 else "Recibido"
                            
                            client.table("compras").update({
                                "productos": json.loads(ed_pc.to_json(orient='records')), 
                                "total": float(new_total), "pendiente": nuevo_pendiente, 
                                "estado": nuevo_estado, "descuento_pp": float(dto_pp)
                            }).eq("id", c_id).execute()
                            
                            st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                            st.success("¡Factura validada y stock sumado correctamente!"); time.sleep(1.5); st.rerun()

                    if st.button("💾 SINCRONIZAR CAMBIOS DE ESTA COMPRA"):
                        pagado_actual = float(c_data.get('pagado') or 0.0)
                        nuevo_pendiente = max(0.0, float(new_total) - pagado_actual)
                        nuevo_estado = "Pagado" if nuevo_pendiente <= 0.01 else str(c_data.get('estado', 'Pendiente'))
                        client.table("compras").update({"productos": json.loads(ed_pc.to_json(orient='records')), "total": float(new_total), "pendiente": nuevo_pendiente, "estado": nuevo_estado, "descuento_pp": float(dto_pp)}).eq("id", c_id).execute()
                        st.success("Compra actualizada."); st.rerun()

    # ==========================================
    # SUB-TAB 4: PAGOS PENDIENTES
    # ==========================================
    with sub_pagos:
        st.markdown("#### 💸 Control de Pagos a Proveedores")
        st.info("💡 Aquí aparecen exclusivamente las facturas de **proveedores de mercancía** que no han sido marcadas como 'Pagado'.")
        
        # Buscar compras que no sean "Pagado"
        res_deudas = client.table("compras").select("*, proveedores(nombre_empresa)").neq("estado", "Pagado").order("created_at").execute()
        
        # Filtro nativo en Python para evitar fallos de Pandas o SQL
        datos_filtrados = [d for d in (res_deudas.data or []) if "Factura:" in str(d.get('tipo', ''))]
        
        if datos_filtrados:
            df_deudas = pd.DataFrame(datos_filtrados)
            df_deudas['Proveedor'] = df_deudas['proveedores'].apply(lambda x: x['nombre_empresa'] if x and isinstance(x, dict) else 'Gasto / Nómina')
            df_deudas['Fecha Vencimiento'] = pd.to_datetime(df_deudas['fecha_vencimiento'], errors='coerce')
            
            df_deudas['pagado'] = pd.to_numeric(df_deudas.get('pagado', 0.0)).fillna(0.0)
            df_deudas['pendiente'] = df_deudas.apply(
                lambda r: float(r['total']) - r['pagado'] if 'pendiente' not in df_deudas.columns or pd.isna(r.get('pendiente')) else float(r.get('pendiente', 0.0)), 
                axis=1
            )
            df_deudas['pendiente'] = df_deudas['pendiente'].apply(lambda x: max(0.0, x))
            
            hoy_date = pd.Timestamp(date.today())
            
            # Calcular estado de vencimiento
            def calc_estado_venc(fecha):
                if pd.isna(fecha): return "⚪ Sin fecha"
                dias = (fecha - hoy_date).days
                if dias < 0: return f"🔴 CADUCADO (hace {abs(dias)} días)"
                elif dias <= 3: return f"⚠️ Vence pronto (en {dias} días)"
                else: return f"🟢 En plazo (en {dias} días)"

            df_deudas['Estado Vencimiento'] = df_deudas['Fecha Vencimiento'].apply(calc_estado_venc)
            df_deudas['Vence'] = df_deudas['Fecha Vencimiento'].dt.strftime('%d/%m/%Y').fillna('-')
            
            st.markdown(f"<h3 style='color: #d32f2f;'>Deuda Total Acumulada: {df_deudas['pendiente'].sum():.2f} €</h3>", unsafe_allow_html=True)
            
            # --- CALENDARIO VISUAL DE PAGOS A PROVEEDORES ---
            with st.expander("📅 Ver Calendario Visual de Vencimientos", expanded=True):
                deuda_vencida = df_deudas[df_deudas['Fecha Vencimiento'] < hoy_date]['pendiente'].sum()
                deuda_7d = df_deudas[(df_deudas['Fecha Vencimiento'] >= hoy_date) & (df_deudas['Fecha Vencimiento'] <= hoy_date + pd.Timedelta(days=7))]['pendiente'].sum()
                deuda_30d = df_deudas[(df_deudas['Fecha Vencimiento'] > hoy_date + pd.Timedelta(days=7)) & (df_deudas['Fecha Vencimiento'] <= hoy_date + pd.Timedelta(days=30))]['pendiente'].sum()
                deuda_futura = df_deudas[df_deudas['Fecha Vencimiento'] > hoy_date + pd.Timedelta(days=30)]['pendiente'].sum()
                
                c_cal1, c_cal2, c_cal3, c_cal4 = st.columns(4)
                with c_cal1: st.metric("🔴 Vencido", f"{deuda_vencida:.2f} €")
                with c_cal2: st.metric("🟠 Próx. 7 días", f"{deuda_7d:.2f} €")
                with c_cal3: st.metric("🟡 Próx. 30 días", f"{deuda_30d:.2f} €")
                with c_cal4: st.metric("🟢 Más adelante", f"{deuda_futura:.2f} €")
                
                # Gráfico de barras por semanas para visualización
                df_chart = df_deudas.dropna(subset=['Fecha Vencimiento']).copy()
                if not df_chart.empty:
                    st.markdown("<p style='font-size: 13px; color: gray; margin-top: 10px;'>Previsión semanal de pagos:</p>", unsafe_allow_html=True)
                    # Agrupar por la semana del año
                    df_chart['Semana'] = df_chart['Fecha Vencimiento'].dt.to_period('W').apply(lambda r: f"Semana {r.start_time.strftime('%d/%m')}")
                    chart_data = df_chart.groupby('Semana')['pendiente'].sum().reset_index()
                    chart_data = chart_data.set_index('Semana')
                    st.bar_chart(chart_data, color="#005275")
                    
            st.markdown("---")

            # Crear vista con checkbox para seleccionar las facturas a pagar
            df_vista_p = df_deudas[['id', 'tipo', 'Proveedor', 'total', 'pendiente', 'Vence', 'Estado Vencimiento']].copy()
            df_vista_p.insert(0, "A Pagar Hoy (€)", 0.0)
            
            # Ordenar para que los caducados salgan arriba
            df_vista_p = df_vista_p.sort_values(by='Estado Vencimiento', ascending=False)
            
            def highlight_vencidos(val):
                if isinstance(val, str):
                    if 'CADUCADO' in val: return 'color: red; font-weight: bold'
                    elif 'Vence pronto' in val: return 'color: orange; font-weight: bold'
                    elif 'En plazo' in val: return 'color: green'
                return ''

            ed_deudas = st.data_editor(
                df_vista_p.style.map(highlight_vencidos, subset=['Estado Vencimiento']), 
                hide_index=True, use_container_width=True, key="ed_deudas",
                column_config={
                    "A Pagar Hoy (€)": st.column_config.NumberColumn("A Pagar Hoy (€)", min_value=0.0, format="%.2f", step=0.01), 
                    "id": None, "tipo": "Documento", 
                    "total": st.column_config.NumberColumn("Total (€)", format="%.2f", disabled=True, step=0.01),
                    "pendiente": st.column_config.NumberColumn("Pendiente (€)", format="%.2f", disabled=True, step=0.01)
                }
            )
            
            filas_pagar = ed_deudas[ed_deudas["A Pagar Hoy (€)"] > 0]
            if not filas_pagar.empty:
                errores_exceso = filas_pagar[filas_pagar["A Pagar Hoy (€)"] > filas_pagar["pendiente"]]
                if not errores_exceso.empty:
                    st.error("⚠️ Has introducido un importe a pagar superior a la deuda pendiente en alguna factura. Por favor, corrígelo antes de continuar.")
                else:
                    total_a_pagar = filas_pagar['A Pagar Hoy (€)'].sum()
                    st.markdown("---")
                    st.markdown(f"**Has indicado pagos para {len(filas_pagar)} factura(s) por un total de <span style='color: #005275; font-size: 1.2em;'>{total_a_pagar:.2f} €</span>**", unsafe_allow_html=True)
                    
                    # Cargar bancos
                    res_b = client.table("cuentas_bancarias").select("id, nombre_banco, saldo_actual").execute()
                    opciones_pago = ["💵 Caja Fuerte (Efectivo de la tienda)"]
                    mapa_bancos = {}
                    if res_b.data:
                        for b in res_b.data:
                            etiqueta = f"🏦 {b['nombre_banco']} ({b['saldo_actual']:.2f} €)"
                            opciones_pago.append(etiqueta)
                            mapa_bancos[etiqueta] = b['id']

                    sel_origen = st.selectbox("💳 Selecciona el origen de los fondos para el pago:", [""] + opciones_pago)
                    
                    if sel_origen and st.button("✅ Confirmar Pago", type="primary", use_container_width=True):
                        # --- PROTECCIÓN DOBLE CLIC BACKEND ---
                        current_time = time.time()
                        if current_time - st.session_state.get('last_pago_time', 0) < 3:
                            st.stop()
                        st.session_state['last_pago_time'] = current_time

                        nombres_pagados = ", ".join(filas_pagar['Proveedor'].unique()[:2])
                        if len(filas_pagar['Proveedor'].unique()) > 2: nombres_pagados += " y otros..."
                        
                        pago_exitoso = False
                        
                        if "Caja Fuerte" in sel_origen:
                            res_caja = client.table("control_caja").select("*").eq("estado", "Abierta").execute()
                            if res_caja.data:
                                id_caja = res_caja.data[0]['id']
                                client.table("movimientos_caja").insert({
                                    "id_caja": id_caja, "tipo": "Retirada", "cantidad": float(total_a_pagar), 
                                    "motivo": f"Pago facturas: {nombres_pagados}"
                                }).execute()
                                pago_exitoso = True
                            else:
                                st.error("⚠️ No puedes pagar con la caja porque no hay ningún turno abierto. Abre la caja primero en la pestaña 5.")
                        else:
                            banco_id = mapa_bancos[sel_origen]
                            banco_data = [b for b in res_b.data if b['id'] == banco_id][0]
                            nuevo_saldo = banco_data['saldo_actual'] - total_a_pagar
                            client.table("cuentas_bancarias").update({"saldo_actual": nuevo_saldo}).eq("id", banco_id).execute()
                            pago_exitoso = True
                            
                        if pago_exitoso:
                            for _, row in filas_pagar.iterrows():
                                c_id = row['id']
                                pago_hoy = float(row['A Pagar Hoy (€)'])
                                
                                actual_row = df_deudas[df_deudas['id'] == c_id].iloc[0]
                                nuevo_pagado = float(actual_row['pagado']) + pago_hoy
                                nuevo_pendiente = float(actual_row['pendiente']) - pago_hoy
                                
                                nuevo_estado = "Pagado" if nuevo_pendiente <= 0.01 else "Pago Parcial"
                                
                                client.table("compras").update({
                                    "estado": nuevo_estado,
                                    "pagado": nuevo_pagado,
                                    "pendiente": nuevo_pendiente
                                }).eq("id", c_id).execute()
                            st.success(f"¡Pago de {total_a_pagar:.2f} € registrado correctamente!"); time.sleep(1.5); st.rerun()
        else:
            st.success("¡Genial! No tienes deudas a proveedores pendientes.")
