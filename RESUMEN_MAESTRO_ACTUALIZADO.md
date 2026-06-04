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

## 2. Módulos Completados (15 Pestañas Funcionales)
El sistema cuenta con **15 módulos principales operativos** ordenados estratégicamente en el código (`app.py`):

📦 **Inventario y Servicios**
- Separación inteligente entre "Productos" (con control de stock) y "Servicios" (peluquería, veterinaria).
- Cálculo automático de Base Imponible e IGIC.
- **Flexibilidad Fiscal de Servicios:** Desbloqueada la posibilidad de asignar IGIC 0% (u otros porcentajes) a servicios específicos como los extras de cosmética.
- **Uso Interno (Peluquería):** Nueva sub-pestaña para retirar productos del almacén para uso profesional (ej. champús). Descuenta el stock sin generar ingresos en caja, pero deja un registro contable a 0€ para el control estricto de consumos.

🛒 **Terminal de Caja (TPV)**
- Buscador manual y escáner de pistola **(con añadido de 1 clic, auto-vaciado y reseteo instantáneo tras cada lectura exitosa o fallida)**. Formulario de artículo manual también con reseteo automático.
- **Estabilización de Componentes:** Prevención de "filas fantasma" vacías en el carrito para evitar bloqueos del sistema o bucles de recarga infinitos.
- **Optimización TPV Tablet:** Código JS global inyectado para desactivar el texto predictivo y autocorrector del teclado. Interfaz de ticket de cobro compactada (`zoom`) para mantener los botones de imprimir/email siempre visibles sin scroll.
- **Simetría y Alineación UI:** Cajas de cobro en efectivo alineadas a la base (`vertical_alignment="bottom"`) para mantener proporciones perfectas en pantallas táctiles.
- **Pagos Parciales Multicanal:** Permite introducir cantidades exactas no solo en efectivo, sino también en Tarjeta y Bizum, gestionando sobrepagos o dejando el resto como deuda pendiente (sin crear la deuda ni guardarla hasta finalizar el cobro).
- **Diccionario Exacto de Clientes:** Selección en caja protegida por mapeo de diccionario en backend, erradicando los "Errores de Supabase" al cobrar a clientes con nombres complejos, espacios adicionales o falta de teléfono.
- **Cobro Rápido Inteligente (Lectura de Ficha Clínica):** El botón de cobro de agenda ahora tiene "Inteligencia Dual". Lee primero la **Ficha Clínica** para volcar al carrito todos los servicios y extras reales registrados hoy (ej. "Extra Nudos"), con sus precios finales. Si la ficha está vacía, lee la cita original por defecto. Además, incluye **Búsqueda Inversa** para emparejar nombres de citas antiguas (largas) con nombres de catálogo nuevos (cortos) evitando bloqueos en la caja.
- **Limpieza Automática (Auto-Reset):** Al finalizar un cobro o pulsar "Nueva Venta", el sistema no solo vacía el carrito y los vales, sino que también resetea automáticamente el selector de clientes a "Ninguno (Venta Anónima)" para evitar cobros erróneos al cliente anterior.
- **Pedidos a Domicilio Automatizados:** Casilla interactiva para enviar la compra a domicilio. Al cobrar, el sistema descuenta stock, ingresa el dinero y genera automáticamente una orden de reparto en el módulo de Servicios Extra.
- **Tickets por Email en Arte ASCII:** El envío de tickets por correo dibuja una maquetación visual tipo ticket de máquina registradora para mejor legibilidad. El sistema extrae el email de la ficha del cliente y abre una pestaña nueva en el navegador para evitar bloqueos internos.
- **Bloqueo Inteligente de Deudas y Contraseñas:** Desactivado agresivo de autocompletado en el navegador (inputs "readonly" temporales) para evitar que salten gestores de contraseñas cruzando datos de empleados y clientes. Obligación de asociar cliente VIP para poder dejar dinero a deber.
- **Selector dinámico de banco/datáfono:** Al cobrar con tarjeta o de forma mixta, permite enviar el dinero directamente a la cuenta bancaria seleccionada (y su datáfono) en tiempo real.
- **Sistema de Fidelización VIP Saneado y Diferido:** Suma 1 punto por cada 10€ de compra. Canjea puntos a 0.50€/pto. Si un cliente deja dinero a deber, **los puntos no se suman hasta que abone la deuda** posteriormente. La contabilidad reajusta proporcionalmente las bases imponibles e IGIC al aplicar puntos.
- **Ticket Regalo:** Opción de imprimir un ticket alternativo con la cabecera completa del negocio sin precios y con un aviso legal de devoluciones para cambios de productos regalados.
- **Filtrado de Cobro Rápido:** El panel de peluquerías de hoy en el TPV oculta automáticamente las citas pendientes, canceladas o modificadas, mostrando exclusivamente las confirmadas para mantener la caja limpia.
- **Integración Total de Vales de Tienda:** El TPV permite introducir códigos de vales, descuenta su saldo del total, actualiza la base de datos de vales automáticamente y lo refleja en el método de pago del ticket (ej. `Efectivo + Vale (VALE-XXXX)`), calculando correctamente los impuestos y bases imponibles.
- Impresión térmica directa a Star Micronics (protocolo `starpassprnt://`) estabilizada: se eliminaron las recargas forzadas y se implementó un **auto-retorno a la pantalla de Nueva Venta a los 30 segundos** de inactividad.

👥 **Clientes y Mascotas (CRM)**
- Directorio principal mejorado con la visibilidad del **teléfono del dueño** directamente en el listado de mascotas.
- **Unificación Inteligente de Dueños (Merge):** Desde la tabla editable de mascotas, al corregir o asignar el nombre del dueño, el sistema detecta si ya existe en la base de datos y fusiona automáticamente sus mascotas, teléfonos, puntos y deudas, eliminando duplicados sin dejar registros huérfanos.
- **Soporte para Familias:** Capacidad de registrar un Contacto Principal (para avisos automáticos) y un Contacto Secundario (Alternativo) con sus respectivos teléfonos, ambos reconocibles por el buscador.
- Fichas de familias y mascotas con cálculo de edad automático, inclusión de los campos **Sexo** (Macho/Hembra) y **Peso** editables, asignación de **Peluquero/a Preferido** y un **Diario de Observaciones Clínicas** independiente.
- **Cálculo de Nacimiento Inverso:** Permite introducir la edad directamente en formato texto (ej. "5 años", "6 meses") y el sistema calcula y guarda la fecha de nacimiento aproximada de forma automática.
- **Historial Clínico Inteligente:** Registro de sesiones de peluquería con **desplegable de servicios vinculado al inventario en tiempo real**, **auto-asignación de precios** si se deja en blanco y cálculo de duración exacto al guardar la sesión.
- **Módulo de Extras Dinámicos:** La ficha clínica incluye ahora un panel específico (expander) para añadir extras a la sesión (ej. Mascarillas, Extra Nudos). Permite registrar la hora exacta de inicio y fin del extra, calculando el precio automáticamente por minuto según la tarifa del catálogo y sumándolo al importe total de la sesión.
- **Alerta de Citas Sin Cerrar:** El sistema detecta si hay citas pasadas confirmadas en la agenda que no se han registrado en el historial de la mascota, mostrando una alerta roja bloqueante hasta que se guarde la sesión clínica.
- **Política Híbrida de Cancelaciones y Fianzas:** Sistema automático de faltas (Strikes) que rastrea los estados `Cancelada`, `Anulada`, `No presentado` y `Cambio (mismo día)`. El sistema otorga 1 falta de margen de confianza. Al acumular 2 faltas o más, el cliente queda bloqueado en la Agenda y el CRM con una alerta roja, obligando al empleado a registrar un pago por adelantado/fianza (`[💰 FIANZA PAGADA]`) para poder agendar su cita.
- **Gestor de Deudas de Tienda (Pagos Pendientes):** Nueva sub-pestaña que agrupa automáticamente a los clientes morosos del TPV. Alerta visualmente a los 14 días y genera un mensaje de WhatsApp para reclamarlo. Además, incluye un **Sistema de Cobro Integrado con Pagos Fraccionados** que permite abonar partes de la deuda introduciendo la cantidad exacta y seleccionando el método (Efectivo/Bancos), actualizando saldos y sumando Puntos VIP proporcionalmente de forma automática.
- **Gestor de Encargos Sincronizado:** Panel de pedidos de clientes protegido contra desincronización y con paginación ilimitada. Incorpora agrupador de alertas en panel desplegable, estado "Cancelado" (con obligatoriedad de añadir motivo) y ocultación por defecto del historial de encargos entregados o cancelados.

📜 **Historial Operativo**
- Registro en vivo de todos los tickets con **generación de Hash SHA-256 encadenado**.
- **Bloqueo Ley Antifraude (VeriFactu):** Borrado de tickets desactivado. Edición limitada exclusivamente a corregir el método de pago en tickets del turno actual, forzando la selección del datáfono/banco específico (Caixa, CajaSiete...) para evitar descuadres. Al hacer el Cierre Z, los tickets quedan bloqueados (Candado 🔒).
- **Políticas de Devolución (Vales y Abonos):** Límite legal de 14 días implementado con alerta visual (permite forzar en casos excepcionales). Al devolver, se puede generar un **Ticket de Abono** (reintegro con importes negativos) o un **Vale de Tienda** con código alfanumérico único para retener la liquidez en el negocio. Ambas opciones restauran el stock automáticamente.
- **Blindaje de Lectura:** Manejo seguro de tickets antiguos (`null safe`) para garantizar que la app nunca se cuelgue al revisar el historial, incluso si faltan datos en descuentos o productos.
- Reimpresión de tickets antiguos conservando método de pago original.

💰 **Control de Caja Fuerte**
- Apertura de turnos con sugerencia automática del Fondo Inicial basada en el arqueo del día anterior.
- Calculadora visual de monedas y billetes para el arqueo.
- Registro de entradas y salidas manuales, con envío automatizado categorizado (Gastos de tienda, Servicios Exteriores, Impuestos, Proveedores) a Contabilidad.
- Generación e impresión del Cierre Z desglosando las tarjetas de forma **100% dinámica por cada datáfono/banco** registrado que haya tenido movimientos.
- **Sumatorio Automático:** El resumen del Cierre Z incluye la suma total de las ventas (Efectivo + Tarjetas + Bizum) calculada y mostrada en un bloque destacado.

📈 **Estadísticas y Salud Financiera**
- **Estructura en Pestañas:** Ahora organizado en dos grandes bloques para mayor claridad visual: "Salud Financiera" y "Estadísticas Comerciales y Operativas".
- **Salud Financiera (Dashboard):** Análisis realista del balance financiero cruzando datos de ventas TPV vs Facturas de proveedores y Gastos Fijos mensualizados.
- **Selector de Periodos Dinámico:** Análisis personalizable (Semanal, Mensual, Trimestral, Semestral, Anual, Personalizado) que recalcula al vuelo el prorrateo de gastos fijos.
- **UI Analítica Moderna:** Sustitución de tablas estáticas por DataFrames con barras de progreso integradas (ProgressColumns) y gráficos de área de evolución.
- **Seguridad de Acceso:** Panel oculto a empleados y restringido **exclusivamente para el rol Administrador**.
- **Métricas Avanzadas de Crecimiento:** Cálculo automático del Crecimiento Mensual (MoM), Ticket Medio y N.º de Operaciones.
- **Rendimiento y ROI Laboral Exacto:** Se calcula cruzando el importe cobrado en la ficha de la mascota con el peluquero asignado originalmente en la agenda, garantizando precisión absoluta.
- **Análisis y Rendimiento de Agenda:** Gráficos multiproyección para analizar volumen de citas, distribución de estados y rendimiento temporal directamente integrado junto a las estadísticas de caja.
- **Top 10 de Ventas:** Business Intelligence depurado que respeta el nombre exacto de los productos/servicios para mantener congruencia con el catálogo.

🚚 **Gestión de Proveedores y Pedidos**
- Directorio de proveedores con sus datos fiscales, de reparto y **control de Pedido Mínimo** para portes gratis.
- **Centro de Envíos:** Panel de alertas visuales en tiempo real que indica las horas de corte de los proveedores para envíos pendientes.
- **Smart Restock Centralizado (Auto-Distribuidor Inteligente):** Sistema de detección de stock bajo con casillas de verificación para desmarcar productos y un botón de "Auto-distribuir" que genera borradores automáticos. **Novedad: Si un producto tiene varios proveedores, el sistema rastrea y escoge automáticamente al que tenga el precio de coste más bajo para maximizar la rentabilidad.**
- Integración de buscador de catálogo y formularios de artículos manuales *dentro* del detalle de cada borrador para evitar duplicidades de botones en la interfaz.

📑 **Facturación Legal y Stock**
- *Sub-1 Emisión:* Emisión de facturas a clientes calculando dinámicamente el desglose interno de Base Imponible y Cuota de IGIC, aunque el empleado solo introduzca el PVP Público.
- **Generación de Hash SHA-256 por factura y bloqueo total de borrado (Cumplimiento VeriFactu).**
- *Sub-2 Compras:* Registro de facturas de proveedores mediante escáner OCR por IA (Gemini). Incluye **Túnel Docker a OneDrive** para almacenar el archivo fiscal de la foto ordenado automáticamente por Año y Mes sin intervención humana.
- Al archivar una compra, el sistema actualiza automáticamente el stock, el precio de coste y el PVP en el inventario.
- *Sub-3 Archivo:* Archivo histórico de documentos con **Filtros Dinámicos Flexibles** (ignoran mayúsculas y plurales para encontrar siempre el gasto) y columna de **Fecha de Registro** exacta.
- *Sub-4 Pagos Pendientes:* Panel exclusivo para **deudas de mercancía a proveedores**, con **Calendario Visual de Vencimientos** y gráfico semanal. Capacidad de realizar **Pagos Parciales** indicando la cantidad exacta entregada hoy, descontándola de Bancos o Caja Fuerte.

📊 **Contabilidad e Informes para Asesoría**
- **Estructura Lineal y Libro Mayor:** Reorganización del flujo (`Puntuales > Fijos > Calendarios > Pagos Pendientes > Archivo Contable > Descargas`). El 'Archivo Contable' sirve como Libro Mayor inalterable de todos los movimientos de la empresa.
- **Calendarios Especializados:** División visual estricta entre **Gastos Operativos** (alquiler, nóminas) y **Calendario de Impuestos** (IRPF, IGIC). Las alertas de vencimientos críticos se han compactado en desplegables (expanders) para no saturar la vista.
- **Centro de Pagos de Gastos:** Panel de pagos pendientes aislado exclusivamente para facturas de servicios y reparaciones, sin mezclar con el stock de proveedores de la tienda.
- **Generador nativo de archivos Excel Inteligentes (.xlsx):** Separación total de la contabilidad en 4 bloques descargables:
  1. Ventas globales. 2. **Facturas para IGIC (Pestaña Emitidas y Recibidas separadas)**. 3. Tickets y Gastos menores. 4. Informe de Gastos Fijos actuales.

🎯 **Módulo Extra: Marketing y Ofertas (Admin)**
- **Panel de Objetivos y ROI:** Definición de KPIs numéricos (ej: aumentar ventas, captar clientes) con barras de progreso interactivas para medir el éxito real de las acciones publicitarias.
- **Plan Maestro y Dashboard Financiero:** Calendario visual de publicaciones y acciones integrado con un control estricto de **Presupuesto Asignado vs Gasto Real**.
- **Análisis por Canales:** Gráficas automatizadas que muestran cómo se distribuye la inversión publicitaria entre medios Digitales (RRSS), Físicos (Cartelería) y Tradicionales (Radio).
- **Campañas Especiales:** Espacio aislado para gestionar la inversión en ferias externas o en la iniciativa privada *Innovate*.
- *Pendiente (Prioridad):* Club de Cumpleaños, Recuperación Win-back y Email Masivo.

🗓️ **Proyectos, Reuniones y Eventos (NUEVO)**
- Módulo puramente corporativo y de gestión logística ajeno a las ventas de la tienda.
- **Macro-Proyectos (Expansión):** Panel de control para aperturas o reformas, con seguimiento de presupuesto, costes reales acumulados y un calendario tipo Kanban para los Hitos o Tareas del proyecto.
- **Ferias y Eventos Externos:** Fichas técnicas para controlar la logística de stands en ferias (dimensiones, material necesario), enlaces directos a planos (Drive/Canva) y panel de lluvia de ideas exclusivo del evento.
- **Talleres y Cursos (Clientes):** Gestor de aforos presenciales en la tienda, con inscripciones, control de reservas pagadas e inserción de clientes.
- **Gestor de Reuniones y Bloqueos:** Creación de clases, reuniones de equipo o formaciones que **bloquean automáticamente los tramos correspondientes en la Agenda de Peluquería** para evitar que se den citas por error.

✅ **Planificación y Tareas (Equipo y Gerencia)**
- **Calendario General de Plannings:** Cuadrícula visual semanal de toda la tienda. Las tareas olvidadas de días anteriores se marcan automáticamente en rojo (❌ Olvidada).
- **Ficha Individual (Empleados):** Selector de personal que aísla el ruido y muestra únicamente las tareas asignadas a la persona que está consultando ese día. Incluye un sistema de **"Anotaciones"** para dejar partes o reportes de incidencias al completar el trabajo.
- **Calendario de Gerencia (Dueños):** Espacio privado para organizar el trabajo de los gerentes (visitas a bancos, papeleos) con su propio calendario visual e histórico de cumplimiento.

 **Servicios Extra de Animalarium (NUEVO)**
- Módulo independiente para gestionar logística y servicios externos (Paseos, Educación, Entregas/Recogidas).
- **Peticiones Abiertas:** Los servicios de Paseo y Adiestramiento usan un formato de "Buzón de Disponibilidad" sin horas estrictas para facilitar la organización de rutas y grupos.
- **Autocompletado de Clientes:** Al seleccionar un cliente registrado, el sistema rellena instantáneamente su teléfono, dirección y un selector múltiple para elegir qué mascotas recibirán el servicio.
- **Botones de Conexión:** Cada petición de servicio genera enlaces automáticos de WhatsApp. Uno para avisar al cliente (ej. "¡Vamos en camino a recoger a Bobby!") y otro de comunicación interna (para mandar el aviso al equipo encargado).
- **Enrutamiento Inteligente de WhatsApp:** Las notificaciones de los paseos diferencian según el tipo; los "Paseos por ciudad" se envían directamente al móvil del paseador responsable.

📅 **Agenda y Citas (Inteligente)**
- Gestor de citas vinculado a las fichas de las mascotas y cruzado con los horarios de los empleados.
- **Identificación Rápida de Especie:** El directorio y las vistas de la agenda muestran automáticamente si la mascota es Perro, Gato, etc., al lado de su nombre para facilitar la preparación del peluquero.
- **Ocultación Inteligente:** Botón (toggle) para ocultar automáticamente las citas pasadas en el directorio y agilizar la visualización diaria.
- **Centro de Recordatorios (Automatización Matutina):** Panel unificado que escanea la agenda aislando exclusivamente las citas pendientes del próximo día hábil (saltando domingos) y las alertas de mantenimiento.
- **Buscador Inteligente de Huecos:** Al seleccionar una mascota, lee su historial, **muestra un panel informativo con su duración media y peluquero preferido**, lee los cuadrantes (y bloqueos de reuniones) y ofrece los tramos libres exactos.
- **Validación de Identidad:** El desplegable de nueva cita muestra el teléfono del dueño junto al nombre de la mascota para evitar confusiones.
- **Radar de Festivos:** Detecta y marca visualmente las fiestas nacionales, autonómicas de Canarias y locales de Santa Cruz de Tenerife en todas las vistas de la agenda y cuadrantes, ayudando a la planificación de cierres.
- **Radar de Huecos (Lista de Espera):** El sistema escanea citas futuras buscando clientes con el estado "Pendiente (Avisar hueco)" y despliega un panel de alertas con accesos directos a WhatsApp para ofrecerles las horas que se vayan liberando.
- **Inyección de Información en Vivo (Vistas):** Las vistas Diaria, Semanal y Mensual informan en la cabecera quién está trabajando, muestran los **Bloqueos/Reuniones** de forma prominente en color morado, y detallan en cada tarjeta de cita el **Nombre del Dueño, Teléfono y Raza** para minimizar clics.
- **Anotaciones / Observaciones Especiales:** Campo dedicado para anotar las peticiones de corte o trato específico de la mascota que pide el cliente al llamar.
- **Limpieza de Cuadrantes Visuales:** Las vistas Diaria, Semanal y Mensual excluyen automáticamente las citas canceladas, anuladas, no presentadas o re-agendadas para no ensuciar la visión de carga de trabajo.
- **Estado "Pendiente" por Defecto:** Las citas nacen en un estado neutro (Pendiente 🟡) y disponen de una política de cancelación clara (Cancelada por Cliente vs Anulada por Tienda).
- **Estados Compuestos y de Asistencia:** Incluye "Asistió ✅" y "No presentado ❌". Emojis dinámicos combinados para identificar rápidamente servicios especiales.
- **Filtro por Peluquero/a Preferido:** Si el cliente tiene un profesional asignado en su ficha, el sistema detecta automáticamente su preferencia y limita la sugerencia de huecos exclusivamente al horario de esa persona concreta.
- **Liberación Inteligente de Huecos y Cancelaciones:** Las citas incluyen estados dinámicos (Confirmada 🟢, Cancelada 💖, Cambio de cita 🔵, etc.). Al marcar una cita como "Cancelada" o "Cambio", **el sistema libera su hueco automáticamente** en el buscador y el cuadrante.
- **Carga Dinámica de Servicios:** El desplegable de servicios en la agenda lee en tiempo real el catálogo de servicios de la pestaña de Inventario.
- **Creación Rápida de Fichas:** Permite agendar una cita para una mascota no registrada, generando automáticamente su familia y ficha básica en la base de datos sin tener que salir de la agenda.
- **Directorio Editable Avanzado:** Tabla interactiva con casilla de **Borrado Seguro Definitivo**, asignación de Peluquero/a y un **desplegable de Servicios conectado al inventario** para correcciones rápidas. Si el usuario fuerza una cita manualmente en una hora ocupada, el sistema obliga a registrar un motivo justificativo.
- **Vista Diaria:** Cuadrante interactivo con vista de bloques de 5 minutos y ocultación de huecos libres.
- **Vista Semanal:** Formato "tarjetas" visuales ordenadas cronológicamente.
- **Vistas Rediseñadas (CSS Grid):** Tanto la vista Diaria, Semanal (a 1 o 2 semanas vista) como la Mensual utilizan un formato HTML/CSS avanzado estético y adaptable que resume el volumen de citas, turnos y festivos sin descuadres.
- **Módulo de Estadísticas:** Panel de análisis de rendimiento con KPIs (Tasa de Cancelación, Horas trabajadas) y gráficas interactivas de volumen por día, carga por peluquero y servicios top.

🏦 **Bancos y Tesorería**
- Directorio de cuentas bancarias de la empresa (CaixaBank, Caja Siete, etc.).
- Gestión de IBAN, titulares y control en tiempo real del saldo y liquidez disponible.
- **Transferencias Internas:** Movimiento de dinero entre cuentas bancarias o ingreso de efectivo sobrante desde la Caja Fuerte a la cuenta del banco (actualizando el saldo bancario y retirando de la caja si hay turno activo).
- **Cuentas Revolut:** Integración total de cuentas online separadas (Negocio / Nóminas).

⏱️ **Personal y Control de Horario**
- Fichaje rápido de entrada/salida para empleados mediante PIN de 4 dígitos (con ajuste estricto a la zona horaria de Canarias).
- **Registro Inalterable Laboral:** Generación de firma criptográfica Hash SHA-256 encadenada en cada fichaje para cumplir con la estricta normativa laboral y evitar modificaciones manuales del administrador.
- **Guardián de Fichajes (Banner No Bloqueante):** Sistema de alerta inteligente que lee los cuadrantes y despliega un "Banner superior" para obligar a fichar, pero **sin interrumpir ni paralizar el uso de la caja** para otros compañeros. El Administrador dispone de acceso VIP ignorando los bloqueos.
- **Cooldown Anti-Errores:** Escudo de 30 minutos de bloqueo automático tras cada fichaje para evitar salidas dobles o marcajes erróneos por solapamiento de compañeros en el mostrador.
- Visualización de cuadrante de trabajo apilado por semanas (sin scroll horizontal).
- **Panel de Administrador:** Gestión de la plantilla, Editor Visual Masivo de Cuadrantes (tipo Excel para planificar el mes completo en segundos) y registro histórico de horas trabajadas para nóminas.

📖 **Ayuda y Procedimientos**
- Manuales de usuario interactivos (Empleados y Administrador) integrados directamente en la aplicación.
- Buscador inteligente en tiempo real que pliega y despliega las secciones relevantes según el término buscado.
- Privacidad automatizada: Los empleados solo ven su propio manual operativo, mientras que el Administrador tiene acceso a los manuales gerenciales completos.

## 3. Estado Actual del Desarrollo (UI Optimizada y Automatizaciones Completadas)
Los hitos de refactorización y conexión inteligente entre módulos se dan por cerrados. Las últimas características clave integradas son:
- **Migración de Datos y Limpieza Histórica (Completado):** Se finalizó con éxito la importación masiva de catálogos exactos y estandarización de nombres (limpiando códigos internos basura de proveedores y unificando marcas y prefijos SKU). Marcas integradas: Ownat, Argomanza, Zootecnia S.L. (Amanova, Cevas, Gloria, Imagine, Julius K9, Kong, SP Veterinaria, Vetnova, Zoetis, Bioiberica, Cunipic, Earth Rated, Stangest, Ecuphar, Beaphar, Boehringer, Cat's Way, Elanco, Flexi, MSD, Opko). Se recuperó el catálogo de Servicios con cálculo de IGIC 7% inverso. El código temporal importador ha sido eliminado.
- **Copias de Seguridad Automáticas:** Mantenimiento activo del sistema de copias de seguridad blindado (`backup_total_automatico.py` / `descargar_base_datos.py` / `descargar_todos_los_datos.bat`) que permite extraer toda la base de datos de la nube a local en un clic, 100% compatible con el Programador de Tareas de Windows.
- **Testeo Técnico Integral:** Inclusión de una suite de pruebas visuales independientes (**`test_tecnico.py`**) para validar la conexión a la base de datos, verificar la integridad de las columnas (Ley Antifraude) y simular la lógica de actualización del stock en tiempo real.
- **Gestión de Bancos y Transferencias** (Pestaña 11).
- **Pago de Deudas** integrando las opciones de usar saldo de bancos o saldo en caja (Pestaña 8, Sub-Pestaña 4).
- **Conexión transparente de hardware de impresión** evitando bloqueos o apertura de múltiples pestañas en el navegador de la tablet.
- **Optimización UI/UX para Tablet (ÚLTIMO PUNTO SEGURO):** Se inyectó CSS personalizado en `app.py` para reducir márgenes (`padding-top: 0.5rem`), agrandar botones (`min-height: 48px`) y mejorar la legibilidad en pantallas táctiles. **Este es el punto oficial de restauración en el Timeline (Control de Versiones) en caso de fallos estructurales.**
- **Refactorización Modular (Hito D Completado):** Se han extraído exitosamente los 12 módulos funcionales a archivos independientes (`inventario.py`, `tpv.py`, `crm.py`, `historial.py`, `caja.py`, `estadisticas.py`, `proveedores.py`, `facturacion.py`, `contabilidad.py`, `agenda.py`, `bancos.py` y `personal.py`). Todos están importados y funcionando correctamente dentro de un `app.py` completamente limpio y simplificado, que ahora actúa únicamente como enrutador principal.
- **Data Trimming y Rendimiento (Completado):** Se reemplazaron todas las peticiones masivas a Supabase (`select("*")`) por selecciones estrictas de columnas en los 12 módulos. Esto ha reducido drásticamente el tamaño del JSON de descarga, acelerando la navegación entre pestañas en la tablet.
- **Estandarización Horaria Global (Canarias) (Completado):** Implementada la conversión forzada inteligente desde el UTC de la base de datos a la zona horaria 'Atlantic/Canary' en todo el sistema (apertura/cierre de cajas, emisión de tickets, facturas, contabilidad, CRM y backups), garantizando fechas exactas incluso en los cambios bianuales de hora.
- **Mejoras UX Agenda y TPV (Completado):** Implementada la nueva vista Mensual en formato Calendario de Pared, visibilidad de los turnos en vivo en las vistas diaria/semanal, marca de especie de la mascota, radar automático de festivos en Canarias/Tenerife y reseteo automático del cliente en el TPV tras cada cobro para evitar cruces.
- **Escudo Anti-Doble Clic Global (Completado):** Desplegada una doble capa de seguridad para evitar cobros o documentos duplicados por latencia de internet. Front-End: Inyección JS que desactiva botones críticos durante 4 segundos. Back-End: Candado de tiempo (Cooldown de 3 segundos) en Python para ignorar peticiones simultáneas idénticas.
- **Sistema de Roles y Seguridad (Completado):** Se implementó inicio de sesión dual (Admin / Empleado). El sistema construye las pestañas dinámicamente, ocultando por completo los módulos sensibles (Contabilidad y Bancos) al personal no autorizado, pero manteniendo visibles Estadísticas y Facturación para el aprendizaje de los empleados.
- **Testeo y Automatización Funcional (Completado):** Se han conectado lógicamente varios módulos para evitar trabajos dobles: El saldo final de caja es el fondo inicial del día siguiente, los gastos de caja viajan solos a Contabilidad y la Agenda bloquea las citas si se marcan vacaciones en el Cuadrante Visual.
- **Cierre Z Dinámico y Agenda Inteligente Total (Completado):** Implementación de la selección dinámica de la cuenta receptora para los pagos con tarjeta en el TPV y la sugerencia cruzada de huecos en la Agenda de citas. El cuadrante diario cuenta con una vista compacta inteligente que detecta solapamientos permitidos (⚠️ Múltiple) y comprime visualmente las citas largas.
- **Sincronización Horaria y Bloqueos de Agenda (Completado):** Configuración de la zona horaria (Atlantic/Canary) para fichajes y solapamientos. Sincronización de las 3 vistas de la Agenda (visibilidad total de Reuniones/Clases con alertas de color morado) y bloqueo automatizado de horas ocupadas.
- **Optimización Extrema de Tablet y UI TPV (Completado):** Inyección JS global anti-autocorrector y anti-gestores de contraseñas. Agilización del buscador a 1 clic con reseteo automático de inputs. Ticket en pantalla rediseñado con impresión de deudas pendientes y política de puntos.
- **Políticas Estrictas y Estabilidad UI (Completado):** Se introdujeron las alertas de penalización de mascotas, el panel inteligente al agendar, la lista de servicios viva, el auto-borrado del escáner en TPV y se protegió la sesión eliminando el refresco forzado al enviar impresiones por Bluetooth/Wifi.
- **Saneamiento Fiscal y Contable (Completado):** Corrección de la lógica de Base Imponible e IGIC. Los tickets y facturas ahora diferencian la venta de "Servicios" (que desglosa IGIC) de la venta de "Productos" (que reporta todo como Base Imponible). Todo a prueba de fallos mediante parseo seguro de datos legados.
- **Automatizaciones Finales y Deep Linking (Completado):** Implementación del "Centro WhatsApp" y "Centro de Envíos" para establecer una rutina matutina clara.
- **Reorganización ERP Multiestructura (Completado):** Desacoplamiento masivo de módulos operativos. (1) Catálogos separados de Compras. (2) Creación del Módulo "Proyectos y Eventos" separado de "Marketing". (3) Separación de "Tareas Visuales y Plannings" en pestañas individuales (General vs Fichas Personales).
- **Auto-Distribuidor Inteligente de Pedidos (Completado):** Se implementó una lógica de selección automática que, al generar borradores de reposición, compara precios entre proveedores para un mismo artículo y asigna la compra al que ofrece el menor coste.
- **Bloqueo Fiscal VeriFactu - Fase 2 (Completado):** Implementación de inalterabilidad en tickets y facturas. Generación de Hash SHA-256 encadenado y bloqueo de edición post-Cierre Z, cumpliendo la Ley Antifraude española.
- **Contabilidad Predictiva y Eventos (Completado):** Implementación del calendario visual a 60 días para gastos recurrentes en Contabilidad y creación del gestor de aforos para Talleres presenciales.
- **Plan de Marketing Anual (Completado):** Despliegue del calendario de campañas 2026 con textos redactados por temporadas y alarmas de contenido.
- **Refactorización de Estadísticas y Salud Financiera (Completado):** Panel rediseñado para cruzar automáticamente las ventas del TPV con las facturas de proveedores y el prorrateo exacto de gastos fijos (mensualizando cuotas anuales o trimestrales), proporcionando un Beneficio Neto estimado real mes a mes.
- **Estructuración Contable Avanzada (Completado):** Reorganización de las categorías de gastos fijos para alinearlas con los estándares de la asesoría y mejorar la lectura financiera del negocio.
- **Estabilización de Interfaz y Prevención de Errores (Completado):** Implementados parches de seguridad en el TPV (resolviendo fallos de diccionarios en despliegues con clientes sin teléfono o con espacios), reparación de CSS para selectores nativos de Hora y fecha, y cálculos automáticos de tiempo en fichas clínicas.
- **Paginación Ilimitada (Bypass Límite 1000 filas de Supabase) (Completado):** Implementado un sistema de bucle de lectura en todos los módulos (Inventario, TPV, Facturación, Agenda, CRM) garantizando que el sistema escale sin perder productos o clientes independientemente del tamaño de la base de datos.
- **Precisión Decimal Global (Completado):** Habilitada la entrada de decimales en todos los campos numéricos del ERP para permitir precios y saldos exactos.
- **Integración Avanzada de Gastos Fijos y Agenda (Completado):** Se implementó el cruce de estados (Pagado/Pendiente) para los gastos fijos directamente con la tabla de compras en Contabilidad, y se extrajo la lógica de la Ficha Clínica a un módulo independiente (`ficha_clinica.py`), lo que permite abrir y editar el historial completo de cualquier mascota directamente desde las tablas de la Agenda ("Ver Ficha").
- **Optimización Interfaz CRM (Completado):** Se ha añadido la funcionalidad de ordenar alfabéticamente (A-Z) ignorando mayúsculas/minúsculas para evitar desórdenes, por más recientes o por puntos, tanto los directorios de clientes como de mascotas. También se implementó parseo robusto para fechas antiguas importadas.
- **Gestión Integral de Recogidas a Domicilio (Completado):** Incorporadas alertas visuales automáticas en la Agenda y el CRM para avisar cuando una mascota requiere recogida, con textos de WhatsApp adaptados (con soporte de formato estricto y emojis) incluyendo la dirección del dueño.
- **Cobro Rápido de Citas y Descuento por Visita Frecuente (Completado):** Desplegable integrado en el TPV que permite volcar las citas del día directamente al carrito de cobro. Si la mascota ha visitado la peluquería en los últimos 2 meses, aplica automáticamente un 10% de descuento. También lo aplica a cualquier cita marcada explícitamente como "Oferta / Dto." en la agenda, saltándose el requisito.
- **Optimización de Rendimiento Global (Lazy Loading Total) (Completado):** Se aplicó una capa de memoria caché (`@st.cache_data` con invalidación dinámica `db_version`) extraída al scope global en todos los módulos pesados. Esto erradica el lag de red y permite que interacciones en tablas (como "Ver Ficha") respondan al milisegundo.
- **Mejoras UI y Fechas de Alta en CRM (Completado):** Rediseño de formularios con `vertical_alignment="bottom"` para evitar cortes de texto en tablets. Añadida y reordenada la columna "F. Alta" en clientes y mascotas para conservar la antigüedad tras unificarlos.
- **Penalización de Morosos y Pago de Deudas por Ticket (Completado):** Bloqueo del uso de puntos VIP en el TPV si el cliente mantiene deudas activas. Refactorización del gestor de pagos en el CRM para saldar deudas de manera individualizada (filtrando primero por cliente).
- **Sincronización Multiusuario en Tiempo Real (Caché Híbrida) (Completado):** Se implementó un sistema de caché con caducidad (`ttl=15`) acoplado a disparadores de versión (`db_version`). Esto permite que varios ordenadores (ej. peluquería, mostrador y casa) vean los cambios de agenda y stock reflejados en un máximo de 15 segundos sin sacrificar la velocidad de la interfaz.
- **Blindaje de Integridad Referencial Anti-cuelgues (Completado):** Se inyectaron bloques de protección en TPV, Historial y Facturación para ignorar IDs temporales al actualizar el stock, garantizando que el sistema nunca colapse al cobrar citas con nombres antiguos que ya no existen en el catálogo o al devolver tickets desfasados.
- **Cálculo de Extras Dinámicos y Uso Interno (Completado):** Se implementó el panel de extras con hora de inicio y fin dentro de la Ficha Clínica. Además, se liberó la opción de IGIC 0% en servicios y se creó la pestaña "Uso Interno" en el Inventario para descontar consumos de tienda a coste cero (0€).
- **Guardián de Fichajes y Pantalla (Completado):** Sistema de bloqueo que fuerza el control de presencia según el cuadrante del empleado, con excepción "VIP" para la navegación del Administrador.
- **Escáner de Facturas por IA (OCR) con Google Gemini (Completado):** Se integró exitosamente el procesamiento inteligente de documentos en la pestaña "Registrar Compra" con soporte para subida de archivos o captura directa con cámara web/tablet.
  - *Extracción Inteligente:* Captura automática de Proveedor, productos, cantidades, importes netos, IGIC, descuentos (línea y pronto pago), lotes, caducidades y códigos de barras. La tabla muestra importes netos para cuadrar visualmente con el papel.
  - *Auto-creación y Enlazado:* Si la IA detecta un producto nuevo, lo crea en el inventario generando un SKU correlativo basado en las dos primeras letras, y fuerza su enlace al proveedor seleccionado.
  - *Escudo Anti-Fallos de API:* Implementado un buscador dinámico de modelos (`list_models`) que filtra versiones experimentales o retiradas de Google para garantizar disponibilidad 100%.
  - *Archivo Fiscal Automático y Túnel Docker:* Las imágenes capturadas desde la tablet traspasan la burbuja de seguridad de Docker a través de un túnel (`/facturas_digitales`) y se guardan directamente en el OneDrive del dueño, ordenadas por Año y Mes.
- **Scripts Locales de Procesamiento en Lote:** Creado el script independiente `procesar_facturas_lote.py` para automatizar la inserción de facturas atrasadas a la base de datos con IA de forma masiva desde Windows.
- **Sincronización Multidispositivo en Encargos (Completado):** Se aplicó el sistema de caché híbrida (`ttl=15` y `db_version`) a la tabla de encargos, resolviendo la desincronización visual entre los ordenadores del mostrador y la tablet de la tienda, y bloqueando la introducción de filas manuales que generaban datos fantasma.
- **Reseteo Limpio de Formularios (UI) (Completado):** Se aplicaron "llaves dinámicas" (`st.session_state.llave_...`) a todos los formularios del programa (Agenda, Proveedores, TPV, Facturación, etc.). Esto garantiza que, al pulsar "Guardar" y hacer el refresco de pantalla (`st.rerun()`), los campos se vacíen completamente, erradicando los datos fantasma y los registros duplicados accidentales.
- **Módulo de Tareas y Proyectos (Completado):** Integración de `tareas.py` con separación de roles (Los empleados ven sus rutinas diarias; el Administrador gestiona el Roadmap de proyectos internos a largo plazo).
- **Orden Alfabético Absoluto (Completado):** Refactorización de las tablas del CRM (Clientes y Mascotas) para ordenar de la A a la Z ignorando el formato de mayúsculas y minúsculas.

## 4. Próximos Pasos y Nueva Hoja de Ruta (Prioridades Ajustadas)

Tras la estabilización de los módulos y el inicio de captación de clientes, la hoja de ruta se ha reorganizado para pulir los detalles finales, implementar mejoras comerciales clave y preparar el terreno para la comercialización del sistema.

### 🛠️ FASE 1: Urgencias y Corrección de Fallos (Perfeccionamiento del Programa)
El objetivo inmediato es dejar el ERP blindado, legal y visualmente perfecto para el trabajo de mostrador y evitar errores humanos.
*   **Facturas IA en Borrador (Validación Manual):** Actualizar `facturacion.py` para que los escaneos OCR se guarden como "Borrador" y **NO sumen stock automáticamente** hasta que el equipo los valide visualmente en la tabla.
*   **Cumplimiento Antifraude (VeriFactu Fase 3):** Sustituir el borrado físico en el 'Archivo Contable' y 'Facturación' por un sistema legal de **"Anulación"** (importes a 0€ y stock revertido), dejando el rastro obligatorio para Hacienda.
*   **Optimización Visual Táctil (Tablet):** Implementar *Media Queries* CSS en `app.py` para aumentar automáticamente el tamaño de textos, tablas y botones solo cuando se use en pantallas pequeñas, manteniendo el diseño compacto en el PC.
*   **Gestión Visual de Inventario:** Incorporar Fechas de Caducidad y Lotes de forma visible en las tablas de stock y avisar de su vencimiento.

### 💎 FASE 2: Mejoras Estratégicas y Fidelización (Captación de Clientes)
Funciones que aporten valor comercial añadido para potenciar las ventas y retener a los nuevos clientes.
*   **Registro Inteligente de Alimentación (Predictor de Pienso):** Anotar en el CRM qué saco de pienso consume cada mascota. Cruzando el tamaño del saco comprado con su peso o ración diaria, el sistema generará una alerta de WhatsApp automatizada días antes de que se agote, garantizando la recompra y un excelente servicio de atención.
*   **Marketing Automatizado (Activo):** 
    1. **Club de Cumpleaños:** Escáner de fechas de mascotas para enviar felicitaciones y promociones por WhatsApp.
    2. **Radar Win-Back:** Sistema de detección de clientes con más de 6 meses sin visitarnos para enviar ofertas de rescate.

### 🏗️ FASE 3: Paso a Producción e Infraestructura Local (Estabilidad Total)
Punto intermedio para garantizar que los cortes de internet o la lentitud de la red no afecten a la tienda.
*   **Despliegue Local Oficial (Docker en la tienda):** Migrar el entorno de producción al ordenador físico de la tienda. La tablet se conecta a través de la red WiFi local, eliminando toda la latencia de internet al recargar la interfaz táctil.
*   **El Reto "Offline-First" (Sin Internet):** Implementar una base de datos temporal local (como SQLite). Si se cae la fibra, el TPV sigue cobrando e imprimiendo tickets al instante localmente, y los sube a Supabase de fondo en cuanto detecta que ha vuelto la conexión.

### 🚀 FASE 4: Comercialización y Escalabilidad (Venta del Software / SaaS)
Preparar el programa para convertirlo en un producto vendible a otras clínicas y peluquerías.
*   **Empaquetado Universal (Instaladores):** Crear un archivo autoejecutable `.exe` (Windows) y una `.apk` (Android) para que los nuevos clientes puedan instalar el programa con un simple doble clic sin necesidad de conocimientos de programación.
*   **Arquitectura Multitienda (SaaS):** Adaptar la estructura de la base de datos (Supabase) para albergar a múltiples empresas, garantizando un aislamiento estricto y total privacidad de los datos financieros de cada negocio.

*(Nota: Las Fases de Estabilidad Básica y Cumplimiento Normativo Inicial han sido completadas satisfactoriamente en iteraciones anteriores).*

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

## 6. HERRAMIENTAS Y SCRIPTS LOCALES (CÓMO USARLOS)

El sistema cuenta con herramientas que se ejecutan directamente desde Windows (y no desde la web de la tablet) para procesar grandes volúmenes de datos.

### 📸 Auto-Procesador de Facturas en Lote (IA)
Este script leerá todas las fotos de facturas que tengas atrasadas, extraerá los datos, creará proveedores si no existen, dará de alta artículos nuevos con códigos SKU generados, sumará el stock, actualizará precios de coste y mandará todo a Contabilidad y a tu carpeta de "Mis Facturas Digitales" de forma 100% autónoma.

**Pasos para ejecutarlo:**
1. Copia todas las fotos (con buena iluminación) a esta carpeta exacta de tu PC:
   `C:\Users\truji\OneDrive\Documentos\ANIMALARIUM\TPV ANIMALARIUM\CONTABILIDAD\Fotos para autocompletar facturas`
2. Abre tu terminal o consola (CMD o PowerShell) y asegúrate de estar en la carpeta donde tienes guardado el código del TPV (Ejemplo: `D:\clon vs mode\tpv-petshop` o similar).
3. Escribe el siguiente comando y pulsa Enter:
   `python procesar_facturas_lote.py`
4. Deja la ventana negra abierta. Irá chivándote paso a paso lo que hace. Cuando termine, las fotos procesadas se habrán movido automáticamente a tu carpeta de `Mis facturas digitales` organizadas por año y mes.

### 💾 Copias de Seguridad de la Base de Datos
- **Script:** `python backup_total_automatico.py`
- **Qué hace:** Descarga todos los clientes, ventas, compras y facturas de la nube (Supabase) y los empaqueta en excels muy limpios dentro de la carpeta local `Backups_Datos_Nube`. Listo para acoplarse al programador de tareas de Windows y ejecutarse cada noche.