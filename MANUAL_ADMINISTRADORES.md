# 👑 MANUAL DE ADMINISTRADOR: ANIMALARIUM TPV y ERP
*Guía completa de los módulos de gestión, contabilidad y gerencia.*

---

## 1. ⏱️ Gestión de Personal (Panel de Administrador)
Como administrador, tienes acceso a la configuración avanzada de tus empleados.

- **Registro de Empleados:** En la parte inferior de la pestaña "Personal", puedes dar de alta a nuevos empleados asignándoles un PIN de 4 dígitos.
- **Asignación de Turnos (Editor Visual):** Ve a "Gestión de Cuadrante (Editable)". Verás un calendario apilado por semanas que funciona como un Excel.
- **Planning y Tareas Diario:** La pestaña "Gestión y Dueño" contiene el Planning Diario y Calendario de Tareas categorizado (Ej. Tienda, Limpieza). Puedes asignar qué empleado hace cada bloque y el sistema calculará al vuelo el reparto de carga laboral del día.
- **Revisión de Horas:** Puedes ver una tabla con los fichajes reales (Entrada y Salida) y las horas totales trabajadas, útil para preparar las nóminas a final de mes.

---

## 2. 📈 Estadísticas y Rendimiento
El panel de estadísticas ha sido reestructurado en dos grandes bloques para facilitar la toma de decisiones:

**💰 1. Salud Financiera:**
- **Dashboard de Balance Neto:** Calcula el beneficio real del mes restándole a las ventas del TPV las facturas de proveedores y el prorrateo inteligente de tus Gastos Fijos (luz, alquiler, autónomos).
- **KPIs Comerciales:** Visualiza el ticket medio y el margen de rentabilidad.

**📊 2. Estadísticas Comerciales y Operativas:**
- **Top 10 Depurado:** Listado de los productos y servicios más vendidos en el mes.
- **Rendimiento y ROI Laboral Exacto:** El sistema cruza las facturaciones reales con el peluquero asignado. Extrae el precio base, descuentos y le suma cualquier "Extra" añadido en el historial clínico para darte una cifra exacta al céntimo del rendimiento generado por trabajador, así como el volumen de citas atendidas.
- **Filtro Global Maestro:** Tienes un único selector de fechas en la parte superior. Al cambiar el periodo (ej. "Mensual" o "Personalizado"), todo el panel (salud financiera, rendimiento laboral y el análisis de la agenda) se sincroniza al unísono, evitando que tengas que ajustar las fechas sección por sección.
---

## 3. 🚚 Proveedores, Pedidos y Facturación
Control de la relación con tus distribuidores y gestión de stock automático.

- **Centro de Envíos:** Alertas en tiempo real sobre los horarios de corte de los comerciales.
- **Borradores de Pedido (Smart Restock):** El sistema reparte los artículos bajo mínimos a sus respectivos proveedores, escogiendo siempre al más barato.
- **Registro de Compras (Albaranes y Facturas):** Al introducir la factura de un proveedor y "Archivarla", el stock del Inventario sube automáticamente.
- **Pago de Deudas a Proveedores (Calendario de Vencimientos):** Puedes saldar facturas atrasadas total o **parcialmente**.

---

## 4. 📊 Contabilidad y Exportación para Asesoría
Preparación fácil de los impuestos y libros contables.

- **Gastos Puntuales vs Gastos Fijos:** Registra el alquiler, luz, nóminas y préstamos en la pestaña "Configurar Gastos Fijos".
- **Calendarios y Pagos Pendientes:** Separa visualmente los "Gastos Operativos" de los "Impuestos".
- **Exportación a Excel (Asesoría):** Usa el botón de **"Solo Facturas (IGIC)"** para generar un Excel limpio de "gastitos" de caja para el contable.

---

## 5. 🏦 Bancos y Tesorería
Control estricto de la liquidez en las cuentas de la empresa.

- **Visualización de Saldo en Vivo:** El saldo de los bancos sube automáticamente cuando los clientes pagan con tarjeta por el TPV.
- **Transferencias Internas e Ingresos:** Puedes mover dinero entre bancos o registrar el ingreso del sobrante del cajón de efectivo directamente en tu cuenta de banco.

---

## 6. 📦 Modificación Avanzada de Inventario y Categorización Web
- **Categorización E-Commerce:** Para que el menú lateral de la tienda online funcione y los clientes puedan filtrar, debes usar el editor de la pestaña de Inventario para rellenar las siguientes columnas con los desplegables:
  - **`Categoría Web` (`familia`) y `Subcategoría`:** Dictan en qué sección y subsección de la tienda aparece cada artículo.
  - **`Marca`:** Escribe la marca real (Ej: "OWNAT", "ROYAL CANIN"). Todos los nombres de marca se normalizan a mayúsculas automáticamente.
  - **`Mascota`:** Selecciona "Perro", "Gato", "Roedor", etc.
  - **`Edad` y `Tamaño`:** Filtros vitales (Ej: "Puppy", "Senior", "Mini", "Gigante").
  - **`Necesidad Especial`:** Filtros clínicos o de dieta (Ej: "Esterilizado", "Hipoalergénico", "Control de Peso").
  - **`Sabor Principal`:** Ideal para dueños que buscan ingredientes específicos (Ej: "Pollo", "Salmón").
- **Robot Importador y Emparejador de Fotografías V2:** El sistema cuenta con un robot inteligente capaz de escanear la carpeta de OneDrive local ("Fotos productos"). 
  - Debes organizar las fotos respetando la jerarquía: `Marca > Mascota > Categoría (seco/humedo/snacks) > Subgama (Grain Free / Cereales)`.
  - El robot usa reglas difusas y explícitas adaptadas a cada marca para detectar variantes (ej. Optima Nova Grain Free vs Cereales) y asigna las fotos correctamente ignorando los kilos.
- **Importación de Cajas Multipack:** Al importar PDFs de tarifas de marcas como Royal Canin, si el sistema detecta cajas (Ej. `Pouch 85Gr X 12Ud`), insertará automáticamente **dos productos**: la caja entera y la unidad suelta dividiendo matemáticamente el coste y el PVP.
- **Importación Masiva de Catálogos:** Utiliza los scripts extractores para subir excels de comerciales extrayendo el código de barras, coste y PVP.

---

## 7. 🌐 Integración E-Commerce y Delivery (NUEVO)
Tu sistema TPV ahora es también el cerebro de tu Tienda Online (Next.js/Vercel).
- **Auto-registro web:** Cuando alguien entra a la web y compra, se registra automáticamente en tu base de datos de "Clientes" del TPV usando su número de teléfono.
- **Gestión de Pedidos Web:** Las compras web caen directamente en la subpestaña "Pedidos Web" del CRM de tu TPV. 
- **Convertir a Reparto:** Puedes pulsar "Crear Servicio a Domicilio" sobre un pedido web para pasarlo automáticamente a tu hoja de repartos físicos, leyendo la dirección que dejó el cliente online.

---

## 8. 👥 Gestión Avanzada de CRM y Agenda
- **Botón WhatsApp de Ahorro Acumulado:** El CRM lee todos los descuentos del 10% por mantenimiento y te muestra el "Ahorro Total". Al pulsar el botón, les enviará un mensaje celebrándolo.
- **Política Híbrida de Cancelaciones y Fianzas:** El sistema cuenta automáticamente las faltas. Otorga 1 falta de margen de confianza. Al llegar a 2 faltas, bloquea la reserva exigiendo cobrar una Fianza/Adelanto.

---

## 8-bis. 🎯 Marketing (Plan Maestro, Objetivos, Ads)
- **Plan Maestro:** Calendario de publicaciones (ago–dic 2026). Arriba del todo: **TEXTO PARA PUBLICAR** — eliges mes y campaña y copias el texto entero (Instagram, cartel, WhatsApp o anuncio). Debajo: **Calendario (títulos y presupuesto)** (solo títulos, no el texto largo).
- **Si no ves “TEXTO PARA PUBLICAR”** y aún pone “Vista de Proyección de Campañas”: la app en la nube no ha cargado el código nuevo → en Streamlit Cloud, **Reboot / Redeploy**, luego recarga forzada del navegador (`Ctrl+F5`). Los datos (objetivos, ~750 €, especiales) ya están en Supabase.
- **Calendario mixto:** mayo–julio pueden ser campañas antiguas; el plan nuevo H2 empieza en **agosto**. Filtra por mes agosto o posterior al copiar textos.
- **Ritmo redes:** ~3 posts Instagram por semana (no saturar). Talleres en **sábado o domingo**, anunciados con antelación.
- **Presupuesto 150 €/mes** (ago–dic ≈ **750 €**): ~70 Instagram/Facebook Ads + ~45 Google Ads + ~35 cartelería. WhatsApp = 0 € (manual). La fecha de la fila Ads es el **mes**, no “gastar todo en un día”: deja la campaña activa el mes con ~€/día.
- **Objetivos:** Metas numéricas (citas, clientes nuevos, etc.). Hoy se actualizan **a mano** en Objetivos y Resultados (progreso semanal/mensual). Automatizar KPIs = trabajo futuro.
- **Detalle y siguiente paso:** `docs_proyecto/MARKETING_H2_2026_Y_SIGUIENTE.md`
- **Estado (30 jul 2026):** datos H2 en producción verificados; código UI en `main`. Uso: Marketing → Plan Maestro / Objetivos / Talleres.

---

## 9. 💾 Copias de Seguridad Automáticas (Backups)
1. **Backup del Código (`crear_backup.bat`):** Empaqueta todo el programa en un archivo `.zip`.
2. **Backup de los Datos (`descargar_todos_los_datos.bat`):** Descarga en la carpeta `Backups_Datos_Nube` todo tu directorio en bruto. 

---

## 🔒 10. Consideraciones de Seguridad y Fiscalidad
1. **VeriFactu:** El sistema inyecta un código criptográfico (Hash SHA-256) en cada ticket y factura, bloqueando su borrado permanentemente.
2. **Sistema de Roles:** Tus empleados solo deben conocer su propio PIN de 4 dígitos. El sistema de ruteo bloqueará automáticamente su acceso a las vistas contables.