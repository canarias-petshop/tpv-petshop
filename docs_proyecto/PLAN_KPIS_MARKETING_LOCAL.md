# Plan: Sync KPIs marketing (solo local + tests)

**Estado (30 jul 2026):** v1 en rama **`feature/marketing-kpis-sync-v1`** — probado en `:8501`.  
**Fase 2:** cron nocturno **23:05 Atlantic/Canary** en Docker (`docker/crontab` + `scripts/sync_marketing_kpis_cron.py`). **Sin merge a `main`** hasta validación completa.

**Fechas:** plan + implementación 30 jul 2026.

Contexto H2 (datos/UI hechos): `docs_proyecto/MARKETING_H2_2026_Y_SIGUIENTE.md`.  
Semilla objetivos: `scripts/seed_marketing_h2_2026_local.py` (`OBJETIVOS` + `kpi_medidor`).

---

## Snapshot para retomar mañana

### Hecho
- `core_marketing.py`: `clasificar_tipo_kpi`, `calcular_valor_kpi`, `sincronizar_objetivos_desde_tpv` (+ helpers).
- `marketing.py`: bloque **“Sincronización desde el TPV”** arriba en Objetivos (antes de columnas crear/lista), botón primary + spinner + resumen ok/omitido/error.
- `tests/test_marketing.py`: 11 tests en verde (`.venv\Scripts\python.exe -m pytest tests/test_marketing.py`).
- Contenedor `animalarium-tpv` reiniciado; código montado por volumen Docker.
- Docs: este plan, `estado_tareas.md`, `.agents/AGENTS.md`, Compendio § Marketing.

### NO hecho / no tocar sin pedirlo
- Commit git (cambios en working tree de `main`, **sin commit**).
- Push / Streamlit Cloud / Supabase prod.
- Cron automático.
- ROI Ads / APIs Meta-Google.
- Checklist operación Ads del mes.

### Cómo probar (usuario)
1. URL **local**: `http://localhost:8501` (no la nube).
2. Marketing → **Objetivos y Resultados**.
3. Arriba debe verse **“Sincronización desde el TPV”** + botón **Sincronizar KPIs desde TPV**.
4. “Actualizar Resultados / Actualizar Progreso” = edición **manual** de siempre (sigue ahí).
5. Tras pulsar sync: mensaje con N actualizados / omitidos / errores. ROI suele ir a omitidos.

### Git (al cerrar PC — no perdido en disco, sí sin commit)
Rama: `main` (solo working tree). Archivos tocados relevantes:
- `core_marketing.py`, `marketing.py`, `tests/test_marketing.py`
- `.agents/AGENTS.md`, `docs_proyecto/PLAN_KPIS_MARKETING_LOCAL.md`, `docs_proyecto/estado_tareas.md`, `docs_proyecto/Compendio_Maestro_Especificaciones.md`
- (ignorar `.coverage` para commit)

Si mañana no aparece el botón: `docker restart animalarium-tpv` + Ctrl+F5 en `:8501`.

---

## Objetivo

En **local** (Docker / `http://localhost:8501`), recalcular `valor_actual` de `marketing_objetivos` desde datos del TPV con un botón manual y tests.  
**No** producción, **no** push a `main`, **no** Ads/cron hasta petición explícita tras prueba local.

## Puertos (no confundir)

| Puerto | Qué es |
|--------|--------|
| **8501** | UI Streamlit (TPV local) |
| **3001** | PostgREST / API datos local (tests y app Docker) |

---

## Alcance v1

### Sí
- Lógica pura en `core_marketing.py`.
- Botón **“Sincronizar KPIs desde TPV”** en Marketing → Objetivos (`marketing.py`), **fuera** de formularios; bloque arriba del panel.
- Tests en `tests/test_marketing.py`.
- Actualización manual por objetivo sigue disponible.

### No (v1)
- Push / producción / redeploy nube.
- Cron nocturno (nada “se sincroniza solo”).
- APIs Meta/Google ni import CSV Ads.
- Mensajería WA/email (aparcado: `DECISION_MENSAJERIA_AUTOMATICA.md`).
- ROI Ads con atribución → **omitido** (no escribir `0` inventado).
- Cambiar `estado` del objetivo a Completado automáticamente.

---

## Mapeo KPI → fuente (v1)

Matching por texto de `kpi_medidor` (keywords / contains), **no** por IDs fijos de fila.  
Rango de fechas = `[fecha_inicio, fecha_fin]` del objetivo.

| `kpi_medidor` (semilla H2) | Tipo interno | Cálculo | Notas |
|----------------------------|--------------|---------|--------|
| Citas peluquería confirmadas / semana | `citas_semana` | Media semanal citas; excluir Cancelada/Anulada/No presentado | |
| Altas nuevas en CRM | `altas_crm` | Contar `clientes.created_at` en periodo | |
| € ticket medio TPV (productos) | `ticket_medio` | Media `ventas_historial` excl. `DEVUELTO` | |
| % plazas ocupadas (media talleres) | `ocupacion_talleres` | Media inscritos/plazas | |
| € facturación productos campaña Nov-Dic | `facturacion_productos` | Suma ventas válidas en rango | |
| Talleres/consultas anti-estrés + packs calma | `packs_calma` | Keywords; si no hay match → omitir | |
| € ventas atribuidas / € gastado (Ads…) | `roi_ads` | **No auto** | omitido |

KPI desconocido → omitido.

---

## Diseño técnico (resumen)

- `clasificar_tipo_kpi` / `calcular_valor_kpi` / `sincronizar_objetivos_desde_tpv`
- Solo objetivos **En progreso**; solo escribe `valor_actual` si el valor no es `None`.
- Resumen: `actualizado` | `omitido` | `error`.

---

## Checklist

- [x] Ampliar `core_marketing`
- [x] Tests en verde (11)
- [x] Botón UI visible arriba + resumen
- [ ] Merge a `main` + prod solo cuando el usuario confirme
- [ ] Fase 2 (objetivo usuario): **automatización total** — cron nocturno o job al abrir TPV; ROI/atribución si se define
- [ ] Fase siguiente (si se pide): checklist Meta/Google del mes

---

## Fase 2 — Automatización nocturna (implementada en rama)

| Pieza | Detalle |
|-------|---------|
| Hora | **23:05** hora Canarias (`Atlantic/Canary`) — después de las 23:00 |
| Cron | `docker/crontab` dentro del contenedor `animalarium-tpv` |
| Script | `scripts/sync_marketing_kpis_cron.py` |
| Log | `logs/kpis_cron.log` (en proyecto / contenedor) |
| Desactivar | `MKT_KPIS_CRON_ENABLED=false` en docker-compose |
| Manual | `python scripts/sync_marketing_kpis_cron.py --force` |
| Rebuild | Tras cambiar Dockerfile: `docker compose build tpv-app && docker compose up -d tpv-app` |

El botón manual en Objetivos sigue disponible para forzar sync al instante.

**Streamlit Cloud / prod:** el cron Docker no aplica en la nube; al merge habrá que definir job externo o sync al abrir app (pendiente).

---

## Prompt para conversación nueva (copiar/pegar)

> Seguimos Animalarium TPV. Lee `.agents/AGENTS.md` y **`docs_proyecto/PLAN_KPIS_MARKETING_LOCAL.md`** (snapshot cierre 30 jul).  
> Sync KPIs v1 ya está en **código local** (sin commit/push). UI: bloque “Sincronización desde el TPV” arriba en Objetivos.  
> Quiero: (1) confirmar prueba en `:8501`, (2) si OK, **commit** local, (3) **no** prod hasta que lo diga.  
> Checklist Ads = después.

---

## Archivos clave

| Archivo | Rol |
|---------|-----|
| `core_marketing.py` | Lógica sync |
| `marketing.py` | UI Objetivos + botón |
| `tests/test_marketing.py` | Tests |
| `scripts/seed_marketing_h2_2026_local.py` | Semilla objetivos H2 |
| `docs_proyecto/MARKETING_H2_2026_Y_SIGUIENTE.md` | Handoff H2 |
| `.agents/AGENTS.md` | Reglas |
| `docs_proyecto/estado_tareas.md` | Backlog |
