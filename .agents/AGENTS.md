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
**Datos:** local y producción (verificados 30 jul). **Código UI plan:** en `main` (TEXTO PARA PUBLICAR). Si la nube aún muestra UI antigua → Reboot Streamlit Cloud.  
→ Handoff: `docs_proyecto/MARKETING_H2_2026_Y_SIGUIENTE.md`  
→ Semilla: `scripts/seed_marketing_h2_2026_local.py` (`--prod` para Supabase)  
→ Innovate: `docs_proyecto/INICIATIVA_INNOVATE.md`  
→ Plan anual: `PLAN_MARKETING_2026.md`

### Sync KPIs marketing (rama `feature/marketing-kpis-sync-v1`)
v1 botón + **cron 23:05 Canarias** en Docker local. Sin merge a `main`/prod.  
→ `docs_proyecto/PLAN_KPIS_MARKETING_LOCAL.md`

### Recogida a domicilio desde citas
Agenda/CRM: control recogida + cascada `registrar_recogida_desde_cita` + rollback si falla (ya en `main` si se desplegó). Ver Compendio § Agenda.

## Flujo de Trabajo Obligatorio
1. **Desarrollo Modular**: ramas por sprint/feature cuando aplique.
2. **Primero local, después producción**: validar en Docker/local. **Nunca** `main` sin petición explícita del usuario tras prueba local.
3. **Documentación**: actualizar Compendio / estado_tareas / Resumen Maestro / este AGENTS cuando se cierren comportamientos de negocio.
4. **Testing**: `tests/` en verde para lógica core.
5. **No romper la DB**: PostgREST + tablas existentes; FKs necesarias para embeds (`marketing_objetivos`, `eventos_asistentes`↔`clientes`, etc.).
6. **UI Streamlit**: `# pragma: no cover` en pantallas puras UI si hace falta.

## Instrucción de inicio para agentes nuevos
Saluda, confirma que has leído `.agents/AGENTS.md`, y pregunta por la prioridad del usuario.  
Si el tema es sync KPIs / marketing objetivos: lee **`docs_proyecto/PLAN_KPIS_MARKETING_LOCAL.md`** (snapshot cierre).  
Si el tema es plan H2 / Ads / talleres: lee `docs_proyecto/MARKETING_H2_2026_Y_SIGUIENTE.md`.  
No asumas Sprint 4B automáticamente si el usuario trae otra tarea.
