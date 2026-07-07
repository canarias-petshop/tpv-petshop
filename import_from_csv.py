import csv
import os
import shutil
import math
from supabase import create_client

# Supabase init
url = "https://zpzhsmyyyfxqbjjiuana.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwemhzbXl5eWZ4cWJqaml1YW5hIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjEwMzAxNiwiZXhwIjoyMDkxNjc5MDE2fQ.9gNW0JdUf_xnbfEuRnO3WoMPASXQjfqRBkyCjPE0DCY"
supabase = create_client(url, key)

csv_files = ["lenda_revision_catalogo.csv", "lenda_grain_free_revision.csv"]
all_products = []

for file in csv_files:
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f, delimiter=";")
            header = next(reader)
            for row in reader:
                if len(row) < 5: continue
                if not row[0].strip(): continue
                
                # Nombre Original PDF;Gama Extraída;Peso Sugerido Web;PVP;Ruta de Foto Asignada por el Bot;Foto Correcta? (SI/NO);Ruta CORRECTA de Foto
                name = row[0].strip()
                gama = row[1].strip()
                peso = row[2].strip()
                pvp_str = row[3].replace(",", ".").replace("€", "").strip()
                pvp = float(pvp_str) if pvp_str else 0.0
                
                foto_bot = row[4].strip()
                foto_correcta = row[6].strip() if len(row) > 6 else ""
                
                final_foto = foto_correcta if foto_correcta else foto_bot
                
                all_products.append({
                    "name": name,
                    "gama": gama,
                    "peso": peso,
                    "pvp": pvp,
                    "foto": final_foto
                })

print(f"Leídos {len(all_products)} productos en total.")

# Get next SKU
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

web_img_dir = r"D:\clon vs mode\web-petshop\public\images\productos"
if not os.path.exists(web_img_dir):
    os.makedirs(web_img_dir)

inserted = 0
for p in all_products:
    name = p["name"]
    peso = p["peso"]
    pvp = p["pvp"]
    gama = p["gama"]
    img_path = p["foto"]
    
    n_lower = name.lower()
    
    # Mascota
    mascota = "Perro"
    if "gato" in n_lower or "cat" in n_lower or "kitten" in n_lower or ("Gatos" in img_path):
        mascota = "Gato"
        
    # Subcategoria
    subcategoria = "Alimentación seca"
    if "lata" in n_lower or "pouch" in n_lower or "foodie" in n_lower or "húmedo" in n_lower or "humedo" in n_lower or "merluza al natural" in n_lower or "atún y gambas" in n_lower or "ml" in peso.lower():
        subcategoria = "Alimentación húmeda"
    elif "snack" in n_lower or "rabo de toro" in n_lower or "mordiscos" in n_lower or "tapenade" in n_lower:
        subcategoria = "Snack"
        
    # Aceite special check
    if "aceite" in n_lower and "atún" in n_lower:
        subcategoria = "Suplementos" # Or Alimentacion humeda? We'll put Alimentacion humeda for now or Snack to show in web
        
    # Necesidad especial
    necesidad = None
    if "light" in n_lower or "low fat" in n_lower or "slimming" in n_lower:
        necesidad = "Control de peso"
    elif "sterilized" in n_lower or "esterilizado" in n_lower:
        necesidad = "Esterilizado"
    elif "sensitive" in n_lower or "digestive" in n_lower or "gastro" in n_lower:
        necesidad = "Sensible / digestivo"
    elif "mobility" in n_lower or "joint" in n_lower:
        necesidad = "Articulaciones"
    elif "renal" in n_lower or "oxalate" in n_lower:
        necesidad = "Renal"
    elif "hepati" in n_lower:
        necesidad = "Hepático"
    elif "urinary" in n_lower or "urinario" in n_lower or "struvite" in n_lower:
        necesidad = "Urinario"
    elif "hairball" in n_lower:
        necesidad = "Bolas de pelo"
    elif "hypo" in n_lower or "allergenic" in n_lower:
        necesidad = "Hipoalergénico"
    elif "exigente" in n_lower or "delicate" in n_lower:
        necesidad = "Paladares exigentes"
    elif "diabetic" in n_lower:
        necesidad = "Diabético"
    elif "cardiac" in n_lower:
        necesidad = "Cardíaco"
        
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
    
    # Evitar duplicar el peso si ya está en el nombre (a veces el usuario lo metió en el nombre en el Excel)
    if peso.lower() not in name.lower():
        full_name = f"{name} {peso}".strip()
    else:
        full_name = name.strip()
        
    precio_base = round(pvp / 1.07, 2) if pvp else 0.0
    
    record = {
        "sku": sku,
        "nombre": full_name,
        "categoria": "Producto",
        "marca": "Lenda",
        "familia": "Alimentación",
        "subcategoria": subcategoria,
        "gama": gama,
        "mascota": mascota,
        "edad": edad,
        "tamano": tamano,
        "necesidad_especial": necesidad,
        "precio_pvp": pvp,
        "precio_base": precio_base,
        "igic_tipo": 7.00,
        "caracteristicas": peso
    }
    
    # Insert to DB
    try:
        sup_res = supabase.table("productos").insert(record).execute()
        
        # Copy image if valid
        if img_path and os.path.isfile(img_path):
            ext = os.path.splitext(img_path)[1]
            if not ext: ext = ".jpg"
            dest = os.path.join(web_img_dir, f"{sku}{ext}")
            shutil.copy2(img_path, dest)
            
        inserted += 1
        current_sku_num += 1
    except Exception as e:
        print(f"Error inserting {full_name}: {e}")

print(f"Importación completada. Se insertaron {inserted} productos.")
