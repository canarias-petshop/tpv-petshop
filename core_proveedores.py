def auto_distribuir_borradores(client, prods_a_pedir_auto, fetch_productos_proveedores_rels, fetch_pedidos_proveedor_borrador):
    """
    Toma un DataFrame de productos a pedir, busca el proveedor con el precio de coste más bajo
    para cada uno, y añade los productos al pedido borrador de ese proveedor (creándolo si no existe).
    """
    res_rels = fetch_productos_proveedores_rels(client)
    mapa_provs = {}
    
    if res_rels and hasattr(res_rels, 'data') and res_rels.data:
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
            if prov_id not in pedidos_a_crear: 
                pedidos_a_crear[prov_id] = []
            pedidos_a_crear[prov_id].append({"Producto": row['nombre'], "Cantidad": int(row['cantidad_reponer'])})
            
    generados = False
    
    if pedidos_a_crear:
        for p_id, prods in pedidos_a_crear.items():
            res_b = fetch_pedidos_proveedor_borrador(client, p_id)
            if res_b and hasattr(res_b, 'data') and res_b.data:
                draft_id = res_b.data[0]['id']
                prods_act = res_b.data[0].get('productos', [])
                nombres_act = [p.get('Producto') for p in prods_act]
                for np in prods:
                    if np['Producto'] not in nombres_act: 
                        prods_act.append(np)
                client.table("pedidos_proveedores").update({"productos": prods_act}).eq("id", draft_id).execute()
            else:
                client.table("pedidos_proveedores").insert({"proveedor_id": p_id, "estado": "Borrador", "productos": prods}).execute()
        generados = True
        
    return generados
