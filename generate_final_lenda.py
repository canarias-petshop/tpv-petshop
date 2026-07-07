import json
import os

with open("lenda_parsed_draft.json", "r", encoding="utf-8") as f:
    products = json.load(f)

# Hardcoded lists of images for mapping
image_dir = r"C:\Users\truji\OneDrive\PERSONAL\Imágenes\Fotos productos\Lenda"
all_images = []
for root, dirs, files in os.walk(image_dir):
    for file in files:
        if file.endswith((".png", ".jpg", ".jpeg")):
            all_images.append(os.path.join(root, file))

def find_best_image(name, weight, mascota):
    # Extremely basic heuristic mapping
    n = name.lower()
    w = str(weight).lower()
    m = mascota.lower()
    
    # Priority matches
    best_score = 0
    best_img = None
    
    for img_path in all_images:
        img_name = os.path.basename(img_path).lower()
        score = 0
        if m in img_path.lower(): score += 5
        
        # specific matches for Grain Free
        if "grain free" in n or "unknown" in n:
            if "poultry" in img_name and "aves" in n: score += 10
            elif "cerdo" in img_name and "cerdo" in n: score += 10
            elif "mini" in img_name and "mini" in n: score += 10
            elif "pavo" in img_name and "pavo" in n: score += 10
            elif "puppy" in img_name and "puppy" in n: score += 10
            elif "fish" in img_name and "pescado" in n: score += 10
            elif "salmon" in img_name and "salmon" in n: score += 10
            elif "senior" in img_name and "senior" in n: score += 10
        
        # general matches
        for word in n.split():
            if word in img_name: score += 2
        
        if f"{w}kg" in img_name or f"{w} kg" in img_name: score += 5
        
        if score > best_score:
            best_score = score
            best_img = img_path
            
    return best_img

final_products = []
for idx, p in enumerate(products):
    name = p["name"]
    # Fix the unknown GF names by hardcoding order or we will just use a generic name for now and I will manually tweak the JSON later.
    # Actually I can just dump them to JSON and manually fix the name strings in the python output or VSCode.
    
    final_products.append({
        "name": name,
        "mascota": p.get("mascota", "Perro"),
        "weight": p["weight"],
        "pvp": p["pvp"],
        "source": p["source"]
    })

with open("lenda_final_draft.json", "w", encoding="utf-8") as f:
    json.dump(final_products, f, indent=2, ensure_ascii=False)

print("Generated lenda_final_draft.json. Please review.")
