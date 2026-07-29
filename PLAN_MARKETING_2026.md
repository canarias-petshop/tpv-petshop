# 🎯 PLAN DE MARKETING ANUAL 2026 - ANIMALARIUM

Este documento contiene la estrategia comercial de la tienda y el esqueleto de las publicaciones para todo el año 2026.

## 📌 Estrategia y Reglas de Publicación
- **Regla Principal:** Alta frecuencia de impactos sin saturar la bandeja de entrada del cliente.
- **Instagram (3x/semana):** Mezcla de Reels (educativos/satisfying), Posts (informativos/sorteos) y Stories (interactivas/día a día).
- **WhatsApp (1x/mes máximo):** Usado con extrema precaución. Solo para avisos de apertura de agenda muy demandada (Verano/Navidad) o recordatorios urgentes.
- **Email Masivo:** Descartado temporalmente hasta construir una base de datos más amplia (RGPD).
- **Promociones Físicas:** Fomentar el cruce de ventas en tienda física (Up-selling) con regalos por volumen de compra.
- **Eventos y Talleres (1x/mes):** Jornadas presenciales en fin de semana (bajo coste, ej. 15€ redimibles en productos) para fidelizar, enseñar mantenimiento básico y generar ventas cruzadas en la tienda.

### ⏸️ Automatización de envíos (WhatsApp / Email) — aparcado
- **29 jul 2026:** Se evaluó automatizar recordatorios de peluquería, mantenimiento, citas del día siguiente y campañas programables.
- **Decisión actual:** seguir **manual** (Centro de Recordatorios del TPV). Más adelante se valorará si implantar todo, solo email de marketing, o nada.
- Documento de decisión: `docs_proyecto/DECISION_MENSAJERIA_AUTOMATICA.md`.

---

## 🤖 INSTRUCCIONES PARA LA IA (FUTURAS TEMPORADAS)
**Contexto para el asistente IA:** Eres el director de marketing de Animalarium. El TPV tiene una alarma que avisa al usuario cuando se queda sin textos. 
Cuando el usuario solicite los textos para la siguiente temporada, DEBES seguir estos pasos:

1. Lee el "Esqueleto" de la temporada correspondiente que se encuentra más abajo.
2. Redacta el campo `contenido_detallado` (Copywriting) para cada acción. Usa un tono cercano, profesional, e incluye emojis y hashtags (`#Animalarium #MascotasTenerife #PeluqueriaCanina`).
3. Genera un bloque SQL con sentencias `UPDATE marketing_plan SET contenido_detallado = '...' WHERE fecha_planificada = '...';` para que el usuario pueda inyectar los textos directamente en Supabase, o proporciona los textos en formato lista si el usuario lo prefiere.

---

## 🗓️ ESQUELETO DEL PLAN ANUAL (Temporadas)

### ✅ TEMPORADA 1: Primavera / Verano (Mayo - Julio)
*(ESTADO: Completado. Los textos ya están redactados e insertados en Supabase).*
- 2026-05-04 | 📱 Instagram | Reel: ¿Por qué desparasitar ahora?
- 2026-05-08 | 📱 Instagram | Story: Encuesta de Muda de Pelo
- 2026-05-13 | 📱 Instagram | Carrusel: 3 errores al bañar en casa
- 2026-05-18 | 📱 Instagram | Reel: Top snacks naturales refrescantes
- 2026-05-22 | 📱 Instagram | Story: Unboxing mercancía
- 2026-05-26 | 💬 WhatsApp | Aviso: Agenda Peluquería Verano
- 2026-05-29 | 🏬 Tienda | Promo finde: Chuche con el pienso
- 2026-06-02 | 📱 Instagram | Reel: ASMR Peluquería Canina
- 2026-06-05 | 📱 Instagram | Story: Adivina la raza
- 2026-06-10 | 💰 Ads | Meta Ads: Promo Deslanado (50€)
- 2026-06-15 | 📱 Instagram | Post: Accesorios imprescindibles playa
- 2026-06-19 | 🏬 Tienda | Promo: Bebedero de viaje
- 2026-06-24 | 📱 Instagram | Story: Huecos libres
- 2026-06-29 | 📱 Instagram | Post: Beneficios hidratación verano
- 2026-07-03 | 📱 Instagram | Reel: Regla 5 segundos Asfalto
- 2026-07-08 | 📱 Instagram | Story: Q&A Verano
- 2026-07-14 | 📱 Instagram | Post: Gatos y el calor
- 2026-07-17 | 📱 Instagram | Reel: Productos de Viaje
- 2026-07-22 | 📱 Instagram | Story: Clientes Felices
- 2026-07-28 | 📱 Instagram | Post: NUNCA rapar perros doble capa
- 2026-07-30 | 💬 WhatsApp | Aviso Ola Calor / Promo Juguetes

### ✅ TEMPORADAS 2–4: Agosto–Diciembre 2026 (H2 Canarias)
*(ESTADO: Sembrado local + prod 29 jul 2026. Verificado en TPV 30 jul: objetivos, ~750 €, especiales, canales. Código UI en `main`; redeploy Streamlit si aún no aparece TEXTO PARA PUBLICAR. Mayo–julio del calendario no se borraron.)*

**Regenerar:**  
`python scripts/seed_marketing_h2_2026_local.py` (local) · `python scripts/seed_marketing_h2_2026_local.py --prod` (Supabase)  
**Handoff:** `docs_proyecto/MARKETING_H2_2026_Y_SIGUIENTE.md`

| Qué | Detalle |
|-----|---------|
| Ritmo IG | **~3 publicaciones/semana** (lun/mié/vie) — sostenible |
| Textos | `contenido_detallado` completo; TPV → Plan Maestro → **TEXTO PARA PUBLICAR** |
| Presupuesto | **150 €/mes** (H2 ≈ **750 €**): IG/FB Ads ~70 · Google ~45 · Cartelería ~35 · WA **0** (manual) |
| Fechas Ads | Ancla del **mes** (campaña activa todo el mes ≈ €/30 al día), no gasto de un solo día |
| Objetivos | 7 metas; progreso **manual** en Objetivos y Resultados |
| Talleres | **Sábado o domingo** + anuncios con previsión en el plan |
| Innovate | Etiqueta opcional → `docs_proyecto/INICIATIVA_INNOVATE.md` |
| Conteos prod | ~131 acciones plan · 7 objetivos · 5 talleres H2 |
| UI nube | Si pone “Vista de Proyección de Campañas” → Reboot Streamlit Cloud |

**Talleres H2:** 22 ago (sáb) higiene · 20 sep (dom) deslanado · 24 oct (sáb) pirotecnia · 22 nov (dom) SPA · 12 dic (sáb) fiesta navideña.

**Enfoque Canarias:** calor/playa/espigas, vuelta al cole, otoño norte Tenerife, Hispanidad, Halloween sin estrés, BF, cierre agenda Navidad, pirotecnia Nochevieja.