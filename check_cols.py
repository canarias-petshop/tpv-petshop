import urllib.request, json, os

with open('.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
    secrets = f.read()
    
url = ''
key = ''
for line in secrets.split('\n'):
    if 'SUPABASE_URL' in line:
        url = line.split('=')[1].strip().strip('"').strip("'")
    if 'SUPABASE_KEY' in line:
        key = line.split('=')[1].strip().strip('"').strip("'")

req = urllib.request.Request(f'{url}/rest/v1/productos?limit=1', headers={'apikey': key, 'Authorization': f'Bearer {key}'})
response = urllib.request.urlopen(req)
data = json.loads(response.read())
if data:
    print('Columns in productos:', list(data[0].keys()))
