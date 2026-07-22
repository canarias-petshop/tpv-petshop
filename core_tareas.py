import pandas as pd

def generar_proyeccion_virtual(todas_tareas, fecha_inicio, fecha_fin):
    """
    Toma un conjunto de tareas (maestras) y proyecta sus ocurrencias futuras
    basándose en la periodicidad, dentro del rango de fechas dado.
    """
    if not todas_tareas: 
        return []
        
    df = pd.DataFrame(todas_tareas)
    if 'fecha_programada' not in df.columns:
        return []
        
    df['fecha_programada'] = pd.to_datetime(df['fecha_programada'])
    
    # Agrupamos por título y periodicidad, cogiendo el primer registro como "maestro"
    maestros = df.loc[df.groupby(['titulo', 'periodicidad'])['fecha_programada'].idxmin()].copy()
    
    df['fecha_str'] = df['fecha_programada'].dt.strftime('%Y-%m-%d')
    reales_dict = {}
    for _, r in df.iterrows():
        key = (str(r['titulo']).strip(), str(r['periodicidad']).strip(), str(r['fecha_str']).strip())
        reales_dict[key] = r.to_dict()
        
    proyectadas = []
    start_dt = pd.to_datetime(fecha_inicio)
    end_dt = pd.to_datetime(fecha_fin)
    
    for _, m in maestros.iterrows():
        tit = str(m.get('titulo', '')).strip()
        per = str(m.get('periodicidad', '')).strip()
        f_base = m['fecha_programada']
        notas = m.get('notas', '')
        
        if per in ["Puntual", "Por horas", "nan", "None", ""]:
            continue
            
        curr = f_base
        limite_seguridad = 0
        while curr <= end_dt and limite_seguridad < 2000:
            limite_seguridad += 1
            curr_str = curr.strftime('%Y-%m-%d')
            if curr >= start_dt:
                key = (tit, per, curr_str)
                if key in reales_dict:
                    rd = reales_dict[key].copy()
                    rd['es_virtual'] = False
                    proyectadas.append(rd)
                else:
                    proyectadas.append({
                        "id": f"v_{tit}_{curr_str}",
                        "titulo": tit,
                        "fecha_programada": curr_str,
                        "periodicidad": per,
                        "estado": "Pendiente ⏳",
                        "notas": notas,
                        "es_virtual": True
                    })
                    
            if per == "Diario": curr += pd.DateOffset(days=1)
            elif per == "Semanal": curr += pd.DateOffset(weeks=1)
            elif per == "Mensual": curr += pd.DateOffset(months=1)
            elif per == "Anual": curr += pd.DateOffset(years=1)
            else: break
            
    # Añadir las tareas puntuales que caen en el rango
    for _, r in df.iterrows():
        per = str(r.get('periodicidad', '')).strip()
        if per in ["Puntual", "Por horas", "nan", "None", ""]:
            if start_dt <= r['fecha_programada'] <= end_dt:
                rd = r.to_dict()
                rd['es_virtual'] = False
                proyectadas.append(rd)
                
    return proyectadas
