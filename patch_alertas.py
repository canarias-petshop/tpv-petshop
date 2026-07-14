import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove old bottom alerts
web_pattern_safe = r"# --- ALERTA GLOBAL DE PEDIDOS WEB ---.*?# --- ALERTA GLOBAL DE PEDIDOS MANUALES A PROVEEDORES ---.*?(?=# --- DEFINICI.N DIN.MICA DE PESTA.AS SEG.N ROL ---)"
web_prov_logic = re.search(web_pattern_safe, content, re.DOTALL)
if web_prov_logic:
    content = content.replace(web_prov_logic.group(0), "")

# 2. Extract the 'if bloqueo:' block
bloqueo_match = re.search(r"(bloqueo = comprobar_fichajes_pendientes\(\)\n\s+)(if bloqueo:.*?)(?=\n\s+st\.markdown\(\"---\"\))", content, re.DOTALL)

if bloqueo_match:
    old_block = bloqueo_match.group(2)
    
    # Let's add 4 spaces to every line of old_block
    lines = old_block.split('\n')
    indented_old_block = "\n".join(["    " + line if line.strip() != "" else "" for line in lines])
    
    new_block = f"""    # --- LÓGICA DE ALERTAS INTEGRADAS ---
    # 1. Pedidos Web
    pedidos_web = []
    try:
        res_pedidos = client.table("encargos_clientes").select("id").eq("origen", "Web").eq("estado", "Recibido").execute()
        pedidos_web = res_pedidos.data if res_pedidos.data else []
    except: pass
    
    # 2. Proveedores
    alertas_provs = []
    try:
        from proveedores import fetch_proveedores, get_alertas_manuales
        res_provs = fetch_proveedores(client)
        if res_provs.data:
            alertas_provs = get_alertas_manuales(res_provs.data)["urgentes"]
    except: pass
    
    num_alertas = (1 if bloqueo else 0) + (1 if pedidos_web else 0) + (1 if alertas_provs else 0)
    
    if num_alertas > 0:
        with st.expander(f"🔔 CENTRO DE NOTIFICACIONES: Tienes {{num_alertas}} alerta(s) pendiente(s) (Despliega para ver y solucionar)", expanded=False):
{indented_old_block}
            if pedidos_web:
                st.error(f"🔴 **¡ATENCIÓN! Tienes {{len(pedidos_web)}} pedido(s) web nuevo(s) sin revisar.** Ve a la pestaña 'Clientes' -> 'Encargos' para gestionarlo(s).")
            if alertas_provs:
                nombres_provs = ", ".join([a['proveedor'] for a in alertas_provs])
                st.warning(f"⚠️ **ALERTA DE PROVEEDORES:** Tienes {{len(alertas_provs)}} pedido(s) urgente(s) pendiente(s) de realizar ({{nombres_provs}}). Ve a 'Proveedores y Pedidos' para registrarlo(s).")"""

    content = content.replace(bloqueo_match.group(2), new_block)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched app.py")
