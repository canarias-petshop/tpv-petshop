import pandas as pd
import json
import sys

excel_path = r"C:\Users\truji\OneDrive\Documentos\ANIMALARIUM\Hojas para pedidos\PIENSO PERROS-LeónTrujillo.xlsx"

try:
    xl = pd.ExcelFile(excel_path)
    print("Sheets:", xl.sheet_names)
    
    df = pd.read_excel(excel_path, sheet_name=xl.sheet_names[0])
    df = df.dropna(how='all').dropna(axis=1, how='all')
    print(df.head(50).to_string())
        
except Exception as e:
    print(f"Error: {e}")
