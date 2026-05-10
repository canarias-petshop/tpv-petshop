# RESUMEN MAESTRO DE PROYECTO: ANIMALARIUM ERP / TPV (Actualizado)

## ✅ ESTADO ACTUAL
El sistema se encuentra estable, optimizado para tablets y con los módulos funcionando al 100%. Se han purgado los scripts residuales y la base de datos está limpia a la espera de nuevas importaciones de catálogo (vía CSV) cuando el usuario lo decida.

## 1. Visión General del Proyecto
**Animalarium ERP / TPV** es un sistema de planificación de recursos empresariales (ERP) y Terminal de Punto de Venta (TPV) diseñado a medida para una tienda de mascotas y peluquería canina. Su objetivo es unificar todas las operativas del negocio (ventas, stock, agenda, contabilidad y CRM) en una única plataforma adaptada al uso táctil en tablets.

- **Frontend (Interfaz):** Python + Streamlit. Interfaz "Touch-First" con CSS personalizado (botones grandes, fuentes legibles y diseño sin márgenes inútiles adaptado a tablets).
- **Backend (Base de Datos):** Supabase (PostgreSQL en la nube).
- **Hardware Integrado:** Lector de códigos de barras de pistola e integración nativa con impresoras térmicas Star Micronics (vía protocolo PassPRNT).

### 🏆 Reglas de Oro del Inventario y Fiscalidad
1. **Nomenclatura Unificada:** El proveedor siempre se referenciará como **"Proveedor"** (nunca "Empresa"), tanto en la interfaz como en las comunicaciones.
2. **Vínculo por Proveedor:** Todo producto nuevo importado debe enlazarse estrictamente al nombre exacto de su proveedor para que funcione el Centro de Envíos.
3. **Fiscalidad de Productos:** La venta de artículos al público está exenta de impuestos (0% IGIC en ventas). El IGIC (ej. 3%) solo se registra como dato interno para compras a proveedores.
4. **Fiscalidad de Servicios:** Los servicios (peluquería, etc.) **SÍ llevan IGIC (ej. 7%)**. Sus tarifas se configuran siempre como **Precio Cerrado (PVP)** y el sistema extrae automáticamente la base imponible hacia abajo.
5. **SKU Automático:** Los códigos de barras internos se generan automáticamente (Ej: `OW-001` para Ownat) respetando un correlativo único continuo.

### 📥 Formato Estándar de Importación de Catálogos
Para futuras importaciones masivas, el sistema utiliza scripts extractores inteligentes con la siguiente lógica unificada:
1. **Origen de Datos:** Se copia el texto directamente de las columnas del Excel del proveedor y se pega en el script.
2. **Lectura Inversa (Derecha a Izquierda):** El script lee cada línea al revés para ignorar cabeceras o textos basura.
3. **Extracción de Precios:** El último número detectado (ej: `15,30`) es siempre el **Precio de Coste**. El penúltimo número detectado es siempre el **PVP**.
4. **Extracción de Código de Barras (EAN):** Busca de izquierda a derecha la primera cadena numérica que tenga 8 o más dígitos. Si existe, la asigna al campo `codigo_barras` para que funcione la pistola escáner automáticamente.
5. **Extracción de Nombre:** Todo el texto restante entre el código EAN y los precios se fusiona para crear el Nombre del artículo.
6. **Filtro Anti-Duplicados:** El script lee toda la base de datos de Supabase antes de empezar y omite cualquier línea cuyo Nombre o Código EAN ya exista en el TPV, evitando fallos en la caja.
7. **Categorización y Vínculos:** Asigna el IGIC (3% en productos), enlaza directamente con la ID exacta del proveedor y pone los stocks a 0 listos para el Centro de Envíos.

## 2. Módulos Completados (14 Pestañas Funcionales)
El sistema cuenta con **14 módulos principales operativos** en el código (`app.py`):

📦 **1. Inventario y Servicios**
- Separación inteligente entre "Productos" (con control de stock) y "Servicios" (peluquería, veterinaria).
- Cálculo automático de Base Imponible e IGIC.

🛒 **2. Terminal de Caja (TPV)**
- Buscador manual y escáner de pistola **(con añadido de 1 clic, auto-vaciado y reseteo instantáneo tras cada lectura exitosa o fallida)**. Formulario de artículo manual también con reseteo automático.
- **Optimización TPV Tablet:** Código JS global inyectado para desactivar el texto predictivo y autocorrector del teclado. Interfaz de ticket de cobro compactada (`zoom`) para mantener los botones de imprimir/email siempre visibles sin scroll.
- **Simetría y Alineación UI:** Cajas de cobro en efectivo alineadas a la base (`vertical_alignment="bottom"`) para mantener proporciones perfectas en pantallas táctiles.
- Pagos mixtos (Efectivo, Tarjeta, Bizum).
- **Detalle en Tickets:** El método de pago exacto (y su desglose en caso de ser mixto) se imprime y envía por email en el ticket al cliente.
- **Bloqueo Inteligente de Deudas y Contraseñas:** Se ha desactivado el autocompletado nativo del navegador para evitar que salten gestores de contraseñas. No se puede fiar dinero a clientes anónimos; el sistema obliga a seleccionar al cliente desde el panel VIP.
- **Selector dinámico de banco/datáfono:** Al cobrar con tarjeta o de forma mixta, permite enviar el dinero directamente a la cuenta bancaria seleccionada (y su datáfono) en tiempo real.
- **Sistema de Fidelización VIP Saneado y Diferido:** Suma 1 punto por cada 10€ de compra. Canjea puntos a 0.50€/pto. Si un cliente deja dinero a deber, **los puntos no se suman hasta que abone la deuda** posteriormente. La contabilidad reajusta proporcionalmente las bases imponibles e IGIC al aplicar puntos.
- Impresión térmica directa a Star Micronics (protocolo `starpassprnt://`) estabilizada: se eliminaron las recargas forzadas y se implementó un **auto-retorno a la pantalla de Nueva Venta a los 30 segundos** de inactividad.

👥 **3. Clientes y Mascotas (CRM)**
- Directorio principal mejorado con la visibilidad del **teléfono del dueño** directamente en el listado de mascotas.
- Fichas de familias y mascotas con cálculo de edad automático, asignación de **Peluquero/a Preferido** y un **Diario de Observaciones Clínicas** independiente.
- Historial clínico y de peluquería con cálculo de tiempo medio por servicio y registro del empleado ("Realizado por") para trazabilidad.
- **Registro de Cancelaciones (Políticas Estrictas):** El CRM detecta automáticamente cuántas veces ha cancelado una mascota y muestra una alerta roja en su ficha para que los empleados lo tengan en cuenta al darle cita.
- **Gestor de Deudas de Tienda (Pagos Pendientes):** Nueva sub-pestaña que agrupa automáticamente a los clientes morosos del TPV. Suma sus deudas, alerta visualmente a los 14 días y genera un mensaje de WhatsApp para recordarles el pago.

📜 **4. Historial Operativo**
- Registro en vivo de todos los tickets con **generación de Hash SHA-256 encadenado**.
- **Bloqueo Ley Antifraude (VeriFactu):** Borrado de tickets desactivado. Edición limitada exclusivamente a corregir el método de pago en tickets del turno actual, forzando la selección del datáfono/banco específico (Caixa, CajaSiete...) para evitar descuadres. Al hacer el Cierre Z, los tickets quedan bloqueados (Candado 🔒).
- Sistema de devoluciones (Abonos) que restaura el stock automáticamente y deja trazabilidad legal.
- Reimpresión de tickets antiguos conservando método de pago original.

💰 **5. Control de Caja Fuerte**
- Apertura de turnos con sugerencia automática del Fondo Inicial basada en el arqueo del día anterior.
- Calculadora visual de monedas y billetes para el arqueo.
- Registro de entradas y salidas manuales, con envío automatizado categorizado (Gastos de tienda, Servicios Exteriores, Impuestos, Proveedores) a Contabilidad.
- Generación e impresión del Cierre Z desglosando las tarjetas de forma **100% dinámica por cada datáfono/banco** registrado que haya tenido movimientos.
- **Sumatorio Automático:** El resumen del Cierre Z incluye la suma total de las ventas (Efectivo + Tarjetas + Bizum) calculada y mostrada en un bloque destacado.

📈 **6. Estadísticas**
- Dashboard financiero con balance neto (Ingresos vs Gastos).
- Gráfica visual de la evolución de las ventas diarias.

🚚 **7. Gestión de Proveedores y Pedidos**
- Directorio de proveedores con sus datos fiscales, de reparto y **control de Pedido Mínimo** para portes gratis.
- **Centro de Envíos:** Panel de alertas visuales en tiempo real que indica las horas de corte de los proveedores para envíos pendientes.
- **Smart Restock Centralizado:** Sistema de detección de stock bajo con casillas de verificación para desmarcar productos y un botón de "Auto-distribuir" que genera borradores automáticos.
- Integración de buscador de catálogo y formularios de artículos manuales *dentro* del detalle de cada borrador para evitar duplicidades de botones en la interfaz.

📑 **8. Facturación Legal y Stock**
- *Sub-1 Emisión:* Emisión de facturas a clientes calculando dinámicamente el desglose interno de Base Imponible y Cuota de IGIC, aunque el empleado solo introduzca el PVP Público.
- **Generación de Hash SHA-256 por factura y bloqueo total de borrado (Cumplimiento VeriFactu).**
- *Sub-2 Compras:* Registro de facturas de proveedores: al archivar una compra, el sistema actualiza automáticamente el stock, el precio de coste y el PVP en el inventario.
- *Sub-3 Archivo:* Archivo histórico de documentos con **Filtros Dinámicos Flexibles** (ignoran mayúsculas y plurales para encontrar siempre el gasto) y columna de **Fecha de Registro** exacta.
- *Sub-4 Pagos Pendientes:* Control para deudas a proveedores con **Calendario Visual de Vencimientos** y gráfico de previsión semanal. Capacidad de realizar **Pagos Parciales** indicando la cantidad exacta entregada hoy, descontándola del saldo de un Banco o de la Caja Fuerte, manteniendo la factura abierta hasta su liquidación total.

📊 **9. Contabilidad e Informes para Asesoría**
- **Gestión Separada de Gastos:** Sub-pestaña para "Gastos Puntuales" (compras, reparaciones) y "Gastos Fijos" (alquileres, luz, nóminas, impuestos, préstamos).
- **Calendario Predictivo y Alertas:** Panel dividido en **Vista Semanal (7 días) y Mensual (30 días)** con gráfico de esfuerzo económico para controlar la liquidez. Incluye ajuste automático para pagos a fin de mes (día 31).
- **Generador nativo de archivos Excel Inteligentes (.xlsx):** Separación total de la contabilidad en 4 bloques descargables:
  1. Ventas globales. 2. **Facturas para IGIC (Pestaña Emitidas y Recibidas separadas)**. 3. Tickets y Gastos menores. 4. Informe de Gastos Fijos actuales.

🎯 **Módulo Extra: Marketing y Ofertas (Admin)**
- **Planificador Anual:** Calendario visual de campañas con alarma predictiva (30-45 días) para evitar quedarse sin contenido.
- **Gestión de Eventos y Talleres:** Control de aforo, inscripciones y reservas (con estrategia de "Bono Redimible" en tienda).
- **Cápsulas de Texto:** Integración de "copywriting" pre-redactado listo para copiar y pegar.
- *Pendiente (Prioridad):* Club de Cumpleaños, Recuperación Win-back y Email Masivo.

📅 **10. Agenda y Citas (Inteligente)**
- Gestor de citas vinculado a las fichas de las mascotas y cruzado con los horarios de los empleados.
- **Centro de Recordatorios (Automatización Matutina):** Panel unificado que escanea la agenda para mostrar las citas del próximo día hábil (saltando domingos) y las alertas de mantenimiento. Incluye un **indicador de Canal Preferido** (WhatsApp, Llamada, SMS) en la ficha del cliente.
- **Buscador Inteligente de Huecos:** Al seleccionar una mascota, lee su historial, **muestra un panel informativo con su duración media y peluquero preferido**, lee los cuadrantes y ofrece los tramos libres exactos.
- **Anotaciones / Observaciones Especiales:** Campo dedicado para anotar las peticiones de corte o trato específico de la mascota que pide el cliente al llamar.
- **Estado "Pendiente" por Defecto:** Las citas nacen en un estado neutro (Pendiente 🟡) para adaptarse al flujo real de llamadas de confirmación unos días antes.
- **Filtro por Peluquero/a Preferido:** Si el cliente tiene un profesional asignado en su ficha, el sistema detecta automáticamente su preferencia y limita la sugerencia de huecos exclusivamente al horario de esa persona concreta.
- **Liberación Inteligente de Huecos y Cancelaciones:** Las citas incluyen estados dinámicos (Confirmada 🟢, Cancelada 💖, Cambio de cita 🔵, etc.). Al marcar una cita como "Cancelada" o "Cambio", **el sistema libera su hueco automáticamente** en el buscador y el cuadrante.
- **Carga Dinámica de Servicios:** El desplegable de servicios en la agenda lee en tiempo real el catálogo de servicios de la pestaña de Inventario.
- **Creación Rápida de Fichas:** Permite agendar una cita para una mascota no registrada, generando automáticamente su familia y ficha básica en la base de datos sin tener que salir de la agenda.
- **Directorio Editable Avanzado:** Tabla interactiva con casilla de **Borrado Seguro Definitivo** y que exige la asignación de un/a Peluquero/a. Si el usuario fuerza manualmente una cita en una hora ocupada, el sistema obliga a registrar un motivo justificativo.
- Cuadrante diario interactivo con vista de bloques de 5 minutos.
- Cuadrante semanal en formato "tarjetas" visuales.
- **Módulo de Estadísticas:** Panel de análisis de rendimiento con KPIs (Tasa de Cancelación, Horas trabajadas) y gráficas interactivas de volumen por día, carga por peluquero y servicios top.

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
- **Migración de Datos y Limpieza Histórica (Completado):** Se finalizó con éxito la importación masiva de catálogos exactos (Ownat/Argomanza S.L. y todo el portfolio de Zootecnia S.L.: Amanova, Cevas, Gloria, Imagine, Julius K9, Kong Clásico y Holiday, SP Veterinaria, Vetnova, Zoetis, Bioiberica, Cunipic, Earth Rated). Se recuperó también el catálogo de Servicios (peluquería) con cálculo de IGIC 7% inverso. Todo el código de uso único (scripts importadores) ha sido eliminado del repositorio para mantener la arquitectura limpia.
- **Copias de Seguridad Automáticas:** Mantenimiento activo del sistema de copias de seguridad blindado (`backup_total_automatico.py` / `descargar_base_datos.py` / `descargar_todos_los_datos.bat`) que permite extraer toda la base de datos de la nube a local en un clic, 100% compatible con el Programador de Tareas de Windows.
- **Testeo Técnico Integral:** Inclusión de una suite de pruebas visuales independientes (**`test_tecnico.py`**) para validar la conexión a la base de datos, verificar la integridad de las columnas (Ley Antifraude) y simular la lógica de actualización del stock en tiempo real.
- **Gestión de Bancos y Transferencias** (Pestaña 11).
- **Pago de Deudas** integrando las opciones de usar saldo de bancos o saldo en caja (Pestaña 8, Sub-Pestaña 4).
- **Conexión transparente de hardware de impresión** evitando bloqueos o apertura de múltiples pestañas en el navegador de la tablet.
- **Optimización UI/UX para Tablet (ÚLTIMO PUNTO SEGURO):** Se inyectó CSS personalizado en `app.py` para reducir márgenes (`padding-top: 0.5rem`), agrandar botones (`min-height: 48px`) y mejorar la legibilidad en pantallas táctiles. **Este es el punto oficial de restauración en el Timeline (Control de Versiones) en caso de fallos estructurales.**
- **Refactorización Modular (Hito D Completado):** Se han extraído exitosamente los 12 módulos funcionales a archivos independientes (`inventario.py`, `tpv.py`, `crm.py`, `historial.py`, `caja.py`, `estadisticas.py`, `proveedores.py`, `facturacion.py`, `contabilidad.py`, `agenda.py`, `bancos.py` y `personal.py`). Todos están importados y funcionando correctamente dentro de un `app.py` completamente limpio y simplificado, que ahora actúa únicamente como enrutador principal.
- **Data Trimming y Rendimiento (Completado):** Se reemplazaron todas las peticiones masivas a Supabase (`select("*")`) por selecciones estrictas de columnas en los 12 módulos. Esto ha reducido drásticamente el tamaño del JSON de descarga, acelerando la navegación entre pestañas en la tablet.
- **Sistema de Roles y Seguridad (Completado):** Se implementó inicio de sesión dual (Admin / Empleado). El sistema construye las pestañas dinámicamente, ocultando por completo los módulos sensibles (Contabilidad y Bancos) al personal no autorizado, pero manteniendo visibles Estadísticas y Facturación para el aprendizaje de los empleados.
- **Testeo y Automatización Funcional (Completado):** Se han conectado lógicamente varios módulos para evitar trabajos dobles: El saldo final de caja es el fondo inicial del día siguiente, los gastos de caja viajan solos a Contabilidad y la Agenda bloquea las citas si se marcan vacaciones en el Cuadrante Visual.
- **Cierre Z Dinámico y Agenda Inteligente Total (Completado):** Implementación de la selección dinámica de la cuenta receptora para los pagos con tarjeta en el TPV y la sugerencia cruzada de huecos en la Agenda de citas. El cuadrante diario cuenta con una vista compacta inteligente que detecta solapamientos permitidos (⚠️ Múltiple) y comprime visualmente las citas largas.
- **Sincronización Horaria y Bloqueos de Agenda (Completado):** Configuración de la zona horaria (Atlantic/Canary) para los fichajes y el cálculo de solapamientos. Sincronización absoluta de las 3 vistas de la Agenda, bloqueando horas ocupadas y documentando excepciones de agendamiento.
- **Optimización Extrema de Tablet y UI TPV (Completado):** Inyección JS global anti-autocorrector y anti-gestores de contraseñas. Agilización del buscador a 1 clic con reseteo automático de inputs. Ticket en pantalla rediseñado con impresión de deudas pendientes y política de puntos.
- **Políticas Estrictas y Estabilidad UI (Completado):** Se introdujeron las alertas de penalización de mascotas, el panel inteligente al agendar, la lista de servicios viva, el auto-borrado del escáner en TPV y se protegió la sesión eliminando el refresco forzado al enviar impresiones por Bluetooth/Wifi.
- **Saneamiento Fiscal y Contable (Completado):** Corrección de la lógica de Base Imponible e IGIC. Los tickets y facturas ahora diferencian la venta de "Servicios" (que desglosa IGIC) de la venta de "Productos" (que reporta todo como Base Imponible). Todo a prueba de fallos mediante parseo seguro de datos legados.
- **Automatizaciones Finales y Deep Linking (Completado):** Implementación del "Centro WhatsApp" y "Centro de Envíos" para establecer una rutina matutina clara.
- **Reorganización ERP (Completado):** Separación total de Catálogo (Inventario) y Compras (Proveedores y Pedidos), logrando un flujo de trabajo profesional sin botones duplicados ni sobrecarga visual.
- **Bloqueo Fiscal VeriFactu - Fase 2 (Completado):** Implementación de inalterabilidad en tickets y facturas. Generación de Hash SHA-256 encadenado y bloqueo de edición post-Cierre Z, cumpliendo la Ley Antifraude española.
- **Contabilidad Predictiva y Eventos (Completado):** Implementación del calendario visual a 60 días para gastos recurrentes en Contabilidad y creación del gestor de aforos para Talleres presenciales.
- **Plan de Marketing Anual (Completado):** Despliegue del calendario de campañas 2026 con textos redactados por temporadas y alarmas de contenido.

## 4. Próximos Pasos y Hoja de Ruta (Hacia el Mundo Real y Empresarial)

### FASE 1: Estabilidad y Seguridad Básica (COMPLETADO)
* Se completó el blindaje RLS en la base de datos con `service_role` key.
* Tolerancia a fallos validada mediante la arquitectura local recomendada (Despliegue de Docker en tienda) descrita en el apartado 5.

### FASE 2: Cumplimiento Normativo y Fiscal (COMPLETADO)
*   **Inalterabilidad de Tickets y Facturas (Ley Antifraude):**
    *   *Objetivo Cumplido:* Se ha desactivado el borrado y la edición libre. Todo error se subsana mediante el sistema de "Devoluciones" (Abonos) que anula el ticket oficial dejando rastro y restaurando stock.
*   **Cierres de Caja Inviolables (Cierre Z):**
    *   *Objetivo Cumplido:* Al emitir el "Cierre Z", el sistema echa el candado 🔒 a las ventas de ese día, impidiendo incluso corregir los métodos de pago.
*   **Integración VeriFactu (Obligatorio Hacienda):**
    *   *Objetivo Cumplido (Fase Local):* El sistema ya encadena criptográficamente (Hash SHA-256) las facturas y tickets en vivo. Queda pendiente (cuando Hacienda abra la pasarela y la API oficial) la simple conexión de envío de este Hash.
*   **Privacidad y Protección de Datos (RGPD):**
    *   *Objetivo:* Cumplir la ley al enviar mensajes (WhatsApp) y guardar datos de clientes.
    *   *Pasos a dar:* 
        1. Añadir una casilla en la ficha del cliente para marcar si "Ha firmado el documento de protección de datos".
        2. Añadir un botón para "Anonimizar Cliente" (si el cliente pide borrar sus datos, se cambia su nombre y teléfono por "Cliente Borrado", manteniendo sus tickets anónimos por obligación fiscal).

### FASE 3: Profesionalización Laboral y Comercial (Largo Plazo)
*   **Módulo de Marketing Automatizado:**
    *   *Objetivo:* Aprovechar la base de datos de clientes para adelantarse y automatizar planes de marketing (Instagram, WhatsApp y Eventos).
    *   *Estado Actual:* Pestaña creada con Planificador Anual y Gestor de Eventos operativo.
    *   *Estrategia Anual (Norma Alta Frecuencia Sin Email):* 
        - **Instagram (3x/semana):** Mezcla de Reels, Posts y Stories interactivas.
        - **WhatsApp (1x/mes máximo):** Solo para campañas clave o aperturas de agenda (evitar saturación).
        - **Ads / Tienda Física:** Acciones puntuales estratégicas. (El Email masivo queda descartado hasta tener una base de datos sólida).
    *   *Gestión de Temporadas y Copywriting:* El esqueleto del plan anual se carga completo en la base de datos. Toda la estrategia, normas de publicación y el esqueleto de campañas futuras residen en la carpeta **`marketing_plans/`**.
    *   *Alarma Predictiva:* Avisará entre 30 y 45 días antes de que se agote el contenido redactado. Cuando esto ocurra, el usuario solo debe decirle a la IA: *"Abre la carpeta marketing_plans, lee el plan anual y redáctame la siguiente temporada"*.
    *   **⏳ PRÓXIMOS PASOS PRIORITARIOS (Motor de Automatización):**
        1. **Marketing de Cumpleaños:** Escáner automático de fechas de nacimiento de mascotas para enviar felicitaciones y ganchos por WhatsApp.
        2. **Recuperación Win-Back:** Radar de clientes con más de 6 meses sin venir para enviarles promociones de rescate.
        3. **Campañas de Email Masivo:** Infraestructura para el envío de boletines cuando la base RGPD crezca.
*   **Gestión de Eventos y Talleres Presenciales:**
    *   *Estado (Completado):* Permite crear talleres, gestionar aforo máximo y llevar control de los clientes inscritos y reservas pagadas.
*   **Calendarios Visuales de Pagos y Tesorería:**
    *   *Objetivo:* Tener un panel visual (semanal y mensual) de todas las previsiones de pagos.
    *   *Pasos a dar:* Integrar en Facturación un panel de vencimientos para proveedores, y en Contabilidad un registro automatizado de gastos fijos/recurrentes (luz, agua, préstamos, nóminas, impuestos) que genere previsiones visuales y alarmas personalizables.
*   **Registro Horario a Prueba de Inspecciones:**
    *   *Objetivo:* Que los fichajes de los empleados sean válidos legalmente ante una inspección de trabajo.
    *   *Pasos a dar:* Asegurar que el sistema de fichaje guarde datos imposibles de alterar por el administrador sin justificación (como la hora exacta del servidor en Canarias, y no la hora que tenga la tablet).
*   **Opciones de Arquitectura y Despliegue (En Evaluación):**
    *   *Objetivo:* Definir la ubicación física del "Cerebro" del sistema y cómo empaquetarlo para el futuro.
    *   *Opción 1 (Máxima Estabilidad): Servidor en la Tienda.* El ordenador de sobremesa ejecuta el Docker (Programa + Base de Datos). La gran ventaja es que si se corta el internet de la calle, la red WiFi local sigue funcionando y el TPV no se detiene nunca.
    *   *Opción 2 (Máxima Comodidad): Servidor en Casa.* El Docker se instala en un equipo del programador. La tienda se conecta por VPN (Tailscale). La desventaja es que si hay un corte de internet en la tienda o en casa, el sistema se paraliza.
    *   *Opción 3 (Ejecutables e Instaladores):* 
        *   *Fase A:* Crear un programa `.exe` ejecutable que se instale en el ordenador de la tienda y se conecte a la base de datos en casa (o en la nube).
        *   *Fase B (Comercialización):* Crear un instalador universal (.exe para Windows, .apk para Android) para que otros negocios puedan comprar e instalar el programa fácilmente sin saber nada de programación ni consolas.
*   **El Reto del "Modo Sin Internet" (Sincronización Offline-First):**
    *   *Objetivo:* Que el TPV sea inmune a los cortes de internet, incluso si el servidor/base de datos está lejos.
    *   *Pasos a dar:* Implementar una "memoria caché" o base de datos temporal local (como SQLite). Si el internet se cae, el TPV sigue cobrando y guarda los tickets en esa memoria interna. En cuanto el sistema detecta que ha vuelto la conexión, envía automáticamente todos los tickets retenidos a la base de datos principal de forma invisible.
*   **Comercialización y Escalabilidad (Vender el programa):**
    *   *Objetivo:* Preparar el sistema para venderlo a otras tiendas o clínicas (Modelo SaaS).
    *   *Pasos a dar:* Crear una estructura de "Multitienda" o un proceso de instalación para que cada cliente (otra clínica) tenga su base de datos totalmente separada y privada.

## 5. MANUAL DE DESPLIEGUE EN TIENDA (Paso a Paso)

Esta sección es una guía estricta para el día que se decida instalar el sistema en el ordenador de sobremesa de la tienda, conectando el trabajo que se hace desde casa (Portátil) con el negocio, utilizando GitHub y Docker.

### A) Preparación inicial en el ordenador de la TIENDA (Solo se hace 1 vez)
1. **Instalar GitHub Desktop:** Descargar e instalar la aplicación oficial "GitHub Desktop" para Windows. Iniciar sesión con la misma cuenta de GitHub que se usa en el portátil.
2. **Clonar el Proyecto:** En GitHub Desktop, ir a `File > Clone repository`. Buscar el repositorio `tpv-petshop` y descargarlo (clonarlo) en una carpeta fácil de encontrar (por ejemplo: `C:\Animalarium\tpv-petshop`).
3. **Instalar Docker Desktop:** Descargar e instalar "Docker Desktop" para Windows. (Puede pedir reiniciar el ordenador. Es necesario aceptar todas las configuraciones por defecto y asegurarse de que el programa "Docker Desktop" se queda abierto y con el icono en verde).

### B) El Día a Día (Cómo aplicar las mejoras que haces desde casa)
Cada vez que programes algo nuevo en el portátil de tu casa y quieras que la tienda lo tenga, estos son los 3 pasos exactos:

**En tu CASA (Portátil):**
1. Termina de programar o realizar los cambios con la IA.
2. Asegúrate de hacer un *Commit* (guardar los cambios) y darle al botón **"Push"** en tu entorno de desarrollo para que el código suba a la nube de GitHub.

**En la TIENDA (Ordenador de sobremesa):**
1. **Descargar los cambios:** Abre la aplicación **GitHub Desktop**, selecciona el proyecto `tpv-petshop` y pulsa el botón azul **"Fetch origin"** (y luego **"Pull origin"**) que aparece arriba. Esto descargará instantáneamente los cambios que hiciste en casa.
2. **Encender el Motor:** Abre la terminal de Windows (Símbolo del sistema o PowerShell), navega hasta la carpeta del proyecto (`cd C:\Animalarium\tpv-petshop`) y escribe el siguiente comando:
   `docker-compose up -d --build`
   *(Este comando lee los cambios nuevos, reconstruye el sistema y lo deja funcionando de fondo).*
3. **¡A trabajar!:** En la tablet de la tienda, abre el navegador web y pon la Dirección IP del ordenador de sobremesa seguido de `:8501` (Ejemplo: `http://192.168.1.55:8501`). ¡El TPV ya estará actualizado y funcionando a máxima velocidad!