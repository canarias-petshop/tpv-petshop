import tomli
from supabase import create_client

with open(".streamlit/secrets.toml", "rb") as f:
    secrets = tomli.load(f)

client = create_client(secrets["url"], secrets["key"])
res = client.table("productos").select("familia, subcategoria").execute()

fams = set(str(p.get("familia")).strip() for p in res.data if p.get("familia"))
subcats = set(str(p.get("subcategoria")).strip() for p in res.data if p.get("subcategoria"))
print("Familias:", fams)
print("Subcategorias:", subcats)
