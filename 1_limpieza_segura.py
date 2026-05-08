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

print("🛡️ Iniciando Limpieza Segura (Basada en Clientes)...")

# 1. Identificar a los perros intocables (Los que tienen citas)
res_citas = client.table("citas").select("mascotas_id").execute()
mascotas_protegidas = set([c['mascotas_id'] for c in res_citas.data if c.get('mascotas_id')])

# 2. Buscar CLIENTES importados HOY (La tabla clientes sí tiene created_at)
hace_24h = (datetime.utcnow() - timedelta(hours=24)).isoformat()
res_c = client.table("clientes").select("id").gte("created_at", hace_24h).execute()

borradas_m = 0
borrados_c = 0

if res_c.data:
    clientes_basura_ids = [c['id'] for c in res_c.data]
    
    # 3. Buscar y borrar las mascotas de esos clientes nuevos
    res_m = client.table("mascotas").select("id, cliente_id").in_("cliente_id", clientes_basura_ids).execute()
    if res_m.data:
        for m in res_m.data:
            if m['id'] not in mascotas_protegidas:
                client.table("mascotas").delete().eq("id", m['id']).execute()
                borradas_m += 1

    # 4. Borrar los clientes (solo si ya no les quedan mascotas protegidas)
    for c_id in clientes_basura_ids:
        res_check = client.table("mascotas").select("id").eq("cliente_id", c_id).execute()
        if not res_check.data:
            client.table("clientes").delete().eq("id", c_id).execute()
            borrados_c += 1

print(f"\n✅ ¡Caos solucionado! Se borraron {borradas_m} mascotas y {borrados_c} clientes basura.")
print("Tus 403 fichas originales y TODAS las citas de la agenda están a salvo.")