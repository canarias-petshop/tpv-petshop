import pandas as pd
import toml
from postgrest import SyncPostgrestClient
import os
from datetime import datetime

def init_supabase():
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    with open(secrets_path, "r") as f: secrets = toml.load(f)
    raw_url = secrets.get('url', '').strip().strip('"').strip("'").rstrip('/')
    api_url = raw_url if raw_url.endswith('/rest/v1') else f"{raw_url}/rest/v1"
    api_key = secrets.get('key', '').strip().strip('"').strip("'")
    return SyncPostgrestClient(api_url, headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"})

client = init_supabase()
fecha_hoy = datetime.now().strftime("%Y_%m_%d")
hora_hoy = datetime.now().strftime("%H_%M")

# Crear la carpeta principal de backups si no existe
carpeta_maestra = "Backups_Datos_Nube"
if not os.path.exists(carpeta_maestra):
    os.makedirs(carpeta_maestra)

# Crear la subcarpeta con la fecha de hoy
carpeta_hoy = os.path.join(carpeta_maestra, f"Backup_{fecha_hoy}_{hora_hoy}")
os.makedirs(carpeta_hoy)

print(f"📥 Iniciando DESCARGA TOTAL de datos en la carpeta: {carpeta_hoy} ...\n")

# ==========================================
# 1. DESCARGAR CLIENTES Y MASCOTAS
# ==========================================
print("⏳ Descargando Clientes y Mascotas...")
res_clientes = client.table("clientes").select("nombre_dueno, telefono, email, puntos, mascotas(nombre, especie, raza, fecha_nacimiento, observaciones)").execute()
if res_clientes.data:
    filas_cli = []
    for c in res_clientes.data:
        mascotas = c.get('mascotas', [])
        if not mascotas:
            filas_cli.append({"Dueño": c.get('nombre_dueno', ''), "Teléfono": c.get('telefono', ''), "Puntos VIP": c.get('puntos', 0), "Mascota": "", "Especie": "", "Raza": ""})
        else:
            for m in mascotas:
                filas_cli.append({"Dueño": c.get('nombre_dueno', ''), "Teléfono": c.get('telefono', ''), "Puntos VIP": c.get('puntos', 0), "Mascota": m.get('nombre', ''), "Especie": m.get('especie', ''), "Raza": m.get('raza', '')})
    pd.DataFrame(filas_cli).to_excel(os.path.join(carpeta_hoy, "1_Clientes_Mascotas.xlsx"), index=False)
    print("  ✅ Clientes guardados.")

# ==========================================
# 2. DESCARGAR VENTAS (TICKETS DEL TPV)
# ==========================================
print("⏳ Descargando Historial de Ventas...")
res_ventas = client.table("ventas_historial").select("id, created_at, total, pagado, pendiente, metodo_pago, estado, cliente_vip_nombre").execute()
if res_ventas.data:
    df_v = pd.DataFrame(res_ventas.data)
    df_v['Fecha'] = pd.to_datetime(df_v['created_at']).dt.strftime('%d/%m/%Y %H:%M')
    cols_v = ['id', 'Fecha', 'total', 'pagado', 'pendiente', 'metodo_pago', 'estado', 'cliente_vip_nombre']
    df_v = df_v[[c for c in cols_v if c in df_v.columns]]
    df_v.to_excel(os.path.join(carpeta_hoy, "2_Historial_Ventas_TPV.xlsx"), index=False)
    print("  ✅ Ventas guardadas.")

# ==========================================
# 3. DESCARGAR COMPRAS Y GASTOS (CONTABILIDAD)
# ==========================================
print("⏳ Descargando Compras, Gastos y Facturas recibidas...")
res_compras = client.table("compras").select("id, created_at, tipo, total, estado, proveedores(nombre_empresa)").execute()
if res_compras.data:
    df_c = pd.DataFrame(res_compras.data)
    df_c['Fecha'] = pd.to_datetime(df_c['created_at']).dt.strftime('%d/%m/%Y %H:%M')
    df_c['Proveedor'] = df_c['proveedores'].apply(lambda x: x.get('nombre_empresa', '') if isinstance(x, dict) else '')
    cols_c = ['id', 'Fecha', 'tipo', 'total', 'estado', 'Proveedor']
    df_c = df_c[[c for c in cols_c if c in df_c.columns]]
    df_c.to_excel(os.path.join(carpeta_hoy, "3_Compras_y_Gastos.xlsx"), index=False)
    print("  ✅ Compras guardadas.")

# ==========================================
# 4. DESCARGAR FACTURAS EMITIDAS
# ==========================================
print("⏳ Descargando Facturas Emitidas a clientes...")
res_fac = client.table("facturas").select("numero_factura, created_at, total_neto, total_igic, total_final, forma_pago, clientes(nombre_dueno)").execute()
if res_fac.data:
    df_f = pd.DataFrame(res_fac.data)
    df_f['Fecha'] = pd.to_datetime(df_f['created_at']).dt.strftime('%d/%m/%Y %H:%M')
    df_f['Cliente'] = df_f['clientes'].apply(lambda x: x.get('nombre_dueno', '') if isinstance(x, dict) else '')
    cols_f = ['numero_factura', 'Fecha', 'Cliente', 'total_neto', 'total_igic', 'total_final', 'forma_pago']
    df_f = df_f[[c for c in cols_f if c in df_f.columns]]
    df_f.to_excel(os.path.join(carpeta_hoy, "4_Facturas_Emitidas.xlsx"), index=False)
    print("  ✅ Facturas guardadas.")

print("\n🎉 ¡COPIA DE SEGURIDAD TOTAL COMPLETADA CON ÉXITO!")
print(f"Revisa la carpeta: {carpeta_hoy}")