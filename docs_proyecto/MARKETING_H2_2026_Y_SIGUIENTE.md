# Marketing H2 2026 + hoja de ruta (handoff)

**Fecha:** 29–30 jul 2026  
**Ámbito datos:** Sembrado en **local** y en **producción Supabase** (29 jul 2026, script `--prod`).  
**Código:** en `main` (UI **TEXTO PARA PUBLICAR** + calendario “títulos y presupuesto”).  
**Script:** `scripts/seed_marketing_h2_2026_local.py`  
- Local: `python scripts/seed_marketing_h2_2026_local.py`  
- Prod: `python scripts/seed_marketing_h2_2026_local.py --prod`  

Este documento cierra el trabajo de marketing de esta conversación y deja listo el contexto para **seguir en una conversación nueva** (automatización de KPIs en local primero).

---

## 0. Verificación en TPV producción (30 jul 2026)

Comprobado en el TPV apuntando a Supabase prod:

| Pieza | Estado |
|-------|--------|
| Objetivos (7 metas H2) | ✅ Coincide |
| Presupuesto total H2 ~**750 €** | ✅ Coincide |
| Campañas especiales | ✅ Coincide |
| Gestión de canales / precios | ✅ Coincide |
| Datos plan ago–dic (`contenido_detallado`) | ✅ En Supabase |
| UI **TEXTO PARA PUBLICAR** + título calendario nuevo | ⚠️ En `main`; si el TPV nube aún muestra **“Vista de Proyección de Campañas”**, es **código viejo en Streamlit Cloud** → Reboot/Redeploy + `Ctrl+F5` |

**Calendario / campañas antiguas:** la semilla **no borró** mayo–julio. Solo reemplazó desde `2026-08-01`. En la lista pueden mezclarse filas viejas (may–jul) + H2 (ago–dic). Para textos nuevos: filtrar mes **agosto o posterior** en TEXTO PARA PUBLICAR (cuando la UI nueva esté desplegada).

**Señal de UI antigua vs nueva**
- Antigua: “Vista de Proyección de Campañas” → falta redeploy.
- Nueva: “TEXTO PARA PUBLICAR” arriba + “Calendario (títulos y presupuesto)” abajo.

---

## 1. Qué hay hecho (local + producción)

### Plan Maestro (`marketing_plan`)
- ~**3 posts Instagram/semana** (lun / mié / vie), no diarios (ritmo sostenible).
- Textos en `contenido_detallado` **listos para copiar/pegar** (posts, stories, reels, WA, carteles, anuncios Ads).
- UI Plan Maestro: bloque **TEXTO PARA PUBLICAR** arriba (filtro mes → campaña → cuadro de texto). La tabla solo muestra título/presupuesto.
- Talleres intercalados con previsión (anuncios previos + día + recap).
- Campañas especiales: tipo `Campaña de Evento/Feria` (talleres) e `Iniciativa Innovate` (etiqueta; ver `INICIATIVA_INNOVATE.md`).
- **Producción (29 jul 2026):** ~131 filas H2 (`fecha_planificada >= 2026-08-01`); mayo–julio no se tocaron.

### Presupuesto 150 €/mes (ago–dic = 750 € H2)
| Soporte | €/mes | Notas |
|---------|------:|--------|
| Instagram/Facebook Ads (Meta) | ~70 | Canal principal pagado |
| Google Ads | ~45 | Búsqueda local |
| Cartelería / impresión | ~35 | Sobre mensual; piezas sueltas no suman otra vez |
| WhatsApp a clientes | 0 | Envío manual 1 clic; API aparcada |

La **fecha** de cada fila Ads (p. ej. 08/08) es el ancla del **sobre del mes**, no “gastar todo ese día”. En la práctica: campaña activa **todo el mes** con presupuesto diario ≈ mensual/30.

### Objetivos (`marketing_objetivos`) — 7 metas H2
Hoy el seguimiento es **manual**: Objetivos y Resultados → Actualizar Resultados (`valor_actual` + estado).  
Las acciones del plan tienen `objetivo_id` para agrupar; **no cuentan solas** citas/ventas.

### Talleres (`eventos_talleres`) — sábado o domingo
| Fecha | Día | Taller |
|-------|-----|--------|
| 2026-08-22 | sáb | Higiene básica oídos/ojos/uñas |
| 2026-09-20 | dom | Masterclass deslanado |
| 2026-10-24 | sáb | Miedos, estrés y pirotecnia |
| 2026-11-22 | dom | Masajes / SPA en casa |
| 2026-12-12 | sáb | Fiesta navideña y cuidado invernal |

FK: en prod ya existían (`marketing_plan`→objetivos, `eventos_asistentes`→taller/cliente). En local se añadieron si faltaban.

### Fixes UI
- Mensaje engañoso “tabla no encontrada / ejecuta SQL” sustituido por error real + fallback sin embed.
- Talleres visibles en Proyectos y Eventos.

---

## 2. Cómo usarlo día a día (sin automatizar)

1. **Publicar redes:** Marketing → Plan Maestro → TEXTO PARA PUBLICAR → mes → campaña → copiar → pegar en IG → subir foto/vídeo.
2. **Ads del mes:** Crear/ajustar campaña en Meta (prioridad IG) y Google con el texto del plan; presupuesto diario ≈ 70/30 y 45/30; al cerrar el mes, anotar **gasto real** en la fila del plan.
3. **Cartelería:** Copiar texto del cartel al diseño; impresión sale del sobre de 35 €.
4. **WA:** Copiar mensaje; enviar solo a quien corresponda (RGPD); coste 0.
5. **Objetivos:** 1× semana o 1× mes, actualizar `valor_actual` a mano (citas, altas CRM, ticket medio, plazas talleres, etc.).
6. **Talleres:** Gestionar aforo en Proyectos y Eventos; anuncios ya van en el plan con fechas.

---

## 3. Qué se puede automatizar después (backlog técnico)

Priorizar solo si el usuario lo pide. Orden sugerido:

### A. Objetivos (recomendado primero)
| Idea | Cómo | Dependencias |
|------|------|----------------|
| Citas pelu / semana | Job o botón “Recalcular” que cuente `citas` no canceladas en rango | Tabla `citas`, parse estado |
| Altas CRM | Contar `clientes.created_at` en el periodo | Tabla `clientes` |
| Ticket medio | Media tickets TPV productos en periodo | Historial ventas |
| Ocupación talleres | `inscritos / plazas` media en `eventos_*` | Ya hay tablas |
| ROI Ads | `ventas_atribuidas / gasto_real` (gasto del plan o import CSV Ads) | Definir atribución (manual “¿cómo nos conociste?” o UTM) |

UI: botón **“Sincronizar KPIs desde TPV”** en Objetivos, o cron nocturno solo local primero.

### B. Gasto Ads
- Campo gasto_real rellenado a mano (ahora) → o import CSV de Meta/Google → o API Marketing de cada plataforma (más trabajo / secretos).

### C. Recordatorios WA / Email
- **Aparcado** (`DECISION_MENSAJERIA_AUTOMATICA.md`). Manual = Agenda Recordatorios 1 clic.
- Si se retoma: Meta WABA + plantillas + cron; email SMTP opcional; filtrar `rgpd_consent`.

### D. Cumpleaños / Win-back
- Pestañas “Próximamente” en Marketing. Reutilizar textos del plan cuando se active.

### E. Regenerar / reseeding
- Local o prod con el script (`--prod`). Solo reemplaza H2 (ago+); no borra mayo–julio.

---

## 4. Archivos clave

| Archivo | Rol |
|---------|-----|
| `marketing.py` | UI Objetivos, Plan Maestro (copy), Canales, Especiales |
| `core_marketing.py` | Progreso % + alerta fin de plan |
| `proyectos_eventos.py` | Talleres + asistentes |
| `scripts/seed_marketing_h2_2026_local.py` | Semilla H2 local / `--prod` |
| `PLAN_MARKETING_2026.md` | Estrategia anual + estado H2 |
| `docs_proyecto/INICIATIVA_INNOVATE.md` | Qué es la etiqueta Innovate |
| `docs_proyecto/DECISION_MENSAJERIA_AUTOMATICA.md` | WA/Email auto aparcado |

---

## 5. Prompt sugerido para la siguiente conversación

> Seguimos Animalarium TPV. Lee `.agents/AGENTS.md` y `docs_proyecto/MARKETING_H2_2026_Y_SIGUIENTE.md`.  
> Datos H2 en prod verificados (objetivos, 750 €, especiales, canales). Código UI en `main`.  
> Si falta TEXTO PARA PUBLICAR en la nube: redeploy Streamlit Cloud.  
> Quiero trabajar en **local** la automatización de KPIs (o checklist Meta/Google).  
> No toques `main` hasta que lo pida.

---

## 6. Fuera de alcance inmediato

- WhatsApp Business API / email masivo (sigue aparcado).
- Cumpleaños / win-back (“Próximamente”).
- Re-sembrar producción sin petición (ya está cargado).
- Borrar a mano mayo–julio del plan (opcional; no hace falta para usar H2).
