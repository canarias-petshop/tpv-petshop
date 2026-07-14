import tomli
from supabase import create_client, Client

with open(".streamlit/secrets.toml", "rb") as f:
    secrets = tomli.load(f)

supabase_url = secrets["url"]
supabase_key = secrets["key"]

client: Client = create_client(supabase_url, supabase_key)

print("Fetching products...")
offset = 0
all_products = []
while True:
    res = client.table("productos").select("id, categoria, subcategoria, nombre").range(offset, offset + 999).execute()
    if not res.data:
        break
    all_products.extend(res.data)
    offset += 1000

print(f"Found {len(all_products)} products.")

updates_count = 0
for p in all_products:
    cat = str(p.get("categoria") or "").strip()
    subcat = str(p.get("subcategoria") or "").strip()
    
    new_cat = cat
    new_subcat = subcat
    changed = False
    
    # 1. Update Categoría
    if cat.lower() in ["alimentación húmeda", "alimentación seca", "alimentacion humeda", "alimentacion seca", "snack", "pienso", "alimentación", "alimentacion"]:
        if cat != "Alimentación":
            new_cat = "Alimentación"
            changed = True
            
    # 2. Update Subcategoría
    sub_lower = subcat.lower()
    
    if sub_lower == "pienso seco" or sub_lower == "alimento seco":
        if subcat != "Alimento Seco":
            new_subcat = "Alimento Seco"
            changed = True
    elif sub_lower in ["pienso húmedo", "pienso humedo", "alimento húmedo", "alimento humedo"]:
        if subcat != "Alimento Húmedo":
            new_subcat = "Alimento Húmedo"
            changed = True
    elif sub_lower in ["semi-húmedo", "semi-humedo", "pienso semihúmedo", "alimento semihúmedo"]:
        if subcat != "Alimento Semihúmedo":
            new_subcat = "Alimento Semihúmedo"
            changed = True
    elif sub_lower in ["snacks", "snack"]:
        if subcat != "Snack":
            new_subcat = "Snack"
            changed = True
    elif "collar" in sub_lower or "arnes" in sub_lower or "arnés" in sub_lower:
        if subcat != "Collares/Arneses":
            new_subcat = "Collares/Arneses"
            changed = True
    elif sub_lower in ["champús", "champu", "champú"]:
        if subcat != "Champú":
            new_subcat = "Champú"
            changed = True
    elif sub_lower in ["medicamentos", "medicamento"]:
        if subcat != "Medicamento":
            new_subcat = "Medicamento"
            changed = True
    elif sub_lower == "juguetes":
        if subcat != "Juguetes":
            new_subcat = "Juguetes"
            changed = True
            
    if changed:
        client.table("productos").update({"categoria": new_cat, "subcategoria": new_subcat}).eq("id", p["id"]).execute()
        updates_count += 1
        print(f"Updated {p['nombre']}: {cat} -> {new_cat} | {subcat} -> {new_subcat}")

print(f"Updated {updates_count} products successfully.")
