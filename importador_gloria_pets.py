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
print("🔌 Conectando a Supabase para leer el PDF de Gloria Pets...")

# 1. Asegurar que el proveedor existe
NOMBRE_PROV = "Gloria Pets"
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

# 3. Generador inteligente de SKU correlativo (GP-001, GP-002...) para Gloria Pets
contador_sku = 1
def generar_sku():
    global contador_sku
    while True:
        nuevo_sku = f"GP-{contador_sku:03d}"
        if nuevo_sku not in skus_existentes:
            return nuevo_sku
        contador_sku += 1

# 4. El texto bruto copiado directamente de tu PDF
datos_pdf = """
Cod. Producto Cod. Ean Descripción Tarifa P.V.P.R. Tarifa
P.V.T
CG-3090 8432288210390 Arnes Nylon Liso Ajustable L 61-91Cm 16,47 11,53
CG-3089 8432288210338 Arnes Nylon Liso Ajustable M 47-71Cm 12,37 8,66
CG-3088 8432288210314 Arnes Nylon Liso Ajustable S 35-51Cm 10,26 7,18
CG-4121 8432288110423 Calatrava Raton con Rabito de Cuero Piel Conejo 4,56 3,19
CG-3082 8432288073889 CR00048NE Correa Nylon Redondo Negro 12X120Cm 12,44 8,71
CG-3036 8432288108826 CR00800AZ Correa Leopardo Azul 120CmX15Mm 8,17 5,72
CG-3037 8432288108833 CR00800NA Correa Leopardo Naranja 120CmX15Mm 8,17 5,72
CG-3038 8432288108840 CR00800RO Correa Leopardo Rosa 120CmX15Mm 8,17 5,72
CG-3042 8432288108888 CR00802 Correa Camuflaje 120CmX15Mm 8,17 5,72
CG-3044 8432288109014 CR00804 Correa Jeans 120CmX15Mm 8,17 5,72
CG-3045 8432288122792 CR01989 Acople Nylon 2 Perros 32-56CmX16Mm 8,79 6,15
CG-3046 8432288120880 CR01991 Acople Cadena 2 Perros 50CmX2Mm 6,37 4,46
CG-3047 8432288120897 CR01992 Acople Cadena 2 Perros 50CmX3Mm 11,06 7,74
CG-3048 8432288120903 CR01993 Acople Cadena 2 Perros 60CmX3Mm 11,73 8,21
CG-3049 8432288122273 CR01996 Acople Cadena 3 Perros 50CmX2Mm 12,51 8,76
CG-3050 8432288122280 CR01998 Acople Cadena 3 Perros 60CmX3Mm 16,49 11,54
POC-0165 5060428498198 Dispensador Bolsas Con Mini-Linterna 10Bolsas 80Gr 8,13 5,69
POC-0162 5060428497641 Dispensador De Bolsas Con Linterna 15Bolsas 140Gr 10,8 7,56
POC-0161 5060428497610 Dispensador De Gel Desinfectante 15Bolsas 140Gr 7,51 5,26
POC-0164 5060428497665 Dispensador Gel Desinfectante Mini 10Bolsas 95Gr 5,83 4,08
CG-3078 8432288110799 Display Camas Domino 60X70Cm 14Ud 376,97 263,88
CG-4131 8432288030400 Display Snackys Buey 30 Bolsitas 75Gr 35,87 25,11
CG-4133 8432288031131 Display Snackys Cachorro 30 Bolsitas 75Gr 35,87 25,11
CG-4128 8432288030431 Display Snackys Higado 30 Bolsitas 75Gr 35,87 25,11
CG-4127 8432288030363 Display Snackys Jamon 30 Bolsitas 75Gr 35,87 25,11
CG-4132 8432288030417 Display Snackys Pavo 30 Bolsitas 75Gr 35,87 25,11
CG-4129 8432288030387 Display Snackys Pescado 30 Bolsitas 75Gr 35,87 25,11
CG-4130 8432288030332 Display Snackys Pollo 30 Bolsitas 75Gr 35,87 25,11
CG-4119 8432288110492 Eero Cojin Pequeño Piel Conejo 24X7Cm 6,77 4,74
CG-4125 8432288110447 Gaudi Palo con Pompon Pequeño Piel Conejo 6Cm Dim 7,99 5,59
CG-4120 8432288110508 Gehry Cojin Grande Piel Conejo 40X11Cm 8,46 5,92
POC-0168 8424678080461 Juguetes Huevos Rie Grande Latex 18 Uds 63,03 44,12
POC-0169 8432288172049 Juguetes Huevos Rie Latex 24 Uds 62,8 43,96
CG-4126 8432288110485 Niemeyeer Palo con Gusano Piel Conejo 8,56 5,99
CG-4117 8432288106617 Pelota Dental Para Perro M 7Cm 3,97 2,78
CG-4116 8432288106624 Pelota Dental Para Perro S 5Cm 2,41 1,69
CG-4118 8432288106631 Pelota Rugby Dental Para Perro 11Cm 5,23 3,66
CG-3075 8432288110638 Peluche Champcane 4,37 3,06
CG-3072 8432288110614 Peluche Chocolate Dognut 3,84 2,69
CG-3071 8432288110607 Peluche Fries 6,84 4,79
CG-3074 8432288110621 Peluche Gloicecream 3,87 2,71
CG-3076 8432288110645 Peluche Hamburdog 4,71 3,3
CG-3002 8432288210406 PT00820RO Arnes Leopardo XS Rosa 17-22Cm/20-25Cm 10,06 7,04
CG-3003 8432288210444 PT00821AZ Arnes Leopardo S Azul 21-29Cm/25-33Cm 11,04 7,73
CG-3005 8432288210437 PT00821RO Arnes Leopardo S Rosa 21-29Cm/25-33Cm 11,04 7,73
CG-3006 8432288210901 PT00822AZ Arnes Leopardo M Azul 27-35Cm/33-40Cm 13,64 9,55
En vigor 01/02/2026
Tarifas Gloria Pets 2026 Tienda
Última modificación Ene -26
Cod. Producto Cod. Ean Descripción Tarifa P.V.P.R. Tarifa
P.V.T
CG-3011 8432288108673 PT00823RO Arnes Leopardo L Rosa 33-44Cm/44-55Cm 16,9 11,83
CG-3012 8432288210536 PT00840RO Arnes Puntos XS Rosa 17-22Cm/20-25Cm 11,86 8,3
CG-3013 8432288210543 PT00840VE Arnes Puntos XS Verde 17-22Cm/20-25Cm 11,86 8,3
CG-3017 8432288210949 PT00842VE Arnes Puntos M Verde 27-35Cm/33-40Cm 15,76 11,03
CG-3018 8432288108680 PT00843RO Arnes Puntos L Rosa 33-44Cm/44-55Cm 19,01 13,31
CG-3020 8432288106433 PT00845 Arnes Puntos XS Rojo 17-22m/20-25Cm 10,31 7,22
CG-3022 8432288106457 PT00847 Arnes Puntos M Rojo 27-35m/33-40Cm 13,61 9,53
CG-3023 8432288108703 PT00848 Arnes Puntos L Rojo 33-44m/44-55Cm 16,54 11,58
CG-3024 8432288106464 PT00850 Arnes Camuflaje XS 17-22Cm/20-25Cm 10,39 7,27
CG-3025 8432288106471 PT00851 Arnes Camuflaje S 21-29Cm/25-33Cm 11,69 8,18
CG-3028 8432288106495 PT00855 Arnes Checked XS 17-22Cm/20-25Cm 11,3 7,91
CG-3031 8432288108727 PT00858 Arnes Checked L 33-44Cm/44-55Cm 17,81 12,47
CG-3032 8432288108970 PT00860 Arnes Jeans XS 17-22Cm/20-25Cm 10,54 7,38
CG-3033 8432288108987 PT00861 Arnes Jeans S 21-29Cm/25-33Cm 11,86 8,3
CG-3034 8432288108994 PT00862 Arnes Jeans M 27-35Cm/33-40Cm 14,79 10,35
CG-3035 8432288109007 PT00863 Arnes Jeans L 33-44Cm/44-55Cm 17,39 12,17
CG-4122 8432288110430 Renzo Rata con Rabito de Cuero Piel Conejo 4,06 2,84
CG-4123 8432288110478 Rogers Rata con Rabito de Cuero Piel Conejo 12Cm 7,19 5,03
CG-4124 8432288110416 Shigeru Palo con Rata Piel Conejo 7,99 5,59
CG-3051 8432288123201 VA00520AZ Enganche Cinturon Azul 28-45CmX20Mm 5,29 3,7
CG-3052 8432288123218 VA00520MO Enganche Cinturon Morado 28-45CmX20Mm 5,29 3,7
CG-3053 8432288232798 VA00520NE Enganche Cinturon Negro 28-45CmX20Mm 5,29 3,7
CG-3054 8432288123225 VA00520RJ Enganche Cinturon Rojo 28-45CmX20Mm 5,29 3,7
CG-3055 8432288123232 VA00520RO Enganche Cinturon Rosa 28-45CmX20Mm 5,29 3,7
CG-3056 8432288123249 VA00520VE Enganche Cinturon Verde 28-45CmX20Mm 5,29 3,7
"""

# 5. Procesar los datos
lineas = datos_pdf.strip().split('\n')
insertados = 0
omitidos = 0

# Este "radar" busca: Ref. Original + Código Barras (8 a 14 números) + Nombre + PVP + Coste
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
            "igic_tipo": 3.0, # IGIC al 3% según indicación
            "precio_pvp": pvp,
            "stock_actual": 0,
            "stock_minimo": 2,
            "cantidad_reponer": 5
        }).execute()
        
        if res_ins.data:
            prod_id = res_ins.data[0]['id']
            # Enlazarlo con Gloria Pets
            client.table("productos_proveedores").insert({
                "producto_id": prod_id,
                "proveedor_id": prov_id,
                "precio_coste": coste
            }).execute()
            
            skus_existentes.add(nuevo_sku)
            nombres_existentes.add(nombre.lower())
            insertados += 1
            print(f"  ✅ Añadido: [{nuevo_sku}] {nombre} (PVP: {pvp}€ | Coste: {coste}€)")

print(f"\n🎉 ¡Magia completada! {insertados} productos nuevos de Gloria Pets insertados. {omitidos} omitidos por estar duplicados.")
