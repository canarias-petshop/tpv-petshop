import tomli
from supabase import create_client

with open(".streamlit/secrets.toml", "rb") as f:
    secrets = tomli.load(f)

client = create_client(secrets["url"], secrets["key"])
res = client.table("productos").select("subcategoria").execute()

subcats = set()
for p in res.data:
    if p.get("subcategoria"):
        subcats.add(p["subcategoria"].strip())

for s in sorted(subcats):
    print(s)
