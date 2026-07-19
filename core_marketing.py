import pandas as pd
from datetime import date

def calcular_progreso_objetivo(valor_actual, meta_cuantitativa):
    """
    Calcula el porcentaje de progreso de un objetivo de marketing.
    Retorna un valor entre 0.0 y 1.0
    """
    try:
        val = float(valor_actual)
        meta = float(meta_cuantitativa)
        if meta <= 0:
            return 0.0
        progreso = val / meta
        return min(max(progreso, 0.0), 1.0)
    except:
        return 0.0

def verificar_alertas_plan_marketing(ultima_fecha_str):
    """
    Verifica si el plan de marketing está a punto de caducar (menos de 45 días)
    Retorna un diccionario con 'nivel' (error/warning/info) y 'mensaje'.
    """
    if not ultima_fecha_str:
        return None
        
    try:
        ultima_fecha = pd.to_datetime(ultima_fecha_str).date()
        dias_restantes = (ultima_fecha - date.today()).days
        
        if 0 <= dias_restantes <= 30:
            return {
                "nivel": "error",
                "mensaje": f"🚨 **¡ALERTA DE CONTENIDO!** Tu plan de marketing programado se agota el **{ultima_fecha.strftime('%d/%m/%Y')}** (en {dias_restantes} días). ¡Pídele a tu asistente que te redacte y prepare la campaña de la siguiente temporada!"
            }
        elif 30 < dias_restantes <= 45:
            return {
                "nivel": "warning",
                "mensaje": f"⚠️ **Aviso de Temporada:** Tu plan de marketing actual abarca hasta el **{ultima_fecha.strftime('%d/%m/%Y')}**. Recuerda solicitar la redacción de la próxima tanda de publicaciones pronto para no quedarte sin contenido."
            }
        return None
    except:
        return None
