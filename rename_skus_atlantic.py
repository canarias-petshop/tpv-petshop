import os
import shutil
from supabase import create_client

url = "https://zpzhsmyyyfxqbjjiuana.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwemhzbXl5eWZ4cWJqaml1YW5hIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjEwMzAxNiwiZXhwIjoyMDkxNjc5MDE2fQ.9gNW0JdUf_xnbfEuRnO3WoMPASXQjfqRBkyCjPE0DCY"
supabase = create_client(url, key)

DESTINO_DIR = r"D:\clon vs mode\web-petshop\public\images\productos"

res = supabase.table("productos").select("id, sku, nombre, mascota, familia, subcategoria").ilike("marca", "atlantic pet").execute()
productos = res.data

def sort_key(p):
    mascota = p.get("mascota") or "Z"
    familia = p.get("familia") or "Z"
    nombre = p.get("nombre") or ""
    return (mascota, familia, nombre)

productos_ordenados = sorted(productos, key=sort_key)

print(f"Total productos a procesar de Atlantic Pet: {len(productos_ordenados)}")

# Pass 1: rename files to temp to avoid collisions, AND rename in DB to TEMP
temp_mappings = []
for idx, p in enumerate(productos_ordenados, start=1):
    nuevo_sku = f"ATP-{idx:03d}"
    temp_sku = f"TEMP-{nuevo_sku}"
    viejo_sku = p.get("sku")
    p_id = p.get("id")
    
    # Update DB to TEMP sku to avoid unique constraint collision
    supabase.table("productos").update({"sku": temp_sku}).eq("id", p_id).execute()
    
    if viejo_sku:
        old_img_path = os.path.join(DESTINO_DIR, f"{viejo_sku}.jpg")
        temp_img_path = os.path.join(DESTINO_DIR, f"{temp_sku}.jpg")
        if os.path.exists(old_img_path):
            shutil.move(old_img_path, temp_img_path)
            temp_mappings.append((temp_img_path, os.path.join(DESTINO_DIR, f"{nuevo_sku}.jpg")))

# Pass 2: update DB from TEMP to FINAL and rename temp files to final
updated_count = 0
for idx, p in enumerate(productos_ordenados, start=1):
    nuevo_sku = f"ATP-{idx:03d}"
    temp_sku = f"TEMP-{nuevo_sku}"
    p_id = p.get("id")
    
    supabase.table("productos").update({"sku": nuevo_sku}).eq("id", p_id).execute()
    updated_count += 1

for temp_path, final_path in temp_mappings:
    if os.path.exists(final_path):
        os.remove(final_path) # Just in case a leftover exists
    shutil.move(temp_path, final_path)

print(f"\nMigración de Atlantic Pet completada. Productos con nuevo SKU asignado: {updated_count}")
