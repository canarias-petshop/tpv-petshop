# Compendio Maestro de Especificaciones (Spec-Driven Development)

Este documento es la **Única Fuente de la Verdad**. Ha sido generado cruzando la lectura profunda y exhaustiva del código (Realidad Técnica) con el Resumen Maestro y tus instrucciones empresariales (Realidad de Negocio). 

Sirve como "mapa" inquebrantable antes de iniciar la refactorización (Fase 2) y parametrización. Las reglas se marcan según su estado actual:
- ✅ **[CÓDIGO]**: Regla comprobada y extraída directamente del código fuente.
- ⚠️ **[DISCREPANCIA]**: Conflicto detectado entre lo que dice el Resumen Maestro / Negocio y lo que hace el Código.
- 🚀 **[NEGOCIO/FUTURO]**: Regla que exige el negocio pero que aún no está desarrollada o está pendiente.

---

## 1. Módulo Core y RRHH (`app.py`, `personal.py`)
- ✅ **[CÓDIGO]** **Guardián de Fichajes**: Bloqueo estricto de 30 minutos entre el último fichaje y un nuevo intento (Anti-doble click y errores).
- ✅ **[CÓDIGO]** **Trazabilidad (Hashing)**: Todo fichaje genera un hash inalterable `SHA-256`.
- ⚠️ **[DISCREPANCIA]** **Ausencias/Vacaciones**: Aunque se pueden marcar vacaciones en el panel, el sistema *sigue ofreciendo huecos* de peluquería en la agenda para ese empleado. *Se debe arreglar en la Fase 2.*

## 2. Facturación y Contabilidad (`facturacion.py`, `caja.py`)
- ✅ **[CÓDIGO]** **VeriFactu / Hashes**: El código (`facturacion.py`, lín. 281-290) calcula y guarda en la base de datos el `hash_anterior` y `hash_actual` para cada factura, cumpliendo la Ley Antifraude.
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
