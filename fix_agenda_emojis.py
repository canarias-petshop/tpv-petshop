with open('agenda.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re
# Replace the elif conditions with exactly what is in the radio box
content = re.sub(r'elif seccion_agenda == "[^"]+Vista Diaria":', 'elif seccion_agenda == "🕒 Vista Diaria":', content)
content = re.sub(r'elif seccion_agenda == "[^"]+Vista Semanal":', 'elif seccion_agenda == "🗓️ Vista Semanal":', content)
content = re.sub(r'elif seccion_agenda == "[^"]+Vista Mensual":', 'elif seccion_agenda == "📅 Vista Mensual":', content)
content = re.sub(r'elif seccion_agenda == "[^"]+Recordatorios":', 'elif seccion_agenda == "🔔 Recordatorios":', content)
content = re.sub(r'elif seccion_agenda == "[^"]+Cancelaciones":', 'elif seccion_agenda == "🚫 Cancelaciones":', content)
content = re.sub(r'elif seccion_agenda == "[^"]+Sin Historial":', 'elif seccion_agenda == "🚨 Sin Historial":', content)

with open('agenda.py', 'w', encoding='utf-8') as f:
    f.write(content)
