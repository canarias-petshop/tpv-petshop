# Resumen Maestro Actualizado - TPV y E-Commerce Animalarium
**Fecha de última actualización**: 2 de Julio de 2026

Este documento centraliza todos los avances, arquitecturas y módulos del ecosistema completo de Animalarium (TPV Físico + Tienda Web). Es el punto de partida **obligatorio** para retomar el proyecto en futuras sesiones.

> [!CAUTION]
> **NORMA ESTRICTA: PRODUCTOS vs SERVICIOS**
> Una cosa son los productos (piensos, accesorios) y otra muy distinta son los servicios (peluquerÃ­a, clÃ­nica).
> Si el usuario ordena eliminar o modificar una marca concreta o un grupo de artÃ­culos en el contexto de "productos", **JAMÃS** debes alterar los registros que pertenezcan a "servicios" (aunque compartan tabla en la base de datos o utilicen la marca 'GenÃ©rico' u otra para categorizarse).
> **No asumas ni interpretes nada.** Verifica siempre si la acciÃ³n puede afectar a los servicios antes de ejecutar un borrado masivo.


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

---

## ðŸ† Lo que se ha conseguido hasta hoy (Historial de Ã‰xitos)

### 1. Sistema TPV (Tienda Local)
- **Cobro RÃ¡pido (Tickets)**: Solucionado el problema de duplicidad de extras en los tickets. Al cobrar una ficha clÃ­nica, el ticket desglosa el servicio general y el extra en lÃ­neas separadas sin duplicar el total.
- **GestiÃ³n de Fichas (CRM)**: Corregido el error ("Data Mixing") que mezclaba datos de clientes y mascotas al abrir varias fichas simultÃ¡neamente.
- **Inventario Avanzado**:
  - Se han aÃ±adido nuevas columnas visuales y en base de datos para: `fecha_caducidad`, `stock_minimo`, `cantidad_reponer` y `marca`.
  - En la vista del inventario, los campos de categorizaciÃ³n (Edad, TamaÃ±o, etc.) utilizan selectores cerrados (`SelectboxColumn`) para evitar erratas tipogrÃ¡ficas y asegurar que los filtros de la web cuadren.
- **CRM Encargos y Delivery**: 
  - RediseÃ±ado en dos pestaÃ±as claras: ðŸª Encargos de Tienda y ðŸŒ Pedidos Web.
  - Se habilitÃ³ la eliminaciÃ³n dinÃ¡mica directo de filas en las tablas de encargos.
  - Se aÃ±adiÃ³ un botÃ³n "ðŸšš Crear Servicio a Domicilio" para convertir encargos web directamente en la hoja de reparto.
- **Reparto desde Caja (TPV)**: Automatizada la creaciÃ³n de Servicios a Domicilio desde el Cobro, rellenando automÃ¡ticamente la direcciÃ³n guardada del cliente al seleccionarlo.
- **Centro de Recordatorios Inteligente**:
  - La tabla de confirmaciones del dÃ­a siguiente ahora es editable en vivo y posee una columna independiente ("ðŸ”” Aviso") que guarda en *observaciones* si se ha mandado el WhatsApp.
- **OptimizaciÃ³n de Rendimiento (Caching)**: Aplicado el sistema de `Smart Caching` de Streamlit en todas las pantallas. La base de datos no se satura al cambiar de pestaÃ±a.
- **SincronizaciÃ³n en Caliente (TPV â†” CRM)**: Si al cobrar un usuario da de alta un cliente nuevo en el CRM, el selector de clientes de la Caja se refresca automÃ¡ticamente *sin vaciar el carrito*.

### 2. Tienda Online (E-Commerce) y EstandarizaciÃ³n de Base de Datos
- **El "Diccionario Maestro" Universal (Â¡GRAN LOGRO!)**: 
  - Se reescribieron las entraÃ±as de los mÃ¡s de 400 productos en Supabase (Amanova y OWNAT) para que dejen de usar el vocabulario del fabricante (Puppy vs Junior, Mini vs Small) y utilicen un **EstÃ¡ndar Universal** fijado por la tienda.
  - *Edades*: Cachorro / Kitten, Adulto, Senior, Todas las edades.
  - *TamaÃ±os*: Mini / PequeÃ±o, Mediano, Grande, Gigante, Todas las Razas.
  - *Necesidades*: Esterilizado, Control de Peso, Sensible / Digestivo, HipoalergÃ©nico, Urinario, Renal, Bolas de Pelo, Articulaciones, Pelo Blanco, Paladares Exigentes, Ninguna.
  - *Sabores Principales*: Limpios y puros (Pollo, SalmÃ³n, Cordero, Pato, Pavo, AtÃºn, Cerdo, Ternera/Buey, Conejo, Ciervo, JabalÃ­, Pescado, Mix de Carnes).
- **ImportaciÃ³n Inteligente y CreaciÃ³n de Multipacks**: 
  - Desarrollada la lÃ³gica para leer las tarifas PDF del proveedor y detectar "Cajas Multipack" (Ej: 12x85gr).
  - El sistema crea automÃ¡ticamente **dos productos por cada caja**: el multipack entero y la unidad suelta, dividiendo a la perfecciÃ³n los costes y redondeando precios.
- **FusiÃ³n y Enlazado de ImÃ¡genes Extremo (Fuzzy Matching)**: 
  - Se completÃ³ la indexaciÃ³n de todas las gamas (Amanova completa, y OWNAT: Classic, Prime, Ultra, Just, Care, Hypoallergenic). 
  - El script cruzÃ³ inteligentemente los nombres de base de datos con las fotos locales renombradas manualmente, superando casi 800 imÃ¡genes perfectas de alta calidad.
  - Nomenclaturas estandarizadas (ej. marca `OWNAT` siempre en mayÃºsculas en DB). Se han limpiado y eliminado productos descatalogados.
- **Frontend Web Mejorado (`ClientCatalog.tsx`)**: 
  - El menÃº lateral izquierdo ahora agrupa de forma interactiva. 
  - Al lado de la marca "OWNAT" aparece el sÃ­mbolo `+` que despliega sus familias (Classic, Prime, Ultra, Wetline...). Esto permite filtrados cruzados sÃºper precisos.
  - Se eliminÃ³ visualmente la opciÃ³n "Ninguna" de las necesidades especiales para limpiar la interfaz.
  - Se forzÃ³ el modo `force-dynamic` (sin cachÃ©) en el catÃ¡logo de Next.js para que refleje los cambios de base de datos en tiempo real al hacer F5.
- **Ajustes Exactos de Amanova y Servicios**:
  - Se rescataron 54 servicios histÃ³ricos desde la tabla de citas y se aislaron bajo la marca "GenÃ©rico" para que desapareciera el filtro fantasma "Animalarium" de la web.
  - Se reestructuraron las gamas de Amanova: los hÃºmedos se reasignaron a "Wet Line", y 18 formatos exactos de pienso seco (indicados manualmente por gerencia) se clasificaron estrictamente como "Low Grain", dejando el resto como "Grain Free".
  - Se aÃ±adiÃ³ la columna visible **"Gama"** en la tabla de inventario del TPV (`inventario.py`) para permitir gestiÃ³n manual, y se automatizÃ³ su despliegue a Streamlit Cloud.
- **Auto-registro de Clientes y ConexiÃ³n Web-TPV**: IntegraciÃ³n bidireccional perfeccionada. El sistema en la web busca cruzar clientes no solo por telÃ©fono, sino tambiÃ©n por **Nombre y Apellidos completos**, evitando duplicados y vinculando las cuentas existentes.
- **Checkout, Puntos y Descuentos Automatizados**: 
  - La web aplica las reglas de negocio del TPV fÃ­sico: AcumulaciÃ³n de 1 punto por cada 10â‚¬ de compra y canjeo (1 punto = 0.50â‚¬ descuento, mÃ¡ximo 50% del total).
  - El sistema crea la venta en estado "Deuda" en el historial del TPV, y se coordina un encargo para descontar stock. Si el encargo se cancela por falta de stock fÃ­sico, una devoluciÃ³n en el TPV restaura el inventario.
- **LÃ³gica de EnvÃ­os y Portes Web**:
  - Implementado coste dinÃ¡mico de envÃ­o: EnvÃ­o CercanÃ­a (Santa Cruz/La Laguna) = 5â‚¬; Distancias largas = 10â‚¬; EnvÃ­o Gratuito a partir de 130â‚¬.
  - Los gastos de envÃ­o se desglosan en ticket como un *servicio* con 7% de IGIC, a diferencia de la alimentaciÃ³n animal (exenta).
- **"Candado" del CatÃ¡logo Web**: La web bloquea y oculta estrictamente cualquier producto que no sea de la categorÃ­a "AlimentaciÃ³n seca", "AlimentaciÃ³n hÃºmeda" o "Snack". Todo lo demÃ¡s (champÃºs, collares, etc.) se gestiona en el TPV pero no contamina el catÃ¡logo online.
- **Enriquecimiento de CatÃ¡logo Asistido por IA (Gemini)**:
  - Se implementÃ³ un script automatizado en Python (`enrich_products.py`) para consultar la API de Gemini 2.5 Flash, el cual redacta descripciones comerciales cortas (con emojis y destacando ingredientes clave) para todos los productos que no tenÃ­an informaciÃ³n.
  - MÃ¡s del 50% del catÃ¡logo (330+ productos) ya cuenta con textos Ãºnicos generados, lo que mejora drÃ¡sticamente el SEO y la experiencia de usuario.
- **CorrecciÃ³n de Permisos RLS (Row Level Security) y Mi Cuenta**:
  - Solucionado el problema permanente de "Ficha en revisiÃ³n" en la web. Se creÃ³ un cliente `anonSupabase` dedicado para consultar los perfiles (puntos y mascotas) saltando las restricciones RLS, permitiendo la vinculaciÃ³n instantÃ¡nea web-TPV.
- **Mejoras Visuales de UX Web**:
  - Se modificaron las tarjetas de producto (`ClientCatalog.tsx`) para exponer claramente la Referencia (Ref) del artÃ­culo y la DescripciÃ³n generada por la IA, directamente sobre el precio.
- **DESPLIEGUE A PRODUCCIÃ“N**: La web ha sido subida a la nube (Vercel) con despliegue automÃ¡tico conectado a GitHub, y el dominio final de GoDaddy (`animalariumtenerife.es`) ha sido vinculado exitosamente con certificados SSL.

---


### 3. Mantenimiento y Limpieza de Datos (1 de Julio de 2026)
- **Corrección de la IA de Categorización (Gemini)**:
  - Se parcheó el módulo de Streamlit Cloud para soportar de forma nativa la nueva API de Google, resolviendo el conflicto de dependencias.
  - El filtro de lectura en inventario.py se ha blindado contra valores vacíos (NaN) procedentes del Excel.
- **Limpieza de Vocabulario (Filtros Web)**:
  - Se eliminaron las duplicidades visuales en la web causadas por diferencias de espacios y mayúsculas entre la importación del Excel y el código (ej. *Wet Line* vs *Wet line*, *Todas las Razas* vs *Todas las razas*).
  - Se unificaron los sabores en la base de datos (se fusionó *Mix de carne* en *Mix de carnes*, y *Ternera / Buey* en *Ternera/Buey*).
- **Restauración Estratégica**:
  - Tras una categorización automática de la IA, se utilizó el Excel original como copia de seguridad para inyectar de vuelta las Categorías (Familias) exactas que el usuario había asignado, garantizando que el árbol de navegación de la web mantenga la estructura comercial deseada.
  - Se bloqueó a la IA para que convierta automáticamente las siglas Amv en AMANOVA.

### 4. Expansión del Catálogo y Flujo de Importación (Lenda, Amanova y Atlantic Pet - Julio 2026)
- **Importación del Catálogo de Lenda (132 Productos)**:
  - Se extrajeron con éxito las tarifas en PDF de Lenda 2026 y Lenda Grain Free, inyectándose en Supabase.
  - Se estandarizó la marca a mayúsculas ("LENDA") en todos los registros.
- **Revisión y Consolidación de Amanova y Atlantic Pet**:
  - Se aplicó el nuevo flujo estricto: se exportaron 164 productos de Amanova y 54 de Atlantic Pet a Excel (CSV).
  - El usuario rellenó manualmente los PVPs vacíos y purgó productos descatalogados.
  - El sistema auto-calculó los PVDs faltantes y eliminó permanentemente los productos descartados tanto de la BD como sus fotos del servidor web.
- **Tratamiento Automático de Imágenes (Script Anti-Transparencias)**:
  - Se detectó un problema crítico visual: las fotos originales en formato `.png` o `.webp` (transparentes) generaban fondos negros feos o se mezclaban con el _placeholder_ amarillo del catálogo al pasarlas a la web.
  - Se creó un script de saneamiento visual (`fix_black_backgrounds.py` y equivalentes) que detecta transparencias o falsos JPGs (WebP camuflados), fundiéndolos sobre un fondo 100% blanco puro antes de convertirlos a un `.jpg` real.
- **Corrección Frontend de Fallback**:
  - Se eliminó el "doble fondo" (`backgroundImage` múltiple) en los componentes de React (`ClientCatalog.tsx`, `FeaturedProductsGrid.tsx`, `FloatingProductWidget.tsx`). La web ahora renderiza las fotos sobre un fondo limpio sin asomar la imagen de reemplazo.
- **Normativa de Inteligencia Artificial (`AGENTS.md`)**:
  - A petición de gerencia, se ha instaurado como **ley fundamental** el "Flujo Estándar de Importación de Marcas".
  - Se ha creado el archivo `.agents/AGENTS.md` que obliga a la IA a someter toda nueva importación de datos a una revisión manual en Excel por parte del usuario antes de inyectar en la base de datos o subir imágenes a la nube.

---

## ðŸ§¹ Tareas de Limpieza Realizadas
- Se eliminaron por completo todos los scripts residuales temporales de Python (`relink_prime.py`, `standardize_categories.py`, `import_ownat_v3.py`, etc.) del directorio local para no contaminar el repositorio y dejar el Ã¡rea de trabajo impecable.

---

## ðŸš€ PlanificaciÃ³n para la PrÃ³xima SesiÃ³n (Siguientes Pasos)

**Hito 1: Escaparate Web, Marketing y Responsive Design**
- **AdaptaciÃ³n MÃ³vil (Responsive)**: Escribir las reglas CSS (Media Queries) para que la web se vea perfecta en telÃ©fonos y tablets (menÃº hamburguesa, apilar grid de productos, reducir fuentes del Hero).
- **Banners Rotativos**: Implementar el plan de anuncios rotativos (`PromoBanner.tsx`) en la cabecera del catÃ¡logo y en la pÃ¡gina de inicio, anunciando: 10% primera compra, 10% en cajas enteras de pouch, sistema de puntos, y portes gratis >130â‚¬.

**Hito 2: GestiÃ³n de Web y Delivery (Workflow Avanzado)**
- **Alertas de AntigÃ¼edad**: Implementar un sistema visual que alerte cuando un "Pedido Web" lleve mÃ¡s de 2 dÃ­as atascado sin enviarse o recogerse.
- **GestiÃ³n de Estados y Cancelaciones**: Implementar el estado final "Recibido y Avisado" para los encargos locales, junto con la lÃ³gica de cancelaciÃ³n y borrado seguro.

**Hito 3: Agenda y Periodicidad**
- Avanzar en el sistema de recurrencia y repeticiÃ³n de tareas (diario/semanal/mensual) dentro de la agenda o calendario.

**Hito 4: UX Web y Filtros Finales**
- **SincronizaciÃ³n Web Avanzada**: Modificar la interfaz web para mostrar las opciones secundarias conectadas de forma reactiva, permitiendo una experiencia de compra fluida.
- **Ajustes EstÃ©ticos**: RediseÃ±ar la zona del pie de pÃ¡gina y botones de WhatsApp web.

**Hito 5: Integraciones Futuras (A medio plazo)**
- **Nuevas Marcas**: Cuando se integre Royal Canin o cualquier otra marca, se deberÃ¡ usar **estrictamente** el "Diccionario Maestro" para encajarla mediante scripts de importaciÃ³n (la web lo asimilarÃ¡ instantÃ¡neamente).
- **Pasarela de Pago (Stripe)**: Configurar la pasarela para aceptar cobros directos online.
- **MÃ³dulos Adicionales**: AmpliaciÃ³n hacia categorÃ­as de accesorios o reservas directas de peluquerÃ­a en la tienda online.

