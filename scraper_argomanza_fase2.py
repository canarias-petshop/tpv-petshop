import toml
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

print("🤖 Iniciando la Fase 2 del Robot: Lectura de Catálogo...")

# 1. Leer tus claves en secreto
secrets_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
with open(secrets_path, "r") as f:
    secrets = toml.load(f)

email_argo = secrets.get("argomanza", {}).get("email", "")
pass_argo = secrets.get("argomanza", {}).get("password", "")

chrome_options = Options()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

try:
    print("🌐 Iniciando sesión...")
    driver.get("https://b2b.argomanza.com/customer/account/login/")
    time.sleep(3)
    
    driver.find_element(By.ID, "email").send_keys(email_argo)
    driver.find_element(By.ID, "pass").send_keys(pass_argo)
    driver.find_element(By.ID, "send2").click()
    time.sleep(4) # Le damos tiempo a la web para cargar tu sesión
    print("✅ Sesión iniciada con éxito.")
    
    # ---------------------------------------------------------
    # PASO IMPORTANTE: AQUÍ DEBES PONER EL ENLACE DE LA CATEGORÍA
    # Entra tú manualmente con tu navegador a la pestaña "PERROS"
    # Copia el enlace de arriba y sustitúyelo aquí abajo:
    URL_CATEGORIA = "https://b2b.argomanza.com/perros/pienso-humedo/gear" # <-- ¡CAMBIA ESTO!
    # ---------------------------------------------------------
    
    print(f"🚀 Navegando al catálogo: {URL_CATEGORIA}")
    driver.get(URL_CATEGORIA)
    time.sleep(5) # Esperamos a que carguen las fotos y precios
    
    print(f"📍 El robot está viendo esta dirección: {driver.current_url}")
    print(" Buscando productos en la pantalla...\n")
    
    # Atrapamos todos los productos usando una red mucho más grande (listas, tablas B2B, etc.)
    selector_amplio = ".product-item, .item.product, .product, .product-item-info, tr.item, tr.product, li.item, .product-list-item"
    productos = driver.find_elements(By.CSS_SELECTOR, selector_amplio)
    
    if not productos:
        print("⚠️ No encontré productos con el diseño estándar. Vamos a investigar qué está leyendo el robot:")
        texto_body = driver.find_element(By.TAG_NAME, "body").text
        print("--- INICIO DE LO QUE VE EL ROBOT ---")
        print(texto_body[:1500]) # Muestra los primeros 1500 caracteres de la web
        print("--- FIN ---")
        print("¿Ves los nombres de los productos y precios en el texto de arriba?")
    else:
        print(f"🎯 ¡Encontrados {len(productos)} productos en esta página!\n")
        for idx, prod in enumerate(productos):
            texto_caja = prod.text.replace('\n', ' | ')
            print(f"📦 Producto {idx + 1}: {texto_caja}")
            
    print("\n✅ Prueba de lectura finalizada. Revisa si en la consola salen los precios correctos.")
    input("Presiona Enter para cerrar el robot...")
    
finally:
    driver.quit()