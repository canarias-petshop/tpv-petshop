import json
import os
import shutil
from supabase import create_client

url = "https://zpzhsmyyyfxqbjjiuana.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwemhzbXl5eWZ4cWJqaml1YW5hIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjEwMzAxNiwiZXhwIjoyMDkxNjc5MDE2fQ.9gNW0JdUf_xnbfEuRnO3WoMPASXQjfqRBkyCjPE0DCY"
supabase = create_client(url, key)

OLD_SKU = "AM-011"
NEW_SKU = "S-AMJ91NS8A"
DESTINO_DIR = r"D:\clon vs mode\web-petshop\public\images\productos"

# Renombrar foto local en el servidor web
old_img = os.path.join(DESTINO_DIR, f"{OLD_SKU}.jpg")
new_img = os.path.join(DESTINO_DIR, f"{NEW_SKU}.jpg")

if os.path.exists(old_img):
    shutil.move(old_img, new_img)
    print(f"Foto renombrada en web-petshop de {OLD_SKU}.jpg a {NEW_SKU}.jpg")
else:
    print(f"La foto {old_img} no existía. Voy a usar la del 2kg.")
    origen_2kg = os.path.join(DESTINO_DIR, "S-AMJ91NS02.jpg")
    if os.path.exists(origen_2kg):
        shutil.copy2(origen_2kg, new_img)
        print("Copiada foto del 2kg al nuevo SKU.")

# Actualizar SKU en la BD
res = supabase.table("productos").select("id, nombre").ilike("nombre", "%Mini Sensitive Salmon Deluxe & Calabaza 800Gr%").execute()
if res.data:
    p_id = res.data[0]["id"]
    
    # Podría ser que su precio también falte, revisemos si en el volcado del pdf existe
    # Según el comportamiento habitual, actualizamos solo el SKU
    supabase.table("productos").update({"sku": NEW_SKU}).eq("id", p_id).execute()
    print(f"SKU actualizado en Supabase para {res.data[0]['nombre']} -> {NEW_SKU}")
else:
    # Buscar por el antiguo SKU
    res2 = supabase.table("productos").select("id, nombre").eq("sku", OLD_SKU).execute()
    if res2.data:
        p_id = res2.data[0]["id"]
        supabase.table("productos").update({"sku": NEW_SKU}).eq("id", p_id).execute()
        print(f"SKU actualizado en Supabase para {res2.data[0]['nombre']} -> {NEW_SKU}")
    else:
        print("No se encontró el producto en la BD.")
