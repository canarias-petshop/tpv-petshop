import os
import shutil
from supabase import create_client

url = "https://zpzhsmyyyfxqbjjiuana.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwemhzbXl5eWZ4cWJqaml1YW5hIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjEwMzAxNiwiZXhwIjoyMDkxNjc5MDE2fQ.9gNW0JdUf_xnbfEuRnO3WoMPASXQjfqRBkyCjPE0DCY"
supabase = create_client(url, key)

DESTINO_DIR = r"D:\clon vs mode\web-petshop\public\images\productos"

# Obtener todos los productos de OWNAT (ilike para abarcar 'Ownat' y 'OWNAT')
res = supabase.table("productos").select("id, sku, nombre, mascota, familia, subcategoria").ilike("marca", "ownat").execute()
productos = res.data

# Función para ordenar los productos
def sort_key(p):
    mascota = p.get("mascota") or "Z"
    familia = p.get("familia") or "Z"
    nombre = p.get("nombre") or ""
    return (mascota, familia, nombre)

productos_ordenados = sorted(productos, key=sort_key)

print(f"Total productos a procesar de OWNAT: {len(productos_ordenados)}")

updated_count = 0
for idx, p in enumerate(productos_ordenados, start=1):
    nuevo_sku = f"OW-{idx:03d}" # OW-001, OW-002, etc.
    viejo_sku = p.get("sku")
    p_id = p.get("id")
    
    if viejo_sku == nuevo_sku:
        continue # Ya está correcto
        
    # 1. Renombrar en la DB
    supabase.table("productos").update({"sku": nuevo_sku}).eq("id", p_id).execute()
    
    # 2. Renombrar foto si existe (solo importa para Vercel)
    if viejo_sku:
        old_img_path = os.path.join(DESTINO_DIR, f"{viejo_sku}.jpg")
        new_img_path = os.path.join(DESTINO_DIR, f"{nuevo_sku}.jpg")
        
        if os.path.exists(old_img_path):
            try:
                shutil.move(old_img_path, new_img_path)
            except Exception as e:
                print(f"Error renombrando {old_img_path}: {e}")
                
    updated_count += 1
    
print(f"\nMigración de OWNAT completada. Productos con nuevo SKU asignado: {updated_count}")
