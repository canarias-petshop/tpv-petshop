# Reglas del Proyecto Animalarium (TPV y Web)

## Estado Actual y Contexto
Este es un proyecto doble (TPV en Streamlit y Web E-commerce). Hemos establecido una metodología de trabajo rigurosa basada en Sprints y testing. 
Actualmente nos encontramos en la **Fase 4: Suite de Pruebas y Refactorización**. 
El Sprint 4A (Núcleo y Personal) ya ha sido completado y subido a la rama `sprint-4a-core`.

## Dónde encontrar la documentación
Para conocer todas las reglas de negocio, la arquitectura y las tareas pendientes, DEBES leer obligatoriamente estos dos archivos antes de hacer grandes modificaciones:
1. `docs_proyecto/Compendio_Maestro_Especificaciones.md` -> Contiene el ADN del proyecto, la arquitectura Supabase y las reglas de negocio puras.
2. `docs_proyecto/estado_tareas.md` -> Contiene la lista de Sprints y qué está terminado (marcado con `[x]`) y qué falta por hacer.

### Mensajería automática (WhatsApp / Email)
**No implementar** salvo petición explícita del usuario. Hoy los recordatorios son **manuales** (1 clic). Decisión y opciones futuras: `docs_proyecto/DECISION_MENSAJERIA_AUTOMATICA.md`.

## Flujo de Trabajo Obligatorio
1. **Desarrollo Modular**: Trabaja siempre creando ramas nuevas para cada Sprint (por ejemplo, `sprint-4b-crm`).
2. **Primero local, después producción**: Los cambios se desarrollan, prueban y validan **siempre en local / Docker** antes de subirlos a la rama principal (`main`) de producción. **Nunca** publiques a `main` sin que el usuario lo pida explícitamente tras la prueba local.
3. **Guía de desarrollo**: Antes de cambios relevantes, consulta `RESUMEN_MAESTRO_ACTUALIZADO.md`, `docs_proyecto/Compendio_Maestro_Especificaciones.md` y `docs_proyecto/estado_tareas.md`, y actualiza esa documentación cuando se cierren comportamientos de negocio.
4. **Testing Estricto**: Todo código refactorizado debe tener tests en la carpeta `tests/`. No des por finalizado un refactor si los tests no están en verde (con cobertura por encima del 80%).
5. **No romper la DB**: Usamos Supabase y la conexión es a través de `postgrest.SyncPostgrestClient`. Respeta la estructura de tablas existente.
6. **Respetar la UI**: Si usas `# pragma: no cover` en funciones exclusivas de Streamlit, está bien para no ensuciar la métrica de cobertura de la lógica de negocio pura.

## Instrucción de inicio para agentes nuevos
Si eres un nuevo agente uniéndote a esta conversación por primera vez, saluda al usuario, infórmale de que has leído automáticamente estas reglas en `.agents/AGENTS.md` y pregúntale si desea iniciar el **Sprint 4B (CRM e Inventario)** tal y como marca el archivo `estado_tareas.md`.
