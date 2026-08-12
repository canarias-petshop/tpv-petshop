from datetime import timedelta


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


def construir_bloqueos_rango(
    fecha_ini,
    fecha_fin,
    hora_inicio: str,
    hora_fin: str,
    titulo: str,
    empleado_afectado: str,
    bloquea_agenda: bool = True,
):
    """
    Genera filas para agenda_bloqueos, un día por cada fecha del rango inclusivo.
    Raises ValueError si el rango es inválido o faltan datos.
    """
    if not titulo or not hora_inicio or not hora_fin:
        raise ValueError("Título y horas son obligatorios.")
    if fecha_fin < fecha_ini:
        raise ValueError("La fecha de fin no puede ser anterior a la de inicio.")

    filas = []
    delta = fecha_fin - fecha_ini
    for i in range(delta.days + 1):
        dia = fecha_ini + timedelta(days=i)
        filas.append({
            "fecha": str(dia),
            "hora_inicio": hora_inicio,
            "hora_fin": hora_fin,
            "titulo": titulo,
            "empleado_afectado": empleado_afectado,
            "bloquea_agenda": bloquea_agenda,
        })
    return filas
