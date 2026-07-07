import os
from supabase import create_client

url = "https://zpzhsmyyyfxqbjjiuana.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwemhzbXl5eWZ4cWJqaml1YW5hIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjEwMzAxNiwiZXhwIjoyMDkxNjc5MDE2fQ.9gNW0JdUf_xnbfEuRnO3WoMPASXQjfqRBkyCjPE0DCY"
supabase = create_client(url, key)

res = supabase.table("productos").select("*").execute()
productos = res.data

updated = 0

for p in productos:
    updates = {}
    
    # 1. Mascota
    mascota = p.get("mascota")
    if mascota:
        m_low = mascota.lower()
        if "perro" in m_low:
            updates["mascota"] = "Perro"
        elif "gato" in m_low or "cat" in m_low:
            updates["mascota"] = "Gato"
        elif "roedor" in m_low or "ave" in m_low or "reptil" in m_low or "pez" in m_low:
            updates["mascota"] = None # El usuario solo quiere perros y gatos de momento

    # 2. Familia and Subcategoría
    familia = p.get("familia") or ""
    subcategoria = p.get("subcategoria") or ""
    
    lower_fam = familia.lower()
    lower_sub = subcategoria.lower()
    
    is_food = any(w in lower_fam or w in lower_sub for w in ["alimento", "alimentación", "pienso", "lata", "pouch", "húmedo", "seco", "snack", "wet", "dry"])
    
    if is_food:
        updates["familia"] = "Alimentación"
        if "seco" in lower_fam or "seco" in lower_sub or "pienso" in lower_sub or "dry" in lower_sub:
            updates["subcategoria"] = "Alimentación seca"
        elif "húmedo" in lower_fam or "humedo" in lower_fam or "húmedo" in lower_sub or "humedo" in lower_sub or "lata" in lower_sub or "pouch" in lower_sub or "wet" in lower_sub:
            updates["subcategoria"] = "Alimentación húmeda"
        elif "snack" in lower_fam or "snack" in lower_sub:
            updates["subcategoria"] = "Snack"
            
    # 3. Tamaño
    tamano = p.get("tamano")
    if tamano:
        t_low = tamano.lower()
        if t_low == "mini" or t_low == "pequeño" or t_low == "mini/pequeño":
            updates["tamano"] = "Mini/Pequeño"
        elif t_low == "todas las razas" or t_low == "todas":
            updates["tamano"] = "Todas las razas"
        elif "grande" in t_low or "maxi" in t_low:
            updates["tamano"] = "Grande"
        elif "mediano" in t_low or "medium" in t_low:
            updates["tamano"] = "Mediano"
            
    # 4. Necesidades Especiales
    necesidad = p.get("necesidad_especial")
    if necesidad:
        n_low = necesidad.lower().strip()
        if "exigente" in n_low:
            updates["necesidad_especial"] = "Paladares exigentes"
        elif "digestivo" in n_low or "sensible" in n_low:
            updates["necesidad_especial"] = "Sensible / digestivo"
        elif "articulacion" in n_low or "articulaciones" in n_low or "mobility" in n_low:
            updates["necesidad_especial"] = "Articulaciones"
        elif "bola de pelo" in n_low or "bolas de pelo" in n_low or "hairball" in n_low:
            updates["necesidad_especial"] = "Bolas de pelo"
        elif "peso" in n_low or "light" in n_low:
            updates["necesidad_especial"] = "Control de peso"
        elif "esterilizado" in n_low or "sterilized" in n_low:
            updates["necesidad_especial"] = "Esterilizado"
        elif "hipoalergénico" in n_low or "hipoalergenico" in n_low or "hypoallergenic" in n_low:
            updates["necesidad_especial"] = "Hipoalergénico"
        elif "urinario" in n_low or "urinary" in n_low:
            updates["necesidad_especial"] = "Urinario"
        elif "renal" in n_low:
            updates["necesidad_especial"] = "Renal"
        elif "dermatológico" in n_low or "dermatologico" in n_low or "derma" in n_low:
            updates["necesidad_especial"] = "Dermatológico"
        elif "hepático" in n_low or "hepatico" in n_low or "hepatic" in n_low:
            updates["necesidad_especial"] = "Hepático"
        elif "blanco" in n_low or "white" in n_low:
            updates["necesidad_especial"] = "Pelo blanco"

    # 5. Marca
    marca = p.get("marca")
    if marca:
        if marca.lower() == "ownat":
            updates["marca"] = "OWNAT"
        elif marca.lower() == "royal canin":
            updates["marca"] = "Royal Canin"

    # Final reconciliation to apply updates
    final_updates = {}
    for k, v in updates.items():
        if p.get(k) != v:
            final_updates[k] = v
            
    if final_updates:
        supabase.table("productos").update(final_updates).eq("id", p["id"]).execute()
        updated += 1

print(f"Total productos corregidos en la base de datos: {updated}")
