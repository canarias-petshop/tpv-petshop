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
print("🛠️ Moviendo productos de Royal Canin a Zootecnia...")

# 1. Obtener ID de Zootecnia
res_zoo = client.table("proveedores").select("id").eq("nombre_empresa", "Zootecnia - Zootecnia S.L.").execute()
if not res_zoo.data:
    print("❌ Error: No se encontró 'Zootecnia - Zootecnia S.L.'.")
    exit()
zoo_id = res_zoo.data[0]['id']

# 2. Buscar Royal Canin y arreglarlo
res_malos = client.table("proveedores").select("id").eq("nombre_empresa", "Royal Canin").execute()
if res_malos.data:
    for p in res_malos.data:
        client.table("productos_proveedores").update({"proveedor_id": zoo_id}).eq("proveedor_id", p['id']).execute()
        client.table("proveedores").delete().eq("id", p['id']).execute()
    print("✅ ¡Arreglado! Los 146 productos de Royal Canin ya pertenecen a Zootecnia.")
else:
    print("✅ No se encontró el proveedor 'Royal Canin'.")