import pandas as pd
from datetime import datetime
from postgrest import SyncPostgrestClient
import re

def crear_cliente(client: SyncPostgrestClient, nombre_dueno: str, telefono: str, nombre_dueno_2: str = "",
                  telefono_2: str = "", email: str = "", metodo_contacto: str = "WhatsApp",
                  fecha_nacimiento: str = "", rgpd_consent: bool = True, direccion: str = "",
                  servicio_domicilio: bool = False):
    """Crea un nuevo cliente en la base de datos."""
    if not nombre_dueno:
        raise ValueError("El nombre del dueño es obligatorio.")
    
    res = client.table("clientes").insert({
        "nombre_dueno": nombre_dueno,
        "telefono": telefono,
        "nombre_dueno_2": nombre_dueno_2,
        "telefono_2": telefono_2,
        "email": email,
        "metodo_contacto": metodo_contacto,
        "fecha_nacimiento": fecha_nacimiento,
        "rgpd_consent": rgpd_consent,
        "puntos": 0,
        "direccion": direccion,
        "servicio_domicilio": servicio_domicilio
    }).execute()
    return res.data[0] if res.data else None

def crear_mascota(client: SyncPostgrestClient, cliente_id: str, nombre: str, especie: str = "",
                  sexo: str = "", raza: str = "", peso: str = "", observaciones: str = "",
                  fecha_nacimiento: str = ""):
    """Crea una nueva mascota asociada a un cliente."""
    if not nombre:
        raise ValueError("El nombre de la mascota es obligatorio.")
    if not cliente_id:
        raise ValueError("El ID del cliente es obligatorio.")
        
    res = client.table("mascotas").insert({
        "cliente_id": cliente_id,
        "nombre": nombre,
        "especie": especie,
        "sexo": sexo,
        "raza": raza,
        "peso": peso,
        "observaciones": observaciones,
        "fecha_nacimiento": fecha_nacimiento
    }).execute()
    return res.data[0] if res.data else None

def actualizar_cliente(client: SyncPostgrestClient, cliente_id: str, datos_update: dict):
    """Actualiza los datos de un cliente."""
    if not cliente_id:
        raise ValueError("ID de cliente inválido.")
    res = client.table("clientes").update(datos_update).eq("id", cliente_id).execute()
    return res.data[0] if res.data else None

def anonimizar_cliente(client: SyncPostgrestClient, cliente_id: str):
    """Anonimiza los datos de un cliente por la LOPD manteniendo el histórico de ventas."""
    if not cliente_id:
        raise ValueError("ID de cliente inválido.")
    res = client.table("clientes").update({
        "nombre_dueno": "Cliente Borrado",
        "telefono": "",
        "email": "",
        "rgpd_consent": False
    }).eq("id", cliente_id).execute()
    return res.data[0] if res.data else None

def crear_encargo(client: SyncPostgrestClient, nombre_cliente: str, telefono: str, producto: str, cantidad: int, observaciones: str = ""):
    """Registra un nuevo encargo pendiente."""
    if not nombre_cliente or not producto:
        raise ValueError("Nombre de cliente y producto son obligatorios.")
        
    res = client.table("encargos_clientes").insert({
        "nombre_cliente": nombre_cliente,
        "telefono": telefono,
        "detalle_pedido": f"{cantidad}x {producto}",
        "notas": observaciones,
        "estado": "Pendiente",
        "origen": "Tienda"
    }).execute()
    return res.data[0] if res.data else None

def registrar_recogida_desde_cita(
    client: SyncPostgrestClient,
    mascota_id: str,
    fecha_str: str,
    hora_str: str,
    direccion: str = "",
    observaciones: str = "",
    servicio_nombre: str = "Peluquería",
    origen: str = "agenda",
):
    """
    Crea el servicio de recogida y actualiza la ficha del cliente
    (dirección + servicio_domicilio=True) a partir de una cita.
    Devuelve dict con datos usados / errores.
    """
    if not mascota_id:
        raise ValueError("Falta el ID de la mascota para registrar la recogida.")

    res_m = client.table("mascotas").select("id, nombre, cliente_id").eq("id", mascota_id).execute()
    if not res_m.data:
        raise ValueError("No se encontró la mascota al crear la recogida.")
    mascota = res_m.data[0]
    cliente_id = mascota.get("cliente_id")
    if not cliente_id:
        raise ValueError("La mascota no tiene cliente asociado.")

    res_c = client.table("clientes").select("id, nombre_dueno, telefono, direccion, servicio_domicilio").eq("id", cliente_id).execute()
    if not res_c.data:
        raise ValueError("No se encontró el cliente al crear la recogida.")
    cliente = res_c.data[0]

    try:
        fecha_obj = pd.to_datetime(fecha_str)
        fecha_reco_txt = f"{fecha_obj.strftime('%d/%m/%Y')} a las {hora_str}"
    except Exception:
        fecha_reco_txt = f"{fecha_str} a las {hora_str}"

    dir_final = str(direccion or "").strip() or str(cliente.get("direccion") or "").strip()
    obs = str(observaciones or "").strip()
    if obs:
        obs = f"Cita {origen}: {obs}"
    else:
        obs = f"Generado desde cita {origen} ({servicio_nombre})"

    res_ins = client.table("servicios_recogida").insert({
        "cliente": cliente.get("nombre_dueno") or "Cliente",
        "mascota": mascota.get("nombre") or "Mascota",
        "telefono": cliente.get("telefono") or "",
        "direccion": dir_final,
        "fecha_recogida": fecha_reco_txt,
        "observaciones": obs,
        "estado": "Pendiente",
    }).execute()

    upd_cli = {"servicio_domicilio": True}
    if dir_final:
        upd_cli["direccion"] = dir_final
    client.table("clientes").update(upd_cli).eq("id", cliente_id).execute()

    return {
        "recogida": (res_ins.data or [None])[0],
        "cliente_id": cliente_id,
        "direccion": dir_final,
    }

def agendar_cita(client: SyncPostgrestClient, mascotas_id: str, fecha_str: str, hora_str: str, 
                 servicio: str, duracion_minutos: int, peluquero: str = "", forzado: bool = False,
                 motivo_forzado: str = "", fianza_pagada: bool = False, recogida: bool = False,
                 direccion_recogida: str = "", observaciones: str = "",
                 cliente_id: str = None, nombre_cliente: str = "", telefono: str = "",
                 nombre_mascota: str = ""):
    """Agenda una cita para una mascota. Si recogida=True, crea servicio de recogida y actualiza la ficha del cliente."""
    if not mascotas_id or not fecha_str or not hora_str:
        raise ValueError("Faltan datos obligatorios para la cita.")
        
    servicio_final = f"{servicio} ({peluquero})" if peluquero else servicio
    if forzado and motivo_forzado:
        servicio_final += f" [Forzado: {motivo_forzado}]"
    
    estado_cita = "Servicio de recogida pendiente" if recogida else "Pendiente"
    if fianza_pagada:
        servicio_final = f"[ESTADO: {estado_cita}] [💰 FIANZA PAGADA] {servicio_final}"
    else:
        servicio_final = f"[ESTADO: {estado_cita}] {servicio_final}"
        
    res = client.table("citas").insert({
        "mascotas_id": mascotas_id,
        "fecha_hora": f"{fecha_str} {hora_str}",
        "servicio": servicio_final,
        "duracion_minutos": int(duracion_minutos),
        "observaciones": str(observaciones or "")
    }).execute()

    if recogida:
        registrar_recogida_desde_cita(
            client=client,
            mascota_id=mascotas_id,
            fecha_str=fecha_str,
            hora_str=hora_str,
            direccion=direccion_recogida,
            observaciones=observaciones,
            servicio_nombre=servicio,
            origen="CRM",
        )

    return res.data[0] if res.data else None
