import json
import PyPDF2
import re

PDF_PATH = r"C:\Users\truji\OneDrive\Documentos\ANIMALARIUM\LISTADO DE PRECIOS PROVEEDORES\ZOTECNIA\tarifas-amanova-2025-tienda.pdf"
DB_DUMP = "amanova_db_dump.json"

# Extraer texto
text_all = ""
with open(PDF_PATH, "rb") as f:
    reader = PyPDF2.PdfReader(f)
    for p in reader.pages:
        text_all += p.extract_text() + "\n"

# Parsear productos del PDF
# Formato: S-AMJ74AR10 8413037332082 Amv Adult Digestive Divine Rabbit & Calabaza 10Kg 77,62 46,37
pdf_products = {}
pattern = re.compile(r"([A-Z0-9-]+)\s+(\d{13})\s+(.+?)\s+(\d+,\d{2})\s+(\d+,\d{2})")
for match in pattern.finditer(text_all):
    sku = match.group(1).strip()
    ean = match.group(2).strip()
    name = match.group(3).strip()
    pvp = float(match.group(4).replace(",", "."))
    pvt = float(match.group(5).replace(",", "."))
    
    pdf_products[sku] = {
        "ean": ean,
        "name": name,
        "pvp": pvp,
        "pvt": pvt
    }

# Cargar DB
with open(DB_DUMP, "r", encoding="utf-8") as f:
    productos_db = json.load(f)

# Cruzar datos y generar reporte
discrepancias = []
no_en_pdf = []
match_count = 0

for prod in productos_db:
    sku = prod.get("sku", "")
    if sku in pdf_products:
        match_count += 1
        pdf_prod = pdf_products[sku]
        db_pvp = float(prod.get("precio_pvp") or 0.0)
        
        # Comparar PVP
        if abs(db_pvp - pdf_prod["pvp"]) > 0.01:
            discrepancias.append({
                "sku": sku,
                "nombre_db": prod.get("nombre"),
                "pvp_db": db_pvp,
                "pvp_pdf": pdf_prod["pvp"]
            })
    else:
        # Intentar por EAN si el SKU falla
        ean_db = str(prod.get("codigo_barras", ""))
        found_by_ean = False
        for p_sku, p_data in pdf_products.items():
            if p_data["ean"] == ean_db:
                found_by_ean = True
                match_count += 1
                db_pvp = float(prod.get("precio_pvp") or 0.0)
                if abs(db_pvp - p_data["pvp"]) > 0.01:
                    discrepancias.append({
                        "sku": p_sku,
                        "nombre_db": prod.get("nombre"),
                        "pvp_db": db_pvp,
                        "pvp_pdf": p_data["pvp"]
                    })
                break
        
        if not found_by_ean:
            no_en_pdf.append(prod)

# Productos en PDF que no están en la DB
skus_db = {p.get("sku") for p in productos_db}
eans_db = {str(p.get("codigo_barras")) for p in productos_db}
no_en_db = []
for p_sku, p_data in pdf_products.items():
    if p_sku not in skus_db and p_data["ean"] not in eans_db:
        no_en_db.append(p_data)

# Escribir el reporte
md = "# Reporte de Anomalías AMANOVA (Fase 2: Precios)\n\n"
md += f"**Total de productos cruzados exitosamente:** {match_count}\n\n"

md += "## 1. Discrepancias de Precios (PVP)\n"
if discrepancias:
    for d in discrepancias:
        md += f"- **{d['sku']}** - {d['nombre_db']}\n"
        md += f"  - Precio en DB: **{d['pvp_db']} €**\n"
        md += f"  - Precio en PDF: **{d['pvp_pdf']} €**\n"
else:
    md += "✅ Todos los precios cruzados coinciden perfectamente.\n"

md += "\n## 2. Productos en la Base de Datos que NO están en el PDF\n"
if no_en_pdf:
    for p in no_en_pdf:
        md += f"- {p.get('sku')} - {p.get('nombre')}\n"
else:
    md += "✅ Todos los productos de la BD se encontraron en el PDF.\n"

md += "\n## 3. Productos en el PDF que NO están en la Base de Datos\n"
if no_en_db:
    for p in no_en_db:
        md += f"- {p['name']} (EAN: {p['ean']})\n"
else:
    md += "✅ Todos los productos del PDF están en la BD.\n"

with open(r"C:\Users\truji\.gemini\antigravity\brain\bf96cb32-208d-4f97-9525-9a35c9aef1d8\reporte_precios.md", "w", encoding="utf-8") as f:
    f.write(md)

print(f"Reporte de precios generado. Discrepancias: {len(discrepancias)}")
