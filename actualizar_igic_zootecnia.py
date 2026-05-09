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

print("🔄 Buscando productos de Zootecnia (Códigos ZT-)...")

res = client.table("productos").select("id, nombre").like("sku", "ZT-%").execute()

if res.data:
    for p in res.data:
        client.table("productos").update({"igic_tipo": 3.0}).eq("id", p['id']).execute()
    print(f"✅ ¡Éxito! Se ha corregido el IGIC al 3% en {len(res.data)} productos de Zootecnia.")
else:
    print("⚠️ No se encontraron productos de Zootecnia.")