import toml
from postgrest import SyncPostgrestClient
import os

def init_supabase():
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    with open(secrets_path, "r") as f: secrets = toml.load(f)
    raw_url = secrets.get('url', '').strip().strip('"').strip("'").rstrip('/')
    api_url = raw_url if raw_url.endswith('/rest/v1') else f"{raw_url}/rest/v1"
    api_key = secrets.get('key', '').strip().strip('"').strip("'")
    return SyncPostgrestClient(api_url, headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"})

client = init_supabase()

print("🚑 Iniciando Rescate de Clientes 'Solo Tienda' y sus Puntos...")

# 1. Obtener todos los clientes actuales para saber quién falta
res_cli = client.table("clientes").select("nombre_dueno").execute()
clientes_actuales = {c['nombre_dueno'].lower().strip() for c in res_cli.data} if res_cli.data else set()

# 2. Leer todo el historial de ventas (¡Los tickets nunca se borran!)
res_ventas = client.table("ventas_historial").select("cliente_vip_nombre, puntos_ganados, puntos_usados").execute()

if not res_ventas.data:
    print("No hay historial de ventas. Nada que rescatar.")
    exit()

# 3. Analizar quién falta y contar sus puntos exactos desde el principio de los tiempos
clientes_rescatados = {}

for v in res_ventas.data:
    nombre = v.get('cliente_vip_nombre')
    if not nombre or str(nombre).strip() == "" or str(nombre).lower() == "nan" or str(nombre).lower() == "none":
        continue
        
    nombre_clean = str(nombre).strip()
    nombre_lower = nombre_clean.lower()
    
    # Si el cliente que está en el ticket NO está en la base de datos actual de clientes
    if nombre_lower not in clientes_actuales:
        if nombre_clean not in clientes_rescatados:
            clientes_rescatados[nombre_clean] = 0
        
        pts_ganados = int(v.get('puntos_ganados') or 0)
        pts_usados = int(v.get('puntos_usados') or 0)
        clientes_rescatados[nombre_clean] += (pts_ganados - pts_usados)

if clientes_rescatados:
    print(f"🔍 Se han encontrado {len(clientes_rescatados)} clientes VIP perdidos. Restaurando...")
    for nombre, puntos in clientes_rescatados.items():
        print(f"  👉 Rescatando a: {nombre} | Saldo: {max(0, puntos)} puntos")
        client.table("clientes").insert({"nombre_dueno": nombre, "telefono": "", "puntos": max(0, puntos), "rgpd_consent": True}).execute()
    print("\n✅ ¡Rescate completado! Han vuelto al directorio con sus puntos intactos.")
else:
    print("\n✅ Todo en orden. No faltan clientes VIP en el directorio respecto a las ventas realizadas.")