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
print("🔌 Conectando a Supabase para leer el PDF de Beaphar...")

# 1. Asegurar que el proveedor existe
NOMBRE_PROV = "Beaphar"
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

# 3. Generador inteligente de SKU correlativo (BE-001, BE-002...) para Beaphar
contador_sku = 1
def generar_sku():
    global contador_sku
    while True:
        nuevo_sku = f"BE-{contador_sku:03d}"
        if nuevo_sku not in skus_existentes:
            return nuevo_sku
        contador_sku += 1

# 4. El texto bruto copiado directamente de tu PDF
datos_pdf = """
BEA0008 8711231112951 Aceite De Salmon Perro y Gato 425Ml 16,60 11,62
BEA0012 8711231116386 Bocaditos Catnip Bits Gato 35Gr 2,53 1,77
BEA0010 8711231116232 Bocaditos Dental Bits Gato 35Gr 2,39 1,67
BEA0009 8711231116096 Bocaditos Malta Bits Gato 150Gr 5,81 4,07
BEA0013 8711231116461 Bocaditos Malta Bits Gato 35Gr 2,53 1,77
BEA0054 8711231116270 Bocaditos Salmon Bits Gato 35Gr 2,57 1,80
BEA0028 8711231156825 Bucal Water Perro y Gato 250Ml 10,16 7,11
BEA0045 8711231175789 Calming Bits 35Gr 3,00 2,10
BEA0047 8711231175840 Calming Collar Gato 35Cm 8,27 5,79
BEA0046 8711231175833 Calming Collar Perro 65Cm 9,11 6,38
BEA0004 8711231105489 Calming Spot On Gato 3X0,4Ml 9,47 6,63
BEA0037 8710729093901 Care + Arena De Baño 1,3Kg 8,09 5,67
BEA0049 8711231184040 Care + Cobaya 1,5Kg 17,85 12,49
BEA0048 8711231184033 Care + Conejo 1,5Kg 17,52 12,26
BEA0050 8711231184071 Care + Conejo Junior 1,5Kg 17,85 12,49
BEA0051 8711231122530 Catcomfort Pipetas Gatos 3 Ud 14,70 10,29
BEA0003 8711231104482 Cepillo Dental De Dedo 2Ud 3,00 2,10
BEA0016 8711231130979 Collar Bio Band Repelente Perro 65Cm 6,15 4,31
BEA0044 8711231173006 Collar Canishield Perro 1 X 48Cm 18,17 12,72
BEA0041 8711231172337 Collar Canishield Perro 1 X 65Cm 18,67 13,07
BEA0042 8711231172344 Collar Canishield Perro 2 X 48Cm 25,79 18,05
BEA0043 8711231172351 Collar Canishield Perro 2 X 65Cm 27,94 19,56
BEA0038 8711231164486 Fiprotec Spot On Gato 4 Pip X 0,5Ml 11,70 8,19
BEA0027 8711231154081 Fiprotec Spray Perros Gatos 100Ml 15,08 10,56
BEA0031 8711231156856 Gel Dental Perro y Gato 100Gr 9,87 6,91
BEA0055 8711231213788 Keep Off Spray Educador para Gatos y Perros 200Ml 11,50 8,05
BEA0007 8711231112449 Lactol Kit: Biberon + 6 Tetinas + Limpiador 7,46 5,22
BEA0011 8711231116294 Limpiador De Lagrimas Perro y Gato 50Ml 8,74 6,12
BEA0014 8711231116720 Limpiador De Oidos Perro y Gato 50Ml 8,22 5,75
BEA0006 8711231106202 Locion Repelente Perro Gato 250Ml 15,17 10,62
BEA0023 8711231152322 Neutralizador De Olores Gato 400Gr 9,64 6,75
BEA0026 8711231153848 Neutralizador De Olores Roedores 600Gr 10,22 7,16
BEA0021 8711231148974 No Stress Gato Pack Difusor y Recambio 30Ml 14,19 9,93
BEA0022 8711231148998 No Stress Gato Recambio 30Ml 10,07 7,05
BEA0024 8711231152995 Pack Dental: Pasta Dental + Cepillo Dental 10,32 7,23
BEA0015 8711231129478 Pasta De Malta Gatos 100Gr 7,97 5,58
BEA0025 8711231153671 Pasta De Malta Para Hurones 100Gr 8,96 6,27
BEA0030 8711231156849 Pasta Dental Perro y Gato 100Gr 7,61 5,33
BEA0053 8711231175048 Pinza Quita Garrapatas 1Ud 5,31 3,72
BEA0005 8711231106172 Pipetas Repelentes Gato 3X1Ml 9,27 6,49
BEA0018 8711231135066 Puppy Trainer Educador para Cachorros 20Ml 10,15 7,11
BEA0029 8711231156832 Spray Aliento Fresco Perro y Gato 150Ml 9,51 6,65
BEA0002 8711231102358 Spray Protector Almohadillas 150Ml 10,58 7,41
BEA0033 8711231146048 Vermipure Gato 50 Comp 18,49 12,94
BEA0032 8711231146215 Vermipure Perro Grande &gt;15Kg 50 Comp 19,33 13,53
BEA0034 8711231146055 Vermipure Perro Pequeño &lt;15Kg 50 Comp 18,49 12,94
BEA0057 8711231218806 Wet Dog Anti-Olor Perro Mojado 250Ml 7,86 5,5 NOVEDAD
BEA0035 8710729093116 Xtravital Conejo 1Kg 5,54 3,88
BEA0036 8710729093123 Xtravital Conejo 2,5Kg 11,47 8,03
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
            # Enlazarlo con Beaphar
            client.table("productos_proveedores").insert({
                "producto_id": prod_id,
                "proveedor_id": prov_id,
                "precio_coste": coste
            }).execute()
            
            skus_existentes.add(nuevo_sku)
            nombres_existentes.add(nombre.lower())
            insertados += 1
            print(f"  ✅ Añadido: [{nuevo_sku}] {nombre} (PVP: {pvp}€ | Coste: {coste}€ | EAN: {ean if ean else 'Faltante'})")

print(f"\n🎉 ¡Magia completada! {insertados} productos nuevos de Beaphar insertados. {omitidos} omitidos.")