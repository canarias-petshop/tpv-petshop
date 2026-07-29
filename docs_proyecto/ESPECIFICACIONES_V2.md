# Documento Maestro de Especificaciones (Animalarium V2)

**Última Actualización**: Julio de 2026
**Metodología**: Spec-Driven Development (spec-kit)
**Objetivo**: Sentar las bases arquitectónicas, técnicas y de negocio para la reescritura de Animalarium TPV + Web a la Versión 2.0 (Next.js/React + Supabase).

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

---

## 3. Resolución de Problemas Arquitectónicos del Pasado

Al construir la V2 en React/Next.js, solucionaremos de base los problemas que requirieron "parches" en Python:

1. **La "Zona Muerta" Táctil en Tablets**:
   - *Problema anterior*: Los `checkbox` / `toggle` fallaban en iPads/Androids por el bloqueo de teclado.
   - *Solución V2*: Uso de Botones nativos `<button>` de HTML5 y `onClick` manejado por React. Adiós a las desincronizaciones táctiles.

2. **Pérdida de Estado al cambiar de Pantalla**:
   - *Problema anterior*: Cambiar de "Caja" a "Agenda" en Streamlit borraba el carrito.
   - *Solución V2*: Uso de una store global (`Zustand`). El estado `cartStore` y `appointmentStore` persistirá a nivel de aplicación (layout), o incluso en `localStorage`, garantizando cero pérdida de datos.

3. **Duplicación de Fichas (Data Mixing)**:
   - *Problema anterior*: Abrir fichas rápido mezclaba los IDs de los clientes.
   - *Solución V2*: React gestiona el estado a nivel de componente aislado. Cada modal de cliente tendrá su propio contexto (Scope) hermético.

4. **Lentitud en Consultas Complejas Anidadas (Error PGRST200)**:
   - *Problema anterior*: Consultar Pedidos + Proveedores con `.select("*, tabla_externa(*)")` reventaba el caché interno de Supabase/PostgREST.
   - *Solución V2*: GraphQL / Múltiples peticiones asíncronas con `Promise.all()` gestionadas y cacheadas por `React Query`, fusionando los objetos en el cliente sin forzar al backend.

---

## 4. Estructura de Rutas Propuesta (Next.js App Router)

```text
/app
 ├─ (tienda-online)        # E-Commerce Público
 │   ├─ /catalogo
 │   ├─ /carrito
 │   └─ /mi-cuenta
 ├─ (tpv-interno)          # Dashboard Privado (Protegido por Auth Guard)
 │   ├─ /tpv               # Caja (React POS Interface)
 │   ├─ /agenda            # Calendario Drag & Drop (FullCalendar)
 │   ├─ /crm               # Clientes y Mascotas
 │   ├─ /inventario        # Tablas de datos rápidas (Ag-Grid / TanStack Table)
 │   └─ /facturacion
 └─ api                    # Serverless Functions (Next.js API Routes)
     ├─ /verifactu         # Generación de Hashes y Facturas
     └─ /webhooks          # Sincronización
```

---

*Este documento será la referencia obligatoria a leer antes de crear componentes o modificar lógica en el nuevo repositorio V2.*
