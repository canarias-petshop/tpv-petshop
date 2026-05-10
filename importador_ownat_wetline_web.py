import toml
import os
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from postgrest import SyncPostgrestClient

print("🤖 Iniciando Robot Importador de Ownat Wetline (Web a TPV)...")

# 1. Conectar a Base de Datos
secrets_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
with open(secrets_path, "r") as f: secrets = toml.load(f)
raw_url = secrets.get('url', '').strip().strip('"').strip("'").rstrip('/')
api_url = raw_url if raw_url.endswith('/rest/v1') else f"{raw_url}/rest/v1"
api_key = secrets.get('key', '').strip().strip('"').strip("'")
client = SyncPostgrestClient(api_url, headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"})

# Asegurar proveedor (Zootecnia)
NOMBRE_PROV = "Zootecnia - Zootecnia S.L."
res_prov = client.table("proveedores").select("id").eq("nombre_empresa", NOMBRE_PROV).execute()
prov_id = res_prov.data[0]['id'] if res_prov.data else client.table("proveedores").insert({"nombre_empresa": NOMBRE_PROV}).execute().data[0]['id']

# Skus y Nombres existentes
res_prod = client.table("productos").select("sku, nombre").execute()
skus_existentes = {str(p['sku']).upper() for p in res_prod.data} if res_prod.data else set()
nombres_existentes = {str(p['nombre']).lower() for p in res_prod.data} if res_prod.data else set()

contador_sku = 1
def generar_sku():
    global contador_sku
    while True:
        ns = f"OWW-{contador_sku:03d}"
        if ns not in skus_existentes: return ns
        contador_sku += 1

# 2. Configurar Robot
email_argo = secrets.get("argomanza", {}).get("email", "")
pass_argo = secrets.get("argomanza", {}).get("password", "")

chrome_options = Options()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

try:
    print("🌐 Iniciando sesión en la plataforma B2B...")
    driver.get("https://b2b.argomanza.com/customer/account/login/")
    time.sleep(3)
    driver.find_element(By.ID, "email").send_keys(email_argo)
    driver.find_element(By.ID, "pass").send_keys(pass_argo)
    driver.find_element(By.ID, "send2").click()
    time.sleep(4)
    
    # --- ENLACE A LA CATEGORÍA DE WETLINE (HÚMEDO) ---
    URL_CATEGORIA = "https://b2b.argomanza.com/gatos/alimento-humedo/wetline"
    # -----------------------------------------------------------
    
    print(f"🚀 Extrayendo productos de: {URL_CATEGORIA}")
    driver.get(URL_CATEGORIA)
    time.sleep(5)
    
    productos = driver.find_elements(By.CSS_SELECTOR, ".product-item-info")
    insertados = 0
    
    for prod in productos:
        texto = prod.text.strip()
        if not texto: continue
            
        lineas = [L.strip() for L in texto.split('\n') if L.strip()]
        if not lineas: continue
            
        nombre = lineas[0] # La primera línea suele ser el nombre
        
        # Buscar el precio en el texto
        match_precio = re.search(r'(\d+,\d{2})\s*€', texto)
        if not match_precio: continue
            
        coste = float(match_precio.group(1).replace(',', '.'))
        # Margen base automático del 40% (puedes editarlo en la app luego)
        pvp_estimado = round(coste * 1.40, 2) 
        
        if nombre.lower() in nombres_existentes:
            print(f"⚠️ Omitido (Ya existe): {nombre}")
            continue
            
        nuevo_sku = generar_sku()
        
        res_ins = client.table("productos").insert({
            "sku": nuevo_sku, "codigo_barras": "", "nombre": nombre, "categoria": "Producto",
            "precio_base": coste, "igic_tipo": 3.0, "precio_pvp": pvp_estimado, "stock_actual": 0,
            "stock_minimo": 2, "cantidad_reponer": 5
        }).execute()
        
        if res_ins.data:
            client.table("productos_proveedores").insert({"producto_id": res_ins.data[0]['id'], "proveedor_id": prov_id, "precio_coste": coste}).execute()
            skus_existentes.add(nuevo_sku); nombres_existentes.add(nombre.lower()); insertados += 1
            print(f"  ✅ Importado: [{nuevo_sku}] {nombre} | Coste: {coste}€")
            
    print(f"\n🎉 ¡Magia completada! {insertados} latas de Ownat Wetline importadas a Zootecnia.")

finally:
    driver.quit()