import toml
import json
import traceback
from supabase import create_client, Client

secrets = toml.load(".streamlit/secrets.toml")
url = secrets["url"].strip('"').strip("'")
key = secrets["key"].strip('"').strip("'")
supabase: Client = create_client(url, key)

output_lines = ["# 🛡️ Servicios Recuperados del Historial\n", "Aquí tienes la lista de los servicios que he podido rescatar escaneando la base de datos de citas e historial de ventas.\n"]

print("--- RECUPERANDO DESDE CITAS ---")
try:
    res_citas = supabase.table("citas").select("servicio").execute()
    servicios_citas = set()
    if res_citas.data:
        for c in res_citas.data:
            nombre = c.get('servicio')
            if nombre:
                servicios_citas.add(nombre.strip().capitalize())
        output_lines.append("## 📅 Encontrados en la tabla de Citas:")
        for s in sorted(list(servicios_citas)):
            output_lines.append(f"- {s}")
    else:
        output_lines.append("## 📅 Encontrados en la tabla de Citas:\nNo hay datos.")
except Exception as e:
    print(f"Error leyendo citas: {e}")

print("\n--- RECUPERANDO DESDE HISTORIAL DE VENTAS ---")
try:
    res_ventas = supabase.table("ventas_historial").select("*").order("id", desc=True).limit(100).execute()
    servicios_tickets = {}
    
    if res_ventas.data:
        # print("Columnas:", res_ventas.data[0].keys())
        for v in res_ventas.data:
            # Check common names for details: 'detalles', 'ticket', 'productos', 'items'
            info = v.get('detalles') or v.get('ticket') or v.get('productos') or v.get('items')
            if not info: continue
            
            if isinstance(info, str):
                try:
                    info = json.loads(info)
                except:
                    continue
            if isinstance(info, dict):
                items = info.get('items', [])
            elif isinstance(info, list):
                items = info
            else:
                continue
                
            for item in items:
                nombre = item.get('nombre', '')
                if not nombre: continue
                n_up = nombre.upper()
                
                # Excluir los piensos conocidos
                if 'ATP' not in n_up and 'OWNAT' not in n_up and 'AMANOVA' not in n_up and 'PIENSO' not in n_up and 'SACO' not in n_up:
                    precio = item.get('precio_unitario', item.get('precio', item.get('precio_pvp', 0)))
                    servicios_tickets[nombre.strip().capitalize()] = precio
                    
        output_lines.append("\n## 🧾 Encontrados en el Historial de Tickets (Ventas):")
        output_lines.append("*(Se excluyen los piensos registrados. Es posible que haya accesorios además de servicios)*")
        for k, v in sorted(servicios_tickets.items()):
            output_lines.append(f"- **{k}**: {v} €")
    else:
        output_lines.append("\n## 🧾 Encontrados en el Historial de Tickets:\nNo hay datos de tickets.")
except Exception as e:
    print(f"Error leyendo ventas: {e}")
    traceback.print_exc()

with open("servicios_recuperados_temp.md", "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))
    
print("Archivo generado.")
