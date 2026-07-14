with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("font-size: 1.1rem;'>", "font-size: 1.5rem;'>")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
