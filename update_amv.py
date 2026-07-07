import os
from supabase import create_client

url = "https://zpzhsmyyyfxqbjjiuana.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwemhzbXl5eWZ4cWJqaml1YW5hIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjEwMzAxNiwiZXhwIjoyMDkxNjc5MDE2fQ.9gNW0JdUf_xnbfEuRnO3WoMPASXQjfqRBkyCjPE0DCY"
supabase = create_client(url, key)

res = supabase.table("productos").select("id, nombre, marca").execute()
updated_count = 0
for p in res.data:
    nombre_original = p.get("nombre") or ""
    # Only replace at the beginning or as an isolated word
    if nombre_original.startswith("Amv "):
        nuevo_nombre = nombre_original.replace("Amv ", "AMANOVA ", 1)
        supabase.table("productos").update({"nombre": nuevo_nombre}).eq("id", p["id"]).execute()
        updated_count += 1
        print(f"Actualizado: {nombre_original} -> {nuevo_nombre}")
    elif nombre_original.startswith("AMV "):
        nuevo_nombre = nombre_original.replace("AMV ", "AMANOVA ", 1)
        supabase.table("productos").update({"nombre": nuevo_nombre}).eq("id", p["id"]).execute()
        updated_count += 1
        print(f"Actualizado: {nombre_original} -> {nuevo_nombre}")

print(f"Total de productos actualizados: {updated_count}")
