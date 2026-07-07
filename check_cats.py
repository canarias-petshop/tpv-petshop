import os
import toml
from postgrest import SyncPostgrestClient

secrets_path = os.path.join('.streamlit', 'secrets.toml')
with open(secrets_path, 'r') as f: secrets = toml.load(f)

raw_url = secrets.get('url', '').strip().strip('"').strip("'").rstrip('/')
api_url = raw_url if raw_url.endswith('/rest/v1') else f'{raw_url}/rest/v1'
api_key = secrets.get('key', '').strip().strip('"').strip("'")
client = SyncPostgrestClient(api_url, headers={'apikey': api_key, 'Authorization': f'Bearer {api_key}'})

res = client.table('productos').select('nombre, familia, subcategoria').execute()
data = res.data

snacks = 0
humedos = 0
secos = 0
for p in data:
    cat = (p.get('subcategoria') or p.get('familia') or '').lower()
    if 'snack' in cat: snacks += 1
    elif 'húmedo' in cat or 'humedo' in cat or 'pouch' in cat or 'lata' in cat: humedos += 1
    elif 'pienso' in cat or 'seco' in cat or 'seca' in cat: secos += 1

print(f'Total productos: {len(data)}')
print(f'Snacks: {snacks}')
print(f'Humedos: {humedos}')
print(f'Secos: {secos}')
