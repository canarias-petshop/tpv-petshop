import toml
import json
from supabase import create_client, Client

secrets = toml.load(".streamlit/secrets.toml")
url = secrets["url"].strip('"').strip("'")
key = secrets["key"].strip('"').strip("'")
supabase: Client = create_client(url, key)

print("--- RECUPERACIÓN DE SERVICIOS DESDE CITAS ---")
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
                    servicios_citas[nombre] = coste
        print(f"Encontrados {len(servicios_citas)} servicios únicos en citas:")
        for k, v in servicios_citas.items():
            print(f"  - {k}: {v} €")
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
                    if 'ATP' not in nombre_upper and 'OWNAT' not in nombre_upper and 'AMANOVA' not in nombre_upper and 'PIENSO' not in nombre_upper:
                        if nombre_upper not in servicios_tickets:
                            servicios_tickets[nombre_upper] = d.get('precio_unitario', 0)
        print(f"\nEncontrados {len(servicios_tickets)} posibles servicios/productos genéricos en tickets:")
        for k, v in servicios_tickets.items():
            print(f"  - {k}: {v} €")
    else:
        print("No hay datos en la tabla ventas_tickets.")
except Exception as e:
    print(f"Error leyendo tickets: {e}")
