import datetime
from zoneinfo import ZoneInfo
import json
import re

def parsear_dias_reparto(texto):
    texto = texto.lower()
    if "demanda" in texto or "sin especificar" in texto:
        return []
        
    dias = []
    if "lunes a viernes" in texto:
        return [0, 1, 2, 3, 4]
        
    if "lunes" in texto: dias.append(0)
    if "martes" in texto: dias.append(1)
    if "miercoles" in texto or "miércoles" in texto: dias.append(2)
    if "jueves" in texto: dias.append(3)
    if "viernes" in texto: dias.append(4)
    if "sabado" in texto or "sábado" in texto: dias.append(5)
    if "domingo" in texto: dias.append(6)
    
    return dias

def calcular_alertas(proveedores):
    ahora = datetime.datetime.now(ZoneInfo("Atlantic/Canary"))
    # for testing:
    # ahora = datetime.datetime(2026, 7, 6, 12, 0, tzinfo=ZoneInfo("Atlantic/Canary")) # Monday
    
    alertas = []
    
    for p in proveedores:
        freq = p.get('frecuencia_reparto', '')
        dias_entrega = parsear_dias_reparto(freq)
        if not dias_entrega:
            continue
            
        hora_corte_str = p.get('hora_limite', '')
        # Extraer hora: "14h" -> 14, "20h" -> 20, "14:00" -> 14
        m = re.search(r'(\d{1,2})', hora_corte_str)
        hora = 12 # Default to noon if we can't parse
        if m:
            hora = int(m.group(1))
            
        # Determinar el PRÓXIMO día de corte. 
        # El día de corte es el *día laborable anterior* al día de entrega.
        # Laborables: Lunes(0) a Viernes(4). Si el reparto es el Lunes(0), el corte es el Viernes(4).
        
        # Encontramos la próxima fecha de corte buscando hacia atrás desde los días de entrega futuros.
        # Mejor estrategia: iteramos los próximos 7 días buscando si alguno es día de entrega.
        for i in range(1, 8): # Next 1 to 7 days
            dia_futuro = ahora + datetime.timedelta(days=i)
            if dia_futuro.weekday() in dias_entrega:
                # El reparto será el `dia_futuro`
                # El día de corte es el laborable anterior
                dia_corte = dia_futuro - datetime.timedelta(days=1)
                while dia_corte.weekday() > 4: # Si cae en Sábado(5) o Domingo(6), retroceder más
                    dia_corte -= datetime.timedelta(days=1)
                
                # Ahora tenemos la fecha límite (corte)
                corte_dt = dia_corte.replace(hour=hora, minute=0, second=0, microsecond=0)
                
                # Si el corte_dt ya pasó, entonces esta entrega no nos importa, pero espera...
                # Si el corte_dt ya pasó (ej. era hoy a las 10 y son las 11), nos interesa mostrarlo?
                # The user wants an alert to make the order.
                
                contacto = p.get('contacto', '')
                ultimo_manual_dt = None
                if contacto:
                    try:
                        data = json.loads(contacto)
                        if 'ultimo_manual' in data:
                            ultimo_manual_dt = datetime.datetime.fromisoformat(data['ultimo_manual'])
                            if ultimo_manual_dt.tzinfo is None:
                                ultimo_manual_dt = ultimo_manual_dt.replace(tzinfo=ZoneInfo("Atlantic/Canary"))
                    except:
                        pass
                
                # Si no se ha hecho pedido, o si se hizo un pedido *antes* del último corte?
                # Simplificamos: si estamos dentro de las 48 horas previas al corte, mostramos la alerta.
                tiempo_hasta_corte = (corte_dt - ahora).total_seconds() / 3600
                
                # Show alert if we are within 24 hours of the cutoff, OR if the cutoff passed recently (e.g. up to 12 hours ago) and we haven't ordered
                if -12 <= tiempo_hasta_corte <= 24:
                    # Check if we already ordered recently
                    if ultimo_manual_dt:
                        # Si se pidió hace menos de 48 horas, lo consideramos hecho
                        if (ahora - ultimo_manual_dt).total_seconds() / 3600 < 48:
                            break # We ordered already for this cycle
                            
                    alertas.append({
                        "id": p['id'],
                        "proveedor": p['nombre_empresa'],
                        "corte_dt": corte_dt,
                        "ultimo_manual": ultimo_manual_dt
                    })
                break # Only consider the VERY NEXT delivery
                
    return alertas

provs = [
    {'id': 1, 'nombre_empresa': 'Test Lunes', 'frecuencia_reparto': 'Lunes', 'hora_limite': '14h'},
    {'id': 2, 'nombre_empresa': 'Test Martes', 'frecuencia_reparto': 'Martes', 'hora_limite': '10h'},
    {'id': 3, 'nombre_empresa': 'Test Todos', 'frecuencia_reparto': 'lunes a viernes', 'hora_limite': '14h'},
]
print("Alertas:", calcular_alertas(provs))
