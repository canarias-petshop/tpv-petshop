def calcular_desviacion_presupuesto(presupuesto_estimado, coste_real):
    """
    Calcula la desviación de un proyecto respecto al presupuesto.
    Retorna la desviación y un flag indicando si está en negativo (sobrecoste).
    """
    try:
        p_est = float(presupuesto_estimado)
        c_real = float(coste_real)
        desviacion = p_est - c_real
        es_sobrecoste = desviacion < 0
        return desviacion, es_sobrecoste
    except:
        return 0.0, False

def analizar_estado_proyecto(proyecto_data):
    """
    Analiza los datos de un proyecto y devuelve un resumen de salud.
    """
    if not proyecto_data:
        return None
        
    p_est = float(proyecto_data.get('presupuesto_estimado', 0.0))
    c_real = float(proyecto_data.get('coste_real', 0.0))
    desv, sobrecoste = calcular_desviacion_presupuesto(p_est, c_real)
    
    estado = proyecto_data.get('estado', 'Desconocido')
    
    return {
        "desviacion": desv,
        "en_peligro": sobrecoste and estado not in ["Cancelado", "Completado"],
        "estado_actual": estado
    }
