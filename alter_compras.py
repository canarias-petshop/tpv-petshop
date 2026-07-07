import toml
from supabase import create_client, Client

secrets = toml.load(".streamlit/secrets.toml")
supabase: Client = create_client(secrets["url"].strip('"').strip("'"), secrets["key"].strip('"').strip("'"))

res = supabase.rpc('exec_sql', {'query': 'ALTER TABLE compras ADD COLUMN fecha_factura date;'}).execute()
print(res.data)
