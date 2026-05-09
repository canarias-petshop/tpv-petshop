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
print("🛠️ Iniciando corrección masiva de proveedores...")

# 1. Obtener ID del proveedor correcto
res_zoo = client.table("proveedores").select("id").eq("nombre_empresa", "Zootecnia - Zootecnia S.L.").execute()
if not res_zoo.data:
    print("❌ Error: No se encontró 'Zootecnia - Zootecnia S.L.' en la base de datos.")
    exit()
zoo_id = res_zoo.data[0]['id']

# 2. Lista de proveedores erróneos que creé antes
prov_malos = [
    "Gloria Pets", "Julius", "Kong Holiday", "Cunipic", "Earth Rated",
    "Kong", "Kong Mundial", "Stangest", "Beaphar", "Boehringer",
    "Elanco", "Flexi", "Ceva", "Kong Halloween"
]

# 3. Buscar y arreglar
res_malos = client.table("proveedores").select("id, nombre_empresa").in_("nombre_empresa", prov_malos).execute()
if res_malos.data:
    for p in res_malos.data:
        client.table("productos_proveedores").update({"proveedor_id": zoo_id}).eq("proveedor_id", p['id']).execute()
        client.table("proveedores").delete().eq("id", p['id']).execute()
        print(f"✅ Productos de '{p['nombre_empresa']}' traspasados a Zootecnia y nombre falso eliminado.")
    print(f"\n🎉 ¡Corrección completada! Todos los artículos ahora pertenecen a Zootecnia.")
else: print("✅ No se encontraron proveedores erróneos.")