import os
from supabase import create_client

url = "https://zpzhsmyyyfxqbjjiuana.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwemhzbXl5eWZ4cWJqaml1YW5hIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjEwMzAxNiwiZXhwIjoyMDkxNjc5MDE2fQ.9gNW0JdUf_xnbfEuRnO3WoMPASXQjfqRBkyCjPE0DCY"
supabase = create_client(url, key)

res = supabase.table("productos").select("id, marca").ilike("marca", "Lenda").execute()

count = 0
for p in res.data:
    if p["marca"] != "LENDA":
        supabase.table("productos").update({"marca": "LENDA"}).eq("id", p["id"]).execute()
        count += 1

print(f"Marcas Lenda actualizadas a mayúsculas: {count}")
