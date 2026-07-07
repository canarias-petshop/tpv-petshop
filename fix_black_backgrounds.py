import csv
import os
import shutil
from PIL import Image
from supabase import create_client

url = "https://zpzhsmyyyfxqbjjiuana.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwemhzbXl5eWZ4cWJqaml1YW5hIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjEwMzAxNiwiZXhwIjoyMDkxNjc5MDE2fQ.9gNW0JdUf_xnbfEuRnO3WoMPASXQjfqRBkyCjPE0DCY"
supabase = create_client(url, key)

web_img_dir = r"D:\clon vs mode\web-petshop\public\images\productos"

# Fetch all Lenda from DB to map name -> sku
res = supabase.table("productos").select("sku, nombre").like("sku", "LE-%").execute()
db_products = res.data

name_to_sku = {}
for p in db_products:
    name_to_sku[p["nombre"].strip().lower()] = p["sku"]

csv_files = ["lenda_revision_catalogo.csv", "lenda_grain_free_revision.csv"]
fixed = 0

for file in csv_files:
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=";")
            header = next(reader)
            for row in reader:
                if len(row) < 5: continue
                if not row[0].strip(): continue
                
                name = row[0].strip()
                peso = row[2].strip()
                foto_bot = row[4].strip()
                foto_correcta = row[6].strip() if len(row) > 6 else ""
                final_foto = foto_correcta if foto_correcta else foto_bot
                
                if not final_foto or final_foto == "SIN FOTO":
                    continue
                    
                if peso.lower() not in name.lower():
                    full_name = f"{name} {peso}".strip().lower()
                else:
                    full_name = name.strip().lower()
                    
                sku = name_to_sku.get(full_name)
                
                if sku and os.path.isfile(final_foto):
                    dest = os.path.join(web_img_dir, f"{sku}.jpg")
                    try:
                        # Open original image from OneDrive
                        with Image.open(final_foto) as img:
                            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                                img = img.convert('RGBA')
                                background = Image.new('RGB', img.size, (255, 255, 255))
                                background.paste(img, mask=img.split()[3])
                                background.save(dest, "JPEG", quality=95)
                            else:
                                img.convert('RGB').save(dest, "JPEG", quality=95)
                        fixed += 1
                    except Exception as e:
                        print(f"Error processing {final_foto}: {e}")

print(f"Reparadas {fixed} imágenes con fondo blanco.")
