# 👑 MANUAL DE ADMINISTRADOR: ANIMALARIUM TPV y ERP
*Guía completa de los módulos de gestión, contabilidad y gerencia.*

---

## 1. ⏱️ Gestión de Personal (Panel de Administrador)
Como administrador, tienes acceso a la configuración avanzada de tus empleados.

- **Registro de Empleados:** En la parte inferior de la pestaña "Personal", puedes dar de alta a nuevos empleados asignándoles un PIN de 4 dígitos.
- **Asignación de Turnos (Cuadrante):** Puedes establecer qué horario hace cada empleado. Al asignar un turno (ej. `09:00 a 17:00` o `Libre`), el sistema de la Agenda lo leerá automáticamente para bloquear citas fuera de esa franja o en sus días libres.
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

- **Gestión de Proveedores:** Registra los datos de los comerciales, días de reparto y correos electrónicos de pedidos.
- **Borradores de Pedido (Smart Restock):** 
  - Desde "Inventario", el sistema te avisa del stock bajo. Pulsando "Auto-distribuir", el sistema reparte esos artículos pendientes a sus respectivos proveedores.
  - Desde "Proveedores", puedes revisar el borrador y pulsar el botón **"📧 Enviar Pedido"** para generar automáticamente un correo con la lista lista para mandar.
- **Registro de Compras (Albaranes y Facturas):**
  - Ve a **"Facturación y Stock > Registro de Compras"**.
  - Al introducir la factura de un proveedor, el sistema te permite actualizar el Precio de Coste de los productos.
  - Al "Archivar" esa compra, **el stock del Inventario sube automáticamente**.
- **Pago de Deudas a Proveedores:** En "Pagos Pendientes", puedes saldar facturas atrasadas descontando el dinero directamente de un Banco o de la Caja Fuerte.

---

## 4. 📊 Contabilidad y Exportación para Asesoría
Preparación fácil de los impuestos y libros contables.

- **Registro de Gastos Manuales:** Anota nóminas, recibos de luz, alquiler, seguros o cualquier otro gasto que no esté ligado a la compra de productos.
- **Gestión de Vencimientos:** El sistema te alertará si tienes recibos pendientes de pago.
- **Exportación a Excel (Asesoría):** 
  - Genera archivos `.xlsx` profesionales a final del trimestre.
  - El Excel ya viene con formato moneda, celdas de totales y columnas separadas de Base Imponible, IGIC y Cuotas, listo para que tu asesor lo importe en su programa.

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
- **Modificación Manual de Stock:** Solo usar en caso de robos, mermas o inventario físico anual (ya que las ventas y las devoluciones modifican el stock automáticamente).

---

## 🔒 Consideraciones de Seguridad
1. **Nunca reveles la contraseña/URL de acceso al panel principal (Streamlit Cloud)** a los empleados. 
2. Tus empleados solo deben conocer su propio PIN de 4 dígitos. Si entran con su PIN, no verán ni la pestaña de Contabilidad ni la de Bancos.
3. El archivo `RESUMEN_MAESTRO_ACTUALIZADO.md` detalla el funcionamiento interno del software y es solo para uso técnico y de mantenimiento.