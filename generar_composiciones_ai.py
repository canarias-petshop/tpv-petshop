import os
import sys
import json
import time
import urllib.request
import google.generativeai as genai
from postgrest import SyncPostgrestClient

# 1. Cargar secretos (usamos un método crudo para asegurar que funcione fuera de streamlit también)
try:
    with open('.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
        secrets_raw = f.read()
    
    url = ''
    key = ''
    gemini_key = ''
    for line in secrets_raw.split('\n'):
        if line.startswith('url '): url = line.split('=')[1].strip().strip('"').strip("'")
        if line.startswith('key '): key = line.split('=')[1].strip().strip('"').strip("'")
        if line.startswith('gemini_api_key '): gemini_key = line.split('=')[1].strip().strip('"').strip("'")
except Exception as e:
    print("Error cargando secretos:", e)
    sys.exit(1)

# 2. Configurar Clientes
db = SyncPostgrestClient(f"{url}/rest/v1", headers={'apikey': key, 'Authorization': f'Bearer {key}'})
genai.configure(api_key=gemini_key)

# Usamos el modelo más rápido y barato para tareas de texto
model = genai.GenerativeModel('gemini-2.5-flash')

def get_productos_sin_composicion(limite=5):
    # Buscamos productos que sean Alimentación o Snacks y que no tengan composición
    print(f"Buscando hasta {limite} productos sin composición en la base de datos...")
    
    # Postgrest syntax:
    # familia.in.(Alimentación seca,Alimentación húmeda,Alimentacion,Alimentación,Snack,Snacks)
    # composicion.is.null
    try:
        response = db.table("productos") \
            .select("id, nombre, marca, familia") \
            .is_("composicion", "null") \
            .neq("familia", "") \
            .not_.is_("familia", "null") \
            .limit(limite) \
            .execute()
            
        # Filtramos localmente para estar seguros
        validos = []
        for p in response.data:
            fam = str(p.get("familia")).lower()
            if "alimentaci" in fam or "snack" in fam:
                validos.append(p)
                
        return validos
    except Exception as e:
        print("Error obteniendo productos:", e)
        return []

def generar_composicion(producto):
    nombre = producto.get("nombre", "")
    marca = producto.get("marca", "")
    
    prompt = f"""
    Eres un experto en nutrición animal. 
    Necesito la composición nutricional (Ingredientes y Análisis Analítico/Constituyentes) del siguiente producto para mascotas:
    Nombre del producto: {nombre}
    Marca: {marca if marca and marca != 'Generico' else 'Desconocida'}
    
    Instrucciones estrictas:
    1. Si conoces el producto o puedes deducirlo con alta seguridad, devuelve la información.
    2. Si no tienes idea de cuál es el producto, responde exactamente con la palabra: NO_ENCONTRADO
    3. El formato de salida debe ser directamente HTML limpio (sin etiquetas <html>, <body> ni markdown envolvente). Solo el HTML interno.
    4. Usa esta estructura exacta:
    
    <div class="composicion-box">
      <h4 style="color: var(--primary); margin-top: 0;">Ingredientes</h4>
      <p style="font-size: 0.9rem; color: var(--text); line-height: 1.5;">
        [Lista de ingredientes aquí, separados por comas. Mantenlo en un solo párrafo.]
      </p>
      
      <h4 style="color: var(--primary); margin-top: 1rem;">Componentes Analíticos</h4>
      <ul style="font-size: 0.9rem; color: var(--text); line-height: 1.5; padding-left: 1.2rem;">
        <li><strong>Proteína bruta:</strong> [X]%</li>
        <li><strong>Grasa bruta:</strong> [X]%</li>
        <!-- Añade fibra, ceniza, calcio, fósforo, etc. si lo sabes -->
      </ul>
    </div>
    """
    
    try:
        res = model.generate_content(prompt)
        texto = res.text.strip()
        
        # Limpiar bloques markdown si la IA los pone por error
        if texto.startswith("```html"):
            texto = texto[7:]
        if texto.endswith("```"):
            texto = texto[:-3]
            
        texto = texto.strip()
        
        if "NO_ENCONTRADO" in texto:
            return None
            
        return texto
    except Exception as e:
        print(f"Error con Gemini para {nombre}:", e)
        return None

def actualizar_composicion(id_producto, html_composicion):
    try:
        db.table("productos").update({"composicion": html_composicion}).eq("id", id_producto).execute()
        return True
    except Exception as e:
        print(f"Error actualizando DB para {id_producto}:", e)
        return False

import re

def limpiar_nombre(nombre):
    # Quita pesos como 10KG, 100GR, 11.4 KG del nombre para encontrar el nombre base
    n = str(nombre).upper()
    n = re.sub(r'\b\d+(?:[.,]\d+)?\s*(?:KG|GR|G|L|ML)\b.*$', '', n)
    return n.strip()

def main():
    print("--- INICIANDO ASISTENTE DE NUTRICION IA ---")
    LIMITE = 2000
    productos = get_productos_sin_composicion(limite=LIMITE)
    
    if not productos:
        print("No se encontraron productos pendientes de procesar.")
        return
        
    print(f"Procesando {len(productos)} productos...\n")
    
    # 1. Cargar cache de composiciones existentes
    cache_composiciones = {}
    try:
        print("Cargando caché de composiciones existentes para no duplicar...")
        res_comp = db.table("productos").select("nombre, composicion").not_.is_("composicion", "null").execute()
        for row in res_comp.data:
            nb = limpiar_nombre(row['nombre'])
            if nb:
                cache_composiciones[nb] = row['composicion']
        print(f"Caché cargada: {len(cache_composiciones)} productos base encontrados.\n")
    except Exception as e:
        print("Aviso: No se pudo cargar la caché previa:", e)
    
    exitos = 0
    fallos = 0
    
    for p in productos:
        print(f"Analizando: {p['nombre']} (Marca: {p.get('marca', 'N/A')})")
        
        nombre_base = limpiar_nombre(p['nombre'])
        
        # Verificar si ya tenemos esta composición en caché (ahorro de API)
        if nombre_base in cache_composiciones:
            print(f"[CACHE] Copiando composición idéntica de otro peso/tamaño ({nombre_base}).")
            if actualizar_composicion(p['id'], cache_composiciones[nombre_base]):
                print("[OK] Copia guardada exitosamente.\n")
                exitos += 1
            else:
                print("[ERROR] Error al guardar la copia en base de datos.\n")
                fallos += 1
            continue
            
        composicion_html = generar_composicion(p)
        
        if composicion_html:
            if actualizar_composicion(p['id'], composicion_html):
                print("[OK] Composicion guardada exitosamente.\n")
                cache_composiciones[nombre_base] = composicion_html # Guardar en caché para los siguientes
                exitos += 1
            else:
                print("[ERROR] Error al guardar en base de datos.\n")
                fallos += 1
        else:
            print("[ATENCION] La IA no encontro datos seguros para este producto.\n")
            fallos += 1
            
        # Pequeña pausa para no saturar la API
        time.sleep(2)
        
    print(f"--- RESUMEN FINAL ---")
    print(f"Composiciones creadas/copiadas: {exitos}")
    print(f"No encontrados / Errores: {fallos}")
    print(f"Si quieres procesar más, vuelve a ejecutar el script o aumenta el LIMITE en el código.")

if __name__ == "__main__":
    main()
