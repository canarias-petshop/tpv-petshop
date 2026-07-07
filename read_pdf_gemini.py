import os
import toml
import google.generativeai as genai

pdf_path = r"C:\Users\truji\OneDrive\Documentos\ANIMALARIUM\LISTADO DE PRECIOS PROVEEDORES\ZOTECNIA\tarifas-amanova-2025-tienda.pdf"

secrets_path = os.path.join(".streamlit", "secrets.toml")
with open(secrets_path, "r") as f:
    secrets = toml.load(f)
gemini_key = secrets.get("gemini_api_key", "").strip()
genai.configure(api_key=gemini_key)

modelo = genai.GenerativeModel('gemini-2.5-flash')

prompt = "Extrae el texto de las primeras 3 páginas de este PDF. Muestra los productos, formatos, y precios pvp que encuentres, manten un formato de tabla simple o texto legible."

try:
    with open(pdf_path, "rb") as f_pdf:
        payload = [prompt, {"mime_type": "application/pdf", "data": f_pdf.read()}]
    response = modelo.generate_content(payload)
    
    with open("pdf_sample.txt", "w", encoding="utf-8") as out:
        out.write(response.text)
    print("Muestra del PDF con Gemini guardada en pdf_sample.txt")
except Exception as e:
    print("Error:", e)
