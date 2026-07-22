def realizar_transferencia_interna(client, ori_sel, des_sel, cant_trans, lista_bancos):
    """
    Realiza una transferencia interna entre cuentas bancarias o desde la caja fuerte.
    Retorna (True, mensaje) en caso de éxito, (False, mensaje) si hay error.
    """
    if ori_sel == des_sel:
        return False, "El origen y el destino no pueden ser el mismo."
        
    if not cant_trans or cant_trans <= 0:
        return False, "La cantidad a transferir debe ser mayor que 0."

    aviso_caja = ""
    # 1. Procesar Origen
    if "Caja Fuerte" in ori_sel:
        res_caja = client.table("control_caja").select("*").eq("estado", "Abierta").execute()
        if res_caja.data:
            id_caja_abierta = res_caja.data[0]['id']
            client.table("movimientos_caja").insert({
                "id_caja": id_caja_abierta, 
                "tipo": "Retirada", 
                "cantidad": float(cant_trans), 
                "motivo": f"Ingreso a banco: {des_sel.split(' (')[0]}"
            }).execute()
        else:
            aviso_caja = "⚠️ La caja fuerte está cerrada. El dinero se sumará al banco, pero no se restará del arqueo actual porque no hay turno abierto."
    else:
        nombre_banco_ori = ori_sel.split(" (")[0].replace("🏦 ", "")
        banco_ori = next((b for b in lista_bancos if b['nombre_banco'] == nombre_banco_ori), None)
        if banco_ori: 
            client.table("cuentas_bancarias").update({
                "saldo_actual": banco_ori['saldo_actual'] - cant_trans
            }).eq("id", banco_ori['id']).execute()
    
    # 2. Procesar Destino
    nombre_banco_des = des_sel.split(" (")[0].replace("🏦 ", "")
    banco_des = next((b for b in lista_bancos if b['nombre_banco'] == nombre_banco_des), None)
    if banco_des: 
        client.table("cuentas_bancarias").update({
            "saldo_actual": banco_des['saldo_actual'] + cant_trans
        }).eq("id", banco_des['id']).execute()
        
    mensaje_final = f"Transferencia de {cant_trans:.2f} € completada con éxito."
    if aviso_caja:
        mensaje_final = f"{aviso_caja}\n{mensaje_final}"
        
    return True, mensaje_final
