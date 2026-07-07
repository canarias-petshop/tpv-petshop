import pdfplumber
import json
import os

pdf_dir = r"C:\Users\truji\OneDrive\Documentos\ANIMALARIUM\LISTADO DE PRECIOS PROVEEDORES\FEEDCAN\Lenda"
files = [
    "Tarifa Lenda 2026 Tienda.pdf",
    "Tarifa Lenda 2026 Nueva Gama - Grain Free PVD.pdf",
    "Tarifa LendaVet 2026 Clinica.pdf"
]

data = {}

for f in files:
    path = os.path.join(pdf_dir, f)
    if not os.path.exists(path):
        continue
    
    print(f"Reading {f}...")
    tables_data = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for t in tables:
                tables_data.append(t)
    
    data[f] = tables_data

with open("lenda_tables.json", "w", encoding="utf-8") as out:
    json.dump(data, out, indent=2, ensure_ascii=False)

print("Extracted tables to lenda_tables.json")
