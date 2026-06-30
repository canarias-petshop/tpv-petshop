# Resumen Maestro Actualizado - TPV y E-Commerce Animalarium
**Fecha de última actualización**: 30 de Junio de 2026

Este documento centraliza todos los avances, arquitecturas y módulos del ecosistema completo de Animalarium (TPV Físico + Tienda Web). Es el punto de partida **obligatorio** para retomar el proyecto en futuras sesiones.

> [!CAUTION]
> **NORMA ESTRICTA: PRODUCTOS vs SERVICIOS**
> Una cosa son los productos (piensos, accesorios) y otra muy distinta son los servicios (peluquería, clínica).
> Si el usuario ordena eliminar o modificar una marca concreta o un grupo de artículos en el contexto de "productos", **JAMÁS** debes alterar los registros que pertenezcan a "servicios" (aunque compartan tabla en la base de datos o utilicen la marca 'Genérico' u otra para categorizarse).
> **No asumas ni interpretes nada.** Verifica siempre si la acción puede afectar a los servicios antes de ejecutar un borrado masivo.

---

## 🏆 Lo que se ha conseguido hasta hoy (Historial de Éxitos)

### 1. Sistema TPV (Tienda Local)
- **Cobro Rápido (Tickets)**: Solucionado el problema de duplicidad de extras en los tickets. Al cobrar una ficha clínica, el ticket desglosa el servicio general y el extra en líneas separadas sin duplicar el total.
- **Gestión de Fichas (CRM)**: Corregido el error ("Data Mixing") que mezclaba datos de clientes y mascotas al abrir varias fichas simultáneamente.
- **Inventario Avanzado**:
  - Se han añadido nuevas columnas visuales y en base de datos para: `fecha_caducidad`, `stock_minimo`, `cantidad_reponer` y `marca`.
  - En la vista del inventario, los campos de categorización (Edad, Tamaño, etc.) utilizan selectores cerrados (`SelectboxColumn`) para evitar erratas tipográficas y asegurar que los filtros de la web cuadren.
- **CRM Encargos y Delivery**: 
  - Rediseñado en dos pestañas claras: 🏪 Encargos de Tienda y 🌐 Pedidos Web.
  - Se habilitó la eliminación dinámica directo de filas en las tablas de encargos.
  - Se añadió un botón "🚚 Crear Servicio a Domicilio" para convertir encargos web directamente en la hoja de reparto.
- **Reparto desde Caja (TPV)**: Automatizada la creación de Servicios a Domicilio desde el Cobro, rellenando automáticamente la dirección guardada del cliente al seleccionarlo.
- **Centro de Recordatorios Inteligente**:
  - La tabla de confirmaciones del día siguiente ahora es editable en vivo y posee una columna independiente ("🔔 Aviso") que guarda en *observaciones* si se ha mandado el WhatsApp.
- **Optimización de Rendimiento (Caching)**: Aplicado el sistema de `Smart Caching` de Streamlit en todas las pantallas. La base de datos no se satura al cambiar de pestaña.
- **Sincronización en Caliente (TPV ↔ CRM)**: Si al cobrar un usuario da de alta un cliente nuevo en el CRM, el selector de clientes de la Caja se refresca automáticamente *sin vaciar el carrito*.

### 2. Tienda Online (E-Commerce) y Estandarización de Base de Datos
- **El "Diccionario Maestro" Universal (¡GRAN LOGRO!)**: 
  - Se reescribieron las entrañas de los más de 400 productos en Supabase (Amanova y OWNAT) para que dejen de usar el vocabulario del fabricante (Puppy vs Junior, Mini vs Small) y utilicen un **Estándar Universal** fijado por la tienda.
  - *Edades*: Cachorro / Kitten, Adulto, Senior, Todas las edades.
  - *Tamaños*: Mini / Pequeño, Mediano, Grande, Gigante, Todas las Razas.
  - *Necesidades*: Esterilizado, Control de Peso, Sensible / Digestivo, Hipoalergénico, Urinario, Renal, Bolas de Pelo, Articulaciones, Pelo Blanco, Paladares Exigentes, Ninguna.
  - *Sabores Principales*: Limpios y puros (Pollo, Salmón, Cordero, Pato, Pavo, Atún, Cerdo, Ternera/Buey, Conejo, Ciervo, Jabalí, Pescado, Mix de Carnes).
- **Importación Inteligente y Creación de Multipacks**: 
  - Desarrollada la lógica para leer las tarifas PDF del proveedor y detectar "Cajas Multipack" (Ej: 12x85gr).
  - El sistema crea automáticamente **dos productos por cada caja**: el multipack entero y la unidad suelta, dividiendo a la perfección los costes y redondeando precios.
- **Fusión y Enlazado de Imágenes Extremo (Fuzzy Matching)**: 
  - Se completó la indexación de todas las gamas (Amanova completa, y OWNAT: Classic, Prime, Ultra, Just, Care, Hypoallergenic). 
  - El script cruzó inteligentemente los nombres de base de datos con las fotos locales renombradas manualmente, superando casi 800 imágenes perfectas de alta calidad.
  - Nomenclaturas estandarizadas (ej. marca `OWNAT` siempre en mayúsculas en DB). Se han limpiado y eliminado productos descatalogados.
- **Frontend Web Mejorado (`ClientCatalog.tsx`)**: 
  - El menú lateral izquierdo ahora agrupa de forma interactiva. 
  - Al lado de la marca "OWNAT" aparece el símbolo `+` que despliega sus familias (Classic, Prime, Ultra, Wetline...). Esto permite filtrados cruzados súper precisos.
  - Se eliminó visualmente la opción "Ninguna" de las necesidades especiales para limpiar la interfaz.
  - Se forzó el modo `force-dynamic` (sin caché) en el catálogo de Next.js para que refleje los cambios de base de datos en tiempo real al hacer F5.
- **Ajustes Exactos de Amanova y Servicios**:
  - Se rescataron 54 servicios históricos desde la tabla de citas y se aislaron bajo la marca "Genérico" para que desapareciera el filtro fantasma "Animalarium" de la web.
  - Se reestructuraron las gamas de Amanova: los húmedos se reasignaron a "Wet Line", y 18 formatos exactos de pienso seco (indicados manualmente por gerencia) se clasificaron estrictamente como "Low Grain", dejando el resto como "Grain Free".
  - Se añadió la columna visible **"Gama"** en la tabla de inventario del TPV (`inventario.py`) para permitir gestión manual, y se automatizó su despliegue a Streamlit Cloud.
- **Auto-registro de Clientes y Conexión Web-TPV**: Integración bidireccional perfeccionada. El sistema en la web busca cruzar clientes no solo por teléfono, sino también por **Nombre y Apellidos completos**, evitando duplicados y vinculando las cuentas existentes.
- **Checkout, Puntos y Descuentos Automatizados**: 
  - La web aplica las reglas de negocio del TPV físico: Acumulación de 1 punto por cada 10€ de compra y canjeo (1 punto = 0.50€ descuento, máximo 50% del total).
  - El sistema crea la venta en estado "Deuda" en el historial del TPV, y se coordina un encargo para descontar stock. Si el encargo se cancela por falta de stock físico, una devolución en el TPV restaura el inventario.
- **Lógica de Envíos y Portes Web**:
  - Implementado coste dinámico de envío: Envío Cercanía (Santa Cruz/La Laguna) = 5€; Distancias largas = 10€; Envío Gratuito a partir de 130€.
  - Los gastos de envío se desglosan en ticket como un *servicio* con 7% de IGIC, a diferencia de la alimentación animal (exenta).
- **"Candado" del Catálogo Web**: La web bloquea y oculta estrictamente cualquier producto que no sea de la categoría "Alimentación seca", "Alimentación húmeda" o "Snack". Todo lo demás (champús, collares, etc.) se gestiona en el TPV pero no contamina el catálogo online.
- **Enriquecimiento de Catálogo Asistido por IA (Gemini)**:
  - Se implementó un script automatizado en Python (`enrich_products.py`) para consultar la API de Gemini 2.5 Flash, el cual redacta descripciones comerciales cortas (con emojis y destacando ingredientes clave) para todos los productos que no tenían información.
  - Más del 50% del catálogo (330+ productos) ya cuenta con textos únicos generados, lo que mejora drásticamente el SEO y la experiencia de usuario.
- **Corrección de Permisos RLS (Row Level Security) y Mi Cuenta**:
  - Solucionado el problema permanente de "Ficha en revisión" en la web. Se creó un cliente `anonSupabase` dedicado para consultar los perfiles (puntos y mascotas) saltando las restricciones RLS, permitiendo la vinculación instantánea web-TPV.
- **Mejoras Visuales de UX Web**:
  - Se modificaron las tarjetas de producto (`ClientCatalog.tsx`) para exponer claramente la Referencia (Ref) del artículo y la Descripción generada por la IA, directamente sobre el precio.
- **DESPLIEGUE A PRODUCCIÓN**: La web ha sido subida a la nube (Vercel) con despliegue automático conectado a GitHub, y el dominio final de GoDaddy (`animalariumtenerife.es`) ha sido vinculado exitosamente con certificados SSL.

---

## 🧹 Tareas de Limpieza Realizadas
- Se eliminaron por completo todos los scripts residuales temporales de Python (`relink_prime.py`, `standardize_categories.py`, `import_ownat_v3.py`, etc.) del directorio local para no contaminar el repositorio y dejar el área de trabajo impecable.

---

## 🚀 Planificación para la Próxima Sesión (Siguientes Pasos)

**Hito 1: Escaparate Web, Marketing y Responsive Design**
- **Adaptación Móvil (Responsive)**: Escribir las reglas CSS (Media Queries) para que la web se vea perfecta en teléfonos y tablets (menú hamburguesa, apilar grid de productos, reducir fuentes del Hero).
- **Banners Rotativos**: Implementar el plan de anuncios rotativos (`PromoBanner.tsx`) en la cabecera del catálogo y en la página de inicio, anunciando: 10% primera compra, 10% en cajas enteras de pouch, sistema de puntos, y portes gratis >130€.

**Hito 2: Gestión de Web y Delivery (Workflow Avanzado)**
- **Alertas de Antigüedad**: Implementar un sistema visual que alerte cuando un "Pedido Web" lleve más de 2 días atascado sin enviarse o recogerse.
- **Gestión de Estados y Cancelaciones**: Implementar el estado final "Recibido y Avisado" para los encargos locales, junto con la lógica de cancelación y borrado seguro.

**Hito 3: Agenda y Periodicidad**
- Avanzar en el sistema de recurrencia y repetición de tareas (diario/semanal/mensual) dentro de la agenda o calendario.

**Hito 4: UX Web y Filtros Finales**
- **Sincronización Web Avanzada**: Modificar la interfaz web para mostrar las opciones secundarias conectadas de forma reactiva, permitiendo una experiencia de compra fluida.
- **Ajustes Estéticos**: Rediseñar la zona del pie de página y botones de WhatsApp web.

**Hito 5: Integraciones Futuras (A medio plazo)**
- **Nuevas Marcas**: Cuando se integre Royal Canin o cualquier otra marca, se deberá usar **estrictamente** el "Diccionario Maestro" para encajarla mediante scripts de importación (la web lo asimilará instantáneamente).
- **Pasarela de Pago (Stripe)**: Configurar la pasarela para aceptar cobros directos online.
- **Módulos Adicionales**: Ampliación hacia categorías de accesorios o reservas directas de peluquería en la tienda online.
