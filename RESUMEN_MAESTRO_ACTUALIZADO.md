# RESUMEN MAESTRO DE PROYECTO: ANIMALARIUM ERP / TPV (Actualizado)

## 1. Visión General del Proyecto
**Animalarium ERP / TPV** es un sistema de planificación de recursos empresariales (ERP) y Terminal de Punto de Venta (TPV) diseñado a medida para una tienda de mascotas y peluquería canina. Su objetivo es unificar todas las operativas del negocio (ventas, stock, agenda, contabilidad y CRM) en una única plataforma adaptada al uso táctil en tablets.

- **Frontend (Interfaz):** Python + Streamlit. Interfaz "Touch-First" con CSS personalizado (botones grandes, fuentes legibles y diseño sin márgenes inútiles adaptado a tablets).
- **Backend (Base de Datos):** Supabase (PostgreSQL en la nube).
- **Hardware Integrado:** Lector de códigos de barras de pistola e integración nativa con impresoras térmicas Star Micronics (vía protocolo PassPRNT).

## 2. Módulos Completados (13 Pestañas Funcionales)
El sistema cuenta con **13 módulos principales 100% operativos** en el código (`app.py`):

📦 **1. Inventario y Servicios**
- Separación inteligente entre "Productos" (con control de stock) y "Servicios" (peluquería, veterinaria).
- Cálculo automático de Base Imponible e IGIC.
- Smart Restock: Sistema de alertas de stock bajo con un botón para "Auto-distribuir" y generar borradores de pedidos a proveedores automáticamente.

🛒 **2. Terminal de Caja (TPV)**
- Buscador manual y escáner de pistola.
- Pagos mixtos (Efectivo, Tarjeta, Bizum).
- **Selector dinámico de banco/datáfono:** Al cobrar con tarjeta o de forma mixta, permite enviar el dinero directamente a la cuenta bancaria seleccionada (y su datáfono) en tiempo real.
- Sistema de fidelización VIP (suma y canjeo de puntos automáticos).
- Impresión térmica directa a Star Micronics sin recargar la página ni abrir pestañas infinitas (solución vía JavaScript con `window.top.location.href`).

👥 **3. Clientes y Mascotas (CRM)**
- Fichas de familias y mascotas con cálculo de edad automático y asignación de **Peluquero/a Preferido**.
- Historial clínico y de peluquería con cálculo de tiempo medio por servicio y registro del empleado ("Realizado por") para trazabilidad.
- Alertas de Mantenimiento: Sistema que detecta mascotas que llevan mucho tiempo sin venir y genera un enlace para enviarles un WhatsApp de recordatorio con un solo clic.

📜 **4. Historial Operativo**
- Registro en vivo de todos los tickets.
- Edición directa de errores (cambiar métodos de pago, aplicar descuentos a posteriori).
- Sistema de devoluciones que restaura el stock automáticamente.
- Reimpresión de tickets antiguos.

💰 **5. Control de Caja Fuerte**
- Apertura de turnos con sugerencia automática del Fondo Inicial basada en el arqueo del día anterior.
- Calculadora visual de monedas y billetes para el arqueo.
- Registro de entradas y salidas manuales, con envío automatizado a Contabilidad al registrar gastos de tienda.
- Generación e impresión del Cierre Z desglosando las tarjetas de forma **100% dinámica por cada datáfono/banco** registrado que haya tenido movimientos.

📈 **6. Estadísticas**
- Dashboard financiero con balance neto (Ingresos vs Gastos).
- Gráfica visual de la evolución de las ventas diarias.

🚚 **7. Proveedores y Pedidos**
- Directorio de proveedores con sus datos fiscales y de reparto.
- Gestor de Borradores de Pedido con un botón para generar automáticamente un correo electrónico con el pedido listo para enviar.

📑 **8. Facturación Legal y Stock**
- *Sub-1 Emisión:* Emisión de facturas a clientes a partir de compras (con selector de forma de pago y cliente).
- *Sub-2 Compras:* Registro de facturas de proveedores: al archivar una compra, el sistema actualiza automáticamente el stock, el precio de coste y el PVP en el inventario.
- *Sub-3 Archivo:* Archivo de documentos con opción de edición y borrado.
- *Sub-4 Pagos Pendientes:* Control para deudas a proveedores y gastos, con la capacidad de pagar seleccionando múltiples facturas y descontando el importe del saldo de un Banco o de la Caja Fuerte (dejando constancia en el movimiento de caja si hay turno abierto).

📊 **9. Contabilidad e Informes para Asesoría**
- Registro de gastos manuales (nóminas, luz, agua) y recepción automática de gastos menores derivados directamente desde la Caja Fuerte por los empleados.
- Generador nativo de archivos Excel (.xlsx) profesionales para la asesoría, con filas de totales, colores y formato moneda pre-configurado.
- Alertas de vencimientos pendientes.

📅 **10. Agenda y Citas (Inteligente)**
- Gestor de citas vinculado a las fichas de las mascotas y cruzado con los horarios de los empleados.
- **Buscador Inteligente de Huecos:** Al seleccionar una mascota, calcula su duración media basada en su historial, lee los cuadrantes de las empleadas en tiempo real y ofrece los tramos libres exactos. Permite que ambas empleadas trabajen en paralelo sugiriendo los huecos de ambas a la misma hora si están disponibles.
- **Filtro por Peluquero/a Preferido:** Si el cliente tiene un profesional asignado en su ficha, el sistema detecta automáticamente su preferencia y limita la sugerencia de huecos exclusivamente al horario de esa persona concreta.
- **Creación Rápida de Fichas:** Permite agendar una cita para una mascota no registrada, generando automáticamente su familia y ficha básica en la base de datos sin tener que salir de la agenda.
- **Directorio Editable Avanzado:** Tabla interactiva que exige la asignación de un/a Peluquero/a. Las citas "Sin Asignar" bloquean preventivamente el calendario. Si el usuario fuerza manualmente una cita en una hora ocupada, el sistema obliga a registrar un motivo justificativo.
- Cuadrante diario interactivo con vista de bloques de 5 minutos.
- Cuadrante semanal en formato "tarjetas" visuales.

🏦 **11. Bancos y Tesorería**
- Directorio de cuentas bancarias de la empresa (CaixaBank, Caja Siete, etc.).
- Gestión de IBAN, titulares y control en tiempo real del saldo y liquidez disponible.
- **Transferencias Internas:** Movimiento de dinero entre cuentas bancarias o ingreso de efectivo sobrante desde la Caja Fuerte a la cuenta del banco (actualizando el saldo bancario y retirando de la caja si hay turno activo).

⏱️ **12. Personal y Control de Horario**
- Fichaje rápido de entrada/salida para empleados mediante PIN de 4 dígitos (con ajuste estricto a la zona horaria de Canarias).
- Visualización de cuadrante de trabajo apilado por semanas (sin scroll horizontal).
- **Panel de Administrador:** Gestión de la plantilla, Editor Visual Masivo de Cuadrantes (tipo Excel para planificar el mes completo en segundos) y registro histórico de horas trabajadas para nóminas.

📖 **13. Ayuda y Procedimientos (NUEVO)**
- Manuales de usuario interactivos (Empleados y Administrador) integrados directamente en la aplicación.
- Buscador inteligente en tiempo real que pliega y despliega las secciones relevantes según el término buscado.
- Privacidad automatizada: Los empleados solo ven su propio manual operativo, mientras que el Administrador tiene acceso a los manuales gerenciales completos.

## 3. Estado Actual del Desarrollo (UI Optimizada y Automatizaciones Completadas)
Los hitos de refactorización y conexión inteligente entre módulos se dan por cerrados. Las últimas características clave integradas son:
- **Gestión de Bancos y Transferencias** (Pestaña 11).
- **Pago de Deudas** integrando las opciones de usar saldo de bancos o saldo en caja (Pestaña 8, Sub-Pestaña 4).
- **Conexión transparente de hardware de impresión** evitando bloqueos o apertura de múltiples pestañas en el navegador de la tablet.
- **Optimización UI/UX para Tablet (ÚLTIMO PUNTO SEGURO):** Se inyectó CSS personalizado en `app.py` para reducir márgenes (`padding-top: 0.5rem`), agrandar botones (`min-height: 48px`) y mejorar la legibilidad en pantallas táctiles. **Este es el punto oficial de restauración en el Timeline (Control de Versiones) en caso de fallos estructurales.**
- **Refactorización Modular (Hito D Completado):** Se han extraído exitosamente los 12 módulos funcionales a archivos independientes (`inventario.py`, `tpv.py`, `crm.py`, `historial.py`, `caja.py`, `estadisticas.py`, `proveedores.py`, `facturacion.py`, `contabilidad.py`, `agenda.py`, `bancos.py` y `personal.py`). Todos están importados y funcionando correctamente dentro de un `app.py` completamente limpio y simplificado, que ahora actúa únicamente como enrutador principal.
- **Data Trimming y Rendimiento (Completado):** Se reemplazaron todas las peticiones masivas a Supabase (`select("*")`) por selecciones estrictas de columnas en los 12 módulos. Esto ha reducido drásticamente el tamaño del JSON de descarga, acelerando la navegación entre pestañas en la tablet.
- **Sistema de Roles y Seguridad (Completado):** Se implementó inicio de sesión dual (Admin / Empleado). El sistema construye las pestañas dinámicamente, ocultando por completo los módulos sensibles (Contabilidad y Bancos) al personal no autorizado, pero manteniendo visibles Estadísticas y Facturación para el aprendizaje de los empleados.
- **Testeo y Automatización Funcional (Completado):** Se han conectado lógicamente varios módulos para evitar trabajos dobles: El saldo final de caja es el fondo inicial del día siguiente, los gastos de caja viajan solos a Contabilidad y la Agenda bloquea las citas si se marcan vacaciones en el Cuadrante Visual.
- **Cierre Z Dinámico y Agenda Inteligente Total (Completado):** Implementación de la selección dinámica de la cuenta receptora para los pagos con tarjeta en el TPV y la sugerencia cruzada de huecos en la Agenda de citas, integrando el filtro automático del Peluquero/a preferido y la creación rápida de fichas de clientes.
- **Sincronización Horaria y Bloqueos de Agenda (Completado):** Configuración de la zona horaria (Atlantic/Canary) para los fichajes y el cálculo de solapamientos. Sincronización absoluta de las 3 vistas de la Agenda, bloqueando horas ocupadas y documentando excepciones de agendamiento.

## 4. Próximos Pasos y Hoja de Ruta

**A Corto Plazo (Optimización Post-Refactorización):**
- **Testeo en Entorno Real:** Validar la aplicación durante el día a día en tienda para corregir pequeños detalles de experiencia de usuario en las tabletas (por ejemplo, detalle del cálculo de IGIC en la Facturación).

**A Medio Plazo (Obligación Legal - Próximo Año):**
- **Integración Verifactu:** Conexión obligatoria con Hacienda para cumplir con la normativa legal española (las tablas de la base de datos ya están preparadas para ello).

**A Largo Plazo (Visión Comercial):**
- **Comercialización (SaaS / Licencias):** Empaquetar el ERP/TPV para ofrecerlo o venderlo a otras clínicas y tiendas de mascotas. Aprovechar el "know-how" único del sector para ofrecer una solución robusta y adaptada que escasea en el mercado actual.