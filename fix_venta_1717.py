import os
import tomllib
from supabase import create_client

secrets = tomllib.load(open('.streamlit/secrets.toml', 'rb'))
client = create_client(secrets['url'], secrets['key'])

venta_id = 1717
print(f"Cancelando y devolviendo venta #{venta_id}...")

# 1. Marcar como devolución
client.table('ventas_historial').update({
    "estado": "Devolucion",
    "motivo_devolucion": "Venta web de prueba cancelada / error"
}).eq("id", venta_id).execute()
print("Venta marcada como Devolucion. La deuda ha desaparecido.")

# 2. Restaurar stock
prod_id = "5e29f94e-9c84-42d9-868f-c0bda79fc5c8"
res_prod = client.table("productos").select("stock_actual").eq("id", prod_id).execute()
if res_prod.data:
    stock_actual = res_prod.data[0].get("stock_actual", 0)
    nuevo_stock = stock_actual + 1
    client.table("productos").update({"stock_actual": nuevo_stock}).eq("id", prod_id).execute()
    print(f"Stock restaurado para el producto. Nuevo stock: {nuevo_stock}")

print("Proceso finalizado.")
