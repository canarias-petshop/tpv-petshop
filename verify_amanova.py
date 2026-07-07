import os
import json
import difflib

# Rutas
FOTOS_DIR = r"C:\Users\truji\OneDrive\PERSONAL\Imágenes\Fotos productos\Amanova"
DB_DUMP = "amanova_db_dump.json"

# Cargar DB
with open(DB_DUMP, "r", encoding="utf-8") as f:
    productos_db = json.load(f)

# Función de normalización
def normalize_name(name):
    n = name.lower().replace("amanova", "").replace("amv", "").replace("-", " ").replace("_", " ").strip()
    return n

# Escanear fotos
fotos_locales = []
for root, dirs, files in os.walk(FOTOS_DIR):
    for file in files:
        if file.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
            path_parts = root.replace(FOTOS_DIR, "").strip("\\").split("\\")
            mascota_dir = path_parts[0] if len(path_parts) > 0 else "Desconocido"
            tipo_dir = path_parts[1] if len(path_parts) > 1 else "Desconocido"
            
            fotos_locales.append({
                "filename": file,
                "name_clean": normalize_name(os.path.splitext(file)[0]),
                "mascota_dir": mascota_dir,
                "tipo_dir": tipo_dir,
                "full_path": os.path.join(root, file),
                "matched": False
            })


# Realizar emparejamiento (Fuzzy Matching)
anomalias = []
db_sin_foto = []
match_log = []

for prod in productos_db:
    prod_name_norm = normalize_name(prod.get("nombre", ""))
    
    # Buscar mejor coincidencia
    best_match = None
    best_ratio = 0
    
    for foto in fotos_locales:
        if foto["matched"]: continue
        
        ratio = difflib.SequenceMatcher(None, prod_name_norm, foto["name_clean"]).ratio()
        
        # También chequear si todas las palabras del nombre de la foto están en el producto
        foto_words = set(foto["name_clean"].replace("-", " ").replace("_", " ").split())
        prod_words = set(prod_name_norm.replace("-", " ").replace("_", " ").split())
        
        if len(foto_words) > 0 and foto_words.issubset(prod_words):
            ratio = max(ratio, 0.9) # Fuerte coincidencia si las palabras están contenidas
            
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = foto
            
    if best_match and best_ratio > 0.65:
        best_match["matched"] = True
        
        # Verificar categorías
        db_mascota = prod.get("mascota", "Desconocido")
        db_familia = prod.get("familia", "Desconocido")
        db_subcat = prod.get("subcategoria", "Desconocido")
        
        dir_mascota = best_match["mascota_dir"]
        dir_tipo = best_match["tipo_dir"]
        
        # Validar mascota
        error_mascota = False
        if dir_mascota.lower() != db_mascota.lower() and dir_mascota != "Desconocido":
            error_mascota = True
            
        # Validar familia/tipo (Húmedo, Seco, Snack)
        error_tipo = False
        tipo_map = {
            "húmedo": ["alimento húmedo", "pienso húmedo", "pouch", "lata"],
            "seco": ["alimentación seca", "pienso seco", "alimentación"],
            "snack": ["snack", "snacks", "premios"]
        }
        
        tipo_esperado = tipo_map.get(dir_tipo.lower(), [])
        if dir_tipo != "Desconocido":
            match_tipo = False
            for t in tipo_esperado:
                if t in db_familia.lower() or t in db_subcat.lower():
                    match_tipo = True
                    break
            if not match_tipo:
                # Comprobación laxa extra (si familia es 'Alimentación' asume seco)
                if dir_tipo.lower() == "seco" and db_familia.lower() == "alimentación":
                    pass
                else:
                    error_tipo = True
                
        if error_mascota or error_tipo:
            anomalias.append({
                "tipo": "Error de Categoría",
                "producto_db": prod["nombre"],
                "foto": best_match["filename"],
                "detalle": f"DB: {db_mascota} / {db_familia} | FOTO: {dir_mascota} / {dir_tipo}"
            })
    else:
        db_sin_foto.append(prod)

fotos_huerfanas = [f for f in fotos_locales if not f["matched"]]

# Generar Markdown
md = "# Reporte de Anomalías AMANOVA (Fase 1: Fotos y Categorías)\n\n"

md += "## 1. Discrepancias de Categorización\n"
if anomalias:
    for a in anomalias:
        md += f"- **Producto:** {a['producto_db']}\n  - **Foto emparejada:** {a['foto']}\n  - **Conflicto:** {a['detalle']}\n"
else:
    md += "✅ No se encontraron conflictos de categorización entre la base de datos y la ubicación de las fotos.\n"

md += "\n## 2. Productos en DB sin foto asociada\n"
if db_sin_foto:
    for p in db_sin_foto:
        md += f"- {p['nombre']}\n"
else:
    md += "✅ Todos los productos en la base de datos encontraron una foto.\n"

md += "\n## 3. Fotos en local sin producto en DB (Fotos Huérfanas)\n"
if fotos_huerfanas:
    for f in fotos_huerfanas:
        md += f"- {f['mascota_dir']}/{f['tipo_dir']}/{f['filename']}\n"
else:
    md += "✅ Todas las fotos locales se emparejaron con un producto.\n"

with open("reporte_anomalias_amanova.md", "w", encoding="utf-8") as f:
    f.write(md)

print(f"Reporte generado. Anomalías: {len(anomalias)}, Sin foto: {len(db_sin_foto)}, Huérfanas: {len(fotos_huerfanas)}")
