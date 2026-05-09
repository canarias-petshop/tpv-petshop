import toml
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

print("🤖 Iniciando el Robot Explorador de Argomanza...")

# 1. Leer tus claves en secreto
secrets_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
with open(secrets_path, "r") as f:
    secrets = toml.load(f)

email_argo = secrets.get("argomanza", {}).get("email", "")
pass_argo = secrets.get("argomanza", {}).get("password", "")

if not email_argo or not pass_argo:
    print("❌ Error: No he encontrado tus claves en secrets.toml bajo [argomanza].")
    exit()

# 2. Configurar Google Chrome para que lo controle el robot
chrome_options = Options()

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

try:
    # 3. Entrar a la web
    print("🌐 Abriendo la página de inicio de sesión...")
    driver.get("https://b2b.argomanza.com/customer/account/login/")
    time.sleep(3) # Esperar a que cargue
    
    # 4. Inyectar usuario y contraseña
    print("🔑 Introduciendo credenciales...")
    driver.find_element(By.ID, "email").send_keys(email_argo)
    driver.find_element(By.ID, "pass").send_keys(pass_argo)
    
    # 5. Hacer clic en Entrar
    driver.find_element(By.ID, "send2").click()
    
    print("✅ ¡Botón de entrar pulsado! Revisa la ventana de Chrome que se ha abierto.")
    input("Presiona Enter aquí en la terminal cuando quieras cerrar el robot...")
finally:
    driver.quit()