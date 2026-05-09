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

print("🧹 Buscando productos antiguos de Ownat (Códigos OW-)...")
res = client.table("productos").select("id").like("sku", "OW-%").execute()

if res.data:
    borrados = 0
    for p in res.data:
        client.table("productos_proveedores").delete().eq("producto_id", p['id']).execute()
        client.table("productos").delete().eq("id", p['id']).execute()
        borrados += 1
    print(f"✅ Se han borrado {borrados} productos antiguos de Ownat.")
else:
    print("✅ No había productos de Ownat que borrar.")

print("✨ ¡Terreno despejado! Ya puedes ejecutar importador_ownat.py en limpio.")