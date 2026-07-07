import json
with open('amanova_db_dump.json', encoding='utf-8') as f:
    db = json.load(f)
with open('sku_check.txt', 'w', encoding='utf-8') as out:
    for p in db:
        if p.get('sku') == 'S-AMT50PO1A':
            out.write(f"{p['sku']} | {p['nombre']} | {p['precio_pvp']}\n")
