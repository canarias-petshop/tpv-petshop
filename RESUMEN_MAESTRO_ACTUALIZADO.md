# Resumen Maestro Actualizado - TPV y E-Commerce Animalarium
**Fecha de última actualización**: 17 de Agosto de 2026

Este documento centraliza todos los avances, arquitecturas y módulos del ecosistema completo de Animalarium (TPV Físico + Tienda Web). Es el punto de partida **obligatorio** para retomar el proyecto en futuras sesiones.

> Para portar a **Animalarium V2**: leer también `docs_proyecto/GUIA_V2_AVANCES_2026-07-30.md` (esp. **§7 CI/QA** y **§8 reuniones/CRM**) y `docs_proyecto/ESPECIFICACIONES_V2.md` (§2.9–2.11).

> [!CAUTION]
> **NORMA ESTRICTA: PRODUCTOS vs SERVICIOS**
> Una cosa son los productos (piensos, accesorios) y otra muy distinta son los servicios (peluquería, clínica).
> Si el usuario ordena eliminar o modificar una marca concreta o un grupo de artículos en el contexto de "productos", **JAMÁS** debes alterar los registros que pertenezcan a "servicios" (aunque compartan tabla en la base de datos o utilicen la marca 'Genérico' u otra para categorizarse).
> **No asumas ni interpretes nada.** Verifica siempre si la acción puede afectar a los servicios antes de ejecutar un borrado masivo.

---

## 🆕 12–17 de Agosto de 2026 (prod + documentación sellada)

### CRM — Contacto y teléfono alternativo (`1d5e361`)
- En el **Directorio de clientes**, editar solo **Contacto Alt.** / **Tel. Alt.** (o Canal pref.) no disparaba el update: el detector de cambios omitía esas columnas.
- Corregido con `core_crm.fila_cliente_tiene_cambios` (incluye `nombre_dueno_2`, `telefono_2`, `metodo_contacto`).
- Tests: `test_fila_cliente_detecta_contacto_y_tel_alternativo` + `test_actualizar_cliente_contacto_alternativo`. En `main` / Streamlit Cloud.

### Proyectos — Reuniones de Equipo por rango (`c5ff197`)
- Antes: una sola fecha; bloquear varios días era uno a uno.
- Ahora: **Desde el día / Hasta el día**; se inserta un `agenda_bloqueos` por cada día (mismas horas, empleado y flag de bloquear agenda).
- Lógica: `core_proyectos.construir_bloqueos_rango` · UI `proyectos_eventos.py`. Tests en `tests/test_proyectos.py`.

### Marketing H2 (`6577d07`)
- Textos H2 enriquecidos listos para aplicar sin reseeding de datos.

### Estado operativo
- TPV producción = `main`. No hay sprint abierto. Mensajería automática sigue **aparcada**.

---

## 🆕 1 de Agosto de 2026 (CI + smoke CRM / handoff V2)

### QA técnico sobre `main`
- Suite local Docker: **93+ tests en verde** + smoke sync KPIs.
- Lógica CRM de guardado (cliente / mascota / encargo) cubierta por smoke de ida y vuelta.
- Un rojo puntual de GitHub Actions en un commit de **docs** no se interpretó como fallo de producción; se endureció el CI.

### CI endurecido (`dee59ae`)
- Esperar schema real (`/clientes?select=id&limit=1`) antes de pytest.
- `python -m pytest` + permisos de checks para el reporter.
- Smoke CRM: `tests/test_crm.py::test_smoke_guardado_cliente_mascota_encargo`.

### Documentación V2
- `GUIA_V2_AVANCES_2026-07-30.md` §7 — contratos de guardado y lecciones de CI.
- `ESPECIFICACIONES_V2.md` §2.9–2.10 — requisitos obligatorios al portar CRM/QA a Next.js.

### Nota operativa tienda
- Si un puesto “no guarda” encargos/clientes y otro sí con el mismo `main`: priorizar caché/sesión/red frente a cambiar `core_crm`.

---

## 🆕 Cierre 30–31 de Julio de 2026 (producción validada)

### Despliegue a `main` + verificación usuario
- Merge a `main` / push remoto: mantenimiento material, sync KPIs + CI, bloqueo vacaciones agenda/CRM, docs V2.
- SQL `mantenimiento_*` aplicado en **Supabase** por el usuario.
- **Validado en producción** por el usuario (31 jul): ficha clínica (cierre/guardado), módulo de mantenimiento de material y operativa general OK.

### Hotfixes post-despliegue
- **Agenda `UnboundLocalError`**: import local de `aplicar_bloqueos_a_turnos` dentro de `render_pestana_agenda` → corregido (import solo a nivel módulo). Commit `d7e4084`.
- **Ficha clínica**: `aplicar_descuentos_fidelidad` sacado del bucle al guardar; mensaje de error si falla el update a Supabase.
- **Cron KPIs 23:05**: primera noche disparó pero `Connection refused` (cron sin `API_URL`). Fix entrypoint inyecta `API_URL=http://animalarium-api:3000` (`fb77ef8`); imagen Docker rebuild 31 jul. Cron = **solo local**; en nube el sync es el **botón manual**.

### Mantenimiento de Material (módulo Tareas) — prod
- Submódulo **Tareas → 🛠️ Mantenimiento Material**.
- Tablas: `mantenimiento_materiales`, `mantenimiento_planes`, `mantenimiento_ejecuciones`, `mantenimiento_movimientos`.
- Frecuencias: diaria, semanal, 2×semana, 15 días, mensual, 3m, 6m, puntual.
- Pendientes hasta marcar Hecho; movimientos de taller (incl. Sale a mantenimiento).
- Spec V2: `ESPECIFICACIONES_V2.md` §2.7 + `GUIA_V2_AVANCES_2026-07-30.md`.

### Agenda: vacaciones / ausencias bloquean huecos
- `core_agenda.aplicar_bloqueos_a_turnos` unifica Agenda y CRM.

---

## 🆕 Cambios (27-29 de Julio de 2026)

### Agenda / Recogida a Domicilio desde Nueva Cita
- **Cuadro de recogida en el gestor de citas (`agenda.py`)**: Al seleccionar una mascota (o en alta rápida) aparece un control compacto de **Recogida a domicilio** con la dirección del cliente si ya existe y un botón Activar/Desmarcar **solo para esa cita**.
- **Misma experiencia en CRM (`crm.py` / `core_crm.py`)**: El atajo **Agendar Cita Inteligente** de la ficha de mascota replica el mismo comportamiento.
- **Helper robusto `registrar_recogida_desde_cita`**: Al guardar con recogida activa se consulta de nuevo mascota/cliente en BD, se inserta en `servicios_recogida` y se actualiza `clientes.direccion` + `servicio_domicilio=true`. Corrige el caso en el que el cliente no tenía aún dirección ni flag activo.
- **UI compacta**: La info de tiempo medio/peluquero preferido va en expander plegado; la recogida queda en una línea con botones cortos.
- **Al guardar con recogida activa**:
  1. La cita entra al directorio con estado **`Servicio de recogida pendiente`**.
  2. Se crea automáticamente el registro en **`servicios_recogida`**.
  3. Se actualiza la ficha del cliente (dirección + recogida activa).
- **Al desmarcar recogida en una cita**: no se crea servicio de recogida y la cita queda como `Pendiente` normal; no se apaga el flag permanente del cliente solo por desmarcar “esta vez”.
- **Tests**: Añadidos/verificados tests de CRM (cita con recogida + actualización de ficha), facturación (pagos exactos) y personal (fichaje). Suite local: **todos en verde**.

### Facturación de Compras y Pagos a Proveedores
- **Validación fiable de borradores (`facturacion.py`)**: Corregido el flujo de *Facturas Recibidas* para que al pulsar **"Validar documento y actualizar stock"** el documento salga realmente de `Borrador` y pase a `Recibido` (o `Pagado` si ya no queda pendiente), limpiando además la caché visual para evitar que la tabla siguiera mostrando el estado antiguo.
- **Separación correcta Borrador vs Stock**: Queda reforzada la regla de negocio de que una factura recibida en `Borrador` **puede crear o enlazar artículos**, pero **no suma stock** hasta la validación. Si se elimina un borrador, solo se borra el documento; el stock no se toca.
- **Borrado seguro de compras/documentos**: Ajustada la eliminación de compras y documentos contables para que solo resten stock cuando el documento ya estaba validado (`Recibido`, `Pagado`, etc.). Los borradores ya no deshacen stock por error.
- **Pagos pendientes con céntimos exactos**: Resuelto el bug de redondeo/`float` que impedía pagar importes exactos como `177,01 €`, obligando a introducir un céntimo menos. Ahora las comparaciones y liquidaciones se redondean a 2 decimales con tolerancia segura.

### Recursos Humanos / Fichajes
- **Confirmación inteligente de salida (`personal.py`)**: Mejorado el flujo de fichaje para que, si un trabajador ya tiene una entrada abierta y vuelve a introducir su PIN pasado el bloqueo de 30 minutos, el sistema **no fiche la salida directamente**. En su lugar muestra un aviso confirmando que va a registrar una salida.
- **Lectura del cuadrante en tiempo real**: El aviso de salida informa de la **hora de entrada registrada**, del tiempo ya trabajado y de cuánto queda (o cuánto se ha pasado) respecto a la **hora prevista de salida según el cuadrante del trabajador**. Esto reduce los cierres accidentales de jornada por despiste.

---

## 🆕 Últimos Cambios (14-17 de Julio de 2026)


### Integración de IA para Composición de Productos
- **Script Autoadministrado (`generar_composiciones_ai.py`)**: Desarrollado un motor de IA usando Gemini que escanea el catálogo, busca las composiciones de los productos en internet y las inyecta en formato HTML estilizado dentro de Supabase.
- **Deduplicación Inteligente**: El motor detecta productos idénticos que sólo varían en peso (ej. "Saco 2kg" vs "Saco 10kg") para hacer una única llamada a la IA, ahorrando tiempo y peticiones, copiando la misma composición a todos.
- **UI en la Web (`ClientCatalog.tsx`)**: Implementado un botón "ℹ️ Ver Composición" en las tarjetas de la tienda online que despliega un popup (Modal) estilizado para que los clientes lean los ingredientes y características nutricionales del producto.

### Mejoras de Búsqueda
- **Buscador Inteligente Multi-palabra**: Se actualizaron los buscadores del TPV (productos y servicios) para que soporten búsqueda libre. Ahora el usuario puede escribir palabras desordenadas y en minúsculas (ej. "hypoallergenic royal canin") y el sistema dividirá el texto buscando las coincidencias sin importar el orden ni las mayúsculas.

### Resolución Definitiva de Bugs (TPV Tablet)
- **Transformación de Interruptores a Botones Nativos (`tpv.py`)**: Se documentó y resolvió una incompatibilidad estructural entre el bloqueador de teclado táctil (Javascript en `app.py`) y los componentes de interruptor (`st.toggle` / `st.checkbox`) en navegadores de tablet (Chrome/Safari), los cuales generaban una "zona muerta". La solución definitiva fue erradicar los interruptores y reemplazarlos por **Botones Interactivos con Memoria de Estado** en `st.session_state`. Ahora, funciones críticas como "Envío a Domicilio" y "Canjear Puntos" utilizan la sólida API de botones de Streamlit, garantizando un 100% de respuesta táctil en Android/iOS.
- **Altura Dinámica de Tablas**: Se solucionó un cuelgue fatal (`ResizeObserver`) en Streamlit Cloud provocado por iframes superpuestos al calcular matemáticamente y en vivo la altura del carrito de la compra en función del número de artículos (`len(df_car)`), eliminando márgenes invisibles.

---

## 🆕 Cambios Anteriores (7-13 de Julio de 2026)


### Sincronización TPV ↔ Web (Perfiles y Encargos)
- **Solución "Ficha en revisión"**: Se corrigió un bloqueo crítico en la web que ocurría cuando existían múltiples clientes físicos vinculados al mismo `auth_user_id` en Supabase. Ahora la API selecciona automáticamente la ficha más reciente (`.order('created_at').limit(1).single()`).
- **Limpieza de Vinculaciones Antiguas**: La API de `link/route.ts` ahora desvincula automáticamente las fichas antiguas y duplicadas al establecer un nuevo enlace, previniendo cuelgues futuros.
- **Edición de Perfil en la Web**: Implementado un nuevo endpoint (`api/user/update/route.ts`) y un formulario en la pestaña *Mi Cuenta* (`mi-cuenta/page.tsx`) que permite a los usuarios modificar su teléfono, nombre y dirección desde la web, reflejándose al instante en el CRM del TPV.
- **Edición Segura de Encargos en TPV (`crm.py`)**: Corregido un grave error lógico (conflicto de tipos `str` vs `int`) que causaba la eliminación accidental de *todos* los encargos al pulsar "Guardar Cambios". Ahora las modificaciones se guardan con total seguridad.
- **Auto-sincronización Telefónica**: Si se edita el teléfono de un cliente directamente en un encargo del TPV, el sistema detecta el cambio y actualiza el teléfono maestro en la tabla central `clientes` automáticamente.

### Infraestructura y Estabilidad
- **Revisión de Cuotas de Supabase**: Se verificó una alerta preventiva de límites de uso de Supabase ("Grace period over"). Se comprobó empíricamente mediante los informes de facturación que el uso de la Base de Datos está en parámetros óptimos (7% de tamaño máximo, <1% de ancho de banda). La alerta se originó por el consumo del código antiguo no optimizado; las recientes integraciones de caché han mitigado el problema.
- **(Pendiente) Congelador de Memoria Global**: Se ha diseñado teóricamente un "Escudo de Memoria" para evitar que Streamlit borre el progreso (como el recuento de caja o la creación de citas) al cambiar de sección con el menú desplegable. El diseño se basa en interceptar y volcar `st.session_state` al inicio de `app.py`. A la espera de ser testeado tras revisar las pantallas afectadas.

## 🆕 Cambios Anteriores (5-6 de Julio de 2026)

### Limpieza y Deduplicación de Datos
- **Deduplicación de Proveedores**: Consolidados de 22 a 18 proveedores, eliminando duplicados por variaciones ortográficas (mayúsculas/minúsculas, espacios extra, tildes). Se migraron las relaciones de `productos_proveedores` y `compras` antes de eliminar los duplicados.
- **Deduplicación de Productos**: Identificados y fusionados productos duplicados. Los genéricos `CA-007` y `CA-008` se fusionaron con los productos OWNAT correctos `OW-020` y `OW-021`.
- **Limpieza Catálogo Amanova**: Eliminados 5 clones "12Ud" que se habían autogenerado, conservando los productos originales en caja. 115 productos de la Tarifa 2025 comprobados, sin faltar ninguno.
- **Propagación Borrador→Inventario (`facturacion.py`)**: Modificada la lógica del botón "🚀 VALIDAR DOCUMENTO" (línea ~1056) para que al confirmar un borrador de factura, cualquier cambio manual realizado en Descripción, Ref/EAN, IGIC%, Base Ud o PVP se propague automáticamente a la tabla `productos` del inventario.

### Generación Masiva y Precios
- **Detección Automática de Multipacks**: Escaneados 142 productos tipo caja/pack (patrones como `12x85g`, `Caja 12 ud`, `Pack 6`).
- **Creación de 134 Unidades Nuevas**: Se crearon automáticamente los productos unitarios correspondientes con el sufijo `-UD` en el SKU y `(Unidad)` en el nombre.
- **Regla de Redondeo Comercial Estricta**: Implementado redondeo al alza en tramos de 5 céntimos (`math.ceil(valor * 20) / 20`), pero **ÚNICAMENTE** aplicado a unidades sueltas que se generan a partir de cajas (Ej. sobres, pouches de gatos de Ownat Wetline o Amanova). Los PVPR de los fabricantes para piensos y otros productos se mantienen al céntimo original.
- **Actualización Exacta de Amanova y Ownat**: Re-cálculo de unidades desde cajas corrigiendo un error donde se dividían cajas de 24 como si fuesen de 12. Precios PVP de pouches unitarios ajustados a la perfección (ej. 1.45€ Amanova, 1.85€ Ownat), respetando el PVP exacto de las cajas cerradas (ej. 22.08€ Ownat).

### Bugfix: Herramienta "Abrir Caja / Saco" (`inventario.py`)
- Corregido el error `invalid input syntax for type integer: "5.0"` al traspasar stock de cajas a unidades. El problema era que Python enviaba los valores de stock como `float` (decimal) y la base de datos Supabase los rechazaba porque la columna `stock_actual` espera un entero.
- Se convirtieron los cálculos de stock a `int()` sin tocar los UUIDs de los productos.

### SEO, Arquitectura Web y RLS
- **Solución RLS en Supabase (Web)**: Corregido un fallo crítico donde el catálogo web devolvía `0 productos` en producción. Se implementó `supabaseAdmin` en `page.tsx` y en las rutas de API internas para realizar las consultas de lectura (`SELECT`) ignorando las políticas de seguridad de nivel de fila (RLS), garantizando la disponibilidad del inventario público.
- **Sitemap XML**: Confirmado el envío de `sitemap.xml` a Google Search Console con las rutas: `/`, `/catalogo`, `/contacto`, `/aviso-legal`, `/privacidad`, `/terminos`.
- **Verificación de Propiedad**: Completada la verificación del dominio `animalariumtenerife.es` en Google Search Console.
- **Redirecciones 301 (`next.config.ts`)**: Configuradas redirecciones permanentes para las URLs antiguas de la web anterior (Kit Digital).
- **Favicon Personalizado y Transparencias**: Creado `LOGO.png` transparente y `icon.jpg` configurado como el nuevo favicon estándar en todas las ventanas y resultados de Google.

---

## 🏆 Lo que se ha conseguido hasta hoy (Historial de Éxitos)

### 1. Sistema TPV (Tienda Local)
- **Cobro Rápido (Tickets)**: Solucionado el problema de duplicidad de extras en los tickets. Al cobrar una ficha clínica, el ticket desglosa el servicio general y el extra en líneas separadas sin duplicar el total.
- **Gestión de Fichas (CRM)**: Corregido el error ("Data Mixing") que mezclaba datos de clientes y mascotas al abrir varias fichas simultáneamente.
- **Inventario Avanzado**:
  - Se han añadido nuevas columnas visuales y en base de datos para: `fecha_caducidad`, `stock_minimo`, `cantidad_reponer` y `marca`.
  - En la vista del inventario, los campos de categorización (Edad, Tamaño, etc.) utilizan selectores cerrados (`SelectboxColumn`) para evitar erratas tipográficas y asegurar que los filtros de la web cuadren.
- **Herramienta de Desempaquetado (TPV)**:
  - Creada la utilidad Traspaso de Cajas a Unidades en el inventario. Permite romper stock de un producto "Master/Caja" y sumarlo automáticamente al producto individual, calculando unidades internas.
  - Corregido el bug de conversión de tipos (float→int) que impedía el traspaso.
- **CRM Encargos y Delivery**: 
  - Rediseñado en dos pestañas claras: 🏪 Encargos de Tienda y 🌐 Pedidos Web.
  - Se habilitó la eliminación dinámica directo de filas en las tablas de encargos.
  - Se añadió un botón "🚚 Crear Servicio a Domicilio" para convertir encargos web directamente en la hoja de reparto.
- **Reparto desde Caja (TPV)**: Automatizada la creación de Servicios a Domicilio desde el Cobro, rellenando automáticamente la dirección guardada del cliente al seleccionarlo.
- **Centro de Recordatorios Inteligente**:
  - La tabla de confirmaciones del día siguiente ahora es editable en vivo y posee una columna independiente ("🔔 Aviso") que guarda en *observaciones* si se ha mandado el WhatsApp.
  - **Envío = manual (1 clic a WhatsApp).** La automatización por API (WA Business / email / cron) está **aparcada** a la espera de decidir alcance; ver `docs_proyecto/DECISION_MENSAJERIA_AUTOMATICA.md`.
- **Optimización de Rendimiento (Caching)**: Aplicado el sistema de `Smart Caching` de Streamlit en todas las pantallas. La base de datos no se satura al cambiar de pestaña.
- **Sincronización en Caliente (TPV ↔ CRM)**: Si al cobrar un usuario da de alta un cliente nuevo en el CRM, el selector de clientes de la Caja se refresca automáticamente *sin vaciar el carrito*.

### 2. Tienda Online (E-Commerce) y Estandarización de Base de Datos
- **El "Diccionario Maestro" Universal (¡GRAN LOGRO!)**: 
  - Se reescribieron las entrañas de los más de 400 productos en Supabase (Amanova y OWNAT) para que dejen de usar el vocabulario del fabricante (Puppy vs Junior, Mini vs Small) y utilicen un **Estándar Universal** fijado por la tienda.
  - *Edades*: Cachorro / Kitten, Adulto, Senior, Todas las edades.
  - *Tamaños*: Mini / Pequeño, Mediano, Grande, Gigante, Todas las Razas.
  - *Necesidades*: Esterilizado, Control de Peso, Sensible / Digestivo, Hipoalérgico, Urinario, Renal, Bolas de Pelo, Articulaciones, Pelo Blanco, Paladares Exigentes, Ninguna.
  - *Sabores Principales*: Limpios y puros (Pollo, Salmón, Cordero, Pato, Pavo, Atún, Cerdo, Ternera/Buey, Conejo, Ciervo, Jabalí, Pescado, Mix de Carnes).
- **Importación Inteligente y Creación de Multipacks**: 
  - Desarrollada la lógica para leer las tarifas PDF del proveedor y detectar "Cajas Multipack" (Ej: 12x85gr).
  - El sistema crea automáticamente **dos productos por cada caja**: el multipack entero y la unidad suelta, dividiendo a la perfección los costes y redondeando precios al alza en tramos de 5 céntimos.
- **Fusión y Enlazado de Imágenes Extremo (Fuzzy Matching)**: 
  - Se completó la indexación de todas las gamas (Amanova completa, y OWNAT: Classic, Prime, Ultra, Just, Care, Hypoallergenic). 
  - El script cruzó inteligentemente los nombres de base de datos con las fotos locales renombradas manualmente, superando casi 800 imágenes perfectas de alta calidad.
  - Nomenclaturas estandarizadas (ej. marca `OWNAT` siempre en mayúsculas en DB). Se han limpiado y eliminado productos descatalogados.
- **Promociones Automáticas Web**:
  - Implementado descuento automático del 10% en productos que se venden por cajas enteras (pouches, latas).
  - La web muestra ahora una etiqueta (badge rojo) de "-10% DTO" y el precio original tachado tanto en el catálogo como en el carrito.
- **Flujo de Pago (Checkout) Optimizado para WhatsApp**:
  - Se eliminó la necesidad de pagar por transferencia inmediata.
  - El sistema asume que la tienda usará "Paygold / Enlace de Pago" (Dojo, CaixaBank, Cajasur) tras confirmar el stock. 
  - La pasarela ofrece opciones amigables: "Tarjeta (Enlace por WhatsApp)", "Bizum (Confirmación por WhatsApp)" y "Pago al recoger".
- **Histórico de Pedidos en Perfil de Usuario**:
  - Añadida la sección "Histórico de Pedidos" en Mi Cuenta, donde los usuarios web pueden revisar sus compras online y ver si están Pendientes o Entregados, conectando directamente con encargos_clientes.
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
- **Corrección Estructural Checkout (Bugfixes)**:
  - Se arregló un fallo silencioso de Supabase donde ventas_historial rechazaba inserciones por columnas obsoletas (cliente_fidel).
  - Se modificó la API de Checkout para que TODOS los pedidos web caigan en "Pedidos Web" (encargos_clientes) y, si son a domicilio, se clonen inteligentemente a pedidos_domicilio para el repartidor.
- **DESPLIEGUE A PRODUCCIÓN**: La web ha sido subida a la nube (Vercel) con despliegue automático conectado a GitHub, y el dominio final de GoDaddy (`animalariumtenerife.es`) ha sido vinculado exitosamente con certificados SSL.

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

### 5. Página de Contacto y SEO (5 de Julio de 2026)
- **Página de Contacto** (`/contacto`): Creada con la dirección (C. José Hernández Alfonso, 26), teléfono (922 065 170), WhatsApp (672 481 295) y enlace a Google Maps.
- **Páginas Legales**: Creadas las páginas de Aviso Legal, Privacidad y Términos y Condiciones.
- **SEO Metadata**: Implementados títulos, meta descriptions y canonicals en `layout.tsx` para todas las páginas.
- **Sitemap XML**: Generado dinámicamente con `sitemap.ts`, enviado y verificado en Google Search Console.
- **Redirecciones 301**: Configuradas en `next.config.ts` para redirigir todas las URLs de la web antigua del Kit Digital a las nuevas páginas equivalentes.
- **Logo Transparente y Favicon**: Logo sin fondo blanco para la navegación y favicon circular personalizado con las huellitas de la marca.

---

## 🧹 Tareas de Limpieza Realizadas
- Se eliminaron por completo todos los scripts residuales temporales de Python (`relink_prime.py`, `standardize_categories.py`, `import_ownat_v3.py`, etc.) del directorio local para no contaminar el repositorio y dejar el área de trabajo impecable.

---

## 🚀 Planificación a Medio y Largo Plazo (Fase de Maduración)

Tras haber completado gran parte de los hitos operativos iniciales (Diseño Responsive, Banners Web, Alarmas de Encargos, Tareas/Notas de personal, Filtros UX y Pasarela de Pago Virtual TPV), el proyecto entra en una nueva fase orientada a la independencia, la fiabilidad legal y la futura comercialización del software:

**Hito 1: Independencia de Infraestructura (Entorno Local)**
- **Servidor Local en Tienda**: Abandonar la dependencia exclusiva de Supabase en la nube para la operativa diaria.
- **Base de Datos Propia**: Montar y configurar PostgreSQL (u otra solución) en un ordenador/servidor físico en la tienda, logrando que el TPV funcione en una red local de forma rápida y autónoma, manteniendo sincronización secundaria con la web.

**Hito 2: Cumplimiento Legal (VeriFactu) y Contabilidad**
- **Integración VeriFactu**: Finalizar y pulir el sistema de generación de hash y envío de facturas para cumplir con la normativa de la Agencia Tributaria. (Nota: existe código base antiguo que debe ser reactivado y validado).
- **Módulo de Contabilidad**: Consolidar y cerrar los procesos pendientes del módulo contable del TPV.

**Hito 3: Estabilidad y Testing (Preparación Comercial)**
- **Pruebas Automatizadas (Tests)**: Desarrollar baterías de pruebas (unitarias y de integración) para asegurar la solidez del programa, garantizando que futuras modificaciones no rompan los flujos de caja o inventario. Fundamental para dar un buen soporte si el software se comercializa.

**Hito 4: Documentación / Especificaciones V2**
- Compendio + Resumen Maestro + `ESPECIFICACIONES_V2.md` + handoff **`GUIA_V2_AVANCES_2026-07-30.md`** (incluye mantenimiento de material y vacaciones→agenda).
- Usar esa guía al continuar módulos en el repo `animalarium-v2`.

**Hito 5: Refactorización y Optimización (Fase 2)**
- **Código Limpio**: Con el respaldo de los tests y las especificaciones, reestructurar el código existente para eliminar deuda técnica, optimizar consultas, mejorar el rendimiento global y aplicar prácticas modernas.

**Hito 6 (aparcado): Mensajería automática**
- Valorar en el futuro: seguir manual / solo email marketing / recordatorios WA por API / paquete completo.
- **No es trabajo activo.** Detalle: `docs_proyecto/DECISION_MENSAJERIA_AUTOMATICA.md`.

**Hito 7: Plan marketing H2 2026 (datos 29 jul; verificación TPV 30 jul 2026)**
- Plan ago–dic: textos copy/paste, ~3 IG/sem, 150 €/mes ≈ 750 € H2 (IG Ads / Google / cartelería), talleres sáb/dom, objetivos manuales.
- UI Plan Maestro: **TEXTO PARA PUBLICAR** + calendario de títulos (código en `main`).
- **Datos verificados en prod:** objetivos, ~750 €, campañas especiales, canales. Mayo–julio del plan no se borraron.
- Si Streamlit Cloud muestra UI antigua (“Vista de Proyección…”): Reboot/Redeploy.
- Continuación (automatizar KPIs en local): `docs_proyecto/MARKETING_H2_2026_Y_SIGUIENTE.md`.

**Hito 8: Mantenimiento de Material — cerrado en prod (31 jul 2026)**
- Submódulo en Tareas; tablas en local y Supabase; validado en Streamlit Cloud.
- Spec V2: `GUIA_V2_AVANCES_2026-07-30.md` §2.
