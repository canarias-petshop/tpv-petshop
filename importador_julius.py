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
print("🔌 Conectando a Supabase para leer el PDF de Julius...")

# 1. Asegurar que el proveedor existe
NOMBRE_PROV = "Julius"
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

# 3. Generador inteligente de SKU correlativo (K9-001, K9-002...) para Julius
contador_sku = 1
def generar_sku():
    global contador_sku
    while True:
        nuevo_sku = f"K9-{contador_sku:03d}"
        if nuevo_sku not in skus_existentes:
            return nuevo_sku
        contador_sku += 1

# 4. El texto bruto copiado directamente de tu PDF
datos_pdf = """
Cod. Producto Cod. Ean Descripción Tarifa P.V.P.R. Tarifa
P.V.T
CJ-0220 5999053659417 Julius K9 Arnes cinta Color & Gray 0 Azul 27,00 18,90
CJ-0238 5999053679453 Julius K9 Arnes cinta Color & Gray 0 Naranja 27,00 18,90
CJ-0214 5999053659691 Julius K9 Arnes cinta Color & Gray 0 Negro 27,00 18,90
CJ-0244 5999053681234 Julius K9 Arnes cinta Color & Gray 0 Neon 27,00 18,90
CJ-0226 5999053661861 Julius K9 Arnes cinta Color & Gray 0 Rojo 27,00 18,90
CJ-0232 5999053661878 Julius K9 Arnes cinta Color & Gray 0 Rosa 27,00 18,90
CJ-0221 5999053662639 Julius K9 Arnes cinta Color & Gray 1 Azul 38,88 27,21
CJ-0239 5999053679408 Julius K9 Arnes cinta Color & Gray 1 Naranja 38,88 27,21
CJ-0215 5999053662578 Julius K9 Arnes cinta Color & Gray 1 Negro 38,88 27,21
CJ-0245 5999053680602 Julius K9 Arnes cinta Color & Gray 1 Neon 38,88 27,21
CJ-0227 5999053662608 Julius K9 Arnes cinta Color & Gray 1 Rojo 38,88 27,21
CJ-0222 5999053662646 Julius K9 Arnes cinta Color & Gray 2 Azul 39,18 27,42
CJ-0216 5999053662585 Julius K9 Arnes cinta Color & Gray 2 Negro 39,18 27,42
CJ-0228 5999053662615 Julius K9 Arnes cinta Color & Gray 2 Rojo 39,18 27,42
CJ-0234 5999053662677 Julius K9 Arnes cinta Color & Gray 2 Rosa 39,18 27,42
CJ-0223 5999053662653 Julius K9 Arnes cinta Color & Gray 3 Azul 41,02 28,71
CJ-0241 5999053679422 Julius K9 Arnes cinta Color & Gray 3 Naranja 41,02 28,71
CJ-0217 5999053662592 Julius K9 Arnes cinta Color & Gray 3 Negro 41,02 28,71
CJ-0247 5999053680626 Julius K9 Arnes cinta Color & Gray 3 Neon 41,02 28,71
CJ-0229 5999053662622 Julius K9 Arnes cinta Color & Gray 3 Rojo 41,02 28,71
CJ-0235 5999053662684 Julius K9 Arnes cinta Color & Gray 3 Rosa 41,02 28,71
CJ-0219 5999053659431 Julius K9 Arnes cinta Color & Gray Mini Azul 22,36 15,65
CJ-0218 5999053659424 Julius K9 Arnes cinta Color & Gray Mini Mini Azul 21,29 14,90
CJ-0212 5999053659684 Julius K9 Arnes cinta Color & Gray Mini Mini Negro 21,29 14,90
CJ-0242 5999053680589 Julius K9 Arnes cinta Color & Gray Mini Mini Neon 21,29 14,90
CJ-0224 5999053661847 Julius K9 Arnes cinta Color & Gray Mini Mini Rojo 21,29 14,90
CJ-0230 5999053661854 Julius K9 Arnes cinta Color & Gray Mini Mini Rosa 21,29 14,90
CJ-0237 5999053679446 Julius K9 Arnes cinta Color & Gray Mini Naranja 22,36 15,65
CJ-0243 5999053680596 Julius K9 Arnes cinta Color & Gray Mini Neon 22,36 15,65
CJ-0225 5999053661823 Julius K9 Arnes cinta Color & Gray Mini Rojo 22,36 15,65
CJ-0231 5999053661830 Julius K9 Arnes cinta Color & Gray Mini Rosa 22,36 15,65
CJ-0236 5999053679439 Julius K9 Arnes cinta Color&Gray Mini Mini Naranj 21,29 14,90
CJ-0320 5999053670771 Julius K9 Asa arnes invidente regul 35 45cm 70,29 49,20
CJ-0319 5999053608163 Julius K9 Asa para arnes invidente 16cmx45cm 34,09 23,86
CJ-0318 5999053662844 Julius K9 Asa para arnes invidente 35 cm 32,33 22,63
CJ-0314 5999053676315 Julius K9 Asa para arnes invidente 40 cm 34,09 23,86
CJ-0315 5999053676322 Julius K9 Asa para arnes invidente 50 cm 34,09 23,86
CJ-0316 5999053676339 Julius K9 Asa para arnes invidente 55 cm 34,09 23,86
CJ-0317 5999053675653 Julius K9 Asa para arnes invidente 60 cm 34,09 23,86
CJ-0313 5999053675783 Julius K9 Bolsas Laterales 0 1 par Camuflaje 31,92 22,34
CJ-0312 5999053675110 Julius K9 Bolsas Laterales 1 2 1 par Neon 34,98 24,48
CJ-0311 5999053660529 Julius K9 Bolsas universales Mini 4 Azul 22,76 15,93
CJ-0287 5999053651398 Julius K9 ESPAÑA Bandera Etiqueta Grande 4,96 3,47
CJ-0286 5999053651381 Julius K9 ESPAÑA Bandera Etiqueta Pequeña 4,96 3,47
CJ-0295 5999053657604 Julius K9 Etiqueta grande CORREMOS?? 1Par 4,33 3,03
CJ-0296 5999053657611 Julius K9 Etiqueta grande CUIDADO! 1Par 4,33 3,03
CJ-0297 5999053632168 Julius K9 Etiqueta grande FBI 1Par 4,33 3,03
CJ-0298 5999053632441 Julius K9 Etiqueta grande HAPPY 1Par 4,33 3,03
CJ-0299 5999053632540 Julius K9 Etiqueta grande HOT DOG 1Par 4,33 3,03
CJ-0300 5999053634155 Julius K9 Etiqueta grande SHERIFF 1Par 4,33 3,03
CJ-0301 5999053608996 Julius K9 Etiqueta grande SUPERDOG 1Par 4,33 3,03
CJ-0302 5999053657659 Julius K9 Etiqueta grande TIENES CHUCHES? 1Par 4,33 3,03
CJ-0294 5999053657550 Julius K9 Etiqueta peq TIENES CHUCHES?1Par 4,33 3,03
CJ-0288 5999053657505 Julius K9 Etiqueta pequeña CORREMOS?? 1Par 4,33 3,03
CJ-0289 5999053657512 Julius K9 Etiqueta pequeña CUIDADO! 1Par 4,33 3,03
CJ-0290 5999053635794 Julius K9 Etiqueta pequeña FBI 1Par 4,33 3,03
CJ-0291 5999053636173 Julius K9 Etiqueta pequeña HOT DOG 1Par 4,33 3,03
CJ-0292 5999053630560 Julius K9 Etiqueta pequeña SHERIFF 1Par 4,33 3,03
CJ-0293 5999053608132 Julius K9 Etiqueta pequeña SUPERDOG 1Par 4,33 3,03
CJ-0309 5999053629472 Julius K9 Etiqueta personalizada Baby1 blanco 5,50 3,85
CJ-0305 5999053659592 Julius K9 Etiqueta personalizada Grande Blanco 5,50 3,85
CJ-0308 5999053659639 Julius K9 Etiqueta personalizada Pequeña blanco 5,50 3,85
CJ-0280 5999053679361 Julius K9 IDC Longwalk black gray 2XL 73,79 51,65
CJ-0276 5999053678838 Julius K9 IDC Longwalk black gray L 68,53 47,97
CJ-0278 5999053678814 Julius K9 IDC Longwalk black gray S 63,22 44,25
CJ-0268 5999053678715 Julius K9 IDC Longwalk blue gray S 63,22 44,25
CJ-0269 5999053678746 Julius K9 IDC Longwalk blue gray XL 71,70 50,19
CJ-0275 5999053679347 Julius K9 IDC Longwalk neon gray 2XL 73,79 51,65
CJ-0272 5999053678777 Julius K9 IDC Longwalk neon gray M 66,38 46,46
CJ-0273 5999053678760 Julius K9 IDC Longwalk neon gray S 63,22 44,25
CJ-0274 5999053678791 Julius K9 IDC Longwalk neon gray XL 71,70 50,19
CJ-0285 5999053679385 Julius K9 IDC Longwalk red gray 2XL 73,79 51,65
CJ-0282 5999053678876 Julius K9 IDC Longwalk red gray M 66,38 46,46
CJ-0284 5999053678890 Julius K9 IDC Longwalk red gray XL 71,70 50,19
CJ-0047 5999053645533 Julius K9 IDC Powerharness 0 Agua marina 40,95 28,66
CJ-0261 5999053655983 Julius K9 IDC Powerharness 0 Americano 44,40 31,08
CJ-0182 5999053670511 Julius K9 IDC Powerharness 0 Arco Iris 40,93 28,65
CJ-0029 5999053616465 Julius K9 IDC Powerharness 0 Azul 40,95 28,66
CJ-0038 5999053642839 Julius K9 IDC Powerharness 0 Camuflaje 40,95 28,66
CJ-0164 5999053669799 Julius K9 IDC Powerharness 0 Chocolate 40,95 28,66
CJ-0252 5999053672959 Julius K9 IDC Powerharness 0 España 40,95 28,66
CJ-0128 5999053665531 Julius K9 IDC Powerharness 0 Fucsia 40,95 28,66
CJ-0110 5999053665555 Julius K9 IDC Powerharness 0 Granate 40,93 28,65
CJ-0101 5999053665548 Julius K9 IDC Powerharness 0 Gris Antracita 40,93 28,65
CJ-0137 5999053665807 Julius K9 IDC Powerharness 0 Jeans 40,93 28,65
CJ-0011 5999053616441 Julius K9 IDC Powerharness 0 Negro 40,95 28,66
En vigor 01/03/2024
Tarifas Julius 2025 Tienda
Última modificación Abr -25
Cod. Producto Cod. Ean Descripción Tarifa P.V.P.R. Tarifa
P.V.T
CJ-0074 5999053616540 Julius K9 IDC Powerharness 0 Neon 40,95 28,66
CJ-0065 5999053640972 Julius K9 IDC Powerharness 0 Purpura 40,95 28,66
CJ-0344 5999053685430 Julius K9 IDC Powerharness 0 Purpura Oscuro 40,95 28,66
CJ-0020 5999053616458 Julius K9 IDC Powerharness 0 Rojo 40,95 28,66
CJ-0056 5999053616526 Julius K9 IDC Powerharness 0 Rosa 40,95 28,66
CJ-0092 5999053664503 Julius K9 IDC Powerharness 0 Rosa Flores 40,93 28,65
CJ-0083 5999053659820 Julius K9 IDC Powerharness 0 UV Naranja 40,95 28,66
CJ-0146 5999053670429 Julius K9 IDC Powerharness 0 Vaquero 40,95 28,66
CJ-0155 5999053671556 Julius K9 IDC Powerharness 0 vaquero y neon 40,95 28,66
CJ-0119 5999053665524 Julius K9 IDC Powerharness 0 Verde 40,93 28,65
CJ-0173 5999053670245 Julius K9 IDC Powerharness 0 Verde Claro 40,95 28,66
CJ-0048 5999053645540 Julius K9 IDC Powerharness 1 Agua marina 43,70 30,59
CJ-0262 5999053655990 Julius K9 IDC Powerharness 1 Americano 47,16 33,01
CJ-0183 5999053670528 Julius K9 IDC Powerharness 1 Arco Iris 43,70 30,59
CJ-0030 5999053616571 Julius K9 IDC Powerharness 1 Azul 43,70 30,59
CJ-0039 5999053642846 Julius K9 IDC Powerharness 1 Camuflaje 43,70 30,59
CJ-0165 5999053669805 Julius K9 IDC Powerharness 1 Chocolate 43,70 30,59
CJ-0253 5999053672966 Julius K9 IDC Powerharness 1 España 43,70 30,59
CJ-0129 5999053665579 Julius K9 IDC Powerharness 1 Fucsia 43,70 30,59
CJ-0111 5999053665593 Julius K9 IDC Powerharness 1 Granate 43,70 30,59
CJ-0102 5999053665586 Julius K9 IDC Powerharness 1 Gris Antracita 43,70 30,59
CJ-0012 5999053616557 Julius K9 IDC Powerharness 1 Negro 43,70 30,59
CJ-0075 5999053616656 Julius K9 IDC Powerharness 1 Neon 43,70 30,59
CJ-0066 5999053640989 Julius K9 IDC Powerharness 1 Purpura 43,70 30,59
CJ-0345 5999053685447 Julius K9 IDC Powerharness 1 Purpura Oscuro 43,70 30,59
CJ-0021 5999053616564 Julius K9 IDC Powerharness 1 Rojo 43,70 30,59
CJ-0057 5999053616632 Julius K9 IDC Powerharness 1 Rosa 43,70 30,59
CJ-0093 5999053664510 Julius K9 IDC Powerharness 1 Rosa Flores 43,70 30,59
CJ-0084 5999053659837 Julius K9 IDC Powerharness 1 UV Naranja 43,70 30,59
CJ-0147 5999053670436 Julius K9 IDC Powerharness 1 Vaquero 43,70 30,59
CJ-0156 5999053671563 Julius K9 IDC Powerharness 1 vaquero y neon 43,70 30,59
CJ-0120 5999053665562 Julius K9 IDC Powerharness 1 Verde 43,70 30,59
CJ-0174 5999053670252 Julius K9 IDC Powerharness 1 Verde Claro 43,70 30,59
CJ-0049 5999053645557 Julius K9 IDC Powerharness 2 Agua marina 43,70 30,59
CJ-0263 5999053656003 Julius K9 IDC Powerharness 2 Americano 47,16 33,01
CJ-0184 5999053670535 Julius K9 IDC Powerharness 2 Arco Iris 43,70 30,59
CJ-0031 5999053616687 Julius K9 IDC Powerharness 2 Azul 43,70 30,59
CJ-0040 5999053642853 Julius K9 IDC Powerharness 2 Camuflaje 43,70 30,59
CJ-0166 5999053669812 Julius K9 IDC Powerharness 2 Chocolate 43,70 30,59
CJ-0254 5999053672973 Julius K9 IDC Powerharness 2 España 43,70 30,59
CJ-0130 5999053665616 Julius K9 IDC Powerharness 2 Fucsia 43,70 30,59
CJ-0112 5999053665630 Julius K9 IDC Powerharness 2 Granate 43,70 30,59
CJ-0103 5999053665623 Julius K9 IDC Powerharness 2 Gris Antracita 43,70 30,59
CJ-0013 5999053616663 Julius K9 IDC Powerharness 2 Negro 43,70 30,59
CJ-0067 5999053640996 Julius K9 IDC Powerharness 2 Purpura 43,70 30,59
CJ-0347 5999053685454 Julius K9 IDC Powerharness 2 Purpura Oscuro 43,70 30,59
CJ-0022 5999053616670 Julius K9 IDC Powerharness 2 Rojo 43,70 30,59
CJ-0058 5999053616748 Julius K9 IDC Powerharness 2 Rosa 43,70 30,59
CJ-0094 5999053664527 Julius K9 IDC Powerharness 2 Rosa Flores 43,70 30,59
CJ-0085 5999053659844 Julius K9 IDC Powerharness 2 UV Naranja 43,70 30,59
CJ-0148 5999053670443 Julius K9 IDC Powerharness 2 Vaquero 43,70 30,59
CJ-0157 5999053671570 Julius K9 IDC Powerharness 2 vaquero y neon 43,70 30,59
CJ-0175 5999053670269 Julius K9 IDC Powerharness 2 Verde Claro 43,70 30,59
CJ-0050 5999053645564 Julius K9 IDC Powerharness 3 Agua marina 43,70 30,59
CJ-0264 5999053656010 Julius K9 IDC Powerharness 3 Americano 47,16 33,01
CJ-0185 5999053670542 Julius K9 IDC Powerharness 3 Arco Iris 43,70 30,59
CJ-0188 5999053671419 Julius K9 IDC Powerharness 3 Attila 43,70 30,59
CJ-0032 5999053616793 Julius K9 IDC Powerharness 3 Azul 43,70 30,59
CJ-0041 5999053642860 Julius K9 IDC Powerharness 3 Camuflaje 43,70 30,59
CJ-0167 5999053669829 Julius K9 IDC Powerharness 3 Chocolate 43,70 30,59
CJ-0255 5999053672980 Julius K9 IDC Powerharness 3 España 43,70 30,59
CJ-0113 5999053665678 Julius K9 IDC Powerharness 3 Granate 43,70 30,59
CJ-0104 5999053665661 Julius K9 IDC Powerharness 3 Gris Antracita 43,70 30,59
CJ-0140 5999053665838 Julius K9 IDC Powerharness 3 Jeans 43,70 30,59
CJ-0014 5999053616779 Julius K9 IDC Powerharness 3 Negro 43,70 30,59
CJ-0077 5999053616878 Julius K9 IDC Powerharness 3 Neon 43,70 30,59
CJ-0068 5999053641009 Julius K9 IDC Powerharness 3 Purpura 43,70 30,59
CJ-0346 5999053685423 Julius K9 IDC Powerharness 3 Purpura Oscuro 43,70 30,59
CJ-0023 5999053616786 Julius K9 IDC Powerharness 3 Rojo 43,70 30,59
CJ-0059 5999053616854 Julius K9 IDC Powerharness 3 Rosa 43,70 30,59
CJ-0095 5999053664534 Julius K9 IDC Powerharness 3 Rosa Flores 43,70 30,59
CJ-0086 5999053659851 Julius K9 IDC Powerharness 3 UV Naranja 43,70 30,59
CJ-0149 5999053670450 Julius K9 IDC Powerharness 3 Vaquero 43,70 30,59
CJ-0158 5999053671587 Julius K9 IDC Powerharness 3 vaquero y neon 43,70 30,59
CJ-0122 5999053665647 Julius K9 IDC Powerharness 3 Verde 43,70 30,59
CJ-0176 5999053670276 Julius K9 IDC Powerharness 3 Verde Claro 43,70 30,59
CJ-0051 5999053645571 Julius K9 IDC Powerharness 4 Agua marina 51,50 36,05
CJ-0265 5999053656027 Julius K9 IDC Powerharness 4 Americano 55,08 38,55
CJ-0186 5999053670559 Julius K9 IDC Powerharness 4 Arco Iris 51,50 36,05
CJ-0189 5999053671426 Julius K9 IDC Powerharness 4 Attila 51,50 36,05
CJ-0033 5999053616908 Julius K9 IDC Powerharness 4 Azul 51,50 36,05
CJ-0042 5999053642877 Julius K9 IDC Powerharness 4 Camuflaje 51,50 36,05
CJ-0168 5999053669836 Julius K9 IDC Powerharness 4 Chocolate 51,50 36,05
CJ-0256 5999053672997 Julius K9 IDC Powerharness 4 España 51,50 36,05
CJ-0114 5999053665715 Julius K9 IDC Powerharness 4 Granate 51,50 36,05
CJ-0105 5999053665708 Julius K9 IDC Powerharness 4 Gris Antracita 51,50 36,05
CJ-0141 5999053665845 Julius K9 IDC Powerharness 4 Jeans 51,50 36,05
CJ-0015 5999053616885 Julius K9 IDC Powerharness 4 Negro 51,50 36,05
CJ-0069 5999053641016 Julius K9 IDC Powerharness 4 Purpura 51,50 36,05
CJ-0211 5999053667757 Julius K9 IDC Powerharness 4 Reggae Canis 55,08 38,55
CJ-0024 5999053616892 Julius K9 IDC Powerharness 4 Rojo 51,50 36,05
CJ-0096 5999053664541 Julius K9 IDC Powerharness 4 Rosa Flores 51,50 36,05
CJ-0087 5999053659868 Julius K9 IDC Powerharness 4 UV Naranja 51,50 36,05
CJ-0150 5999053670467 Julius K9 IDC Powerharness 4 Vaquero 51,50 36,05
CJ-0159 5999053671594 Julius K9 IDC Powerharness 4 vaquero y neon 51,50 36,05
CJ-0177 5999053670283 Julius K9 IDC Powerharness 4 Verde Claro 51,50 36,05
CJ-0190 5999053617189 Julius K9 IDC Powerharness anillas lat 0 Negro 40,95 28,66
CJ-0191 5999053617202 Julius K9 IDC Powerharness anillas lat 1 Negro 43,70 30,59
CJ-0192 5999053617226 Julius K9 IDC Powerharness anillas lat 2 Negro 43,70 30,59
CJ-0193 5999053617240 Julius K9 IDC Powerharness anillas lat 3 Negro 43,70 30,59
CJ-0043 5999053645496 Julius K9 IDC Powerharness Baby 1 Agua marina 18,75 13,12
CJ-0257 5999053655945 Julius K9 IDC Powerharness Baby 1 Americano 22,89 16,02
CJ-0025 5999053616021 Julius K9 IDC Powerharness Baby 1 Azul 18,75 13,12
CJ-0034 5999053642792 Julius K9 IDC Powerharness Baby 1 Camuflaje 18,75 13,12
CJ-0160 5999053669751 Julius K9 IDC Powerharness Baby 1 Chocolate 18,75 13,12
CJ-0248 5999053672911 Julius K9 IDC Powerharness Baby 1 España 18,75 13,12
CJ-0124 5999053665371 Julius K9 IDC Powerharness Baby 1 Fucsia 18,75 13,12
CJ-0106 5999053665395 Julius K9 IDC Powerharness Baby 1 Granate 18,75 13,12
CJ-0097 5999053665388 Julius K9 IDC Powerharness Baby 1 Gris Antracita 18,75 13,12
CJ-0133 5999053665760 Julius K9 IDC Powerharness Baby 1 Jeans 18,75 13,12
CJ-0007 5999053616007 Julius K9 IDC Powerharness Baby 1 Negro 18,75 13,12
CJ-0070 5999053616106 Julius K9 IDC Powerharness Baby 1 Neon 18,75 13,12
CJ-0340 5999053685393 Julius K9 IDC Powerharness Baby 1 Purpura Oscuro 18,75 13,12
CJ-0016 5999053616014 Julius K9 IDC Powerharness Baby 1 Rojo 18,75 13,12
CJ-0052 5999053616083 Julius K9 IDC Powerharness Baby 1 Rosa 18,75 13,12
CJ-0088 5999053664466 Julius K9 IDC Powerharness Baby 1 Rosa Flores 18,75 13,12
CJ-0079 5999053659783 Julius K9 IDC Powerharness Baby 1 UV Naranja 18,75 13,12
CJ-0142 5999053670382 Julius K9 IDC Powerharness Baby 1 Vaquero 18,75 13,12
CJ-0151 5999053671518 Julius K9 IDC Powerharness Baby 1 vaquero neon 18,75 13,12
CJ-0115 5999053665364 Julius K9 IDC Powerharness Baby 1 Verde 18,75 13,12
CJ-0169 5999053670207 Julius K9 IDC Powerharness Baby 1 Verde Claro 18,75 13,12
CJ-0044 5999053645502 Julius K9 IDC Powerharness Baby 2 Agua marina 21,52 15,06
CJ-0179 5999053670481 Julius K9 IDC Powerharness Baby 2 Arco Iris 21,50 15,05
CJ-0026 5999053616137 Julius K9 IDC Powerharness Baby 2 Azul 21,52 15,06
CJ-0035 5999053642808 Julius K9 IDC Powerharness Baby 2 Camuflaje 21,52 15,06
CJ-0249 5999053672928 Julius K9 IDC Powerharness Baby 2 España 21,52 15,06
CJ-0125 5999053665418 Julius K9 IDC Powerharness Baby 2 Fucsia 21,52 15,06
CJ-0107 5999053665432 Julius K9 IDC Powerharness Baby 2 Granate 21,50 15,05
CJ-0098 5999053665425 Julius K9 IDC Powerharness Baby 2 Gris Antracita 21,50 15,05
CJ-0008 5999053616113 Julius K9 IDC Powerharness Baby 2 Negro 21,52 15,06
CJ-0071 5999053616212 Julius K9 IDC Powerharness Baby 2 Neon 21,52 15,06
CJ-0062 5999053640941 Julius K9 IDC Powerharness Baby 2 Purpura 21,52 15,06
CJ-0341 5999053685386 Julius K9 IDC Powerharness Baby 2 Purpura Oscuro 21,52 15,06
CJ-0204 5999053667689 Julius K9 IDC Powerharness Baby 2 Reggae Canis 24,98 17,48
CJ-0017 5999053616120 Julius K9 IDC Powerharness Baby 2 Rojo 21,52 15,06
CJ-0053 5999053616199 Julius K9 IDC Powerharness Baby 2 Rosa 21,52 15,06
CJ-0089 5999053664473 Julius K9 IDC Powerharness Baby 2 Rosa Flores 21,50 15,05
CJ-0080 5999053659790 Julius K9 IDC Powerharness Baby 2 UV Naranja 21,52 15,06
CJ-0143 5999053670399 Julius K9 IDC Powerharness Baby 2 Vaquero 21,52 15,06
CJ-0152 5999053671525 Julius K9 IDC Powerharness Baby 2 vaquero neon 21,52 15,06
CJ-0116 5999053665401 Julius K9 IDC Powerharness Baby 2 Verde 21,50 15,05
CJ-0170 5999053670214 Julius K9 IDC Powerharness Baby 2 Verde Claro 21,52 15,06
CJ-0046 5999053645526 Julius K9 IDC Powerharness Mini Agua marina 34,70 24,29
CJ-0181 5999053670504 Julius K9 IDC Powerharness Mini Arco Iris 34,69 24,28
CJ-0028 5999053616359 Julius K9 IDC Powerharness Mini Azul 34,70 24,29
CJ-0037 5999053642822 Julius K9 IDC Powerharness Mini Camuflaje 34,70 24,29
CJ-0163 5999053669782 Julius K9 IDC Powerharness Mini Chocolate 34,70 24,29
CJ-0251 5999053672942 Julius K9 IDC Powerharness Mini España 34,70 24,29
CJ-0127 5999053665494 Julius K9 IDC Powerharness Mini Fucsia 34,70 24,29
CJ-0109 5999053665517 Julius K9 IDC Powerharness Mini Granate 34,69 24,28
CJ-0100 5999053665500 Julius K9 IDC Powerharness Mini Gris Antracita 34,69 24,28
CJ-0045 5999053645519 Julius K9 IDC Powerharness Mini Mini Agua marina 32,62 22,83
CJ-0259 5999053655969 Julius K9 IDC Powerharness Mini Mini Americano 36,08 25,25
CJ-0180 5999053670498 Julius K9 IDC Powerharness Mini Mini Arco Iris 32,62 22,83
CJ-0027 5999053616243 Julius K9 IDC Powerharness Mini Mini Azul 32,62 22,83
CJ-0036 5999053642815 Julius K9 IDC Powerharness Mini Mini Camuflaje 32,62 22,83
CJ-0162 5999053669775 Julius K9 IDC Powerharness Mini Mini Chocolate 32,62 22,83
CJ-0250 5999053672935 Julius K9 IDC Powerharness Mini Mini España 32,62 22,83
CJ-0126 5999053665456 Julius K9 IDC Powerharness Mini Mini Fucsia 32,62 22,83
CJ-0108 5999053665470 Julius K9 IDC Powerharness Mini Mini Granate 32,62 22,83
CJ-0099 5999053665463 Julius K9 IDC Powerharness Mini Mini Gris Antracit 32,62 22,83
CJ-0009 5999053616229 Julius K9 IDC Powerharness Mini Mini Negro 32,62 22,83
CJ-0072 5999053616328 Julius K9 IDC Powerharness Mini Mini Neon 32,62 22,83
CJ-0063 5999053640958 Julius K9 IDC Powerharness Mini Mini Purpura 32,62 22,83
CJ-0342 5999053685409 Julius K9 IDC Powerharness Mini Mini Purpura Oscur 32,62 22,83
CJ-0018 5999053616236 Julius K9 IDC Powerharness Mini Mini Rojo 32,62 22,83
CJ-0054 5999053616304 Julius K9 IDC Powerharness Mini Mini Rosa 32,62 22,83
CJ-0090 5999053664480 Julius K9 IDC Powerharness Mini Mini Rosa Flores 32,62 22,83
CJ-0081 5999053659806 Julius K9 IDC Powerharness Mini Mini UV Naranja 32,62 22,83
CJ-0153 5999053671532 Julius K9 IDC Powerharness Mini Mini vaque neon 32,62 22,83
CJ-0144 5999053670405 Julius K9 IDC Powerharness Mini Mini Vaquero 32,62 22,83
CJ-0171 5999053670221 Julius K9 IDC Powerharness Mini Mini Verde Claro 32,62 22,83
CJ-0010 5999053616335 Julius K9 IDC Powerharness Mini Negro 34,70 24,29
CJ-0073 5999053616434 Julius K9 IDC Powerharness Mini Neon 34,70 24,29
CJ-0064 5999053640965 Julius K9 IDC Powerharness Mini Purpura 34,70 24,29
CJ-0343 5999053685416 Julius K9 IDC Powerharness Mini Purpura Oscuro 34,70 24,29
CJ-0019 5999053616342 Julius K9 IDC Powerharness Mini Rojo 34,70 24,29
CJ-0055 5999053616410 Julius K9 IDC Powerharness Mini Rosa 34,70 24,29
CJ-0091 5999053664497 Julius K9 IDC Powerharness Mini Rosa Flores 34,69 24,28
CJ-0082 5999053659813 Julius K9 IDC Powerharness Mini UV Naranja 34,70 24,29
CJ-0145 5999053670412 Julius K9 IDC Powerharness Mini Vaquero 34,70 24,29
CJ-0154 5999053671549 Julius K9 IDC Powerharness Mini vaquero y neon 34,70 24,29
CJ-0118 5999053665487 Julius K9 IDC Powerharness Mini Verde 34,69 24,28
CJ-0172 5999053670238 Julius K9 IDC Powerharness Mini Verde Claro 34,70 24,29
CJ-0310 2054369871472 Julius K9 Kanesjob Linterna para Arnes 0 1 2 3 4 3,66 2,56
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
            # Enlazarlo con Julius
            client.table("productos_proveedores").insert({
                "producto_id": prod_id,
                "proveedor_id": prov_id,
                "precio_coste": coste
            }).execute()
            
            skus_existentes.add(nuevo_sku)
            nombres_existentes.add(nombre.lower())
            insertados += 1
            print(f"  ✅ Añadido: [{nuevo_sku}] {nombre} (PVP: {pvp}€ | Coste: {coste}€)")

print(f"\n🎉 ¡Magia completada! {insertados} productos nuevos de Julius K9 insertados. {omitidos} omitidos por estar duplicados.")