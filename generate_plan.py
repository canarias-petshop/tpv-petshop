import pandas as pd
import os
import difflib

# 1. Fetch DB records
from supabase import create_client, Client
import toml
secrets = toml.load(".streamlit/secrets.toml")
supabase: Client = create_client(secrets["url"].strip('"').strip("'"), secrets["key"].strip('"').strip("'"))
res = supabase.table('productos').select('id, sku, nombre, precio_pvp, gama').ilike('marca', '%atlantic%').execute()
db_products = res.data

# 2. Get photos
base_dir = r"C:\Users\truji\OneDrive\PERSONAL\Imágenes\Fotos productos\Atlanctic Pet"
photos = []
for root, dirs, files in os.walk(base_dir):
    for name in files:
        if name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            photos.append(os.path.join(root, name))

# Match
def find_best_photo(prod_name):
    prod_name_lower = prod_name.lower().replace('atlantic pet', '').replace('atlanticpet', '').strip()
    
    best_score = 0
    best_photo = None
    
    for p in photos:
        p_name = os.path.basename(p).lower()
        
        # very basic heuristics
        score = 0
        if "puppy" in prod_name_lower and "puppy" in p_name: score += 10
        if "adult" in prod_name_lower and "adult" in p_name: score += 10
        if "kitten" in prod_name_lower and "kitten" in p_name: score += 10
        if "steril" in prod_name_lower and "steril" in p_name: score += 10
        if "chicken" in prod_name_lower and "chicken" in p_name: score += 10
        if "pollo" in prod_name_lower and "chicken" in p_name: score += 10
        if "salmon" in prod_name_lower and "salmon" in p_name: score += 10
        if "salmón" in prod_name_lower and "salmon" in p_name: score += 10
        if "turkey" in prod_name_lower and "turkey" in p_name: score += 10
        if "pavo" in prod_name_lower and "turkey" in p_name: score += 10
        if "lamb" in prod_name_lower and "lamb" in p_name: score += 10
        if "cordero" in prod_name_lower and "lamb" in p_name: score += 10
        if "fish" in prod_name_lower and "fish" in p_name: score += 10
        if "bully" in prod_name_lower and "bully" in p_name: score += 10
        if "oceanic" in prod_name_lower and "oceanic" in p_name: score += 10
        if "grassland" in prod_name_lower and "grassland" in p_name: score += 10
        if "skin" in prod_name_lower and "skin" in p_name: score += 10
        if "wilderness" in prod_name_lower and "wilderness" in p_name: score += 10
        if "light" in prod_name_lower and "light" in p_name: score += 10
        if "exquisite" in prod_name_lower and "exquisite" in p_name: score += 10
        if "rabbit" in prod_name_lower and "rabbit" in p_name: score += 10
        
        if score > best_score:
            best_score = score
            best_photo = p
            
    return best_photo

# Map gama logic
def map_gama(prod_name):
    n = prod_name.lower()
    if 'gato' in n or 'cat' in n:
        if 'classic supreme' in n: return 'CLASSIC SUPREME GATO'
        elif 'ultra' in n or 'grain free' in n: return 'ULTRA PREMIUN RECETA GRAIN FREE'
        else: return 'PREMIUN RECETA GATOS'
    else:
        if 'classic supreme' in n: return 'CLASSIC SUPREME'
        elif 'bully' in n: return 'Atlantic Pet Especial Bully perro'
        elif 'ultra' in n: return 'ULTRA PREMIUN GRAIN FREE'
        elif 'grain free' in n or 'sin cereales' in n: return 'SUPER PREMIUN RECETA GRAIN FREE'
        else: return 'PREMIUN RECETAS'

with open("plan_data.txt", "w", encoding="utf-8") as f:
    for prod in db_products:
        gama = map_gama(prod['nombre'])
        photo = find_best_photo(prod['nombre'])
        pname = os.path.basename(photo) if photo else "NO MATCH"
        f.write(f"[{prod['sku']}] {prod['nombre']} -> Gama: {gama} | Photo: {pname}\n")
