import pandas as pd

def aplicar_descuentos_fidelidad(df_save, fechas_oferta):
    """
    Recorre el historial médico y aplica un descuento del 10% si:
    1. La fecha de la visita coincide con una fecha de oferta.
    2. La visita anterior (a la actual) ocurrió hace menos de 60 días.
    Retorna el DataFrame modificado y una lista de mensajes de éxito.
    """
    mensajes_exito = []
    
    for idx, row in df_save.iterrows():
        srv = str(row.get('Trabajo / Servicio')).strip()
        precio_base = row.get('Precio Base (€)')
        precio_desc = row.get('Precio con desc. (€)')
        
        # Validar precio base
        if pd.isna(precio_base) or str(precio_base).strip() == "":
            continue
            
        try:
            precio_base = float(precio_base)
        except ValueError:
            continue
            
        if srv and srv not in ["Otro", "None", "nan"]:
            fecha_actual_str = row.get('Fecha')
            try:
                if fecha_actual_str and str(fecha_actual_str).strip() != "" and str(fecha_actual_str).strip() != "nan":
                    fecha_actual_dt = pd.to_datetime(fecha_actual_str, format='%d/%m/%Y')
                    
                    aplica_desc = False
                    motivo_desc = ""
                    
                    if fecha_actual_str in fechas_oferta:
                        aplica_desc = True
                        motivo_desc = "Oferta en agenda"
                    else:
                        prev_dates = []
                        for i, r in df_save.iterrows():
                            if i != idx and str(r.get('Trabajo / Servicio')).strip() not in ["", "Otro", "None", "nan"]:
                                f_str = str(r.get('Fecha')).strip()
                                if f_str and f_str != "nan":
                                    fd = pd.to_datetime(f_str, format='%d/%m/%Y')
                                    if fd < fecha_actual_dt:
                                        prev_dates.append(fd)
                        
                        if prev_dates:
                            last_visit = max(prev_dates)
                            days_diff = (fecha_actual_dt - last_visit).days
                            if 0 < days_diff <= 60:
                                aplica_desc = True
                                motivo_desc = "Visita < 2 meses"
                                
                    if aplica_desc:
                        precio_calc = round(precio_base * 0.90, 2)
                        
                        # Aplicar descuento si el usuario no ha puesto un precio final manual
                        if pd.isna(precio_desc) or str(precio_desc).strip() == "" or float(precio_desc) == 0.0:
                            df_save.at[idx, 'Precio con desc. (€)'] = precio_calc
                            ahorro = round(precio_base - precio_calc, 2)
                            
                            nota_act = str(df_save.at[idx, 'Nota Sesión']).strip()
                            if nota_act == "None" or nota_act == "nan": nota_act = ""
                            nota_desc = f"[Desc. 10% ({motivo_desc}) aplicado. Ahorro: {ahorro}€]"
                            if nota_desc not in nota_act:
                                df_save.at[idx, 'Nota Sesión'] = f"{nota_act} {nota_desc}".strip()
                                mensajes_exito.append(f"🎉 ¡Descuento del 10% ({motivo_desc}) aplicado automáticamente a la sesión del {fecha_actual_str}! Ahorro: {ahorro}€")
            except Exception:
                pass
                
        # Asegurar que el Precio Final se rellene con el Base si no hay descuento
        precio_desc_check = df_save.at[idx, 'Precio con desc. (€)']
        if pd.isna(precio_desc_check) or str(precio_desc_check).strip() == "" or float(precio_desc_check) == 0.0:
            p_b = df_save.at[idx, 'Precio Base (€)']
            if pd.notna(p_b) and str(p_b).strip() != "":
                df_save.at[idx, 'Precio con desc. (€)'] = float(p_b)
                
    return df_save, mensajes_exito
