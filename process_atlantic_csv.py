import csv
import os
from PIL import Image
from supabase import create_client

url = "https://zpzhsmyyyfxqbjjiuana.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwemhzbXl5eWZ4cWJqaml1YW5hIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjEwMzAxNiwiZXhwIjoyMDkxNjc5MDE2fQ.9gNW0JdUf_xnbfEuRnO3WoMPASXQjfqRBkyCjPE0DCY"
supabase = create_client(url, key)

csv_file = "atlantic_pet_revision_catalogo.csv"
web_img_dir = r"D:\clon vs mode\web-petshop\public\images\productos"

updated_prices = 0
updated_photos = 0
deleted_products = 0

with open(csv_file, mode="r", encoding="cp1252", errors="replace") as f:
    # Handle both comma and semicolon just in case
    # Let's peek at the first line
    first_line = f.readline()
    delimiter = ";" if ";" in first_line else ","
    f.seek(0)
    
    reader = csv.reader(f, delimiter=delimiter)
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
    # 11: (Optional) Eliminar
    
    for row in reader:
        if not row or len(row) < 2:
            continue
            
        id_supabase = row[0].strip()
        sku = row[1].strip() if len(row) > 1 else ""
        
        if not id_supabase:
            continue
            
        # Check for "eliminar" column (usually index 11 or anywhere past 10)
        should_delete = False
        for cell in row[10:]:
            if "eliminar" in cell.lower():
                should_delete = True
                break
                
        if should_delete:
            try:
                # Delete from Supabase
                supabase.table("productos").delete().eq("id", id_supabase).execute()
                deleted_products += 1
                
                # Delete image if exists
                if sku:
                    img_path = os.path.join(web_img_dir, f"{sku}.jpg")
                    if os.path.exists(img_path):
                        os.remove(img_path)
            except Exception as e:
                print(f"Error deleting product {sku}: {e}")
            continue

        pvp_str = row[6].strip().replace(",", ".") if len(row) > 6 else ""
        pvd_str = row[7].strip().replace(",", ".") if len(row) > 7 else ""
        ruta_correcta = row[10].strip() if len(row) > 10 else ""
        ruta_actual = row[8].strip() if len(row) > 8 else ""
        
        if not ruta_correcta and ruta_actual and not ruta_actual.startswith("public"):
            ruta_correcta = ruta_actual
        
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

print(f"Resumen de actualización Atlantic Pet:")
print(f"Precios actualizados: {updated_prices}")
print(f"Fotos nuevas/corregidas: {updated_photos}")
print(f"Productos eliminados: {deleted_products}")
