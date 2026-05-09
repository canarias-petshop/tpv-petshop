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
print("🔌 Conectando a Supabase para leer el PDF de Kong...")

# 1. Asegurar que el proveedor existe
NOMBRE_PROV = "Kong"
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

# 3. Generador inteligente de SKU correlativo (KG-001, KG-002...) para Kong
contador_sku = 1
def generar_sku():
    global contador_sku
    while True:
        nuevo_sku = f"KG-{contador_sku:03d}"
        if nuevo_sku not in skus_existentes:
            return nuevo_sku
        contador_sku += 1

# 4. El texto bruto copiado directamente de tu PDF
datos_pdf = """
Cod. Producto Cod. Ean Descripción Tarifa P.V.P.R. Tarifa
P.V.T
K382947 611932100111 10011E KONG Goodie Bone Hueso Rojo M 10,69 7,48
K382948 611932100128 10012E KONG Goodie Bone X-Treme Hueso Negro M 11,31 7,92
K383353 035585780702 10014E KONG Goodie Bone Hueso Rojo L 15,24 10,67
K383731 035585356006 10015E KONG Goodie Bone X-Treme Hueso Negro L 17,94 12,56
K383367 035585775524 ABS1E KONG Sport Balls L 2Ud 6,59 4,61
K383366 035585775630 ABS2E KONG Sport Balls M 3Ud 6,11 4,28
K383365 035585775647 ABS3E KONG Sport Balls S 3Ud 4,70 3,29
K383364 035585775661 ABS5E KONG Sport Balls XS 3Ud 4,54 3,18
K383108 035585747125 AKFS1E KONG AirDog Fetch Stick Juguete L 10,07 7,05
K383107 035585737225 AKFS2E KONG AirDog Fetch Stick Juguete M 7,74 5,42
K383024 35585775302 ASB1E KONG AirDog Squeaker Hueso Con Sonido L 10,07 7,05
K383023 35585775296 ASB2E KONG AirDog Squeaker Hueso Con Sonido M 7,74 5,42
K383022 35585775289 ASB3E KONG AirDog Squeaker Hueso Con Sonido S 5,96 4,17
K383016 035585775340 ASD1E KONG AirDog Squeaker Donut Con Sonido L 10,07 7,05
K383015 035585775333 ASD2E KONG AirDog Squeaker Donut Con Sonido M 7,74 5,42
K383029 035585775272 ASDB1E KONG AirDog Squeaker Dumbbell L 10,07 7,05
K383028 35585775265 ASDB2E KONG AirDog Squeaker Dumbbell M 7,74 5,42
K383027 35585775258 ASDB3E KONG AirDog Squeaker Dumbbell S 5,94 4,16
K383019 35585775241 ASFB1E KONG AirDog Squeaker Pelota de Futbol L 10,07 7,05
K383018 35585775234 ASFB2E KONG AirDog Squeaker Pelota de Futbol M 7,74 5,42
K383017 35585775227 ASFB3E KONG AirDog Squeaker Pelota de Futbol S 5,94 4,16
K383007 35585775173 AST1BE KONG SqueakAir Grande 3,01 2,11
K383098 0035585775555 AST1E KONG SqueakAir L 2Ud 6,27 4,39
K383074 0035585774978 AST21E KONG SqueakAir Ball Con Cuerda M 4,31 3,02
K387055 035585416007 AST22E KONG SqueakAir M 6Ud 9,43 6,60
K383006 35585775210 AST2BE KONG SqueakAir Medio 1,54 1,08
K383005 0035585775203 AST2E KONG SqueakAir M 3Ud 5,17 3,62
POC-0013 035585775197 AST2YE KONG SqueakAir Birthday Ball M 5,43 3,80
K383097 035585775159 AST3E KONG SqueakAir S 3Ud 4,31 3,02
K383008 0035585775180 AST5E KONG SqueakAir XS 3Ud 3,10 2,17
K383363 035585775579 ASTXBE KONG SqueakAir XL 4,70 3,29
POC-0012 0035585302034 AUT2E KONG SqueakAir Ultra Ball M 7,67 5,37
POC-0080 035585111377 BB3E KONG Biscuit Ball S 11,67 8,17
K383687 0035585013268 C4E KONG Cat Kitty 6,33 4,43
K383686 035585334066 CA56E KONG Cat Tennis Balls With Bells 4,24 2,97
POC-0033 035585459042 CA75E KONG Cat Peluche Fantasia Modelos Surtidos 5,00 3,50
POC-0184 035585459134 CA81E KONG Cat Enchanted Buzzy Unicorn 6,09 4,26
POC-0191 035585459448 CA92E KONG Cat Enchanted 5,43 3,80
POC-0075 035585450612 CAT41E KONG Cat Active Feather Teaser 4,73 3,31
POC-0076 035585334219 CAT45E KONG Cat Active Window Teaser Surtido 6,09 4,26
K383358 035585450490 CB4E KONG Cat Peluche Wild Tails (Modelos Surtidos 4,00 2,80
K383409 0035585211220 CCSE KONG Cat Premium Hierba Gatera Spray 30Ml 6,34 4,44
K382930 035585111155 CK1E KONG Aqua L 13,77 9,64
K382931 035585111254 CK2E KONG Aqua M 11,13 7,79
POC-0079 035585418001 CR7E KONG Cat Kickeroo Cuddler Colores Surtidos 5,81 4,07
POC-0185 035585459202 CSF53E KONG Cat Softies Buzzy Llama 5,94 4,16
POC-0159 035585404028 CT51E KONG Connects Kitty Comber Cat 10,51 7,36
K383077 35585431116 FK3E KONG Small Animall Rojo 6,83 4,78
K382905 0035585111124 K1E KONG Extreme Negro L 12,23 8,56
K382908 035585111148 K2E KONG Extreme Negro M 10,46 7,32
K382909 035585111605 K3E KONG Extreme Negro S 7,74 5,42
K383352 035585181127 KB1E KONG Ball Rojo M/L 13,10 9,17
K383351 035585181226 KB2E KONG Ball Rojo S 8,53 5,97
POC-0047 035585780108 KB31E KONG Goodie Bone Hueso Rojo S 7,20 5,04
POC-0048 035585131405 KB51E KONG Goodie Bone Hueso Rojo XS 6,71 4,70
POC-0085 035585121123 KD1E KONG Dental Stick L 11,67 8,17
POC-0084 035585121222 KD2E KONG Dental Stick M 8,99 6,29
POC-0083 035585121321 KD3E KONG Dental Stick S 6,34 4,44
K383354 035585129174 KF15E KONG Flyer Frisbee Para Perros Rojo S 10,76 7,53
K382990 035585129082 KF3E KONG Flyer Frisbee Para Perros Rojo L 12,56 8,79
K382991 035585129150 KG1E KONG Tug-Toy 14,84 10,39
POC-0118 035585127323 KJ1E KONG Jump' N Jack L 16,19 11,33
POC-0117 035585127330 KJ2 KONG Jump' N Jack M 13,46 9,42
K382904 35585111414 KKE KONG Classic Rojo XXL 22,99 16,09
POC-0014 0035585356099 KM1E KONG Ring M/L 11,70 8,19
POC-0015 0035585356105 KM2E KONG Ring S/M 8,53 5,97
POC-0007 0035585111438 KN1E KONG Senior Violeta L 10,46 7,32
En vigor 01/02/2025
Tarifas Kong 2025 Tienda
Última modificación Abr -25
Cod. Producto Cod. Ean Descripción Tarifa P.V.P.R. Tarifa
P.V.T
POC-0006 0035585111490 KN2E KONG Senior Violeta M 8,67 6,07
POC-0005 0035585111551 KN3E KONG Senior Violeta S 6,40 4,48
POC-0121 35585131085 KP13E KONG Puppy Teething Stick L 11,31 7,92
K382992 035585131160 KP15E KONG Puppy Flyer Frisbee Para Cachorros 10,76 7,53
K382911 035585131115 KP1E KONG Puppy Classic L 10,23 7,16
POC-0123 035585131245 KP22E KONG Puppy Activity Ball M 11,70 8,19
POC-0120 035585131184 KP23E KONG Puppy Teething Stick M 8,53 5,97
K382994 035585131191 KP27E KONG Puppy Binkie Chupa M 10,76 7,53
K382910 0035585131214 KP2E KONG Puppy Classic M 8,67 6,07
K382944 035585131283 KP31E KONG Puppy Goodie Bone Hueso Cachorro 7,20 5,04
POC-0122 035585131252 KP32E KONG Puppy Activity Ball S 8,44 5,91
POC-0119 035585131375 KP33E KONG Puppy Teething Stick S 6,33 4,43
K382993 035585131207 KP37E KONG Puppy Binkie Chupa S 8,14 5,70
K382915 35585131313 KP3E KONG Puppy Classic S 6,43 4,50
POC-0151 035585131474 KP51E KONG Hueso Con Cuerda Puppy 6,47 4,53
K383870 035585356020 KPB1E KONG Puppy Ball M/L 13,10 9,17
K383869 035585356037 KPB2E KONG Puppy Ball S 8,53 5,97
K383872 035585356044 KPT11E KONG Puppy Tires Neumatico M/L 14,41 10,09
K383871 035585356051 KPT21E KONG Puppy Tires Neumatico S 11,70 8,19
POC-0116 035585141114 KS1E KONG Stuff A-Ball L 15,27 10,69
POC-0115 035585141213 KS2E KONG Stuff A-Ball M 13,47 9,43
POC-0114 035585141312 KS3 KONG Stuff A-Ball S 9,91 6,94
K383286 035585250007 KT11E KONG TRAXX Neumatico Negro M/L 14,41 10,09
K383284 035585250014 KT21E KONG TRAXX Neumatico Negro S 11,70 8,19
K382903 035585111018 KXLE KONG Classic Rojo XL 17,59 12,31
POC-0016 0035585429014 LBT1E KONG Ballistic Hide N Treat Modelo Surtido L 11,70 8,19
POC-0017 0035585429007 LBT2E KONG Ballistic Hide N Treat Modelo Surtido M 8,99 6,29
POC-0186 035585008462 LPSX1E KONG Squeakstix 12,76 8,93
POC-0195 35585499581 LWT22E KONG Low Stuff Stripes Cow 16,82 8,41
POC-0196 35585499604 LWT24E KONG Low Stuff Stripes Donkey 16,82 8,41
POC-0187 035585008479 MPSX2E KONG Squeakstix 10,20 7,14
POC-0188 035585503592 MZYK21E KONG Cozie Pocketz Fox 12,16 8,51
POC-0189 035585503622 MZYK24E KONG Cozie Pocketz Beaver 12,16 8,51
POC-0148 035585011462 NH42E KONG Cat Refillable Erizo 4,70 3,29
POC-0065 035585454030 NK14E KONG Peluche Tugger Knots Alce L/M 11,70 8,19
POC-0064 035585454061 NK33E KONG Peluche Tugger Knots Mono S 9,06 6,34
K387007 035585402048 NKF11E KONG Peluche Floppy Knots Elefante M/L 13,10 9,17
K387008 035585402079 NKF14E KONG Peluche Floppy Knots Hipopotamo M/L 13,10 9,17
K387005 035585402017 NKF32E KONG Peluche Floppy Knots Zorro S/M 10,36 7,25
K387006 035585402024 NKF33E KONG Peluche Floppy Knots Conejo S/M 10,36 7,25
POC-0018 035585400013 NKK21E KONG Dragon Knots Modelos Surtidos M/L 12,09 8,46
POC-0061 035585454269 NKR1E KONG Peluche Wild Knots Osos M/L Surtido 11,21 7,85
K383299 035585454252 NKR3E KONG Peluche Wild Knots Osos S/M Surtido 8,43 5,90
POC-0068 035585454429 NKS11E KONG Peluche Scrunch Knots Zorro L 11,21 7,85
POC-0069 035585454399 NKS12E KONG Peluche Scrunch Knots Mapache L 11,21 7,85
POC-0070 035585454436 NKS13E KONG Peluche Scrunch Knots Ardilla L 11,21 7,85
POC-0066 035585454443 NKS32E KONG Peluche Scrunch Knots Mapache S 8,14 5,70
POC-0067 035585454450 NKS33E KONG Peluche Scrunch Knots Ardilla S 8,14 5,70
POC-0174 035585475899 NKV32E KONG Knots Carnival Elephant Sm/Md 7,87 5,51
POC-0172 035585475905 NKV33E KONG Knots Carnival Lion Sm/Md 7,87 5,51
K383396 035585454481 NKX32E KONG Peluche Cross Knots Monkey S/M 9,61 6,73
POC-0147 035585031170 NR45E KONG Cat Refillable Rata 4,70 3,29
POC-0146 035585124032 NT43E KONG Cat Refillable Tortuga 4,70 3,29
K383289 035585034041 PB1E KONG Bounzer 370Gr Rojo L 14,41 10,09
K383288 035585034034 PB2E KONG Bounzer 200Gr Rojo M 7,81 5,47
K383281 035585249001 PF1E KONG Safestix 70Cm L 20,50 14,35
K383279 035585249018 PF2E KONG Safestix 50Cm M 16,71 11,70
K383278 035585249025 PF3E KONG Safestix 30Cm S 11,63 8,14
POC-0019 035585447018 PFC11E KONG Corestrength Bone M/L 10,30 7,21
POC-0021 035585447056 PFC13E KONG Corestrength Ball L 8,99 6,29
POC-0022 035585447001 PFC31E KONG Corestrength Bone S/M 7,20 5,04
POC-0025 0035585034171 PGY1E KONG Gyro L 14,41 10,09
POC-0024 0035585034188 PGY3E KONG Gyro S 11,70 8,19
POC-0026 0035585464022 PSA13E KONG Squeezz Action Red L 8,53 5,97
POC-0027 0035585464053 PSA23E KONG Squeezz Action Red M 8,53 5,97
POC-0028 0035585464084 PSA33E KONG Squeezz Action Red S 6,71 4,70
K382954 035585034003 PW1E KONG Wobbler Dispensador De Comida L 20,14 14,10
K383203 035585034010 PW2E KONG Wobbler Dispensador De Comida S 15,27 10,69
K383873 035585246000 RBF1E KONG Peluche Belly Flops Langosta 9,43 6,60
POC-0207 35585523316 RCP21E KONG Comfort Pups Goldie M 11,63 8,14
POC-0208 35585523347 RCP24E KONG Comfort Pups Spot M 11,63 8,14
POC-0181 035585485232 RJXE KONG Comfort Jumbo Assorted XL 12,33 8,63
K383677 0035585319124 RL13E KONG Peluche Cuteseas Pulpo L 11,21 7,85
K383679 035585319148 RL15E KONG Peluche Cuteseas Ballena L 11,21 7,85
K383674 0035585319056 RL33E KONG Peluche Cuteseas Pulpo S 6,57 4,60
POC-0093 035585360249 RLC11E KONG Peluche Comfort Kiddos Oso L 10,76 7,53
POC-0180 035585360300 RLC14E KONG Comfort Kiddos Lion Lg 10,76 7,53
Cod. Producto Cod. Ean Descripción Tarifa P.V.P.R. Tarifa
P.V.T
POC-0092 035585360294 RLC33E KONG Peluche Comfort Kiddos Elefante S 8,53 5,97
POC-0091 035585360331 RLC35E KONG Peluche Comfort Kiddos Cerdo S 8,53 5,97
POC-0176 035585360485 RLC53E KONG Comfort Kiddos Elephant XS 6,71 4,70
POC-0205 35585498973 RLR11E KONG Cuteseas Rufflez Shark M/L 11,63 8,14
POC-0206 35585499499 RLR32E KONG Cuteseas Rufflez Hermit Crab S/M 10,86 7,60
POC-0029 0035585360348 RPA21E KONG Phatz Hippo M 10,76 7,53
POC-0031 0035585360430 RPA33E KONG Phatz Pig S 6,71 4,70
POC-0089 035585360225 RPZE12E KONG Peluche KONG Puzzlement Escape Flower 10,20 7,14
K383892 035585377063 RSH11E KONG Peluche Shells Tortuga L 12,56 8,79
K383891 035585377018 RSH32E KONG Peluche Shells Oso S 8,14 5,70
POC-0096 035585475325 RSL11E KONG Peluche Stretchezz Legz Oso L 12,56 8,79
POC-0095 035585475370 RSL32E KONG Peluche Stretchezz Legz Elefante S 8,99 6,29
POC-0037 035585475233 RSS14E KONG Peluche Sea Shells Tortuga M/L 12,56 8,79
POC-0035 035585475172 RSS32E KONG Peluche Sea Shells Caballito DeMar S/M 8,14 5,70
POC-0170 035585485454 RTGX1E KONG Tuggz Sloth XL 13,56 9,49
POC-0171 035585485461 RTGX2E KONG Tuggz Monkey XL 13,56 9,49
K383928 035585378015 RTS12E KONG Peluche TenniShoes Jirafa L 12,56 8,79
K383925 035585378046 RTS32E KONG Peluche TenniShoes Jirafa S 9,43 6,60
POC-0204 35585499635 RWM2E KONG Woozles Monster Assorted M 14,09 9,86
POC-0183 035585421049 RYN11E KONG Yarnimals Monkey M/L 10,36 7,25
POC-0182 035585421124 RYN33E KONG Yarnimals Dog Xs/S 6,74 4,72
POC-0197 35585499871 SCF11E KONG Scruffs Chicken M/L 12,40 8,68
POC-0198 35585499888 SCF12E KONG Scruffs Turtle M/L 12,40 8,68
POC-0201 35585498911 SHCX1E KONG Shakers Crumples Elephant XL 16,27 11,39
POC-0199 35585498935 SHCX3E KONG Shakers Crumples Sloth XL 16,27 11,39
POC-0200 35585498942 SHCX4E KONG Shakers Crumples Bunny XL 16,27 11,39
POC-0058 035585476162 SKB1E KONG Signature Ball Pack 2Ud L 13,17 9,22
POC-0055 035585476124 SKB2BE KONG Signature Ball EU Bulk M 4,64 3,25
POC-0057 035585476155 SKB2E KONG Signature Ball Pack 2Ud M 9,61 6,73
POC-0056 035585476148 SKB3E KONG Signature Ball Pack 2Ud S 6,57 4,60
K383048 035585000565 SQ2E KONG Peluche Squiggles M (Modelos Surtidos) 7,06 4,94
K383047 035585000572 SQ3E KONG Peluche Squiggles S (Modelos Surtidos) 5,17 3,62
K382902 35585111117 T1E KONG Classic Rojo L 11,37 7,96
K382901 035585111216 T2E KONG Classic Rojo M 9,51 6,66
K382900 0035585111315 T3E KONG Classic Rojo S 6,83 4,78
K383069 035585125008 T4E KONG Classic Rojo XS 6,33 4,43
K387016 035585401034 TDD11E KONG Dotz Circulo L 12,09 8,46
K387018 035585401058 TDD13E KONG Dotz Triangulo L 12,09 8,46
K387013 035585401003 TDD31E KONG Dotz Circulo S 6,71 4,70
POC-0054 035585034089 TMB1E KONG Jumbler Ball XL 19,59 13,71
POC-0053 035585034096 TMB2E KONG Jumbler Ball M 13,47 9,43
POC-0106 035585034119 TMF1E KONG Jumbler Football XL Surtido 19,59 13,71
POC-0099 035585034126 TMF2E KONG Jumbler Football M Surtido 13,47 9,43
K383208 035585181134 UB1E KONG Ball Extreme Negro M/L 13,47 9,43
K383204 035585181141 UB2E KONG Ball Extreme Negro S 8,99 6,29
K382959 035585123189 UF3E KONG Extreme Flyer Frisbee Para Perros L 14,41 10,09
K382907 035585111421 UKKE KONG Extreme Negro XXL 23,84 16,69
K382906 035585111025 UXLE KONG Extreme Negro XL 18,44 12,91
POC-0156 742061000161 VT1 KONG Azul L 12,14 8,50
POC-0155 742061000178 VT2 KONG Azul M 10,29 7,20
POC-0154 742061000185 VT3 KONG Azul S 7,51 5,26
POC-0158 742061000208 VTK KONG Azul XXL 24,14 16,90
POC-0113 035585800011 WB1E KONG Wubba L 10,51 7,36
POC-0087 035585800028 WB3E KONG Wubba S 7,44 5,21
POC-0108 035585800868 WE1E KONG Peluche Wubba Floppy Ears L 11,21 7,85
POC-0107 035585800875 WE3E KONG Peluche Wubba Floppy Ears S 8,06 5,64
POC-0203 35585502823 WPS1E Wubba Octopus Assorted L 13,96 9,77
POC-0202 35585502816 WPS3E Wubba Octopus Assorted S 8,53 5,97
POC-0009 0035585213002 XO1E KONG Stuff''N Galleta-Snacks Queso Grande 8,44 5,91
POC-0008 0035585213019 XO3E KONG Stuff''N Galleta-Snacks Queso Pequeño 6,57 4,60
K383418 035585011127 XP1E KONG Stuff''N Galleta-Snacks Higado Grande 8,43 5,90
K383417 035585011141 XP3E KONG Stuff''N Galleta-Snacks Higado Pequeño 6,57 4,60
K382912 35585011110 XS1E KONG Easy Treat Liver 236Ml 8,89 6,22
K382916 0035585010502 XS4E KONG Easy Treat Puppy 236Ml 8,89 6,22
POC-0010 0035585364001 XS9E KONG Easy Treat Queso 236Ml 8,89 6,22
K383428 035585009254 XY1E KONG Stuff''N Galleta-Snacks Cachorro Grande 8,43 5,90
K383419 0035585009261 XY3E KONG Stuff''N Galleta-Snacks Cachorro Pequeño 6,57 4,60
K383195 035585159133 ZYB2E KONG Peluche Cozie Brigths Modelos Surtidos 9,29 6,50
POC-0045 035585159140 ZYP2E KONG Peluche Cozie Pastels Modelos Surtidos 9,29 6,50
POC-0190 035585509075 ZYT12E KONG Cozie Tuggz Elephant M-L 12,21 8,55
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
            # Enlazarlo con Kong
            client.table("productos_proveedores").insert({
                "producto_id": prod_id,
                "proveedor_id": prov_id,
                "precio_coste": coste
            }).execute()
            
            skus_existentes.add(nuevo_sku)
            nombres_existentes.add(nombre.lower())
            insertados += 1
            print(f"  ✅ Añadido: [{nuevo_sku}] {nombre} (PVP: {pvp}€ | Coste: {coste}€ | EAN: {ean if ean else 'Faltante'})")

print(f"\n🎉 ¡Magia completada! {insertados} productos nuevos de Kong insertados. {omitidos} omitidos.")