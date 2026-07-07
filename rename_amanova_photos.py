import os

FOTOS_DIR = r"C:\Users\truji\OneDrive\PERSONAL\Imágenes\Fotos productos\Amanova"

renombrados = 0
for root, dirs, files in os.walk(FOTOS_DIR):
    for file in files:
        if file.lower().startswith('amv-'):
            # Reemplazar 'amv-' por 'amanova-'
            nuevo_nombre = 'amanova-' + file[4:]
            
            ruta_antigua = os.path.join(root, file)
            ruta_nueva = os.path.join(root, nuevo_nombre)
            
            try:
                os.rename(ruta_antigua, ruta_nueva)
                renombrados += 1
                print(f"Renombrado: {file} -> {nuevo_nombre}")
            except Exception as e:
                print(f"Error renombrando {file}: {e}")
        elif file.lower().startswith('amv '):
            nuevo_nombre = 'amanova ' + file[4:]
            ruta_antigua = os.path.join(root, file)
            ruta_nueva = os.path.join(root, nuevo_nombre)
            try:
                os.rename(ruta_antigua, ruta_nueva)
                renombrados += 1
                print(f"Renombrado: {file} -> {nuevo_nombre}")
            except Exception as e:
                print(f"Error renombrando {file}: {e}")
                
print(f"Total de fotos renombradas: {renombrados}")
