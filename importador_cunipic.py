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
print("🔌 Conectando a Supabase para leer el PDF de Cunipic...")

# 1. Asegurar que el proveedor existe
NOMBRE_PROV = "Cunipic"
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

# 3. Generador inteligente de SKU correlativo (CP-001, CP-002...) para Cunipic
contador_sku = 1
def generar_sku():
    global contador_sku
    while True:
        nuevo_sku = f"CP-{contador_sku:03d}"
        if nuevo_sku not in skus_existentes:
            return nuevo_sku
        contador_sku += 1

# 4. El texto bruto copiado directamente de tu PDF
datos_pdf = """
Cod. Producto Cod. Ean Descripción Tarifa P.V.P.R. Tarifa
P.V.T
CU13227 8437020409360 Agapornie 1 Kg 5,21 3,65
CU93328 8437010615914 Agapornie 25 Kg, 78,57 55,00
CU13221 8427013149274 Agapornie 3Kg 9,93 6,95
CU35512 8437010615771 Algodon Roedores Multicolor 70Grs 16Ud 3,97 2,78
CU61011 8437013149518 Alpha Pro Adult Rabbit 1,750Kg. 14,69 10,28
CU61010 8437013149556 Alpha Pro Adult Rabbit 500Grs. 5,01 3,51
CU61031 8437013149532 Alpha Pro Chinchilla 1,750Kg. 14,94 10,46
CU61030 8437013149570 Alpha Pro Chinchilla 500Grs. 5,09 3,56
CU61021 8437013149525 Alpha Pro Guinea Pig 1,750Kg. 14,47 10,13
CU61020 8437013149563 Alpha Pro Guinea Pig 500Grs. 4,93 3,45
CU61001 8437013149501 Alpha Pro Junior Rabbit 1,750Kg. 15,70 10,99
CU61000 8437013149549 Alpha Pro Junior Rabbit 500Grs 5,34 3,74
CU61051 8437013149617 Alpha Pro Snack Apple 50Grs. 2,69 1,88
CU61050 8437013149624 Alpha Pro Snack Berry 50Grs. 2,69 1,88
CU61052 8437013149631 Alpha Pro Snack Carrot 50Grs. 2,69 1,88
CU61053 8437013149600 Alpha Pro Snack Malta 50Grs. 2,69 1,88
CU21216 8437010615085 Arena De Baño Chinchillas 1Kg 6,99 4,89
CU23210 8437010615078 Arena para aves 2 Kg. 5,19 3,63
CU13223 8437020409407 Aves Silvestres 1 Kg 6,23 4,36
CU22220 8437013149044 Bloque De Calcio Canario 96Ud 2,07 1,45
CU22221 8437013149037 Bloque De Calcio Periquito 2,91 2,04
CU22222 8437013149051 Bloque De Sal Roedores 2,91 2,04
CU11331 8437013149006 Bola De Heno 9,46 6,62
CU13225 8437020409384 Canarios 1 Kg 5,41 3,79
CU21214 8437006583305 Champú Seco Polvo Roedor 125Grs 25Ud 9,60 6,72
CU93343 8437021991635 Chinchilla & Degu 2,5Kg 13,50 9,45
CU93342 8437021991628 Chinchilla & Degu 700Gr 4,79 3,35
CU93336 8437021991529 Conejo Adulto 2,5Kg 11,19 7,83
CU93337 8437021991536 Conejo Adulto 5Kg 16,43 11,50
CU93335 8437021991512 Conejo Adulto 700Gr 4,73 3,31
CU93334 8437021991505 Conejo Baby 2,5Kg 12,50 8,75
CU911105 8437010615815 Conejo Baby 5 Kg 2Ud 21,00 14,70
CU93333 8437021991499 Conejo Baby 700Gr 4,93 3,45
CU21215 8437006583411 Desodorante Odor Roedor 125 Ml 20Ud 11,86 8,30
CU93339 ]C101843702199158181 Guinea Pigs 2,5Kg 4Ud 11,73 8,21
CU93340 8437021991598 Guinea Pigs 5Kg 23,50 16,45
CU93338 8437021991574 Guinea Pigs 700Gr 4,54 3,18
CU93341 8437021991604 Hamster & Gerbil 600Gr 4,34 3,04
CU11310 8437006583060 Heno Fibra 1Kg. 3,40 2,38
CU12214 8437006583145 Huron Adult 2 Kg 27,19 19,03
CU12213 8437006583114 Huron Adult 600 Grs 8,69 6,08
CU12211 8437006583138 Huron Baby 2 Kg 32,87 23,01
CU12210 8437006583107 Huron Baby 600 Grs 10,31 7,22
CU11248 8437013149228 Jerbo 700Grs 4,59 3,21
CU13217 8437009971277 Loros 1Kg 5,19 3,63
En vigor 27/05/2024
Tarifas Cunipic 2025 Tienda
Última modificación Abr -25
Cod. Producto Cod. Ean Descripción Tarifa P.V.P.R. Tarifa
P.V.T
CU13218 8437010615740 Loros 3Kg 13,40 9,38
CU11322 8437013150293 Naturaliss Chinchilla y Degu 1,81Kg 11,34 7,94
CU11321 8437013150279 Naturaliss Cobaya 1,81Kg 9,60 6,72
CU11320 8437013150255 Naturaliss Conejo Adulto 1,81Kg 10,07 7,05
CU11323 8437013150262 Naturaliss Conejo Junior 1,81Kg 10,99 7,69
CU11324 8437013150309 Naturaliss Hamster y Jerbo 500Gr 3,49 2,44
CU11315 8436560005735 Naturaliss Heno De Montaña 500Grs 4,86 3,40
CU11316 8437013149112 Naturaliss Heno Orchad Grass 500Grs 4,86 3,40
CU11317 8437013149181 Naturaliss Heno Salvaje 500Grs 4,86 3,40
CU11318 8437013149105 Naturaliss Heno Timothy 500Grs 5,19 3,63
CU45512 8437009971871 Naturlitter Madera 15L 14,06 9,84
CU45513 8437013149266 Naturlitter Madera 48L 42,86 30,00
CU45510 8437009971864 Naturlitter Madera 4L 4,16 2,91
CU45511 8437006583503 Naturlitter Madera 8L 8,69 6,08
CU45523 8437020409292 Naturlitter Madera Gatos 10L 10,91 7,64
CU45515 8437006583527 Naturlitter Maiz 10L 11,69 8,18
CU45516 8437006583534 Naturlitter Maiz 31L 28,57 20,00
CU45519 8437010615955 Naturlitter Papel 45L 57,07 39,95
CU45517 8437006583374 Naturlitter Papel 10L 10,21 7,15
CU45517PR 8437020409056 Naturlitter Papel 10L+2L 10,21 7,15
CU45518 8437006583381 Naturlitter Papel 25L 24,27 16,99
CU45509 8437013149068 Naturlitter Papel 4L 4,39 3,07
CU45520 8437010615658 Naturlitter Papel Gatos 10L 10,59 7,41
CU13226 8437020409377 Ninfas 1 Kg 5,29 3,70
CU13214 8437010615733 Ninfas 3 Kg. 9,84 6,89
CU13224 8437020409353 Periquito 1 Kg 5,29 3,70
CU13211 8437010615726 Periquito 3Kg 10,34 7,24
CU93344 8437021991642 Rata 600Gr 6,16 4,31
CU13516 8437010615047 Snack Loros-Fruta Tropical 130Grs 4,54 3,18
CU13514 8437010615023 Snack Ninfas Agapornis Mix Fruta 130Grs 4,54 3,18
CU11516 8437006583442 Snack Para Cobaya 112Grs 3,84 2,69
CU11517 8437006583435 Snack Para Conejo Adult 90Grs 4,21 2,95
CU11515 8437006583428 Snack Para Conejo Baby 112Grs 4,03 2,82
CU11311 8437006583077 Sol De Heno Diente De Leon 500Grs 4,86 3,40
CU11312 8437006583367 Sol De Heno Frutos Silvestres 500Grs 4,86 3,40
CU11314 8437006583350 Sol De Heno Manzanilla 500Grs 4,86 3,40
CU11313 8437006583343 Sol De Heno Zanahoria 500Grs 4,86 3,40
CU95533 2015855558888 Sweet Dreams Papel 10 Kg. 37,77 26,44
CU45521 Transportin Grande 1,06 0,74
CU45522 Transportin Pequeño 0,87 0,61
CU13228 8437020409391 Tropicales 1 Kg 5,49 3,84
CU11330 8437013149013 Tunel De Heno Mediano 10,59 7,41
CU11329 8437013149020 Tunel De Heno Pequeño 5,61 3,93
CU52110 8437010615306 Vl Cobaya Intestinal 1,4 Kg 15,07 10,55
CU51113 8437010615283 Vl Conejo Dental 1,4 Kg 15,83 11,08
CU51111 8437010615269 Vl Conejo Intestinal 1,4 Kg 15,83 11,08
CU51115 8437010615610 Vl Conejo Obesity 1,4 Kg 15,83 11,08
CU51110 8437010615252 Vl Conejo Renal Detoxicante 1,4 Kg 15,83 11,08
CU51112 8437010615276 Vl Conejo Respiratory 1,4 Kg 15,83 11,08
CU51114 8437010615290 Vl Conejo Skin Support 1,4 Kg 4Ud 15,83 11,08
CU55110 8437010615665 Vl Herbal Convalescence 125Grs 7,13 4,99
CU55111 8437010615986 Vl Herbal Convalescence Extra Fino 125Grs 7,13 4,99
CU53110 8437010615351 Vl Roedor Intestinal 1,4 Kg 4Ud 23,50 16,45
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
            # Enlazarlo con Cunipic
            client.table("productos_proveedores").insert({
                "producto_id": prod_id,
                "proveedor_id": prov_id,
                "precio_coste": coste
            }).execute()
            
            skus_existentes.add(nuevo_sku)
            nombres_existentes.add(nombre.lower())
            insertados += 1
            print(f"  ✅ Añadido: [{nuevo_sku}] {nombre} (PVP: {pvp}€ | Coste: {coste}€ | EAN: {ean if ean else 'Faltante'})")

print(f"\n🎉 ¡Magia completada! {insertados} productos nuevos de Cunipic insertados. {omitidos} omitidos.")