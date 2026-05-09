import pandas as pd
import toml
from postgrest import SyncPostgrestClient
import os
from datetime import datetime

def init_supabase():
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    with open(secrets_path, "r") as f: secrets = toml.load(f)
    raw_url = secrets.get('url', '').strip().strip('"').strip("'").rstrip('/')
    api_url = raw_url if raw_url.endswith('/rest/v1') else f"{raw_url}/rest/v1"
    api_key = secrets.get('key', '').strip().strip('"').strip("'")
    return SyncPostgrestClient(api_url, headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"})

client = init_supabase()
print("📥 Descargando copia de seguridad de la base de datos...")

# Descargar clientes con sus mascotas asociadas
res_clientes = client.table("clientes").select("nombre_dueno, telefono, email, puntos, mascotas(nombre, especie, raza, fecha_nacimiento, observaciones)").execute()

if res_clientes.data:
    filas = []
    for c in res_clientes.data:
        mascotas = c.get('mascotas', [])
        if not mascotas:
            filas.append({
                "Dueño": c.get('nombre_dueno', ''), "Teléfono": c.get('telefono', ''),
                "Email": c.get('email', ''), "Puntos VIP": c.get('puntos', 0),
                "Mascota": "", "Especie": "", "Raza": "", "Nacimiento Mascota": "", "Observaciones": ""
            })
        else:
            for m in mascotas:
                filas.append({
                    "Dueño": c.get('nombre_dueno', ''), "Teléfono": c.get('telefono', ''),
                    "Email": c.get('email', ''), "Puntos VIP": c.get('puntos', 0),
                    "Mascota": m.get('nombre', ''), "Especie": m.get('especie', ''),
                    "Raza": m.get('raza', ''), "Nacimiento Mascota": m.get('fecha_nacimiento', ''),
                    "Observaciones": m.get('observaciones', '')
                })
    
    df = pd.DataFrame(filas)
    df.to_excel("Copia_Seguridad_Clientes.xlsx", index=False)
    print(f"✅ ¡Éxito! Se ha guardado el archivo 'Copia_Seguridad_Clientes.xlsx' en tu carpeta con {len(df)} registros.")