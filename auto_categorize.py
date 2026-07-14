import tomli
from supabase import create_client

with open(".streamlit/secrets.toml", "rb") as f:
    secrets = tomli.load(f)

client = create_client(secrets["url"], secrets["key"])
offset = 0
all_products = []
while True:
    res = client.table("productos").select("id, categoria, familia, subcategoria, nombre, marca").range(offset, offset + 999).execute()
    if not res.data:
        break
    all_products.extend(res.data)
    offset += 1000

def get_inferred_brand(p):
    marca = str(p.get("marca") or "").strip()
    if marca.lower() in ["genérico", "generico", ""]:
        nombre = str(p.get("nombre") or "").strip()
        if nombre:
            return nombre.split(" ")[0].upper()
    return marca.upper()

def categorize(brand, name):
    name_lower = name.lower()
    b = brand.lower()
    
    if b == "antos":
        return "Alimentación", "Snack"
    elif b == "applaws" or b == "lenda" or b == "ownat" or b == "amanova":
        # Check if wet or dry
        if "lata" in name_lower or "pouch" in name_lower or "gel" in name_lower or "húmed" in name_lower or "humed" in name_lower:
            return "Alimentación", "Alimento Húmedo"
        else:
            return "Alimentación", "Alimento Seco"
    elif b == "artero":
        if "dedal" in name_lower or "tijera" in name_lower or "peine" in name_lower or "corta" in name_lower:
            return "Accesorios", "Peluquería"
        else:
            return "Higiene", "Champú"
    elif b == "douxo" or b == "douxo spa":
        return "Higiene", "Champú"
    elif b == "dentican":
        return "Higiene", "Medicamento"
    elif b == "heiniger":
        return "Accesorios", "Otros"
    elif b == "kong":
        return "Juguetes", "Juguetes"
    elif b == "flexi":
        return "Paseo", "Collares"
    elif b in ["seresto", "advantix", "frontline", "scalibor", "prevendog", "adtab", "pestigon"]:
        return "Farmacia/Cuidados", "Medicamento"
    
    return None, None

updates = 0
for p in all_products:
    if str(p.get("categoria")).strip() != "Producto":
        continue
        
    fam = str(p.get("familia") or "").strip()
    sub = str(p.get("subcategoria") or "").strip()
    
    # Only try to infer if empty or generic
    if not fam or fam in ["Generico", "Otros", ""] or not sub or sub == "":
        brand = get_inferred_brand(p)
        new_fam, new_sub = categorize(brand, str(p.get("nombre") or ""))
        
        # Merge logic: if we found a new fam/sub, we apply it. If they only had one missing, we update both anyway to keep consistency.
        if new_fam and new_sub:
            if fam != new_fam or sub != new_sub:
                client.table("productos").update({"familia": new_fam, "subcategoria": new_sub}).eq("id", p["id"]).execute()
                updates += 1
                print(f"[{brand}] {p['nombre']}: {fam}/{sub} -> {new_fam}/{new_sub}")

print(f"Auto-categorized {updates} products.")
