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

print("🧹 Borrando proveedor equivocado 'Zotécnica'...")
client.table("proveedores").delete().eq("nombre_empresa", "Zotécnica").execute()

print("🧹 Borrando productos importados con código ZT-...")
res = client.table("productos").select("id").like("sku", "ZT-%").execute()
if res.data:
    for p in res.data:
        client.table("productos").delete().eq("id", p['id']).execute()
    print(f"✅ Se han borrado {len(res.data)} productos.")
else:
    print("✅ No había productos que borrar.")

print("\n✨ ¡Limpieza completada! El terreno está listo.")