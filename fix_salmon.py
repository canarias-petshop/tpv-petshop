import json
import os
import shutil
import re
from supabase import create_client

url = "https://zpzhsmyyyfxqbjjiuana.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwemhzbXl5eWZ4cWJqaml1YW5hIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjEwMzAxNiwiZXhwIjoyMDkxNjc5MDE2fQ.9gNW0JdUf_xnbfEuRnO3WoMPASXQjfqRBkyCjPE0DCY"
supabase = create_client(url, key)

FOTO_ORIGEN = r"C:\Users\truji\OneDrive\PERSONAL\Imágenes\Fotos productos\Amanova\Perro\Seco\Grain Free\amanova-adult-mini-sensitive-salmon-deluxe-calabaz-2kg perro.jpg"
DESTINO_DIR = r"D:\clon vs mode\web-petshop\public\images\productos"

# Fetch DB products
res = supabase.table("productos").select("id, sku, nombre").ilike("nombre", "%Mini Sensitive Salmon Deluxe%").execute()
productos = res.data

updated_count = 0
for p in productos:
    nombre_actual = p["nombre"]
    
    # Arreglar nombre:
    # Ej: "AMANOVA Adult Mini Sensitive Salmon Deluxe&Calabaz 2Kg"
    # Ej: "AMANOVA Adult Mini Sensitive Salmon Deluxe&Calab 800Gr"
    nuevo_nombre = re.sub(r'Deluxe\s*&?\s*Calab[a-z]*', 'Deluxe & Calabaza', nombre_actual, flags=re.IGNORECASE)
    
    if nuevo_nombre != nombre_actual:
        supabase.table("productos").update({"nombre": nuevo_nombre}).eq("id", p["id"]).execute()
        updated_count += 1
        print(f"Nombre arreglado: {nombre_actual} -> {nuevo_nombre}")
    
    # Copiar foto
    sku = p["sku"]
    if sku:
        dest_path = os.path.join(DESTINO_DIR, f"{sku}.jpg")
        shutil.copy2(FOTO_ORIGEN, dest_path)
        print(f"Foto enlazada para el SKU {sku}")

print(f"Total productos arreglados: {updated_count}")
