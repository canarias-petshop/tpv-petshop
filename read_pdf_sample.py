import PyPDF2
import os

pdf_path = r"C:\Users\truji\OneDrive\Documentos\ANIMALARIUM\LISTADO DE PRECIOS PROVEEDORES\ZOTECNIA\tarifas-amanova-2025-tienda.pdf"

try:
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for i in range(min(3, len(reader.pages))): # read first 3 pages
            text += f"--- PAGE {i+1} ---\n"
            text += reader.pages[i].extract_text() + "\n"
        
        with open("pdf_sample.txt", "w", encoding="utf-8") as out:
            out.write(text)
        print("Muestra del PDF guardada en pdf_sample.txt")
except Exception as e:
    print("Error leyendo PDF:", e)
