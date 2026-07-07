import os
import json
import re

with open("lenda_parsed_draft.json", "r", encoding="utf-8") as f:
    products = json.load(f)

img_dir = r"C:\Users\truji\OneDrive\PERSONAL\Imágenes\Fotos productos\Lenda"
all_images = []
for root, dirs, files in os.walk(img_dir):
    for file in files:
        if file.endswith((".png", ".jpg", ".jpeg")):
            all_images.append(os.path.join(root, file))

def clean_word(w):
    return re.sub(r'[^a-z0-9]', '', w.lower())

def match_score(prod_name, prod_weight, img_path):
    img_name = os.path.basename(img_path).lower()
    score = 0
    w_str = str(prod_weight).lower()
    if f"{w_str}kg" in img_name or f"{w_str} kg" in img_name: score += 20
        
    words = [clean_word(w) for w in prod_name.split() if len(w) > 2]
    img_clean = clean_word(img_name)
    for w in words:
        if w in img_clean: score += 10
            
    aliases = {
        "poultry": "aves", "pork": "cerdo", "fish": "pescado", "krill": "pescado",
        "puppy": "cachorro", "maxi": "maxi", "light": "light", "sterilized": "sterilized",
        "senior": "senior", "mobility": "mobility", "buey": "beef", "conejo": "rabbit",
        "cat": "gato", "dog": "perro"
    }
    for eng, esp in aliases.items():
        if esp in [clean_word(x) for x in prod_name.split()] and eng in img_clean: score += 15
        if eng in [clean_word(x) for x in prod_name.split()] and esp in img_clean: score += 15
            
    return score

matched_products = []
for p in products:
    name = p["name"].lower()
    mascota = p.get("mascota", "Perro").lower()
    source = p["source"]
    
    # Define strict folder restrictions
    allowed_folders = []
    
    is_wet = "lata" in name or "pouch" in name or "foodie" in name or "húmedo" in name or "humedo" in name or "merluza" in name or "atún" in name or "caballa" in name or "gambas" in name or "buey" in name and "arandano" not in name
    
    if is_wet:
        if mascota == "gato":
            if "foodie" in name: allowed_folders = ["Gama Lenda Foodie Gatos"]
            else: allowed_folders = ["Gama Lenda Wet Gatos"]
        else:
            if "foodie" in name: allowed_folders = ["Gama Lenda Foddie"]
            else: allowed_folders = ["Gama  Lenda Wet Grain Free"]
    else:
        # Dry food
        if source == "Vet":
            allowed_folders = ["Gama Veterinaria"]
        elif source == "GrainFree":
            if mascota == "gato": allowed_folders = ["Gama Grain Free Gatos"]
            else: allowed_folders = ["Gama Grain Free"]
        elif source == "Tienda":
            if "urban" in name:
                if mascota == "gato": allowed_folders = ["Gama Urban Gatos"]
                else: allowed_folders = ["Gama Urban"]
            elif "lc" in name or "country meat" in name or "performance" in name:
                allowed_folders = ["Gama Lc"]
            else:
                if mascota == "gato":
                    if "grain free" in name or "gf" in name: allowed_folders = ["Gama Lenda Gatos Original Sin Cereales"]
                    else: allowed_folders = ["Gama Lenda Gatos Original Sin Cereales"] # All Lenda original cats seem to be here
                else:
                    allowed_folders = ["Gama Lenda"]
                    
    # Now find best match ONLY within allowed folders
    best_img = None
    best_score = -1
    
    for img in all_images:
        folder_name = os.path.basename(os.path.dirname(img))
        # Strict filter: the folder name must match one of the allowed folders exactly (or be very close)
        if any(clean_word(af) in clean_word(folder_name) for af in allowed_folders):
            # Also enforce Mascota restriction strictly by looking at the parent directory
            parent_folder = os.path.basename(os.path.dirname(os.path.dirname(img))).lower()
            grandparent = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(img)))).lower()
            img_mascota = parent_folder if "gato" in parent_folder or "perro" in parent_folder else grandparent
            if (mascota == "gato" and "gato" not in img_mascota) or (mascota == "perro" and "perro" not in img_mascota):
                continue
                
            sc = match_score(p["name"], p["weight"], img)
            if sc > best_score:
                best_score = sc
                best_img = img
                
    p["best_image"] = best_img
    p["match_score"] = best_score
    p["allowed_folders"] = allowed_folders
    matched_products.append(p)

with open("lenda_matched_strict.json", "w", encoding="utf-8") as f:
    json.dump(matched_products, f, indent=2, ensure_ascii=False)

print(f"Strict matched {len(matched_products)} products.")
