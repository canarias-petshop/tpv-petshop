import sys

with open(r'd:\clon vs mode\tpv-petshop\crm.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out_utils = [
    'import streamlit as st\n',
    'import pandas as pd\n',
    'import time\n',
    'from datetime import date\n\n'
]

out_crm = []
in_funcs = False

for i, line in enumerate(lines):
    # Start extracting at calcular_edad
    if 'def calcular_edad(fecha_str):' in line and not in_funcs:
        in_funcs = True
        out_crm.append('        from utils_ficha import calcular_edad, get_pref, strip_pref, calcular_duracion_media, mostrar_ficha_clinica\n')
        # We also need to rewrite the signature of mostrar_ficha_clinica
        
    if in_funcs:
        if 'st.markdown("---")' in line.replace(' ', ''): # wait, the exact line is `st.markdown("---")` or similar
            if i + 1 < len(lines) and '#### 🚫 Historial de Cancelaciones' in lines[i+1]:
                # We have reached the end of the extraction!
                in_funcs = False
                out_crm.append('            st.markdown("---")\n') 
                continue
                
        # Unindent and append to utils_ficha
        if line.startswith('        '):
            modified_line = line[8:]
            if 'def mostrar_ficha_clinica(m_id, m_nombre, m_data, prefix):' in modified_line:
                modified_line = 'def mostrar_ficha_clinica(m_id, m_nombre, m_data, prefix, client, servicios_lista, empleados_lista, precios_servicios):\n'
            out_utils.append(modified_line)
        elif line == '\n':
            out_utils.append(line)
        else:
            out_utils.append(line)
    else:
        # We need to change the call to mostrar_ficha_clinica in crm.py
        if 'mostrar_ficha_clinica(m_id_sel, masc_info.get("nombre", ""), masc_info, "crm_search")' in line:
            line = line.replace('mostrar_ficha_clinica(m_id_sel, masc_info.get("nombre", ""), masc_info, "crm_search")', 'mostrar_ficha_clinica(m_id_sel, masc_info.get("nombre", ""), masc_info, "crm_search", client, servicios_lista, empleados_lista, precios_servicios)')
        elif 'mostrar_ficha_clinica(masc_id, masc_nombre, res_masc.data[0], f"crm_fam_{masc_id}")' in line:
            line = line.replace('mostrar_ficha_clinica(masc_id, masc_nombre, res_masc.data[0], f"crm_fam_{masc_id}")', 'mostrar_ficha_clinica(masc_id, masc_nombre, res_masc.data[0], f"crm_fam_{masc_id}", client, servicios_lista, empleados_lista, precios_servicios)')
            
        out_crm.append(line)

with open(r'd:\clon vs mode\tpv-petshop\utils_ficha.py', 'w', encoding='utf-8') as f:
    f.writelines(out_utils)

with open(r'd:\clon vs mode\tpv-petshop\crm.py', 'w', encoding='utf-8') as f:
    f.writelines(out_crm)
