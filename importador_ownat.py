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
print("🔌 Conectando a Supabase para leer el listado de Ownat...")

# 1. Asegurar que van directamente al proveedor Zootecnia
NOMBRE_PROV = "Zootecnia - Zootecnia S.L."
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

# 3. Generador inteligente de SKU correlativo (OW-001, OW-002...) para Ownat
contador_sku = 1
def generar_sku():
    global contador_sku
    while True:
        nuevo_sku = f"OW-{contador_sku:03d}"
        if nuevo_sku not in skus_existentes:
            return nuevo_sku
        contador_sku += 1

# 4. El texto bruto copiado directamente de tu PDF
datos_pdf = """
OWNAT PERROS						
CLASSIC (CEREALES INTEGRALES) 10% CARNE FRESCA						
OWNAT CLASSIC JUNIOR 	4KG		12,34 €			15,65 €
OWNAT CLASSIC JUNIOR 	12KG		35,70 €			45,21 €
OWNAT CLASSIC COMPLET 	4KG		9,86 €			12,53 €
OWNAT CLASSIC COMPLET 	12KG		27,90 €			35,50 €
OWNAT CLASSIC COMPLET 	20KG		41,00 €			48,93 €
OWNAT CLASSIC LAMB&RICE 	4KG		12,14 €			15,41 €
OWNAT CLASSIC LAMB&RICE 	12KG		32,71 €			41,65 €
OWNAT CLASSIC LAMB&RICE 	20KG		50,23 €			59,30 €
OWNAT CLASSIC FISH DOG 	4KG		11,17 €			14,23 €
OWNAT CLASSIC FISH DOG 	12KG		30,68 €			39,06 €
OWNAT CLASSIC FISH DOG 	20KG		48,40 €			57,63 €
OWNAT CLASSIC LIGHT 	4KG		10,12 €			12,83 €
OWNAT CLASSIC LIGHT 	12KG		27,97 €			35,47 €
OWNAT CLASSIC LIGHT 	20KG		43,67 €			52,02 €
OWNAT CLASSIC MINI ADULT 	400GR		2,01 €			2,50 €
OWNAT CLASSIC MINI ADULT 	1,5KG		5,25 €			6,68 €
OWNAT CLASSIC MINI ADULT 	4KG		10,36 €			13,14 €
OWNAT CLASSIC MINI ADULT 	8KG		19,34 €			23,10 €
OWNAT CLASSIC DUCK 	4KG		11,74 €			14,92 €
OWNAT CLASSIC DUCK 	12KG		34,09 €			43,97 €
OWNAT CLASSIC ENERGY 	4KG		11,84 €			15,02 €
OWNAT CLASSIC ENERGY 	12KG		31,37 €			39,93 €
OWNAT CLASSIC ENERGY 	20KG		49,49 €			59,43 €
CLASSIC (CERELALES INTEGRALES) MONOPROTÉICO						
OWNAT CLASSIC MONOPROTEIC SALMON 	4KG		16,34 €			23,99 €
OWNAT CLASSIC MONOPROTEIC SALMON 	12KG		40,77 €			59,90 €
OWNAT CLASSIC MONOPROTEIC LAMB 	4KG		14,44 €			21,21 €
OWNAT CLASSIC MONOPROTEIC LAMB 	12KG		39,10 €			57,46 €
OWNAT CLASSIC MONOPROTEIC IBERIAN PORK 	4KG		13,59 €			19,95 €
OWNAT CLASSIC MONOPROTEIC IBERIAN PORK 	12KG		37,39 €			54,93 €
JUST (SIN CEREALES) 20% CARNE FRESCA						
OWNAT JUST JUNIOR 	3KG		14,45 €			18,08 €
OWNAT JUST JUNIOR 	14KG		55,26 €			65,91 €
OWNAT JUST ADULT CHICKEN 	3KG		14,16 €			20,86 €
OWNAT JUST ADULT CHICKEN 	14KG		50,32 €			60,05 €
OWNAT JUST LAMB 	3KG		14,58 €			21,68 €
OWNAT JUST LAMB 	14KG		55,94 €			66,73 €
OWNAT JUST SALMON	3KG		14,56 €			21,48 €
OWNAT JUST SALMON 	14KG		55,15 €			65,80 €
OWNAT JUST TROUT 	3KG		14,77 €			21,81 €
OWNAT JUST TROUT 	14KG		55,56 €			66,26 €
OWNAT JUST LIGHT 	3KG		14,22 €			21,78 €
OWNAT JUST LIGHT 	14KG		50,66 €			60,47 €
OWNAT JUST DUCK 	3KG		14,49 €			21,35 €
OWNAT JUST DUCK 	14KG		54,66 €			65,81 €
ULTRA (BAJO EN CEREALES) 30% CARNE FRESCA						
OWNAT ULTRA MINI JUNIOR 	400GR		2,63 €			3,32 €
OWNAT ULTRA MINI JUNIOR 	3KG		15,30 €			19,06 €
OWNAT ULTRA MINI ADULT 	400KG		2,55 €			3,17 €
OWNAT ULTRA MINI ADULT 	3KG		14,65 €			18,27 €
OWNAT ULTRA MEDIUM JUNIOR 	3KG		16,41 €			20,46 €
OWNAT ULTRA MEDIUM JUNIOR 	12KG		47,39 €			61,69 €
OWNAT ULTRA MEDIUM ADULT 	3KG		14,20 €			17,70 €
OWNAT ULTRA MEDIUM ADULT 	12KG		40,95 €			53,33 €
OWNAT ULTRA MEDIUM STERILIZED 	3KG		14,88 €			18,67 €
OWNAT ULTRA MEDIUM STERILIZED	12KG		44,07 €			57,40 €
OWNAT ULTRA MEDIUM LIGHT	3KG		14,88 €			18,54 €
OWNAT ULTRA MEDIUM LIGHT 	12KG		43,64 €			56,81 €
OWNAT ULTRA MEDIUM LAMB&RICE	3KG		16,69 €			20,67 €
OWNAT ULTRA MEDIUM LAMB&RICE 	12KG		49,25 €			64,09 €
OWNAT ULTRA MAXI JUNIOR 	3KG		16,04 €			19,99 €
OWNAT ULTRA MAXI JUNIOR 	12KG		47,55 €			61,88 €
OWNAT ULTRA MAXI ADULT 	12KG		43,07 €			56,09 €
PRIME (SIN CEREALES) 35-50% CARNE FRESCA						
OWNAT PRIME JUNIOR CHICKEN 	3KG		18,65 €			23,39 €
OWNAT PRIME JUNIOR CHICKEN 	12KG		54,79 €			66,58 €
OWNAT PRIME JUNIOR LAMB	3KG		19,40 €			24,32 €
OWNAT PRIME JUNIOR LAMB 	12KG		58,38 €			70,96 €
OWNAT PRIME MINI CHICKEN&TURKEY 	1KG		6,68 €			8,38 €
OWNAT PRIME MINI CHICKEN&TURKEY 	3KG		18,29 €			22,93 €
OWNAT PRIME MINI LAMB 	400GR		3,53 €			4,40 €
OWNAT PRIME MINI LAMB 	1KG		7,41 €			9,29 €
OWNAT PRIME MINI LAMB 	3KG		19,38 €			4,30 €
OWNAT PRIME ADULT CHICKEN&TURKEY 	3KG		18,29 €			22,93 €
OWNAT PRIME ADULT CHICKEN&TURKEY 	12KG		53,39 €			64,82 €
OWNAT PRIME ADULT LAMB 	3KG		19,27 €			24,14 €
OWNAT PRIME ADULT LAMB 	12KG		58,22 €			69,06 €
OWNAT PRIME ADULT OILY FISH 	3KG		20,13 €			25,23 €
OWNAT PRIME ADULT OILY FISH 	12KG		59,53 €			70,65 €
OWNAT PRIME SENIOR CHICKEN&TURKEY 	3KG		18,65 €			23,39 €
OWNAT PRIME SENIOR CHICKEN&TURKEY 	12KG		54,79 €			66,68 €
HIPOALERGÉNICO						
OWNAT HYPOALLERGENIC MINI LAMB 	1KG		10,74 €			13,44 €
OWNAT HYPOALLERGENIC MINI LAMB 	3KG		22,09 €			27,89 €
OWNAT HYPOALLERGENIC LAMB 	3KG		21,27 €			26,85 €
OWNAT HYPOALLERGENIC LAMB 	12KG		59,00 €			74,98 €
OWNAT HYPOALLERGENIC SALMON 	3KG		21,68 €			27,40 €
OWNAT HYPOALLERGENIC SALMON 	12KG		58,11 €			73,51 €
OWNAT HYPOALLERGENIC PORK 	3KG		20,11 €			25,38 €
OWNAT HYPOALLERGENIC PORK 	12KG		53,77 €			68,16 €
CARE (CUIDADOS ESPECIFICOS)						
OWNAT CARE DERMATOLOGIC 	3KG		18,77 €			25,58 €
OWNAT CARE DERMATOLOGIC 	10KG		48,42 €			65,97 €
OWNAT CARE DIGESTIVE 	3KG		16,85 €			22,93 €
OWNAT CARE DIGESTIVE 	10KG		42,64 €			58,03 €
OWNAT CARE MOBILITY 	3KG		18,24 €			24,81 €
OWNAT CARE MOBILITY 	10KG		47,33 €			64,37 €
OWNAT CARE WEIGHT CONTROL	3KG		16,49 €			22,36 €
OWNAT CARE WEIGHT CONTROL	10KG		41,94 €			56,90 €
AUTHOR (SIN CEREALES) 60% CARNE FRESCA						
OWNAT AUTHOR JUNIOR FRESH CHICKEN 	3KG		18,28 €			23,91 €
OWNAT AUTHOR JUNIOR FRESH CHICKEN 	10KG		52,51 €			68,73 €
OWNAT AUTHOR FRESH ROOSTER 	3KG		17,32 €			22,66 €
OWNAT AUTHOR FRESH ROOSTER 	10KG		49,54 €			64,84 €
OWNAT AUTHOR FRESH DUCK&CHICKEN	3KG		18,44 €			24,14 €
OWNAT AUTHOR FRESH DUCK&CHICKEN 	10KG		53,03 €			69,43 €
OWNAT AUTHOR FRESH LAMB&PORK 	3KG		19,20 €			25,13 €
OWNAT AUTHOR FRESH LAMB&PORK 	10KG		57,61 €			75,41 €
OWNAT GATOS						
CLASSIC (CEREALES INTEGRALES) 10% CARNE FRESCA 						
OWNAT CLASSIC KITTEN 	400GR		2,15 €			2,74 €
OWNAT CLASSIC KITTEN 	1,5KG		6,45 €			8,19 €
OWNAT CLASSIC KITTEN 	4KG		14,61 €			18,59 €
OWNAT CLASSIC DAILY CARE 	400GR		2,04 €			2,60 €
OWNAT CLASSIC DAILY CARE 	1,5KG		5,72 €			7,28 €
OWNAT CLASSIC DAILY CARE 	4KG		12,05 €			15,30 €
OWNAT CLASSIC DAILY CARE 	15KG		41,23 €			49,23 €
OWNAT CLASSIC FISH GATO 	1,5KG		5,76 €			7,30 €
OWNAT CLASSIC FISH GATO 	4KG		12,61 €			16,05 €
OWNAT CLASSIC HAIRBALL 	1,5KG		5,63 €			7,16 €
OWNAT CLASSIC HAIRBALL	4KG		12,35 €			15,74 €
OWNAT CLASSIC LIGHT GATO 	1,5KG		5,54 €			7,04 €
OWNAT CLASSIC LIGHT GATO 	4KG		12,08 €			14,59 €
OWNAT CLASSIC STERILIZED 	400GR		2,06 €			2,62 €
OWNAT CLASSIC STERILIZED 	1,5KG		6,03 €			7,68 €
OWNAT CLASSIC STERILIZED 	4KG		13,21 €			16,10 €
OWNAT CLASSIC STERILIZED 	15KG		41,80 €			49,93 €
JUST (SIN CEREALES) 20% CARNE FRESCA						
OWNAT JUST ADULT CHICKEN CAT	1KG		6,98 €			8,46 €
OWNAT JUST ADULT CHICKEN CAT	3KG		17,02 €			20,80 €
OWNAT JUST ADULT CHICKEN CAT	8KG		35,46 €			43,08 €
OWNAT JUST STERILIZED 	400GR		3,27 €			3,83 €
OWNAT JUST STERILIZED	1KG		7,17 €			8,69 €
OWNAT JUST STERILIZED 	3KG		17,57 €			21,45 €
OWNAT JUST STERILIZED 	8KG		36,29 €			44,39 €
OWNAT JUST STERILIZED FISH 	1KG		7,90 €			9,58 €
OWNAT JUST STERILIZED FISH 	3KG		18,01 €			22,01 €
OWNAT JUST STERILIZED FISH 	8KG		36,62 €			44,50 €
ULTRA (BAJO EN CEREALES) 30% CARNE FRESCA						
OWNAT ULTRA KITTEN	1,5KG		8,68 €			11,51 
OWNAT ULTRA KITTEN	3KG		15,69 €			20,84 €
OWNAT ULTRA KITTEN STERILIZED	1,5KG		8,95 €			11,88 €
OWNAT ULTRA KITTEN STERILIZED	3KG		16,23 €			21,55 €
OWNAT ULTRA YOUNG	1,5KG		8,05 €			10,68 €
OWNAT ULTRA YOUNG	3KG		14,68 €			19,50 €
OWNAT ULTRA YOUNG	8KG		32,93 €			43,60 €
OWNAT ULTRA YOUNG STERILIZED	1,5KG		8,14 €			10,81 €
OWNAT ULTRA YOUNG STERILIZED	3KG		14,81 €			19,67 €
OWNAT ULTRA YOUNG STERILIZED	8KG		33,40 €			44,37 €
OWNAT ULTRA YOUNG STERLIZED FISH	1,5KG		8,57 €			11,36 €
OWNAT ULTRA YOUNG STERLIZED FISH	3KG		15,22 €			20,20 €
OWNAT ULTRA MATURE	1,5KG		8,09 €			10,74 €
OWNAT ULTRA MATURE	3KG		14,71 €			19,54 €
OWNAT ULTRA MATURE	8KG		33,14 €			44,04 €
OWNAT ULTRA MATURE STERLIZED	1,5KG		8,19 €			10,87 €
OWNAT ULTRA MATURE STERLIZED	3KG		14,89 €			19,78 €
OWNAT ULTRA MATURE STERLIZED	8KG		33,61 €			44,65 €
OWNAT ULTRA MATURE STERLIZED FISH	1,5KG		8,57 €			11,36 €
OWNAT ULTRA MATURE STERLIZED FISH	3KG		15,17 €			20,14 €
OWNAT ULTRA AGEING FISH	1,5KG		9,14 €			12,13 €
OWNAT ULTRA AGEING FISH	3KG		17,04 €			22,62 €
PRIME (SIN CEREALES) 35-50% CARNE FRESCA						
OWNAT PRIME KITTEN 	400GR		4,18 €			5,32 €
OWNAT PRIME KITTEN 	1KG		8,83 €			11,23 €
OWNAT PRIME KITTEN 	3KG		24,90 €			31,67 €
OWNAT PRIME HAIR&SKIN 	3KG		23,89 €			30,39 €
OWNAT PRIME ADULT CHICKEN 	400GR		3,69 €			4,67 €
OWNAT PRIME ADULT CHICKEN 	1KG		7,76 €			9,87 €
OWNAT PRIME ADULT CHICKEN 	3KG		21,86 €			27,79 €
OWNAT PRIME ADULT CHICKEN 	8KG		44,01 €			55,17 €
OWNAT PRIME STERILIZED 	1KG		8,51 €			10,81 €
OWNAT PRIME STERILIZED 	3KG		23,89 €			30,39 €
OWNAT PRIME STERILIZED 	8KG		49,70 €			62,24 €
OWNAT PRIME STERILIZED FISH 	1KG		9,23 €			11,74 €
OWNAT PRIME STERILIZED FISH 	3KG		25,94 €			32,96 €
OWNAT PRIME STERILIZED FISH 	8KG		53,93 €			67,53 €
CARE (CUIDADOS ESPECIFICOS)						
OWNAT CARE URINARY 	1,5KG		11,20 €			15,45 €
OWNAT CARE URINARY 	3KG		18,99 €			26,21 €
OWNAT CARE RENAL 	1,5KG		10,99 €			15,17 €
OWNAT CARE RENAL	3KG		18,62 €			25,72 €
OWNAT CARE HYPOALLERGENIC 	1,5KG		11,15 €			15,40 €
OWNAT CARE HYPOALLERGENIC 	3KG		18,93 €			26,13 €
OWNAT CARE WEIGHT CONTROL CAT	1,5KG		11,29 €			15,55 €
OWNAT CARE WEIGHT CONTROL CAT	3KG		19,10 €			26,27 €
AUTHOR (SIN CEREALES) 60% CARNE FRESCA						
OWNAT AUTHOR STERILIZED FRESH CHICKEN 	1,5KG		10,15 €			13,30 €
OWNAT AUTHOR STERILIZED FRESH CHICKEN 	3KG		17,96 €			23,53 €
OWNAT AUTHOR FRESH OILY&POULTRY	1,5KG		10,73 €			14,04 €
OWNAT AUTHOR FRESH OILY&POULTRY	3KG		18,95 €			24,80 €
"""

# 5. Procesar los datos (Radar Inteligente adaptado a Ownat para ignorar símbolos de € y fusionar nombre+peso)
lineas = datos_pdf.strip().split('\n')
insertados = 0
omitidos = 0

for linea in lineas:
    # Limpiamos todos los símbolos de Euro para que no rompan la lectura de precios
    linea = linea.replace('€', '').strip()
    if not linea: continue
        
    partes = linea.split()
    
    # Buscamos los dos últimos números (Tarifa y PVP) leyendo de derecha a izquierda
    precios = []
    indices_precios = []
    for i in range(len(partes)-1, -1, -1):
        if re.match(r'^\d+,\d{1,2}$', partes[i]):
            precios.append(partes[i])
            indices_precios.append(i)
        if len(precios) == 2:
            break
            
    if len(precios) == 2:
        # Como hemos leído de derecha a izquierda:
        # precios[0] es el PVP (el último de la frase)
        # precios[1] es la Tarifa/Coste (el penúltimo)
        pvp_str = precios[0]
        coste_str = precios[1]
        
        idx_fin_nombre = indices_precios[1] # Aquí termina el nombre
        
        # El nombre final une todo lo que hay antes de los precios. 
        # Al no haber EAN, esto fusionará automáticamente el nombre con el peso (Ej: "OWNAT CLASSIC JUNIOR 4KG")
        nombre = " ".join(partes[:idx_fin_nombre]).strip()
        ean = ""
        
        pvp = float(pvp_str.replace(',', '.'))
        coste = float(coste_str.replace(',', '.'))
        
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

print(f"\n🎉 ¡Magia completada! {insertados} productos de Ownat insertados a nombre de Zootecnia. {omitidos} omitidos.")