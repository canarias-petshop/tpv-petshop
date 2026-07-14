import tomli
from supabase import create_client

with open(".streamlit/secrets.toml", "rb") as f:
    secrets = tomli.load(f)

client = create_client(secrets["url"], secrets["key"])
res = client.table("productos").update({"subcategoria": "Alimento Seco"}).eq("subcategoria", "Alimentación seca").execute()
print(f"Updated {len(res.data)} products from 'Alimentación seca' to 'Alimento Seco'.")
