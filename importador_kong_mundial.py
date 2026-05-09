import re
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
print("🔌 Conectando a Supabase para leer el PDF de Kong Mundial...")

# 1. Asegurar que el proveedor existe
NOMBRE_PROV = "Kong Mundial"
res_prov = client.table("proveedores").select("id").eq("nombre_empresa", NOMBRE_PROV).execute()
if res_prov.data:
    prov_id = res_prov.data[0]['id']
else:
    res_ins_p = client.table("proveedores").insert({"nombre_empresa": NOMBRE_PROV}).execute()
    prov_id = res_ins_p.data[0]['id']

# 2. Cargar productos existentes para no duplicar
res_prod = client.table("productos").select("id, sku, nombre").execute()
skus_existentes = {str(p.get('sku', '')).strip().upper() for p in res_prod.data} if res_prod.data else set()
nombres_existentes = {str(p.get('nombre', '')).strip().lower() for p in res_prod.data} if res_prod.data else set()

# 3. Generador inteligente de SKU correlativo (KM-001, KM-002...) para Kong Mundial
contador_sku = 1
def generar_sku():
    global contador_sku
    while True:
        nuevo_sku = f"KM-{contador_sku:03d}"
        if nuevo_sku not in skus_existentes:
            return nuevo_sku
        contador_sku += 1

# 4. El texto bruto copiado directamente de tu PDF
datos_pdf = """
Cod. Producto Cod. Ean Descripción Tarifa P.V.P.R. Tarifa
P.V.T
POC-0218 035585539003 NKRS32 Kong Wild Knots Sport Bear M Alemania 11,10 7,77
POC-0219 035585539034 NKRS35 Kong Wild Knots Sport Bear M Inglaterra 11,10 7,77
POC-0220 035585539041 NKRS36 Kong Wild Knots Sport Bear M España 11,10 7,77
POC-0221 035585539058 NKRS37 Kong Wild Knots Sport Bear M Italia 11,10 7,77
POC-0222 035585539072 NKRS39 Kong Wild Knots Sport Bear M Argentina 11,10 7,77
POC-0223 035585539089 NKRS41 Kong Wild Knots Sport Bear M Brasil 11,10 7,77
POC-0224 035585539218 ABSB2 Kong Sport Soccer Balls 3-Pk M 6,06 4,24
POC-0225 035585539225 ABSB3 Kong Sport Soccer Balls 3-Pk S 4,66 3,26
POC-0226 035585539232 ABSB5 Kong Sport Soccer Balls 3-Pk Xs 4,50 3,15
POC-0227 035585537726 225P198ESP Display Kong Wild Knots Bear M España 133,17 93,22
En vigor 01/02/2026
Tarifas Kong Mundial 2026 Tienda
Última modificación Abr -26
"""

# 5. Procesar los datos (Radar inteligente)
lineas = datos_pdf.strip().split('\n')
insertados = 0
omitidos = 0

for linea in lineas:
    linea = linea.strip()
    if not linea: continue
        
    partes = linea.split()
    
    if len(partes) >= 4 and re.match(r'^\d+,\d{2}$', partes[-2]) and re.match(r'^\d+,\d{2}$', partes[-1]):
        pvp = float(partes[-2].replace(',', '.'))
        coste = float(partes[-1].replace(',', '.'))
        
        posible_ean = partes[1]
        if len(posible_ean) >= 7 and not any(c.islower() for c in posible_ean) and any(c.isdigit() for c in posible_ean):
            ean = posible_ean
            nombre = " ".join(partes[2:-2]).strip()
        else:
            ean = ""
            nombre = " ".join(partes[1:-2]).strip()
            
        if nombre.lower() in nombres_existentes:
            print(f"⚠️ Omitido (Ya existe): {nombre}")
            omitidos += 1
            continue
            
        nuevo_sku = generar_sku()
        
        res_ins = client.table("productos").insert({
            "sku": nuevo_sku, "codigo_barras": ean, "nombre": nombre, "categoria": "Producto",
            "precio_base": coste, "igic_tipo": 3.0, "precio_pvp": pvp, "stock_actual": 0,
            "stock_minimo": 2, "cantidad_reponer": 5
        }).execute()
        
        if res_ins.data:
            client.table("productos_proveedores").insert({
                "producto_id": res_ins.data[0]['id'], "proveedor_id": prov_id, "precio_coste": coste
            }).execute()
            
            skus_existentes.add(nuevo_sku)
            nombres_existentes.add(nombre.lower())
            insertados += 1
            print(f"  ✅ Añadido: [{nuevo_sku}] {nombre} (PVP: {pvp}€ | Coste: {coste}€)")

print(f"\n🎉 ¡Magia completada! {insertados} productos de Kong Mundial insertados. {omitidos} omitidos.")