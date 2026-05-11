# 👑 MANUAL DE ADMINISTRADOR: ANIMALARIUM TPV y ERP
*Guía completa de los módulos de gestión, contabilidad y gerencia.*

---

## 1. ⏱️ Gestión de Personal (Panel de Administrador)
Como administrador, tienes acceso a la configuración avanzada de tus empleados.

- **Registro de Empleados:** En la parte inferior de la pestaña "Personal", puedes dar de alta a nuevos empleados asignándoles un PIN de 4 dígitos.
- **Asignación de Turnos (Editor Visual):** Ve a "Gestión de Cuadrante (Editable)". Verás un calendario apilado por semanas que funciona como un Excel. Selecciona el rango de fechas (ej. un mes entero), haz doble clic en las celdas para escribir el turno (ej. `09:00 - 17:00` o `Vacaciones`) y pulsa "Guardar Todo el Cuadrante". La Agenda leerá esto y bloqueará las citas cuando no trabajen.
- **Revisión de Horas:** Puedes ver una tabla con los fichajes reales (Entrada y Salida) y las horas totales trabajadas, útil para preparar las nóminas a final de mes.

---

## 2. 📈 Estadísticas y Rendimiento
Panel visual para analizar la salud financiera del negocio en tiempo real.

- **Dashboard Principal:** Muestra el Balance Neto (Ingresos totales menos Gastos registrados).
- **Gráfico de Evolución:** Visualiza la tendencia de las ventas día a día.
- **Top Productos y Servicios:** Descubre qué artículos de la tienda o qué servicios de peluquería generan más ingresos para potenciar sus ventas.

---

## 3. 🚚 Proveedores, Pedidos y Facturación
Control de la relación con tus distribuidores y gestión de stock automático.

- **Gestión de Proveedores:** Registra los comerciales, días de reparto y el **Pedido Mínimo (€)**. Si el proveedor exige un mínimo para no cobrar portes, el sistema te avisará al hacer un borrador.
- **Borradores de Pedido (Smart Restock):** 
  - Desde "Inventario", el sistema te avisa del stock bajo. Pulsando "Auto-distribuir", el sistema reparte esos artículos pendientes a sus respectivos proveedores. **Si un producto tiene varios proveedores, el sistema elegirá automáticamente al que tenga el precio de coste más bajo.**
  - Desde "Proveedores", puedes revisar el borrador y pulsar el botón **"📧 Enviar Pedido"** para generar automáticamente un correo con la lista lista para mandar.
- **Registro de Compras (Albaranes y Facturas):**
  - Ve a **"Facturación y Stock > Registro de Compras"**.
  - Al introducir la factura de un proveedor, el sistema te permite actualizar el Precio de Coste de los productos e incluir descuentos por Pronto Pago.
  - Al "Archivar" esa compra, **el stock del Inventario sube automáticamente**.
- **Pago de Deudas a Proveedores:** En "Pagos Pendientes", puedes saldar facturas atrasadas total o **parcialmente** (ej: pagando solo 50€ de una factura de 100€) descontando el dinero directamente de un Banco o de la Caja Fuerte.
  - En esta sección dispones de un **Calendario Visual** que te muestra qué pagos están vencidos, cuáles vencen esta semana y cuáles en los próximos 30 días.

---

## 4. 📊 Contabilidad y Exportación para Asesoría
Preparación fácil de los impuestos y libros contables.

- **Gastos Puntuales vs Gastos Fijos:** Registra las reparaciones o compras menores en "Gastos Puntuales". Registra el alquiler, luz, nóminas y préstamos en "Gastos Fijos", indicando qué día del mes se cobran.
  - *Truco:* Si un gasto fijo se cobra siempre a final de mes, pon el día **31**. El sistema lo ajustará automáticamente a 28 o 30 según el mes.
- *Nota de Automatización:* Los gastos menores (limpieza, pagos a repartidores en metálico) **los registran las empleadas directamente desde la Caja** al hacer la retirada, enviándose a este panel automáticamente sin que tú tengas que apuntarlos de nuevo.
- **Calendario Predictivo y Alertas:** En la pestaña "Calendario y Alertas", verás dividido lo que tienes que pagar **esta semana** y lo que tienes que pagar **este mes**, junto con un gráfico de esfuerzo económico.
- **Archivo Inteligente:** En la pestaña Facturación -> Archivo, puedes usar el **filtro de categorías** para ver únicamente un tipo de gasto (ej. Solo "Impuestos y Tasas" o "Nóminas").
- **Exportación a Excel (Asesoría):** 
  - Para la asesoría, usa el botón de **"Solo Facturas (IGIC)"**. Te generará un Excel con dos pestañas: Facturas Emitidas y Facturas Recibidas, descartando automáticamente los gastos menores.
  - Puedes generar listados independientes para Tickets sin IVA y para el Cuadro de Gastos Fijos.

---

## 5. 🏦 Bancos y Tesorería
Control estricto de la liquidez en las cuentas de la empresa.

- **Directorio de Cuentas:** Registra tus cuentas (ej. CaixaBank, Caja Siete) con su IBAN.
- **Visualización de Saldo en Vivo:** El saldo de los bancos sube automáticamente cuando los clientes pagan con tarjeta por el TPV, o cuando archivas facturas. El saldo baja al registrar gastos bancarios o pagar proveedores con transferencia.
- **Transferencias Internas:** 
  - Puedes mover dinero entre dos bancos tuyos.
  - **Ingreso de Caja a Banco:** Si la caja fuerte tiene mucho dinero en efectivo, puedes registrar un ingreso en el banco. El sistema descontará el efectivo de la caja y lo sumará a la cuenta bancaria seleccionada, dejando el rastro contable.

---

## 6. 📦 Modificación Avanzada de Inventario
Aunque los empleados pueden vender, la estructura del catálogo recae en la administración.

- **Familias y Subfamilias:** Mantén el catálogo ordenado por categorías (Pienso, Accesorios, Peluquería) para facilitar las estadísticas.
- **Importación Masiva de Catálogos:** Utiliza el script `importador_productos.py` para subir Excels de tus proveedores, añadiendo cientos de productos nuevos de golpe sin duplicar los ya existentes.
- **Modificación Manual de Stock:** Solo usar en caso de robos, mermas o inventario físico anual (ya que las ventas y las devoluciones modifican el stock automáticamente).

---

## 7.  Gestión Avanzada de CRM y Agenda
- **Soporte para Familias:** El CRM ahora permite registrar un Contacto Principal (usado para recordatorios automáticos de WhatsApp) y un Contacto Secundario. El buscador general reconocerá a la familia por cualquiera de los dos teléfonos o nombres.
- **Trazabilidad de Tiempos:** El historial clínico calcula automáticamente la duración de las sesiones en base a las horas de inicio y fin, permitiéndote extraer estadísticas precisas sobre el rendimiento de tus empleados.
- **Directorio Limpio:** La agenda cuenta con ocultación inteligente de citas pasadas para agilizar la carga diaria.

---

## 8. 💾 Copias de Seguridad Automáticas (Backups)
Para garantizar que tus datos nunca se pierdan, el sistema incluye dos herramientas en la carpeta de tu ordenador:
1. **Backup del Código (`crear_backup.bat`):** Al hacerle doble clic, empaqueta todo el programa en un archivo `.zip`. Útil por si cambias de ordenador.
2. **Backup de los Datos (`descargar_todos_los_datos.bat`):** Al hacerle doble clic, se conecta a la nube y te descarga en la carpeta `Backups_Datos_Nube` todo tu directorio de clientes, facturas, compras y tickets de venta en formato Excel en bruto. 
   - *Automatización:* Puedes configurar el "Programador de Tareas" de Windows para que ejecute este archivo todos los días al cierre de forma invisible.

---

## 🔒 9. Consideraciones de Seguridad
1. **Nunca reveles la contraseña/URL de acceso al panel principal (Streamlit Cloud)** a los empleados. 
2. Tus empleados solo deben conocer su propio PIN de 4 dígitos (Contraseña general de acceso a la tablet + su PIN personal de fichaje). No verán ni la pestaña de Contabilidad ni la de Bancos.
3. **Bloqueo Inteligente de Deudas:** Los empleados ya no pueden fiar dinero sin registrar a quién se lo fían, evitando descuadres o "olvidos". Las deudas se agrupan en el CRM para reclamarlas por WhatsApp.
4. El archivo `RESUMEN_MAESTRO_ACTUALIZADO.md` detalla el funcionamiento interno del software y es solo para uso técnico y de mantenimiento.
5. **Ley Antifraude (VeriFactu):** El sistema inyecta un código criptográfico (Hash SHA-256) en cada ticket y factura, bloqueando su borrado. Si un empleado comete un error, indícale que debe usar el botón de "Devolución".