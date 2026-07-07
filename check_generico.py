import toml
from supabase import create_client, Client

secrets = toml.load(".streamlit/secrets.toml")
url = secrets["url"].strip('"').strip("'")
key = secrets["key"].strip('"').strip("'")
supabase: Client = create_client(url, key)

r = supabase.table('productos').select('nombre, marca').ilike('nombre', '%agua%').execute()
print(r.data)
