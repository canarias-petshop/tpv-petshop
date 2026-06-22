# 👑 MANUAL DE ADMINISTRADOR: ANIMALARIUM TPV y ERP
*Guía completa de los módulos de gestión, contabilidad y gerencia.*

---

## 1. ⏱️ Gestión de Personal (Panel de Administrador)
Como administrador, tienes acceso a la configuración avanzada de tus empleados.

- **Registro de Empleados:** En la parte inferior de la pestaña "Personal", puedes dar de alta a nuevos empleados asignándoles un PIN de 4 dígitos.
- **Asignación de Turnos (Editor Visual):** Ve a "Gestión de Cuadrante (Editable)". Verás un calendario apilado por semanas que funciona como un Excel.
- **Revisión de Horas:** Puedes ver una tabla con los fichajes reales (Entrada y Salida) y las horas totales trabajadas, útil para preparar las nóminas a final de mes.

---

## 2. 📈 Estadísticas y Rendimiento
El panel de estadísticas ha sido reestructurado en dos grandes bloques para facilitar la toma de decisiones:

**💰 1. Salud Financiera:**
- **Dashboard de Balance Neto:** Calcula el beneficio real del mes restándole a las ventas del TPV las facturas de proveedores y el prorrateo inteligente de tus Gastos Fijos (luz, alquiler, autónomos).
- **KPIs Comerciales:** Visualiza el ticket medio y el margen de rentabilidad.

**📊 2. Estadísticas Comerciales y Operativas:**
- **Top 10 Depurado:** Listado de los productos y servicios más vendidos en el mes.
- **Rendimiento y ROI Laboral Exacto:** El sistema cruza las facturaciones con el peluquero asignado.

---

## 3. 🚚 Proveedores, Pedidos y Facturación
Control de la relación con tus distribuidores y gestión de stock automático.

- **Centro de Envíos:** Alertas en tiempo real sobre los horarios de corte de los comerciales.
- **Borradores de Pedido (Smart Restock):** El sistema reparte los artículos bajo mínimos a sus respectivos proveedores, escogiendo siempre al más barato.
- **Registro de Compras (Albaranes y Facturas):** Al introducir la factura de un proveedor y "Archivarla", el stock del Inventario sube automáticamente.
- **Pago de Deudas a Proveedores (Calendario de Vencimientos):** Puedes saldar facturas atrasadas total o **parcialmente**.

---

## 4. 📊 Contabilidad y Exportación para Asesoría
Preparación fácil de los impuestos y libros contables.

- **Gastos Puntuales vs Gastos Fijos:** Registra el alquiler, luz, nóminas y préstamos en la pestaña "Configurar Gastos Fijos".
- **Calendarios y Pagos Pendientes:** Separa visualmente los "Gastos Operativos" de los "Impuestos".
- **Exportación a Excel (Asesoría):** Usa el botón de **"Solo Facturas (IGIC)"** para generar un Excel limpio de "gastitos" de caja para el contable.

---

## 5. 🏦 Bancos y Tesorería
Control estricto de la liquidez en las cuentas de la empresa.

- **Visualización de Saldo en Vivo:** El saldo de los bancos sube automáticamente cuando los clientes pagan con tarjeta por el TPV.
- **Transferencias Internas e Ingresos:** Puedes mover dinero entre bancos o registrar el ingreso del sobrante del cajón de efectivo directamente en tu cuenta de banco.

---

## 6. 📦 Modificación Avanzada de Inventario (¡Actualizado para la Web!)
- **Familias y Categoría Web:** Mantén el catálogo ordenado por categorías. La columna **`Categoría Web` (`familia`)** dicta en qué sección de la tienda online (Next.js) aparece cada artículo.
- **Marcas (NUEVO):** En la nueva columna **`Marca`** del inventario, escribe exactamente la marca real del pienso o producto (Ej: "Royal Canin"). Esto habilitará automáticamente el filtro por marcas en la tienda online.
- **Importación Masiva de Catálogos:** Utiliza los scripts extractores para subir excels de comerciales extrayendo el código de barras, coste y PVP.

---

## 7. 🌐 Integración E-Commerce y Delivery (NUEVO)
Tu sistema TPV ahora es también el cerebro de tu Tienda Online (Next.js/Vercel).
- **Auto-registro web:** Cuando alguien entra a la web y compra, se registra automáticamente en tu base de datos de "Clientes" del TPV usando su número de teléfono.
- **Gestión de Pedidos Web:** Las compras web caen directamente en la subpestaña "Pedidos Web" del CRM de tu TPV. 
- **Convertir a Reparto:** Puedes pulsar "Crear Servicio a Domicilio" sobre un pedido web para pasarlo automáticamente a tu hoja de repartos físicos, leyendo la dirección que dejó el cliente online.

---

## 8. 👥 Gestión Avanzada de CRM y Agenda
- **Botón WhatsApp de Ahorro Acumulado:** El CRM lee todos los descuentos del 10% por mantenimiento y te muestra el "Ahorro Total". Al pulsar el botón, les enviará un mensaje celebrándolo.
- **Política Híbrida de Cancelaciones y Fianzas:** El sistema cuenta automáticamente las faltas. Otorga 1 falta de margen de confianza. Al llegar a 2 faltas, bloquea la reserva exigiendo cobrar una Fianza/Adelanto.

---

## 9. 💾 Copias de Seguridad Automáticas (Backups)
1. **Backup del Código (`crear_backup.bat`):** Empaqueta todo el programa en un archivo `.zip`.
2. **Backup de los Datos (`descargar_todos_los_datos.bat`):** Descarga en la carpeta `Backups_Datos_Nube` todo tu directorio en bruto. 

---

## 🔒 10. Consideraciones de Seguridad y Fiscalidad
1. **VeriFactu:** El sistema inyecta un código criptográfico (Hash SHA-256) en cada ticket y factura, bloqueando su borrado permanentemente.
2. **Sistema de Roles:** Tus empleados solo deben conocer su propio PIN de 4 dígitos. El sistema de ruteo bloqueará automáticamente su acceso a las vistas contables.