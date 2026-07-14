with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_expander = False
for i, line in enumerate(lines):
    if "with st.expander" in line:
        in_expander = True
        continue
    
    if in_expander:
        if "if pedidos_web:" in line:
            in_expander = False
            # Break out, the rest is fine
        else:
            if line.strip() != "":
                # Currently lines inside start with at least 4 spaces if they are 'if bloqueo'
                # Actually, let's just strip them and then see what they should be.
                # It's easier to just add 8 spaces to them, since they were originally indented for 0 spaces ('if bloqueo:') or 4 spaces.
                # Actually, earlier I did `"    " + line`. So 'if bloqueo' has 4 spaces.
                # But it needs 12 spaces. So I will add 8 spaces.
                lines[i] = "        " + line

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
