import streamlit as st
import pandas as pd
import time
import streamlit.components.v1 as components

def render_pestana_caja(client):
    try:
        res_caja = client.table("control_caja").select("*").eq("estado", "Abierta").execute()
        caja_actual = res_caja.data[0] if res_caja.data else None
    except:
        caja_actual = None

    if not caja_actual:
        st.info("😴 La caja está actualmente CERRADA.")
        
        try:
            res_ult_caja = client.table("control_caja").select("*").eq("estado", "Cerrada").order("id", desc=True).limit(1).execute()
            if res_ult_caja.data:
                ult_caja = res_ult_caja.data[0]
                resumen = ult_caja.get('resumen_pagos', {})
                if not resumen: resumen = {"Efectivo": 0, "Tarjeta": 0, "Bizum": 0, "Ingresos": 0, "Retiradas": 0}
                f_apertura = pd.to_datetime(ult_caja['created_at']).strftime('%d/%m/%Y %H:%M')
                
                st.markdown(f"#### 🖨️ Último Cierre de Caja Registrado (Apertura: {f_apertura})")
                
                html_cierre_ult = f"""
                <!DOCTYPE html>
                <html>
                <head>
                <style>
                    @media screen {{
                        #ticket-z {{ display: block; border: 1px solid #ccc; padding: 15px; margin-top: 15px; background-color: #fffaf0; width: 300px; margin-left: auto; margin-right: auto; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }}
                        .btn-print-z {{ background-color: #005275; color: white; border: none; padding: 10px; border-radius: 5px; width: 100%; font-weight: bold; cursor: pointer; margin-bottom: 15px; }}
                    }}
                    @media print {{
                        #btn-area {{ display: none; }}
                        #ticket-z {{ display: block; font-family: monospace; font-size: 12px; width: 300px; color: black; }}
                    }}
                </style>
                </head>
                <body>
                    <div id="btn-area">
                        <button class="btn-print-z" onclick="window.print()">🖨️ IMPRIMIR ÚLTIMO CIERRE Z</button>
                    </div>
                    <div id="ticket-z">
                        <div style="text-align: center; font-weight: bold; font-size: 16px;">CIERRE DE CAJA Z</div>
                        <div style="text-align: center;">ANIMALARIUM</div>
                        <hr style="border-top: 1px dashed black;">
                        Apertura: {f_apertura}<br>
                        Fondo Inicial: {ult_caja['fondo_inicial']:.2f} €<br>
                        <hr style="border-top: 1px dashed black;">
                        <b>VENTAS POR MÉTODO:</b><br>
                        Efectivo: {resumen.get('Efectivo', 0):.2f} €<br>
                        Tarjeta (Caixa): {resumen.get('Tarjeta Caixa', 0):.2f} €<br>
                        Tarjeta (C.Siete): {resumen.get('Tarjeta Caja Siete', 0):.2f} €<br>
                        Bizum: {resumen.get('Bizum', 0):.2f} €<br>
                        <hr style="border-top: 1px dashed black;">
                        <b>MOVIMIENTOS DE CAJA:</b><br>
                        Ingresos Extra: +{resumen.get('Ingresos', 0):.2f} €<br>
                        Retiradas/Pagos: -{resumen.get('Retiradas', 0):.2f} €<br>
                        <hr style="border-top: 1px dashed black;">
                        <b>RESULTADO DEL ARQUEO:</b><br>
                        Efectivo Contado: {ult_caja['total_contado']:.2f} €<br>
                        <b>DESCUADRE: {ult_caja['descuadre']:.2f} €</b><br>
                        <hr style="border-top: 1px dashed black;">
                        <div style="text-align: center;">Firma Responsable</div>
                        <br><br><br>
                    </div>
                </body>
                </html>
                """
                components.html(html_cierre_ult, height=550)
        except: pass
        
        with st.form("abrir_caja", border=True):
            st.markdown("<h4 style='margin: 0 0 10px 0;'>🔓 Apertura de Turno</h4>", unsafe_allow_html=True)
            fondo_ini = st.number_input("Fondo Inicial €", min_value=0.0, step=1.0, value=None)
            if st.form_submit_button("ABRIR CAJA AHORA", type="primary", use_container_width=True):
                fondo_val = fondo_ini or 0.0
                client.table("control_caja").insert({"fondo_inicial": float(fondo_val), "estado": "Abierta"}).execute()
                st.success("¡Caja abierta!"); time.sleep(1); st.rerun()
    else:
        id_caja = caja_actual['id']
        fondo_actual = caja_actual['fondo_inicial']
        fecha_ap_str = caja_actual['created_at']
        fecha_ap_visual = pd.to_datetime(fecha_ap_str).strftime('%d/%m/%Y %H:%M')
        
        st.success(f"🔓 **CAJA ABIERTA** | Inicio: {fecha_ap_visual} | Fondo: **{fondo_actual:.2f}€**")
        st.markdown("<div style='margin-top: -30px;'></div>", unsafe_allow_html=True) 
        
        c_tit1, c_tit2 = st.columns([1, 1.2], gap="large")
        with c_tit1: st.markdown("<h4 style='margin: 0 0 5px 0;'>💸 Entradas y Salidas</h4>", unsafe_allow_html=True)
        with c_tit2: st.markdown("<h4 style='margin: 0 0 5px 0;'>⚖️ Arqueo y Cierre</h4>", unsafe_allow_html=True)

        col_izq, col_der = st.columns([1, 1.2], gap="large")
        
        with col_izq:
            with st.form("form_movimientos", clear_on_submit=True, border=True):
                c_tipo, c_cant = st.columns([1, 1])
                with c_tipo: tipo_mov = st.selectbox("Tipo", ["Retirada 🔻", "Ingreso 🔺"])
                with c_cant: cant_mov = st.number_input("Euros €", min_value=0.01, step=1.0, value=None)
                motivo_mov = st.text_input("Motivo", placeholder="Ej: Pago proveedor, cambio...")
                if st.form_submit_button("Registrar Movimiento", use_container_width=True):
                    if motivo_mov and cant_mov is not None:
                        tipo_limpio = "Retirada" if "Retirada" in tipo_mov else "Ingreso"
                        client.table("movimientos_caja").insert({"id_caja": id_caja, "tipo": tipo_limpio, "cantidad": float(cant_mov), "motivo": motivo_mov}).execute()
                        st.rerun()
            
            res_movs = client.table("movimientos_caja").select("*").eq("id_caja", id_caja).execute()
            if res_movs.data:
                df_m = pd.DataFrame(res_movs.data)[['tipo', 'cantidad', 'motivo']]
                df_m['tipo'] = df_m['tipo'].apply(lambda x: '🔻' if x == 'Retirada' else '🔺')
                st.dataframe(df_m, use_container_width=True, hide_index=True, height=150)

        with col_der:
            with st.container(border=True):
                st.markdown("<p style='font-size: 11px; font-weight: bold; color: gray; margin:0;'>💵 BILLETES</p>", unsafe_allow_html=True)
                cb1, cb2, cb3, cb4, cb5, cb6 = st.columns(6)
                with cb1: b200 = st.number_input("200", 0, step=1, key="b200", value=None)
                with cb2: b100 = st.number_input("100", 0, step=1, key="b100", value=None)
                with cb3: b50 = st.number_input("50", 0, step=1, key="b50", value=None)
                with cb4: b20 = st.number_input("20", 0, step=1, key="b20", value=None)
                with cb5: b10 = st.number_input("10", 0, step=1, key="b10", value=None)
                with cb6: b5 = st.number_input("5", 0, step=1, key="b5", value=None)

                st.markdown("<p style='font-size: 11px; font-weight: bold; color: gray; margin:0; padding-top: 5px;'>🪙 MONEDAS</p>", unsafe_allow_html=True)
                cm1, cm2, cm3, cm4, cm5, cm6, cm7, cm8 = st.columns(8)
                with cm1: m2 = st.number_input("2€", 0, step=1, key="m2", value=None)
                with cm2: m1 = st.number_input("1€", 0, step=1, key="m1", value=None)
                with cm3: m50c = st.number_input("50¢", 0, step=1, key="m50c", value=None)
                with cm4: m20c = st.number_input("20¢", 0, step=1, key="m20c", value=None)
                with cm5: m10c = st.number_input("10¢", 0, step=1, key="m10c", value=None)
                with cm6: m5c = st.number_input("5¢", 0, step=1, key="m5c", value=None)
                with cm7: m2c = st.number_input("2¢", 0, step=1, key="m2c", value=None)
                with cm8: m1c = st.number_input("1¢", 0, step=1, key="m1c", value=None)
                
                total_calc = ((b200 or 0)*200) + ((b100 or 0)*100) + ((b50 or 0)*50) + ((b20 or 0)*20) + ((b10 or 0)*10) + ((b5 or 0)*5) + \
                             ((m2 or 0)*2) + ((m1 or 0)*1) + ((m50c or 0)*0.50) + ((m20c or 0)*0.20) + ((m10c or 0)*0.10) + ((m5c or 0)*0.05) + \
                             ((m2c or 0)*0.02) + ((m1c or 0)*0.01)
                st.info(f"**Total Contado: {total_calc:.2f}€**")

            with st.form("form_cierre_final", border=True):
                st.markdown("<p style='margin: 0 0 5px 0; font-weight: bold;'>🔒 Confirmar Cierre</p>", unsafe_allow_html=True)
                
                c_f1, c_f2 = st.columns([1, 1])
                with c_f1: efectivo_final = st.number_input("Efectivo Final Real", min_value=0.0, value=None, placeholder=f"{total_calc:.2f}", label_visibility="collapsed")
                with c_f2: submit_cierre = st.form_submit_button("CERRAR CAJA DEFINITIVA", type="primary", use_container_width=True)
                    
                if submit_cierre:
                    ef_val = efectivo_final if efectivo_final is not None else total_calc
                    ingresos = sum(m['cantidad'] for m in res_movs.data if m['tipo'] == 'Ingreso') if res_movs.data else 0.0
                    retiradas = sum(m['cantidad'] for m in res_movs.data if m['tipo'] == 'Retirada') if res_movs.data else 0.0
                    
                    res_ventas = client.table("ventas_historial").select("pago_efectivo, pago_tarjeta, pago_bizum, estado, metodo_pago").gte("created_at", fecha_ap_str).execute()
                    t_efe = 0.0; t_tar = 0.0; t_biz = 0.0; t_tar_caixa = 0.0; t_tar_cajasiete = 0.0
                    
                    if res_ventas.data:
                        for v in res_ventas.data:
                            if v.get('estado') != 'DEVUELTO':
                                t_efe += float(v.get('pago_efectivo') or 0.0)
                                t_biz += float(v.get('pago_bizum') or 0.0)
                                val_tarjeta = float(v.get('pago_tarjeta') or 0.0)
                                t_tar += val_tarjeta
                                mp = v.get('metodo_pago', '')
                                if 'Caixa' in mp: t_tar_caixa += val_tarjeta
                                elif 'Caja Siete' in mp: t_tar_cajasiete += val_tarjeta
                                else: t_tar_caixa += val_tarjeta
                        
                    efectivo_teorico_en_caja = fondo_actual + t_efe + ingresos - retiradas
                    descuadre = ef_val - efectivo_teorico_en_caja
                    
                    resumen_json = {
                        "Efectivo": round(t_efe, 2), "Tarjeta": round(t_tar, 2), 
                        "Tarjeta Caixa": round(t_tar_caixa, 2), "Tarjeta Caja Siete": round(t_tar_cajasiete, 2),
                        "Bizum": round(t_biz, 2), "Ingresos": round(ingresos, 2), "Retiradas": round(retiradas, 2)
                    }
                    
                    client.table("control_caja").update({
                        "estado": "Cerrada", "total_contado": float(ef_val), "descuadre": float(descuadre), "resumen_pagos": resumen_json
                    }).eq("id", id_caja).execute()
                    
                    st.success(f"Caja Cerrada. Descuadre: {descuadre:.2f}€")
                    time.sleep(1.5); st.rerun()