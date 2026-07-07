import csv
import re
from supabase import create_client

url = "https://zpzhsmyyyfxqbjjiuana.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwemhzbXl5eWZ4cWJqaml1YW5hIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjEwMzAxNiwiZXhwIjoyMDkxNjc5MDE2fQ.9gNW0JdUf_xnbfEuRnO3WoMPASXQjfqRBkyCjPE0DCY"
supabase = create_client(url, key)

res = supabase.table("productos").select("*").ilike("marca", "AMANOVA").execute()

products = res.data

# Sort by name
products.sort(key=lambda x: x.get("nombre", ""))

csv_file = "amanova_revision_catalogo.csv"

with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, delimiter=";")
    writer.writerow([
        "ID_Supabase", 
        "SKU", 
        "Nombre", 
        "Gama", 
        "Subcategoria",
        "Peso (kg/g)", 
        "PVP", 
        "Precio Base (PVD)", 
        "Ruta Foto Actual", 
        "Foto Correcta?", 
        "Ruta CORRECTA de Foto"
    ])
    
    for p in products:
        name = p.get("nombre", "")
        
        # Try to extract weight (e.g., 2 KG, 85 G, 10KG, 400g)
        peso = ""
        match = re.search(r'(\d+(?:[.,]\d+)?\s*(?:kg|g|gr|ml|l))', name, re.IGNORECASE)
        if match:
            peso = match.group(1).upper()
            
        sku = p.get("sku", "")
        ruta_foto = f"public/images/productos/{sku}.jpg" if sku else ""
        
        writer.writerow([
            p.get("id", ""),
            sku,
            name,
            p.get("gama", ""),
            p.get("subcategoria", ""),
            peso,
            p.get("precio_pvp", ""),
            p.get("precio_base", ""),
            ruta_foto,
            "",
            ""
        ])

print(f"Exportados {len(products)} productos de Amanova a {csv_file}")
