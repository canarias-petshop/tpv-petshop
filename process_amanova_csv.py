import csv
import os
from PIL import Image
from supabase import create_client

url = "https://zpzhsmyyyfxqbjjiuana.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwemhzbXl5eWZ4cWJqaml1YW5hIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjEwMzAxNiwiZXhwIjoyMDkxNjc5MDE2fQ.9gNW0JdUf_xnbfEuRnO3WoMPASXQjfqRBkyCjPE0DCY"
supabase = create_client(url, key)

csv_file = "amanova_revision_catalogo.csv"
web_img_dir = r"D:\clon vs mode\web-petshop\public\images\productos"

updated_prices = 0
updated_photos = 0

with open(csv_file, mode="r", encoding="utf-8") as f:
    reader = csv.reader(f, delimiter=";")
    header = next(reader)
    
    # Expected columns:
    # 0: ID_Supabase
    # 1: SKU
    # 2: Nombre
    # 3: Gama
    # 4: Subcategoria
    # 5: Peso (kg/g)
    # 6: PVP
    # 7: Precio Base (PVD)
    # 8: Ruta Foto Actual
    # 9: Foto Correcta?
    # 10: Ruta CORRECTA de Foto
    
    for row in reader:
        if len(row) < 11:
            continue
            
        id_supabase = row[0].strip()
        sku = row[1].strip()
        pvp_str = row[6].strip().replace(",", ".")
        pvd_str = row[7].strip().replace(",", ".")
        ruta_correcta = row[10].strip()
        
        if not id_supabase:
            continue
            
        # 1. Update Prices
        updates = {}
        if pvp_str:
            try:
                pvp = float(pvp_str)
                updates["precio_pvp"] = pvp
                
                if pvd_str:
                    updates["precio_base"] = float(pvd_str)
                else:
                    updates["precio_base"] = round(pvp / 1.07, 2)
                    
            except ValueError:
                pass
                
        if updates:
            try:
                supabase.table("productos").update(updates).eq("id", id_supabase).execute()
                updated_prices += 1
            except Exception as e:
                print(f"Error updating prices for {sku}: {e}")
                
        # 2. Update Photos
        if ruta_correcta and os.path.isfile(ruta_correcta):
            if sku:
                dest = os.path.join(web_img_dir, f"{sku}.jpg")
                try:
                    with Image.open(ruta_correcta) as img:
                        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                            img = img.convert('RGBA')
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            background.paste(img, mask=img.split()[3])
                            background.save(dest, "JPEG", quality=95)
                        else:
                            img.convert('RGB').save(dest, "JPEG", quality=95)
                    updated_photos += 1
                except Exception as e:
                    print(f"Error processing image for {sku}: {e}")

print(f"Resumen de actualización Amanova:")
print(f"Precios actualizados: {updated_prices}")
print(f"Fotos nuevas/corregidas: {updated_photos}")
