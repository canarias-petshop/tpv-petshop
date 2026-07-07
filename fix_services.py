import toml
from supabase import create_client, Client

secrets = toml.load(".streamlit/secrets.toml")
url = secrets["url"].strip('"').strip("'")
key = secrets["key"].strip('"').strip("'")
supabase: Client = create_client(url, key)

# Actualizar todos los servicios recién insertados
res = supabase.table("productos").update({"categoria": "Servicio"}).ilike("sku", "SRV-%").execute()
print(f"Actualizados {len(res.data) if res.data else 0} servicios con categoria='Servicio'.")
