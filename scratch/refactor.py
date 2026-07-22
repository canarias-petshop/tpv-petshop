import sys

with open('tpv.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if 'carrito_limpio = [item for item in carrito_limpio if item.get(\'Producto\')' in line:
        start_idx = i - 1 
    if '"email_cliente": cliente_email' in line:
        end_idx = i + 1 

if start_idx != -1 and end_idx != -1:
    new_code = '''                        try:
                            from core_tpv import procesar_venta
                            
                            cliente_info = None
                            if "Ninguno" not in cliente_fidelidad:
                                cliente_info = mapa_clientes_tpv.get(cliente_fidelidad, {})

                            res_last = fetch_last_hash_tpv(client)
                            hash_anterior = res_last.data[0].get("hash_actual", "") if res_last.data else ""

                            ticket_info = procesar_venta(
                                client=client,
                                carrito=carrito_limpio,
                                total_f=total_f,
                                pagado_hoy=pagado_hoy,
                                pendiente=pendiente,
                                metodo_log=metodo_log,
                                p_efectivo=p_efectivo,
                                p_tarjeta=p_tarjeta,
                                p_bizum=p_bizum,
                                desc_g_val=desc_g_val,
                                cliente_info=cliente_info,
                                puntos_a_descontar=puntos_a_descontar,
                                vale_aplicado=st.session_state.vale_aplicado,
                                banco_sel_id=banco_sel_id,
                                banco_sel_saldo=banco_sel_saldo,
                                enviar_domicilio=enviar_domicilio,
                                dir_entrega=dir_entrega,
                                cfg=cfg,
                                hash_anterior=hash_anterior
                            )
                            
                            st.session_state.ticket_actual = ticket_info
'''
    lines = lines[:start_idx] + [new_code] + lines[end_idx:]
    with open('tpv.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print('Refactor successful')
else:
    print('Could not find block', start_idx, end_idx)
