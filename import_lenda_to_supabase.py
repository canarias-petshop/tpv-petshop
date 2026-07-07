import os
import json
import shutil
from supabase import create_client

url = "https://zpzhsmyyyfxqbjjiuana.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwemhzbXl5eWZ4cWJqaml1YW5hIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjEwMzAxNiwiZXhwIjoyMDkxNjc5MDE2fQ.9gNW0JdUf_xnbfEuRnO3WoMPASXQjfqRBkyCjPE0DCY"
supabase = create_client(url, key)

web_img_dir = r"D:\clon vs mode\web-petshop\public\images\productos"
if not os.path.exists(web_img_dir):
    os.makedirs(web_img_dir)

with open("lenda_matched_strict.json", "r", encoding="utf-8") as f:
    products = json.load(f)

# Determine next SKU
res = supabase.table("productos").select("sku").like("sku", "LE-%").execute()
existing_skus = [p["sku"] for p in res.data if p.get("sku")]
max_num = 0
for s in existing_skus:
    try:
        num = int(s.split("-")[1])
        if num > max_num: max_num = num
    except:
        pass

current_sku_num = max_num + 1

inserted_count = 0

for p in products:
    name = p["name"]
    mascota = p.get("mascota", "Perro")
    peso = p["weight"]
    pvp = p["pvp"]
    img_path = p.get("best_image")
    source = p.get("source")
    
    gama = "Lenda"
    if source == "GrainFree": gama = "Grain Free"
    elif source == "Vet": gama = "Veterinaria"
    
    # Categorize
    familia = "Alimentación"
    subcategoria = "Alimentación seca" # Default
    
    n_lower = name.lower()
    if "lata" in n_lower or "pouch" in n_lower or "foodie" in n_lower or "húmedo" in n_lower or "humedo" in n_lower or "merluza al natural" in n_lower or "atún y gambas" in n_lower:
        subcategoria = "Alimentación húmeda"
    elif "snack" in n_lower or "rabo de toro" in n_lower or "mordiscos" in n_lower or "tapenade" in n_lower:
        subcategoria = "Snack"
        
    # Necesidad especial
    necesidad = None
    if "light" in n_lower or "low fat" in n_lower:
        necesidad = "Control de peso"
    elif "sterilized" in n_lower:
        necesidad = "Esterilizado"
    elif "sensitive" in n_lower or "digestive" in n_lower:
        necesidad = "Sensible / digestivo"
    elif "mobility" in n_lower:
        necesidad = "Articulaciones"
    elif "renal" in n_lower:
        necesidad = "Renal"
    elif "hepati" in n_lower:
        necesidad = "Hepático"
    elif "urinary" in n_lower or "urinario" in n_lower:
        necesidad = "Urinario"
    elif "hairball" in n_lower:
        necesidad = "Bolas de pelo"
    elif "hypo" in n_lower:
        necesidad = "Hipoalergénico"
    elif "exigente" in n_lower:
        necesidad = "Paladares exigentes"
        
    # Tamaño
    tamano = "Todas las razas"
    if "mini" in n_lower: tamano = "Mini/Pequeño"
    elif "maxi" in n_lower: tamano = "Grande"
    
    # Edad
    edad = "Todas las edades"
    if "puppy" in n_lower or "kitten" in n_lower: edad = "Cachorro/Kitten"
    elif "senior" in n_lower: edad = "Senior"
    else: edad = "Adulto"
    
    # Construct DB record
    sku = f"LE-{current_sku_num:03d}"
    
    formatted_peso = f"{peso} kg" if str(peso).replace(".","").isdigit() else str(peso)
    full_name = f"{name} {formatted_peso}".strip()
    
    record = {
        "sku": sku,
        "nombre": full_name,
        "categoria": "Producto",
        "marca": "Lenda",
        "familia": familia,
        "subcategoria": subcategoria,
        "gama": gama,
        "mascota": mascota,
        "edad": edad,
        "tamano": tamano,
        "necesidad_especial": necesidad,
        "precio_pvp": pvp if pvp else 0.0,
        "precio_base": pvp if pvp else 0.0,
        "caracteristicas": formatted_peso
    }
    
    # Insert to DB
    try:
        supabase.table("productos").insert(record).execute()
        
        # Copy image
        if img_path and os.path.exists(img_path):
            ext = os.path.splitext(img_path)[1]
            dest_path = os.path.join(web_img_dir, f"{sku}{ext}") # or forced .jpg
            dest_path_jpg = os.path.join(web_img_dir, f"{sku}.jpg") # Web app uses .jpg
            
            # Since web app hardcodes `.jpg` we will rename it to .jpg
            shutil.copy2(img_path, dest_path_jpg)
            
        current_sku_num += 1
        inserted_count += 1
    except Exception as e:
        print(f"Error inserting {name}: {e}")

print(f"Inserted {inserted_count} products.")
