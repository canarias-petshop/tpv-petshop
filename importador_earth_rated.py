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
print("🔌 Conectando a Supabase para leer el PDF de Earth Rated...")

# 1. Asegurar que el proveedor existe
NOMBRE_PROV = "Earth Rated"
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

# 3. Generador inteligente de SKU correlativo (ER-001, ER-002...) para Earth Rated
contador_sku = 1
def generar_sku():
    global contador_sku
    while True:
        nuevo_sku = f"ER-{contador_sku:03d}"
        if nuevo_sku not in skus_existentes:
            return nuevo_sku
        contador_sku += 1

# 4. El texto bruto copiado directamente de tu PDF
datos_pdf = """
Cod. Producto Cod. Ean Descripción Tarifa P.V.P.R. Tarifa
P.V.T
CG-0026 870856000703 Earth Rated Bolsas 21x15Ud Lavanda 13,10 9,17
CG-0027 870856000710 Earth Rated Bolsas 21x15Ud Sin Perfume 13,10 9,17
CG-0022 870856000079 Earth Rated Bolsas 300Ud Lavanda 10,11 7,08
CG-0023 870856000253 Earth Rated Bolsas 300Ud Sin Perfume 10,11 7,08
CG-0020 870856000024 Earth Rated Bolsas 8x15Ud Lavanda 5,47 3,83
CG-0021 870856000185 Earth Rated Bolsas 8x15Ud Sin Perfume 5,47 3,83
CG-0024 870856000055 Earth Rated Bolsas Asas Lavanda 120Ud 5,47 3,83
CG-0025 870856000345 Earth Rated Bolsas Asas Sin Perfume 120Ud 5,47 3,83
CG-0028 Earth Rated Bolsas Rollo Individual 21Ud 0,69 0,48
CG-0019 870856000949 Earth Rated Dispensador Con 15Bolsas Sin Perfume 3,89 2,72
CG-0029 870856001366 Earth Rated Expositor 2023 37,57 26,30
CG-0017 870856000567 Toallitas Earth Rated Lavanda 100Uds 6,93 4,85
CG-0018 870856000574 Toallitas Earth Rated Sin Perfume 100Uds 6,93 4,85
"""

# 5. Procesar los datos (Nuevo radar inteligente flexible)
lineas = datos_pdf.strip().split('\n')
insertados = 0
omitidos = 0

for linea in lineas:
    linea = linea.strip()
    if not linea: continue
        
    partes = linea.split()
    
    # Comprobamos que al menos haya 4 elementos y que los dos últimos sean precios (formato X,XX)
    if len(partes) >= 4 and re.match(r'^\d+,\d{2}$', partes[-2]) and re.match(r'^\d+,\d{2}$', partes[-1]):
        ref_orig = partes[0]
        pvp_str = partes[-2]
        coste_str = partes[-1]
        
        # Identificamos si el segundo elemento es un EAN (código de barras) o si falta
        # Asumimos que es EAN si tiene al menos 7 caracteres, contiene números y no tiene letras minúsculas
        posible_ean = partes[1]
        if len(posible_ean) >= 7 and not any(c.islower() for c in posible_ean) and any(c.isdigit() for c in posible_ean):
            ean = posible_ean
            nombre = " ".join(partes[2:-2])
        else:
            ean = ""
            nombre = " ".join(partes[1:-2])
            
        nombre = nombre.strip()
        pvp = float(pvp_str.replace(',', '.'))
        coste = float(coste_str.replace(',', '.'))
        
        if nombre.lower() in nombres_existentes:
            print(f"⚠️ Omitido (Ya existe): {nombre}")
            omitidos += 1
            continue
            
        nuevo_sku = generar_sku()
        
        # Insertar el producto
        res_ins = client.table("productos").insert({
            "sku": nuevo_sku,
            "codigo_barras": ean,
            "nombre": nombre,
            "categoria": "Producto",
            "precio_base": coste,
            "igic_tipo": 3.0, # IGIC al 3% según política estricta de la tienda
            "precio_pvp": pvp,
            "stock_actual": 0,
            "stock_minimo": 2,
            "cantidad_reponer": 5
        }).execute()
        
        if res_ins.data:
            prod_id = res_ins.data[0]['id']
            # Enlazarlo con Earth Rated
            client.table("productos_proveedores").insert({
                "producto_id": prod_id,
                "proveedor_id": prov_id,
                "precio_coste": coste
            }).execute()
            
            skus_existentes.add(nuevo_sku)
            nombres_existentes.add(nombre.lower())
            insertados += 1
            print(f"  ✅ Añadido: [{nuevo_sku}] {nombre} (PVP: {pvp}€ | Coste: {coste}€ | EAN: {ean if ean else 'Faltante'})")

print(f"\n🎉 ¡Magia completada! {insertados} productos nuevos de Earth Rated insertados. {omitidos} omitidos.")