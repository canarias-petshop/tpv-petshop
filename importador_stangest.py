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
print("🔌 Conectando a Supabase para leer el PDF de Stangest...")

# 1. Asegurar que el proveedor existe
NOMBRE_PROV = "Stangest"
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

# 3. Generador inteligente de SKU correlativo (ST-001, ST-002...) para Stangest
contador_sku = 1
def generar_sku():
    global contador_sku
    while True:
        nuevo_sku = f"ST-{contador_sku:03d}"
        if nuevo_sku not in skus_existentes:
            return nuevo_sku
        contador_sku += 1

# 4. El texto bruto copiado directamente de tu PDF
datos_pdf = """
Cod. Producto Cod. Ean Descripción Tarifa
P.V.P.R.
Tarifa
P.V.T.
OT-024 8436020784026 Anima Strath 100Ml 18,79 13,15
OT-060 8436020787676 Anima Strath 1L 117,16 82,01
OT-066 8436020786068 Anima Strath 250Ml 35,41 24,79
OT-067 8436020788451 Anima Strath 30Ml Expositor 9Ud 69,60 48,72
OT-068 8436020784064 Anima Strath 360Comp 170,03 119,02
OT-0240 8436020786501 Anima Strath Pasta 125Gr 19,71 13,80
OT-040 8436020788260 Anima Strath Tomillo 100Ml 25,53 17,87
OT-070 8436020788666 Anima Strath Tomillo 9x30Ml 100,96 70,67
OT-026 8436020787096 Calcio Fosforo (Dicalfon) 100 Comp 8,16 5,71
OT-1604 8436020787904 Can Bel 60Ml 8,40 5,88
OT-1045 8436020784927 Condrocare 30Comp 48,74 34,12
OT-1044 8436020784965 Condrocare 240Comp Blister 282,86 198,00
OT-071 8436020784354 Coprovet 50Gr 15,71 11,00
DI0140 8436020784835 Cronicare 100Ml 91,80 64,26
OT-1210 8436020784989 Cronicare 120 Comp 71,09 49,76
OT-1214 8436020786488 Cronicare 300 Comp (30 Blister x 10 Comp) 292,86 205,00
OT-059 8436020784545 Cronicare 30Ml 34,43 24,10
DI0141 8436020784972 Cronicare 60 Comp 40,29 28,20
OT-1211 8436020786440 Cronicare Collar 20,00 14,00
OT-1215 8436020786457 Cronicare Synergy 10Ml 37,64 26,35
OT-072 8436020788185 Curtivet Spray 125 Ml 12,16 8,51
OT-041 8436020787805 Dentican Kit Dental Cepillo + Pasta 14,51 10,16
OT-074 8436020788307 Dentican Soluble 250Ml 12,79 8,95
OT-073 8436020787935 Dentican Soluble 500Ml 18,36 12,85
OT-018 8436020787003 Dentican Spray 125Ml 10,46 7,32
OT-029 8436020787874 Dentisan 180Gr 28,86 20,20
OT-022 8436020788208 Dentivet Proteccion Total 125Ml 14,07 9,85
OT-035 8436020787492 Dermovital Omega 3.6.9 60 Caps 22,14 15,50
OT-1212 8436020786242 Gastroprotect 30 Comp 23,50 16,45
OT-1216 8436020786471 Gastroprotect Blister 120 Comp (12x10) 119,71 83,80
AC005 8436020788062 Gradual Action Cardio-I G/C 60 Comp 31,09 21,76
AC006 8436020788079 Gradual Action Cardio-II Carnitine 60 Comp 29,71 20,80
AC009 8436020788109 Gradual Action Enzivet Alquerzim 60 Comp 25,57 17,90
AC015 8436020788161 Gradual Action Gingivet 60 Comp 28,23 19,76
AC022 84360207861811 Gradual Action Gingivet Pasta 100Gr 18,71 13,10
AC007 8436020788048 Gradual Action Hepa-T Detox 60 Comp 23,71 16,60
AC018 8436020788512 Gradual Action Histamin Control 60 Comp 34,29 24,00
AC019 8436020784491 Gradual Action Histamin Control 60Comp Razas Gdes 66,14 46,30
AC008 8436020788055 Gradual Action Neurovet 60 Comp 30,21 21,15
AC012 8436020788086 Gradual Action Ocuhealth 60 Comp 25,14 17,60
AC013 8436020788093 Gradual Action Oncovet I 60 Comp 30,86 21,60
AC017 8436020788284 Gradual Action Urovet-C 100Gr Pasta 30,00 21,00
AC016 8436020788291 Gradual Action Urovet-RQ 100Gr Pasta 26,86 18,80
OT-1605 8436020784910 Heliovet Protector Solar 50Gr (SPF 50+) 17,77 12,44
Tarifas Stangest 2026 Tienda
En vigor 01/02/2026
Última modificación feb-26
Cod. Producto Cod. Ean Descripción Tarifa
P.V.P.R.
Tarifa
P.V.T.
OT-1606 8436020786198 Heliovet Spray Solar 80Ml (SPF 50) 19,57 13,70
OT-036 8436020788437 Krill Vet 60 Comp 32,60 22,82
OT-033 8436020787577 M.S.M. 60 Comp 26,84 18,79
OT-075 8436020787553 Optican Limpiador Ojos 125Ml 8,07 5,65
OT-076 8436020787027 Otican Limpiador Oidos 125Ml 8,50 5,95
OT-1601 8436020787300 Piss Can 200Ml 10,29 7,20
OT-1602 8436020787034 Piss Stop 200Ml 10,14 7,10
OT-1603 8436020787607 Piss Stop 500Ml 18,36 12,85
OT-077 8436020787447 Pulfin Ambiental 500Ml 15,14 10,60
OT-078 8436020788529 Pulfin Fogger IGR 150Ml 16,59 11,61
OT-1400 8436020784712 Stanvet Life Spray 500Ml 16,01 11,21
OT-1600 8436020787058 Stanvet Malta 100Gr 10,21 7,15
OT-1401 8436020784552 Stanvet Life Pipetas 4Ud 20,80 14,56
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
            # Enlazarlo con Stangest
            client.table("productos_proveedores").insert({
                "producto_id": prod_id,
                "proveedor_id": prov_id,
                "precio_coste": coste
            }).execute()
            
            skus_existentes.add(nuevo_sku)
            nombres_existentes.add(nombre.lower())
            insertados += 1
            print(f"  ✅ Añadido: [{nuevo_sku}] {nombre} (PVP: {pvp}€ | Coste: {coste}€ | EAN: {ean if ean else 'Faltante'})")

print(f"\n🎉 ¡Magia completada! {insertados} productos nuevos de Stangest insertados. {omitidos} omitidos.")