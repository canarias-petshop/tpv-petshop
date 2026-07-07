import json
import PyPDF2
import re
from supabase import create_client

# Supabase config
url = "https://zpzhsmyyyfxqbjjiuana.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwemhzbXl5eWZ4cWJqaml1YW5hIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjEwMzAxNiwiZXhwIjoyMDkxNjc5MDE2fQ.9gNW0JdUf_xnbfEuRnO3WoMPASXQjfqRBkyCjPE0DCY"
supabase = create_client(url, key)

PDF_PATH = r"C:\Users\truji\OneDrive\Documentos\ANIMALARIUM\LISTADO DE PRECIOS PROVEEDORES\ZOTECNIA\tarifas-amanova-2025-tienda.pdf"

# Extract text from PDF
text_all = ""
with open(PDF_PATH, "rb") as f:
    reader = PyPDF2.PdfReader(f)
    for p in reader.pages:
        text_all += p.extract_text() + "\n"

# Parse PDF
pdf_products = {}
pattern = re.compile(r"([A-Z0-9-]+)\s+(\d{13})\s+(.+?)\s+(\d+,\d{2})\s+(\d+,\d{2})")
for match in pattern.finditer(text_all):
    sku = match.group(1).strip()
    ean = match.group(2).strip()
    pvp = float(match.group(4).replace(",", "."))
    
    pdf_products[sku] = {"ean": ean, "pvp": pvp}

# Fetch DB products
res = supabase.table("productos").select("*").eq("marca", "AMANOVA").execute()
productos_db = res.data

updated_count = 0

# Helper to find divisor based on matching Caja item in DB
def find_divisor_from_db(ean, base_name):
    for p in productos_db:
        if p.get("codigo_barras") == ean and "caja" in p.get("nombre", "").lower():
            match = re.search(r"caja\s*(\d+)", p.get("nombre", "").lower())
            if match:
                return int(match.group(1))
    return 1

for prod in productos_db:
    db_pvp = float(prod.get("precio_pvp") or 0.0)
    sku = prod.get("sku", "")
    ean = str(prod.get("codigo_barras", ""))
    
    # Try finding in PDF by SKU then by EAN
    pdf_pvp = None
    if sku in pdf_products:
        pdf_pvp = pdf_products[sku]["pvp"]
    else:
        for p_sku, p_data in pdf_products.items():
            if p_data["ean"] == ean:
                pdf_pvp = p_data["pvp"]
                break
                
    if pdf_pvp:
        # Determine correct price to apply
        final_pvp = pdf_pvp
        
        # Si es "(Unidad)" y hay diferencia grande, deducimos que el PDF nos da el precio de caja
        nombre = prod.get("nombre", "")
        if "(unidad)" in nombre.lower():
            divisor = find_divisor_from_db(ean, nombre)
            if divisor > 1:
                final_pvp = round(pdf_pvp / divisor, 2)
            else:
                # Si no encontramos divisor en la DB, adivinamos basándonos en la relación
                # Si el PDF dice 17.4 y la DB dice 1.45, es 12
                # Pero si la DB es 0.0, asumiremos 12 o 24 según el caso
                if db_pvp > 0:
                    ratio = pdf_pvp / db_pvp
                    if 10 < ratio < 14: final_pvp = round(pdf_pvp / 12, 2)
                    elif 20 < ratio < 26: final_pvp = round(pdf_pvp / 24, 2)
                    elif 8 < ratio < 11: final_pvp = round(pdf_pvp / 10, 2)
        
        # Si el precio es exactamente el mismo o muy cercano, no hacemos update
        if abs(db_pvp - final_pvp) > 0.02:
            supabase.table("productos").update({"precio_pvp": final_pvp}).eq("id", prod["id"]).execute()
            updated_count += 1
            print(f"Actualizado: {nombre} | Antiguo: {db_pvp} -> Nuevo: {final_pvp}")

print(f"\nTotal de productos actualizados en Supabase: {updated_count}")
