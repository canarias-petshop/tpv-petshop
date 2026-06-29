import os
import zipfile
from datetime import datetime

# Rutas
RUTA_WEB = r"D:\clon vs mode\web-petshop"
RUTA_TPV = r"D:\clon vs mode\tpv-petshop"
RUTA_MAESTRA = r"D:\clon vs mode\tpv-petshop\Backups_Datos_Nube"

# Excluir carpetas pesadas/autogeneradas
EXCLUIR_DIRS = {".venv", "node_modules", ".next", ".git", "__pycache__"}

def crear_backup_codigo():
    if not os.path.exists(RUTA_MAESTRA):
        os.makedirs(RUTA_MAESTRA)
        
    fecha_hoy = datetime.now().strftime("%Y_%m_%d")
    hora_hoy = datetime.now().strftime("%H_%M")
    nombre_zip = os.path.join(RUTA_MAESTRA, f"Backup_Codigo_{fecha_hoy}_{hora_hoy}.zip")
    
    print(f"⏳ Comprimiendo código fuente en: {nombre_zip}")
    
    with zipfile.ZipFile(nombre_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Añadir TPV
        for root, dirs, files in os.walk(RUTA_TPV):
            dirs[:] = [d for d in dirs if d not in EXCLUIR_DIRS and not d.startswith("Backup_")]
            for file in files:
                if file.endswith(".zip"): continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(RUTA_TPV))
                zipf.write(file_path, arcname)
                
        # Añadir Web
        if os.path.exists(RUTA_WEB):
            for root, dirs, files in os.walk(RUTA_WEB):
                dirs[:] = [d for d in dirs if d not in EXCLUIR_DIRS]
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(RUTA_WEB))
                    zipf.write(file_path, arcname)
                    
    print("✅ ¡Copia del código fuente terminada con éxito!")

if __name__ == "__main__":
    crear_backup_codigo()
