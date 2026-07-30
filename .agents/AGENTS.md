# Reglas del Proyecto Animalarium (TPV y Web)

## Estado Actual y Contexto
Este es un proyecto doble (TPV en Streamlit y Web E-commerce). Metodología: Sprints + testing + **primero local, después producción**.

Documentación obligatoria antes de cambios grandes:
1. `docs_proyecto/Compendio_Maestro_Especificaciones.md`
2. `docs_proyecto/estado_tareas.md`

## Decisiones y módulos recientes (leer si el tema aplica)

### Mensajería automática (WhatsApp / Email)
**No implementar** salvo petición explícita. Recordatorios = **manuales** (1 clic).  
→ `docs_proyecto/DECISION_MENSAJERIA_AUTOMATICA.md`

### Marketing H2 2026 (ago–dic)
Plan con textos copy/paste, objetivos, 150 €/mes (IG Ads + Google + cartelería), talleres sáb/dom.  
**Datos:** local y producción (verificados 30 jul). **Código UI plan:** en `main` (TEXTO PARA PUBLICAR).  
→ `docs_proyecto/MARKETING_H2_2026_Y_SIGUIENTE.md` · `scripts/seed_marketing_h2_2026_local.py`

### Sync KPIs marketing — **rama activa** `feature/marketing-kpis-sync-v1`
**Hecho (rama, 4 commits, sin push):** sync manual + cron **23:05 Canarias** + CI GitHub Actions (86 pytest + smoke).  
**Pendiente:** verificar cron esta noche (`logs/kpis_cron.log`) → push rama → merge `main` si usuario confirma. **Sin prod.**  
→ Handoff completo: **`docs_proyecto/PLAN_KPIS_MARKETING_LOCAL.md`**  
→ CI: `.github/workflows/ci.yml` · local: `scripts/run_ci_local.ps1`

### Recogida a domicilio desde citas
Agenda/CRM: `registrar_recogida_desde_cita` (ver Compendio § Agenda).

## Flujo de Trabajo Obligatorio
1. **Desarrollo Modular**: ramas por sprint/feature cuando aplique.
2. **Primero local, después producción**: validar en Docker/local. **Nunca** `main` sin petición explícita tras prueba local.
3. **Documentación**: actualizar Compendio / estado_tareas / Resumen Maestro / este AGENTS al cerrar sesión.
4. **Testing**: `tests/` en verde; CI en GitHub tras push de rama.
5. **No romper la DB**: PostgREST + tablas existentes.
6. **UI Streamlit**: `# pragma: no cover` en pantallas puras UI si hace falta.

## Instrucción de inicio para agentes nuevos
Saluda, confirma lectura de `.agents/AGENTS.md`, pregunta prioridad.  
**Sync KPIs / marketing objetivos:** lee **`docs_proyecto/PLAN_KPIS_MARKETING_LOCAL.md`** (snapshot cierre).  
**Plan H2 / Ads:** `docs_proyecto/MARKETING_H2_2026_Y_SIGUIENTE.md`.
