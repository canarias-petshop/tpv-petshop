import toml
from postgrest import SyncPostgrestClient
import os

def init_supabase():
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    with open(secrets_path, "r") as f: secrets = toml.load(f)
    raw_url = secrets.get('url', '').strip().strip('"').strip("'").rstrip('/')
    api_url = raw_url if raw_url.endswith('/rest/v1') else f"{raw_url}/rest/v1"
    api_key = secrets.get('key', '').strip().strip('"').strip("'")
    return SyncPostgrestClient(api_url, headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"})

client = init_supabase()
print("🔌 Conectando a la base de datos...")

# Hemos extraído tus gastos directamente de la tabla que proporcionaste
gastos_a_importar = [
    {"concepto": "Seguros Sociales (SS SS EMPL)", "categoria": "Personal y autónomos (Nóminas, SS...)", "importe": 796.79},
    {"concepto": "Nómina - Sueldo L", "categoria": "Personal y autónomos (Nóminas, SS...)", "importe": 618.71},
    {"concepto": "Nómina - Sueldo Ale", "categoria": "Personal y autónomos (Nóminas, SS...)", "importe": 1144.36},
    {"concepto": "Cuota Autónomos", "categoria": "Personal y autónomos (Nóminas, SS...)", "importe": 600.00},
    {"concepto": "Gestoría / Asesor", "categoria": "Servicios exteriores y profesionales", "importe": 53.50},
    {"concepto": "Préstamo ICO", "categoria": "Suministros y Operativos (Alquiler, Luz, Agua, Teléfono, Seguros, Préstamos...)", "importe": 221.39},
    {"concepto": "Tarjeta de Crédito", "categoria": "Suministros y Operativos (Alquiler, Luz, Agua, Teléfono, Seguros, Préstamos...)", "importe": 234.15},
    {"concepto": "Tarjeta Ventajon", "categoria": "Suministros y Operativos (Alquiler, Luz, Agua, Teléfono, Seguros, Préstamos...)", "importe": 163.33},
    {"concepto": "Préstamo Personal", "categoria": "Suministros y Operativos (Alquiler, Luz, Agua, Teléfono, Seguros, Préstamos...)", "importe": 133.63},
    {"concepto": "Alquiler Tienda", "categoria": "Suministros y Operativos (Alquiler, Luz, Agua, Teléfono, Seguros, Préstamos...)", "importe": 673.20},
    {"concepto": "Agua", "categoria": "Suministros y Operativos (Alquiler, Luz, Agua, Teléfono, Seguros, Préstamos...)", "importe": 40.00},
    {"concepto": "Luz", "categoria": "Suministros y Operativos (Alquiler, Luz, Agua, Teléfono, Seguros, Préstamos...)", "importe": 100.00},
    {"concepto": "Seguro", "categoria": "Suministros y Operativos (Alquiler, Luz, Agua, Teléfono, Seguros, Préstamos...)", "importe": 21.26},
    {"concepto": "Ozono", "categoria": "Suministros y Operativos (Alquiler, Luz, Agua, Teléfono, Seguros, Préstamos...)", "importe": 33.33},
    {"concepto": "Software (Holded)", "categoria": "Suministros y Operativos (Alquiler, Luz, Agua, Teléfono, Seguros, Préstamos...)", "importe": 40.00},
    {"concepto": "Mantenimiento Datáfono", "categoria": "Suministros y Operativos (Alquiler, Luz, Agua, Teléfono, Seguros, Préstamos...)", "importe": 17.21},
    {"concepto": "Cuota Cuenta Bancaria (ACT)", "categoria": "Suministros y Operativos (Alquiler, Luz, Agua, Teléfono, Seguros, Préstamos...)", "importe": 6.00},
    {"concepto": "Teléfono / Internet", "categoria": "Suministros y Operativos (Alquiler, Luz, Agua, Teléfono, Seguros, Préstamos...)", "importe": 250.00},
    {"concepto": "Garaje", "categoria": "Suministros y Operativos (Alquiler, Luz, Agua, Teléfono, Seguros, Préstamos...)", "importe": 98.00},
    {"concepto": "Alarma Securitas", "categoria": "Suministros y Operativos (Alquiler, Luz, Agua, Teléfono, Seguros, Préstamos...)", "importe": 59.76},
    {"concepto": "Publicidad", "categoria": "Servicios exteriores y profesionales", "importe": 120.00},
    {"concepto": "Plan Pago Impuestos", "categoria": "Impuestos y Tasas (IGIC, IRPF, tributos...)", "importe": 112.57},
]

print("🚀 Insertando 22 gastos fijos...")
for g in gastos_a_importar:
    client.table("gastos_recurrentes").insert({
        "concepto": g["concepto"], "categoria": g["categoria"], 
        "importe_estimado": g["importe"], "dia_cargo": 1,  # Por defecto el día 1, luego lo editas en la app
        "frecuencia": "Mensual", "activo": True
    }).execute()
    print(f"  ✅ Añadido: {g['concepto']} ({g['importe']}€)")

print("\n🎉 ¡Todos los gastos importados correctamente!")