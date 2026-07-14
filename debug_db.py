import tomli
from supabase import create_client

with open(".streamlit/secrets.toml", "rb") as f:
    secrets = tomli.load(f)

client = create_client(secrets["url"], secrets["key"])
res = client.table("productos").select("nombre, familia, subcategoria").eq("categoria", "Producto").limit(20).execute()
for p in res.data:
    print(p)
