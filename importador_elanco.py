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
print("🔌 Conectando a Supabase para leer el PDF de Elanco...")

# 1. Asegurar que el proveedor existe
NOMBRE_PROV = "Elanco"
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

# 3. Generador inteligente de SKU correlativo (EL-001, EL-002...) para Elanco
contador_sku = 1
def generar_sku():
    global contador_sku
    while True:
        nuevo_sku = f"EL-{contador_sku:03d}"
        if nuevo_sku not in skus_existentes:
            return nuevo_sku
        contador_sku += 1

# 4. El texto bruto copiado directamente de tu PDF
datos_pdf = """
Cod. Producto Cod. Ean Descripción Tarifa P.V.P.R. Tarifa
P.V.T
NOV-221 5420036974529 AdTab 112 Mg Perro &gt;2,5-5,5 Kg 1 Comp 15,17 10,62
NOV-241 5420036975458 AdTab 112 Mg Perro &gt;2,5-5,5 Kg 3 Comp 42,16 29,51
NOV-225 5420036974352 AdTab 12 Mg Gato 0,5-2 Kg 1 Comp 20,14 14,10
NOV-245 5420036975427 AdTab 12 Mg Gato 0,5-2 Kg 3 Comp 56,86 39,80
NOV-222 5420036974536 AdTab 225 Mg Perro &gt;5,5-11 Kg 1 Comp 16,21 11,35
NOV-242 5420036975465 AdTab 225 Mg Perro &gt;5,5-11 Kg 3 Comp 45,13 31,59
NOV-223 5420036974543 AdTab 450 Mg Perro &gt;11-22 Kg 1 Comp 17,93 12,55
NOV-243 5420036975472 AdTab 450 Mg Perro &gt;11-22 Kg 3 Comp 49,90 34,93
NOV-226 5420036974369 AdTab 48 Mg Gato &gt;2-8 Kg 1 Comp 20,76 14,53
NOV-246 5420036975434 AdTab 48 Mg Gato &gt;2-8 Kg 3 Comp 58,60 41,02
NOV-220 5420036974512 AdTab 56 Mg Perro 1,3-2,5 Kg 1 Comp 15,01 10,51
NOV-240 5420036975441 AdTab 56 Mg Perro 1,3-2,5 Kg 3 Comp 41,80 29,26
NOV-224 5420036974550 AdTab 900 Mg Perro &gt;22-45 Kg 1 Comp 19,60 13,72
NOV-244 5420036975489 AdTab 900 Mg Perro &gt;22-45 Kg 3 Comp 54,54 38,18
BAY321 5420036929628 Advantix 1 Pip X 0,4 Ml 0-4 Kg Verde 11,10 7,77
BAY322 5420036929574 Advantix 1 Pip X 1,0 Ml 4-10 Kg Turquesa 11,71 8,20
BAY323 5420036936572 Advantix 1 Pip X 2,5 Ml 10-25 Kg Rojo 13,23 9,26
BAY324 5420036929710 Advantix 1 Pip X 4,0 Ml +25 Kg Azul 14,33 10,03
BAY093 4007221043119 Advantix 24 Pip X 0,4 Ml 0-4 Kg Verde 194,39 136,07
BAY094 4007221043126 Advantix 24 Pip X 1,0 Ml 4-10 Kg Turquesa 207,10 144,97
BAY095 4007221043133 Advantix 24 Pip X 2,5 Ml 10-25 Kg Rojo 238,51 166,96
BAY096 4007221043140 Advantix 24 Pip X 4,0 Ml +25 Kg Azul 260,89 182,62
BAY021 4007221017189 Advantix 4 Pip X 0,4 Ml 0-4 Kg Verde 41,17 28,82
BAY022 4007221017196 Advantix 4 Pip X 1,0 Ml 4-10 Kg Turquesa 43,40 30,38
BAY023 4007221017202 Advantix 4 Pip X 2,5 Ml 10-25 Kg Rojo 49,07 34,35
BAY024 4007221017219 Advantix 4 Pip X 4,0 Ml +25 Kg Azul 53,17 37,22
NOV-180 5420036914853 Capstar 11 Caja De 6 Comp 21,09 14,76
NOV-181 5420036914983 Capstar 57 Caja De 6 Comp 23,44 16,41
BAY058 5420036954972 Sano&Bello Limpiador Dental 140Gr 11,69 8,18
BAY082 4007221035916 Seresto Collar Gatos 38Cm 54,66 38,26
BAY301 4007221052494 Seresto Collar Gatos 38Cm Clinico 1x12 612,23 428,56
BAY084 4007221035923 Seresto Collar Perro Gde &gt; 8Kg 70Cm 58,94 41,26
BAY303 4007221052500 Seresto Collar Perro Gde &gt; 8Kg 70Cm Clinico 1x12 660,81 462,57
BAY083 4007221035930 Seresto Collar Perro Peq &lt; 8Kg 38Cm 54,66 38,26
BAY302 4007221052487 Seresto Collar Perro Peq &lt; 8Kg 38Cm Clinico 1x12 612,23 428,56
BAY069 5420036971375 Toallitas Limpiadoras 35Ud 7,36 5,15
BAY018 5420036941026 Vetriderm 350Ml Solución Tópica 32,66 22,86
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
            
        # Limpieza de entidades HTML raras del PDF (&gt; -> > , &lt; -> <)
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
            # Enlazarlo con Elanco
            client.table("productos_proveedores").insert({
                "producto_id": prod_id,
                "proveedor_id": prov_id,
                "precio_coste": coste
            }).execute()
            
            skus_existentes.add(nuevo_sku)
            nombres_existentes.add(nombre.lower())
            insertados += 1
            print(f"  ✅ Añadido: [{nuevo_sku}] {nombre} (PVP: {pvp}€ | Coste: {coste}€ | EAN: {ean if ean else 'Faltante'})")

print(f"\n🎉 ¡Magia completada! {insertados} productos nuevos de Elanco insertados. {omitidos} omitidos.")