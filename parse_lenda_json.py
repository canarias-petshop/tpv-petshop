import json
import re

with open("lenda_tables.json", "r", encoding="utf-8") as f:
    data = json.load(f)

products = []

def parse_price(val):
    if not val: return None
    s = str(val).replace("€", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(s)
    except:
        return None

# Parse Tienda
tienda_tables = data.get("Tarifa Lenda 2026 Tienda.pdf", [])
current_mascota = "Perro"
for table in tienda_tables:
    current_name = None
    for row in table:
        if not row: continue
        name_raw = row[0]
        if name_raw and isinstance(name_raw, str):
            name_raw = name_raw.strip()
            if name_raw.upper() == "PERRO": current_mascota = "Perro"
            elif name_raw.upper() == "GATO": current_mascota = "Gato"
            elif name_raw and name_raw not in ["Kilos", "Tienda*", "Pvpr", "Húmedos Lenda", "Húmedos Lenda Foodie", "Aceites / Snacks Lenda", "Lenda LC", "Lenda Urban", "Lenda Urban GATO", "Base Daily Food"]:
                current_name = name_raw
        elif name_raw is None and current_name:
            pass
            
        if not current_name: continue
        weight = str(row[1]).strip() if len(row) > 1 and row[1] else None
        if not weight and len(row) > 0 and row[0] and isinstance(row[0], str) and "Ud" in row[0]: continue
        
        prices = []
        for i in range(2, len(row)):
            if isinstance(row[i], str) and "€" in row[i]: prices.append(row[i])
                
        if weight and prices:
            products.append({"source": "Tienda", "name": f"Lenda {current_name}", "mascota": current_mascota, "weight": weight, "pvp": parse_price(prices[-1])})

# Parse Grain Free
gf_tables = data.get("Tarifa Lenda 2026 Nueva Gama - Grain Free PVD.pdf", [])
for table in gf_tables:
    for row in table:
        if not row: continue
        if len(row) >= 4:
            w_raw = str(row[0]).strip() if row[0] else ""
            if "KG" in w_raw.upper():
                weight = w_raw.upper().replace("KG", "").strip()
                prices = [c for c in row if isinstance(c, str) and "€" in c]
                if prices:
                    products.append({"source": "GrainFree", "name": f"Lenda Grain Free [Unknown]", "mascota": "Perro", "weight": weight, "pvp": parse_price(prices[-1])})

# Parse Vet
vet_tables = data.get("Tarifa LendaVet 2026 Clinica.pdf", [])
current_mascota_vet = "Perro"
for table in vet_tables:
    current_name = None
    for row in table:
        if not row: continue
        name_raw = row[0]
        if name_raw and isinstance(name_raw, str) and "€" not in name_raw and not name_raw.isdigit():
            name_raw = name_raw.strip()
            if name_raw.upper() == "PERRO": current_mascota_vet = "Perro"
            elif name_raw.upper() == "GATO": current_mascota_vet = "Gato"
            elif name_raw and name_raw not in ["Kilos", "Clinica", "Pvpr"]:
                current_name = name_raw
                
        if not current_name: continue
        weight = str(row[1]).strip() if len(row) > 1 and row[1] else None
        prices = [c for c in row[2:] if isinstance(c, str) and "€" in c]
        if weight and prices and weight.replace(",", "").replace(".", "").isdigit():
            products.append({"source": "Vet", "name": f"Lenda Vet {current_name}", "mascota": current_mascota_vet, "weight": weight, "pvp": parse_price(prices[-1])})

print(f"Extracted {len(products)} total products")
with open("lenda_parsed_draft.json", "w", encoding="utf-8") as f:
    json.dump(products, f, indent=2, ensure_ascii=False)
