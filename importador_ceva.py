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
print("🔌 Conectando a Supabase para leer el PDF de Ceva...")

# 1. Asegurar que el proveedor existe
NOMBRE_PROV = "Ceva"
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

# 3. Generador inteligente de SKU correlativo (CV-001, CV-002...) para Ceva
contador_sku = 1
def generar_sku():
    global contador_sku
    while True:
        nuevo_sku = f"CV-{contador_sku:03d}"
        if nuevo_sku not in skus_existentes:
            return nuevo_sku
        contador_sku += 1

# 4. El texto bruto copiado directamente de tu PDF
datos_pdf = """
Cod. Producto Cod. Ean Descripción Tarifa P.V.P.R. Tarifa
P.V.T
VET-372 3411113097622 Adaptil Calm Recambio PACK 3X48 Ml 71,11 49,78
VET-363 3411113084424 Adaptil Chew 30 Chews 37,94 26,56
SAN038 3411112940431 Adaptil Collar Junior 33,11 23,18
SAN043 3411112116676 Adaptil Collar Perro Mediano y Grande 34,64 24,25
SAN044 3411112116652 Adaptil Collar Perro Pequeño 31,61 22,13
VET-303 3411112169252 Adaptil Difusor+Vial 48Ml 1Mes 34,11 23,88
VET-306 3411112133758 Adaptil Spray 60 Ml 27,94 19,56
VET-304 3411112169344 Adaptil Vial Recambio 48Ml 1Mes 28,87 20,21
VET-336 3411113009441 Douxo S3 Calm Champu 200 Ml 24,29 17,00
VET-422 3411113174583 Douxo S3 Calm Champu 500 Ml 47,83 33,48
VET-394 3411113166779 Douxo S3 Calm Champu Solido 21,86 15,30
VET-340 3411113011345 Douxo S3 Calm Mousse 150 Ml 24,41 17,09
VET-362 3411113065416 Douxo S3 Calm Pads 30Ud 15,09 10,56
VET-337 3411113009571 Douxo S3 Care Champu 200 Ml 15,73 11,01
VET-392 3411113123673 Douxo S3 Care Ear 120Ml 18,54 12,98
VET-391 3411113122836 Douxo S3 Care Ear 60Ml 11,44 8,01
VET-342 3411113018191 Douxo S3 Pyo Champu 200 Ml 24,29 17,00
VET-423 3411113174545 Douxo S3 Pyo Champu 500 Ml 47,83 33,48
VET-341 3411113018122 Douxo S3 Pyo Mousse 150 Ml 24,41 17,09
SAN085 3411113021658 Douxo S3 Pyo Pads 30Ud 15,09 10,56
VET-338 3411113009977 Douxo S3 Seb Champu 200 Ml 24,29 17,00
VET-339 3411113010898 Douxo S3 Seb Mousse 150 Ml 24,41 17,09
SAN088 3660176502943 Douxo Seb Spot-On (25X2Ml) 91,99 64,39
VET-409 3411113154295 Douxo Spa 100 Toallitas Multiusos 16,23 11,36
VET-406 3411113166892 Douxo Spa Acondicionador Avena Hidratante 250Ml 14,43 10,10
VET-408 3411113166915 Douxo Spa Auricular 120 Ml 10,83 7,58
VET-402 3411113166885 Douxo Spa Champu Acond 2 En 1 Ultras Perros 250Ml 14,43 10,10
VET-407 3411113166908 Douxo Spa Champu Alivia 250Ml 15,34 10,74
VET-403 3411113166854 Douxo Spa Champu Antiolor 250Ml 14,43 10,10
VET-401 3411113166847 Douxo Spa Champu Avena Hidratante 250Ml 14,43 10,10
VET-412 3411113166878 Douxo Spa Champu Cachorro 250Ml 14,43 10,10
VET-410 3411113166861 Douxo Spa Champu Control De La Muda 250Ml 14,43 10,10
VET-405 3411113167424 Douxo Spa Mousse Gato Sin Estres 150Ml 9,93 6,95
VET-404 3411113167417 Douxo Spa Mousse Perro Limpieza Express 150Ml 9,93 6,95
VET-411 3411113167400 Douxo Spa Spray Desenredante 340Ml 18,40 12,88
VET-388 8421617200072 Expositor Feliway Opt Dif+Rec x4Uds+Rec x3Uds 263,54 184,48
VET-387 8421617200089 Expositor Feliway Optimum Dif+Rec x3Uds 118,89 83,22
VET-389 8421617200027 Expositor Happy Snack by Feliway x10Uds 78,60 55,00
VET-413 8421617700015 Expositor Sobremesa Douxo Spa x10Uds 109,94 76,96
VET-301 3411112169498 Feliway Classic Difusor + Recambio 48Ml 33,11 23,18
VET-302 3411112169603 Feliway Classic Recambio 48Ml 28,93 20,25
VET-326 3411112291632 Feliway Classic Recambio PACK 3X48Ml 71,11 49,78
VET-300 3411112133789 Feliway Classic Spray 60 Ml 27,79 19,45
VET-305 3411112046003 Feliway Classic Spray Travel 20Ml 15,11 10,58
VET-318 3411112251186 Feliway Friends Difusor + Recambio 48 Ml 33,11 23,18
VET-319 3411112251230 Feliway Friends Recambio 48 Ml 28,93 20,25
En vigor 01/02/2026
Tarifas Ceva 2026 Tienda
Última modificación Ene -26
Cod. Producto Cod. Ean Descripción Tarifa P.V.P.R. Tarifa
P.V.T
VET-327 3411112291687 Feliway Friends Recambio PACK 3X48 Ml 71,44 50,01
VET-364 3411113085865 Feliway Help Difusor + Recambio 14,70 10,29
VET-365 3411113168513 Feliway Help Recambio PACK 3 24,86 17,40
VET-343 3411113030421 Feliway Optimum Difusor + Recambio 48Ml 39,83 27,88
VET-344 3411113030438 Feliway Optimum Recambio 48Ml 35,63 24,94
VET-361 3411113072940 Feliway Optimum Recambio PACK 3X48 Ml 94,37 66,06
VET-393 3411113168469 Happy Snack By Feliway Chicken 24Sticks 28,03 19,62
VET-377 3411113127879 Happy Snack By Feliway Chicken 6Sticks 7,87 5,51
VET-421 3411113168506 Happy Snack By Feliway Salmon 24Sticks 28,03 19,62
VET-420 3411113168476 Happy Snack By Feliway Salmon 6Sticks 7,87 5,51
VET-370 3411113088200 Thundershirt L 18-29Kg 43,14 30,20
VET-369 3411113088194 Thundershirt M 11-18Kg 41,66 29,16
VET-368 3411113088187 Thundershirt S 6-11Kg 38,97 27,28
VET-371 3411113088217 Thundershirt XL 29-50Kg 45,40 31,78
VET-367 3411113088163 Thundershirt XS 4-6Kg 37,97 26,58
VET-311 3411112080038 Vectra 3D Dog +40Kg 3 Pip 49,59 34,71
VET-307 3411112080083 Vectra 3D Dog 1.5-4Kg 3 Pip 34,56 24,19
VET-309 3411112080069 Vectra 3D Dog 10-25Kg 3 Pip 42,93 30,05
VET-310 3411112080052 Vectra 3D Dog 25-40Kg 3 Pip 47,44 33,21
VET-308 3411112080076 Vectra 3D Dog 4-10Kg 3 Pip 37,23 26,06
VET-334 3411112991358 Vectra 3D L Dog 25-40Kg 12 Pip 165,07 115,55
VET-333 3411112991341 Vectra 3D M Dog 10-25Kg 12 Pip 149,47 104,63
VET-332 3411112991334 Vectra 3D S Dog 4-10Kg 12 Pip 129,41 90,59
VET-335 3411112991389 Vectra 3D XL Dog +40Kg 12 Pip 172,41 120,69
VET-331 3411112991174 Vectra 3D XS Dog 1.5-4Kg 12 Pip 120,16 84,11
SAN079 3411112122622 Vectra Felis 0,6-10Kg 3Pip 29,61 20,73
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
            print(f"  ✅ Añadido: [{nuevo_sku}] {nombre} (PVP: {pvp}€ | Coste: {coste}€ | EAN: {ean if ean else 'Faltante'})")

print(f"\n🎉 ¡Magia completada! {insertados} productos nuevos de Ceva insertados. {omitidos} omitidos.")