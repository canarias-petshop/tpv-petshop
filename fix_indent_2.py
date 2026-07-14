with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_alertas = False

for i, line in enumerate(lines):
    if "LÓGICA DE ALERTAS INTEGRADAS" in line:
        in_alertas = True
    
    if in_alertas:
        # Stop dedenting when we hit the end of the expander block
        if "st.markdown(\"---\")" in line:
            in_alertas = False
            new_lines.append(line)
            continue
        
        # Remove 4 spaces from the beginning of the line
        if line.startswith("    "):
            new_lines.append(line[4:])
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
