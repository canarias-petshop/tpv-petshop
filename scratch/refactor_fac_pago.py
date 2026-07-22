import sys

with open('facturacion.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx_pa = -1
end_idx_pa = -1
for i, line in enumerate(lines):
    if 'if pago_exitoso:' in line:
        start_idx_pa = i
    if 'st.success(f"¡Pago de {total_a_pagar:.2f}' in line:
        end_idx_pa = i + 1
        break

if start_idx_pa != -1 and end_idx_pa != -1:
    new_code_pa = '''                        if pago_exitoso:
                            from core_facturacion import registrar_pago_deuda
                            for _, row in filas_pagar.iterrows():
                                c_id = row['id']
                                pago_hoy = float(row['A Pagar Hoy (€)'])
                                try:
                                    registrar_pago_deuda(client, c_id, pago_hoy, cuenta_id=None)
                                except ValueError as ve:
                                    st.error(f"Error: {ve}")
                            st.success(f"¡Pago de {total_a_pagar:.2f} € registrado correctamente!")
                            time.sleep(1.5)
                            st.rerun()
'''
    lines = lines[:start_idx_pa] + [new_code_pa] + lines[end_idx_pa:]
    with open('facturacion.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Refactor pagar deuda exitoso.")
else:
    print("No se encontró el bloque de pago.", start_idx_pa, end_idx_pa)
