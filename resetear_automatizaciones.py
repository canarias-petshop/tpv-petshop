import os
import toml
from postgrest import SyncPostgrestClient

def init_supabase():
    print("🔌 Conectando con Supabase...")
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    with open(secrets_path, "r", encoding="utf-8") as f: secrets = toml.load(f)
    
    raw_url = secrets.get('url', '').strip().strip('"').strip("'").rstrip('/')
    api_url = raw_url if raw_url.endswith('/rest/v1') else f"{raw_url}/rest/v1"
    api_key = secrets.get('key', '').strip().strip('"').strip("'")
    
    return SyncPostgrestClient(api_url, headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"})

client = init_supabase()

print("⚠️ Iniciando el reseteo masivo de automatizaciones de pedidos...")

try:
    # Ponemos a 0 el mínimo y la reposición de TODOS los productos (gt id -1 afecta a todos)
    res = client.table('productos').update({'stock_minimo': 0, 'cantidad_reponer': 0}).gt('id', -1).execute()
    
    if res.data:
        print(f"✅ ¡Éxito! Se han reseteado {len(res.data)} productos.")
        print("🚀 Ahora el Auto-Distribuidor solo te pedirá los artículos a los que les pongas manualmente la 'Cantidad a reponer' mayor a 0 en el Inventario.")
except Exception as e:
    print(f"❌ Error durante el reseteo: {e}")