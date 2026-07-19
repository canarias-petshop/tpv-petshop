import sys

with open('facturacion.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx_em = -1
end_idx_em = -1
for i, line in enumerate(lines):
    if 'c_id = df_cli[df_cli[\'nombre_dueno\'] == sel_c.split(" | ")[0]].iloc[0][\'id\']' in line:
        start_idx_em = i
    if 'st.session_state.factura_v_temp = []; st.success("Factura guardada' in line:
        end_idx_em = i + 1
        break

if start_idx_em != -1 and end_idx_em != -1:
    new_code_em = '''                    c_id = df_cli[df_cli['nombre_dueno'] == sel_c.split(" | ")[0]].iloc[0]['id']
                    
                    try:
                        from core_facturacion import emitir_factura_cliente
                        res_last_f = get_last_hash_fac(client)
                        hash_ant_f = res_last_f.data[0].get("hash_actual", "") if res_last_f.data else ""
                        
                        emitir_factura_cliente(
                            client=client,
                            cliente_id=int(c_id),
                            total_neto=float(total_base_final),
                            total_igic=float(total_igic_final),
                            total_final=float(total_v_final),
                            descuento_global=float(desc_g_val),
                            forma_pago=f_pago,
                            fecha_vencimiento=str(f_vence),
                            productos=st.session_state.factura_v_temp,
                            hash_anterior=hash_ant_f
                        )
                        st.session_state.db_version = st.session_state.get('db_version', 0) + 1
                        st.session_state.factura_v_temp = []
                        st.success("Factura guardada correctamente.")
                        time.sleep(1)
                        limpiar_cache_facturacion()
                        st.rerun()
                    except Exception as e:
                        st.error(f"🚨 Error al emitir factura: {e}")
'''
    lines = lines[:start_idx_em] + [new_code_em] + lines[end_idx_em:]
    with open('facturacion.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Refactor emitir factura exitoso.")
else:
    print("No se encontró el bloque de emitir factura.", start_idx_em, end_idx_em)
    
# Ahora registrar compra borrador
with open('facturacion.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx_co = -1
end_idx_co = -1
for i, line in enumerate(lines):
    if 'res_dup = get_compras_dup_fac(client, prov_id_final, tipo_doc_completo)' in line:
        start_idx_co = i - 1 # Incluir '# --- ESCUDO ANTI-DUPLICADOS...'
    if 'msg_exito = f"✅ ¡Factura escaneada y guardada en BORRADOR!' in line:
        end_idx_co = i + 1
        break

if start_idx_co != -1 and end_idx_co != -1:
    new_code_co = '''                                # --- REFAC: core_facturacion ---
                                try:
                                    from core_facturacion import registrar_compra_borrador
                                    res_compra = registrar_compra_borrador(
                                        client=client,
                                        proveedor_id=prov_id_final,
                                        num_fac=num_fac,
                                        es_abono=es_abono,
                                        productos=st.session_state.compra_temp,
                                        dto_pp=dto_pp_val,
                                        fecha_fac=fecha_fac,
                                        total=total_guardar_ia
                                    )
                                    if res_compra.get("fusionado"):
                                        msg_exito = f"🔄 ¡Página fusionada! La factura '{num_fac}' ya existía como borrador y se le han añadido estos artículos."
                                    else:
                                        msg_exito = f"✅ ¡Factura escaneada y guardada en BORRADOR! Ve a 'Archivo de Documentos' para validarla."
                                except ValueError as ve:
                                    st.error(f"🚨 **¡ATENCIÓN!** {ve}")
                                    st.session_state.compra_temp = []
                                    st.stop()
'''
    lines = lines[:start_idx_co] + [new_code_co] + lines[end_idx_co:]
    with open('facturacion.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Refactor registrar compra exitoso.")
else:
    print("No se encontró el bloque de registrar compra.", start_idx_co, end_idx_co)

# Ahora registrar pago
with open('facturacion.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx_pa = -1
end_idx_pa = -1
for i, line in enumerate(lines):
    if 'nuevo_estado = "Pagado" if nuevo_pendiente <= 0 else "Pendiente"' in line:
        start_idx_pa = i - 4 # Include 'nuevo_pagado = ...'
    if 'st.success(f"Pago de {pago_eur:.2f}€ registrado correctamente.")' in line:
        end_idx_pa = i + 1
        break

if start_idx_pa != -1 and end_idx_pa != -1:
    # Actually, the logic in facturacion.py for paying debt:
    # I should find exactly how it's written in facturacion.py. Let's not touch it yet.
    pass
