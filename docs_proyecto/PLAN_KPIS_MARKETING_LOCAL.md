# Plan: Sync KPIs marketing (local + automatización)

**Cierre documentación:** 31 jul 2026  
**Estado:** en **`main`** (merge 30 jul). Botón sync en **prod**. Cron nocturno = **Docker local** (fix API_URL 31 jul).  
**Handoff:** este archivo + `estado_tareas.md` + `.agents/AGENTS.md`

Contexto H2: `docs_proyecto/MARKETING_H2_2026_Y_SIGUIENTE.md`

---

## Snapshot actual

| Pieza | Estado |
|-------|--------|
| Sync KPIs v1 + botón UI | ✅ `main` + usable en Streamlit Cloud |
| Cron 23:05 Canarias | ✅ Docker local; entrypoint inyecta `API_URL` |
| Primera noche (30→31 jul) | Disparó; falló `Connection refused` → **corregido** |
| Rebuild imagen | ✅ 31 jul |
| CI GitHub | ✅ en `main` |
| Cron en Streamlit Cloud | ❌ futuro (job externo / sync al abrir) |

### Commits relevantes
- Feature sync + cron + CI (rama → merge main 30 jul)
- `fb77ef8` — fix API_URL en cron entrypoint

### Validado
- Botón local: 4 actualizados / 4 omitidos (periodo H2 aún vacío o parcial — esperado).
- Objetivos H2 empiezan ~1 ago; ceros/omitidos antes de esa ventana son normales.

### Pendiente opcional
1. Mañana: `Get-Content logs\kpis_cron.log -Tail 5` → línea OK sin Connection refused.
2. Si se pide: automatizar KPIs en la nube.

### NO hacer sin pedirlo
- ROI Ads automático
- Checklist Meta/Google del mes
- Job cloud sin petición explícita

---

## Automatizaciones

| Qué | Cuándo | Dónde |
|-----|--------|-------|
| Sync KPIs cron | 23:05 diario | Docker local → `logs/kpis_cron.log` |
| Sync KPIs manual | Al pulsar | UI Objetivos (local y prod) |
| pytest CI | Push/PR a GitHub | Actions |

**Requisito cron local:** PC + `animalarium-tpv` + `animalarium-db` + `animalarium-api` encendidos.

---

## Prompt — siguiente conversación (si toca cron)

> Animalarium TPV. Lee `PLAN_KPIS_MARKETING_LOCAL.md` (cierre 31 jul).  
> Cron fix API_URL en main + rebuild hecho. Revisar log anoche. Sin prod cloud cron salvo que lo pida.
