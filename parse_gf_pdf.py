import pdfplumber
import json
import re
import csv
import os

pdf_path = r"C:\Users\truji\OneDrive\Documentos\ANIMALARIUM\LISTADO DE PRECIOS PROVEEDORES\FEEDCAN\Lenda\Tarifa Lenda 2026 Nueva Gama - Grain Free PVD.pdf"
products = []

try:
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = text.split("\n")
                current_product_1 = None
                current_product_2 = None
                
                for line in lines:
                    if "Lenda " in line:
                        # Extract product names. E.g. "Lenda Grain Free Todo Aves Lenda Grain Free Salmón"
                        parts = line.split(" Lenda ")
                        if len(parts) > 0:
                            current_product_1 = "Lenda " + parts[0].replace("Lenda ", "").strip()
                        if len(parts) > 1:
                            current_product_2 = "Lenda " + parts[1].strip()
                            
                    # Match weight and prices: 2KG 15,40€ 23,95€ 2KG 13,50€ 20,95€
                    matches = re.findall(r'(\d+(?:,\d+)?)\s*(KG|kg|g|gr|ml|L)\s+(\d+,\d{2})\s*?\s+(\d+,\d{2})', line.replace('€', ''))
                    if matches:
                        # If there's 1 match, it belongs to product 1
                        if len(matches) >= 1 and current_product_1:
                            products.append({
                                "name": current_product_1,
                                "weight": matches[0][0],
                                "pvp": matches[0][3].replace(',', '.')
                            })
                        # If there's 2 matches, second belongs to product 2
                        if len(matches) >= 2 and current_product_2:
                            products.append({
                                "name": current_product_2,
                                "weight": matches[1][0],
                                "pvp": matches[1][3].replace(',', '.')
                            })
                            
except Exception as e:
    print(f"Error parsing PDF: {e}")

# Generate CSV directly
with open("lenda_grain_free_revision.csv", "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.writer(f, delimiter=';')
    writer.writerow([
        "Nombre Original PDF",
        "Gama Extraída",
        "Peso Sugerido Web",
        "PVP",
        "Ruta de Foto Asignada por el Bot",
        "Foto Correcta? (SI/NO)",
        "Ruta CORRECTA de Foto (si la anterior es NO)"
    ])
    
    img_dir = r"C:\Users\truji\OneDrive\PERSONAL\Imágenes\Fotos productos\Lenda"
    all_images = []
    for root, _, files in os.walk(img_dir):
        for file in files:
            if file.endswith((".png", ".jpg", ".jpeg")):
                all_images.append(os.path.join(root, file))
                
    for p in products:
        name_pdf = p["name"]
        gama = "Grain Free"
        
        # Formatear peso
        peso_raw = p["weight"]
        try:
            val = float(peso_raw.replace(',', '.'))
            if val < 1.0:
                peso_sugerido = f"{int(val * 1000)} g"
            elif val == int(val):
                peso_sugerido = f"{int(val)} kg"
            else:
                peso_sugerido = f"{val} kg"
        except:
            peso_sugerido = f"{peso_raw} kg"
            
        pvp = p["pvp"].replace(".", ",")
        
        # Buscar foto "a ciegas" (o dejar sin foto para que rellene)
        # Find best image in Gama Grain Free
        best_img = "SIN FOTO"
        best_score = 0
        for img in all_images:
            if "Grain Free" in img:
                img_name = os.path.basename(img).lower()
                n_lower = name_pdf.lower()
                score = 0
                if "salmon" in n_lower and "salmon" in img_name: score+=10
                if "pescado" in n_lower and "fish" in img_name: score+=10
                if "pavo" in n_lower and "pavo" in img_name: score+=10
                if "cerdo" in n_lower and "cerdo" in img_name: score+=10
                if "conejo" in n_lower and "senior" in img_name and "senior" in n_lower: score+=10
                if "aves" in n_lower and "poultry" in img_name: score+=10
                if "puppy" in n_lower and "puppy" in img_name: score+=10
                
                if score > best_score:
                    best_score = score
                    best_img = img

        writer.writerow([
            name_pdf,
            gama,
            peso_sugerido,
            pvp,
            best_img,
            "",
            ""
        ])

print(f"CSV lenda_grain_free_revision.csv generado con {len(products)} productos.")
