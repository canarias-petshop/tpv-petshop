# Guía de avances para V2 — 30 jul – 17 ago 2026

**Propósito:** handoff para `animalarium-v2` (u otro chat/agente).  
**Actualización 31 jul:** mantenimiento y sync KPIs (botón) **validados en producción** TPV Streamlit.  
**Actualización 1 ago:** CI endurecido + smoke de guardados CRM en `main`.  
**Actualización 17 ago (sello):** contacto alternativo CRM + reuniones por rango de fechas en `main` / prod. Ver **§8**.

**Leer también (orden):**
1. Este archivo  
2. `docs_proyecto/ESPECIFICACIONES_V2.md`  
3. `docs_proyecto/Compendio_Maestro_Especificaciones.md`  
4. `RESUMEN_MAESTRO_ACTUALIZADO.md`  
5. `docs_proyecto/estado_tareas.md`

**Norma:** primero local, después producción. Productos ≠ Servicios.

---

## 1. Estado del TPV actual (Streamlit) relevante para V2

| Módulo | Estado | Notas para V2 |
|--------|--------|----------------|
| Caja / puntos / pagos | Estable | Reglas en Compendio § parametrización |
| CRM + citas + recogida | Estable en prod | Cascada recogida; smoke ida/vuelta; **Contacto Alt. / Tel. Alt. deben persistir** (ver §8) |
| Agenda huecos | Estable en prod | Vacaciones/ausencias; hotfix import UnboundLocalError |
| Ficha clínica | Estable en prod | Guardado historial validado 31 jul |
| Facturación compras | Estable | Borrador no mueve stock; pagos a 2 decimales |
| RRHH fichajes | Estable | Anti-spam 30 min + confirmación salida |
| Marketing H2 | Prod | Sync KPIs: botón en nube; cron solo Docker local |
| **Reuniones / bloqueos** | **Prod (13 ago)** | Rango Desde/Hasta → un `agenda_bloqueos` por día (§8) |
| **Mantenimiento material** | **Prod (validado 31 jul)** | Tablas en Supabase; portar a V2 |
| QA / CI | En `main` | Esperar schema real + smoke CRM + smoke KPIs (ver §7) |
| Mensajería automática WA/Email | Aparcado | Manual 1 clic |

---

## 2. Nuevo módulo: Mantenimiento de Material (30 jul 2026; prod 31 jul)

### 2.1 Dónde vive en el TPV
- Pestaña **Tareas → 🛠️ 4. Mantenimiento Material**
- Subvistas: Pendientes | Calendario | Materiales y planes | Salidas / taller
- El **Calendario General** de Tareas muestra resumen diario (`🛠️` / `🚨`)

### 2.2 Archivos de referencia (código fuente de verdad)
| Archivo | Rol |
|---------|-----|
| `core_mantenimiento.py` | Frecuencias, proyección de fechas, estados, sync de ejecuciones |
| `mantenimiento_material.py` | UI Streamlit |
| `tareas.py` | Integración pestaña + resumen calendario general |
| `scripts/sql_mantenimiento_material.sql` | DDL (local ya aplicado; **copiar a Supabase cuando se pida**) |
| `tests/test_mantenimiento.py` | Tests de lógica |
| `docker/init-test-db.sql` | Schema CI incluye tablas `mantenimiento_*` |

### 2.3 Modelo de datos (4 tablas)

```text
mantenimiento_materiales
  id, nombre, categoria, ubicacion, activo, notas

mantenimiento_planes
  id, material_id (FK), tipo_mantenimiento, frecuencia_tipo,
  dias_semana (int[] 0=Lun…6=Dom), fecha_inicio,
  ultima_ejecucion, proxima_ejecucion, activo, rol_asignado, notas

mantenimiento_ejecuciones
  id, plan_id (FK), fecha_programada, fecha_realizada,
  estado (Pendiente|Atrasado|Hecho), notas, detalle_tecnico, empleado_id
  UNIQUE(plan_id, fecha_programada)

mantenimiento_movimientos
  id, material_id (FK), tipo_movimiento, fecha, detalle, estado (Abierto|Cerrado)
```

### 2.4 Frecuencias obligatorias
- Diaria  
- Semanal  
- 2 veces por semana (elegir ≥2 días)  
- Cada 15 días  
- Mensual  
- Cada 3 meses  
- Cada 6 meses  
- Puntual (no regenera tras completar)

### 2.5 Tipos de mantenimiento (plan)
Limpieza, Desinfección, Revisión, Afilado, Cambio / Recambio, Mantenimiento técnico, Limpieza a fondo, Otro.

### 2.6 Tipos de movimiento (salidas / taller)
Sale a afilar, Sale a reparación, **Sale a mantenimiento**, Vuelve de taller, Incidencia, Anotación.

### 2.7 Reglas de comportamiento (críticas)
1. Al abrir el módulo se **sincronizan** ejecuciones pendientes según planes activos.  
2. Una tarea de mantenimiento **no desaparece sola**: permanece `Pendiente` / `Atrasado` hasta marcar **Hecho**.  
3. Al marcar Hecho: se guarda fecha_realizada + notas/detalle; se calcula `proxima_ejecucion` con `siguiente_tras_completar`.  
4. Si la fecha programada ya pasó y sigue abierta → estado `Atrasado` (alerta).  
5. Categorías de material: Máquina, Cuchillas, Cepillos/Peines, Bañera, Zona peluquería, Desinfección, Herramienta, General.  
6. Calendario: vista semanal y mensual (en Streamlit se usa `components.html` para render fiable).  
7. **No mezclar** con `tareas_plannings` / `tareas_duenos`: es submódulo con tablas propias; solo se **proyecta visualmente** en el calendario general.

### 2.8 Estado despliegue
- ✅ Docker local (`animalarium-db` + PostgREST)  
- ✅ Supabase producción (SQL aplicado por el usuario)  
- ✅ `main` + Streamlit Cloud — **validado usuario 31 jul 2026**

---

## 3. Agenda: vacaciones bloquean huecos (cerrado 30 jul)

Antes figuraba como discrepancia; **ya está resuelto en código**.

- RRHH → Ausencias crea filas en `agenda_bloqueos` con `bloquea_agenda=true`.  
- `core_agenda.aplicar_bloqueos_a_turnos` + `calcular_huecos_libres`.  
- Turnos con texto `vacaciones` / `ausencia` / `baja` / `libre` no generan huecos.  
- **Agenda y CRM** usan la misma lógica (CRM dejó de duplicar cálculo antiguo).

V2 debe: al calcular slots, cruzar cuadrante + bloqueos de ausencia.

---

## 4. Mapa de rutas sugerido V2 (ampliado)

Además de lo ya en `ESPECIFICACIONES_V2.md`, incluir:

```text
/app/(tpv-interno)
  ├─ /tareas
  │    ├─ /calendario
  │    ├─ /ficha
  │    ├─ /notas
  │    └─ /mantenimiento-material   ← NUEVO
  │         ├─ pendientes
  │         ├─ calendario
  │         ├─ materiales-planes
  │         └─ movimientos
  ├─ /personal  (cuadrante + ausencias → bloqueos agenda)
  └─ …
```

---

## 5. Prompt sugerido para el chat del proyecto V2

> Lee en el repo TPV (o copia de docs):  
> `docs_proyecto/GUIA_V2_AVANCES_2026-07-30.md`,  
> `docs_proyecto/ESPECIFICACIONES_V2.md`,  
> `docs_proyecto/Compendio_Maestro_Especificaciones.md`.  
> Queremos portar el módulo **Mantenimiento de Material** a V2 respetando tablas, frecuencias y la regla “pendiente hasta marcar hecho”.  
> Incluye también el **contrato de guardados CRM** (§7 / §2.9): smoke crear cliente → actualizar (incl. contacto/tel. alternativo) → mascota → encargo → releer, y CI que espere schema real.  
> Reuniones: alta por **rango de fechas** (§8 / §2.11).  
> Primero local; no tocar prod sin pedirlo.

---

## 6. Checklist al portar a V2

- [ ] Crear las 4 tablas `mantenimiento_*` en el entorno V2 (mismo DDL del SQL)  
- [ ] Portar lógica de `core_mantenimiento.py` (sin UI Streamlit)  
- [ ] UI: pendientes, calendario, CRUD materiales/planes, movimientos  
- [ ] Resumen en calendario de tareas del TPV interno  
- [ ] Tests de frecuencias y “atrasado hasta hecho”  
- [ ] Vacaciones/ausencias bloquean slots de agenda  
- [ ] Smoke CRM: crear cliente → actualizar (incl. **contacto/tel. alternativo y canal**) → mascota → encargo → releer  
- [ ] CI: no marcar “API lista” solo con `/`; esperar endpoint de schema real  
- [ ] Reuniones/bloqueos: alta por **rango de fechas** (un registro por día)  
- [ ] No implementar mensajería automática WA salvo petición  

---

## 7. CI, QA y contratos de guardado (1 ago 2026) — portar mentalidad a V2

Tras el merge a `main` de marketing/KPIs + hotfixes de agenda, se validó la suite local (**93+ tests**) y se endureció GitHub Actions.

### 7.1 Qué pasó (y qué NO implica)
- Un run de CI en un commit **solo de docs** salió en rojo; no implica bug de guardado en Streamlit Cloud.
- Causa plausible: PostgREST responde `200` en `/` **antes** de tener el schema cargado → tests fallan por carrera.
- Incidente puntual en un PC de tienda (encargo/cliente “no guardaba”) mientras en otro equipo sí: apuntar primero a **caché/sesión/red**, no a lógica core (smoke CRM verde).

### 7.2 Cambios en `main` (commit `dee59ae`)
| Pieza | Archivo | Qué hace |
|-------|---------|----------|
| Espera schema | `.github/workflows/ci.yml` | Poll a `/clientes?select=id&limit=1` (no solo `/`) |
| Pytest | mismo | `python -m pytest` + permisos `checks: write` |
| Smoke CRM | `tests/test_crm.py` → `test_smoke_guardado_cliente_mascota_encargo` | Crear → leer → actualizar cliente; mascota; encargo; releer |
| Smoke KPIs | `scripts/sync_marketing_kpis_cron.py --force` | Ya existía en CI |

### 7.3 Contrato mínimo que V2 debe preservar (CRM)
Fuente de verdad lógica: `core_crm.py` (`crear_cliente`, `actualizar_cliente`, `crear_mascota`, `crear_encargo`, `agendar_cita`, `registrar_recogida_desde_cita`).

1. **Cliente**: insert con nombre obligatorio; update por `id`; lectura inmediata debe devolver los mismos campos.  
2. **Mascota**: siempre ligada a `cliente_id` válido.  
3. **Encargo** (`encargos_clientes`): `detalle_pedido` = `{cantidad}x {producto}`, `estado=Pendiente`, `origen=Tienda` (flujo tienda).  
4. **Errores visibles**: la UI no debe tragar excepciones de insert/update en silencio (en Streamlit a veces solo `st.error` genérico; en V2 preferir mensaje + toast + log).  
5. **Tests**: en V2, smoke de ida/vuelta equivalente (no solo unitarios de helpers).  

### 7.4 Prompt extra para el chat V2 (QA)

> Además del módulo de mantenimiento, replica el **smoke de guardados CRM** del TPV: crear cliente, actualizar teléfono/puntos **y contacto/tel. alternativo**, crear mascota, crear encargo y releer de Supabase. El CI no debe dar por lista la API hasta que exista el schema (`/clientes`). Reuniones: alta por rango de fechas. Primero local; no tocar prod sin pedirlo.

---

## 8. CRM contacto alternativo y reuniones por rango (12–17 ago 2026)

### 8.1 Directorio de clientes — no omitir columnas al guardar
En Streamlit, un “optimizador” comparaba solo un subconjunto de columnas antes del `update`. Si el usuario cambiaba **solo** Contacto Alt. / Tel. Alt. / Canal, el guardado se saltaba.

**Contrato V2:** cualquier campo editable del directorio debe entrar en la detección de dirty / PATCH. Campos obligatorios a incluir:

`nombre_dueno`, `telefono`, `nombre_dueno_2`, `telefono_2`, `email`, `metodo_contacto`, `fecha_nacimiento`, `direccion`, RGPD, puntos, domicilio.

Referencia: `core_crm.CAMPOS_DIR_CLIENTES` + `fila_cliente_tiene_cambios`. Tests: `tests/test_crm.py`.

### 8.2 Reuniones de Equipo — rango inclusivo
UI TPV: **Proyectos, Reuniones y Eventos → 🤝 Reuniones de Equipo**.  
Campos: título, **Desde el día**, **Hasta el día**, hora inicio/fin, empleado (`Todas` o uno), checkbox bloquear agenda.

Regla: `fecha_fin >= fecha_ini`; se genera **una fila `agenda_bloqueos` por cada día** del rango (mismas horas). Un solo día = Desde = Hasta.

Referencia: `core_proyectos.construir_bloqueos_rango` · `proyectos_eventos.py`. Tests: `tests/test_proyectos.py`.

V2: el formulario de bloqueo no debe forzar un día a la vez.
