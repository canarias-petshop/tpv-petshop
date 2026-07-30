# Guía de avances para V2 — 30 julio 2026

**Propósito:** documento de handoff para el repositorio `animalarium-v2` (u otro chat/agente).  
Resume lo implementado y validado en el TPV actual (`tpv-petshop`) que **debe preservarse** al portar módulos a Next.js/React.

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
| CRM + citas + recogida | Estable | Cascada `registrar_recogida_desde_cita` |
| Agenda huecos | Estable | Bloqueo por vacaciones/ausencias en `core_agenda` |
| Facturación compras | Estable | Borrador no mueve stock; pagos a 2 decimales |
| RRHH fichajes | Estable | Anti-spam 30 min + confirmación salida |
| Marketing H2 | Datos en prod; sync KPIs en rama local | Ver handoffs marketing |
| **Mantenimiento material** | **Nuevo (local Docker)** | Aún **sin** tablas en Supabase prod |
| Mensajería automática WA/Email | Aparcado | Manual 1 clic |

---

## 2. Nuevo módulo: Mantenimiento de Material (30 jul 2026)

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
- ❌ Supabase producción (SQL pendiente de aplicar cuando el usuario lo pida)  
- ❌ Streamlit Cloud / merge a `main` (hasta confirmación)

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
> Primero local; no tocar prod sin pedirlo.

---

## 6. Checklist al portar a V2

- [ ] Crear las 4 tablas `mantenimiento_*` en el entorno V2 (mismo DDL del SQL)  
- [ ] Portar lógica de `core_mantenimiento.py` (sin UI Streamlit)  
- [ ] UI: pendientes, calendario, CRUD materiales/planes, movimientos  
- [ ] Resumen en calendario de tareas del TPV interno  
- [ ] Tests de frecuencias y “atrasado hasta hecho”  
- [ ] Vacaciones/ausencias bloquean slots de agenda  
- [ ] No implementar mensajería automática WA salvo petición  
