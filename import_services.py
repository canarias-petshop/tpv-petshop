import toml
from supabase import create_client, Client

secrets = toml.load(".streamlit/secrets.toml")
url = secrets["url"].strip('"').strip("'")
key = secrets["key"].strip('"').strip("'")
supabase: Client = create_client(url, key)

pesos = ['0-5 kg', '5-10 kg', '10-20 kg', '20-40 kg', '40+ kg']

completos = {
    "Baño": [22, 25, 31, 35, 39],
    "Baño pelo largo": [26, 29, 36, 40, 45],
    "Baño de ozono": [26, 32, 39, 41, 46],
    "Retoque": [28, 32, 39, 48, 59],
    "Corte máquina": [31, 35, 43, 55, 68],
    "Corte MRT": [37, 41, 49, 61, 77],
    "Esculpido": [49, 59, 71, 86, 110],
    "Corte a tijera": [43, 51, 59, 80, 98],
    "Deslanado": [33, 42, 54, 68, 78],
    "Cepillado": [26, 34, 43, 57, 69],
    "Stripping": [45, 59, 75, 96, 115],
    "Uñas": [8, 8, 8, 8, 8]
}

individuales = {
    "Baño": [20, 23, 29, 35, 39],
    "Baño pelo largo": [26, 29, 34, 40, 45],
    "Baño de ozono": [24, 30, 35, 41, 46],
    "Retoque": [11, 14, 16, 19, 19],
    "Corte máquina": [11, 17, 22, 32, 44],
    "Corte a máquina, recalde y tijera": [22, 28, 33, 44, 55],
    "Esculpido": [33, 39, 44, 66, 77],
    "Corte a tijera": [24, 30, 36, 55, 64],
    "Deslanado": [11, 17, 22, 28, 33],
    "Cepillado": [6, 11, 17, 22, 28],
    "Stripping": [28, 39, 50, 66, 83],
    "Uñas": [8, 8, 8, 8, 8]
}

extras_pesos = {
    "Champú específico (Duoxo) / Pelo Blanco": [5, 7, 10, 13, 18],
    "Champú antiparasitario": [4, 4, 5, 6, 7],
    "Mascarilla": [3, 6, 8, 10, 12]
}

gatos_fijos = {
    "Corte a maquina/tijera (tratamiento completo gato)": 45,
    "Corte maquina/tijera (tratamiento individual gato)": 40,
    "Arreglo (tratamiento completo gato)": 43,
    "Arreglo (tratamiento individual gato)": 37
}

extras_fijos = {
    "Nudos (extra/h)": 22,
    "Perros agresivos / muy nerviosos (extra/h)": 32
}

servicios_a_insertar = []

# Completos
for srv, precios in completos.items():
    for i, p in enumerate(precios):
        nombre = f"{srv} (completo) {pesos[i]}"
        servicios_a_insertar.append((nombre, p))

# Individuales
for srv, precios in individuales.items():
    for i, p in enumerate(precios):
        nombre = f"{srv} (individual) {pesos[i]}"
        servicios_a_insertar.append((nombre, p))

# Extras con peso
for srv, precios in extras_pesos.items():
    for i, p in enumerate(precios):
        # Los extras son "Resto de servicios" -> sin (individual) ni (completo)
        nombre = f"{srv} {pesos[i]}"
        servicios_a_insertar.append((nombre, p))
        
# Gatos
for srv, p in gatos_fijos.items():
    servicios_a_insertar.append((srv, p))

# Extras fijos
for srv, p in extras_fijos.items():
    servicios_a_insertar.append((srv, p))

# Get latest SKU for SRV to avoid collision
res = supabase.table("productos").select("sku").ilike("sku", "SRV-%").execute()
max_srv = 0
if res.data:
    for row in res.data:
        try:
            num = int(row['sku'].split("-")[1])
            if num > max_srv:
                max_srv = num
        except:
            pass

igic = 7.0

records = []
for i, (nombre, pvp) in enumerate(servicios_a_insertar):
    max_srv += 1
    sku = f"SRV-{max_srv:03d}"
    precio_base = round(pvp / (1 + (igic / 100)), 4)
    
    records.append({
        "sku": sku,
        "nombre": nombre,
        "marca": "Servicio",
        "categoria": "Peluquería",
        "precio_base": precio_base,
        "precio_pvp": pvp,
        "igic_tipo": igic,
        "stock_actual": 999, # Servicios no se agotan
        "stock_minimo": 0
    })

print(f"Total servicios a insertar: {len(records)}")

try:
    chunk_size = 50
    for i in range(0, len(records), chunk_size):
        chunk = records[i:i+chunk_size]
        supabase.table("productos").insert(chunk).execute()
        print(f"Insertados {i + len(chunk)} / {len(records)}")
    print("¡Todos los servicios insertados con éxito!")
except Exception as e:
    print(f"Error durante la inserción: {e}")
