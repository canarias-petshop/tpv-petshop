import os
import toml
from supabase import create_client

try:
    with open(".streamlit/secrets.toml", "r") as f:
        secrets = toml.load(f)
    url = secrets["url"]
    key = secrets["key"]
except Exception as e:
    import tomllib
    with open(".streamlit/secrets.toml", "rb") as f:
        secrets = tomllib.load(f)
    url = secrets["url"]
    key = secrets["key"]

client = create_client(url, key)

print("Buscando en ventas_historial de ~52.38...")
res_ventas = client.table("ventas_historial").select("*").eq("total", 52.38).execute()
for v in res_ventas.data:
    print(f"Venta ID: {v['id']}, Cliente: {v.get('cliente_fidel') or v.get('cliente_deuda')}, Fecha: {v.get('created_at')}, Metodo: {v.get('metodos_pago')}, Estado: {v.get('estado')}")

print("\nBuscando clientes con deuda_pendiente ~ 52.38...")
res_cli = client.table("clientes").select("id, nombre_dueno, deuda_pendiente").eq("deuda_pendiente", 52.38).execute()
for c in res_cli.data:
    print(f"Cliente ID: {c['id']}, Nombre: {c['nombre_dueno']}, Deuda: {c['deuda_pendiente']}")
    
print("\nBuscando encargos de clientes...")
res_enc = client.table("encargos_clientes").select("id, nombre_cliente, notas").execute()
for e in res_enc.data:
    if "52" in str(e):
        print(f"Encargo: {e['id']} - {e.get('nombre_cliente')}")
