with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the start and end of the block
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if line.startswith("if num_alertas > 0:"):
        start_idx = i
    if start_idx != -1 and "st.markdown(\"---\")" in line:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    # Extract the block
    block = lines[start_idx:end_idx+1]
    
    # Remove the block from original position
    del lines[start_idx:end_idx+1]
    
    # Remove the st.markdown("---") which is the last element of the block
    if "st.markdown(\"---\")" in block[-1]:
        block.pop()

    # Find the insertion point: before '# --- DEFINICIÓN DINÁMICA'
    insert_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("# --- DEFINICI"):
            insert_idx = i
            break
            
    if insert_idx != -1:
        # Let's insert the block right before the definition of tabs.
        # But we also need to ensure there is an empty line before and after.
        lines = lines[:insert_idx] + ["\n"] + block + ["\n"] + lines[insert_idx:]
        print("Moved successfully!")
        
with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
