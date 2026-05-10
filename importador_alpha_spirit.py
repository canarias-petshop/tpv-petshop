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
print("🔌 Conectando a Supabase para procesar la lista de Alpha Spirit...")

# 1. Asegurar que el proveedor existe
NOMBRE_PROV = "Canes Avero S.L.U."
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

# 3. Generador inteligente de SKU correlativo (AL-001, AL-002...) para Alpha Spirit
contador_sku = 1
def generar_sku():
    global contador_sku
    while True:
        nuevo_sku = f"AL-{contador_sku:03d}"
        if nuevo_sku not in skus_existentes:
            return nuevo_sku
        contador_sku += 1

# 4. El texto bruto copiado directamente de la web
datos_web = """
The Only One Complete Dog Food Duck 12 kg
€77,95 €54,57

Añadir al carrito / Details
The Only One Complete Dog Food Duck 3 kg
€27,95 €19,57

Añadir al carrito / Details
Semi-humedo Multiprotein Complete Dog Food in carton Box and Individual trays 9 kg
€66,95 €46,87
Producto agotado

Details
Semi-húmedo Multiprotein Complete Dog Food in bag 1.5 kg
€16,95 €11,87

Añadir al carrito / Details
Semi-humedo Puppies Complete Dog Food in bag 3 kg
€32,95 €23,07
Producto agotado

Details
Semi-humedo Puppies Complete Dog Food in bag 1.5 kg
€19,95 €13,97

Añadir al carrito / Details
Semi-humedo Poultry Complete Dog Food in carton Box and Individual trays 9 kg
€69,95 €48,97

Añadir al carrito / Details
Semi-humedo Poultry Complete Dog Food in bag 3 kg
€32,95 €23,07
Producto agotado

Details
Semi-humedo Poultry Complete Dog Food in bag 1.5 kg
€17,95 €12,57

Añadir al carrito / Details
Semi-humedos Multiprotein Complete Dog Food in bag 3 kg
€31,95 €22,37

Añadir al carrito / Details
Semi-humedo Wild Fish Complete Dog Food in carton Box and Individual trays 9 kg
€69,95 €48,97

Añadir al carrito / Details
Semi-humedo Wild Fish Complete Dog Food in bag 3 kg
€30,95 €21,67

Añadir al carrito / Details
Semi-humedo Wild Fish Complete Dog Food in bag 1.5 kg
€17,95 €12,57

Añadir al carrito / Details
Semi-humedo Puppies Complete Dog Food in carton Box and Individual trays 9 kg
€69,95 €48,97

Añadir al carrito / Details
The Only One Complete Dog Food Multiprotein 12 kg
€72,95 €51,07

Añadir al carrito / Details
The Only One Complete Dog Food 7 Days 3 kg
€23,95 €16,77

Añadir al carrito / Details
The Only One Complete Dog Food 7 Days 12 kg
€62,95 €44,07

Añadir al carrito / Details
The Only One Complete Dog Food Poultry 12 kg
€77,95 €54,57

Añadir al carrito / Details
The Only One Complete Dog Food Multiprotein 3 kg
€27,95 €19,57

Añadir al carrito / Details
The Only One Complete Dog Food Wild Fish 3 kg
€29,95 €20,97

Añadir al carrito / Details
The Only One Complete Dog Food Wild Fish 12 kg
€77,95 €54,57

Añadir al carrito / Details
The Only One Complete Dog Food Puppies 3 kg
€29,95 €20,97

Añadir al carrito / Details
The Only One Complete Dog Food Puppies 12 kg
€77,95 €54,57

Añadir al carrito / Details
The Only One Complete Dog Food Poultry 3 kg
€29,95 €20,97
"""

# 5. Procesar los datos (Radar adaptado a formato de web)
lineas = datos_web.strip().split('\n')
insertados = 0
omitidos = 0

nombre_actual = ""

for linea in lineas:
    linea = linea.strip()
    if not linea: continue
        
    # Si la línea contiene el símbolo €, es la línea de precios
    if linea.startswith('€'):
        # Extraer PVP (primer precio) y Coste (segundo precio)
        match = re.search(r'€(\d+,\d{2})\s*€(\d+,\d{2})', linea)
        if match and nombre_actual:
            pvp = float(match.group(1).replace(',', '.'))
            coste = float(match.group(2).replace(',', '.'))
            nombre = nombre_actual
            
            if nombre.lower() in nombres_existentes:
                print(f"⚠️ Omitido (Ya existe): {nombre}")
                omitidos += 1
            else:
                nuevo_sku = generar_sku()
                res_ins = client.table("productos").insert({
                    "sku": nuevo_sku, "codigo_barras": "", "nombre": nombre, "categoria": "Producto",
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
            
            nombre_actual = "" # Reseteamos para buscar el siguiente
            
    elif "Añadir al carrito" in linea or "Details" in linea or "Producto agotado" in linea:
        # Ignoramos la basura de la web
        continue
    else:
        # Si no es un precio ni es basura, tiene que ser el nombre del producto
        nombre_actual = linea

print(f"\n🎉 ¡Magia completada! {insertados} productos nuevos de Alpha Spirit insertados. {omitidos} omitidos.")