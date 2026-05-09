import pandas as pd
import toml
from postgrest import SyncPostgrestClient
import os
import re

def init_supabase():
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    with open(secrets_path, "r") as f: secrets = toml.load(f)
    raw_url = secrets.get('url', '').strip().strip('"').strip("'").rstrip('/')
    api_url = raw_url if raw_url.endswith('/rest/v1') else f"{raw_url}/rest/v1"
    api_key = secrets.get('key', '').strip().strip('"').strip("'")
    return SyncPostgrestClient(api_url, headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"})

client = init_supabase()
print("📡 Iniciando Radar de Fichas Rebeldes...\n")

CARPETA_EXCEL = "fichas_a_importar"

# 1. Cargar lo que ya tenemos a salvo para no duplicar
res_cli = client.table("clientes").select("id, nombre_dueno, telefono").execute()
res_masc = client.table("mascotas").select("id, nombre, cliente_id").execute()

mascotas_existentes = {str(m.get('nombre', '')).strip().lower() for m in res_masc.data} if res_masc.data else set()

archivos = [f for f in os.listdir(CARPETA_EXCEL) if f.endswith(('.xlsx', '.xls')) and not f.startswith('~')]

insertados = 0

for archivo in archivos:
    if "EN BLANCO" in archivo.upper() or "PLANTILLA" in archivo.upper():
        continue

    # Limpiar extensión
    clean_name = re.sub(r'\.xlsx?$', '', archivo)
    
    # Extraer teléfono del título del archivo (busca números largos)
    tel_match = re.search(r'\+?\d{9,14}', clean_name)
    telefono_archivo = tel_match.group(0) if tel_match else ""
    
    # Extraer nombre de la mascota del título (lo que hay antes del guion o del teléfono)
    mascota_archivo = re.sub(r'\+?\d{9,14}', '', clean_name).split('-')[0].strip()
    
    # Filtro de seguridad
    if not mascota_archivo or len(mascota_archivo) < 2:
        continue

    # ¿Está ya esta mascota en la base de datos?
    if mascota_archivo.lower() in mascotas_existentes:
        continue # Ya está a salvo en el programa

    # ¡LA MASCOTA FALTA! Vamos a rescatarla
    print(f"🚨 Ficha faltante detectada: {archivo}")
    
    dueño = ""
    # Intentamos buscar el dueño por dentro del Excel "a lo bruto"
    try:
        ruta = os.path.join(CARPETA_EXCEL, archivo)
        df = pd.read_excel(ruta, header=None).fillna("")
        for f in range(min(20, len(df))):
            for c in range(min(10, len(df.columns) - 1)):
                celda = str(df.iloc[f, c]).lower().strip()
                if "dueño" in celda or "propietario" in celda or "nombre" in celda:
                    val = str(df.iloc[f, c + 1]).strip()
                    if val and len(val) > 2 and val.lower() != "nan":
                        dueño = val; break
            if dueño: break
    except: pass
        
    if not dueño:
        dueño = f"Familia de {mascota_archivo}"
        
    # Buscar si ese teléfono ya es de un cliente nuestro para meterle el perro en su ficha
    cliente_id = None
    if res_cli.data:
        for c in res_cli.data:
            if telefono_archivo and telefono_archivo == str(c.get('telefono', '')).strip():
                cliente_id = c['id']
                dueño = c['nombre_dueno'] # Respetamos el nombre que ya tuviera puesto
                break
            
    # Si es una familia totalmente nueva, la creamos
    if not cliente_id:
        res_ins_c = client.table("clientes").insert({
            "nombre_dueno": dueño, "telefono": telefono_archivo, "puntos": 0, "rgpd_consent": True
        }).execute()
        if res_ins_c.data:
            cliente_id = res_ins_c.data[0]['id']
            
    # Insertar el perro
    if cliente_id:
        client.table("mascotas").insert({
            "cliente_id": cliente_id, "nombre": mascota_archivo, "especie": "Perro"
        }).execute()
        mascotas_existentes.add(mascota_archivo.lower())
        insertados += 1
        print(f"  ✅ Rescatado: {mascota_archivo} (Dueño asignado: {dueño})")

print(f"\n🎉 ¡Operación de rastreo finalizada! Se han salvado e introducido a la fuerza {insertados} fichas que faltaban.")