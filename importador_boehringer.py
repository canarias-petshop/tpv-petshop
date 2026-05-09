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
print("🔌 Conectando a Supabase para leer el PDF de Boehringer...")

# 1. Asegurar que el proveedor existe
NOMBRE_PROV = "Boehringer"
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

# 3. Generador inteligente de SKU correlativo (BH-001, BH-002...) para Boehringer
contador_sku = 1
def generar_sku():
    global contador_sku
    while True:
        nuevo_sku = f"BH-{contador_sku:03d}"
        if nuevo_sku not in skus_existentes:
            return nuevo_sku
        contador_sku += 1

# 4. El texto bruto copiado directamente de tu PDF
datos_pdf = """
Cod.
Producto Cod. Ean Descripción
Tarifa
P.V.P.R.
Tarifa P.V.T.
PETVET
BI-169 5703655004199 Seraquin Omega 60Comp 47,90 33,53
PHC
MER-242 3661103041450 Comboline 18 Pip 10-20 Kg Azul 154,34 108,04 *
MER-240 3661103041436 Comboline 18 Pip Gatos Verde 117,86 82,50
MER-200 3661103000242 Frontline 100Ml 20,21 14,15
MER-201 3661103000235 Frontline 250Ml 32,86 23,00
MER-222 3661103006367 Frontline Combo 3 Pip 10-20 Kg Azul 34,25 23,98
MER-221 3661103006350 Frontline Combo 3 Pip 1-10 Kg Amarillo 29,79 20,85
MER-223 3661103006374 Frontline Combo 3 Pip 20-40 Kg Rosa 38,27 26,79
MER-224 3661103006381 Frontline Combo 3 Pip 40-60 Kg Rojo 41,88 29,31
MER-220 3661103006312 Frontline Combo 3 Pip Gatos Verde 26,05 18,24
MER-227 3661103019299 Frontline Combo 6 Pip 10-20 Kg Azul 62,13 43,49
MER-228 3661103019305 Frontline Combo 6 Pip 20-40 Kg Rosa 69,18 48,43
MER-226 3661103019282 Frontline Combo 6 Pip 2-10 Kg Amarillo 54,11 37,88
MER-225 3661103019275 Frontline Combo 6 Pip Gatos Verde 47,09 32,96
MER-247 3661103045748 Frontline Tri-Act 3 Pip 10-20Kg Azul 34,41 24,09
MER-248 3661103045755 Frontline Tri-Act 3 Pip 20-40Kg Violeta 38,36 26,85
MER-245 3661103045724 Frontline Tri-Act 3 Pip 2-5Kg Rosa 29,11 20,38
MER-249 3661103045762 Frontline Tri-Act 3 Pip 40-60Kg Rojo 42,20 29,54
MER-246 3661103045731 Frontline Tri-Act 3 Pip 5-10Kg Amarillo 31,75 22,23
MER-257 3661103045984 Frontline Tri-Act 6 Pip 10-20Kg Azul 58,38 40,86
MER-258 3661103045991 Frontline Tri-Act 6 Pip 20-40Kg Violeta 66,30 46,41
MER-255 3661103045960 Frontline Tri-Act 6 Pip 2-5Kg Rosa 48,05 33,64
MER-259 3661103046004 Frontline Tri-Act 6 Pip 40-60Kg Rojo 70,23 49,16
MER-256 3661103045977 Frontline Tri-Act 6 Pip 5-10Kg Amarillo 51,70 36,19
MER-495 4064951003790 Frontpro 11Mg 3Comp 2-4Kg S Rosa 38,80 27,16
MER-496 4064951003783 Frontpro 28Mg 3Comp 4-10Kg M Naranja 42,75 29,93
MER-497 4064951003776 Frontpro 68Mg 3Comp 10-25Kg L Azul 46,00 32,20
MER-498 4064951003769 Frontpro 136Mg 3Comp 25-50Kg XL Violeta 53,45 37,41
"""

# 5. Procesar los datos (Radar Ultra-Inteligente)
lineas = datos_pdf.strip().split('\n')
insertados = 0
omitidos = 0

for linea in lineas:
    linea = linea.strip()
    if not linea: continue
        
    partes = linea.split()
    
    # Buscamos los dos últimos elementos que parezcan precios (de atrás hacia adelante)
    precios_encontrados = []
    indices_precios = []
    for i in range(len(partes)-1, -1, -1):
        # Coincide con cosas como "11,62" o "5,5"
        if re.match(r'^\d+,\d{1,2}$', partes[i]):
            precios_encontrados.append(partes[i])
            indices_precios.append(i)
        if len(precios_encontrados) == 2:
            break
            
    if len(precios_encontrados) == 2:
        coste_str = precios_encontrados[0] # El último que encontró
        pvp_str = precios_encontrados[1]   # El penúltimo
        idx_pvp = indices_precios[1]       # Dónde termina el nombre
        
        # Identificamos si el segundo elemento es un EAN (código de barras) o si falta
        # Asumimos que es EAN si tiene al menos 7 caracteres, contiene números y no tiene letras minúsculas
        posible_ean = partes[1]
        if len(posible_ean) >= 7 and not any(c.islower() for c in posible_ean) and any(c.isdigit() for c in posible_ean):
            ean = posible_ean
            nombre_raw = " ".join(partes[2:idx_pvp])
        else:
            ean = ""
            nombre_raw = " ".join(partes[1:idx_pvp])
            
        nombre = nombre_raw.replace("&gt;", ">").replace("&lt;", "<").strip()
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
            "igic_tipo": 3.0, # IGIC al 3%
            "precio_pvp": pvp,
            "stock_actual": 0,
            "stock_minimo": 2,
            "cantidad_reponer": 5
        }).execute()
        
        if res_ins.data:
            prod_id = res_ins.data[0]['id']
            # Enlazarlo con Boehringer
            client.table("productos_proveedores").insert({
                "producto_id": prod_id,
                "proveedor_id": prov_id,
                "precio_coste": coste
            }).execute()
            
            skus_existentes.add(nuevo_sku)
            nombres_existentes.add(nombre.lower())
            insertados += 1
            print(f"  ✅ Añadido: [{nuevo_sku}] {nombre} (PVP: {pvp}€ | Coste: {coste}€ | EAN: {ean if ean else 'Faltante'})")

print(f"\n🎉 ¡Magia completada! {insertados} productos nuevos de Boehringer insertados. {omitidos} omitidos.")