import streamlit as st
import pandas as pd
import time

def render_pestana_bancos(client):
    st.markdown("<h3 style='margin-top: -15px;'>🏦 Cuentas Bancarias y Tesorería</h3>", unsafe_allow_html=True)
    st.info("💡 En este módulo puedes registrar las cuentas bancarias de la empresa, añadir su IBAN y controlar su saldo en tiempo real.")
    
    col_b1, col_b2 = st.columns([1, 2], gap="large")
    
    with col_b1:
        st.markdown("#### ➕ Añadir Cuenta Bancaria")
        with st.form("nueva_cuenta_banco", clear_on_submit=True, border=True):
            b_nom = st.text_input("Nombre del Banco *", placeholder="Ej: CaixaBank, Caja Siete...")
            b_titular = st.text_input("Titular de la cuenta")
            b_iban = st.text_input("IBAN")
            b_saldo = st.number_input("Saldo Actual Real (€)", value=0.0, format="%.2f")
            
            if st.form_submit_button("💾 Guardar Cuenta", use_container_width=True, type="primary"):
                if b_nom:
                    try:
                        client.table("cuentas_bancarias").insert({
                            "nombre_banco": b_nom, "titular": b_titular,
                            "iban": b_iban, "saldo_actual": float(b_saldo)
                        }).execute()
                        st.success("Cuenta registrada correctamente."); time.sleep(0.5); st.rerun()
                    except Exception:
                        st.error("⚠️ Asegúrate de haber ejecutado el código SQL para crear la tabla 'cuentas_bancarias' en Supabase.")
                else:
                    st.warning("El nombre del banco es obligatorio.")
                    
    with col_b2:
        st.markdown("#### 💳 Tus Cuentas Registradas")
        try:
            res_bancos = client.table("cuentas_bancarias").select("*").order("id").execute()
            if res_bancos.data:
                df_bancos = pd.DataFrame(res_bancos.data)
                
                saldo_total = df_bancos['saldo_actual'].sum()
                st.markdown(f"<div style='background-color: #e8f4f8; padding: 15px; border-radius: 10px; border-left: 5px solid #005275; margin-bottom: 15px;'><h3 style='margin:0; color: #005275;'>Saldo Total Consolidado: {saldo_total:.2f}€</h3></div>", unsafe_allow_html=True)
                
                st.markdown("💡 *Puedes editar directamente el titular, el IBAN o ajustar el Saldo Actual si lo necesitas.*")
                ed_bancos = st.data_editor(
                    df_bancos[['id', 'nombre_banco', 'titular', 'iban', 'saldo_actual']],
                    hide_index=True, use_container_width=True,
                    column_config={"id": None, "nombre_banco": "Banco", "titular": "Titular", "iban": "IBAN", "saldo_actual": st.column_config.NumberColumn("Saldo Actual (€)", format="%.2f")}
                )
                
                if st.button("💾 Guardar Cambios en las Cuentas", type="primary"):
                    for _, row in ed_bancos.iterrows():
                        client.table("cuentas_bancarias").update({"nombre_banco": str(row['nombre_banco']), "titular": str(row['titular']), "iban": str(row['iban']), "saldo_actual": float(row['saldo_actual'])}).eq("id", row['id']).execute()
                    st.success("Datos bancarios actualizados."); time.sleep(0.5); st.rerun()
            else:
                st.info("Aún no has registrado ninguna cuenta bancaria.")
        except:
            st.info("🔧 Las cuentas se mostrarán aquí una vez hayas creado la tabla en la base de datos.")

    st.markdown("---")
    st.markdown("#### 🔄 Transferencias Internas")
    st.info("Mueve dinero entre tus cuentas bancarias o ingresa efectivo sobrante de la caja.")
    
    try:
        res_b = client.table("cuentas_bancarias").select("*").execute()
        lista_bancos = res_b.data if res_b.data else []
        opciones_origen = ["Caja Fuerte (Efectivo)"] + [f"🏦 {b['nombre_banco']} ({b['saldo_actual']:.2f} €)" for b in lista_bancos]
        opciones_destino = [f"🏦 {b['nombre_banco']} ({b['saldo_actual']:.2f} €)" for b in lista_bancos]
        
        with st.form("form_transferencia", border=True):
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1: ori_sel = st.selectbox("Origen del Dinero 📤", opciones_origen)
            with col_t2: des_sel = st.selectbox("Destino del Dinero 📥", opciones_destino)
            with col_t3: cant_trans = st.number_input("Cantidad a transferir (€) *", min_value=0.01, step=10.0, value=None)
            
            if st.form_submit_button("🚀 Realizar Transferencia", type="primary", use_container_width=True):
                if cant_trans and ori_sel != des_sel:
                    # 1. Procesar Origen
                    if "Caja Fuerte" in ori_sel:
                        res_caja = client.table("control_caja").select("*").eq("estado", "Abierta").execute()
                        if res_caja.data:
                            id_caja_abierta = res_caja.data[0]['id']
                            client.table("movimientos_caja").insert({"id_caja": id_caja_abierta, "tipo": "Retirada", "cantidad": float(cant_trans), "motivo": f"Ingreso a banco: {des_sel.split(' (')[0]}"}).execute()
                        else:
                            st.warning("⚠️ La caja fuerte está cerrada. El dinero se sumará al banco, pero no se restará del arqueo actual porque no hay turno abierto.")
                    else:
                        nombre_banco_ori = ori_sel.split(" (")[0].replace("🏦 ", "")
                        banco_ori = next((b for b in lista_bancos if b['nombre_banco'] == nombre_banco_ori), None)
                        if banco_ori: client.table("cuentas_bancarias").update({"saldo_actual": banco_ori['saldo_actual'] - cant_trans}).eq("id", banco_ori['id']).execute()
                    
                    # 2. Procesar Destino
                    nombre_banco_des = des_sel.split(" (")[0].replace("🏦 ", "")
                    banco_des = next((b for b in lista_bancos if b['nombre_banco'] == nombre_banco_des), None)
                    if banco_des: client.table("cuentas_bancarias").update({"saldo_actual": banco_des['saldo_actual'] + cant_trans}).eq("id", banco_des['id']).execute()
                        
                    st.success(f"Transferencia de {cant_trans:.2f} € completada con éxito."); time.sleep(1.5); st.rerun()
                elif ori_sel == des_sel: st.error("El origen y el destino no pueden ser el mismo.")
                else: st.warning("Introduce una cantidad válida.")
    except Exception as e: st.error(f"Error al cargar módulo de transferencias: {e}")