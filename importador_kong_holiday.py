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
print("🔌 Conectando a Supabase para leer el PDF de Kong Holiday...")

# 1. Asegurar que el proveedor existe
NOMBRE_PROV = "Kong Holiday"
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

# 3. Generador inteligente de SKU correlativo (KO-001, KO-002...) para Kong
contador_sku = 1
def generar_sku():
    global contador_sku
    while True:
        nuevo_sku = f"KO-{contador_sku:03d}"
        if nuevo_sku not in skus_existentes:
            return nuevo_sku
        contador_sku += 1

# 4. El texto bruto copiado directamente de tu PDF
datos_pdf = """
Cod. Producto Cod. Ean Descripción Tarifa P.V.P.R. Tarifa
P.V.T
CG-4160 35585468129 H22C147 Holiday Pull-A-Partz Present 6,39 4,47
CG-4161 35585468167 H22C148 Holiday Crackles Santa Kitty 5,96 4,17
CG-4163 35585468105 H22C153 Holiday Crackles Christmas Tree 4,79 3,35
CG-4164 35585468198 H22C154 Holiday Cat Active Curlz 2Ud 5,11 3,58
CG-4166 35585468181 H22C158 Holiday Puzzlements Hideaway Ginger 6,81 4,77
CG-4141 35585514154 H22D121 Holiday Cozie Reindeer M 9,81 6,87
CG-4143 35585514178 H22D123 Holiday Comfort Polar Bear Assorted M/L 11,09 7,76
CG-4145 35585502366 H22D128 Holiday Comfort Hedgehug M 9,81 6,87
CG-4147 35585514192 H22D131 Holiday Occasions Sleigh M 18,76 13,13
CG-4148 35585514208 H22D132 Holiday Occasions Balls 4Ud M 13,21 9,25
CG-4150 35585502373 H22D134 Holiday Corestrength Rattlez Stick Assor L 12,80 8,96
CG-4152 35585502380 H22D136 Holiday Jaxx Brights Tug W/Ball Assorted M 10,66 7,46
CG-4156 35585502427 H22D141 Holiday Airdog Stick L 11,09 7,76
CG-4158 35585502458 H22D145 Holiday Squeakair Balls 6Ud S 8,53 5,97
CG-4171 35585502915 H23D111 Holiday Wubba Assorted L 14,49 10,14
CG-4174 35585526089 H23D112 Holiday Wild Knots Bear Assorted M/L 13,04 9,13
CG-4173 35585526096 H23D113 Holiday Wild Knots Bear Assorted S/M 10,23 7,16
CG-4172 35585526157 H23PDQC142 Holiday Scrattles Cafe Pqd 12 Piece 39,79 27,85
CG-4178 35585468365 H25C147 Holiday Crackles Christmas Tree 4,34 3,04
CG-4175 35585507026 H25D129 Holiday Snuzzles Penguin 10,07 7,05
CG-4177 35585506999 H25D131 Holiday Snuzzles Reindeer Md 13,17 9,22
CG-4176 35585506982 H25D131 Holiday Snuzzles Reindeer Sm 10,07 7,05
CG-4179 35585506821 H25D133 KONG Holiday SqueakAir Balls 6-pk Md 11,38 7,97
CG-4180 35585506838 H25D134 KONG Holiday SqueakAir Balls 6-pk Sm 8,52 5,97
CG-4181 35585506814 H25D138 KONG Holiday Stocking Paw Lg 8,98 6,29
CG-4182 35585535166 H25D139 KONG Holiday Wild Knots Bear Assorted Md/L 12,40 8,68
En vigor 01/02/2025
Tarifas Kong Holiday 2025 Tienda
Última modificación Nov -25
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
            "igic_tipo": 3.0, # IGIC al 3% según política estricta de la tienda
            "precio_pvp": pvp,
            "stock_actual": 0,
            "stock_minimo": 2,
            "cantidad_reponer": 5
        }).execute()
        
        if res_ins.data:
            prod_id = res_ins.data[0]['id']
            # Enlazarlo con Kong Holiday
            client.table("productos_proveedores").insert({
                "producto_id": prod_id,
                "proveedor_id": prov_id,
                "precio_coste": coste
            }).execute()
            
            skus_existentes.add(nuevo_sku)
            nombres_existentes.add(nombre.lower())
            insertados += 1
            print(f"  ✅ Añadido: [{nuevo_sku}] {nombre} (PVP: {pvp}€ | Coste: {coste}€)")

print(f"\n🎉 ¡Magia completada! {insertados} productos nuevos de Kong Holiday insertados. {omitidos} omitidos.")