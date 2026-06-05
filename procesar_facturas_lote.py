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

CARPETA_ENTRADA = os.path.join(os.getcwd(), "Fotos_Facturas_Entrada")
CARPETA_PROCESADAS = os.path.join(os.getcwd(), "Facturas_Digitales")

CARPETA_ERRORES = os.path.join(CARPETA_ENTRADA, "Errores")

for carpeta in [CARPETA_ENTRADA, CARPETA_PROCESADAS, CARPETA_ERRORES]:
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)

# --- INICIALIZACIÓN DE SUPABASE Y GEMINI ---
def init_clients():
    print("🔌 Conectando con Supabase y Gemini...")
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
        raise Exception("No se encontró gemini_api_key en secrets.toml")
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
    archivos = [f for f in os.listdir(CARPETA_ENTRADA) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    
    if not archivos:
        print(f"🤷‍♂️ No hay imágenes en la carpeta '{CARPETA_ENTRADA}'. Pon tus facturas ahí y vuelve a ejecutar.")
        return

    print(f"🚀 Se han encontrado {len(archivos)} facturas para procesar.\n")
    
    prompt = """
    Eres un contable experto. Extrae los datos de esta imagen de factura y devuélvelos ESTRICTAMENTE en este formato JSON, sin texto adicional ni markdown:
    {
      "numero_factura": "12345",
      "fecha_factura": "YYYY-MM-DD",
      "nombre_proveedor": "Nombre de la Empresa",
      "articulos": [
        {
          "descripcion": "Nombre del articulo",
          "codigo_referencia_o_barras": "12345678",
          "cantidad": 1,
          "precio_base": 12.50,
          "igic_porcentaje": 7.0,
          "descuento_porcentaje": 0.0,
          "precio_pvp": 15.50
        }
      ]
    }
    Si no encuentras un dato o IGIC, pon 0 o déjalo vacío ("").
    """
    
    modelo = genai.GenerativeModel('gemini-1.5-flash')

    for archivo in archivos:
        ruta_archivo = os.path.join(CARPETA_ENTRADA, archivo)
        print(f"📄 Procesando: {archivo} ...")
        
        try:
            # 1. Leer con Gemini
            img = Image.open(ruta_archivo)
            response = modelo.generate_content([prompt, img])
            
            res_text = response.text.strip()
            if res_text.startswith("```json"): res_text = res_text[7:]
            elif res_text.startswith("```"): res_text = res_text[3:]
            if res_text.endswith("```"): res_text = res_text[:-3]
            
            datos_ia = json.loads(res_text.strip())
            
            # 2. Gestionar Proveedor (Crear si no existe)
            nombre_prov = datos_ia.get("nombre_proveedor", "Proveedor Desconocido").strip()
            res_prov = client.table("proveedores").select("id").ilike("nombre_empresa", f"%{nombre_prov}%").execute()
            
            if res_prov.data:
                prov_id = res_prov.data[0]['id']
            else:
                print(f"   ➕ Creando nuevo proveedor: {nombre_prov}")
                res_new_prov = client.table("proveedores").insert({"nombre_empresa": nombre_prov, "cif": ""}).execute()
                prov_id = res_new_prov.data[0]['id']

            # 3. Gestionar Artículos y Calcular Total
            productos_compra = []
            total_compra = 0.0
            
            for art in datos_ia.get("articulos", []):
                desc = art.get("descripcion", "Artículo desconocido")
                cant = int(parse_float_ia(art.get("cantidad", 1)) or 1)
                p_base = parse_float_ia(art.get("precio_base", 0.0))
                igic = parse_float_ia(art.get("igic_porcentaje", 0.0))
                desc_linea = parse_float_ia(art.get("descuento_porcentaje", 0.0))
                pvp_ia = parse_float_ia(art.get("precio_pvp", 0.0))
                ref_barras = art.get("codigo_referencia_o_barras", "")

                # Buscar si el artículo ya existe en Inventario
                res_prod = client.table("productos").select("id, sku, stock_actual, precio_pvp").ilike("nombre", f"%{desc.strip()}%").execute()
                
                if res_prod.data:
                    # EL ARTÍCULO EXISTE
                    item = res_prod.data[0]
                    prod_id = item['id']
                    sku_final = item['sku']
                    
                    # NO SUMAMOS STOCK AQUÍ (Se guarda como Borrador para validación manual)
                    # nuevo_stock = (item['stock_actual'] or 0) + cant
                    # pvp_final = pvp_ia if pvp_ia > 0 else float(item.get('precio_pvp', 0.0))
                    # client.table("productos").update({"stock_actual": nuevo_stock, "precio_base": p_base, "precio_pvp": pvp_final}).eq("id", prod_id).execute()
                    
                    # VINCULAR A ESTE PROVEEDOR (Para Auto-Distribuidor / Smart Restock)
                    res_link = client.table("productos_proveedores").select("id").eq("producto_id", prod_id).eq("proveedor_id", prov_id).execute()
                    if not res_link.data:
                        print(f"   🔗 Vinculando artículo existente '{desc}' al proveedor '{nombre_prov}'.")
                        client.table("productos_proveedores").insert({"producto_id": prod_id, "proveedor_id": prov_id, "precio_coste": p_base}).execute()
                    else:
                        client.table("productos_proveedores").update({"precio_coste": p_base}).eq("producto_id", prod_id).eq("proveedor_id", prov_id).execute()
                else:
                    # EL ARTÍCULO ES NUEVO (Crear)
                    print(f"   ✨ Creando nuevo artículo en inventario: {desc}")
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
                productos_compra.append({"id": str(prod_id), "Código": sku_final, "Descripción": desc, "Cantidad": cant, "Base Ud": p_base, "IGIC %": igic, "Desc %": desc_linea, "PVP (€)": pvp_ia})
                
                # Sumar al total de la factura
                base_neta = (p_base * cant) * (1 - desc_linea / 100)
                total_compra += base_neta * (1 + igic / 100)

            # 4. Registrar en Contabilidad (Tabla compras)
            num_fac = datos_ia.get("numero_factura", "S/N")
            fecha_fac = datos_ia.get("fecha_factura", str(datetime.now().date()))
            
            client.table("compras").insert({
                "proveedor_id": prov_id, "total": round(total_compra, 2), "estado": "Borrador",
                "tipo": f"Factura: {num_fac}", "fecha_vencimiento": fecha_fac, "productos": productos_compra,
                "pagado": 0.0, "pendiente": round(total_compra, 2)
            }).execute()

            # 5. Mover a Mis Facturas Digitales organizado por Año / Mes
            año_act = str(datetime.now().year)
            mes_act = f"{datetime.now().month:02d}"
            carpeta_final = os.path.join(CARPETA_PROCESADAS, año_act, mes_act)
            if not os.path.exists(carpeta_final): os.makedirs(carpeta_final)
            
            nombre_nuevo = f"{nombre_prov.replace(' ', '_').replace('/', '-')}_{num_fac.replace('/', '-')}_{int(time.time())}.jpg"
            ruta_final = os.path.join(carpeta_final, nombre_nuevo)
            shutil.move(ruta_archivo, ruta_final)
            
            print(f"   ✅ Guardada y foto enviada a: {carpeta_final}\n")
            
        except Exception as e:
            print(f"   ❌ Error al procesar {archivo}: {e}")
            shutil.move(ruta_archivo, os.path.join(CARPETA_ERRORES, archivo))

if __name__ == "__main__":
    procesar_lote()