import os

carpeta = "fichas_a_importar"
archivo_salida = "lista_nombres_excel.txt"

try:
    archivos = [f for f in os.listdir(carpeta) if f.endswith(('.xlsx', '.xls'))]
    
    with open(archivo_salida, "w", encoding="utf-8") as f:
        for nombre in archivos:
            f.write(nombre + "\n")
            
    print(f"✅ ¡Magia hecha! Se ha creado el archivo '{archivo_salida}' con los {len(archivos)} nombres.")
except Exception as e:
    print(f"❌ Uy, ha habido un error: {e}")