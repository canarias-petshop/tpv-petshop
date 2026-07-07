import json
with open('amanova_db_dump.json', encoding='utf-8') as f:
    db = json.load(f)
for p in db:
    if 'caja' in p.get('nombre', '').lower():
        print(f"{p.get('sku')} - {p.get('nombre')} - {p.get('precio_pvp')}")
