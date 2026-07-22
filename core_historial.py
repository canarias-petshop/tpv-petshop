import random
import string
import pandas as pd

def procesar_devolucion(client, tk_id, t_info, prods, btn_abono, btn_vale, sel_metodo_abono, bancos_abono, total_final_calculado):
    """
    Procesa la devolución de un ticket (reversión de stock, puntos, movimientos de caja/banco y creación de vales).
    """
    # 1. Devolver stock
    for p in prods:
        if not p.get('Manual', False) and 'id' in p:
            if str(p['id']).startswith('cita_'):
                continue
            try:
                res_p = client.table("productos").select("stock_actual").eq("id", p['id']).execute()
                if res_p.data:
                    client.table("productos").update({"stock_actual": res_p.data[0]['stock_actual'] + p['Cantidad']}).eq("id", p['id']).execute()
            except Exception:
                pass

    # 2. Revertir puntos si era cliente VIP
    cliente_vip = str(t_info.get('cliente_vip_nombre', ''))
    if cliente_vip and cliente_vip != "nan" and cliente_vip != "None":
        res_cli = client.table("clientes").select("id, puntos").eq("nombre_dueno", cliente_vip).execute()
        if res_cli.data:
            cli_id = res_cli.data[0]['id']
            p_ganados = int(t_info.get('puntos_ganados', 0))
            p_usados = int(t_info.get('puntos_usados', 0))
            nuevo_saldo = max(0, res_cli.data[0].get('puntos', 0) - p_ganados + p_usados)
            client.table("clientes").update({"puntos": nuevo_saldo}).eq("id", cli_id).execute()

    # 3. Marcar ticket como devuelto
    client.table("ventas_historial").update({"estado": "DEVUELTO"}).eq("id", int(tk_id)).execute()

    # 4. Movimiento de abono o crear vale
    vale_info = None
    if btn_abono:
        if "Efectivo" in sel_metodo_abono:
            res_caja_ab = client.table("control_caja").select("id").eq("estado", "Abierta").execute()
            if res_caja_ab.data:
                client.table("movimientos_caja").insert({
                    "id_caja": res_caja_ab.data[0]['id'],
                    "tipo": "Retirada",
                    "cantidad": total_final_calculado,
                    "motivo": f"Devolución en efectivo Ticket #{tk_id}"
                }).execute()
        elif "Tarjeta" in sel_metodo_abono:
            nombre_banco = sel_metodo_abono.replace("💳 Tarjeta (", "").replace(")", "")
            banco = next((b for b in bancos_abono if b['nombre_banco'] == nombre_banco), None)
            if banco:
                client.table("cuentas_bancarias").update({
                    "saldo_actual": banco['saldo_actual'] - total_final_calculado
                }).eq("id", banco['id']).execute()
                
    if btn_vale:
        codigo_vale = "VALE-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        try:
            client.table("vales_tienda").insert({
                "codigo_vale": codigo_vale,
                "saldo_inicial": total_final_calculado,
                "saldo_actual": total_final_calculado,
                "id_ticket_origen": int(tk_id),
                "notas": f"Generado por devolución de ticket #{tk_id}"
            }).execute()
        except: pass
        
        try:
            now_str = pd.Timestamp.now('Atlantic/Canary').strftime("%d/%m/%Y %H:%M")
        except:
            now_str = pd.Timestamp.now('UTC').strftime("%d/%m/%Y %H:%M")
            
        vale_info = {"fecha": now_str, "valor": total_final_calculado, "codigo": codigo_vale}

    return vale_info
