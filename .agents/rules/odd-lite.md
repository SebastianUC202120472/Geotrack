# Regla de Proyecto: ODD Lite (Organic-Driven Development Lite)

Esta regla define el flujo de trabajo para el desarrollo de módulos en GeoTrack.

## 1. Principio Fundamental
- **Cambios menores / ajustes rápidos:** Se resuelven de forma directa (*inline*) acompañados de pruebas inmediatas.
- **Cambios sustanciales / nuevos módulos:** Requieren planificación previa y registro de seguimiento en `odd/tasks/<nombre-modulo>.md`.

## 2. Ciclo de Trabajo ODD Lite
1. **Exploración en solo lectura (Read-First):**
   - Siempre inspeccionar el código existente antes de proponer código o arquitectura.
   - Respetar la integridad del núcleo (no alterar modelos, migraciones centrales ni contratos de API existentes a menos que sea explícito).
2. **Resolución temprana de incertidumbre:**
   - Si faltan definiciones de esquema, credenciales o storage, clarificar con el usuario antes de asumir.
3. **Registro y Tracking de Tareas:**
   - Mantener el progreso actualizado en `odd/tasks/<nombre-modulo>.md`.
   - Cada tarea debe tener alcance acotado y criterios de verificación verificables (tests automatizados o validaciones funcionales).
4. **Implementación por incrementos:**
   - Trabajar de forma incremental (tarea por tarea o bloque semanal).
   - Validar con pruebas y marcar `[x]` en el archivo de tracking antes de pasar a la siguiente etapa.
5. **No invasión del Núcleo:**
   - Los módulos satélite (como asistentes o auditoría con IA) deben ser servicios desacoplados, con esquemas de base de datos propios (`schema`), consultas al núcleo en solo lectura y autenticación delegada al backend central.
