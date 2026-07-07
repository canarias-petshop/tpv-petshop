import json
import os
import csv

def format_weight(w):
    w_str = str(w).replace(',', '.').strip()
    try:
        val = float(w_str)
        # If it's something like 0.4, convert to 400 g
        if val < 1.0:
            return f"{int(val * 1000)} g"
        elif val == int(val):
            return f"{int(val)} kg"
        else:
            return f"{val} kg"
    except:
        return w_str

with open("lenda_matched_strict.json", "r", encoding="utf-8") as f:
    products = json.load(f)

# Generar CSV (separado por punto y coma para Excel en español)
with open("lenda_revision_catalogo.csv", "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.writer(f, delimiter=';')
    writer.writerow([
        "Nombre Original PDF",
        "Gama Extraída",
        "Peso Sugerido Web",
        "PVP",
        "Ruta de Foto Asignada por el Bot",
        "Foto Correcta? (SI/NO)",
        "Ruta CORRECTA de Foto (si la anterior es NO)"
    ])
    
    for p in products:
        name_pdf = p["name"]
        gama = p.get("source", "")
        if gama == "Tienda": gama = "Lenda"
        elif gama == "GrainFree": gama = "Grain Free"
        elif gama == "Vet": gama = "Veterinaria"
        
        # Formatear peso: 0,4 -> 400 g
        # Si dice "200 ml" o algo en el PDF original, lo mantenemos si no es float
        peso_raw = p["weight"]
        peso_sugerido = format_weight(peso_raw)
        
        # Especial para aceites (Lenda Atún de 200 ml) si por alguna razón el peso quedó como "200 ml" o "0.2"
        # The script should naturally format 0.2 as 200 g, we might need to adjust manually if it's oil.
        if "ml" in str(peso_raw).lower():
            peso_sugerido = peso_raw
        elif "atún" in name_pdf.lower() and "aceite" in name_pdf.lower():
            peso_sugerido = str(peso_raw) + " ml"
            
        pvp = str(p["pvp"]).replace(".", ",") if p["pvp"] else ""
        foto = p.get("best_image", "SIN FOTO")
        
        writer.writerow([
            name_pdf,
            gama,
            peso_sugerido,
            pvp,
            foto,
            "",
            ""
        ])

print("CSV lenda_revision_catalogo.csv generado con éxito.")
