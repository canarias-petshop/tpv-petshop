import pandas as pd

def calcular_balance_financiero(df_ventas, df_compras, gastos_recurrentes_data, factor_fijos):
    """
    Calcula el balance financiero incluyendo ventas, gastos variables y fijos proporcionados.
    Retorna un diccionario con los KPIs y totales calculados.
    """
    # 1. Ventas
    df_v = df_ventas.copy()
    if not df_v.empty and 'estado' in df_v.columns:
        df_v = df_v[df_v['estado'] != 'DEVUELTO']
        
    total_ventas = 0.0
    num_operaciones = 0
    ticket_medio = 0.0
    
    if not df_v.empty:
        total_ventas = float(df_v['total'].sum()) if 'total' in df_v.columns else 0.0
        num_operaciones = len(df_v)
        ticket_medio = total_ventas / num_operaciones if num_operaciones > 0 else 0.0
        
    # 2. Compras
    df_c = df_compras.copy()
    total_compras = 0.0
    if not df_c.empty and 'total' in df_c.columns:
        df_c['total'] = pd.to_numeric(df_c['total'], errors='coerce').fillna(0.0)
        total_compras = float(df_c['total'].sum())
        
    # 3. Fijos
    total_fijos_mes = 0.0
    if gastos_recurrentes_data:
        for gf in gastos_recurrentes_data:
            imp_raw = gf.get('importe_estimado', 0.0)
            imp = float(imp_raw) if imp_raw is not None else 0.0
            frec = gf.get('frecuencia', 'Mensual')
            if frec == 'Bimestral': imp = imp / 2
            elif frec == 'Trimestral': imp = imp / 3
            elif frec == 'Anual': imp = imp / 12
            total_fijos_mes += imp
            
    total_fijos_periodo = total_fijos_mes * factor_fijos
    
    # Global
    gastos_totales = total_compras + total_fijos_periodo
    balance_neto = total_ventas - gastos_totales
    
    return {
        "total_ventas": total_ventas,
        "num_operaciones": num_operaciones,
        "ticket_medio": ticket_medio,
        "total_compras": total_compras,
        "total_fijos_mes": total_fijos_mes,
        "total_fijos_periodo": total_fijos_periodo,
        "gastos_totales": gastos_totales,
        "balance_neto": balance_neto,
        "df_v_filtrado": df_v
    }

def calcular_roi_laboral(citas_data, empleados_lista):
    """
    Cruza la agenda con el historial clínico para calcular los ingresos generados por empleado.
    """
    rendimiento_empleados = {emp: {"Ingresos": 0.0, "Citas": 0} for emp in empleados_lista}
    
    if not citas_data:
        return rendimiento_empleados
        
    for c in citas_data:
        servicio_raw = c.get('servicio', '')
        if "[ESTADO: Cancelada]" in servicio_raw or "[ESTADO: Anulada]" in servicio_raw or "[ESTADO: No presentado]" in servicio_raw or "[ESTADO: Cambio" in servicio_raw: 
            continue
    
        # Buscar empleado
        emp_cita = None
        for e in empleados_lista:
            if f"({e})" in servicio_raw:
                emp_cita = e
                break
    
        if not emp_cita: 
            continue
            
        rendimiento_empleados[emp_cita]["Citas"] += 1
        
        try:
            dt_c_raw = pd.to_datetime(c['fecha_hora'])
            dt_c = dt_c_raw.date()
        
            masc = c.get('mascotas')
            if not isinstance(masc, dict): 
                continue
        
            hist = masc.get('historial_trabajos')
            if isinstance(hist, list):
                for t in hist:
                    try:
                        f_str = str(t.get('Fecha', ''))
                        if f_str:
                            dt_t = pd.to_datetime(f_str, format="%d/%m/%Y").date()
                            if dt_t == dt_c:
                                imp_base = float(t.get('Precio con desc. (€)') or t.get('Precio Base (€)') or t.get('Importe (€)') or 0.0)
                                imp_extras = float(t.get('Extras (€)') or 0.0)
                                total_sesion = imp_base + imp_extras
                                rendimiento_empleados[emp_cita]["Ingresos"] += total_sesion
                    except:
                        pass
        except:
            pass
            
    return rendimiento_empleados
