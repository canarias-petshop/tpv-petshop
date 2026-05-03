import streamlit as st
import pandas as pd
import time
from datetime import date
import json

def render_pestana_facturacion(client):
    st.markdown("<h3 style='margin-top: -15px;'> 📑  Gestión Integral de Facturación</h3>", unsafe_allow_html=True)

    sub_emitir, sub_registrar, sub_archivo, sub_pagos = st.tabs([
        " 🧾  Emitir Factura (Venta)", 
        " 📥  Registrar Compra (Proveedor)", 
        " 📂  Archivo de Documentos",
        " 💸  Pagos Pendientes"
    ])
    
    res_inv = client.table("productos").select("id, sku, nombre, precio_base, igic_tipo, precio_pvp, stock_actual").execute()
    df_inv = pd.DataFrame(res_inv.data) if res_inv.data else pd.DataFrame()
    res_cli = client.table("clientes").select("id, nombre_dueno, cif").execute()
    df_cli = pd.DataFrame(res_cli.data) if res_cli.data else pd.DataFrame()
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
                nc1, nc2 = st.columns(2); n_n = nc1.text_input("Nombre*"); n_c = nc2.text_input("CIF*")
                if st.form_submit_button("Crear Cliente"):
                    if n_n and n_c: client.table("clientes").insert({"nombre_dueno": n_n, "cif": n_c}).execute(); st.rerun()
        
        st.markdown("####  📦  Añadir Artículos a la Venta")
        if not df_inv.empty:
            opciones_v = df_inv.apply(lambda x: f"{x['nombre']} | SKU: {x['sku']}", axis=1).tolist()
            prod_v = st.selectbox("🔍 Buscar producto en almacén:", opciones_v, index=None, key=f"search_v_alta_{st.session_state.llave_busqueda_v}", placeholder="Escribe para filtrar...")
            
            if prod_v:
                sku_v = prod_v.split(" | SKU: ")[1]
                it_v = df_inv[df_inv['sku'] == sku_v].iloc[0]
                st.session_state.factura_v_temp.append({
                    "id": str(it_v['id']), "Código": it_v['sku'], "Descripción": it_v['nombre'],
                    "Cantidad": 1, "Precio Venta": float(it_v['precio_pvp']), "Desc %": 0.0
                })
                st.session_state.llave_busqueda_v += 1 
                st.rerun()
                
        with st.expander("✨ ¿Artículo manual o nuevo producto?"):
            with st.form("form_nuevo_art_venta", clear_on_submit=True):
                st.markdown("<p style='font-size:13px; color:gray;'>Añade un artículo manual a la factura. Si dejas marcada la casilla, también se guardará permanentemente en el Inventario.</p>", unsafe_allow_html=True)
                col_m1, col_m2 = st.columns(2)
                with col_m1: m_nom = st.text_input("Nombre del Artículo *")
                with col_m2: m_sku = st.text_input("SKU / Ref (Opcional si no se guarda)")
                
                col_m3, col_m4, col_m5 = st.columns(3)
                with col_m3: m_pvp = st.number_input("Precio Venta Público (€) *", min_value=0.0, format="%.2f")
                with col_m4: m_igic = st.selectbox("IGIC %", [7.0, 0.0, 3.0, 15.0])
                with col_m5: m_cant = st.number_input("Cantidad a facturar", min_value=1, value=1)
                
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
                        
                        if not add_to_stock or (add_to_stock and m_sku):
                            st.session_state.factura_v_temp.append({
                                "id": str(nuevo_id), "Código": m_sku if m_sku else "---", "Descripción": m_nom,
                                "Cantidad": m_cant, "Precio Venta": m_pvp, "Desc %": 0.0
                            })
                            st.success("Artículo añadido a la factura."); time.sleep(0.5); st.rerun()
                    else:
                        st.error("El nombre y el precio de venta son obligatorios.")
        
        if st.session_state.factura_v_temp:
            # Parche anti-fantasmas
            if 'Precio Venta' not in st.session_state.factura_v_temp[0]:
                st.session_state.factura_v_temp = []; st.rerun()

            df_v = pd.DataFrame(st.session_state.factura_v_temp)
            df_v['Total Línea'] = (df_v['Precio Venta'] * df_v['Cantidad']) * (1 - df_v['Desc %']/100)
            df_v['Total Línea'] = df_v['Total Línea'].round(2)

            df_v_edit = st.data_editor(
                df_v, hide_index=True, use_container_width=True, key="ed_v_final",
                num_rows="dynamic",
                column_config={
                    "id": None, "Código": st.column_config.TextColumn(disabled=True),
                    "Descripción": st.column_config.TextColumn(disabled=True),
                    "Cantidad": st.column_config.NumberColumn("Cant.", min_value=1),
                    "Precio Venta": st.column_config.NumberColumn("Precio Venta (€)", format="%.2f"),
                    "Desc %": st.column_config.NumberColumn("Desc. %", min_value=0.0),
                    "Total Línea": st.column_config.NumberColumn("Total Línea (€)", disabled=True, format="%.2f")
                }
            )

            nuevos_datos_v = df_v_edit[['id', 'Código', 'Descripción', 'Cantidad', 'Precio Venta', 'Desc %']].to_dict('records')
            if nuevos_datos_v != st.session_state.factura_v_temp:
                st.session_state.factura_v_temp = nuevos_datos_v
                st.rerun()

            suma_articulos_v = df_v['Total Línea'].sum()
            st.markdown("---")
            col_v1, col_v2 = st.columns([1, 2])
            with col_v1:
                desc_g_v = st.number_input(" 🎁  Dto. Global (%)", 0.0, 100.0, value=None, key="desc_v_alta")
            
            total_v_final = suma_articulos_v * (1 - (desc_g_v or 0.0) / 100)

            with col_v2:
                st.markdown(f"""
                <div style="background-color: #f0f7f9; padding: 15px; border-radius: 10px; border-left: 5px solid #005275; text-align: right;">
                <p style="margin:0; font-size: 14px;">Suma artículos: {suma_articulos_v:.2f}€</p>
                <h2 style="margin:0; color: #005275;">TOTAL FACTURA: {total_v_final:.2f}€</h2>
                </div>
                """, unsafe_allow_html=True)
            
            if st.button(" 🚀  EMITIR FACTURA", type="primary", use_container_width=True):
                if sel_c:
                    c_id = df_cli[df_cli['nombre_dueno'] == sel_c.split(" | ")[0]].iloc[0]['id']
                    
                    client.table("facturas").insert({
                        "cliente_id": c_id, "total_neto": float(total_v_final), "total_igic": 0.0, "total_final": float(total_v_final),
                        "descuento_global": float(desc_g_v or 0.0), "forma_pago": f_pago, "fecha_vencimiento": str(f_vence), "productos": st.session_state.factura_v_temp
                    }).execute()
                    for i in st.session_state.factura_v_temp:
                        if str(i.get('id', '0')) != '0' and str(i.get('id')) != 'None':
                            res = client.table("productos").select("stock_actual").eq("id", i['id']).execute()
                            if res.data: client.table("productos").update({"stock_actual": res.data[0]['stock_actual'] - i['Cantidad']}).eq("id", i['id']).execute()
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
            
        c_c1, c_c2, c_c3 = st.columns(3)
        with c_c1: n_fac = st.text_input("Nº Factura Proveedor", key="fac_prov_n")
        with c_c2: f_fac = st.date_input("Fecha Factura", key="fac_prov_f")
        with c_c3: f_ven = st.date_input("Vencimiento", key="fac_prov_v")
        
        with st.expander(" 🚚  Seleccionar / Crear Proveedor", expanded=True):
            p_opc = df_prov['nombre_empresa'].tolist() if not df_prov.empty else []
            sel_p = st.selectbox("Selecciona el Proveedor:", p_opc, index=None, placeholder="Escribe el nombre del proveedor...")
            with st.form("form_nuevo_proveedor_rapido", clear_on_submit=True):
                np1, np2 = st.columns(2); n_emp_new = np1.text_input("Nombre Empresa*"); n_cif_new = np2.text_input("CIF")
                if st.form_submit_button("➕ Crear Nuevo Proveedor"):
                    if n_emp_new: client.table("proveedores").insert({"nombre_empresa": n_emp_new, "cif": n_cif_new}).execute(); st.rerun()
                        
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
                                    "Cantidad": art['Cantidad'], "Base Ud": float(item['precio_base']), "IGIC %": float(item['igic_tipo']), "Desc %": 0.0, "PVP (€)": float(item.get('precio_pvp', 0.0))
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
                    "Cantidad": 1, "Base Ud": float(item['precio_base']), "IGIC %": float(item['igic_tipo']), "Desc %": 0.0, "PVP (€)": float(item.get('precio_pvp', 0.0))
                })
                st.session_state.llave_busqueda_c += 1; st.rerun()

        with st.expander("✨ ¿Artículo manual o nuevo producto?"):
            with st.form("form_nuevo_art_compra", clear_on_submit=True):
                st.markdown("<p style='font-size:13px; color:gray;'>Añade un artículo manual a la factura. Si dejas marcada la casilla, también se guardará permanentemente en el Inventario.</p>", unsafe_allow_html=True)
                col_m1, col_m2 = st.columns(2)
                with col_m1: m_nom = st.text_input("Nombre del Artículo *")
                with col_m2: m_sku = st.text_input("SKU / Ref (Opcional)")
                
                col_m3, col_m4, col_m5 = st.columns(3)
                with col_m3: m_base = st.number_input("Precio Base Compra (€) *", min_value=0.0, format="%.2f")
                with col_m4: m_igic = st.selectbox("IGIC %", [7.0, 0.0, 3.0, 15.0])
                with col_m5: m_cant = st.number_input("Cantidad a registrar", min_value=1, value=1)
                
                col_m6, col_m7 = st.columns(2)
                with col_m6: m_pvp = st.number_input("PVP Venta Público (€) (Solo si se guarda)", min_value=0.0, format="%.2f")
                with col_m7:
                    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                    add_to_stock = st.checkbox("💾 Guardar permanentemente en Inventario", value=True)
                
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
                            "Cantidad": m_cant, "Base Ud": float(m_base_val), "IGIC %": float(m_igic), "Desc %": 0.0, "PVP (€)": float(m_pvp_val)
                        })
                        st.success("Artículo añadido a la factura."); time.sleep(0.5); st.rerun()
                    else:
                        st.error("El nombre y el precio base son obligatorios.")

        if st.session_state.compra_temp:
            # Protección por si hay carritos guardados antes de esta actualización
            for x in st.session_state.compra_temp:
                if 'PVP (€)' not in x: x['PVP (€)'] = 0.0
                
            df_c = pd.DataFrame(st.session_state.compra_temp)
            df_c['Coste Ud'] = (df_c['Base Ud'] * (1 + df_c['IGIC %']/100)).round(2)
            df_c['Base Neta'] = (df_c['Base Ud'] * df_c['Cantidad']) * (1 - df_c['Desc %']/100)
            df_c['IGIC €'] = (df_c['Base Neta'] * (df_c['IGIC %']/100)).round(2)
            df_c['Total Línea'] = (df_c['Base Neta'] + df_c['IGIC €']).round(2)
            
            df_c_edit = st.data_editor(
                df_c, hide_index=True, use_container_width=True, num_rows="dynamic",
                column_config={
                    "id": None, "Base Neta": None, "IGIC €": None,
                    "Código": st.column_config.TextColumn(disabled=True),
                    "Descripción": st.column_config.TextColumn(disabled=True),
                    "PVP (€)": st.column_config.NumberColumn("PVP Público (€)", format="%.2f"),
                    "Coste Ud": st.column_config.NumberColumn("Coste Ud c/IGIC", disabled=True),
                    "Total Línea": st.column_config.NumberColumn("Total c/IGIC", disabled=True)
                }
            )
            
            nuevos_datos = df_c_edit[['id', 'Código', 'Descripción', 'Cantidad', 'Base Ud', 'IGIC %', 'Desc %', 'PVP (€)']].to_dict('records')
            if nuevos_datos != st.session_state.compra_temp:
                st.session_state.compra_temp = nuevos_datos; st.rerun()
                
            t_base_c = df_c['Base Neta'].sum()
            t_igic_c = df_c['IGIC €'].sum()
            suma_articulos_c = df_c['Total Línea'].sum()
            desc_pp = st.number_input(" 🎁  Dto. Pronto Pago (%)", 0.0, 100.0, value=None)
            
            desc_pp_val = float(desc_pp or 0.0)
            total_con_pp = suma_articulos_c * (1 - desc_pp_val / 100)
            
            st.markdown(f"""
            <div style="background-color: #fff5f5; padding: 15px; border-radius: 10px; border-left: 5px solid #d32f2f; text-align: right;">
            <p style="margin:0;">Base: {t_base_c * (1-desc_pp_val/100):.2f}€ | IGIC: {t_igic_c * (1-desc_pp_val/100):.2f}€</p>
            <h2 style="margin:0; color: #d32f2f;">TOTAL COMPRA: {total_con_pp:.2f}€</h2>
            </div>
            """, unsafe_allow_html=True)
                
            if st.button(" 📥  ARCHIVAR COMPRA Y SUMAR STOCK", type="primary", use_container_width=True):
                if sel_p and n_fac:
                    p_id = df_prov[df_prov['nombre_empresa'] == sel_p].iloc[0]['id']
                    client.table("compras").insert({
                        "proveedor_id": p_id, "total": float(total_con_pp), "descuento_pp": float(desc_pp or 0.0),
                        "estado": "Recibido", "tipo": f"Factura: {n_fac}", "fecha_vencimiento": str(f_ven),
                        "productos": st.session_state.compra_temp
                    }).execute()
                    for i in st.session_state.compra_temp:
                        if str(i.get('id', '0')) != '0' and str(i.get('id')) != 'None':
                            res_s = client.table("productos").select("stock_actual").eq("id", i['id']).execute()
                            if res_s.data: 
                                # Actualizamos stock, el PRECIO DE COSTE general y el PVP PÚBLICO
                                client.table("productos").update({
                                    "stock_actual": (res_s.data[0]['stock_actual'] or 0) + i['Cantidad'],
                                    "precio_base": float(i['Base Ud']),
                                    "precio_pvp": float(i.get('PVP (€)', 0.0))
                                }).eq("id", i['id']).execute()
                                # Actualizamos el precio de coste del proveedor específico
                                client.table("productos_proveedores").update({"precio_coste": float(i['Base Ud'])}).eq("producto_id", i['id']).eq("proveedor_id", p_id).execute()
                    
                    if st.session_state.pedido_vinculado:
                        client.table("pedidos_proveedores").update({"estado": "Recibido"}).eq("id", st.session_state.pedido_vinculado).execute()
                        st.session_state.pedido_vinculado = None
                        
                    st.session_state.compra_temp = []; st.success("Compra archivada y precios actualizados."); time.sleep(1); st.rerun()

    # ==========================================
    # SUB-TAB 3: ARCHIVO Y GESTIÓN (EDICIÓN Y BORRADO DIRECTO)
    # ==========================================
    with sub_archivo:
        st.markdown("####  🔍  Archivo Histórico")
        tipo_doc = st.radio("Documento:", ["Facturas Emitidas (Ventas)", "Facturas Recibidas (Compras)"], horizontal=True)
        c_f1, c_f2 = st.columns(2)
        f_ini = c_f1.date_input("Desde:", pd.to_datetime('today') - pd.Timedelta(days=30), key="a_i")
        f_fin = c_f2.date_input("Hasta:", pd.to_datetime('today'), key="a_f")

        # --- ARCHIVO DE VENTAS ---
        if "Ventas" in tipo_doc:
            res_fac = client.table("facturas").select("*, clientes(nombre_dueno)").gte("created_at", f"{f_ini}T00:00:00").lte("created_at", f"{f_fin}T23:59:59").order("id", desc=True).execute()
            if res_fac.data:
                df_fac = pd.DataFrame(res_fac.data)
                df_fac['Cliente'] = df_fac['clientes'].apply(lambda x: x['nombre_dueno'] if x else '---')
                df_vista = df_fac[['id', 'numero_factura', 'total_final', 'Cliente', 'forma_pago']].copy()
                
                # 🚨 LEY ANTIFRAUDE (VERI*FACTU): Prohibido borrar facturas emitidas
                df_vista.insert(0, "Borrar", False)
                df_vista.insert(0, "Ver", False)
                
                ed_fac = st.data_editor(
                    df_vista, hide_index=True, use_container_width=True, key="ed_h_f", 
                    column_config={
                        "Ver": st.column_config.CheckboxColumn("👁️ Ver"), 
                        "Borrar": st.column_config.CheckboxColumn("🗑️ Borrar"), 
                        "id": None
                    }
                )
                
                # 1. SISTEMA DE BORRADO DIRECTO DESDE LA TABLA
                filas_borrar_v = ed_fac[ed_fac["Borrar"] == True]
                if not filas_borrar_v.empty:
                    st.error(f"⚠️ Has marcado {len(filas_borrar_v)} factura(s) para eliminar. El stock de los artículos se devolverá automáticamente a la tienda.")
                    if st.button("🚨 CONFIRMAR ELIMINACIÓN DE FACTURA(S)", type="primary", use_container_width=True):
                        for idx, row in filas_borrar_v.iterrows():
                            f_id = row['id']
                            f_data = df_fac[df_fac['id'] == f_id].iloc[0]
                            # Devolver stock
                            for p in f_data.get('productos', []):
                                if str(p.get('id', '0')) != '0' and str(p.get('id')) != 'None':
                                    res_p = client.table("productos").select("stock_actual").eq("id", p['id']).execute()
                                    if res_p.data: client.table("productos").update({"stock_actual": res_p.data[0]['stock_actual'] + p['Cantidad']}).eq("id", p['id']).execute()
                            # Eliminar registro
                            client.table("facturas").delete().eq("id", f_id).execute()
                        st.success("Factura(s) eliminada(s) correctamente."); time.sleep(1); st.rerun()
                
                st.markdown("---")
                
                # 2. SISTEMA DE GUARDADO DE CABECERA (Forma de pago)
                if st.button(" 💾  Guardar Cambios en Forma de Pago"):
                    filas_validas = ed_fac[ed_fac["Borrar"] == False]
                    for idx, row in filas_validas.iterrows():
                        client.table("facturas").update({"forma_pago": str(row['forma_pago'])}).eq("id", row['id']).execute()
                    st.success("Formas de pago actualizadas."); time.sleep(0.5); st.rerun()

                # 3. SISTEMA DE DESGLOSE
                filas = ed_fac[(ed_fac["Ver"] == True) & (ed_fac["Borrar"] == False)]
                if not filas.empty:
                    f_id = filas.iloc[0]['id']
                    f_data = df_fac[df_fac['id'] == f_id].iloc[0]
                    prods = pd.DataFrame(f_data['productos'])
                    if 'Precio Venta' not in prods.columns: prods['Precio Venta'] = (prods.get('Base Ud',0)*(1+prods.get('IGIC %',0)/100)).round(2)
                    prods['Total Línea'] = (prods['Precio Venta']*prods['Cantidad'])*(1-prods.get('Desc %',0)/100)
                    
                    st.markdown(f"#### 📝 Editando Factura {f_data['numero_factura']}")
                    ed_ph = st.data_editor(prods, hide_index=True, use_container_width=True, num_rows="dynamic", key=f"ed_v_{f_id}", column_config={"id": None, "Base Ud": None, "IGIC %": None, "Base Neta": None, "IGIC €": None})
                    
                    new_total = ed_ph['Total Línea'].sum() * (1 - st.number_input("Dto. Global (%)", 0.0, 100.0, float(f_data.get('descuento_global',0)), key=f"dg_{f_id}")/100)
                    st.metric("NUEVO TOTAL FACTURA", f"{new_total:.2f} €")
                    
                    if st.button("💾 SINCRONIZAR CAMBIOS DE ESTA FACTURA"):
                        client.table("facturas").update({"productos": json.loads(ed_ph.to_json(orient='records')), "total_final": float(new_total)}).eq("id", f_id).execute()
                        st.success("Guardado."); st.rerun()

        # --- ARCHIVO DE COMPRAS ---
        else: 
            res_comp = client.table("compras").select("*, proveedores(nombre_empresa)").gte("created_at", f"{f_ini}T00:00:00").lte("created_at", f"{f_fin}T23:59:59").order("id", desc=True).execute()
            if res_comp.data:
                df_comp = pd.DataFrame(res_comp.data)
                df_comp['Proveedor'] = df_comp['proveedores'].apply(lambda x: x['nombre_empresa'] if x else '---')
                df_vista = df_comp[['id', 'tipo', 'total', 'Proveedor', 'estado']].copy()
                
                # Insertamos las dos casillas
                df_vista.insert(0, "Borrar", False)
                df_vista.insert(0, "Ver", False)
                
                ed_comp = st.data_editor(
                    df_vista, hide_index=True, use_container_width=True, key="ed_h_c", 
                    column_config={
                        "Ver": st.column_config.CheckboxColumn("👁️ Ver"), 
                        "Borrar": st.column_config.CheckboxColumn("🗑️ Borrar"),
                        "id": None, "tipo": "Nº Factura"
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
                            for p in c_data.get('productos', []):
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
                    prods = pd.DataFrame(c_data['productos'])
                    prods['Total Línea'] = (prods['Base Ud']*prods['Cantidad'])*(1+prods.get('IGIC %',0)/100)
                    
                    st.markdown(f"#### 🛒 Editando Compra {c_data['tipo']}")
                    ed_pc = st.data_editor(prods, hide_index=True, use_container_width=True, num_rows="dynamic", key=f"ed_c_{c_id}", column_config={"id": None})
                    
                    new_total = ed_pc['Total Línea'].sum() * (1 - st.number_input("Dto. Pronto Pago (%)", 0.0, 100.0, float(c_data.get('descuento_pp',0)), key=f"pp_{c_id}")/100)
                    st.metric("NUEVO TOTAL COMPRA", f"{new_total:.2f} €")

                    if st.button("💾 SINCRONIZAR CAMBIOS DE ESTA COMPRA"):
                        client.table("compras").update({"productos": json.loads(ed_pc.to_json(orient='records')), "total": float(new_total)}).eq("id", c_id).execute()
                        st.success("Compra actualizada."); st.rerun()

    # ==========================================
    # SUB-TAB 4: PAGOS PENDIENTES
    # ==========================================
    with sub_pagos:
        st.markdown("#### 💸 Control de Pagos Pendientes (Deudas a Proveedores y Gastos)")
        st.info("💡 Aquí aparecen todas las compras y gastos que no han sido marcados como 'Pagado'. Puedes saldarlos descontando el dinero de tus bancos o directamente desde la caja fuerte.")
        
        # Buscar compras que no sean "Pagado"
        res_deudas = client.table("compras").select("*, proveedores(nombre_empresa)").neq("estado", "Pagado").order("created_at").execute()
        if res_deudas.data:
            df_deudas = pd.DataFrame(res_deudas.data)
            df_deudas['Proveedor'] = df_deudas['proveedores'].apply(lambda x: x['nombre_empresa'] if x and isinstance(x, dict) else 'Gasto / Nómina')
            df_deudas['Fecha Vencimiento'] = pd.to_datetime(df_deudas['fecha_vencimiento'], errors='coerce')
            
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
            
            st.markdown(f"<h3 style='color: #d32f2f;'>Deuda Total Acumulada: {df_deudas['total'].sum():.2f} €</h3>", unsafe_allow_html=True)
            
            # Crear vista con checkbox para seleccionar las facturas a pagar
            df_vista_p = df_deudas[['id', 'tipo', 'Proveedor', 'total', 'Vence', 'Estado Vencimiento']].copy()
            df_vista_p.insert(0, "Pagar", False)
            
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
                column_config={"Pagar": st.column_config.CheckboxColumn("Pagar Ahora"), "id": None, "tipo": "Documento", "total": st.column_config.NumberColumn("Total (€)", format="%.2f")}
            )
            
            filas_pagar = df_vista_p[ed_deudas["Pagar"] == True] # Recuperar del dataframe original guiado por la edición
            if not filas_pagar.empty:
                total_a_pagar = filas_pagar['total'].sum()
                st.markdown("---")
                st.markdown(f"**Has seleccionado {len(filas_pagar)} factura(s) por un total de <span style='color: #005275; font-size: 1.2em;'>{total_a_pagar:.2f} €</span>**", unsafe_allow_html=True)
                
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
                    # Nombres de proveedores para el motivo de la caja
                    nombres_pagados = ", ".join(filas_pagar['Proveedor'].unique()[:2])
                    if len(filas_pagar['Proveedor'].unique()) > 2: nombres_pagados += " y otros..."
                    
                    pago_exitoso = False
                    
                    if "Caja Fuerte" in sel_origen:
                        res_caja = client.table("control_caja").select("*").eq("estado", "Abierta").execute()
                        if res_caja.data:
                            id_caja = res_caja.data[0]['id']
                            client.table("movimientos_caja").insert({
                                "id_caja": id_caja, "tipo": "Retirada", "cantidad": float(total_a_pagar), 
                                "motivo": f"Pago de facturas/gastos: {nombres_pagados}"
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
                        # Actualizar estado de las compras
                        for _, row in filas_pagar.iterrows():
                            client.table("compras").update({"estado": "Pagado"}).eq("id", row['id']).execute()
                        st.success(f"¡Pago de {total_a_pagar:.2f} € registrado correctamente!"); time.sleep(1.5); st.rerun()
        else:
            st.success("¡Genial! No tienes deudas pendientes.")
