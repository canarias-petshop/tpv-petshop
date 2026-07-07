import toml
from supabase import create_client, Client

secrets = toml.load(".streamlit/secrets.toml")
url = secrets["url"].strip('"').strip("'")
key = secrets["key"].strip('"').strip("'")
supabase: Client = create_client(url, key)

res = supabase.table('productos').select('id, sku, nombre, precio_pvp, gama').ilike('marca', '%atlantic%').execute()

print(f"Encontrados {len(res.data)} productos en la BD:")
for r in res.data:
    print(r)
