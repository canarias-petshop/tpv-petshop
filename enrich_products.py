import os
import json
import time
from supabase import create_client, Client
import google.generativeai as genai
import toml

# 1. Load Secrets
secrets_path = os.path.join(".streamlit", "secrets.toml")
with open(secrets_path, "r") as f:
    secrets = toml.load(f)

url = secrets.get("url")
key = secrets.get("key") # Note: this is the service role key based on my previous checks
supabase: Client = create_client(url, key)

gemini_key = secrets.get("gemini_api_key")
genai.configure(api_key=gemini_key)
# gemini-2.5-flash or 1.5
model = genai.GenerativeModel('gemini-1.5-flash')

def call_gemini(products_chunk):
    prompt = """Eres un experto en nutrición de mascotas y marketing. 
Por favor, escribe una descripción corta, atractiva y comercial (máximo 2-3 líneas) para cada uno de los siguientes productos.
Incluye algún emoji relevante (🐾, 🥩, 🐟, etc.) y menciona el beneficio principal o ingrediente clave basándote en el nombre y la marca.

Responde ÚNICAMENTE con un array en formato JSON válido, donde cada objeto tenga 'id' (el id exacto que te doy) y 'desc' (la descripción generada). No uses bloques de código markdown, solo el texto JSON puro.

Productos:
"""
    products_json = json.dumps(products_chunk, indent=2, ensure_ascii=False)
    
    try:
        response = model.generate_content(prompt + products_json)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
    except Exception as e:
        print("Gemini Error:", e)
        return None

def main():
    print("Fetching products...")
    response = supabase.table("productos").select("id, nombre, marca, familia").is_("caracteristicas", "null").execute()
    all_products = response.data
    
    print(f"Found {len(all_products)} products to update.")
    
    chunk_size = 15
    updated_count = 0
    
    for i in range(0, len(all_products), chunk_size):
        chunk = all_products[i:i + chunk_size]
        print(f"Processing chunk {i//chunk_size + 1} of {(len(all_products) + chunk_size - 1)//chunk_size}...")
        
        # Prepare small chunk for Gemini
        mini_chunk = [{"id": p["id"], "nombre": p["nombre"], "marca": p["marca"], "categoria": p.get("familia")} for p in chunk]
        
        gemini_data = call_gemini(mini_chunk)
        if gemini_data and isinstance(gemini_data, list):
            for item in gemini_data:
                item_id = item.get("id")
                desc = item.get("desc")
                if item_id and desc:
                    try:
                        supabase.table("productos").update({"caracteristicas": desc}).eq("id", item_id).execute()
                        updated_count += 1
                    except Exception as e:
                        print(f"Error updating {item_id}:", e)
        else:
            print("Failed to get valid JSON for this chunk.")
            
        time.sleep(4)
        
    print(f"Finished! Updated {updated_count} products.")

if __name__ == "__main__":
    main()
