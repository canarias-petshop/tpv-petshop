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
print("🔌 Conectando a Supabase para leer el PDF de Flexi...")

# 1. Asegurar que el proveedor existe
NOMBRE_PROV = "Flexi"
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

# 3. Generador inteligente de SKU correlativo (FX-001, FX-002...) para Flexi
contador_sku = 1
def generar_sku():
    global contador_sku
    while True:
        nuevo_sku = f"FX-{contador_sku:03d}"
        if nuevo_sku not in skus_existentes:
            return nuevo_sku
        contador_sku += 1

# 4. El texto bruto copiado directamente de tu PDF
datos_pdf = """
Cod. Producto Cod. Ean Descripción Tarifa P.V.P.R. Tarifa
P.V.T
CG-0506 4000498031711 Correa Flexi Neon Reflect L Cin 5M Amarillo 50Kg 25,77 18,04
CG-0505 4000498031704 Correa Flexi Neon Reflect M Cin 5M Amarillo 25Kg 22,64 15,85
CG-0502 4000498025222 Correa Flexi Neon Reflect M Cord 5M Amarillo12Kg 17,11 11,98
CG-0504 4000498023518 Correa Flexi Neon Reflect S Cin 5M Amarillo 15Kg 18,99 13,29
CG-0501 4000498025215 Correa Flexi Neon Reflect S Cord 5M Amarillo 12Kg 15,06 10,54
CG-0503 4000498023501 Correa Flexi Neon Reflect XS Cin 3M Amarillo 12Kg 15,07 10,55
CG-0500 4000498025208 Correa Flexi Neon Reflect XS Cord 3M Amarillo 8Kg 12,61 8,83
CG-0403 4000498023426 Correa Flexi New Classic Gato XS Cord 3M Negro 8Kg 10,04 7,03
CG-0400 4000498023419 Correa Flexi New Classic Gato XS Cord. 3M Azul 8Kg 10,04 7,03
CG-0401 4000498023402 Correa Flexi New Classic Gato XS Cord. 3M Rojo 8Kg 10,04 7,03
CG-0402 4000498023433 Correa Flexi New Classic Gato XS Cord. 3M Rosa 8Kg 10,04 7,03
CG-0490 4000498032312 Correa Flexi New Classic L Cinta 5M Azul 50Kg 21,70 15,19
CG-0493 4000498032329 Correa Flexi New Classic L Cinta 5M Negro 50Kg 21,70 15,19
CG-0491 4000498032305 Correa Flexi New Classic L Cinta 5M Rojo 50Kg 21,70 15,19
CG-0492 4000498023013 Correa Flexi New Classic L Cinta 8M Azul 50Kg 29,57 20,70
CG-0495 4000498023020 Correa Flexi New Classic L Cinta 8M Negro 50Kg 29,57 20,70
CG-0494 4000498023006 Correa Flexi New Classic L Cinta 8M Rojo 50Kg 29,57 20,70
CG-0480 4000498032213 Correa Flexi New Classic M Cinta 5M Azul 25Kg 19,13 13,39
CG-0483 4000498032220 Correa Flexi New Classic M Cinta 5M Negro 25Kg 19,13 13,39
CG-0481 4000498032206 Correa Flexi New Classic M Cinta 5M Rojo 25Kg 19,13 13,39
CG-0482 4000498032237 Correa Flexi New Classic M Cinta 5M Rosa 25Kg 19,13 13,39
CG-0430 4000498022610 Correa Flexi New Classic M Cordon 5M Azul 20Kg 14,24 9,97
CG-0433 4000498022627 Correa Flexi New Classic M Cordon 5M Negro 20Kg 14,24 9,97
CG-0431 4000498022603 Correa Flexi New Classic M Cordon 5M Rojo 20Kg 14,24 9,97
CG-0432 4000498022634 Correa Flexi New Classic M Cordon 5M Rosa 20Kg 14,24 9,97
CG-0450 4000498022818 Correa Flexi New Classic M Cordon 8M Azul 20Kg 20,34 14,24
CG-0453 4000498022825 Correa Flexi New Classic M Cordon 8M Negro 20Kg 20,34 14,24
CG-0451 4000498022801 Correa Flexi New Classic M Cordon 8M Rojo 20Kg 20,34 14,24
CG-0452 4000498022832 Correa Flexi New Classic M Cordon 8M Rosa 20Kg 20,34 14,24
CG-0470 4000498023211 Correa Flexi New Classic S Cinta 5M Azul 15Kg 15,33 10,73
CG-0473 4000498023228 Correa Flexi New Classic S Cinta 5M Negro 15Kg 15,33 10,73
CG-0471 4000498023204 Correa Flexi New Classic S Cinta 5M Rojo 15Kg 15,33 10,73
CG-0472 4000498023235 Correa Flexi New Classic S Cinta 5M Rosa 15Kg 15,33 10,73
CG-0420 4000498022511 Correa Flexi New Classic S Cordon 5M Azul 12Kg 12,07 8,45
CG-0423 4000498022528 Correa Flexi New Classic S Cordon 5M Negro 12Kg 12,07 8,45
CG-0421 4000498022504 Correa Flexi New Classic S Cordon 5M Rojo 12Kg 12,07 8,45
CG-0422 4000498022535 Correa Flexi New Classic S Cordon 5M Rosa 12Kg 12,07 8,45
CG-0440 4000498022719 Correa Flexi New Classic S Cordon 8M Azul 12Kg 18,17 12,72
CG-0443 4000498022726 Correa Flexi New Classic S Cordon 8M Negro 12Kg 18,17 12,72
CG-0441 4000498022702 Correa Flexi New Classic S Cordon 8M Rojo 12Kg 18,17 12,72
CG-0442 4000498022733 Correa Flexi New Classic S Cordon 8M Rosa 12Kg 18,17 12,72
CG-0460 4000498023112 Correa Flexi New Classic XS Cinta 3M Azul 12Kg 12,89 9,02
CG-0463 4000498023129 Correa Flexi New Classic XS Cinta 3M Negro 12Kg 12,89 9,02
CG-0461 4000498023105 Correa Flexi New Classic XS Cinta 3M Rojo 12Kg 12,89 9,02
CG-0462 4000498023136 Correa Flexi New Classic XS Cinta 3M Rosa 12Kg 12,89 9,02
En vigor 01/02/2025
Tarifas Flexi 2025 Tienda
Última modificación Ene -25
Cod. Producto Cod. Ean Descripción Tarifa P.V.P.R. Tarifa
P.V.T
CG-0410 4000498022412 Correa Flexi New Classic XS Cordon 3M Azul 8Kg 10,04 7,03
CG-0413 4000498022429 Correa Flexi New Classic XS Cordon 3M Negro 8Kg 10,04 7,03
CG-0411 4000498022405 Correa Flexi New Classic XS Cordon 3M Rojo 8Kg 10,04 7,03
CG-0412 4000498022436 Correa Flexi New Classic XS Cordon 3M Rosa 8Kg 10,04 7,03
CG-0230 4000498043714 Correa Flexi New Comfort L Cinta 5M Azul 12Kg 32,41 22,69
CG-0231 4000498043707 Correa Flexi New Comfort L Cinta 5M Rojo 12Kg 32,41 22,69
CG-0220 4000498043639 Correa Flexi New Comfort M Cinta 5M Azul 25Kg 21,97 15,38
CG-0221 4000498043622 Correa Flexi New Comfort M Cinta 5M Rojo 25Kg 21,97 15,38
CG-0222 4000498043608 Correa Flexi New Comfort M Cinta 5M Rosa 25Kg 21,97 15,38
CG-0210 4000498043530 Correa Flexi New Comfort S Cinta 5M Azul 15Kg 18,59 13,01
CG-0211 4000498043523 Correa Flexi New Comfort S Cinta 5M Rojo 15Kg 18,59 13,01
CG-0212 4000498043509 Correa Flexi New Comfort S Cinta 5M Rosa 15Kg 18,59 13,01
CG-0200 4000498043431 Correa Flexi New Comfort XS Cinta 3M Azul 12Kg 14,91 10,44
CG-0201 4000498043424 Correa Flexi New Comfort XS Cinta 3M Rojo 12Kg 14,91 10,44
CG-0202 4000498043400 Correa Flexi New Comfort XS Cinta 3M Rosa 12Kg 14,91 10,44
CG-0311 4000498032534 Correa Flexi Style M Cinta 5M Negro 25Kg 22,53 15,77
CG-0301 4000498032435 Correa Flexi Style S Cinta 3M Negro 12Kg 18,50 12,95
CG-0509 4000498034408 Correa Flexi Xtreme L Cin 5M Naran/Negro 65Kg 41,10 28,77
CG-0508 4000498034309 Correa Flexi Xtreme M Cin 5M Naran/Negro 35Kg 29,16 20,41
CG-0507 4000498034200 Correa Flexi Xtreme S Cin 5M Naran/Negro 20Kg 23,46 16,42
CG-0510 4000498023709 Flexi Multi Box Negro 6,79 4,75
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
        if re.match(r'^\d+,\d{1,2}$', partes[i]):
            precios_encontrados.append(partes[i])
            indices_precios.append(i)
        if len(precios_encontrados) == 2:
            break
            
    if len(precios_encontrados) == 2:
        coste_str = precios_encontrados[0] # El último que encontró
        pvp_str = precios_encontrados[1]   # El penúltimo
        idx_pvp = indices_precios[1]       # Dónde termina el nombre
        
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
            # Enlazarlo con Flexi
            client.table("productos_proveedores").insert({
                "producto_id": prod_id,
                "proveedor_id": prov_id,
                "precio_coste": coste
            }).execute()
            
            skus_existentes.add(nuevo_sku)
            nombres_existentes.add(nombre.lower())
            insertados += 1
            print(f"  ✅ Añadido: [{nuevo_sku}] {nombre} (PVP: {pvp}€ | Coste: {coste}€ | EAN: {ean if ean else 'Faltante'})")

print(f"\n🎉 ¡Magia completada! {insertados} productos nuevos de Flexi insertados. {omitidos} omitidos.")