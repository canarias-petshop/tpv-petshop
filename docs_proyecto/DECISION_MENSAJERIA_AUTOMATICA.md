# Decisión pendiente: mensajería automática (WhatsApp / Email)

**Estado (29 jul 2026):** Aparcamiento consciente. **No implementar por ahora.**  
El flujo **manual** (Agenda → Recordatorios → enlace WhatsApp de 1 clic) funciona bien en el día a día y basta con unos minutos por la mañana.

Cuando se retome, **decidir con el negocio** una de estas opciones (no asumir “todo”):

| Opción | Qué implica |
|--------|-------------|
| **A. Seguir manual** | Sin cambios. Centro de Recordatorios + marketing por Instagram / envíos a mano. |
| **B. Solo email marketing** | SMTP o servicio (SendGrid/Resend), base RGPD (`rgpd_consent`), campañas del plan anual. Sin API de WhatsApp. |
| **C. Solo recordatorios WA automáticos** | Meta WhatsApp Business API + plantillas (cita mañana / mantenimiento) + cron/worker. Promos siguen manuales. |
| **D. Todo** | WA automático + email + campañas programables (servicios, ofertas, promos). |

## Situación actual en el TPV

- **No hay** envío por API: solo `api.whatsapp.com` y `mailto:` (abre el cliente del empleado).
- Textos y listas ya existen en Agenda (`🔔 Recordatorios`): citas del día siguiente + mantenimiento (umbral ~45 días).
- Flag `[RECORDATORIO: Avisado|Sin avisar]` en `citas.observaciones` (solo rutina de mañana).
- Marketing (`marketing.py` / `PLAN_MARKETING_2026.md`): calendario de planificación; cumpleaños / win-back / email masivo = “Próximamente” o aparcado por RGPD.
- Preferencias útiles ya en ficha: `metodo_contacto`, `rgpd_consent`.

## Si algún día se implementa (checklist resumido)

1. Meta Business + WhatsApp Cloud API (o proveedor tipo Twilio) y **plantillas aprobadas**.
2. Secretos (`token`, `phone_number_id`, SMTP si email).
3. Worker/cron (Docker tienda o externo) — el TPV Streamlit no “manda solo” si está cerrado.
4. Módulo de envío + tabla de log (quién / cuándo / canal / resultado).
5. Filtrar por consentimiento; reutilizar lógica actual de Recordatorios.
6. Orden sensato: citas mañana → mantenimiento → promos → email.

## Referencias

- UI manual: `agenda.py` (Centro Recordatorios), `MANUAL_EMPLEADOS.md` § rutina matutina.
- Plan canales: `PLAN_MARKETING_2026.md`.
- Tareas: `docs_proyecto/estado_tareas.md` (backlog aparcado).
