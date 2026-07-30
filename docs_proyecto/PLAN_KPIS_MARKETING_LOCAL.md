# Plan: Sync KPIs marketing (local + automatización)

**Cierre documentación:** 30 jul 2026 (tarde) — **siguiente chat: tras verificar cron esta noche**  
**Rama:** `feature/marketing-kpis-sync-v1` (**4 commits**, **sin push** a GitHub, **sin merge** a `main`)  
**Handoff principal:** este archivo + `estado_tareas.md` + `.agents/AGENTS.md`

Contexto H2: `docs_proyecto/MARKETING_H2_2026_Y_SIGUIENTE.md`  
Semilla objetivos: `scripts/seed_marketing_h2_2026_local.py`

---

## Snapshot — retomar después de esta noche

### Implementado (en rama, commiteado)

| Pieza | Detalle |
|-------|---------|
| Sync KPIs v1 | `core_marketing.py` — clasificar / calcular / `sincronizar_objetivos_desde_tpv` |
| UI | `marketing.py` — bloque arriba en Objetivos + botón manual + resumen |
| Cron nocturno | **23:05** `Atlantic/Canary` — `docker/crontab`, `scripts/sync_marketing_kpis_cron.py`, entrypoint `/entrypoint.sh` |
| Log cron | `logs/kpis_cron.log` (gitignored) |
| CI GitHub | `.github/workflows/ci.yml` — 86 pytest + smoke sync KPIs |
| CI local | `scripts/run_ci_local.ps1` / `run_ci_local.sh` |
| Schema CI | `docker/init-test-db.sql` (BD nueva en CI) |
| Tests | **86** suite completa OK · **13** en `test_marketing.py` |

### Commits en la rama (orden)

1. `3ac7909` — feat sync KPIs v1 (botón + core + tests)
2. `bbe8c2d` — cron 23:05 Canarias
3. `0938003` — fix Docker entrypoint + CRLF crontab
4. `d17b811` — CI GitHub Actions + `run_ci_local`

### Validado por el usuario

- Botón sync en `:8501` → **4 actualizados, 4 omitidos, 0 errores** (ceros = BD local / periodo H2 aún vacío).
- ROI y packs sin datos → omitidos (correcto v1).

### Pendiente esta noche (usuario)

1. PC + Docker encendidos **antes de 23:05** Canarias.
2. Contenedores: `animalarium-tpv`, `animalarium-db`, `animalarium-api`.
3. Tras 23:05:
   ```powershell
   Get-Content logs\kpis_cron.log -Tail 5
   ```
   Línea esperada: `[fecha] Sync KPIs cron: N actualizado(s)...`
4. Si no hay línea nueva → `docker logs animalarium-tpv --tail 20` y revisar cron.

### Verificación primera noche (30→31 jul 2026)

- Cron **sí disparó** a las 23:05 (mtime del log).
- Resultado: `ERROR ... Connection refused` — cron no heredaba `API_URL` → apuntaba a `localhost:3000`.
- **Fix (31 jul):** `docker/entrypoint.sh` inyecta `API_URL=http://animalarium-api:3000` en el crontab. Requiere rebuild del contenedor `tpv-app`.
- Código ya estaba en **`main`** (merge 30 jul). El automatico nocturno es **solo Docker local** (PC encendido); Streamlit Cloud no ejecuta este cron.

### Pendiente siguiente conversación (orden sugerido)

1. Rebuild local: `docker compose build tpv-app && docker compose up -d tpv-app` (o equivalente).
2. Confirmar cron la siguiente noche (log sin Connection refused).
3. **Prod / Streamlit Cloud:** cron Docker **no** viaja a la nube; definir job externo o sync al abrir app (futuro).
4. Opcional: unificar objetivos ROI duplicados en BD; ticket medio sin ventas → 0 vs omitido.

### NO hacer sin pedirlo

- Push / merge a `main` / redeploy nube / Supabase prod
- ROI Ads automático
- Checklist operación Meta+Google del mes

---

## Automatizaciones activas

| Qué | Cuándo | Dónde ver |
|-----|--------|-----------|
| Sync KPIs cron | 23:05 diario (Docker local) | `logs/kpis_cron.log` |
| Sync KPIs manual | Al pulsar botón | UI Objetivos |
| pytest CI | Tras `git push` (rama/feature o PR) | GitHub → Actions → Checks |
| pytest local | `.\scripts\run_ci_local.ps1` | terminal + `pytest-results.xml` |

**Requisito cron:** imagen reconstruida (`docker compose build tpv-app`). Variable `MKT_KPIS_CRON_ENABLED=false` desactiva cron.

---

## Puertos

| Puerto | Qué es |
|--------|--------|
| **8501** | UI Streamlit (TPV local) |
| **3001** | PostgREST local (tests + app Docker) |

---

## Mapeo KPI → fuente (v1)

Matching por `kpi_medidor` (keywords). ROI → omitido.

| KPI H2 | Tipo | Notas |
|--------|------|--------|
| Citas pelu / semana | `citas_semana` | Excluye canceladas/anuladas/no presentado |
| Altas CRM | `altas_crm` | `clientes.created_at` |
| Ticket medio | `ticket_medio` | Sin ventas → **omitido** (no 0) |
| Ocupación talleres | `ocupacion_talleres` | |
| Facturación Nov-Dic | `facturacion_productos` | |
| Packs calma / pirotecnia | `packs_calma` | Sin match → omitido |
| ROI Ads | `roi_ads` | **No auto** |

---

## Checklist global

- [x] Sync v1 + botón UI
- [x] Cron 23:05 Docker
- [x] Tests (86 + marketing)
- [x] CI workflow + schema init
- [x] Docs handoff
- [x] Verificar cron primera noche (disparó; falló por API_URL — fix entrypoint 31 jul)
- [x] En `main` (merge 30 jul)
- [ ] Rebuild imagen + confirmar cron OK la siguiente noche
- [ ] Prod / cloud cron

---

## Prompt — copiar en la siguiente conversación

> Animalarium TPV. Lee `.agents/AGENTS.md` y **`docs_proyecto/PLAN_KPIS_MARKETING_LOCAL.md`** (cierre 30 jul tarde).  
> Rama `feature/marketing-kpis-sync-v1` (4 commits, sin push).  
> Anoche debía correr cron 23:05 — revisé / no revisé el log `logs/kpis_cron.log`.  
> Siguiente: (1) validar cron, (2) push rama si OK, (3) merge a `main` solo si confirmo. Sin prod.

---

## Archivos clave

| Archivo | Rol |
|---------|-----|
| `core_marketing.py` | Lógica sync |
| `marketing.py` | UI |
| `scripts/sync_marketing_kpis_cron.py` | Cron nocturno |
| `docker/crontab` | Hora 23:05 |
| `docker/entrypoint.sh` | Arranca cron + Streamlit |
| `.github/workflows/ci.yml` | CI |
| `scripts/run_ci_local.ps1` | CI local Windows |
| `tests/test_marketing.py` | Tests marketing |
| `docker/init-test-db.sql` | Schema BD CI |
