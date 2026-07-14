import tomli
import re
from supabase import create_client

with open(".streamlit/secrets.toml", "rb") as f:
    secrets = tomli.load(f)

client = create_client(secrets["url"], secrets["key"])

offset = 0
all_products = []
while True:
    res = client.table("productos").select("id, nombre, categoria, familia, subcategoria, marca, mascota, edad, tamano, necesidad_especial, sabor_principal").range(offset, offset + 999).execute()
    if not res.data:
        break
    all_products.extend(res.data)
    offset += 1000

updates_count = 0

def is_empty(val, defaults):
    if not val: return True
    if val.strip() in defaults: return True
    return False

for p in all_products:
    if str(p.get("categoria")).strip() != "Producto":
        continue
        
    nombre = str(p.get("nombre") or "").upper()
    
    # Current values
    fam = str(p.get("familia") or "").strip()
    sub = str(p.get("subcategoria") or "").strip()
    marca = str(p.get("marca") or "").strip()
    mascota = str(p.get("mascota") or "").strip()
    edad = str(p.get("edad") or "").strip()
    tamano = str(p.get("tamano") or "").strip()
    necesidad = str(p.get("necesidad_especial") or "").strip()
    sabor = str(p.get("sabor_principal") or "").strip()
    
    updates = {}
    
    # MARCA DEDUCTION
    if is_empty(marca, ["", "Genérico", "Generico"]):
        if "ACANA" in nombre: updates["marca"] = "ACANA"
        elif "ATLANTIC PET" in nombre: updates["marca"] = "ATLANTIC PET"
        elif "OWNAT" in nombre: updates["marca"] = "OWNAT"
        elif "LENDA" in nombre: updates["marca"] = "LENDA"
        elif "ROYAL CANIN" in nombre: updates["marca"] = "ROYAL CANIN"
        elif "PRO PLAN" in nombre: updates["marca"] = "PRO PLAN"
        elif "OASY" in nombre: updates["marca"] = "OASY"
        elif "ANTOS" in nombre: updates["marca"] = "ANTOS"
        elif "APPLAWS" in nombre: updates["marca"] = "APPLAWS"
    
    current_marca = updates.get("marca", marca).upper()

    # FAMILIA AND SUBCATEGORIA
    if is_empty(fam, ["", "Generico", "Otros"]) or is_empty(sub, ["", "Otros"]):
        if current_marca in ["ACANA", "ATLANTIC PET", "OWNAT", "LENDA", "ROYAL CANIN", "PRO PLAN", "OASY", "NATURES VARIETY", "ADVANCE", "LIBRA", "GOSBI"]:
            updates["familia"] = "Alimentación"
            if "LATA" in nombre or "POUCH" in nombre or "PATE" in nombre or "SOBRE" in nombre or "GEL" in nombre:
                updates["subcategoria"] = "Alimento Húmedo"
            else:
                updates["subcategoria"] = "Alimento Seco"
        if "ACEITE DE SALMON" in nombre or "ACEITE DE SALMÓN" in nombre:
            updates["familia"] = "Alimentación"
            updates["subcategoria"] = "Suplementos" # Or snack, as user suggested "snack". Let's use Suplementos or Snack. TPV has "Snack"
            if "subcategoria" not in updates: updates["subcategoria"] = "Snack"
            
    # MASCOTA
    if is_empty(mascota, ["", "Universal"]):
        if re.search(r'\b(CAT|GATO|GATOS|KITTEN|FELINE)\b', nombre): updates["mascota"] = "Gato"
        elif re.search(r'\b(DOG|PERRO|PERROS|PUPPY|CANINE)\b', nombre): updates["mascota"] = "Perro"
        elif re.search(r'\b(HAMSTER|COBAYA|CONEJO|HENO|ROEDOR)\b', nombre): updates["mascota"] = "Roedor"
        elif re.search(r'\b(PAJARO|AVES|CANARIO|PERIQUITO|AGAPORNI|NINFA)\b', nombre): updates["mascota"] = "Aves"
        elif re.search(r'\b(TORTUGA|IGUANA|REPTIL)\b', nombre): updates["mascota"] = "Reptiles"

    # EDAD
    if is_empty(edad, ["", "Todas las edades"]):
        if re.search(r'\b(PUPPY|KITTEN|JUNIOR|CACHORRO)\b', nombre): updates["edad"] = "Cachorro/Kitten"
        elif re.search(r'\b(SENIOR|MATURE|7\+|11\+|AGED)\b', nombre): updates["edad"] = "Senior"
        elif re.search(r'\b(ADULT|ADULTO)\b', nombre): updates["edad"] = "Adulto"

    # TAMANO
    if is_empty(tamano, ["", "Todas las razas", "Todas las Razas"]):
        if re.search(r'\b(MINI|SMALL|PEQUEÑO)\b', nombre): updates["tamano"] = "Mini"
        elif re.search(r'\b(MEDIUM|MEDIANO)\b', nombre): updates["tamano"] = "Mediano"
        elif re.search(r'\b(MAXI|LARGE|GRANDE|GIANT)\b', nombre): updates["tamano"] = "Grande"

    # NECESIDAD ESPECIAL
    if is_empty(necesidad, ["", "Ninguna"]):
        if re.search(r'\b(STERILISED|STERILIZED|ESTERILIZADO|NEUTERED)\b', nombre): updates["necesidad_especial"] = "Esterilizado"
        elif re.search(r'\b(HYPOALLERGENIC|HIPOALERGENICO|HIPO|SENSITIVE|DIGESTIVE|SENSORY)\b', nombre): updates["necesidad_especial"] = "Sensible/digestivo" # or Hipoalergénico depending
            # let's try to match exact option names if possible
        if re.search(r'\b(HYPOALLERGENIC|HIPOALERGENICO|HIPOALERGÉNICO)\b', nombre): updates["necesidad_especial"] = "Hipoalergénico"
        elif re.search(r'\b(URINARY|URINARIO)\b', nombre): updates["necesidad_especial"] = "Urinario"
        elif re.search(r'\b(RENAL|KIDNEY)\b', nombre): updates["necesidad_especial"] = "Renal"
        elif re.search(r'\b(HEPATIC|HEPATICO)\b', nombre): updates["necesidad_especial"] = "Hepático"
        elif re.search(r'\b(WEIGHT|LIGHT|OBESITY)\b', nombre): updates["necesidad_especial"] = "Control de peso"
        elif re.search(r'\b(HAIRBALL|BOLAS DE PELO)\b', nombre): updates["necesidad_especial"] = "Bolas de pelo"
        elif re.search(r'\b(JOINT|MOBILITY|ARTICULACIONES)\b', nombre): updates["necesidad_especial"] = "Articulaciones"

    # SABOR
    if is_empty(sabor, ["", "Sin especificar"]):
        if re.search(r'\b(POLLO|CHICKEN|POULTRY|AVES)\b', nombre): updates["sabor_principal"] = "Pollo"
        elif re.search(r'\b(SALMON|SALMÓN)\b', nombre): updates["sabor_principal"] = "Salmón"
        elif re.search(r'\b(CORDERO|LAMB)\b', nombre): updates["sabor_principal"] = "Cordero"
        elif re.search(r'\b(PATO|DUCK)\b', nombre): updates["sabor_principal"] = "Pato"
        elif re.search(r'\b(PAVO|TURKEY)\b', nombre): updates["sabor_principal"] = "Pavo"
        elif re.search(r'\b(TERNERA|BEEF|BUEY)\b', nombre): updates["sabor_principal"] = "Ternera/Buey"
        elif re.search(r'\b(CERDO|PORK)\b', nombre): updates["sabor_principal"] = "Cerdo"
        elif re.search(r'\b(PESCADO|FISH|ATUN|ATÚN|TUNA|CABALLA|SARDINA)\b', nombre): 
            if "ATUN" in nombre or "ATÚN" in nombre or "TUNA" in nombre: updates["sabor_principal"] = "Atún"
            else: updates["sabor_principal"] = "Pescado"
        elif re.search(r'\b(CONEJO|RABBIT)\b', nombre): updates["sabor_principal"] = "Conejo"
        elif re.search(r'\b(CIERVO|VENISON)\b', nombre): updates["sabor_principal"] = "Ciervo"

    if updates:
        client.table("productos").update(updates).eq("id", p["id"]).execute()
        updates_count += 1
        print(f"Updated {p['nombre']}: {updates}")

print(f"\nAdvanced auto-categorization finished. Updated {updates_count} products.")
