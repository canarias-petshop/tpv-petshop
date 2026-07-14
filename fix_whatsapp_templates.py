with open('agenda.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_msg1 = 'msg = f"Hola buenos 🐾🐾 días desde Animalarium le recordamos la cita de peluquería {texto_mascotas_horas}\\nDía: {fecha_str_wa}\\nDirección de recogida: {direccion_alguno}\\nConfirmanos contestando a este mensaje, de lo contrario la cita será cancelada.\\nSi desea cambiar la cita no dude en comunicarlo.🐾😊❤️🐶🚗"'
new_msg1 = 'msg = f"¡Hola, buenos días! ☀️ Desde Animalarium 🐾 le recordamos la cita de peluquería {texto_mascotas_horas}\\n🗓️ Día: {fecha_str_wa}\\n📍 Dirección de recogida: {direccion_alguno}\\n\\n⚠️ Confírmanos contestando a este mensaje, de lo contrario la cita será cancelada.\\n🔄 Si deseas cambiar la cita, no dudes en comunicarlo.\\n\\n¡Te esperamos! 🐶❤️😊🚗"'

old_msg2 = 'msg = f"Hola buenos 🐾🐾 días desde Animalarium le recordamos la cita de peluquería {texto_mascotas_horas}\\nDía: {fecha_str_wa}\\nConfirmanos contestando a este mensaje, de lo contrario la cita será cancelada.\\nSi desea cambiar la cita no dude en comunicarlo.🐾😊❤️🐶"'
new_msg2 = 'msg = f"¡Hola, buenos días! ☀️ Desde Animalarium 🐾 le recordamos la cita de peluquería {texto_mascotas_horas}\\n🗓️ Día: {fecha_str_wa}\\n\\n⚠️ Confírmanos contestando a este mensaje, de lo contrario la cita será cancelada.\\n🔄 Si deseas cambiar la cita, no dudes en comunicarlo.\\n\\n¡Te esperamos! 🐶❤️😊"'

content = content.replace(old_msg1, new_msg1)
content = content.replace(old_msg2, new_msg2)

with open('agenda.py', 'w', encoding='utf-8') as f:
    f.write(content)
