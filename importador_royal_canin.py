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
print("🔌 Conectando a Supabase para leer el PDF de Royal Canin...")

# 1. Asegurar que el proveedor existe
NOMBRE_PROV = "Royal Canin"
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

# 3. Generador inteligente de SKU correlativo (RC-001, RC-002...) para Royal Canin
contador_sku = 1
def generar_sku():
    global contador_sku
    while True:
        nuevo_sku = f"RC-{contador_sku:03d}"
        if nuevo_sku not in skus_existentes:
            return nuevo_sku
        contador_sku += 1

# 4. El texto bruto copiado directamente de tu PDF
datos_pdf = """
Cod.
Producto Cod. Ean Descripción
Tarifa
P.V.P.R.
Tarifa P.V.T.
BHN
RC148864 3182550821773 Bhn Beagle Adult 12Kg 76,82 61,44
RC148836 3182550821766 Bhn Beagle Adult 3Kg 28,18 19,50
RC148026 3182550782203 Bhn Bichon Maltes Adulto 1,5Kg 17,70 13,15
RC148014 3182550782180 Bhn Bichon Maltes Adulto 500Gr 6,52 4,55
RC156964 3182550719766 Bhn Boxer Adulto 12Kg 77,25 61,44
RC157064 3182550743945 Bhn Boxer Puppy 12Kg 85,79 66,20
RC157264 3182550719803 Bhn Bulldog Adulto 12Kg 76,82 61,44
RC625124 9003579051399 Bhn Bulldog Frances Adulto 85Gr X 12Ud 14,87 10,40
RC159868 3182550846042 Bhn Bulldog Frances Adulto 9Kg 61,73 48,37
RC159830 3182550811637 Bhn Bulldog Frances Adulto 3Kg 28,18 19,50
RC159960 3182550777674 Bhn Bulldog Frances Puppy 10Kg 77,66 57,95
RC159930 3182550811705 Bhn Bulldog Frances Puppy 3Kg 29,23 20,65
RC157364 3182550743891 Bhn Bulldog Puppy 12Kg 85,79 66,20
RC156526 3182550743174 Bhn Caniche Adulto 1,5Kg 17,71 12,19
RC156550 3182550716932 Bhn Caniche Adulto 7,5Kg 67,59 48,79
RC156560 3182550765206 Bhn Caniche Puppy 3Kg 29,20 21,75
RC394450 Bhn Caniche Wet 12 X 85Gr 13,81 10,20
RC147126 3182550752404 Bhn Carlino Adulto 1,5Kg 17,71 12,19
RC147136 3182550799775 Bhn Carlino Adulto 3Kg 28,23 20,48
RC147326 3182550813082 Bhn Carlino Junior 1,5Kg 18,10 12,95
RC147530 3182550777698 Bhn Cavalier King Charles Adult 3Kg 27,14 20,48
RC158126 3182550728102 Bhn Chihuahua Adulto 1,5Kg 17,70 13,15
RC158145 3182550747820 Bhn Chihuahua Adulto 3Kg 27,00 21,03
RC158114 3182550718813 Bhn Chihuahua Adulto 500Gr 6,52 4,55
RC158226 3182550722544 Bhn Chihuahua Puppy 1,5Kg 18,08 13,95
RC158214 3182550722537 Bhn Chihuahua Puppy 500Gr 7,32 4,85
RC394422 9003579001516 Bhn Chihuahua Wet Pouch 12 X 85Gr. 14,14 10,44
RC158763 3182550811538 Bhn Cocker Adulto 12Kg 87,56 61,44
RC158732 3182550743709 Bhn Cocker Adulto 3Kg 28,18 19,50
RC158825 3182550813211 Bhn Cocker Junior 3Kg 29,23 20,65
RC159664 3182550765183 Bhn Dalmata Adulto 12Kg 77,25 61,44
RC159064 3182550743440 Bhn Golden Retriever Adulto 12Kg 76,82 61,44
RC159264 3182550751261 Bhn Golden Retriever Puppy 12Kg 85,79 66,20
RC158464 3182550736046 Bhn Gran Danes Adulto 12Kg 78,27 58,38
RC148636 3182550821421 Bhn Jack Russel Adult 3Kg 28,23 20,48
RC148650 3182550821438 Bhn Jack Russel Adult 7,5Kg 67,59 48,79
RC148436 3182550822138 Bhn Jack Russel Junior 3Kg 29,20 21,75
RC146666 3182550908412 Bhn Labrador Adulto +5 12Kg 82,36 65,73
RC146664 3182550715645 Bhn Labrador Adulto 12Kg 76,82 61,44
RC146632 3182550715614 Bhn Labrador Adulto 3Kg 28,18 19,50
RC145864 3182550787581 Bhn Labrador Adulto Sterilised 12Kg 76,82 61,44
RC146764 3182550725514 Bhn Labrador Puppy 12Kg 85,79 66,20
RC146732 3182550725507 Bhn Labrador Puppy 3Kg 29,23 20,65
RC395035 9003579013656 Bhn Labrador Wet 10 X 140Gr 18,78 14,21
RC146465 3182550908399 Bhn Pastor Aleman Adulto +5 12 Kg 82,36 65,73
RC146463 3182550892759 Bhn Pastor Aleman Adulto 11Kg 70,41 56,34
RC146564 3182550724159 Bhn Pastor Aleman Puppy 12Kg 85,79 66,20
RC146532 3182550724142 Bhn Pastor Aleman Puppy 3Kg 29,23 20,65
Tarifas Royal Canin 2026 Tienda
En vigor 01/03/2026
Última modificación Mar-26
Cod.
Producto Cod. Ean Descripción
Tarifa
P.V.P.R.
Tarifa P.V.T.
RC148980 3182550908450 Bhn Pomeranian Adult 3Kg 28,04 21,03
RC146864 3182550736060 Bhn Rottweiler Adulto 12Kg 78,27 58,38
RC146964 3182550755351 Bhn Rottweiler Junior 12K 85,73 62,90
RC157832 3182550730587 Bhn Schnauzer Adulto 3Kg 27,14 20,48
RC157850 3182550813020 Bhn Schnauzer Adulto 7,5Kg 67,59 48,79
RC158536 3182550813105 Bhn Schnauzer Junior 1,5Kg 18,10 12,95
RC157532 3182550848442 Bhn Shih Tzu Adult 3 Kg 28,04 21,03
RC157526 3182550743228 Bhn Shih Tzu Adulto 1,5Kg 17,70 13,15
RC157626 3182550722605 Bhn Shih Tzu Junior 1,5Kg 18,08 13,95
RC395030 Bhn Shih Tzu Wet 12 X 85Gr 14,14 10,44
RC156726 3182550717335 Bhn Teckel Adulto 1,5Kg 16,66 12,19
RC156760 3182550812016 Bhn Teckel Adulto 7,5 Kg 67,59 48,79
RC395022 Bhn Teckel Wet 12 X 85Gr 13,81 10,20
RC147026 3182550751308 Bhn Westie Adulto 1,5Kg 17,71 12,19
RC147030 3182550811774 Bhn Westie Adulto 3Kg 28,23 20,48
RC156126 3182550716857 Bhn Yorkshire Adulto 1,5Kg 17,70 13,15
RC156132 3182550799768 Bhn Yorkshire Adulto 3Kg 27,00 21,03
RC156114 3182550710046 Bhn Yorkshire Adulto 500Gr 6,52 4,55
RC156150 3182550716925 Bhn Yorkshire Adulto 7,5Kg 67,51 52,57
RC156128 3182550908504 Bhn Yorkshire Ageing +8 1,5Kg 19,81 14,08
RC156026 3182550743471 Bhn Yorkshire Puppy 1,5Kg 18,08 13,95
RC156014 3182550743464 Bhn Yorkshire Puppy 500Gr 7,32 4,85
RC156045 3182550811422 Bhn Yorkshire Terrier Puppy 7,5Kg 70,57 55,85
RC394022 9003579001448 Bhn Yorkshire Wet 12 X 85Gr 14,14 10,44
CYNO
RC186028 3182550768658 Cyno Babydog Milk 2Kg 72,70 53,35
RC186012 3182550768641 Cyno Babydog Milk 400Gr 28,80 21,15
FBN
RC309560 3182550756464 Fbn British Shorthair Adult 10Kg 109,16 87,28
RC309528 3182550756419 Fbn British Shorthair Adult 2Kg 31,36 24,58
RC398621 9003579001257 Fbn British Shorthair Gravy Pouch 85Gr X 12Ud 19,76 14,74
RC309780 3182550816533 Fbn Kitten British Shorthair 2Kg 35,23 27,30
RC302060 3182550863681 Fbn Kitten Maine Coon 10Kg 120,95 96,75
RC302036 3182550770958 Fbn Kitten Maine Coon 4Kg 60,51 46,45
RC306230 3182550721219 Fbn Kitten Persian 2Kg 35,23 27,30
RC306214 3182550721202 Fbn Kitten Persian 400Gr 8,07 6,25
RC306238 3182550721226 Fbn Kitten Persian 4Kg 60,51 46,45
RC398321 9003579001219 Fbn Maine Coon Gravy Pouch 85Gr X 12Ud 19,76 14,74
RC309361 3182550710664 Fbn Mainecoon Adult 10Kg 109,16 87,28
RC309330 3182550710640 Fbn Mainecoon Adult 2Kg 31,36 24,58
RC309338 3182550710657 Fbn Mainecoon Adult 4Kg 52,42 41,90
RC309760 3182550825405 Fbn Norwegian Forest Cat 10Kg 109,16 87,28
RC309728 3182550825399 Fbn Norwegian Forest Cat 2Kg 31,36 24,58
RC306861 3182550702621 Fbn Persian Adult 10Kg 109,16 87,28
RC306830 3182550702614 Fbn Persian Adult 2Kg 31,36 24,58
RC306813 3182550702607 Fbn Persian Adult 400Gr 7,30 5,59
RC306838 3182550704533 Fbn Persian Adult 4Kg 52,42 41,90
RC398021 9003579001172 Fbn Persian Pate Pouch 85Gr X 12Ud 19,76 14,74
RC309100 3182550825351 Fbn Ragdoll Adult 2Kg 31,36 24,58
RC309161 3182550710701 Fbn Siamese Adult 10Kg 109,16 87,28
RC309129 3182550710688 Fbn Siamese Adult 2Kg 31,36 24,58
RC307061 3182550758857 Fbn Sphynx Adult 10Kg 109,16 87,28
RC307029 3182550758840 Fbn Sphynx Adult 2Kg 31,36 24,58
FCN
RC388800 9003579014905 Fcn Appetite Control Gravy Pouch 85Gr X 12Ud 19,83 15,82
RC388820 9003579016923 Fcn Appetite Control Jelly Pouch 85Gr X 12Ud 19,83 15,82
RC308330 3182550920384 Fcn Appetite Control Sterilised 10Kg 111,84 89,44
RC308310 3182550920391 Fcn Appetite Control Sterilised 2Kg 32,89 25,24
RC308320 3182550920407 Fcn Appetite Control Sterilised 3,5Kg 47,02 37,59
Cod.
Producto Cod. Ean Descripción
Tarifa
P.V.P.R.
Tarifa P.V.T.
RC308300 3182550920414 Fcn Appetite Control Sterilised 400Gr 7,17 5,71
RC317427 3182550717182 Fcn Care Dental 1,5Kg 23,65 18,92
RC317453 3182550721622 Fcn Care Dental 8Kg 89,46 71,55
RC382024 9003579309537 Fcn Care Digestive Gravy Pouch 85Gr X 12Ud 19,83 15,82
RC317060 3182550752015 Fcn Digestive Care 10Kg 111,84 89,44
RC317028 3182550751995 Fcn Digestive Care 2Kg 32,89 25,24
RC317012 3182550751988 Fcn Digestive Care 400Gr 7,17 5,71
RC317029 3182550752008 Fcn Digestive Care 4Kg 53,74 42,94
RC307161 3182550721752 Fcn Hair & Skin 33 10Kg 111,84 89,44
RC307129 3182550721738 Fcn Hair & Skin 33 2Kg 32,89 25,24
RC307137 3182550721745 Fcn Hair & Skin 33 4Kg 53,74 42,94
RC307113 3182550721721 Fcn Hair & Skin33 400Gr 7,17 5,71
RC380524 9003579308929 Fcn Hair Skin Gravy Pouch 85Gr X 12Ud 19,83 15,82
RC380825 9003579311721 Fcn Hair Skin Jelly Pouch 85Gr X 12Ud 19,83 15,82
RC313561 3182550721424 Fcn Hairball Care 10Kg 111,84 89,44
RC313529 3182550721400 Fcn Hairball Care 2Kg 32,89 25,24
RC313513 3182550721394 Fcn Hairball Care 400Gr 7,17 5,71
RC313537 3182550721417 Fcn Hairball Care 4Kg 53,74 42,94
RC391025 9003579000410 Fcn Hairball Care Gravy Pouch 85Gr X 12Ud 19,83 15,82
RC625095 Fcn Hairball Care Jelly Pouch 85Gr X 12Ud 22,60 15,82
RC318630 3182550902991 Fcn Light Weight Care 1,5Kg 23,65 18,92
RC318636 3182550903929 Fcn Light Weight Care 3Kg 40,19 32,17
RC318613 3182550706810 Fcn Light Weight Care 40 400Gr 7,17 5,71
RC318662 3182550902984 Fcn Light Weight Care 8Kg 89,46 71,55
RC380024 9003579308769 Fcn Ultralight Gravy Pouch 85Gr X 12Ud 19,83 15,82
RC380324 9003579311738 Fcn Ultralight Jelly Pouch 85Gr X 12Ud 19,83 15,82
RC307360 3182550842969 Fcn Urinary Care 10Kg 111,84 89,44
RC307328 3182550842938 Fcn Urinary Care 2Kg 32,89 25,24
RC307312 3182550842907 Fcn Urinary Care 400Gr 7,17 5,71
RC307336 3182550842952 Fcn Urinary Care 4Kg 53,74 42,94
RC391125 9003579000366 Fcn Urinary Care Gravy Pouch 85Gr X 12Ud 19,83 15,82
RC625096 Fcn Urinary Care Jelly Pouch 85Gr X 12Ud 22,60 15,82
FHN
RC625108 9003579050170 Fhn Ageing +15 Gravy Pouch 85Gr X 12Ud 20,80 14,53
RC625099 3182551066005 Fhn Ageing+11 2Kg 33,77 23,63
RC625098 3182551065916 Fhn Ageing+11 400Gr 7,71 5,40
RC625100 3182551066098 Fhn Ageing+11 4Kg 57,49 40,24
RC625106 9003579050095 Fhn Ageing+11 Gravy Pouch 85Gr X 12Ud 20,80 14,53
RC625107 9003579050057 Fhn Ageing+11 Jelly Pouch 85Gr X 12Ud 20,80 14,53
RC625101 3182551066036 Fhn Ageing+11 Sterilised 2Kg 33,77 23,63
RC625102 3182551066210 Fhn Ageing+11 Sterilised 4Kg 57,49 40,24
RC625104 3182551066067 Fhn Ageing+15 2Kg 34,37 24,05
RC625103 3182551065978 Fhn Ageing+15 400Gr 7,84 5,49
RC625105 3182551066128 Fhn Ageing+15 4Kg 58,49 40,94
RC377808 9003579311660 Fhn Babycat Instinctive Lata 195Gr X 12Ud 40,55 32,55
RC310310 3182550710862 Fhn Babycat Milk 300 Gr 24,87 19,85
RC315160 3182550702249 Fhn Fit 32 10Kg 90,96 72,76
RC315128 3182550702201 Fhn Fit 32 2Kg 25,68 20,55
RC315112 3182550702157 Fhn Fit 32 400Gr 6,09 4,69
RC315136 3182550702225 Fhn Fit 32 4Kg 43,63 34,89
RC625112 3182551065763 Fhn Fussy 10Kg 106,23 74,36
RC625110 3182551065701 Fhn Fussy 2Kg 29,96 20,97
RC625109 3182551065671 Fhn Fussy 400Gr 6,84 4,78
RC625111 3182551065732 Fhn Fussy 4Kg 50,98 35,69
RC312827 3182550784399 Fhn Indoor +7 Ageing 1,5Kg 23,69 17,32
RC312834 3182550784412 Fhn Indoor +7 Ageing 3,5Kg 46,55 34,44
RC312812 3182550784351 Fhn Indoor +7 Ageing 400Gr 7,03 5,15
RC312361 3182550706940 Fhn Indoor 27 10Kg 93,19 74,57
RC312329 3182550704625 Fhn Indoor 27 2Kg 27,83 21,06
Cod.
Producto Cod. Ean Descripción
Tarifa
P.V.P.R.
Tarifa P.V.T.
RC312313 3182550704618 Fhn Indoor 27 400Gr 6,75 4,81
RC312337 3182550706933 Fhn Indoor 27 4Kg 46,48 35,82
RC387800 Fhn Indoor Sterilised Gravy Pouch 85Gr X 12Ud 16,85 13,27
RC387820 Fhn Indoor Sterilised Jelly Pouch 85Gr X 12Ud 16,85 13,27
RC383024 9003579310168 Fhn Instinctive +7 Gravy Pouch 85Gr X 12Ud 18,26 14,62
RC379024 9003579308936 Fhn Instinctive Gravy Pouch 85Gr X 12Ud 16,85 13,27
RC379304 9003579309513 Fhn Instinctive Jelly Pouch 85Gr X 12Ud 16,85 13,27
RC379404 9003579003886 Fhn Instinctive Pate Pouch 85Gr X 12Ud 16,85 13,27
RC310862 3182550702973 Fhn Kitten 36 10Kg 102,09 81,65
RC310830 3182550702423 Fhn Kitten 36 2Kg 29,20 23,00
RC310814 3182550702379 Fhn Kitten 36 400G 6,59 5,25
RC310838 3182550702447 Fhn Kitten 36 4Kg 49,02 39,20
RC378524 9003579308943 Fhn Kitten Instinctive Gravy Pouch 85Gr X 12Ud 19,42 14,25
RC378825 9003579311714 Fhn Kitten Instinctive Jelly Pouch 85Gr X 12Ud 19,42 14,25
RC378924 9003579003848 Fhn Kitten Instinctive Pate Pouch 85Gr X 12Ud 19,42 14,25
RC316228 3182550805186 Fhn Kitten Sterilised 2Kg 29,20 23,00
RC316235 3182550877831 Fhn Kitten Sterilised 3,5Kg 43,81 34,30
RC316210 3182550805155 Fhn Kitten Sterilised 400Gr 6,59 5,25
RC390624 9003579007136 Fhn Kitten Sterilised Gravy Pouch 85Gr X 12Ud 19,42 14,25
RC378324 9003579007174 Fhn Kitten Sterilised Jelly Pouch 85Gr X 12Ud 19,42 14,25
RC310759 3182550931038 Fhn Mother&Babycat 10Kg 106,46 85,15
RC310740 3182550707312 Fhn Mother&Babycat 2Kg 32,15 24,00
RC310715 3182550707305 Fhn Mother&Babycat 400Gr 6,89 5,45
RC310755 3182550707329 Fhn Mother&Babycat 4Kg 51,58 40,85
RC315629 3182550707374 Fhn Outdoor 30 2Kg 27,83 21,06
RC318061 3182550702355 Fhn Sensible 33 10Kg 90,96 72,76
RC318027 3182550702317 Fhn Sensible 33 2Kg 25,68 20,55
RC318013 3182550702263 Fhn Sensible 33 400Gr 6,09 4,69
RC318037 3182550702331 Fhn Sensible 33 4Kg 43,63 34,89
RC390715 Fhn Sensory Feel Gravy Pouch 85Gr X 12Ud 16,85 13,27
RC390700 Fhn Sensory Smell Gravy Pouch 85Gr X 12Ud 16,85 13,27
RC390710 Fhn Sensory Taste Gravy Pouch 85Gr X 12Ud 16,85 13,27
RC316527 3182550784566 Fhn Sterilised +7 1,5Kg 23,69 17,02
RC316534 3182550784580 Fhn Sterilised +7 3,5Kg 46,52 33,77
RC316512 3182550784511 Fhn Sterilised +7 400Gr 7,19 5,17
RC319160 3182550737623 Fhn Sterilised 37 10Kg 91,42 73,13
RC319128 3182550737593 Fhn Sterilised 37 2Kg 25,81 20,65
RC319112 3182550737555 Fhn Sterilised 37 400Gr 6,12 4,71
RC319136 3182550737616 Fhn Sterilised 37 4Kg 43,84 35,06
RC390024 9003579311301 Fhn Sterilised Gravy Pouch 85Gr X 12Ud 16,85 13,27
RC390324 9003579311776 Fhn Sterilised Jelly Pouch 85Gr X 12Ud 16,85 13,27
RC390424 9003579003923 Fhn Sterilised Pate Pouch 85Gr X 12Ud 16,85 13,27
LHN
RC625087 3182551063608 LHN Digestive Support Chews Adult Suplement 6x160g 59,50 41,65
RC625086 3182551063561 LHN Immune Digestion Suport Chews Puppy 8x100Gr 79,29 55,50
RC625089 3182551063684 LHN Joint Ageing Adult Supplement 5x240Gr 64,93 45,45
RC625088 3182551063639 LHN Skin Coat Chews Adult Supplement 5x240Gr 64,93 45,45
RC145172 3182550837958 LHN Sport Life Trail 4300 15Kg 98,42 73,58
RC625090 3182551063721 LHN Training Treats 8x110Gr 27,79 19,45
RC625091 3182551063226 LHN Treats Gastrointestinal 6x230Gr 42,50 29,75
RC625092 3182551063165 LHN Treats Hypoallergenic 6x230Gr 42,50 29,75
RC625093 3182551063196 LHN Treats Satiety 6x230Gr 42,50 29,75
RC625094 3182551063134 LHN Treats Urinary 6x230Gr 42,50 29,75
SHN
RC356160 9003579008829 Shn Care Dermacomfort Pouch 12 x 85gr 15,99 11,27
RC356150 9003579008782 Shn Care Digestive Pouch 12 x 85gr 15,99 11,27
RC356180 9003579009468 Shn Care Exigent Pouch 12 x 85Gr 15,99 11,27
RC356130 9003579008706 Shn Care Light Weight Pouch 12 x 85gr 15,99 11,27
RC153966 3182550928540 Shn Care Maxi Dermacomfort 12kg 79,02 63,17
Cod.
Producto Cod. Ean Descripci
ó
n
Tarifa
P.V.P.R.
Tarifa P.V.T.
RC153932 3182550773850 Shn Care Maxi Dermacomfort 3Kg 25,77 19,55
RC154201 Shn Care Maxi Digestive Care 12kg 79,02 63,17
RC153165 3182550893701 Shn Care Maxi Joint Care 10kg 71,82 55,27
RC154075 3182550928625 Shn Care Maxi Light Weight 12kg 79,02 63,17
RC154032 3182550852364 Shn Care Maxi Light Weightcare 3Kg 25,77 19,55
RC153767 3182550928748 Shn Care Maxi Sterilised 12kg 79,02 63,17
RC153735 3182550852081 Shn Care Maxi Sterilised 3kg 25,77 19,55
RC152763 3182550928526 Shn Care Medium Dermacomfort 12Kg 79,02 63,17
RC152732 3182550773829 Shn Care Medium Dermacomfort 3Kg 25,77 19,55
RC152664 3182550928663 Shn Care Medium Digestive Care 12kg 79,02 63,17
RC152632 3182550852678 Shn Care Medium Digestive Care 3Kg 25,77 19,55
RC152461 3182550928588 Shn Care Medium Light Weightcare 12 Kg 79,02 63,17
RC152433 3182550852319 Shn Care Medium Light Weightcare 3 Kg 25,77 19,55
RC152166 3182550928724 Shn Care Medium Sterilised 12kg 79,02 63,17
RC152132 3182550787826 Shn Care Medium Sterilised 3Kg 25,77 19,55
RC151650 3182550894371 Shn Care Mini Dental Care 3kg 26,87 20,62
RC151630 3182550893886 Shn Care Mini Dermacomfort 1kg 12,37 8,49
RC151635 3182550893916 Shn Care Mini Dermacomfort 3kg 26,87 20,62
RC151658 3182550894999 Shn Care Mini Dermacomfort 8kg 66,49 52,48
RC151130 3182550893947 Shn Care Mini Digestive Care 1Kg 12,37 8,49
RC151135 3182550894012 Shn Care Mini Digestive Care 3Kg 26,87 20,62
RC151139 3182550895057 Shn Care Mini Digestive Care 8kg 66,49 52,48
RC150830 3182550894050 Shn Care Mini Exigent 3Kg 26,87 20,62
RC150930 3182550894074 Shn Care Mini Light Weight Care 1Kg 12,37 8,49
RC150937 3182550894104 Shn Care Mini Light Weight Care 3Kg 26,87 20,62
RC150955 3182550716918 Shn Care Mini Light Weightcare 8 Kg 66,49 52,48
RC151420 3182550894142 Shn Care Mini Sterilised 1Kg 12,37 8,49
RC151424 3182550894128 Shn Care Mini Sterilised 3Kg 26,87 20,62
RC151451 3182550807074 Shn Care Mini Sterilised 8Kg 75,80 52,48
RC151670 3182550895156 Shn Care Mini Urinary Care 3kg 26,87 20,62
RC356140 9003579008744 Shn Care Sterilised Pouch 12 x 85gr 15,99 11,27
RC356170 9003579009383 Shn Care Urinary Pouch 12 x 85Gr 15,99 11,27
RC150900 3182550902045 Shn Care X-Small Light Weight 1,5Kg 19,69 13,26
RC149926 3182550832540 Shn Care Xsmall Sterilised 1,5Kg 19,69 13,26
RC155171 3182550703079 Shn Giant Adult 15Kg 81,99 63,52
RC154972 3182550707077 Shn Giant Junior 15Kg 87,17 68,45
RC154720 Shn Giant Puppy 1 Kg 9,69 5,65
RC154772 3182550707046 Shn Giant Puppy 15Kg 87,17 68,45
RC154870 3182550778831 Shn Giant Starter Mother & Baby 15Kg 97,50 74,70
RC153838 3182550402293 Shn Maxi Adult +5 4Kg 30,24 22,72
RC153873 3182550402316 Shn Maxi Adult +5 15Kg 89,47 71,50
RC153651 3182551055931 Shn Maxi Adult 10Kg 57,16 44,58
RC153685 3182551055955 Shn Maxi Adult 15Kg 83,55 66,87
RC153638 3182551055894 Shn Maxi Adult 4Kg 27,68 21,23
RC356250 9003579029879 Shn Maxi Adult Lata 410Gr X 12Ud 47,04 32,90
RC356115 Shn Maxi Adult Pouch 140Gr X 10Ud 17,66 12,81
RC154170 3182550803113 Shn Maxi Ageing +8 15Kg 94,33 73,58
RC356260 9003579029930 Shn Maxi Ageing Lata 410Gr X 12Ud 51,60 36,10
RC356118 Shn Maxi Ageing Pouch 140Gr X 10Ud 19,52 14,01
RC153450 3182550402460 Shn Maxi Puppy 1 Kg 7,72 5,95
RC153470 3182550778305 Shn Maxi Puppy 10Kg 61,58 48,05
RC153482 3182550402163 Shn Maxi Puppy 15Kg 90,08 72,05
RC153439 3182550402149 Shn Maxi Puppy 4Kg 28,53 22,85
RC356110 9003579008454 Shn Maxi Puppy Pouch 140Gr X 10Ud 19,59 13,70
RC153370 3182550778787 Shn Maxi Starter Mother & Baby 15Kg 98,19 78,60
RC153336 3182550778770 Shn Maxi Starter Mother & Baby 4Kg 32,15 24,95
RC152237 3182550708203 Shn Medium Adult +7 4Kg 30,24 22,72
RC152272 3182550402286 Shn Medium Adult +7 15 Kg 89,47 71,50
RC152061 3182551055825 Shn Medium Adult 10Kg 55,79 44,58
Cod.
Producto Cod. Ean Descripción
Tarifa
P.V.P.R.
Tarifa P.V.T.
RC152078 3182551055849 Shn Medium Adult 15Kg 83,55 66,87
RC152038 3182551055788 Shn Medium Adult 4Kg 26,62 21,23
RC356230 9003579029763 Shn Medium Adult Lata 410Gr X 12Ud 47,04 32,90
RC356105 Shn Medium Adult Pouch 140Gr X 10Ud 17,62 12,81
RC152370 3182550802758 Shn Medium Ageing +10 15Kg 93,27 73,58
RC152332 3182550802734 Shn Medium Ageing +10 3Kg 28,66 17,52
RC356240 9003579029824 Shn Medium Ageing Lata 410Gr X 12Ud 51,60 36,10
RC356107 Shn Medium Ageing Pouch 140Gr X 10Ud 19,52 14,01
RC151850 Shn Medium Puppy 10Kg 61,58 48,05
RC151875 3182550402132 Shn Medium Puppy 15Kg 90,08 72,05
RC151827 3182550402439 Shn Medium Puppy 1Kg 7,72 5,95
RC151842 3182550708180 Shn Medium Puppy 4Kg 28,53 22,85
RC356100 Shn Medium Puppy Pouch 140Gr X 10Ud 19,60 13,70
RC151950 3182550778718 Shn Medium Starter Mother & Baby 1 Kg 8,70 6,50
RC151968 3182550932714 Shn Medium Starter Mother & Baby 15 Kg 98,19 78,60
RC151936 3182550778725 Shn Medium Starter Mother & Baby 4Kg 32,15 24,95
RC150533 3182551055672 Shn Mini Adult 2Kg 17,67 13,46
RC150538 3182551055719 Shn Mini Adult 4Kg 29,13 22,65
RC150522 3182551055634 Shn Mini Adult 800Gr 7,24 5,57
RC150560 3182551055740 Shn Mini Adult 8Kg 53,94 43,12
RC356200 9003579029633 Shn Mini Adult Lata 195Gr X 12Ud 22,32 15,60
RC356005 9003579008256 Shn Mini Adult Pouch 85Gr X 12Ud 13,31 9,27
RC151030 3182550793575 Shn Mini Ageing +12 1,5Kg 17,14 11,14
RC151038 3182550793582 Shn Mini Ageing +12 3,5Kg 29,69 21,78
RC356210 9003579029701 Shn Mini Ageing Lata 195Gr X 12Ud 24,60 17,20
RC356007 9003579008294 Shn Mini Ageing Pouch 85Gr X 12Ud 15,00 10,07
RC150730 3182550831383 Shn Mini Mature +8 2Kg 19,26 14,13
RC150737 3182550831390 Shn Mini Mature +8 4Kg 31,20 23,72
RC150753 3182550831406 Shn Mini Mature +8 8Kg 57,27 45,29
RC150320 3182550793001 Shn Mini Puppy 2Kg 18,47 14,30
RC150348 3182550793032 Shn Mini Puppy 4Kg 30,00 24,00
RC150318 3182550792929 Shn Mini Puppy 800Gr 7,71 5,95
RC150350 3182550793049 Shn Mini Puppy 8Kg 58,53 45,77
RC356001 9003579008218 Shn Mini Puppy Pouch 85Gr X 12Ud 15,64 9,95
RC151224 3182550778657 Shn Mini Starter Mother & Baby 1Kg 13,63 8,10
RC151235 3182550932707 Shn Mini Starter Mother & Baby 4 Kg 34,01 26,20
RC151240 3182550932691 Shn Mini Starter Mother & Baby 8 Kg 63,38 49,97
RC357009 9003579311462 Shn Starter Mousse Lata 195Gr X 12Ud 33,49 25,05
RC150126 3182550793728 Shn Xsmall Adult 1,5Kg 15,61 10,88
RC150136 3182550793735 Shn Xsmall Adult 3Kg 26,38 17,47
RC150114 3182550793704 Shn Xsmall Adult 500Gr 6,47 3,76
RC356280 9003579028964 Shn XSmall Adult Pouch 85Gr X 12Ud 13,31 9,29
RC151020 3182550793858 Shn Xsmall Ageing +12 1,5Kg 17,66 12,01
RC150226 3182550831345 Shn Xsmall Mature +8 1,5Kg 16,54 11,44
RC150214 3182550831376 Shn Xsmall Mature +8 500Gr 7,25 3,97
RC150026 3182550793612 Shn Xsmall Puppy 1,5Kg 15,58 11,60
RC150036 3182550793636 Shn Xsmall Puppy 3Kg 23,35 18,50
RC150014 3182550793568 Shn Xsmall Puppy 500Gr 6,76 4,00
RC356020 Shn XSmall Puppy Pouch 85Gr X 12Ud 15,64 9,95
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
            print(f"  ✅ Añadido: [{nuevo_sku}] {nombre} (PVP: {pvp}€ | Coste: {coste}€)")

print(f"\n🎉 ¡Magia completada! {insertados} productos de Royal Canin insertados. {omitidos} omitidos.")