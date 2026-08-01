# Reglas del Proyecto Animalarium (TPV y Web)

## Estado Actual y Contexto
Este es un proyecto doble (TPV en Streamlit y Web E-commerce). Metodología: Sprints + testing + **primero local, después producción**.

Documentación obligatoria antes de cambios grandes:
1. `docs_proyecto/Compendio_Maestro_Especificaciones.md`
2. `docs_proyecto/estado_tareas.md`
3. Para V2 / otro repo: `docs_proyecto/GUIA_V2_AVANCES_2026-07-30.md` + `docs_proyecto/ESPECIFICACIONES_V2.md`

## Cierre sesión 1 ago 2026
- Suite local verde + **CI endurecido** y **smoke CRM** en `main` (`dee59ae` + docs handoff V2).
- Usuario valida operativa en tienda tras redeploy (encargos/clientes); si un PC falla y otro no → entorno primero.
- Handoff V2: `GUIA_V2_AVANCES` **§7** · `ESPECIFICACIONES_V2` **§2.9–2.10**.

## Cierre sesión 30–31 jul 2026 (producción OK)
Usuario validó en **Streamlit Cloud / prod**: ficha clínica, mantenimiento de material y operativa general.  
Código en **`main`**. Tablas `mantenimiento_*` aplicadas en Supabase.

## Decisiones y módulos recientes (leer si el tema aplica)

### CI / QA — **en `main`** (1 ago)
Espera schema `/clientes` antes de pytest; smoke cliente→mascota→encargo; smoke KPIs.  
→ `GUIA_V2_AVANCES_2026-07-30.md` §7 · `.github/workflows/ci.yml` · `tests/test_crm.py`

### Mantenimiento de Material — **en producción**
Submódulo **Tareas → 🛠️ Mantenimiento Material**. Tablas `mantenimiento_*` en local **y** Supabase.  
Pendientes hasta marcar Hecho. Movimientos: afilar / reparación / **mantenimiento** / taller / incidencia.  
→ `docs_proyecto/GUIA_V2_AVANCES_2026-07-30.md` §2 · `core_mantenimiento.py` · SQL `scripts/sql_mantenimiento_material.sql`

### Agenda / vacaciones + hotfix Nueva Cita
Vacaciones/ausencias bloquean huecos (`core_agenda` + CRM).  
Hotfix prod: `UnboundLocalError` por import local en `agenda.py` (commit `d7e4084`).  
Ficha clínica: descuentos fuera del bucle al guardar + error visible si falla el update.

### Sync KPIs marketing — **en `main`**
Botón manual en Objetivos (funciona en prod).  
Cron **23:05 Canarias** solo en **Docker local** (PC encendido). Fix `API_URL` en entrypoint (`fb77ef8`); rebuild hecho 31 jul.  
Nube ≠ cron automático. Handoff: `docs_proyecto/PLAN_KPIS_MARKETING_LOCAL.md`

### Mensajería automática (WhatsApp / Email)
**No implementar** salvo petición explícita. Recordatorios = **manuales** (1 clic).  
→ `docs_proyecto/DECISION_MENSAJERIA_AUTOMATICA.md`

### Marketing H2 2026 (ago–dic)
Plan con textos copy/paste, objetivos, 150 €/mes, talleres sáb/dom. Datos local + prod.  
→ `docs_proyecto/MARKETING_H2_2026_Y_SIGUIENTE.md`

### Recogida a domicilio desde citas
Agenda/CRM: `registrar_recogida_desde_cita` (ver Compendio § Agenda).

## Flujo de Trabajo Obligatorio
1. **Desarrollo Modular**: ramas por sprint/feature cuando aplique.
2. **Primero local, después producción**: validar en Docker/local. **Nunca** `main` sin petición explícita tras prueba local.
3. **Documentación**: actualizar Compendio / estado_tareas / Resumen Maestro / GUIA_V2 / este AGENTS al cerrar sesión.
4. **Testing**: `tests/` en verde; CI en GitHub tras push de rama.
5. **No romper la DB**: PostgREST + tablas existentes.
6. **UI Streamlit**: `# pragma: no cover` en pantallas puras UI si hace falta.

## Instrucción de inicio para agentes nuevos
Saluda, confirma lectura de `.agents/AGENTS.md`, pregunta prioridad.  
**V2 / portar módulos:** **`docs_proyecto/GUIA_V2_AVANCES_2026-07-30.md`** (mantenimiento §2 + **QA/CRM §7**).  
**Sync KPIs:** `docs_proyecto/PLAN_KPIS_MARKETING_LOCAL.md`.  
**Plan H2 / Ads:** `docs_proyecto/MARKETING_H2_2026_Y_SIGUIENTE.md`.
