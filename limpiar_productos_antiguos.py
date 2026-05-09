import toml
from postgrest import SyncPostgrestClient
import os

def init_supabase():
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    with open(secrets_path, "r") as f: secrets = toml.load(f)
    raw_url = secrets.get('url', '').strip().strip('"').strip("'").rstrip('/')
    api_url = raw_url if raw_url.endswith('/rest/v1') else f"{raw_url}/rest/v1"
    api_key = secrets.get('key', '').strip().strip('"').strip("'")
    return SyncPostgrestClient(api_url, headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"})

client = init_supabase()

print("🧹 Buscando productos antiguos para hacer limpieza general...")

# Traer todos los artículos que sean "Producto" (ignorando los "Servicios")
res = client.table("productos").select("id, sku, nombre").eq("categoria", "Producto").execute()

if res.data:
    borrados = 0
    omitidos = 0
    
    for p in res.data:
        sku = str(p.get('sku', '')).upper()
        # Conservamos los que empiezan por AM- (Amanova) o GP- (Gloria Pets)
        if sku.startswith("AM-") or sku.startswith("GP-"):
            omitidos += 1
        else:
            client.table("productos_proveedores").delete().eq("producto_id", p['id']).execute()
            client.table("productos").delete().eq("id", p['id']).execute()
            borrados += 1
            
    print(f"✅ Limpieza completada. Se han borrado {borrados} productos antiguos.")
    print(f"🛡️ Se han conservado {omitidos} productos de tus importaciones recientes (AM- y GP-).")
    print("✂️ Los servicios de peluquería están a salvo y no se han tocado.")
else:
    print("⚠️ No se encontraron productos.")