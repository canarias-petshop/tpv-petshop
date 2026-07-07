import toml
import json
from supabase import create_client, Client

secrets = toml.load(".streamlit/secrets.toml")
url = secrets["url"].strip('"').strip("'")
key = secrets["key"].strip('"').strip("'")
supabase: Client = create_client(url, key)

print("--- REVISIÓN ATLANTIC PET ---")
res_atp = supabase.table("productos").select("sku, nombre, gama, mascota").ilike("marca", "Atlantic Pet").execute()
if res_atp.data:
    print(f"Total Atlantic Pet en BD: {len(res_atp.data)}")
    print("Muestra de 5 productos:")
    for p in res_atp.data[:5]:
        print(f"  - {p['sku']}: {p['nombre']} (Gama: {p['gama']}, Mascota: {p['mascota']})")
else:
    print("No hay productos de Atlantic Pet en la BD.")

print("\n--- RECUPERACIÓN DE SERVICIOS DESDE CITAS ---")
try:
    res_citas = supabase.table("citas").select("tipo_servicio, coste").execute()
    servicios_citas = {}
    if res_citas.data:
        for c in res_citas.data:
            nombre = c.get('tipo_servicio')
            coste = c.get('coste')
            if nombre:
                nombre = nombre.strip().upper()
                if nombre not in servicios_citas:
                    servicios_citas[nombre] = coste
                elif coste and (not servicios_citas[nombre] or coste > servicios_citas[nombre]):
                    # Keep the highest cost found as a reference
                    servicios_citas[nombre] = coste
        print(f"Encontrados {len(servicios_citas)} servicios únicos en citas.")
    else:
        print("No hay datos en la tabla citas.")
except Exception as e:
    print(f"Error leyendo citas: {e}")

print("\n--- RECUPERACIÓN DE SERVICIOS DESDE TICKETS ---")
try:
    res_tickets = supabase.table("ventas_tickets").select("detalles").execute()
    servicios_tickets = {}
    if res_tickets.data:
        for t in res_tickets.data:
            detalles = t.get('detalles', [])
            if isinstance(detalles, str):
                try:
                    detalles = json.loads(detalles)
                except:
                    continue
            for d in detalles:
                nombre = d.get('nombre')
                if nombre:
                    nombre_upper = nombre.strip().upper()
                    # Si no es un producto con SKU de tienda, asumimos que es servicio
                    # O si tiene palabras clave como peluqueria, corte, baño, etc.
                    # Vamos a extraer todos los que no parecen piensos
                    if 'ATP' not in nombre_upper and 'OWNAT' not in nombre_upper and 'AMANOVA' not in nombre_upper:
                        if nombre_upper not in servicios_tickets:
                            servicios_tickets[nombre_upper] = d.get('precio_unitario', 0)
        print(f"Encontrados potenciales {len(servicios_tickets)} items en tickets (podrían incluir otros productos sin marca).")
    else:
        print("No hay datos en la tabla ventas_tickets.")
except Exception as e:
    print(f"Error leyendo tickets: {e}")
