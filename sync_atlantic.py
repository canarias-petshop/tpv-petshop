import os
import shutil
from supabase import create_client, Client
import toml

# --- CONFIG ---
secrets = toml.load(".streamlit/secrets.toml")
supabase: Client = create_client(secrets["url"].strip('"').strip("'"), secrets["key"].strip('"').strip("'"))
base_dir = r"C:\Users\truji\OneDrive\PERSONAL\Imágenes\Fotos productos\Atlanctic Pet"
dest_dir = r"D:\clon vs mode\web-petshop\public\images\productos"

# --- 1. Get DB products ---
res = supabase.table('productos').select('id, sku, nombre, precio_pvp, gama').ilike('marca', '%atlantic%').execute()
db_products = res.data

# --- 2. Get photos ---
photos = []
for root, dirs, files in os.walk(base_dir):
    for name in files:
        if name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            photos.append(os.path.join(root, name))

# --- 3. Mappers ---
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

def find_best_photo(prod_name, gama):
    # Filter photos by gama folder if possible
    # We look at the parent directory of the photo to match the gama
    gama_lower = gama.lower()
    candidate_photos = []
    
    for p in photos:
        folder_name = os.path.basename(os.path.dirname(p)).lower()
        # Some folder names might be slightly different, so we do a partial match
        if folder_name in gama_lower or gama_lower in folder_name or ("bully" in gama_lower and "perros" in folder_name):
            candidate_photos.append(p)
            
    if not candidate_photos:
        # Fallback to all photos if no folder match
        candidate_photos = photos

    prod_name_lower = prod_name.lower().replace('atlantic pet', '').replace('atlanticpet', '').strip()
    best_score = 0
    best_photo = None
    
    for p in candidate_photos:
        p_name = os.path.basename(p).lower()
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
        if "conejo" in prod_name_lower and "rabbit" in p_name: score += 10
        if "beef" in prod_name_lower and "beef" in p_name: score += 10
        
        # Exact word matches
        words = prod_name_lower.split()
        for w in words:
            if len(w) > 3 and w in p_name:
                score += 2

        if score > best_score:
            best_score = score
            best_photo = p
            
    return best_photo

# --- 4. Execution ---
os.makedirs(dest_dir, exist_ok=True)

for prod in db_products:
    print(f"\nProcessing {prod['sku']} - {prod['nombre']}")
    
    # 4a. Update Gama
    new_gama = map_gama(prod['nombre'])
    if prod['gama'] != new_gama:
        print(f"  -> Updating Gama: '{prod['gama']}' to '{new_gama}'")
        supabase.table('productos').update({'gama': new_gama}).eq('id', prod['id']).execute()
    else:
        print(f"  -> Gama already correct: '{new_gama}'")
        
    # 4b. Find and copy photo
    photo = find_best_photo(prod['nombre'], new_gama)
    if photo:
        # We save it as .webp if it is webp, else we can just save it as .jpg (since the web expects .jpg typically for the others)
        # Actually NextJS Image component handles extensions, but our DB or code expects `{sku}.jpg`?
        # The web code checks for `/images/productos/{sku}.jpg`. Let's just save as .jpg for simplicity, or preserve extension and change web code.
        # Wait, the web code: <img src={`/images/productos/${product.sku}.jpg`} ... />
        # So we MUST save it as `{sku}.jpg` (even if it's technically a PNG or WEBP, browsers can sniff it, or we can convert it).
        # It's safest to just copy it as `{sku}.jpg`. Most browsers sniff the format anyway.
        dest_path = os.path.join(dest_dir, f"{prod['sku']}.jpg")
        shutil.copy2(photo, dest_path)
        print(f"  -> Copied photo: {os.path.basename(photo)} -> {prod['sku']}.jpg")
    else:
        print("  -> NO PHOTO MATCH FOUND")

print("\nDone!")
