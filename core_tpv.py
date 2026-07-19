import json
import hashlib
from datetime import datetime
import copy

def calcular_totales(
    carrito: list, 
    descuento_global_pct: float = 0.0, 
    puntos_disp: int = 0, 
    tiene_deuda: bool = False, 
    limite_desc_puntos_pct: float = 50.0, 
    valor_punto_eur: float = 0.50, 
    saldo_vale: float = 0.0,
    usar_puntos: bool = False
) -> dict:
    """
    Calcula todos los totales de un carrito de compra.
    Retorna un diccionario con los detalles de la compra para renderizar la UI y luego procesar.
    """
    
    subtotal_bruto = sum(float(item.get("Precio", 0)) * int(item.get("Cantidad", 1)) for item in carrito)
    subtotal_con_descuentos_linea = sum(float(item.get("Subtotal", 0)) for item in carrito)
    
    # 1. Aplicar descuento global
    total = subtotal_con_descuentos_linea * (1 - (descuento_global_pct / 100))
    if total < 0: total = 0.0
    
    # 2. Puntos (Fidelización)
    puntos_permitidos = 0
    desc_puntos_eur = 0.0
    if puntos_disp > 0 and not tiene_deuda:
        max_descuento_eur = total * (limite_desc_puntos_pct / 100.0)
        max_puntos_permitidos = int(max_descuento_eur / valor_punto_eur)
        puntos_permitidos = min(puntos_disp, max_puntos_permitidos)
        
        if usar_puntos:
            desc_puntos_eur = puntos_permitidos * valor_punto_eur
            
    total -= desc_puntos_eur
    if total < 0: total = 0.0
    
    # 3. Vales de Tienda
    desc_vale_eur = min(saldo_vale, total)
    total -= desc_vale_eur
    if total < 0: total = 0.0
    
    return {
        "subtotal_bruto": subtotal_bruto,
        "subtotal_lineas": subtotal_con_descuentos_linea,
        "total_final": total,
        "puntos_usados": puntos_permitidos if usar_puntos else 0,
        "desc_puntos_eur": desc_puntos_eur,
        "desc_vale_eur": desc_vale_eur
    }

def procesar_venta(
    client, 
    carrito: list, 
    total_f: float, 
    pagado_hoy: float, 
    pendiente: float, 
    metodo_log: str, 
    p_efectivo: float, 
    p_tarjeta: float, 
    p_bizum: float, 
    desc_g_val: float, 
    cliente_info: dict, 
    puntos_a_descontar: int, 
    vale_aplicado: dict, 
    banco_sel_id: int, 
    banco_sel_saldo: float, 
    enviar_domicilio: bool, 
    dir_entrega: str, 
    cfg: dict,
    hash_anterior: str = ""
) -> dict:
    """
    Registra la venta en la base de datos, actualizando stock, puntos, caja y vales.
    Devuelve los datos del ticket para imprimir.
    """
    # --- Limpieza del carrito ---
    carrito_limpio = [item for item in carrito if item.get('Producto') and str(item.get('Producto')).strip() != '']
    if not carrito_limpio:
        raise ValueError("El carrito está vacío o contiene líneas no válidas.")
        
    cliente_fidel_nombre = cliente_info.get('nombre_dueno', '') if cliente_info else ""
    cliente_id = cliente_info.get('id', None) if cliente_info else None
    
    puntos_ganados = 0
    nuevo_saldo_puntos = 0
    if cliente_info:
        if pendiente == 0:
            puntos_ganados = int(total_f // float(cfg.get('euros_para_un_punto', 10.0)))
        
        ptos_act = int(cliente_info.get('puntos') or 0)
        nuevo_saldo_puntos = ptos_act - puntos_a_descontar + puntos_ganados
        client.table("clientes").update({"puntos": nuevo_saldo_puntos}).eq("id", cliente_id).execute()
        
    data_to_hash = f"TICKET|{datetime.now().isoformat()}|{total_f:.2f}|{hash_anterior}"
    hash_actual = hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest().upper()
    
    carrito_db = copy.deepcopy(carrito_limpio)
    metodo_final_log = str(metodo_log)
    
    desc_vale_eur = 0.0
    if vale_aplicado:
        saldo_vale = float(vale_aplicado.get('saldo_actual', 0))
        desc_vale_eur = min(saldo_vale, total_f + (float(vale_aplicado.get('desc_vale_eur', 0)))) # Aproximación si total_f ya está descontado
        
        if desc_vale_eur > 0:
            carrito_db.append({
                "__meta__": True,
                "vale_aplicado": vale_aplicado.get('codigo_vale', ''),
                "desc_vale_eur": desc_vale_eur
            })
            if float(pagado_hoy) == 0:
                metodo_final_log = f"Vale ({vale_aplicado.get('codigo_vale', '')})"
            else:
                metodo_final_log += f" + Vale ({vale_aplicado.get('codigo_vale', '')})"

    res_venta = client.table("ventas_historial").insert({
        "total": float(total_f), 
        "pagado": float(pagado_hoy), 
        "pendiente": float(pendiente),
        "metodo_pago": metodo_final_log, 
        "cliente_deuda": str(cliente_fidel_nombre) if pendiente > 0 else "",
        "descuento_global": float(desc_g_val), 
        "productos": carrito_db, 
        "estado": "Completado" if pendiente == 0 else "Deuda",
        "pago_efectivo": float(p_efectivo),
        "pago_tarjeta": float(p_tarjeta),
        "pago_bizum": float(p_bizum),
        "cliente_vip_nombre": cliente_fidel_nombre,
        "puntos_ganados": puntos_ganados,
        "puntos_usados": puntos_a_descontar,
        "hash_anterior": hash_anterior,
        "hash_actual": hash_actual
    }).execute()
    
    ticket_num = res_venta.data[0]['id'] if res_venta.data else "S/N"
    
    if banco_sel_id and p_tarjeta > 0:
        client.table("cuentas_bancarias").update({"saldo_actual": float(banco_sel_saldo + p_tarjeta)}).eq("id", banco_sel_id).execute()
        
    if vale_aplicado and desc_vale_eur > 0:
        nuevo_saldo_vale = float(vale_aplicado.get('saldo_actual', 0)) - desc_vale_eur
        client.table("vales_tienda").update({"saldo_actual": nuevo_saldo_vale}).eq("id", vale_aplicado.get('id')).execute()
        
    if enviar_domicilio and cliente_fidel_nombre:
        detalle_pedido = "\\n".join([f"• {p['Cantidad']}x {p['Producto']}" for p in carrito_limpio])
        client.table("pedidos_domicilio").insert({
            "nombre_cliente": cliente_fidel_nombre,
            "telefono": cliente_info.get('telefono', ''),
            "direccion": dir_entrega,
            "detalle_pedido": detalle_pedido,
            "estado": "Pendiente"
        }).execute()
        
    for i in carrito_limpio:
        if not i.get('Manual', False) and 'id' in i:
            if str(i['id']).startswith('cita_'):
                continue
            try:
                res = client.table("productos").select("stock_actual").eq("id", i['id']).execute()
                if res.data:
                    n_stock = int(res.data[0]['stock_actual']) - int(i['Cantidad'])
                    client.table("productos").update({"stock_actual": n_stock}).eq("id", i['id']).execute()
            except Exception:
                pass
                
    ticket_info = {
        "id": ticket_num,
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "total": float(total_f),
        "pagado": float(pagado_hoy),
        "productos": carrito_limpio,
        "metodo": metodo_final_log,
        "descuento_global": float(desc_g_val),
        "cliente_fidel": cliente_fidel_nombre,
        "puntos_ganados": puntos_ganados,
        "puntos_descontados": puntos_a_descontar,
        "nuevo_saldo": nuevo_saldo_puntos,
        "desc_vale_eur": desc_vale_eur,
        "vale_aplicado": vale_aplicado.get('codigo_vale', '') if vale_aplicado else None,
        "email_cliente": cliente_info.get('email', '') if cliente_info else ''
    }
    
    return ticket_info
