import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

def emitir_factura_cliente(
    client, 
    cliente_id: int, 
    total_neto: float, 
    total_igic: float, 
    total_final: float,
    descuento_global: float, 
    forma_pago: str, 
    fecha_vencimiento: str, 
    productos: list, 
    hash_anterior: str = ""
) -> dict:
    """
    Registra una factura emitida a un cliente en la base de datos y resta el stock de los productos vendidos.
    """
    if not productos:
        raise ValueError("No se puede emitir una factura sin productos.")
        
    data_to_hash = f"FACTURA|{datetime.now(ZoneInfo('Atlantic/Canary')).isoformat()}|{total_final:.2f}|{hash_anterior}"
    hash_actual = hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest().upper()
    
    res_fac = client.table("facturas").insert({
        "cliente_id": cliente_id, 
        "total_neto": float(total_neto), 
        "total_igic": float(total_igic), 
        "total_final": float(total_final),
        "descuento_global": float(descuento_global), 
        "forma_pago": forma_pago, 
        "fecha_vencimiento": str(fecha_vencimiento), 
        "productos": productos,
        "hash_anterior": hash_anterior, 
        "hash_actual": hash_actual
    }).execute()
    
    # Restar stock de productos vendidos
    for p in productos:
        if str(p.get('id', '0')) != '0' and str(p.get('id')) != 'None':
            if str(p['id']).startswith('cita_'):
                continue
            try:
                res = client.table("productos").select("stock_actual").eq("id", p['id']).execute()
                if res.data:
                    n_stock = res.data[0]['stock_actual'] - p.get('Cantidad', 1)
                    client.table("productos").update({"stock_actual": n_stock}).eq("id", p['id']).execute()
            except Exception:
                pass
                
    return res_fac.data[0] if res_fac.data else None


def registrar_compra_borrador(
    client, 
    proveedor_id: int, 
    num_fac: str, 
    es_abono: bool, 
    productos: list, 
    dto_pp: float, 
    fecha_fac: str, 
    total: float
) -> dict:
    """
    Registra una factura de compra (o abono) de proveedor en estado 'Borrador'.
    Si ya existe un borrador con el mismo número, fusiona los productos.
    """
    if not productos:
        raise ValueError("No se puede registrar una compra sin productos.")
        
    prefijo_doc = "Abono" if es_abono else "Factura"
    tipo_doc_completo = f"{prefijo_doc}: {num_fac}"
    
    res_dup = client.table("compras").select("id, estado, productos, total, pendiente").eq("proveedor_id", proveedor_id).eq("tipo", tipo_doc_completo).execute()
    
    if res_dup.data and num_fac != "S/N":
        fac_dup = res_dup.data[0]
        if fac_dup['estado'] == 'Borrador':
            prods_ant = fac_dup.get('productos', [])
            if not isinstance(prods_ant, list): prods_ant = []
            prods_ant.extend(productos)
            
            nuevo_tot = float(fac_dup['total']) + total
            nuevo_pen = float(fac_dup['pendiente']) + total
            
            res_update = client.table("compras").update({
                "productos": prods_ant, 
                "total": round(nuevo_tot, 2), 
                "pendiente": round(nuevo_pen, 2)
            }).eq("id", fac_dup['id']).execute()
            
            return {"fusionado": True, "data": res_update.data[0] if res_update.data else None}
        else:
            raise ValueError(f"El {prefijo_doc} '{num_fac}' ya existe y está archivado.")
    else:
        res_insert = client.table("compras").insert({
            "proveedor_id": proveedor_id, 
            "total": round(total, 2), 
            "descuento_pp": float(dto_pp), 
            "estado": "Borrador", 
            "tipo": tipo_doc_completo, 
            "fecha_vencimiento": fecha_fac, 
            "fecha_factura": fecha_fac, 
            "productos": productos, 
            "pagado": 0.0, 
            "pendiente": round(total, 2)
        }).execute()
        
        return {"fusionado": False, "data": res_insert.data[0] if res_insert.data else None}


def registrar_pago_deuda(client, compra_id: int, pago_eur: float, cuenta_id: int) -> dict:
    """
    Registra un pago sobre una deuda de compra a proveedor.
    """
    if pago_eur <= 0:
        raise ValueError("El importe del pago debe ser mayor a 0.")
        
    res_compra = client.table("compras").select("id, pagado, pendiente, total").eq("id", compra_id).execute()
    if not res_compra.data:
        raise ValueError("Compra no encontrada.")
        
    compra = res_compra.data[0]
    pendiente = float(compra['pendiente'])
    pagado = float(compra['pagado'])
    
    if pago_eur > pendiente:
        raise ValueError(f"No puedes pagar {pago_eur}€ porque la deuda pendiente es de {pendiente}€.")
        
    nuevo_pagado = pagado + pago_eur
    nuevo_pendiente = pendiente - pago_eur
    nuevo_estado = "Pagado" if nuevo_pendiente <= 0.01 else "Pendiente"
    
    # Restar de cuenta bancaria
    if cuenta_id:
        res_cuenta = client.table("cuentas_bancarias").select("saldo_actual").eq("id", cuenta_id).execute()
        if res_cuenta.data:
            nuevo_saldo = float(res_cuenta.data[0]['saldo_actual']) - pago_eur
            client.table("cuentas_bancarias").update({"saldo_actual": nuevo_saldo}).eq("id", cuenta_id).execute()
            
    res_update = client.table("compras").update({
        "pagado": nuevo_pagado,
        "pendiente": nuevo_pendiente,
        "estado": nuevo_estado
    }).eq("id", compra_id).execute()
    
    return res_update.data[0] if res_update.data else None
