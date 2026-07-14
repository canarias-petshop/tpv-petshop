import tomli
from supabase import create_client

with open(".streamlit/secrets.toml", "rb") as f:
    secrets = tomli.load(f)

client = create_client(secrets["url"], secrets["key"])
offset = 0
all_products = []
while True:
    res = client.table("productos").select("id, categoria, familia, subcategoria, nombre").range(offset, offset + 999).execute()
    if not res.data:
        break
    all_products.extend(res.data)
    offset += 1000

updates_count = 0
for p in all_products:
    if str(p.get("categoria")).strip() != "Producto":
        continue # Skip Servicios and Uso Interno!
        
    fam = str(p.get("familia") or "").strip()
    subcat = str(p.get("subcategoria") or "").strip()
    
    new_fam = fam
    new_subcat = subcat
    changed = False
    
    # 1. CLEAN FAMILIA ("Categoría" in UI)
    fam_lower = fam.lower()
    if fam_lower in ["alimentación húmeda", "alimentación seca", "alimentacion humeda", "alimentacion seca", "snack", "pienso", "alimentación", "alimentacion"]:
        if fam != "Alimentación":
            new_fam = "Alimentación"
            changed = True
            
    # 2. CLEAN SUBCATEGORIA
    # Sometimes the user accidentally put "Alimentación húmeda" in the subcategory column!
    sub_lower = subcat.lower()
    
    if sub_lower in ["pienso seco", "alimento seco", "alimentación seca", "alimentacion seca"]:
        if subcat != "Alimento Seco":
            new_subcat = "Alimento Seco"
            new_fam = "Alimentación" # Force familia too
            changed = True
    elif sub_lower in ["pienso húmedo", "pienso humedo", "alimento húmedo", "alimento humedo", "alimentación húmeda", "alimentacion humeda"]:
        if subcat != "Alimento Húmedo":
            new_subcat = "Alimento Húmedo"
            new_fam = "Alimentación"
            changed = True
    elif sub_lower in ["semi-húmedo", "semi-humedo", "pienso semihúmedo", "alimento semihúmedo", "semihúmedo", "semihumedo"]:
        if subcat != "Alimento Semihúmedo":
            new_subcat = "Alimento Semihúmedo"
            new_fam = "Alimentación"
            changed = True
    elif sub_lower in ["snacks", "snack"]:
        if subcat != "Snack":
            new_subcat = "Snack"
            new_fam = "Alimentación"
            changed = True
    elif "collar" in sub_lower or "arnes" in sub_lower or "arnés" in sub_lower:
        if subcat != "Collares":
            new_subcat = "Collares"
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
            
    if new_fam != fam or new_subcat != subcat:
        client.table("productos").update({"familia": new_fam, "subcategoria": new_subcat}).eq("id", p["id"]).execute()
        updates_count += 1
        print(f"Updated {p['nombre']}: Fam({fam}->{new_fam}) | Sub({subcat}->{new_subcat})")

print(f"Updated {updates_count} products successfully.")
