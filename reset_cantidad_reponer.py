import os
import toml
from supabase import create_client

try:
    with open(".streamlit/secrets.toml", "r") as f:
        secrets = toml.load(f)
    url = secrets["url"]
    key = secrets["key"]
except:
    try:
        import tomllib
        with open(".streamlit/secrets.toml", "rb") as f:
            secrets = tomllib.load(f)
        url = secrets["url"]
        key = secrets["key"]
    except Exception as e:
        print(f"Error cargando secrets: {e}")
        exit(1)

client = create_client(url, key)

print("Actualizando todos los productos: cantidad_reponer = 0...")

limit = 1000
offset = 0
total_actualizados = 0

while True:
    res = client.table("productos").select("id").eq("categoria", "Producto").range(offset, offset + limit - 1).execute()
    
    if not res.data:
        break
        
    ids = [item['id'] for item in res.data]
    
    # Update en lote, en sub-bloques pequeños para no saturar la URL
    chunk_size = 50
    for i in range(0, len(ids), chunk_size):
        sub_ids = ids[i:i+chunk_size]
        client.table("productos").update({"cantidad_reponer": 0}).in_("id", sub_ids).execute()
    
    total_actualizados += len(ids)
    print(f"Actualizados {total_actualizados} productos...")
    offset += limit

print("¡Proceso completado con éxito!")
