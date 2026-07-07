import PyPDF2

PDF_PATH = r"C:\Users\truji\OneDrive\Documentos\ANIMALARIUM\LISTADO DE PRECIOS PROVEEDORES\ZOTECNIA\tarifas-amanova-2025-tienda.pdf"

with open(PDF_PATH, "rb") as f:
    reader = PyPDF2.PdfReader(f)
    print(f"Total pages: {len(reader.pages)}")
    text = reader.pages[0].extract_text()
    print("PAGE 0:")
    print(text[:1000])
