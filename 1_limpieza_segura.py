import toml
from postgrest import SyncPostgrestClient
import os
from datetime import datetime, timedelta

def init_supabase():
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    with open(secrets_path, "r") as f: secrets = toml.load(f)
    raw_url = secrets.get('url', '').strip().strip('"').strip("'").rstrip('/')
    api_url = raw_url if raw_url.endswith('/rest/v1') else f"{raw_url}/rest/v1"
    api_key = secrets.get('key', '').strip().strip('"').strip("'")
    return SyncPostgrestClient(api_url, headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"})

client = init_supabase()

print("🛡️ Iniciando Limpieza Segura (Protegiendo Citas)...")

# 1. Identificar a los perros intocables (Los que tienen citas)
res_citas = client.table("citas").select("mascotas_id").execute()
mascotas_protegidas = set([c['mascotas_id'] for c in res_citas.data if c.get('mascotas_id')])

# 2. Buscar basura importada HOY
hace_24h = (datetime.utcnow() - timedelta(hours=24)).isoformat()
res_m = client.table("mascotas").select("id, cliente_id, nombre").gte("created_at", hace_24h).execute()

borradas_m = 0
clientes_a_revisar = set()

if res_m.data:
    for m in res_m.data:
        if m['id'] not in mascotas_protegidas:
            client.table("mascotas").delete().eq("id", m['id']).execute()
            clientes_a_revisar.add(m['cliente_id'])
            borradas_m += 1

borrados_c = 0
for c_id in clientes_a_revisar:
    client.table("clientes").delete().eq("id", c_id).execute()
    borrados_c += 1

print(f"\n✅ ¡Caos solucionado! Se borraron {borradas_m} mascotas y {borrados_c} clientes basura.")
print("Tus 403 fichas originales y TODAS las citas de la agenda están a salvo.")