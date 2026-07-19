import pandas as pd
import re

def calcular_huecos_libres(fecha_c, citas_dia, bloqueos_parciales, empleados_a_revisar, empleados_lista, turnos_dict, duracion_c):
    """
    Calcula los huecos libres para una fecha dada, considerando bloqueos, citas existentes y turnos de los empleados.
    Soluciona el bug de ofrecer huecos a empleados ausentes o de baja.
    """
    huecos_obj = []
    citas_virtuales = citas_dia.copy()
    
    # Inyectar bloqueos parciales como citas falsas
    for b in bloqueos_parciales:
        emp_af = b.get('empleado_afectado', '')
        try:
            dt_ini = pd.to_datetime(f"{fecha_c} {b.get('hora_inicio')}")
            dt_fin = pd.to_datetime(f"{fecha_c} {b.get('hora_fin')}")
            duracion_mins = int((dt_fin - dt_ini).total_seconds() / 60)
            
            if emp_af == 'Todas':
                for e in empleados_lista:
                    citas_virtuales.append({'fecha_hora': dt_ini, 'duracion_minutos': duracion_mins, 'servicio': f"BLOQUEO ({e})"})
            else:
                citas_virtuales.append({'fecha_hora': dt_ini, 'duracion_minutos': duracion_mins, 'servicio': f"BLOQUEO ({emp_af})"})
        except Exception:
            pass

    for emp_nombre in empleados_a_revisar:
        turno_str = turnos_dict.get(emp_nombre, "")
        
        # FIX: Evitar que asigne citas a personas ausentes o de baja
        t_lower = str(turno_str).lower()
        if not t_lower or "libre" in t_lower or "vacaciones" in t_lower or "ausencia" in t_lower or "baja" in t_lower:
            continue
            
        times = re.findall(r'(\d{1,2}:\d{2})', turno_str)
        if len(times) >= 2:
            h_ini = pd.to_datetime(f"{fecha_c} {times[0]}")
            h_fin = pd.to_datetime(f"{fecha_c} {times[1]}")
        else:
            if fecha_c.weekday() < 5: # Lunes a Viernes
                h_ini = pd.to_datetime(f"{fecha_c} 09:00")
                h_fin = pd.to_datetime(f"{fecha_c} 21:00")
            else: # Sábados y Domingos
                h_ini = pd.to_datetime(f"{fecha_c} 10:00")
                h_fin = pd.to_datetime(f"{fecha_c} 14:00")
            
        for h in range(0, 24):
            for m in range(0, 60, 5):
                dt_ini = pd.to_datetime(f"{fecha_c} {h:02d}:{m:02d}")
                if dt_ini < h_ini: continue
                dt_fin = dt_ini + pd.Timedelta(minutes=duracion_c)
                if dt_fin > h_fin: continue
                
                solapa = False
                for c in citas_virtuales:
                    s_name = c.get('servicio', '')
                    if "[ESTADO: Cancelada]" in s_name or "[ESTADO: Anulada]" in s_name or "[ESTADO: Cambio" in s_name or "[ESTADO: No presentado]" in s_name: 
                        continue
                    
                    c_ini = pd.to_datetime(c['fecha_hora'])
                    if c_ini.tzinfo: c_ini = c_ini.tz_localize(None)
                    c_fin = c_ini + pd.Timedelta(minutes=c.get('duracion_minutos') or 60)
                    
                    if dt_ini < c_fin and dt_fin > c_ini:
                        assigned_e = None
                        for e in empleados_lista:
                            if f"({e})" in s_name: 
                                assigned_e = e
                                break
                        if assigned_e == emp_nombre or assigned_e is None:
                            solapa = True
                            break
                if not solapa:
                    huecos_obj.append({"dt": dt_ini, "hora": f"{h:02d}:{m:02d}", "emp": emp_nombre})
    
    huecos_obj.sort(key=lambda x: x["dt"])
    huecos_formateados = [f"{x['hora']} (Con {x['emp']})" for x in huecos_obj]
    huecos_formateados.append("Asignación Manual")
    
    return huecos_obj, huecos_formateados, citas_virtuales

def verificar_solape_manual(dt_ini_man, duracion_c, citas_virtuales, empleados_lista, turnos_dict, emp_deseado):
    """
    Comprueba si una hora manual se solapa con otras citas o con los horarios de los empleados.
    """
    dt_fin_man = dt_ini_man + pd.Timedelta(minutes=duracion_c)
    
    # 1. Verificar solape con citas existentes o bloqueos
    for c in citas_virtuales:
        s_name = c.get('servicio', '')
        if "[ESTADO: Cancelada]" in s_name or "[ESTADO: Anulada]" in s_name or "[ESTADO: Cambio" in s_name or "[ESTADO: No presentado]" in s_name: 
            continue
        c_ini = pd.to_datetime(c['fecha_hora'])
        if c_ini.tzinfo: c_ini = c_ini.tz_localize(None)
        c_fin = c_ini + pd.Timedelta(minutes=c.get('duracion_minutos') or 60)
        
        if dt_ini_man < c_fin and dt_fin_man > c_ini:
            assigned_e = None
            for e in empleados_lista:
                if f"({e})" in s_name: 
                    assigned_e = e
                    break
            
            if emp_deseado != "Cualquiera":
                if assigned_e == emp_deseado or assigned_e is None:
                    return True, f"Solapa con {s_name} ({c_ini.strftime('%H:%M')} a {c_fin.strftime('%H:%M')})"
            else:
                return True, f"Solapa con {s_name} ({c_ini.strftime('%H:%M')} a {c_fin.strftime('%H:%M')})"
                
    # 2. Verificar que el empleado (si hay uno elegido explícitamente) está trabajando
    if emp_deseado != "Cualquiera":
        turno_str = turnos_dict.get(emp_deseado, "")
        t_lower = str(turno_str).lower()
        if not t_lower or "libre" in t_lower or "vacaciones" in t_lower or "ausencia" in t_lower or "baja" in t_lower:
            return True, f"{emp_deseado} está marcado como ausente o no tiene turno hoy."
            
        times = re.findall(r'(\d{1,2}:\d{2})', turno_str)
        if len(times) >= 2:
            h_ini = pd.to_datetime(f"{dt_ini_man.date()} {times[0]}")
            h_fin = pd.to_datetime(f"{dt_ini_man.date()} {times[1]}")
            if dt_ini_man < h_ini or dt_fin_man > h_fin:
                return True, f"{emp_deseado} trabaja de {times[0]} a {times[1]}. El servicio está fuera de su horario."
                
    return False, ""
