import streamlit as st
import pandas as pd
import time

def render_pestana_bancos(client):
    if 'llave_bancos_nueva' not in st.session_state: st.session_state.llave_bancos_nueva = 0
    if 'llave_bancos_trans' not in st.session_state: st.session_state.llave_bancos_trans = 0

    st.markdown("<h3 style='margin-top: -15px;'>🏦 Cuentas Bancarias y Tesorería</h3>", unsafe_allow_html=True)
    st.info("💡 En este módulo puedes registrar las cuentas bancarias de la empresa, añadir su IBAN y controlar su saldo en tiempo real.")
    
    col_b1, col_b2 = st.columns([1, 2], gap="large")
    
    with col_b1:
        st.markdown("#### ➕ Añadir Cuenta Bancaria")
        with st.form("nueva_cuenta_banco", clear_on_submit=True, border=True):
            b_nom = st.text_input("Nombre del Banco *", placeholder="Ej: CaixaBank, Caja Siete...", key=f"b_nom_{st.session_state.llave_bancos_nueva}")
            b_titular = st.text_input("Titular de la cuenta", key=f"b_tit_{st.session_state.llave_bancos_nueva}")
            b_iban = st.text_input("IBAN", key=f"b_ib_{st.session_state.llave_bancos_nueva}")
            b_saldo = st.number_input("Saldo Actual Real (€)", value=0.0, format="%.2f", step=0.01, key=f"b_sal_{st.session_state.llave_bancos_nueva}")
            
            if st.form_submit_button("💾 Guardar Cuenta", use_container_width=True, type="primary"):
                if b_nom:
                    try:
                        client.table("cuentas_bancarias").insert({
                            "nombre_banco": b_nom, "titular": b_titular,
                            "iban": b_iban, "saldo_actual": float(b_saldo)
                        }).execute()
                        st.session_state.llave_bancos_nueva += 1
                        st.success("Cuenta registrada correctamente."); time.sleep(0.5); st.rerun()
                    except Exception:
                        st.error("⚠️ Asegúrate de haber ejecutado el código SQL para crear la tabla 'cuentas_bancarias' en Supabase.")
                else:
                    st.warning("El nombre del banco es obligatorio.")
                    
    with col_b2:
        st.markdown("#### 💳 Tus Cuentas Registradas")
        try:
            res_bancos = client.table("cuentas_bancarias").select("id, nombre_banco, titular, iban, saldo_actual").order("id").execute()
            if res_bancos.data:
                df_bancos = pd.DataFrame(res_bancos.data)
                
                saldo_total = df_bancos['saldo_actual'].sum()
                st.markdown(f"<div style='background-color: #e8f4f8; padding: 15px; border-radius: 10px; border-left: 5px solid #005275; margin-bottom: 15px;'><h3 style='margin:0; color: #005275;'>Saldo Total Consolidado: {saldo_total:.2f}€</h3></div>", unsafe_allow_html=True)
                
                st.markdown("💡 *Puedes editar directamente el titular, el IBAN o ajustar el Saldo Actual si lo necesitas.*")
                ed_bancos = st.data_editor(
                    df_bancos[['id', 'nombre_banco', 'titular', 'iban', 'saldo_actual']],
                    hide_index=True, use_container_width=True,
                    column_config={"id": None, "nombre_banco": "Banco", "titular": "Titular", "iban": "IBAN", "saldo_actual": st.column_config.NumberColumn("Saldo Actual (€)", format="%.2f", step=0.01)}
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
        res_b = client.table("cuentas_bancarias").select("id, nombre_banco, saldo_actual").execute()
        lista_bancos = res_b.data if res_b.data else []
        opciones_origen = ["Caja Fuerte (Efectivo)"] + [f"🏦 {b['nombre_banco']} ({b['saldo_actual']:.2f} €)" for b in lista_bancos]
        opciones_destino = [f"🏦 {b['nombre_banco']} ({b['saldo_actual']:.2f} €)" for b in lista_bancos]
        
        with st.form("form_transferencia", border=True):
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1: ori_sel = st.selectbox("Origen del Dinero 📤", opciones_origen, key=f"b_ori_{st.session_state.llave_bancos_trans}")
            with col_t2: des_sel = st.selectbox("Destino del Dinero 📥", opciones_destino, key=f"b_des_{st.session_state.llave_bancos_trans}")
            with col_t3: cant_trans = st.number_input("Cantidad a transferir (€) *", min_value=0.01, step=0.01, value=None, format="%.2f", key=f"b_can_{st.session_state.llave_bancos_trans}")
            
            if st.form_submit_button("🚀 Realizar Transferencia", type="primary", use_container_width=True):
                from core_bancos import realizar_transferencia_interna
                ok, msg = realizar_transferencia_interna(client, ori_sel, des_sel, cant_trans, lista_bancos)
                
                if ok:
                    st.session_state.llave_bancos_trans += 1
                    if "⚠️" in msg:
                        st.warning(msg.split('\n')[0])
                        st.success(msg.split('\n')[1])
                    else:
                        st.success(msg)
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(msg)
                else: st.warning("Introduce una cantidad válida.")
    except Exception as e: st.error(f"Error al cargar módulo de transferencias: {e}")