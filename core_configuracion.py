from datetime import datetime

def get_configuracion_negocio_default():
    """
    Retorna la configuración por defecto del negocio en caso de fallo en BD.
    """
    return {
        'nombre_tienda': 'Animalarium',
        'envio_gratis_a_partir_de': 110.00,
        'coste_envio_cercania': 5.00,
        'coste_envio_lejos': 10.00,
        'euros_para_un_punto': 10.00,
        'valor_punto_euros': 0.50,
        'limite_descuento_puntos_porcentaje': 50.00,
        'descuento_primera_compra_web_porcentaje': 10.00,
        'descuento_cajas_completas_porcentaje': 7.00,
        'descuento_retorno_tienda_porcentaje': 10.00,
        'dias_maximos_retorno_tienda': 60
    }

def construir_payload_configuracion(raw_data, current_time_iso=None):
    """
    Valida y construye el payload para actualizar la configuración.
    Asegura tipos correctos y límites lógicos.
    """
    try:
        envio_g = float(raw_data.get('envio_gratis_a_partir_de', 0))
        lim_pts = float(raw_data.get('limite_descuento_puntos_porcentaje', 50.0))
        lim_pts = min(max(lim_pts, 1.0), 100.0) # Entre 1 y 100%
        
        eur_punto = float(raw_data.get('euros_para_un_punto', 10.0))
        if eur_punto <= 0: eur_punto = 10.0
        
        return {
            "nombre_tienda": str(raw_data.get('nombre_tienda', 'Tienda')).strip(),
            "envio_gratis_a_partir_de": max(envio_g, 0.0),
            "coste_envio_cercania": max(float(raw_data.get('coste_envio_cercania', 0)), 0.0),
            "coste_envio_lejos": max(float(raw_data.get('coste_envio_lejos', 0)), 0.0),
            "descuento_primera_compra_web_porcentaje": min(max(float(raw_data.get('descuento_primera_compra_web_porcentaje', 0)), 0.0), 100.0),
            "descuento_cajas_completas_porcentaje": min(max(float(raw_data.get('descuento_cajas_completas_porcentaje', 0)), 0.0), 100.0),
            "euros_para_un_punto": eur_punto,
            "valor_punto_euros": max(float(raw_data.get('valor_punto_euros', 0.5)), 0.01),
            "limite_descuento_puntos_porcentaje": lim_pts,
            "descuento_retorno_tienda_porcentaje": min(max(float(raw_data.get('descuento_retorno_tienda_porcentaje', 0)), 0.0), 100.0),
            "dias_maximos_retorno_tienda": max(int(raw_data.get('dias_maximos_retorno_tienda', 60)), 1),
            "actualizado_en": current_time_iso if current_time_iso else datetime.now().isoformat()
        }
    except Exception:
        return None
