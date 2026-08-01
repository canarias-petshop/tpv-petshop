# Compendio Maestro de Especificaciones (Spec-Driven Development)

Este documento es la **Única Fuente de la Verdad**. Ha sido generado cruzando la lectura profunda y exhaustiva del código (Realidad Técnica) con el Resumen Maestro y tus instrucciones empresariales (Realidad de Negocio). 

Sirve como "mapa" inquebrantable antes de iniciar la refactorización (Fase 2) y parametrización. Las reglas se marcan según su estado actual:
- ✅ **[CÓDIGO]**: Regla comprobada y extraída directamente del código fuente.
- ⚠️ **[DISCREPANCIA]**: Conflicto detectado entre lo que dice el Resumen Maestro / Negocio y lo que hace el Código.
- 🚀 **[NEGOCIO/FUTURO]**: Regla que exige el negocio pero que aún no está desarrollada o está pendiente.

---

## 1. Módulo Core y RRHH (`app.py`, `personal.py`)
- ✅ **[CÓDIGO]** **Guardián de Fichajes**: Bloqueo estricto de 30 minutos entre el último fichaje y un nuevo intento (Anti-doble click y errores).
- ✅ **[CÓDIGO]** **Confirmación de Salida con Contexto**: Si un empleado ya tiene una entrada abierta y vuelve a fichar tras el bloqueo anti-spam, el sistema no registra la salida sin más; primero muestra una confirmación indicando la **hora de entrada registrada** y el **tiempo restante o excedido** según el turno del cuadrante de ese día.
- ✅ **[CÓDIGO]** **Trazabilidad (Hashing)**: Todo fichaje genera un hash inalterable `SHA-256`.
- ✅ **[CÓDIGO]** **Ausencias/Vacaciones bloquean huecos**: RRHH → Ausencias crea `agenda_bloqueos` (`bloquea_agenda`); turnos con `vacaciones`/`ausencia`/`baja`/`libre` en cuadrante también excluyen huecos. Lógica centralizada en `core_agenda.py` (Agenda + CRM).

## 1-bis. Agenda y Recogida (`agenda.py`, `servicios_animalarium.py`)
- ✅ **[CÓDIGO]** **Recogida desde Nueva Cita**: Al crear una cita se muestra un control compacto de recogida a domicilio con dirección (si existe) y botón activar/desactivar para esa cita.
- ✅ **[CÓDIGO]** **Recogida desde CRM**: El flujo **Agendar Cita Inteligente** de la ficha de mascota usa el mismo comportamiento (UI + cascada al guardar).
- ✅ **[CÓDIGO]** **Cascada al guardar con recogida (`registrar_recogida_desde_cita`)**: Si la recogida está activa, la cita se guarda con estado `Servicio de recogida pendiente`, se inserta en `servicios_recogida` y se actualiza el cliente (`direccion` + `servicio_domicilio=true`), incluso si el cliente partía sin dirección ni flag activo.
- ✅ **[CÓDIGO]** **Estados de recogida en directorio**: Existen `Servicio de recogida pendiente` y `Servicio de recogida confirmado` (el legado `Servicio de recogida` se migra al pendiente).
- ✅ **[CÓDIGO]** **Recordatorios = envío manual**: Agenda → Centro de Recordatorios genera enlaces WhatsApp (`api.whatsapp.com`) y marca `[RECORDATORIO: Avisado]` en observaciones. No hay API de envío ni cron.
- ✅ **[CÓDIGO / QA]** **Smoke guardados CRM** (1 ago 2026): `test_smoke_guardado_cliente_mascota_encargo` — crear/leer/actualizar cliente + mascota + encargo. Spec V2: `ESPECIFICACIONES_V2.md` §2.9 · `GUIA_V2_AVANCES` §7.
- 🚀 **[NEGOCIO/FUTURO]** **Mensajería automática (WA / Email)**: Aparcado (29 jul 2026). Ver `docs_proyecto/DECISION_MENSAJERIA_AUTOMATICA.md`.

## 1-quater. Tareas y Mantenimiento de Material (`tareas.py`, `mantenimiento_material.py`, `core_mantenimiento.py`)
- ✅ **[CÓDIGO / PROD]** **Submódulo Mantenimiento Material** (validado usuario 31 jul): materiales, planes (diaria / semanal / 2×semana / 15 días / mensual / 3m / 6m / puntual), calendario, pendientes hasta **Hecho**, movimientos (afilar / reparación / **mantenimiento** / taller). Tablas `mantenimiento_*` en local y Supabase. SQL: `scripts/sql_mantenimiento_material.sql`.
- ✅ **[CÓDIGO]** **Resumen en Calendario General**: avisos `🛠️` / `🚨` por día.
- ✅ **[SPEC V2]** `docs_proyecto/GUIA_V2_AVANCES_2026-07-30.md` + `ESPECIFICACIONES_V2.md` §2.7.

## 1-ter. Marketing (`marketing.py`, `core_marketing.py`, `proyectos_eventos.py`)
- ✅ **[CÓDIGO / PROD]** **Objetivos y Resultados**: sync **manual** (botón) en TPV nube; **cron 23:05 Canarias** solo Docker local (`main`; entrypoint inyecta `API_URL`). ROI omitido en v1. Plan: `PLAN_KPIS_MARKETING_LOCAL.md`.
- ✅ **[CÓDIGO]** **CI** (1 ago 2026): `.github/workflows/ci.yml` — espera `/clientes` (schema), `python -m pytest`, smoke KPIs; smoke CRM en suite. Ver `GUIA_V2_AVANCES` §7.
- ✅ **[CÓDIGO]** **Plan Maestro**: `marketing_plan` + UI **TEXTO PARA PUBLICAR**.
- ✅ **[CÓDIGO / DATOS]** **Plan H2 2026**: verificado en prod 30 jul. Handoff: `MARKETING_H2_2026_Y_SIGUIENTE.md`.
- ✅ **[CÓDIGO]** **Tipos de campaña**: Ordinaria / Evento-Feria / **Iniciativa Innovate**.
- ✅ **[CÓDIGO]** **Talleres**: sáb o dom.
- 🚀 **[NEGOCIO/FUTURO]** **Cron KPIs en Streamlit Cloud / job externo**; gasto Ads auto; cumpleaños-winback.
## 2. Facturación y Contabilidad (`facturacion.py`, `caja.py`)
- ✅ **[CÓDIGO]** **VeriFactu / Hashes**: El código (`facturacion.py`, lín. 281-290) calcula y guarda en la base de datos el `hash_anterior` y `hash_actual` para cada factura, cumpliendo la Ley Antifraude.
- ✅ **[CÓDIGO]** **Borradores de Factura Recibida**: Las facturas recibidas procedentes de IA o carga manual pueden crear/enlazar artículos en inventario, pero **no actualizan stock** mientras estén en estado `Borrador`.
- ✅ **[CÓDIGO]** **Validación de Compras**: Al validar una compra en borrador, el documento debe pasar a `Recibido` (o `Pagado` si ya no tiene pendiente), recalculando importes y aplicando la actualización real del stock en ese momento.
- ✅ **[CÓDIGO]** **Borrado Seguro de Compras**: El borrado de documentos de compra solo revierte stock si el documento ya había sido validado. Borrar un borrador elimina el documento sin tocar existencias.
- ✅ **[CÓDIGO]** **Pagos Pendientes con Redondeo Comercial**: La validación del importe a pagar trabaja a 2 decimales con tolerancia mínima frente a errores de coma flotante, permitiendo liquidar exactamente el pendiente sin exigir “un céntimo menos”.
- 🚀 **[NEGOCIO/FUTURO]** **Facturas Rectificativas**: Falta programar la opción de hacer devoluciones, anular o generar abonos sin romper la cadena de hashes. 
- 🚀 **[NEGOCIO/FUTURO]** **Contabilidad**: Módulo de contabilidad completa pospuesto para el futuro.

## 3. Web y Pagos (`checkout/page.tsx`, `webhook`)
- ✅ **[CÓDIGO]** **Fiscalidad del Envío**: Los portes se cobran al 7% de IGIC como "Servicios", separados de la alimentación al 0%.
- ✅ **[CÓDIGO]** **Automatización de Deudas**: Si un pago web entra como deuda (Bizum manual), cuando el TPV local lo confirma, el sistema de historial *liquida automáticamente* la deuda, evitando ir al gestor manualmente.
- ✅ **[CÓDIGO]** **Clonado a Reparto**: Todo encargo "A Domicilio" se clona a `pedidos_domicilio`.

---

## 4. LA GRAN PARAMETRIZACIÓN (Valores "Hardcoded" a Extraer)

Se han detectado los siguientes valores "quemados" (fijos) en el código que impiden comercializar el programa. Se extraerán a la tabla `configuracion_negocio` en la Fase 2:

| Concepto | Valor Actual Fijo | Ubicación en el Código | Estado / Discrepancia |
| :--- | :--- | :--- | :--- |
| **Envío Gratis (Web)** | `110 €` | `web/checkout/page.tsx` (L103) y `PromoBanner.tsx` | ✅ **[CÓDIGO]**: Confirmado como el valor correcto de negocio. |
| **Equivalencia Puntos** | 10€ = 1pto | `tpv/tpv.py` (L915) y `crm.py` | ✅ **[CÓDIGO]**: Dividen `tk_total // 10`. |
| **Valor del Punto (€)** | `0.50 €` | `tpv/tpv.py` (L730) y Web | ✅ **[CÓDIGO]**: Multiplican puntos por `0.50`. |
| **Límite Canje Puntos** | `50%` del ticket | `web/checkout/page.tsx` (L112) y `tpv.py` | ✅ **[CÓDIGO]**: `total * 0.50` máximo. |
| **Dto. 1ª Compra (Web)** | `10 %` | `web/checkout/page.tsx` (L119) | ✅ **[CÓDIGO]** |
| **Dto. Cajas Completas** | `7 %` | `PromoBanner.tsx` (L8) | ✅ **[CÓDIGO]**: Confirmado como el valor correcto de negocio. |
| **Retorno Tienda Física** | `10 %` | `tpv/caja.py` | ✅ **[CÓDIGO]**: Descuento si visita previa <= 60 días. |

## 5. Infraestructura y Base de Datos
- ✅ **[CÓDIGO]** **Conexión Predeterminada**: La aplicación web y el TPV apuntan actualmente a Supabase en la nube usando `SUPABASE_URL` y Service Role (`supabaseAdmin`) para bypass RLS.
- 🚀 **[NEGOCIO/FUTURO]** **Entorno Híbrido**: Se mantendrá la nube como producción primaria (Trilin/Streamlit) pero se añadirán variables de entorno `.env` en local para permitir apuntar el sistema a una imagen Docker local en desarrollo o en futuros servidores físicos.
