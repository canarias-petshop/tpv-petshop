import tomli
from supabase import create_client

with open(".streamlit/secrets.toml", "rb") as f:
    secrets = tomli.load(f)

client = create_client(secrets["url"], secrets["key"])
res = client.table("productos").select("marca, familia, subcategoria, nombre").eq("categoria", "Producto").execute()

from collections import defaultdict
brands = defaultdict(list)
for p in res.data:
    fam = p.get("familia")
    sub = p.get("subcategoria")
    if not fam or fam in ["Generico", "Otros", ""] or not sub or sub == "":
        marca = str(p.get("marca") or "Generico").strip()
        brands[marca].append(p.get("nombre"))

for m, prods in sorted(brands.items(), key=lambda x: len(x[1]), reverse=True)[:20]:
    print(f"Marca: {m} - Uncategorized: {len(prods)}")
    print(f"Examples: {prods[:3]}")
    print("---")
