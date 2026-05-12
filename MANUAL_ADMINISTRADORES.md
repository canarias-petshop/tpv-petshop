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
El panel de estadísticas ha sido reestructurado en dos grandes bloques para facilitar la toma de decisiones:

**💰 1. Salud Financiera:**
- **Dashboard de Balance Neto:** Calcula el beneficio real del mes restándole a las ventas del TPV las facturas de proveedores y el prorrateo inteligente de tus Gastos Fijos (luz, alquiler, autónomos).
- **KPIs Comerciales:** Visualiza el ticket medio y el margen de rentabilidad.
- **Estructura de Gastos:** Compara en un gráfico lo que gastas en compras variables frente a lo que gastas en estructura fija.

**📊 2. Estadísticas Comerciales y Operativas:**
- **Top 10 Depurado:** Listado de los productos y servicios más vendidos en el mes (el sistema elimina automáticamente las marcas de nombres de empleados para no distorsionar el catálogo).
- **Rendimiento y ROI Laboral Exacto:** El sistema extrae el dinero de los historiales clínicos de las mascotas y **lo cruza con el peluquero/a asignado originalmente en la agenda**. Así sabrás exactamente cuántos euros ha facturado cada empleado en su tiempo de trabajo real, con gráficas precisas.
- **Análisis de Agenda:** Volumen de citas diarias, tasa de cancelación y carga de trabajo por empleado (horas ocupadas vs libres).

---

## 3. 🚚 Proveedores, Pedidos y Facturación
Control de la relación con tus distribuidores y gestión de stock automático.

- **Centro de Envíos:** Alertas en tiempo real sobre los horarios de corte de los comerciales.
- **Borradores de Pedido (Smart Restock):** 
  - Al pulsar "Auto-distribuir", el sistema reparte los artículos bajo mínimos a sus respectivos proveedores. **Si un producto tiene varios proveedores, el sistema elegirá automáticamente al que tenga el precio de coste más bajo.**
  - Desde "Proveedores", puedes revisar el borrador y pulsar el botón **"📧 Enviar Pedido"** para generar automáticamente un correo electrónico formal con la lista lista para mandar.
- **Registro de Compras (Albaranes y Facturas):**
  - Al introducir la factura de un proveedor y "Archivarla", **el stock del Inventario sube automáticamente** y el precio de coste se actualiza para los futuros cálculos de rentabilidad.
- **Pago de Deudas a Proveedores (Calendario de Vencimientos):**
  - Puedes saldar facturas atrasadas total o **parcialmente** (ej: pagando solo 50€ de una factura de 100€) descontando el dinero directamente de un Banco o de la Caja Fuerte, lo que mantiene el flujo contable 100% exacto.

---

## 4. 📊 Contabilidad y Exportación para Asesoría
Preparación fácil de los impuestos y libros contables.

- **Gastos Puntuales vs Gastos Fijos:** Registra el alquiler, luz, nóminas y préstamos en "Gastos Fijos", indicando qué día del mes se cobran. Si pones el día 31, se ajustará solo a final de mes.
- *Nota de Automatización:* Los gastos menores **los registran las empleadas directamente desde la Caja** al sacar el dinero físico, enviándose a Contabilidad automáticamente.
- **Calendario Predictivo y Alertas:** Verás dividido lo que tienes que pagar **esta semana** y lo que tienes que pagar **este mes**, junto con un gráfico de esfuerzo económico.
- **Exportación a Excel (Asesoría):** 
  - Usa el botón de **"Solo Facturas (IGIC)"**. Te generará un Excel con dos pestañas (Facturas Emitidas y Recibidas) descartando los "gastitos" de caja automáticamente.

---

## 5. 🏦 Bancos y Tesorería
Control estricto de la liquidez en las cuentas de la empresa.

- **Visualización de Saldo en Vivo:** El saldo de los bancos sube automáticamente cuando los clientes pagan con tarjeta por el TPV, seleccionando ese banco específico, o cuando archivas facturas. El saldo baja al registrar gastos bancarios o pagar proveedores.
- **Transferencias Internas e Ingresos:** Puedes mover dinero entre bancos o registrar el ingreso del sobrante del cajón de efectivo directamente en tu cuenta de banco.

---

## 6. 📦 Modificación Avanzada de Inventario
- **Familias y Subfamilias:** Mantén el catálogo ordenado por categorías (Pienso, Accesorios, Peluquería) para facilitar las estadísticas.
- **Fechas de Caducidad:** (Pendiente de integrar visualmente) Permitirá rastrear qué lotes vencen pronto para forzar ventas cruzadas.
- **Importación Masiva de Catálogos:** Utiliza los scripts extractores para subir excels de comerciales extrayendo siempre el código de barras, coste y PVP.

---

## 7. 👥 Gestión Avanzada de CRM y Agenda
- **Botón WhatsApp de Ahorro Acumulado:** El CRM lee todos los descuentos del 10% por mantenimiento generados en los historiales de los perros de una familia y te muestra el "Ahorro Total". Al pulsar el botón, les enviará un mensaje celebrándolo.
- **Directorio de Cancelaciones Estricto:** La agenda contabiliza cuántas veces anula cita un cliente y le pone un aviso visual rojo al empleado para que lo tenga en cuenta.
- **Directorio Limpio y Ocultación Inteligente:** Las citas pasadas desaparecen visualmente para aligerar la carga del día a día, pero las puedes revelar con un botón.

---

## 8. 💾 Copias de Seguridad Automáticas (Backups)
Para garantizar que tus datos nunca se pierdan:
1. **Backup del Código (`crear_backup.bat`):** Empaqueta todo el programa en un archivo `.zip`.
2. **Backup de los Datos (`descargar_todos_los_datos.bat`):** Descarga en la carpeta `Backups_Datos_Nube` todo tu directorio en bruto. Está preparado para programarse automáticamente al cierre de tienda desde el panel de tareas de Windows.

---

## 🔒 9. Consideraciones de Seguridad y Fiscalidad
1. **VeriFactu:** El sistema inyecta un código criptográfico (Hash SHA-256) en cada ticket y factura, bloqueando su borrado permanentemente. Si un empleado comete un error grave post-Cierre Z, debes generar una Devolución legal.
2. **Sistema de Roles:** Tus empleados solo deben conocer su propio PIN de 4 dígitos. El sistema de ruteo bloqueará automáticamente su acceso a las vistas contables, sueldos de empleados o cuentas bancarias.
3. El archivo `RESUMEN_MAESTRO_ACTUALIZADO.md` detalla el funcionamiento interno del software y es la Biblia de referencia en caso de mantenimiento.