import toml
from supabase import create_client, Client

secrets = toml.load(".streamlit/secrets.toml")
url = secrets["url"].strip('"').strip("'")
key = secrets["key"].strip('"').strip("'")
supabase: Client = create_client(url, key)

res = supabase.table('productos').select('*', count='exact').limit(1).execute()
print(f"Total productos en Supabase: {res.count}")

# Check if services exist
res2 = supabase.table('productos').select('nombre').eq('marca', 'Servicio').limit(5).execute()
print("Ejemplo de servicios insertados:")
for r in res2.data:
    print(r['nombre'])
