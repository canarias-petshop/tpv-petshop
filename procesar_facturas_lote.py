import os
import time
import json
import toml
import pandas as pd
from datetime import datetime
from PIL import Image
import shutil
import google.generativeai as genai
from postgrest import SyncPostgrestClient
import difflib

# --- INICIALIZACIÓN DE SUPABASE Y GEMINI ---
def init_clients():
    print("Conectando con Supabase y Gemini...")
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    with open(secrets_path, "r") as f: secrets = toml.load(f)
    
    # Supabase
    raw_url = secrets.get('url', '').strip().strip('"').strip("'").rstrip('/')
    api_url = raw_url if raw_url.endswith('/rest/v1') else f"{raw_url}/rest/v1"
    api_key = secrets.get('key', '').strip().strip('"').strip("'")
    client = SyncPostgrestClient(api_url, headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"})
    
    # Gemini
    gemini_key = secrets.get("gemini_api_key", "").strip()
    if not gemini_key:
        raise Exception("No se encontro gemini_api_key en secrets.toml")
    genai.configure(api_key=gemini_key)
    
    return client

def generar_sku(client, nombre_articulo):
    letras = ''.join([c for c in nombre_articulo if c.isalpha()]).upper()
    prefijo = letras[:2] if len(letras) >= 2 else (letras + "X" if letras else "XX")
    res_sku = client.table("productos").select("sku").like("sku", f"{prefijo}-%").execute()
    max_num = 0
    if res_sku.data:
        for s in res_sku.data:
            try:
                num = int(s['sku'].split("-")[1])
                if num > max_num: max_num = num
            except: pass
    return f"{prefijo}-{max_num + 1:03d}"

def parse_float_ia(val):
    try:
        if isinstance(val, str): val = val.replace(',', '.')
        return float(val)
    except: return 0.0

def procesar_lote():
    client = init_clients()
    ROOT_DIR = r"C:\Users\truji\OneDrive\Documentos\ANIMALARIUM\TPV ANIMALARIUM\CONTABILIDAD\FACTURAS DIGITALES"
    
    archivos_a_procesar = []
    for root, dirs, files in os.walk(ROOT_DIR):
        # Ignorar carpetas que ya son destinos finales
        if "Procesadas" in root or "Errores" in root:
            continue
            
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.pdf')):
                archivos_a_procesar.append(os.path.join(root, file))
    
    if not archivos_a_procesar:
        print(f"No hay facturas pendientes en '{ROOT_DIR}'.")
        return

    print(f"Se han encontrado {len(archivos_a_procesar)} facturas para procesar en total.\n")
    
    # Fetch current providers
    res_prov = client.table("proveedores").select("nombre_empresa").execute()
    provs_list = [p['nombre_empresa'] for p in res_prov.data] if res_prov.data else []
    provs_str = ", ".join(provs_list) if provs_list else "Ninguno"
    
    prompt = f"""
    Eres un contable experto. Extrae los datos de esta factura y devuelvelos ESTRICTAMENTE en este formato JSON, sin texto adicional ni markdown:
    {{
      "numero_factura": "12345",
      "fecha_factura": "YYYY-MM-DD",
      "nombre_proveedor": "OBLIGATORIO: busca el nombre del emisor de la factura en esta lista de proveedores registrados: [{provs_str}]. Si encuentras uno con nombre igual o muy parecido (aunque tenga puntos, comas o abreviaciones distintas), devuelve EXACTAMENTE el nombre de la lista, sin modificar ni una letra. Solo si el proveedor es completamente nuevo y no tiene ninguna similitud con ninguno de la lista, devuelve el nombre tal como aparece en la factura.",
      "articulos": [
        {{
          "descripcion": "Nombre del articulo",
          "codigo_referencia_o_barras": "12345678",
          "cantidad": 1,
          "precio_base": 12.50,
          "igic_porcentaje": 7.0,
          "descuento_porcentaje": 0.0,
          "precio_pvp": 15.50
        }}
      ]
    }}
    Si no encuentras un dato o IGIC, pon 0 o dejalo vacio ("").
    """
    
    modelo = genai.GenerativeModel('gemini-2.5-flash')

    print("Cargando catálogo completo para búsqueda inteligente...")
    res_all = client.table("productos").select("id, sku, nombre").execute()
    todos_productos = res_all.data if res_all.data else []
    nombres_productos = {p['nombre']: p for p in todos_productos}

    for ruta_archivo in archivos_a_procesar:
        carpeta_origen = os.path.dirname(ruta_archivo)
        archivo = os.path.basename(ruta_archivo)
        
        carpeta_procesadas = os.path.join(carpeta_origen, "Procesadas")
        carpeta_errores = os.path.join(carpeta_origen, "Errores")
        if not os.path.exists(carpeta_procesadas): os.makedirs(carpeta_procesadas)
        if not os.path.exists(carpeta_errores): os.makedirs(carpeta_errores)
        
        print(f"Procesando: {ruta_archivo} ...")
        
        try:
            # 1. Leer con Gemini
            if archivo.lower().endswith('.pdf'):
                with open(ruta_archivo, "rb") as f_pdf:
                    payload = [prompt, {"mime_type": "application/pdf", "data": f_pdf.read()}]
            else:
                img = Image.open(ruta_archivo)
                payload = [prompt, img]
                
            intentos = 0
            while intentos < 2:
                try:
                    response = modelo.generate_content(payload)
                    break
                except Exception as ex:
                    if "429" in str(ex):
                        print("   Rate limit excedido (429). Esperando 10 segundos...")
                        time.sleep(10)
                        intentos += 1
                    else:
                        raise ex
            if intentos == 2:
                raise Exception("Se excedieron los reintentos por limite de cuota.")
            
            res_text = response.text.strip()
            if res_text.startswith("```json"): res_text = res_text[7:]
            elif res_text.startswith("```"): res_text = res_text[3:]
            if res_text.endswith("```"): res_text = res_text[:-3]
            
            datos_ia = json.loads(res_text.strip())
            
            # 2. Gestionar Proveedor — búsqueda en 2 niveles para evitar duplicados
            nombre_prov = datos_ia.get("nombre_proveedor", "Proveedor Desconocido").strip()
            
            # Cargar todos los proveedores actuales para comparación
            todos_provs = client.table("proveedores").select("id, nombre_empresa").execute().data or []
            
            prov_id = None
            
            # NIVEL 1: Búsqueda exacta/parcial por texto (ilike)
            res_prov = client.table("proveedores").select("id, nombre_empresa").ilike("nombre_empresa", f"%{nombre_prov}%").execute()
            if res_prov.data:
                prov_id = res_prov.data[0]['id']
                print(f"   Proveedor encontrado (ilike): {res_prov.data[0]['nombre_empresa']}")
            
            # NIVEL 2: Si no se encontró, buscar por similitud fuzzy (>=80%)
            if not prov_id:
                nombres_existentes = [p['nombre_empresa'] for p in todos_provs]
                coincidencias = difflib.get_close_matches(nombre_prov, nombres_existentes, n=1, cutoff=0.80)
                if coincidencias:
                    nombre_match = coincidencias[0]
                    prov_match = next(p for p in todos_provs if p['nombre_empresa'] == nombre_match)
                    prov_id = prov_match['id']
                    print(f"   Proveedor encontrado (fuzzy 80%): '{nombre_prov}' -> '{nombre_match}'")
            
            # NIVEL 3: Si tampoco hay coincidencia, crear nuevo proveedor
            if not prov_id:
                print(f"   Creando nuevo proveedor: {nombre_prov}")
                res_new_prov = client.table("proveedores").insert({"nombre_empresa": nombre_prov, "cif": ""}).execute()
                prov_id = res_new_prov.data[0]['id']

            # 3. Gestionar Articulos y Calcular Total
            productos_compra = []
            total_compra = 0.0
            
            for art in datos_ia.get("articulos", []):
                desc = art.get("descripcion", "Articulo desconocido")
                
                # REGLA: Convertir "Amv" a "AMANOVA" para no duplicar en DB
                if desc.upper().startswith("AMV "):
                    desc = "AMANOVA" + desc[3:]

                cant = int(parse_float_ia(art.get("cantidad", 1)) or 1)
                p_base = parse_float_ia(art.get("precio_base", 0.0))
                igic = parse_float_ia(art.get("igic_porcentaje", 0.0))
                desc_linea = parse_float_ia(art.get("descuento_porcentaje", 0.0))
                pvp_ia = parse_float_ia(art.get("precio_pvp", 0.0))
                ref_barras = art.get("codigo_referencia_o_barras", "")

                # Buscar si el articulo ya existe en Inventario (Alta Semejanza 88%)
                coincidencias = difflib.get_close_matches(desc, nombres_productos.keys(), n=1, cutoff=0.88)
                
                if coincidencias:
                    # EL ARTICULO EXISTE
                    item = nombres_productos[coincidencias[0]]
                    prod_id = item['id']
                    sku_final = item['sku']
                    
                    # VINCULAR A ESTE PROVEEDOR
                    res_link = client.table("productos_proveedores").select("id").eq("producto_id", prod_id).eq("proveedor_id", prov_id).execute()
                    if not res_link.data:
                        print(f"   Vinculando articulo '{coincidencias[0]}' al proveedor '{nombre_prov}'.")
                        client.table("productos_proveedores").insert({"producto_id": prod_id, "proveedor_id": prov_id, "precio_coste": p_base}).execute()
                    else:
                        client.table("productos_proveedores").update({"precio_coste": p_base}).eq("producto_id", prod_id).eq("proveedor_id", prov_id).execute()
                else:
                    # EL ARTICULO ES NUEVO (Crear)
                    print(f"   Creando nuevo articulo: {desc}")
                    sku_final = generar_sku(client, desc)
                    res_new = client.table("productos").insert({
                        "nombre": desc, "sku": sku_final, "codigo_barras": ref_barras,
                        "precio_base": p_base, "igic_tipo": igic, "precio_pvp": pvp_ia,
                        "categoria": "Producto", "stock_actual": 0, "stock_minimo": 2, "cantidad_reponer": 5
                    }).execute()
                    prod_id = res_new.data[0]['id']
                    
                    # Vincular al proveedor
                    client.table("productos_proveedores").insert({"producto_id": prod_id, "proveedor_id": prov_id, "precio_coste": p_base}).execute()

                # Preparar JSON para la compra
                productos_compra.append({"id": str(prod_id), "Codigo": sku_final, "Descripcion": desc, "Cantidad": cant, "Base Ud": p_base, "IGIC %": igic, "Desc %": desc_linea, "PVP (e)": pvp_ia})
                
                # Sumar al total de la factura
                base_neta = (p_base * cant) * (1 - desc_linea / 100)
                total_compra += base_neta * (1 + igic / 100)

            # 4. Registrar en Contabilidad (Tabla compras)
            num_fac = datos_ia.get("numero_factura", "S/N")
            fecha_fac = datos_ia.get("fecha_factura", str(datetime.now().date()))
            
            res_existente = client.table("compras").select("id, estado, productos, total, pendiente").eq("proveedor_id", prov_id).eq("tipo", f"Factura: {num_fac}").execute()
            
            if res_existente.data and num_fac != "S/N":
                fac_existente = res_existente.data[0]
                if fac_existente['estado'] == 'Borrador':
                    prods_antiguos = fac_existente.get('productos', [])
                    if not isinstance(prods_antiguos, list): prods_antiguos = []
                    prods_antiguos.extend(productos_compra)
                    nuevo_total = float(fac_existente['total']) + total_compra
                    nuevo_pendiente = float(fac_existente['pendiente']) + total_compra
                    client.table("compras").update({"productos": prods_antiguos, "total": round(nuevo_total, 2), "pendiente": round(nuevo_pendiente, 2), "fecha_factura": fecha_fac}).eq("id", fac_existente['id']).execute()
                    print(f"   Factura '{num_fac}' existente. Pagina fusionada.")
                else:
                    print(f"   Factura '{num_fac}' ya esta validada. Saltando.")
            else:
                client.table("compras").insert({
                    "proveedor_id": prov_id, "total": round(total_compra, 2), "estado": "Borrador",
                    "tipo": f"Factura: {num_fac}", "fecha_vencimiento": fecha_fac, "fecha_factura": fecha_fac, "productos": productos_compra,
                    "pagado": 0.0, "pendiente": round(total_compra, 2)
                }).execute()
                print("   Procesada y guardada como nuevo Borrador.")

            # 5. Mover a Procesadas
            ruta_final_leida = os.path.join(carpeta_procesadas, archivo)
            shutil.move(ruta_archivo, ruta_final_leida)
            
        except Exception as e:
            print(f"   Error al procesar {archivo}: {e}")
            shutil.move(ruta_archivo, os.path.join(carpeta_errores, archivo))

if __name__ == "__main__":
    procesar_lote()