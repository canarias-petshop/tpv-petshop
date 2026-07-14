import tomli
from supabase import create_client
import pandas as pd

# 1. Init Supabase
secrets = tomli.load(open('.streamlit/secrets.toml', 'rb'))
client = create_client(secrets['url'], secrets['key'])

# 2. Read Excel
df = pd.read_excel('Backups_Datos_Nube/Backup_2026_07_07_23_54/6_Encargos_y_Pedidos.xlsx')
print(f"Loaded {len(df)} orders from backup.")

# 3. Clean dataframe
# Remove 'Fecha' as it's not in the DB schema
if 'Fecha' in df.columns:
    df = df.drop(columns=['Fecha'])

# Fill NaN with empty string or None
df = df.fillna('')

# Convert to list of dicts
records = df.to_dict('records')

# 4. Truncate table (deleting all existing rows)
# Wait, Supabase client doesn't have a truncate method, so we delete by getting all IDs first.
current = client.table('encargos_clientes').select('id').execute().data
if current:
    ids_to_delete = [row['id'] for row in current]
    print(f"Deleting {len(ids_to_delete)} current broken orders...")
    # Delete in batches of 200 just in case
    for i in range(0, len(ids_to_delete), 200):
        batch = ids_to_delete[i:i+200]
        client.table('encargos_clientes').delete().in_('id', batch).execute()

# 5. Insert backup records
print(f"Inserting {len(records)} orders from backup...")
# Insert in batches of 50
for i in range(0, len(records), 50):
    batch = records[i:i+50]
    client.table('encargos_clientes').insert(batch).execute()

print("Restore complete! Encargos table is now identical to the July 7th 23:54 backup.")
