import pandas as pd
import toml
from postgrest import SyncPostgrestClient
import os
import glob

# ==========================================
# --- 1. CONFIGURACIÓN DE LA CARPETA ---
# ==========================================
CARPETA_EXCEL = "fichas importadas sueltas"

# ==========================================
# --- 2. CONECTAR A SUPABASE ---
# ==========================================
def init_supabase():
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    if not os.path.exists(secrets_path):
        print("❌ Error: No se encontró el archivo de contraseñas.")
        exit()
        
    with open(secrets_path, "r") as f:
        secrets = toml.load(f)
        
    raw_url = secrets.get('url', '').strip().strip('"').strip("'").rstrip('/')
    api_url = raw_url if raw_url.endswith('/rest/v1') else f"{raw_url}/rest/v1"
    api_key = secrets.get('key', '').strip().strip('"').strip("'")
    
    return SyncPostgrestClient(api_url, headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"})

print("🔌 Conectando a Supabase...")
client = init_supabase()

# ==========================================
# --- 3. CARGAR BASE DE DATOS ACTUAL ---
# ==========================================
print("📥 Descargando listado actual para no duplicar datos...")
res_clientes = client.table("clientes").select("id, nombre_dueno, telefono").execute()
res_mascotas = client.table("mascotas").select("id, nombre, cliente_id").execute()

clientes_db = res_clientes.data if res_clientes.data else []
mascotas_db = res_mascotas.data if res_mascotas.data else []

mapa_clientes = {f"{str(c.get('nombre_dueno')).strip().lower()} - {str(c.get('telefono')).strip()}": c['id'] for c in clientes_db}
mapa_mascotas = {f"{str(m.get('nombre')).strip().lower()} - {m.get('cliente_id')}": m['id'] for m in mascotas_db}

# ==========================================
# --- 4. IMPORTADOR INTELIGENTE (FORMULARIOS) ---
# ==========================================
archivos = [f for f in os.listdir(CARPETA_EXCEL) if f.endswith(('.xlsx', '.xls')) and not f.startswith('~')]

if not archivos:
    print(f"❌ No se encontraron archivos Excel en la carpeta '{CARPETA_EXCEL}'.")
    exit()

clientes_nuevos = 0
mascotas_nuevas = 0

print(f"\n🔍 Procesando {len(archivos)} fichas...")

def buscar_valor_junto_a(df, palabra_clave):
    """Busca una palabra en todo el Excel sin límite de filas/columnas y devuelve el valor a su derecha."""
    max_filas = len(df)
    max_cols = len(df.columns)
    
    for fila in range(max_filas):
        for col in range(max_cols - 1):
            celda = str(df.iloc[fila, col]).lower().strip()
            if palabra_clave.lower() in celda:
                # Encontramos la palabra, miramos hacia la derecha (hasta 4 celdas por si hay combinadas o márgenes)
                for salto in range(1, min(5, max_cols - col)):
                    valor = str(df.iloc[fila, col + salto]).strip()
                    if valor and valor.lower() != "nan":
                        return valor
                return ""
    return ""

for archivo in archivos:
    ruta_completa = os.path.join(CARPETA_EXCEL, archivo)
    try:
        # Leemos el Excel sin cabeceras (header=None) porque es un formulario visual
        df_excel = pd.read_excel(ruta_completa, header=None)
        df_excel = df_excel.fillna("")
        
        dueño = buscar_valor_junto_a(df_excel, "nombre dueño")
        mascota = buscar_valor_junto_a(df_excel, "nombre mascota")
        telefono = buscar_valor_junto_a(df_excel, "teléfono")
        if not telefono: telefono = buscar_valor_junto_a(df_excel, "telefono") # Sin tilde por si acaso
        raza = buscar_valor_junto_a(df_excel, "raza")
        
        if not dueño or not mascota:
            print(f"⚠️ Saltando {archivo}: No se encontró el nombre del dueño o de la mascota.")
            continue
            
        clave_cliente = f"{dueño.lower()} - {telefono}"
        cliente_id = mapa_clientes.get(clave_cliente)
        
        if not cliente_id:
            res_ins_cli = client.table("clientes").insert({"nombre_dueno": dueño, "telefono": telefono, "puntos": 0, "rgpd_consent": True}).execute()
            if res_ins_cli.data:
                cliente_id = res_ins_cli.data[0]['id']
                mapa_clientes[clave_cliente] = cliente_id
                clientes_nuevos += 1
                
        if cliente_id:
            clave_mascota = f"{mascota.lower()} - {cliente_id}"
            if clave_mascota not in mapa_mascotas:
                print(f"  🐾 Importando: {mascota} (Dueño: {dueño})")
                client.table("mascotas").insert({"cliente_id": cliente_id, "nombre": mascota, "especie": "Perro", "raza": raza, "observaciones": ""}).execute()
                mapa_mascotas[clave_mascota] = True
                mascotas_nuevas += 1
                
    except Exception as e:
        print(f"❌ Error en {archivo}: {e}")

print(f"\n✅ ¡Sincronización Terminada! Se importaron {clientes_nuevos} clientes y {mascotas_nuevas} mascotas nuevas.")
