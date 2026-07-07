import pandas as pd
import toml
import math
from supabase import create_client, Client

secrets = toml.load(".streamlit/secrets.toml")
url = secrets["url"].strip('"').strip("'")
key = secrets["key"].strip('"').strip("'")
supabase: Client = create_client(url, key)

backup_path = r"D:\clon vs mode\tpv-petshop\Backups_Datos_Nube\Backup_2026_06_29_01_20\5_Catalogo_y_Servicios.xlsx"
df = pd.read_excel(backup_path, sheet_name=None)
print("Hojas en el Excel:", list(df.keys()))

if "Sheet1" in df:
    prod_df = df["Sheet1"]
    print("Marcas únicas:", prod_df['marca'].dropna().unique())
    genericos = prod_df[prod_df['marca'].str.contains('Genérico', case=False, na=False) | prod_df['marca'].str.contains('Generico', case=False, na=False)]
    print(f"Encontrados {len(genericos)} servicios Genéricos en el backup.")
    
    # Restoring them
    success = 0
    for idx, row in genericos.iterrows():
        # Clean NaN values to None for Supabase JSON
        row_dict = {}
        for k, v in row.to_dict().items():
            if k == 'id': continue # let DB generate new ID or keep old? Old ID might be referenced in tickets.
            if pd.isna(v) or v is pd.NaT:
                row_dict[k] = None
            else:
                row_dict[k] = v
                
        # If we must preserve the exact ID for relational integrity (e.g., historial ventas)
        if 'id' in row:
            row_dict['id'] = row['id']
            
        try:
            supabase.table("productos").insert(row_dict).execute()
            success += 1
        except Exception as e:
            print(f"Error insertando: {e}")
            
    print(f"Restaurados {success}/{len(genericos)} servicios.")
else:
    print("No se encontró la hoja Productos")
