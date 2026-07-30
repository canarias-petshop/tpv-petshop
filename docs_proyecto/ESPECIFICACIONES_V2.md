# Documento Maestro de Especificaciones (Animalarium V2)

**Última Actualización**: 30 de Julio de 2026  
**Metodología**: Spec-Driven Development (spec-kit)  
**Objetivo**: Sentar las bases arquitectónicas, técnicas y de negocio para la reescritura de Animalarium TPV + Web a la Versión 2.0 (Next.js/React + Supabase).

**Handoff de avances recientes (obligatorio):** `docs_proyecto/GUIA_V2_AVANCES_2026-07-30.md`

---

## 1. Arquitectura Base y Stack Tecnológico (V2)

### 1.1 Backend y Base de Datos (Se mantiene intacto)
- **Proveedor**: Supabase (PostgreSQL).
- **ORM / Conexión**: Supabase JS Client (`@supabase/supabase-js`).
- **Autenticación**: Supabase Auth (Email, Teléfono).
- **Seguridad**: Row Level Security (RLS) habilitado. Se requerirá un cliente `supabaseAdmin` (Service Role) para bypass en rutas específicas del servidor (ej. renderizado del catálogo público).

### 1.2 Frontend y Framework (Nuevo)
- **Framework**: Next.js 15+ (App Router).
- **UI / Componentes**: React, TailwindCSS, shadcn/ui (para componentes nativos rápidos y accesibles).
- **Gestión de Estado Global**: Zustand o Redux Toolkit (crucial para evitar los cuelgues y pérdida de memoria que sufría Streamlit al cambiar de pestañas en el TPV).
- **Data Fetching & Caché**: React Query (`@tanstack/react-query`) para consultas en tiempo real y revalidación de caché (sustituyendo a `@st.cache_data`), lo que evitará los errores `PGRST200` de consultas complejas anidadas.

### 1.3 Estructura de Repositorio
- El proyecto V2 vivirá en un **repositorio de GitHub independiente** (`animalarium-v2`).
- Esto asegura aislamiento total del código de producción actual en Python, evitando romper la tienda física durante el desarrollo.
- Las reglas de negocio se contrastan contra el código vivo de `tpv-petshop` + Compendio + esta guía.

---

## 2. Reglas de Negocio Estrictas (Fidelidad Absoluta)

Cualquier desarrollo de la V2 debe respetar escrupulosamente estas lógicas ya validadas:

### 2.1 Diccionario Maestro de Catálogo (Filtros Universales)
- **Edades**: Cachorro / Kitten, Adulto, Senior, Todas las edades.
- **Tamaños**: Mini / Pequeño, Mediano, Grande, Gigante, Todas las Razas.
- **Necesidades**: Esterilizado, Control de Peso, Sensible / Digestivo, Hipoalérgico, Urinario, Renal, Bolas de Pelo, Articulaciones, Pelo Blanco, Paladares Exigentes.
- **Proteínas (Sabores)**: Pollo, Salmón, Cordero, Pato, Pavo, Atún, Cerdo, Ternera/Buey, Conejo, Ciervo, Jabalí, Pescado, Mix de Carnes.
- *Regla Técnica*: La UI de la V2 debe forzar selectores cerrados (`<select>` o Dropdowns) al editar inventario para evitar errores tipográficos y discrepancias de mayúsculas (ej. "Wet line" vs "Wet Line").

### 2.2 Descomposición de Stock y Redondeo
- **Multipacks**: Cajas enteras (ej. 12x85gr) se descomponen a unidades sueltas con sufijo `-UD`.
- **Cálculo Matemático de PVP de Unidades**: Redondeo comercial al alza en tramos de 5 céntimos: `Math.ceil(valor * 20) / 20`.
- **Prohibición Total de Decimales en Stock**: Las variables de stock deben forzarse siempre a `integer`. `parseInt(stock, 10)` antes de enviar a Supabase.

### 2.3 Pagos y Fidelización (El Corazón del TPV)
- **Sistemas de Pago Soportados**: Efectivo, Tarjeta, Bizum, Mixto (Efectivo + Tarjeta/Bizum con cálculo automático de cambio).
- **Conversión de Puntos**: 
  - Gasto: 10€ = 1 Punto. (Fórmula: `Math.floor(total / 10)`).
  - Canjeo: 1 Punto = 0.50€ de descuento.
  - Límite de Canjeo: Máximo 50% del importe del ticket.
- **Trazabilidad Fiscal (VeriFactu)**: Cada factura cerrada debe guardar `hash_anterior` y generar un nuevo `hash_actual` basado en SHA-256 inalterable.
- **Pagos Pendientes Exactos**: Los importes pendientes deben validarse y liquidarse con redondeo a 2 decimales, evitando rechazos por ruido de coma flotante cuando el usuario paga exactamente el total visible.

### 2.4 Servicios vs Productos (Separación Crítica)
- **Regla Estricta**: Las consultas de eliminación en masa o edición masiva **JAMÁS** deben tocar registros categorizados como "Servicios" (Peluquería, Clínica, Envío a domicilio).
- Los gastos de envío a domicilio tributan al **7% de IGIC**, mientras que la alimentación tributa al **0%**. El carrito de Next.js debe separar ambas líneas de impuestos al mostrar el checkout.

### 2.5 Agenda y Recursos Humanos (Fichajes)
- **Antispam de Fichajes**: Bloqueo duro de 30 minutos entre el último fichaje y un nuevo intento para un mismo empleado.
- **Confirmación de Salida**: Si ya existe una entrada abierta, el siguiente intento de fichaje tras el bloqueo no debe cerrar el turno de forma silenciosa; debe pedir confirmación explícita de salida.
- **Contexto desde el Cuadrante**: En esa confirmación se debe mostrar la hora de entrada registrada y la hora prevista de salida/tiempo restante leído desde el turno del cuadrante del trabajador.
- **Trazabilidad HR**: Todo fichaje genera un Hash `SHA-256`.
- **Recogida desde Agenda**: En Nueva Cita debe poder activarse/desactivarse la recogida a domicilio con dirección visible. Si está activa al guardar: estado `Servicio de recogida pendiente`, alta en `servicios_recogida` y actualización de `clientes.direccion` + `clientes.servicio_domicilio`.
- **Vacaciones / Ausencias bloquean huecos**: Los bloqueos de RRHH (`agenda_bloqueos` con `bloquea_agenda`) y turnos `vacaciones`/`ausencia`/`baja`/`libre` **no** deben ofrecer slots de peluquería. Lógica de referencia: `core_agenda.py` (Agenda + CRM).

### 2.6 Marketing (TPV actual → requisitos a preservar en V2)
- Calendario `marketing_plan` con textos publicables (`contenido_detallado`) y presupuestos por canal.
- Objetivos `marketing_objetivos` con KPI/meta/`valor_actual` (sync desde TPV en curso en rama local; V2 puede nativizarlo).
- Presupuesto mensual repartible (Ads IG/Meta, Google, cartelería); WhatsApp operativo puede seguir siendo 0 € si es envío manual.
- Talleres `eventos_talleres` en fin de semana (sáb o dom) + asistentes.
- Referencia operativa H2 2026: `docs_proyecto/MARKETING_H2_2026_Y_SIGUIENTE.md`.

### 2.7 Tareas y Mantenimiento de Material (NUEVO — portar a V2)
Submódulo **independiente** (no reutilizar genéricamente `tareas_plannings` / `tareas_duenos`).

**Tablas:** `mantenimiento_materiales`, `mantenimiento_planes`, `mantenimiento_ejecuciones`, `mantenimiento_movimientos`.  
**DDL:** `scripts/sql_mantenimiento_material.sql`.  
**Lógica:** `core_mantenimiento.py`.

**Comportamiento:**
- Alta de materiales (máquinas, cuchillas, bañeras, cepillos, zonas, etc.).
- Planes con frecuencias: Diaria, Semanal, 2×semana, Cada 15 días, Mensual, Cada 3 meses, Cada 6 meses, Puntual.
- Pendientes **persisten** (`Pendiente`/`Atrasado`) hasta marcar **Hecho**; entonces se recalcula la próxima fecha.
- Movimientos: Sale a afilar / reparación / **mantenimiento**, Vuelve de taller, Incidencia, Anotación.
- Calendario propio + **resumen** en el calendario general de tareas.
- Detalle completo: `docs_proyecto/GUIA_V2_AVANCES_2026-07-30.md` §2.

### 2.8 Mensajería automática
- **Aparcada.** Recordatorios = manuales. Ver `DECISION_MENSAJERIA_AUTOMATICA.md`.

---

## 3. Resolución de Problemas Arquitectónicos del Pasado

Al construir la V2 en React/Next.js, solucionaremos de base los problemas que requirieron "parches" en Python:

1. **La "Zona Muerta" Táctil en Tablets**:
   - *Problema anterior*: Los `checkbox` / `toggle` fallaban en iPads/Androids por el bloqueo de teclado.
   - *Solución V2*: Uso de Botones nativos `<button>` de HTML5 y `onClick` manejado por React.

2. **Pérdida de Estado al cambiar de Pantalla**:
   - *Problema anterior*: Cambiar de "Caja" a "Agenda" en Streamlit borraba el carrito.
   - *Solución V2*: Store global (`Zustand`) para carrito, citas, etc.

3. **Duplicación de Fichas (Data Mixing)**:
   - *Problema anterior*: Abrir fichas rápido mezclaba los IDs de los clientes.
   - *Solución V2*: Estado aislado por componente/modal.

4. **Lentitud en Consultas Complejas Anidadas (Error PGRST200)**:
   - *Problema anterior*: Embeds PostgREST profundos reventaban caché.
   - *Solución V2*: Varias peticiones + `React Query`, merge en cliente.

5. **HTML de calendarios en Streamlit**:
   - *Problema*: `st.markdown` a veces muestra HTML crudo.
   - *Solución V2*: componentes React / FullCalendar nativos.

---

## 4. Estructura de Rutas Propuesta (Next.js App Router)

```text
/app
 ├─ (tienda-online)
 │   ├─ /catalogo
 │   ├─ /carrito
 │   └─ /mi-cuenta
 ├─ (tpv-interno)
 │   ├─ /tpv
 │   ├─ /agenda
 │   ├─ /crm
 │   ├─ /inventario
 │   ├─ /facturacion
 │   ├─ /personal
 │   ├─ /tareas
 │   │    ├─ /calendario
 │   │    ├─ /ficha
 │   │    ├─ /notas
 │   │    └─ /mantenimiento-material
 │   └─ /marketing
 └─ api
     ├─ /verifactu
     └─ /webhooks
```

---

*Referencia obligatoria antes de crear componentes en V2. Completar con `GUIA_V2_AVANCES_2026-07-30.md`.*
