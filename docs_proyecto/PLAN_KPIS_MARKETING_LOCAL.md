# Plan: Automatización KPIs marketing (solo local + tests)

**Estado:** listo para empezar en conversación nueva (aún no implementado).  
**Fecha plan:** 30 jul 2026  
**Prioridad:** siguiente trabajo de marketing tras H2 sembrado.

Handoff de contexto H2 (datos/UI ya hechos): `docs_proyecto/MARKETING_H2_2026_Y_SIGUIENTE.md` §3A.

---

## Objetivo

Automatizar en **local** (Docker / `http://localhost:8501`) el recálculo de `valor_actual` de `marketing_objetivos` desde datos del TPV, con botón manual + tests. **No** tocar producción ni hacer push a `main` hasta que el usuario lo pida tras prueba local.

## Puertos (no confundir)

| Puerto | Qué es |
|--------|--------|
| **8501** | UI Streamlit (TPV local) |
| **3001** | PostgREST / API datos local (tests y app Docker) |

---

## Alcance v1

### Sí
- Lógica pura en `core_marketing.py`.
- Botón **“Sincronizar KPIs desde TPV”** en Marketing → Objetivos (`marketing.py`).
- Tests en `tests/test_marketing.py` (mocks + integración Docker si cabe).
- Validar en local `:8501`.

### No
- Push / producción sin petición explícita.
- Cron nocturno.
- APIs Meta/Google ni import CSV Ads.
- Mensajería WA/email (aparcado: `DECISION_MENSAJERIA_AUTOMATICA.md`).
- ROI Ads con atribución en v1 → **omitido** (no escribir 0 inventado).

---

## Mapeo KPI → fuente (v1)

Matching por texto de `kpi_medidor` (y/o título H2), no por IDs fijos.

| kpi_medidor (semilla H2) | Cálculo | Notas |
|--------------------------|---------|--------|
| Citas peluquería confirmadas / semana | Contar `citas` en rango del objetivo; excluir Cancelada/Anulada/No presentado; **media semanal** | Parsear `[ESTADO: …]` como en agenda |
| Altas nuevas en CRM | Contar `clientes` con `created_at` en `[fecha_inicio, fecha_fin]` | |
| € ticket medio TPV (productos) | Media totales `ventas_historial` (excl. `DEVUELTO`) en periodo | |
| % plazas ocupadas (media talleres) | Media inscritos/plazas `eventos_talleres` + `eventos_asistentes` | |
| € facturación productos campaña Nov-Dic | Suma ventas en rango del objetivo | |
| Talleres/consultas anti-estrés + packs | Keywords (calma/pirotecnia/estrés) si hay datos; si no, **omitir** | Conservador |
| € ventas atribuidas / € gastado (ROI) | **No auto en v1** | Resumen “omitido” |

---

## Diseño técnico

### `core_marketing.py`
- `clasificar_tipo_kpi(kpi_medidor) -> str`
- `calcular_valor_kpi(client, tipo, fecha_inicio, fecha_fin) -> float | None`
- `sincronizar_objetivos_desde_tpv(client, objetivos=None) -> list[dict]`  
  Solo objetivos **En progreso**. Actualiza `valor_actual` solo si el valor no es `None`.  
  Resumen por fila: `{id, titulo, valor_antes, valor_despues, accion}` (`actualizado` / `omitido` / `error`).

### `marketing.py`
- Botón fuera de formularios en Objetivos.
- Mostrar resumen ok / omitido / error → `rerun`.

### Tests
- Citas canceladas no cuentan.
- Altas CRM en rango.
- Ticket medio ignora `DEVUELTO`.
- Ocupación talleres.
- ROI / KPI desconocido → no escribe.

### Criterio “no trepa”
- Solo escribe `valor_actual` (no borra objetivos ni plan).
- No pasa a `Completado` solo (el usuario confirma estado).
- KPIs dudosos → omitir, no inventar 0.
- Producción intacta.

---

## Checklist de implementación

- [ ] `core_marketing`: clasificar + calcular + sincronizar
- [ ] Tests unitarios / integración en verde
- [ ] Botón UI en Objetivos + resumen
- [ ] Probar en `localhost:8501` con 1–2 objetivos H2
- [ ] Anotar progreso en `estado_tareas.md` (WIP local; sin push prod)
- [ ] Fase siguiente (solo si se pide): checklist Meta/Google del mes

---

## Prompt para conversación nueva

> Seguimos Animalarium TPV. Lee `.agents/AGENTS.md` y **`docs_proyecto/PLAN_KPIS_MARKETING_LOCAL.md`**.  
> Contexto H2: `docs_proyecto/MARKETING_H2_2026_Y_SIGUIENTE.md`.  
> Quiero **implementar en local** la sync de KPIs (botón + tests). No toques `main`/prod hasta que lo pida tras prueba en `:8501`.  
> Checklist Ads = después, no ahora.

---

## Archivos clave

| Archivo | Rol |
|---------|-----|
| `core_marketing.py` | Lógica (ampliar) |
| `marketing.py` | UI Objetivos |
| `tests/test_marketing.py` | Tests |
| `scripts/seed_marketing_h2_2026_local.py` | Semilla objetivos H2 (`kpi_medidor`) |
| `docs_proyecto/MARKETING_H2_2026_Y_SIGUIENTE.md` | Handoff datos/UI H2 |
