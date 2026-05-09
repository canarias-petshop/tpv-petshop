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
print("🔌 Conectando a Supabase para leer el PDF de Zotécnica...")

# 1. Asegurar que el proveedor existe
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

# 3. Generador inteligente de SKU correlativo (ZT-001, ZT-002...)
contador_sku = 1
def generar_sku():
    global contador_sku
    while True:
        nuevo_sku = f"ZT-{contador_sku:03d}"
        if nuevo_sku not in skus_existentes:
            return nuevo_sku
        contador_sku += 1

# 4. El texto bruto copiado directamente de tu PDF
datos_pdf = """
Cod. Producto Cod. Ean Descripción
Tarifa
P.V.P.R.
Tarifa P.V.T.
AMANOVA SECO PERRO
S-AMJ74AR10 8413037332082 Amv Adult Digestive Divine Rabbit & Calabaza 10Kg 77,62 46,37
S-AMJ74AR02 8413037332075 Amv Adult Digestive Divine Rabbit & Calabaza 2Kg 23,25 13,89
S-AMJ71AP10 8413037331993 Amv Adult Exigent Iberian Pork & Calabaza 10Kg 65,00 38,83
S-AMJ71AP02 8413037331986 Amv Adult Exigent Iberian Pork & Calabaza 2Kg 17,43 10,41
S-AMJ59AV10 8413037376819 Amv Adult Exigent Venison Supreme 10Kg 76,65 45,79
S-AMJ59AV02 8413037376802 Amv Adult Exigent Venison Supreme 2Kg 20,34 12,15
S-AMJ60AL12 8413037331726 Amv Adult Large Exquisite Chicken & Quinoa 12Kg 57,23 34,19
S-AMJ80WF10 8413037331757 Amv Adult Mature Fish Delicacy & Quinoa 10Kg 67,91 40,57
S-AMJ80WF02 8413037331740 Amv Adult Mature Fish Delicacy & Quinoa 2Kg 18,40 10,99
S-AMJ30AM12 8413037331702 Amv Adult Medium Exquisite Chicken & Quinoa 12Kg 57,23 34,19
S-AMJ30AM02 8413037331696 Amv Adult Medium Exquisite Chicken & Quinoa 2Kg 14,51 8,67
S-AMJ73NR8A 8413037373771 Amv Adult Mini Digest Divine Rabbit 800Gr 10,63 6,35
S-AMJ73NR02 8413037332044 Amv Adult Mini Digestive Divi Rabbit&Calabaza 2Kg 22,28 13,31
S-AMJ73NR07 8413037332051 Amv Adult Mini Digestive Divi Rabbit&Calabaza 7Kg 65,00 38,83
S-AMJ70NP02 8413037331955 Amv Adult Mini Exigent Iberian Pork & Calabaza 2Kg 19,37 11,57
S-AMJ70NP07 8413037331962 Amv Adult Mini Exigent Iberian Pork & Calabaza 7Kg 56,26 33,61
S-AMJ70PN8A 8413037373801 Amv Adult Mini Exigent Iberian Pork 800Gr 9,17 5,48
S-AMJ20AN02 8413037331665 Amv Adult Mini Exquisite Chicken & Quinoa 2Kg 16,46 9,83
S-AMJ20AN07 8413037331672 Amv Adult Mini Exquisite Chicken & Quinoa 7Kg 45,58 27,23
S-AMJ85ON02 8413037373764 Amv Adult Mini Obesity Turkey Delight 2Kg 16,46 9,83
S-AMJ85ON07 8413037373818 Amv Adult Mini Obesity Turkey Delight 7Kg 52,38 31,29
S-AMJ85ON8A 8413037373757 Amv Adult Mini Obesity Turkey Delight 800gr 9,17 5,48
S-AMJ41LA02 8413037371326 Amv Adult Mini Sensit Delicious Lamb & Calabaz 2Kg 22,28 13,31
S-AMJ41LA07 8413037371333 Amv Adult Mini Sensit Delicious Lamb & Calabaz 7Kg 64,03 38,25
S-AMJ41LA8A 8413037373795 Amv Adult Mini Sensitive Delicious Lamb 800Gr 10,63 6,35
S-AMJ91NS8A 8413037373788 Amv Adult Mini Sensitive Salmon 800Gr 10,15 6,06
S-AMJ91NS02 8413037331894 Amv Adult Mini Sensitive Salmon Deluxe&Calabaz 2Kg 20,34 12,15
S-AMJ91NS07 8413037331900 Amv Adult Mini Sensitive Salmon Deluxe&Calabaz 7Kg 57,23 34,19
S-AMJ88MF10 8413037331849 Amv Adult Mobility Fish Delicacy & Quinoa 10Kg 67,91 40,57
S-AMJ88MF02 8413037331832 Amv Adult Mobility Fish Delicacy & Quinoa 2Kg 18,40 10,99
S-AMJ86OT10 8413037331818 Amv Adult Obesity Turkey Delight & Quinoa 10Kg 58,20 34,77
S-AMJ86OT02 8413037331801 Amv Adult Obesity Turkey Delight & Quinoa 2Kg 15,49 9,25
S-AMJ40LA10 8413037332112 Amv Adult Sensitive Delicious Lamb & Calabaza 10Kg 73,74 44,05
S-AMJ40LA02 8413037332105 Amv Adult Sensitive Delicious Lamb & Calabaza 2Kg 19,37 11,57
S-AMJ92NS10 8413037331931 Amv Adult Sensitive Salmon Deluxe & Calabaza 10Kg 67,91 40,57
S-AMJ92NS02 8413037331924 Amv Adult Sensitive Salmon Deluxe & Calabaza 2Kg 20,34 12,15
S-AMJ81MF02 8413037376727 Amv Mini Mature Fish Delicacy 2Kg 19,37 11,57
S-AMJ81MF5A 8413037376710 Amv Mini Mature Fish Delicacy 500Gr 7,72 4,61
S-AMJ81MF07 8413037376734 Amv Mini Mature Fish Delicacy 7Kg 55,29 33,03
S-AMJ72PR02 8413037332013 Amv Puppy Digestive Divine Rabbit & Calabaza 2Kg 23,25 13,89
S-AMJ72PR07 8413037332020 Amv Puppy Digestive Divine Rabbit & Calabaza 7Kg 65,00 38,83
S-AMJ18PL12 8413037331641 Amv Puppy Large Exquisite Chicken & Quinoa 12Kg 70,83 42,31
S-AMJ15PM12 8413037331627 Amv Puppy Medium Exquisite Chicken & Quinoa 12Kg 70,83 42,31
S-AMJ15PM02 8413037331610 Amv Puppy Medium Exquisite Chicken & Quinoa 2Kg 16,46 9,83
S-AMJ10PN02 8413037331580 Amv Puppy Mini Exquisite Chicken & Quinoa 2Kg 16,46 9,83
S-AMJ10PN5A 8413037335441 Amv Puppy Mini Exquisite Chicken & Quinoa 500Gr 6,75 4,03
S-AMJ90PS02 8413037331863 Amv Puppy Sensitive Salmon Deluxe & Calabaza 2Kg 21,31 12,73
S-AMJ90PS07 8413037331870 Amv Puppy Sensitive Salmon Deluxe & Calabaza 7Kg 58,20 34,77
AMANOVA SECO GATO
Tarifas Amanova 2025 Tienda
En vigor 15/04/2024
Última modificación Oct-25
Cod. Producto Cod. Ean Descripción
Tarifa
P.V.P.R.
Tarifa P.V.T.
S-AMA24LA5B 8413037331436 Amv Adult Cat Delicious Lamb & Calabaza 1,5Kg 17,43 10,41
S-AMA24LA04 8413037335489 Amv Adult Cat Delicious Lamb & Calabaza 4Kg 43,15 25,03
S-AMA25RA5B 8413037331559 Amv Adult Cat Divine Rabbit & Calabaza 1,5Kg 19,37 11,57
S-AMA25RA04 8413037335502 Amv Adult Cat Divine Rabbit & Calabaza 4Kg 48,50 28,97
S-AMA20AD5B 8413037331153 Amv Adult Cat Exquisite Chicken & Quinoa 1,5Kg 13,54 8,09
S-AMA20AD06 8413037331160 Amv Adult Cat Exquisite Chicken & Quinoa 6Kg 33,93 20,27
S-AMA23WF5B 8413037331399 Amv Adult Cat Fish Delicacy & Quinoa 1,5Kg 16,46 9,83
S-AMA23WF06 8413037331405 Amv Adult Cat Fish Delicacy & Quinoa 6Kg 45,58 27,23
S-AMA21SA5B 8413037331191 Amv Adult Cat Salmon Deluxe & Quinoa 1,5Kg 15,49 9,25
S-AMA21SA06 8413037331207 Amv Adult Cat Salmon Deluxe & Quinoa 6Kg 42,67 25,49
S-AMA22TU5B 8413037331351 Amv Adult Cat Turkey Delight & Calabaza 1,5Kg 17,43 10,41
S-AMA22TU04 8413037335496 Amv Adult Cat Turkey Delight & Calabaza 4Kg 37,82 22,59
S-AMA10KT5B 8413037331115 Amv Kitten Exquisite Chicken & Quinoa 1,5Kg 15,49 9,25
S-AMA10KT3A 8413037331108 Amv Kitten Exquisite Chicken & Quinoa 300Gr 4,81 2,87
S-AMA10KT04 8413037335458 Amv Kitten Exquisite Chicken & Quinoa 4Kg 30,53 18,24
S-AMA32LA5B 8413037331313 Amv Sterilised Cat Delicious Lamb & Quinoa 1,5Kg 17,43 10,41
S-AMA32LA3A 8413037331306 Amv Sterilised Cat Delicious Lamb & Quinoa 300Gr 4,81 2,87
S-AMA32LA04 8413037335519 Amv Sterilised Cat Delicious Lamb & Quinoa 4Kg 38,79 23,17
S-AMA30ST5B 8413037331238 Amv Sterilised Cat Exquisite Chicken & Quinoa 1,5K 16,46 9,83
S-AMA30ST3A 8413037331221 Amv Sterilised Cat Exquisite Chicken & Quinoa 300G 4,81 2,87
S-AMA30ST06 8413037331245 Amv Sterilised Cat Exquisite Chicken & Quinoa 6Kg 45,58 27,23
S-AMA34WF5B 8413037331511 Amv Sterilised Cat Fish Delicacy & Calabaza 1,5Kg 17,43 10,41
S-AMA34WF3A 8413037331504 Amv Sterilised Cat Fish Delicacy & Calabaza 300Gr 4,81 2,87
S-AMA34WF04 8413037335472 Amv Sterilised Cat Fish Delicacy & Calabaza 4Kg 37,82 22,59
S-AMA31SS5B 8413037331276 Amv Sterilised Cat Salmon Deluxe & Quinoa 1,5Kg 17,43 10,41
S-AMA31SS3A 8413037331269 Amv Sterilised Cat Salmon Deluxe & Quinoa 300Gr 4,81 2,87
S-AMA31SS06 8413037331283 Amv Sterilised Cat Salmon Deluxe & Quinoa 6Kg 51,41 30,71
AMANOVA POUCH PERRO
S-AMT53BC1A 8413037335014 Amv Wet Adult Beef & Chicken Pouch 100Gr Nº01 12Ud 17,40 11,04
S-AMT53BC3A 8413037371999 Amv Wet Adult Beef & Chicken Pouch 300Gr Nº01 12Ud 46,44 29,64
S-AMT50PO1A 8413037335038 Amv Wet Adult Exquis Chicken Pouch 100Gr Nº03 12Ud 17,40 11,04
S-AMT50PO3A 8413037372019 Amv Wet Adult Exquis Chicken Pouch 300Gr Nº03 12Ud 46,44 29,64
S-AMT52CI1A 8413037335045 Amv Wet Adult Iberian Pork Pouch 100Gr Nº04 12Ud 17,40 11,04
S-AMT52CI3A 8413037372026 Amv Wet Adult Iberian Pork Pouch 300Gr Nº04 12Ud 46,44 29,64
S-AMT60BM1A 8413037335021 Amv Wet Adult Irresitib Beef Pouch 100Gr Nº02 12Ud 17,40 11,04
S-AMT60BM3A 8413037372002 Amv Wet Adult Irresitib Beef Pouch 300Gr Nº02 12Ud 46,44 29,64
S-AMT61LI1A 8413037335052 Amv Wet Adult Lamb & Pork Pouch 100Gr Nº05 12Ud 17,40 11,04
S-AMT61LI3A 8413037372033 Amv Wet Adult Lamb & Pork Pouch 300Gr Nº05 12Ud 46,44 29,64
S-AMT63LP1A 8413037357481 Amv Wet Adult Lamb&Calabaza Pouch 100Gr Nº15 12Ud 17,40 11,04
S-AMT63LP3A 8413037372750 Amv Wet Adult Lamb&Calabaza Pouch 300Gr Nº15 12Ud 46,44 29,64
S-AMT62ST1A 8413037335069 Amv Wet Adult Salmon&Turkey Pouch 100Gr Nº06 12Ud 17,40 11,04
S-AMT62ST3A 8413037372040 Amv Wet Adult Salmon&Turkey Pouch 300Gr Nº06 12Ud 46,44 29,64
S-AMT51TU1A 8413037335076 Amv Wet Adult Turkey Delight Pouch 100Gr Nº07 12Ud 17,40 11,04
S-AMT51TU3A 8413037372057 Amv Wet Adult Turkey Delight Pouch 300Gr Nº07 12Ud 46,44 29,64
S-AMT10PP1A 8413037335090 Amv Wet Puppy Exquis Chicken Pouch 100Gr Nº08 12Ud 17,40 11,04
S-AMT10PP3A 8413037372064 Amv Wet Puppy Exquis Chicken Pouch 300Gr Nº08 12Ud 46,44 29,64
AMANOVA POUCH GATO
S-AMU06VP8A 8413037335786 Amv Wet Cat Beef & Chicken Pouch 85Gr Nº14 12Ud 17,40 11,04
S-AMU05PS8A 8413037335793 Amv Wet Cat Salmon & Turkey Pouch 85Gr Nº11 12Ud 17,40 11,04
S-AMU04ST8A 8413037335809 Amv Wet Cat Steril Lamb&Sardi Pouch 85Gr Nº13 12Ud 17,40 11,04
S-AMU03SB8A 8413037335816 Amv Wet Cat Steril. Fish&Turk Pouch 85Gr Nº12 12Ud 17,40 11,04
S-AMU02SP8A 8413037335779 Amv Wet Cat Sterilis. Chicken Pouch 85Gr Nº10 12Ud 17,40 11,04
S-AMU01KT8A 8413037335823 Amv Wet Kitten Chicken & Fish Pouch 85Gr Nº09 12Ud 17,40 11,04
AMANOVA LATAS GATO
S-WEV75CC7A 8413037333607 Amv Wet Cat Chicken & Cheese Broth 70Gr Nº02 24Ud 34,80 22,08
S-WEV77CS7A 8413037333645 Amv Wet Cat Chicken & Gambas Jelly 70Gr Nº06 24Ud 34,80 22,08
S-WEV79CT7A 8413037333638 Amv Wet Cat Chicken & Tuna Broth 70Gr Nº05 24Ud 34,80 22,08
S-WEV80CF7A 8413037333591 Amv Wet Cat Chicken Fillets Broth 70Gr Nº01 24Ud 34,80 22,08
S-WEV86SW7A 8413037333713 Amv Wet Cat Tuna & Algas Jelly 70Gr Nº13 24Ud 34,80 22,08
S-WEV89TW7A 8413037333676 Amv Wet Cat Tuna & Anchoveta Broth 70Gr Nº09 24Ud 34,80 22,08
Cod. Producto Cod. Ean Descripción
Tarifa
P.V.P.R.
Tarifa P.V.T.
S-WEV82TC7A 8413037333690 Amv Wet Cat Tuna & Cangrejo Jelly 70Gr Nº11 24Ud 34,80 22,08
S-WEV88TB7A 8413037333706 Amv Wet Cat Tuna & Gambas Broth 70Gr Nº12 24Ud 34,80 22,08
S-WEV87TH7A 8413037333683 Amv Wet Cat Tuna & Gambas Jelly 70Gr Nº10 24Ud 34,80 22,08
S-WEV85TS7A 8413037333720 Amv Wet Cat Tuna & Sardines Jelly 70Gr Nº14 24Ud 34,80 22,08
S-WEV83TF7A 8413037333652 Amv Wet Cat Tuna Fillets Broth 70Gr Nº07 24Ud 34,80 22,08
AMANOVA STICK DENTAL
S-SNV17ML1A 8413037371364 Amv Stick Dental Medium & Large 10X180Gr 38,30 22,90
S-SNV16AN1A 8413037371357 Amv Stick Dental Small & Mini 12X110Gr 34,32 20,52
AMANOVA WHITE HAIR
S-AMJ16WH02 8413037378257 Amv Adult White Hair 2Kg 21,31 12,73
S-AMJ16WH07 8413037378264 Amv Adult White Hair 7Kg 58,20 34,77
S-AMJ16WH8A 8413037378240 Amv Adult White Hair 800Gr 11,60 6,93
"""

# 5. Procesar los datos
lineas = datos_pdf.strip().split('\n')
insertados = 0
omitidos = 0

# Este "radar" mágico busca: Ref. Original + Código Barras (8 a 14 números) + Nombre + PVP + Coste
patron = re.compile(r'^(\S+)\s+(\d{8,14})\s+(.+?)\s+(\d+,\d{2})\s+(\d+,\d{2})$')

for linea in lineas:
    linea = linea.strip()
    match = patron.match(linea)
    
    if match:
        ref_orig = match.group(1)
        ean = match.group(2)
        nombre = match.group(3).strip()
        pvp_str = match.group(4)
        coste_str = match.group(5)
        
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
            "igic_tipo": 7.0, # Asumimos 7% estándar
            "precio_pvp": pvp,
            "stock_actual": 0,
            "stock_minimo": 2,
            "cantidad_reponer": 5
        }).execute()
        
        if res_ins.data:
            prod_id = res_ins.data[0]['id']
            # Enlazarlo con Zotécnica
            client.table("productos_proveedores").insert({
                "producto_id": prod_id,
                "proveedor_id": prov_id,
                "precio_coste": coste
            }).execute()
            
            skus_existentes.add(nuevo_sku)
            nombres_existentes.add(nombre.lower())
            insertados += 1
            print(f"  ✅ Añadido: [{nuevo_sku}] {nombre} (PVP: {pvp}€ | Coste: {coste}€)")

print(f"\n🎉 ¡Magia completada! {insertados} productos nuevos insertados desde el PDF. {omitidos} omitidos por estar duplicados.")