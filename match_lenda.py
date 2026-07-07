import os
import json
import re

# Load parsed products
with open("lenda_parsed_draft.json", "r", encoding="utf-8") as f:
    products = json.load(f)

# Load images
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
    
    # Weight match
    w_str = str(prod_weight).lower()
    if f"{w_str}kg" in img_name or f"{w_str} kg" in img_name:
        score += 20
        
    # Words match
    words = [clean_word(w) for w in prod_name.split() if len(w) > 2]
    img_clean = clean_word(img_name)
    for w in words:
        if w in img_clean:
            score += 10
            
    # Some hardcoded aliases
    aliases = {
        "poultry": "aves",
        "pork": "cerdo",
        "fish": "pescado",
        "krill": "pescado",
        "puppy": "cachorro",
        "maxi": "maxi",
        "light": "light",
        "sterilized": "sterilized",
        "senior": "senior",
        "mobility": "mobility",
        "buey": "beef",
        "conejo": "rabbit"
    }
    for eng, esp in aliases.items():
        if esp in [clean_word(x) for x in prod_name.split()] and eng in img_clean:
            score += 15
        if eng in [clean_word(x) for x in prod_name.split()] and esp in img_clean:
            score += 15
            
    return score

matched_products = []
for p in products:
    best_img = None
    best_score = -1
    
    for img in all_images:
        sc = match_score(p["name"], p["weight"], img)
        if sc > best_score:
            best_score = sc
            best_img = img
            
    p["best_image"] = best_img
    p["match_score"] = best_score
    matched_products.append(p)

with open("lenda_matched.json", "w", encoding="utf-8") as f:
    json.dump(matched_products, f, indent=2, ensure_ascii=False)

print(f"Matched {len(matched_products)} products.")
