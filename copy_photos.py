import os
import json
import difflib
import shutil
import re

FOTOS_DIR = r"C:\Users\truji\OneDrive\PERSONAL\Imágenes\Fotos productos\Amanova"
DESTINO_DIR = r"D:\clon vs mode\web-petshop\public\images\productos"
DB_DUMP = "amanova_db_dump.json"

if not os.path.exists(DESTINO_DIR):
    os.makedirs(DESTINO_DIR)

with open(DB_DUMP, "r", encoding="utf-8") as f:
    productos_db = json.load(f)

def normalize_name(name):
    return name.lower().replace("amanova", "").replace("amv", "").replace("-", " ").replace("_", " ").strip()

# Escanear fotos
fotos_locales = []
for root, dirs, files in os.walk(FOTOS_DIR):
    for file in files:
        if file.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
            fotos_locales.append({
                "filename": file,
                "name_clean": normalize_name(os.path.splitext(file)[0]),
                "full_path": os.path.join(root, file),
                "matched_sku": None
            })

# 1. Emparejar directos
match_map = {} # base_name_sin_peso -> foto path

for prod in productos_db:
    prod_name_norm = normalize_name(prod.get("nombre", ""))
    best_match = None
    best_ratio = 0
    
    for foto in fotos_locales:
        ratio = difflib.SequenceMatcher(None, prod_name_norm, foto["name_clean"]).ratio()
        foto_words = set(foto["name_clean"].split())
        prod_words = set(prod_name_norm.split())
        if len(foto_words) > 0 and foto_words.issubset(prod_words):
            ratio = max(ratio, 0.9)
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = foto
            
    if best_match and best_ratio > 0.65:
        # Copiar imagen al SKU
        sku = prod.get("sku")
        if sku:
            # En web-petshop usan jpg
            dest_path = os.path.join(DESTINO_DIR, f"{sku}.jpg")
            shutil.copy2(best_match["full_path"], dest_path)
            
            # Guardar para poder clonar a los hermanos
            base_name = re.sub(r'\b\d+(kg|gr|g|ud)\b.*', '', prod_name_norm, flags=re.IGNORECASE).strip()
            match_map[base_name] = best_match["full_path"]

# 2. Clonar huérfanos (variantes de peso/cajas)
clonados = 0
sin_foto = 0

for prod in productos_db:
    sku = prod.get("sku")
    if not sku: continue
    
    dest_path = os.path.join(DESTINO_DIR, f"{sku}.jpg")
    if not os.path.exists(dest_path):
        # Buscar hermano
        prod_name_norm = normalize_name(prod.get("nombre", ""))
        base_name = re.sub(r'\b\d+(kg|gr|g|ud)\b.*', '', prod_name_norm, flags=re.IGNORECASE).strip()
        
        # Buscar la mejor coincidencia en el map de hermanos
        best_brother = None
        best_ratio = 0
        for b_name, b_path in match_map.items():
            ratio = difflib.SequenceMatcher(None, base_name, b_name).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_brother = b_path
                
        if best_brother and best_ratio > 0.8:
            shutil.copy2(best_brother, dest_path)
            clonados += 1
        else:
            sin_foto += 1

print(f"Fotos copiadas directamente y clonadas para variaciones.")
print(f"Productos con foto asignada por clonación: {clonados}")
print(f"Productos que siguen sin foto: {sin_foto}")
