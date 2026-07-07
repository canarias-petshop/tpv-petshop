# Reglas del Proyecto: TPV y Web Petshop

Estas reglas definen el comportamiento estándar y flujos de trabajo de la IA en este proyecto. 

## Flujo Estándar de Importación de Marcas/Productos
A partir de ahora, cuando el usuario pida importar o montar una nueva marca en el TPV y la web, se DEBE seguir estrictamente este flujo de trabajo para garantizar el control y evitar asignaciones erróneas:

1. **Extracción**: El usuario aportará la información (normalmente en PDF, listas o tarifas). La IA debe escribir un script en Python (por ejemplo, con `pdfplumber`) para extraer en bruto los productos, gamas, pesos y precios.
2. **Generación de CSV para el Usuario**: La IA NO insertará directamente en la base de datos. En su lugar, generará un archivo Excel/CSV (codificación UTF-8 o CP1252 para el español) con las siguientes columnas mínimas:
   - Nombre Original PDF
   - Gama Extraída
   - Peso Sugerido Web
   - PVP
   - Ruta de Foto Asignada por el Bot (Sugerida, con ruta absoluta)
   - Foto Correcta? (SI/NO)
   - Ruta CORRECTA de Foto (si la anterior es NO)
3. **Revisión del Usuario**: El usuario abrirá el CSV/Excel, corregirá lo que considere necesario, añadirá las rutas correctas en su ordenador si la sugerida por la IA falla, y guardará el archivo. Luego, avisará a la IA de que el archivo está listo.
4. **Inserción y Generación de SKUs**: La IA leerá el archivo revisado y creará un script `import_from_csv.py` para insertar los productos en la base de datos (Supabase) generando SKUs secuenciales (ej. `XX-001`, `XX-002`).
   - `precio_pvp` = PVP del CSV
   - `precio_base` = PVP / 1.07 (PVD estimado asumiendo un 7% de IGIC, a no ser que el usuario especifique otro).
   - Aplicar lógica de negocio para auto-completar `categoria`, `subcategoria`, `mascota`, `necesidad_especial`, `edad`, etc., usando reglas previas basadas en palabras clave (ej: "sterilized", "puppy").
5. **Conversión y Copia de Imágenes**: Las fotos ubicadas en las rutas del ordenador del usuario DEBEN:
   - Convertirse obligatoriamente a formato `.jpg`.
   - Si la foto original tiene transparencia (ej. `.png` o `.webp`), se debe incrustar sobre un **fondo blanco puro (255, 255, 255)** usando `Pillow` antes de guardar, para evitar fondos negros y problemas de visualización en la web.
   - Las fotos resultantes se guardarán en `public/images/productos/` en la ruta del repositorio web (`D:\clon vs mode\web-petshop`).
   - El nombre de la imagen debe coincidir exactamente con el SKU generado en la base de datos (ej. `XX-001.jpg`).
6. **Despliegue (Push)**: Finalmente, la IA ejecutará `git add`, `git commit` y `git push` en el repositorio web (`web-petshop`) para subir las nuevas fotos, y notificará al usuario de su disponibilidad.
