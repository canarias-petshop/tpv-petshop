import os
from supabase import create_client

url = "https://zpzhsmyyyfxqbjjiuana.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwemhzbXl5eWZ4cWJqaml1YW5hIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjEwMzAxNiwiZXhwIjoyMDkxNjc5MDE2fQ.9gNW0JdUf_xnbfEuRnO3WoMPASXQjfqRBkyCjPE0DCY"
supabase = create_client(url, key)

res = supabase.table("productos").select("id, nombre, marca").execute()
amv_productos = []
for p in res.data:
    if "AMV" in (p.get("marca") or "").upper() or "AMV" in (p.get("nombre") or "").upper():
        amv_productos.append(p)

print(f"Encontrados {len(amv_productos)} productos con AMV")
for p in amv_productos:
    print(p)
