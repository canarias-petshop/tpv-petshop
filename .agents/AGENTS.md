# Reglas del Proyecto Animalarium (TPV y Web)

## Estado Actual y Contexto
Este es un proyecto doble (TPV en Streamlit y Web E-commerce). Metodología: Sprints + testing + **primero local, después producción**.

Documentación obligatoria antes de cambios grandes:
1. `docs_proyecto/Compendio_Maestro_Especificaciones.md`
2. `docs_proyecto/estado_tareas.md`
3. Para V2 / otro repo: `docs_proyecto/GUIA_V2_AVANCES_2026-07-30.md` + `docs_proyecto/ESPECIFICACIONES_V2.md`

## Decisiones y módulos recientes (leer si el tema aplica)

### Mantenimiento de Material (30 jul 2026 — local)
Submódulo en **Tareas → 🛠️ Mantenimiento Material**. Tablas `mantenimiento_*` en Docker; SQL listo para Supabase: `scripts/sql_mantenimiento_material.sql`.  
Pendientes hasta marcar Hecho. Movimientos incluyen “Sale a mantenimiento”.  
**Sin prod** hasta que el usuario lo pida.  
→ `docs_proyecto/GUIA_V2_AVANCES_2026-07-30.md` §2 · `core_mantenimiento.py`

### Vacaciones / ausencias bloquean agenda
Resuelto: `core_agenda` + CRM. Ya no es discrepancia del Compendio.

### Mensajería automática (WhatsApp / Email)
**No implementar** salvo petición explícita. Recordatorios = **manuales** (1 clic).  
→ `docs_proyecto/DECISION_MENSAJERIA_AUTOMATICA.md`

### Marketing H2 2026 (ago–dic)
Plan con textos copy/paste, objetivos, 150 €/mes (IG Ads + Google + cartelería), talleres sáb/dom.  
**Datos:** local y producción (verificados 30 jul). **Código UI plan:** en `main` (TEXTO PARA PUBLICAR).  
→ `docs_proyecto/MARKETING_H2_2026_Y_SIGUIENTE.md` · `scripts/seed_marketing_h2_2026_local.py`

### Sync KPIs marketing — **rama** `feature/marketing-kpis-sync-v1`
**Hecho (rama, commits locales):** sync manual + cron **23:05 Canarias** + CI.  
**Pendiente:** push / merge solo si usuario confirma. **Sin prod.**  
→ `docs_proyecto/PLAN_KPIS_MARKETING_LOCAL.md`

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
**V2 / portar módulos:** lee **`docs_proyecto/GUIA_V2_AVANCES_2026-07-30.md`**.  
**Sync KPIs / marketing:** `docs_proyecto/PLAN_KPIS_MARKETING_LOCAL.md`.  
**Plan H2 / Ads:** `docs_proyecto/MARKETING_H2_2026_Y_SIGUIENTE.md`.
