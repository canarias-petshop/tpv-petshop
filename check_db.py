import tomli
from supabase import create_client

with open(".streamlit/secrets.toml", "rb") as f:
    secrets = tomli.load(f)

client = create_client(secrets["url"], secrets["key"])
offset = 0
all_products = []
while True:
    res = client.table("productos").select("categoria, subcategoria").range(offset, offset + 999).execute()
    if not res.data:
        break
    all_products.extend(res.data)
    offset += 1000

cats = set(str(p.get("categoria")).strip() for p in all_products)
subcats = set(str(p.get("subcategoria")).strip() for p in all_products)
print("Categorias:", cats)
print("Subcategorias:", subcats)
