import os
import re
import difflib
from supabase import create_client, Client
from dotenv import load_dotenv

# 1. Cargar variables de entorno
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ ERROR: Faltan credenciales de Supabase en el archivo .env")
    exit()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================================================================
# ⚙️ CONFIGURACIÓN DE LA IMPORTACIÓN
# ==============================================================================
NOMBRE_PROVEEDOR = "FEEDCAN distribuciones"
MARCA_SKU = "KONG"
PREFIJO_SKU = "KO" # Para generar KO-001, KO-002...
IGIC_COMPRA = 3.0
UMBRAL_SIMILITUD = 0.85 # 85% de similitud para considerarlo duplicado

TEXTO_CATALOGO = """
# PEGA AQUÍ EL TEXTO DEL EXCEL/PDF.
# Ejemplo: 
# KONG CLASSIC MEDIANO 12.50
# 03558503214 KONG EXTREME LARGE 18.00
"""

def limpiar_precio(texto_precio):
    try:
        limpio = texto_precio.replace('€', '').replace('$', '').strip()
        limpio = limpio.replace(',', '.')
        return float(limpio)
    except:
        return 0.0

def importar_catalogo_kong():
    print("🔍 Conectando con Supabase para obtener catálogo actual...")
    
    # 1. Obtener ID del proveedor
    res_prov = supabase.table("proveedores").select("id, nombre_empresa").eq("nombre_empresa", NOMBRE_PROVEEDOR).execute()
    if not res_prov.data:
        print(f"❌ ERROR: No se encontró el proveedor '{NOMBRE_PROVEEDOR}' en la base de datos.")
        return
    proveedor_id = res_prov.data[0]['id']
    
    # 2. Descargar todos los productos existentes para comparar
    res_prod = supabase.table("productos").select("id, nombre, codigo_barras, sku").execute()
    productos_existentes = res_prod.data if res_prod.data else []
    print(f"✅ Se han descargado {len(productos_existentes)} productos para la comprobación anti-duplicados.")
    
    # 2.1 Calcular el siguiente número correlativo para el SKU (ej. KO-001)
    max_num = 0
    for p in productos_existentes:
        sku_actual = p.get('sku', '')
        if sku_actual and sku_actual.startswith(f"{PREFIJO_SKU}-"):
            try:
                num = int(sku_actual.split('-')[1])
                if num > max_num: max_num = num
            except: pass
    siguiente_num_sku = max_num + 1
    
    lineas = TEXTO_CATALOGO.strip().split('\n')
    productos_a_insertar = []
    
    print("\n🚀 Iniciando lectura del catálogo...")
    for linea in lineas:
        linea = linea.strip()
        if not linea or linea.startswith('#'): continue
        
        partes = linea.split()
        if len(partes) < 2: continue
        
        # 3. Lógica Inversa: Extraer PVP (Último elemento)
        pvp_texto = partes[-1]
        if not re.search(r'\d', pvp_texto): continue # Si el último no es un número, saltar
        
        precio_pvp = limpiar_precio(pvp_texto)
        precio_base = precio_pvp / 2 # <-- LA REGLA DE ORO: EL COSTE ES LA MITAD
        
        # 4. Buscar Código de Barras (EAN)
        codigo_barras = ""
        resto_partes = partes[:-1]
        
        posible_ean = resto_partes[0]
        if len(posible_ean) >= 8 and posible_ean.isdigit():
            codigo_barras = posible_ean
            nombre_lista = resto_partes[1:]
        else:
            nombre_lista = resto_partes
            
        nombre = " ".join(nombre_lista).upper().strip()
        
        # 5. MOTOR DE INTELIGENCIA ANTI-DUPLICADOS (Fuzzy Matching)
        es_duplicado = False
        motivo_duplicado = ""
        
        for p_bd in productos_existentes:
            # Check 1: Por EAN (Si tiene)
            if codigo_barras and p_bd.get('codigo_barras') == codigo_barras:
                es_duplicado = True; motivo_duplicado = f"EAN coincidente con '{p_bd.get('nombre')}'"
                break
            
            # Check 2: Por Similitud de Nombre (Fuzzy Match)
            similitud = difflib.SequenceMatcher(None, nombre.lower(), p_bd.get('nombre', '').lower()).ratio()
            if similitud >= UMBRAL_SIMILITUD:
                es_duplicado = True; motivo_duplicado = f"Nombre muy similar ({similitud*100:.1f}%) a '{p_bd.get('nombre')}'"
                break
                
        if es_duplicado:
            print(f"⏭️ SALTEADO: {nombre} -> {motivo_duplicado}")
        else:
            sku_generado = f"{PREFIJO_SKU}-{siguiente_num_sku:03d}"
            print(f"✅ ACEPTADO: {nombre} | SKU: {sku_generado} | EAN: {codigo_barras} | Coste: {precio_base:.2f}€ | PVP: {precio_pvp:.2f}€")
            siguiente_num_sku += 1
            # Aquí iría el código de inserción a Supabase (supabase.table("productos").insert(...))
            # Por seguridad en la prueba, de momento solo lo imprimimos por pantalla.
            
    print("\n🏁 Análisis completado. Esperando confirmación para insertar en base de datos.")

if __name__ == "__main__":
    importar_catalogo_kong()