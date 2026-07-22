import pandas as pd
from postgrest import SyncPostgrestClient

def crear_producto(client: SyncPostgrestClient, nombre: str, sku: str, cod_barras: str, 
                   p_base: float, igic_tipo: float, pvp: float, stock_actual: int, 
                   stock_minimo: int, cantidad_reponer: int, proveedores_ids: list):
    """Registra un nuevo producto y lo asocia a proveedores si se indica."""
    if not nombre or not sku:
        raise ValueError("Nombre y SKU son obligatorios.")
        
    res_ins = client.table("productos").insert({
        "nombre": nombre, "sku": sku, "codigo_barras": cod_barras, "categoria": "Producto",
        "familia": "Generico", "marca": "Generico", "precio_base": p_base, "igic_tipo": igic_tipo, 
        "precio_pvp": pvp, "stock_actual": stock_actual, "stock_minimo": stock_minimo,
        "cantidad_reponer": cantidad_reponer
    }).execute()
    
    nuevo_prod = res_ins.data[0] if res_ins.data else None
    
    if nuevo_prod and proveedores_ids:
        rels = [{"producto_id": nuevo_prod['id'], "proveedor_id": pid, "precio_coste": p_base} for pid in proveedores_ids]
        client.table("productos_proveedores").insert(rels).execute()
        
    return nuevo_prod

def crear_servicio(client: SyncPostgrestClient, nombre: str, sku: str, pvp: float, igic_tipo: float):
    """Registra un nuevo servicio calculando automáticamente su base imponible."""
    if not nombre or not sku:
        raise ValueError("Nombre y SKU son obligatorios.")
        
    p_base_calc = pvp / (1 + (igic_tipo / 100))
    
    res_ins = client.table("productos").insert({
        "nombre": nombre, "sku": sku, "codigo_barras": "", "categoria": "Servicio",
        "familia": "Generico", "marca": "Generico", "precio_base": p_base_calc, "igic_tipo": igic_tipo, 
        "precio_pvp": pvp, "stock_actual": 0, "stock_minimo": 0,
        "cantidad_reponer": 0
    }).execute()
    
    return res_ins.data[0] if res_ins.data else None

def traspasar_stock(client: SyncPostgrestClient, id_caja: int, id_unidad: int, cant_cajas: int, uds_por_caja: int):
    """Desempaqueta una caja y traspasa su contenido al producto por unidad."""
    if cant_cajas < 1 or uds_por_caja < 1:
        raise ValueError("Cantidades inválidas para traspaso.")
        
    # Obtener el stock actual de ambos
    res_caja = client.table("productos").select("stock_actual, nombre").eq("id", id_caja).execute()
    res_unidad = client.table("productos").select("stock_actual, nombre").eq("id", id_unidad).execute()
    
    if not res_caja.data or not res_unidad.data:
        raise ValueError("Uno o ambos productos no existen.")
        
    stock_caja_actual = int(float(res_caja.data[0].get('stock_actual', 0)))
    stock_unidad_actual = int(float(res_unidad.data[0].get('stock_actual', 0)))
    
    if stock_caja_actual < cant_cajas:
        raise ValueError(f"No hay suficiente stock de cajas para desempaquetar {cant_cajas}.")
        
    nuevo_stock_caja = stock_caja_actual - cant_cajas
    nuevo_stock_unidad = stock_unidad_actual + (cant_cajas * uds_por_caja)
    
    # Actualizar BD
    client.table("productos").update({"stock_actual": nuevo_stock_caja}).eq("id", id_caja).execute()
    client.table("productos").update({"stock_actual": nuevo_stock_unidad}).eq("id", id_unidad).execute()
    
    return {
        "caja_nombre": res_caja.data[0]['nombre'],
        "nuevo_stock_caja": nuevo_stock_caja,
        "unidad_nombre": res_unidad.data[0]['nombre'],
        "nuevo_stock_unidad": nuevo_stock_unidad
    }

def actualizar_producto(client: SyncPostgrestClient, producto_id: int, datos_update: dict, proveedor_id: int = None, precio_coste: float = 0.0):
    """Actualiza datos de un producto y opcionalmente su proveedor asociado."""
    if not producto_id:
        raise ValueError("ID de producto inválido.")
        
    res = client.table("productos").update(datos_update).eq("id", producto_id).execute()
    
    # Si se provee un proveedor_id, reemplazamos las relaciones anteriores
    if proveedor_id is not None:
        client.table("productos_proveedores").delete().eq("producto_id", producto_id).execute()
        client.table("productos_proveedores").insert({
            "producto_id": producto_id, "proveedor_id": proveedor_id, "precio_coste": precio_coste
        }).execute()
        
    return res.data[0] if res.data else None

def eliminar_producto(client: SyncPostgrestClient, producto_id: int):
    """Elimina un producto (o servicio) del inventario."""
    if not producto_id:
        raise ValueError("ID de producto inválido.")
    client.table("productos").delete().eq("id", producto_id).execute()
    return True
