import pandas as pd
import sys
import os

excel_path = r"C:\Users\truji\OneDrive\Documentos\ANIMALARIUM\Hojas para pedidos\PIENSO PERROS-LeónTrujillo.xlsx"

try:
    xl = pd.ExcelFile(excel_path)
    df = pd.read_excel(excel_path, sheet_name=xl.sheet_names[0])
    
    # Col 0: nombre
    # Col 1: peso
    # Col 3: precio_base
    # Col 5: precio_pvp
    
    # We will iterate through rows and print any row that has a string in Col 0
    print("RowIdx | Nombre | Peso | Base | PVP")
    for idx, row in df.iterrows():
        nombre = str(row.iloc[0]).strip()
        if "ATLANTIC" in nombre.upper():
            peso = str(row.iloc[1]).strip()
            base = str(row.iloc[3]).strip()
            pvp = str(row.iloc[5]).strip()
            print(f"{idx} | {nombre} | {peso} | {base} | {pvp}")

except Exception as e:
    print(f"Error: {e}")
