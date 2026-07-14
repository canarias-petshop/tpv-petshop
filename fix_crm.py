import re

with open('crm.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add toast handler at the top of render_pestana_crm
content = content.replace(
    "def render_pestana_crm(client):",
    "def render_pestana_crm(client):\n    if 'crm_toast' in st.session_state:\n        st.toast(st.session_state.pop('crm_toast'), icon=\"✅\")"
)

# 2. Optimize Clientes
cli_search = """                    for _, row in ed_cli_clean.iterrows():
                        if pd.notna(row['id']):
                            datos_update = {"""

cli_replace = """                    for _, row in ed_cli_clean.iterrows():
                        if pd.notna(row['id']):
                            orig_match = df_cli_vista[df_cli_vista['id'] == row['id']]
                            if not orig_match.empty:
                                orig_row = orig_match.iloc[0]
                                cambiado = False
                                for col in ['nombre_dueno', 'telefono', 'email', 'fecha_nacimiento', 'direccion', 'RGPD', 'Puntos', 'Domicilio']:
                                    if col in row and col in orig_row:
                                        if str(row.get(col, '')).strip() != str(orig_row.get(col, '')).strip():
                                            cambiado = True
                                            break
                                if not cambiado:
                                    continue
                                    
                            datos_update = {"""
content = content.replace(cli_search, cli_replace)

content = content.replace(
    'st.success("Directorio de clientes actualizado."); time.sleep(0.5); st.rerun()',
    'st.session_state["crm_toast"] = "Directorio de clientes actualizado."; time.sleep(0.5); st.rerun()'
)

# 3. Optimize Mascotas
masc_search = """                    for _, row in ed_m_clean.iterrows():
                        if pd.notna(row['id']):
                            nueva_fecha_m = str(row['fecha_nacimiento']) if pd.notna(row['fecha_nacimiento']) else ""
                            orig_match = df_m_vista[df_m_vista['id'] == row['id']]
                            if not orig_match.empty:
                                orig_ru = orig_match.iloc[0]"""

masc_replace = """                    for _, row in ed_m_clean.iterrows():
                        if pd.notna(row['id']):
                            nueva_fecha_m = str(row['fecha_nacimiento']) if pd.notna(row['fecha_nacimiento']) else ""
                            orig_match = df_m_vista[df_m_vista['id'] == row['id']]
                            if not orig_match.empty:
                                orig_ru = orig_match.iloc[0]
                                cambiado = False
                                for col in ['nombre', 'especie', 'sexo', 'raza', 'peso', 'fecha_nacimiento', 'observaciones', 'Dueño', 'Edad']:
                                    if col in row and col in orig_ru:
                                        if str(row.get(col, '')).strip() != str(orig_ru.get(col, '')).strip():
                                            cambiado = True
                                            break
                                if not cambiado:
                                    continue
"""
content = content.replace(masc_search, masc_replace)

content = content.replace(
    'st.success("Directorio de mascotas actualizado."); time.sleep(0.5); st.rerun()',
    'st.session_state["crm_toast"] = "Directorio de mascotas actualizado."; time.sleep(0.5); st.rerun()'
)

with open('crm.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
