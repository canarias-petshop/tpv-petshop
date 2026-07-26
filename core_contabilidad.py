import pandas as pd
import json

def eliminar_documento_contabilidad(client, df_comp_arc, c_id, fetch_producto_stock):
    """
    Elimina un documento contable (compra, gasto, etc.).
    Si es una factura de compra ya validada (no borrador), restaura (resta) el stock del inventario.
    """
    try:
        c_data = df_comp_arc[df_comp_arc['id'] == c_id].iloc[0]
        estado_doc = str(c_data.get('estado', ''))
        prods_raw = c_data.get('productos', [])
        # Los borradores nunca sumaron stock: no restar al borrar
        if estado_doc != 'Borrador' and isinstance(prods_raw, list):
            for p in prods_raw:
                p_id = p.get('id') if isinstance(p, dict) else None
                if p_id and str(p_id).strip() not in ["", "None", "0", "nan"]:
                    try:
                        res_p = fetch_producto_stock(client, p_id)
                        if res_p and hasattr(res_p, 'data') and res_p.data:
                            cant = int(float(p.get('Cantidad', 0) or 0))
                            stock_act = int(res_p.data[0]['stock_actual'] or 0)
                            client.table("productos").update({
                                "stock_actual": stock_act - cant
                            }).eq("id", p_id).execute()
                    except Exception:
                        pass
        client.table("compras").delete().eq("id", c_id).execute()
        return True
    except Exception as e:
        print(f"Error al eliminar doc: {e}")
        return False

def safe_float(val, default=0.0):
    if val is None or val == "":
        return default
    try:
        if isinstance(val, str):
            val = val.replace(',', '.')
        return float(val)
    except:
        return default

def calcular_bases_e_igic_y_lineas(productos_raw, desc_global, is_factura, doc_id_str, fecha_str, cliente_nom, mapa_categorias, palabras_clave_serv):
    """
    Calcula bases imponibles, IGIC y líneas desglosadas para facturas y tickets.
    """
    b_prod, b_serv, i_serv = 0.0, 0.0, 0.0
    l_prod, l_serv = [], []
    if not productos_raw: 
        return b_prod, b_serv, i_serv, l_prod, l_serv
        
    if isinstance(productos_raw, str):
        try:
            productos_raw = json.loads(productos_raw)
        except: 
            return b_prod, b_serv, i_serv, l_prod, l_serv
            
    if isinstance(productos_raw, dict): 
        productos_raw = [productos_raw]
        
    factor_desc = (1 - safe_float(desc_global) / 100)
    
    for p in productos_raw:
        if not isinstance(p, dict): continue
        precio_pvp = safe_float(p.get('Precio Venta' if is_factura else 'Precio', p.get('Precio', 0.0)))
        cant = safe_float(p.get('Cantidad', 1))
        desc_item = safe_float(p.get('Desc %', p.get('Desc. %', 0.0)))
        id_item = str(p.get('id', ''))
        cat_db = mapa_categorias.get(id_item, 'Desconocido')
        
        es_servicio = False
        if cat_db == 'Servicio' or id_item.startswith('cita_'): 
            es_servicio = True
        elif cat_db == 'Producto': 
            es_servicio = False
        else:
            nombre_item = str(p.get('Producto', p.get('Descripción', ''))).lower()
            if any(kw in nombre_item for kw in palabras_clave_serv):
                es_servicio = True
                if any(ex in nombre_item for ex in ['cepillo', 'peine', 'champú', 'champu', 'mascarilla', 'tijera', 'carda', 'cortaúñas', 'cortauñas', 'colonia', 'perfume']):
                    es_servicio = False

        pvp_con_desc = (precio_pvp * cant) * (1 - desc_item / 100)
        pvp_final_linea = pvp_con_desc * factor_desc
        nombre_prod = str(p.get('Producto', p.get('Descripción', '')))

        if es_servicio:
            igic_porcentaje = safe_float(p.get('IGIC %', p.get('IGIC', 7.0)))
            base_linea = pvp_con_desc / (1 + igic_porcentaje / 100)
            
            base_final_linea = base_linea * factor_desc
            igic_final_linea = pvp_final_linea - base_final_linea
            
            b_serv += base_linea
            i_serv += (pvp_con_desc - base_linea)
            
            l_serv.append({
                "Fecha": fecha_str, "Documento": doc_id_str, "Cliente": cliente_nom,
                "Servicio": nombre_prod, "Cantidad": cant, "Precio Unit. Final (€)": round(pvp_final_linea/cant if cant>0 else 0, 2),
                "Base Imponible (€)": round(base_final_linea, 2), "IGIC %": igic_porcentaje,
                "Cuota IGIC (€)": round(igic_final_linea, 2), "Total (€)": round(pvp_final_linea, 2)
            })
        else:
            b_prod += pvp_con_desc
            l_prod.append({
                "Fecha": fecha_str, "Documento": doc_id_str, "Cliente": cliente_nom,
                "Producto": nombre_prod, "Cantidad": cant, "Precio Unit. Final (€)": round(pvp_final_linea/cant if cant>0 else 0, 2),
                "Total (0% IGIC) (€)": round(pvp_final_linea, 2)
            })
            
    return round(b_prod * factor_desc, 2), round(b_serv * factor_desc, 2), round(i_serv * factor_desc, 2), l_prod, l_serv
