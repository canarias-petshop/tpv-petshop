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
- Buscador manual y escáner de pistola **(con añadido de 1 clic, auto-vaciado y reseteo instantáneo tras cada lectura exitosa o fallida)**. Formulario de artículo manual también con reseteo automático.
- **Optimización TPV Tablet:** Código JS global inyectado para desactivar el texto predictivo y autocorrector del teclado. Interfaz de ticket de cobro compactada (`zoom`) para mantener los botones de imprimir/email siempre visibles sin scroll.
- **Simetría y Alineación UI:** Cajas de cobro en efectivo alineadas a la base (`vertical_alignment="bottom"`) para mantener proporciones perfectas en pantallas táctiles.
- Pagos mixtos (Efectivo, Tarjeta, Bizum).
- **Detalle en Tickets:** El método de pago exacto (y su desglose en caso de ser mixto) se imprime y envía por email en el ticket al cliente.
- **Selector dinámico de banco/datáfono:** Al cobrar con tarjeta o de forma mixta, permite enviar el dinero directamente a la cuenta bancaria seleccionada (y su datáfono) en tiempo real.
- **Sistema de Fidelización VIP Saneado:** Suma 1 punto por cada 10€ de compra. Canjea puntos a 0.50€/pto (límite del 50% del ticket). La contabilidad reajusta proporcionalmente las bases imponibles e IGIC al aplicar puntos para evitar descuadres fiscales.
- Impresión térmica directa a Star Micronics (protocolo `starpassprnt://`) estabilizada: **se eliminaron las recargas forzadas de página** para evitar el cierre de sesión, manteniendo al empleado en la pantalla con el botón de "Nueva Venta" siempre visible.

👥 **3. Clientes y Mascotas (CRM)**
- Directorio principal mejorado con la visibilidad del **teléfono del dueño** directamente en el listado de mascotas.
- Fichas de familias y mascotas con cálculo de edad automático, asignación de **Peluquero/a Preferido** y un **Diario de Observaciones Clínicas** independiente.
- Historial clínico y de peluquería con cálculo de tiempo medio por servicio y registro del empleado ("Realizado por") para trazabilidad.
- **Registro de Cancelaciones (Políticas Estrictas):** El CRM detecta automáticamente cuántas veces ha cancelado una mascota y muestra una alerta roja en su ficha para que los empleados lo tengan en cuenta al darle cita.
- **WhatsApp Deep Linking:** Sistema que detecta mascotas sin mantenimiento y genera un enlace `wa.me` para enviarles un WhatsApp con un solo clic, incorporando además un descuento gancho del 10%. También envía avisos automáticos de pedidos (Encargos) recibidos en tienda.

📜 **4. Historial Operativo**
- Registro en vivo de todos los tickets.
- Edición directa de errores (cambiar métodos de pago, aplicar descuentos a posteriori).
- Sistema de devoluciones que restaura el stock automáticamente.
- Reimpresión de tickets antiguos.
- Los tickets reimpresos desde el historial conservan e informan del método de pago utilizado.

💰 **5. Control de Caja Fuerte**
- Apertura de turnos con sugerencia automática del Fondo Inicial basada en el arqueo del día anterior.
- Calculadora visual de monedas y billetes para el arqueo.
- Registro de entradas y salidas manuales, con envío automatizado categorizado (Gastos de tienda, Servicios Exteriores, Impuestos, Proveedores) a Contabilidad.
- Generación e impresión del Cierre Z desglosando las tarjetas de forma **100% dinámica por cada datáfono/banco** registrado que haya tenido movimientos.
- **Sumatorio Automático:** El resumen del Cierre Z incluye la suma total de las ventas (Efectivo + Tarjetas + Bizum) calculada y mostrada en un bloque destacado.

📈 **6. Estadísticas**
- Dashboard financiero con balance neto (Ingresos vs Gastos).
- Gráfica visual de la evolución de las ventas diarias.

🚚 **7. Proveedores y Pedidos**
- Directorio de proveedores con sus datos fiscales, de reparto y **control de Pedido Mínimo** para portes gratis.
- Gestor de Borradores de Pedido con un botón para generar automáticamente un correo electrónico con el pedido listo para enviar.

📑 **8. Facturación Legal y Stock**
- *Sub-1 Emisión:* Emisión de facturas a clientes calculando dinámicamente el desglose interno de Base Imponible y Cuota de IGIC, aunque el empleado solo introduzca el PVP Público.
- *Sub-2 Compras:* Registro de facturas de proveedores: al archivar una compra, el sistema actualiza automáticamente el stock, el precio de coste y el PVP en el inventario.
- *Sub-3 Archivo:* Archivo histórico de documentos con **Filtros Dinámicos por Categoría** (Nóminas, Gastos Fijos, Mercancía, Impuestos, Servicios Externos).
- *Sub-4 Pagos Pendientes:* Control para deudas a proveedores y gastos, con la capacidad de pagar seleccionando múltiples facturas y descontando el importe del saldo de un Banco o de la Caja Fuerte (dejando constancia en el movimiento de caja si hay turno abierto).

📊 **9. Contabilidad e Informes para Asesoría**
- Registro de gastos manuales (nóminas, luz, agua, impuestos, técnicos) y recepción automática de gastos menores derivados directamente desde la Caja Fuerte por los empleados.
- **Generador nativo de archivos Excel Inteligentes (.xlsx):** Escanea el carrito exacto de tickets y facturas. Aplica la regla fiscal correcta: **0% de IGIC forzado para venta de Productos** (solo Base Imponible) y **desglose real de IGIC para la venta de Servicios**. Todo protegido con lectura tolerante a fallos (`safe_float`) para tickets antiguos y datos corrompidos.
- Alertas de vencimientos pendientes.

📅 **10. Agenda y Citas (Inteligente)**
- Gestor de citas vinculado a las fichas de las mascotas y cruzado con los horarios de los empleados.
- **Buscador Inteligente de Huecos:** Al seleccionar una mascota, lee su historial, **muestra un panel informativo con su duración media y peluquero preferido**, lee los cuadrantes y ofrece los tramos libres exactos.
- **Estado "Pendiente" por Defecto:** Las citas nacen en un estado neutro (Pendiente 🟡) para adaptarse al flujo real de llamadas de confirmación unos días antes.
- **Filtro por Peluquero/a Preferido:** Si el cliente tiene un profesional asignado en su ficha, el sistema detecta automáticamente su preferencia y limita la sugerencia de huecos exclusivamente al horario de esa persona concreta.
- **Leyenda de Colores y Políticas de Cancelación:** Las citas incluyen estados dinámicos (Confirmada 🟢, Cancelada 💖, Cambio de cita 🔵, etc.). Al marcar una cita como "Cancelada", se libera su hueco en el calendario y viaja a una pestaña específica de "🚫 Cancelaciones".
- **Carga Dinámica de Servicios:** El desplegable de servicios en la agenda lee en tiempo real el catálogo de servicios de la pestaña de Inventario.
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
- **Optimización Extrema de Tablet y UI TPV (Completado):** Corrección definitiva de variables al cobrar en efectivo. Inyección JS global anti-autocorrector. Agilización del buscador a 1 clic con reseteo automático de inputs. Rediseño estructural de la vista del ticket en pantalla eliminando el scroll fantasma y visibilizando el método de pago exacto empleado en todos los documentos.
- **Políticas Estrictas y Estabilidad UI (Completado):** Se introdujeron las alertas de penalización de mascotas, el panel inteligente al agendar, la lista de servicios viva, el auto-borrado del escáner en TPV y se protegió la sesión eliminando el refresco forzado al enviar impresiones por Bluetooth/Wifi.
- **Saneamiento Fiscal y Contable (Completado):** Corrección de la lógica de Base Imponible e IGIC. Los tickets y facturas ahora diferencian la venta de "Servicios" (que desglosa IGIC) de la venta de "Productos" (que reporta todo como Base Imponible). Todo a prueba de fallos mediante parseo seguro de datos legados.
- **Automatizaciones Finales y Deep Linking (Completado):** Implementación de recordatorios de citas, alertas de mantenimiento y avisos de encargos por WhatsApp (1-click) sin coste de API. Inclusión de categorías avanzadas (Servicios Exteriores, Tasas) con filtrado modular y control de pedidos mínimos para envíos.

## 4. Próximos Pasos y Hoja de Ruta (Hacia el Mundo Real y Empresarial)

A continuación, se detallan los pasos para llevar el sistema de un entorno de pruebas a un nivel profesional, cumpliendo con la normativa legal y garantizando su fiabilidad. Los pasos están explicados sin jerga técnica para facilitar su seguimiento y desarrollo.

### FASE 1: Estabilidad y Seguridad Básica (Corto Plazo)
*   **Modo "Sin Internet" (Tolerancia a fallos):**
    *   *Objetivo:* Que la tienda pueda seguir cobrando aunque se caiga el WiFi de forma temporal.
    *   *Pasos a dar:* Investigar e implementar una tecnología que guarde los tickets temporalmente en la memoria de la tablet y los envíe automáticamente al sistema central cuando vuelva la conexión.
*   **Blindaje de la Base de Datos:**
    *   *Objetivo:* Evitar que un error o acceso no autorizado borre datos importantes desde fuera de la aplicación.
    *   *Pasos a dar:* Configurar reglas de seguridad directamente en la base de datos (Supabase) para que, por ejemplo, los empleados solo puedan leer y escribir lo necesario, pero no alterar o borrar tablas enteras.
*   **Testeo en Entorno Real:**
    *   *Objetivo:* Probar el programa en el día a día de la tienda.
    *   *Pasos a dar:* Usar la aplicación en físico para afinar detalles de uso en las tablets (simetría, tamaño de botones, colores de la agenda, etc.).

### FASE 2: Cumplimiento Normativo y Fiscal (Medio Plazo)
* *(Nota actual: Durante la fase de pruebas actual, se permite borrar líneas y tickets para facilitar el desarrollo, pero estas acciones se bloquearán o auditarán en el paso a producción).*
*   **Inalterabilidad de Tickets y Facturas (Ley Antifraude):**
    *   *Objetivo:* Cumplir con la ley que prohíbe los programas de "doble uso" (los que permiten ocultar ventas o modificarlas a posteriori).
    *   *Pasos a dar:* 
        1. Desactivar la opción de borrar o editar libremente tickets o facturas antiguas.
        2. Crear un sistema de "Devoluciones" o "Abonos" (Tickets Rectificativos) que anule el ticket original de manera oficial, dejando rastro de ambas operaciones y reponiendo el stock.
*   **Cierres de Caja Inviolables (Cierre Z):**
    *   *Objetivo:* Evitar descuadres contables y modificaciones de ventas pasadas.
    *   *Pasos a dar:* Programar que, al emitir el "Cierre Z" del día, el sistema bloquee automáticamente la posibilidad de añadir, borrar o editar ventas con la fecha de ese día ya cerrado.
*   **Integración VeriFactu (Obligatorio Hacienda):**
    *   *Objetivo:* Conectar el programa con la Agencia Tributaria (normativa próxima a entrar en vigor).
    *   *Pasos a dar:* Configurar el sistema para que encadene las facturas de forma segura y tenga la capacidad de enviarlas a Hacienda automáticamente.
*   **Privacidad y Protección de Datos (RGPD):**
    *   *Objetivo:* Cumplir la ley al enviar mensajes (WhatsApp) y guardar datos de clientes.
    *   *Pasos a dar:* 
        1. Añadir una casilla en la ficha del cliente para marcar si "Ha firmado el documento de protección de datos".
        2. Añadir un botón para "Anonimizar Cliente" (si el cliente pide borrar sus datos, se cambia su nombre y teléfono por "Cliente Borrado", manteniendo sus tickets anónimos por obligación fiscal).

### FASE 3: Profesionalización Laboral y Comercial (Largo Plazo)
*   **Registro Horario a Prueba de Inspecciones:**
    *   *Objetivo:* Que los fichajes de los empleados sean válidos legalmente ante una inspección de trabajo.
    *   *Pasos a dar:* Asegurar que el sistema de fichaje guarde datos imposibles de alterar por el administrador sin justificación (como la hora exacta del servidor en Canarias, y no la hora que tenga la tablet).
*   **Migración a Servidor Propio y Red Privada (Docker + VPN):**
    *   *Objetivo:* Eliminar la dependencia de la nube (Streamlit Cloud/Supabase) para ganar velocidad extrema y control total, manteniendo la capacidad de actualizar el programa desde casa.
    *   *Pasos a dar:* 
        1. **Servidor Físico:** Utilizar un ordenador (puede ser el de sobremesa del negocio o un servidor dedicado en casa) como "Cerebro Central".
        2. **Contenedores (Docker):** Empaquetar todo el sistema (el código de Python y la Base de Datos PostgreSQL) en "contenedores" dentro de ese ordenador. Esto hace que el programa sea portátil y a prueba de fallos.
        3. **Red Privada (Tailscale/VPN):** Crear una red privada virtual segura. Así, el TPV y la tablet de la tienda pueden comunicarse con el servidor, y al mismo tiempo, el programador puede conectarse desde su portátil en casa para inyectar nuevas actualizaciones de código de forma invisible, sin interrumpir el trabajo de la tienda.
*   **Comercialización y Escalabilidad (Vender el programa):**
    *   *Objetivo:* Preparar el sistema para venderlo a otras tiendas o clínicas (Modelo SaaS).
    *   *Pasos a dar:* Crear una estructura de "Multitienda" o un proceso de instalación para que cada cliente (otra clínica) tenga su base de datos totalmente separada y privada.