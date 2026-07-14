with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace padding-top: 10px with padding-top: 2px
content = content.replace("padding-top: 10px;", "padding-top: 2px;")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
