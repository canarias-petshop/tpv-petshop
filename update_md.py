import os

with open('RESUMEN_MAESTRO_ACTUALIZADO.md', 'r', encoding='utf-8') as f:
    content = f.read()

new_content = """
- **Herramienta de Desempaquetado (TPV)**:
  - Creada la utilidad Traspaso de Cajas a Unidades en el inventario. Permite romper stock de un producto "Master/Caja" y sumarlo automáticamente al producto individual, calculando unidades internas.
- **Promociones Automáticas Web**:
  - Implementado descuento automático del 10% en productos que se venden por cajas enteras (pouches, latas).
  - La web muestra ahora una etiqueta (badge rojo) de "-10% DTO" y el precio original tachado tanto en el catálogo como en el carrito.
- **Flujo de Pago (Checkout) Optimizado para WhatsApp**:
  - Se eliminó la necesidad de pagar por transferencia inmediata.
  - El sistema asume que la tienda usará "Paygold / Enlace de Pago" (Dojo, CaixaBank, Cajasur) tras confirmar el stock. 
  - La pasarela ofrece opciones amigables: "Tarjeta (Enlace por WhatsApp)", "Bizum (Confirmación por WhatsApp)" y "Pago al recoger".
- **Histórico de Pedidos en Perfil de Usuario**:
  - Añadida la sección "Histórico de Pedidos" en Mi Cuenta, donde los usuarios web pueden revisar sus compras online y ver si están Pendientes o Entregados, conectando directamente con encargos_clientes.
- **Corrección Estructural Checkout (Bugfixes)**:
  - Se arregló un fallo silencioso de Supabase donde entas_historial rechazaba inserciones por columnas obsoletas (cliente_fidel).
  - Se modificó la API de Checkout para que TODOS los pedidos web caigan en "Pedidos Web" (encargos_clientes) y, si son a domicilio, se clonen inteligentemente a pedidos_domicilio para el repartidor.

"""

if "Corrección Estructural Checkout" not in content:
    lines = content.split('---')
    lines[0] = lines[0] + new_content
    final = '---'.join(lines)
    with open('RESUMEN_MAESTRO_ACTUALIZADO.md', 'w', encoding='utf-8') as f:
        f.write(final)
        print("Updated successfully")
else:
    print("Already updated")

