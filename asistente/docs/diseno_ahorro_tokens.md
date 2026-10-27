# Diseño: ahorro de tokens con caché del plan

> **Estado: SOLO DISEÑO.** No hay código de esto en el repositorio.

## 1. Cuánto cuesta hoy una pregunta

Medido sobre el código actual (rol admin):

| Parte | Tamaño aprox. | Tokens aprox.* |
|---|---|---|
| Definición de las funciones (`herramientas_para_rol`) | ~7 000 caracteres | ~2 000 |
| Instrucciones del sistema (`prompt.py`) | ~3 000 caracteres | ~900 |
| Memoria (hasta `ASISTENTE_TURNOS_MEMORIA=12` turnos) | variable | 0 – 2 500 |
| Resultado de las funciones (JSON resumido) | variable | 500 – 2 500 |

\* Estimado a ~3,5 caracteres por token en español; se debe confirmar con el `usage` que devuelve cada proveedor.

Una pregunta típica hace **2 rondas** con el modelo:

1. **Ronda de plan:** sistema + funciones + memoria + pregunta → el modelo elige función y parámetros. ≈ **3 000 – 5 500 tokens de entrada**, ~50 de salida.
2. **Ronda de respuesta:** lo mismo + el resultado de la función → el modelo redacta. ≈ **4 000 – 8 000 de entrada**, ~200 – 400 de salida.

Total típico: **≈ 7 000 – 13 000 tokens por pregunta**, y la mitad se va solo en decidir *qué* consultar.

## 2. Propuesta: tres capas

### Capa 1 — Caché semántica del PLAN (pregunta → función + parámetros)

Se guarda **la decisión**, no la respuesta:

```
"¿qué pedidos fallaron hoy?"  →  buscar_pedidos({estado:"FALLIDO", desde:"{hoy}", hasta:"{hoy}"})
```

- **Clave:** la pregunta normalizada (minúsculas, sin tildes, sin signos, DNI/teléfonos ya seudonimizados) + **rol**.
  Primero coincidencia exacta; luego similitud semántica con embeddings (umbral alto, p. ej. coseno ≥ 0,92).
- **Valor:** nombre de la función + parámetros, con las fechas relativas guardadas como **marcadores** (`{hoy}`, `{ayer}`, `{inicio_semana}`), que se resuelven al usarlo.
- **Solo se guarda** si la función terminó bien, la pregunta no depende del contexto ("¿y ayer?", "ese pedido", "el segundo") y no hay códigos/nombres concretos que cambien (o se guardan como parámetro variable: `PD-\d+`).
- **Al acertar:** se salta la ronda de plan, se **ejecuta la función con datos frescos del núcleo** y solo se hace la ronda de respuesta.
- **Seguridad:** los parámetros del plan se validan igual que hoy (`validar_argumentos` y roles); la caché nunca puede habilitar una función que el rol no tiene. Se separa por rol y se invalida al cambiar el catálogo (hash de `DEFINICIONES` en la clave).
- **Ahorro por acierto:** la ronda 1 completa (≈ 3 000 – 5 500 tokens) y ~1–2 s de latencia.

### Capa 2 — Caché corta de RESULTADOS del núcleo (por usuario)

- Guarda el JSON que devolvió el núcleo para `(token del usuario, ruta, parámetros)` durante **30–60 s**.
- Sirve cuando el usuario reformula ("ahora en tabla", "grafícalo") o cuando la misma pregunta llega dos veces seguidas.
- Es **por usuario** (nunca se comparte entre sesiones: los permisos los aplica el núcleo con *su* token) y se descarta al cerrar sesión.
- **No ahorra tokens del modelo**, ahorra consultas al núcleo y tiempo. Con TTL tan corto el dato sigue siendo actual para operación.

### Capa 3 — Plantillas para las consultas más frecuentes (sin modelo)

Para preguntas cerradas y muy repetidas (las sugerencias del widget: "Resumen del día", "¿Qué pedidos fallaron hoy?",
"¿Cuántos pedidos observados hay?", "¿Qué retornos faltan llegar?"):

- Si el plan sale de la caché con **coincidencia exacta** y la función tiene plantilla, se responde con un texto armado por el
  servidor a partir de los datos frescos: *"Hoy van {entregados_hoy} entregados y {fallidos} fallidos. Hay {n} rutas activas…"*.
- Los bloques (tabla, gráfico, enlace) ya los arma hoy el servidor, así que no cambian.
- **Ahorro por acierto:** ~100 % de los tokens (no se llama al modelo). Las cifras salen directo de los datos, sin riesgo de que la IA las altere.

## 3. Por qué NO se cachean respuestas con cifras

1. **Los datos cambian minuto a minuto.** "¿Cuántos fallidos hay hoy?" vale 3 a las 10:00 y 7 a las 12:00. Una respuesta guardada sería
   un dato **falso** dicho con total seguridad, en un sistema donde se toman decisiones operativas (reprogramar, mandar auxilio).
2. **Permisos.** La respuesta de un admin puede contener datos que un usuario de almacén no ve. Cachear el texto final podría filtrarlos entre roles o usuarios.
3. **Contexto de la conversación.** La misma frase significa cosas distintas según los turnos previos ("¿y ayer?").
4. **Privacidad.** Las respuestas pueden contener nombres o direcciones; guardarlas amplía lo que se retiene más allá de la conversación del usuario.
5. **Trazabilidad.** El principio del asistente es "solo datos reales del sistema": cada cifra debe salir de una consulta hecha en ese momento.

Por eso se cachea el **plan** (qué consultar), que es estable, y nunca la **respuesta** (qué decir), que depende de datos vivos.

## 4. Estimación de ahorro

Supuestos (a validar con la tabla `auditoria`, que ya guarda la pregunta y las funciones usadas):

- ~45 % de las preguntas son repetidas o casi iguales (sugerencias del widget + preguntas operativas de rutina).
- De ellas, ~1/3 son exactas y con plantilla.

| Escenario | Tokens por pregunta (prom.) | Ahorro |
|---|---|---|
| Hoy | ~10 000 | — |
| + Capa 1 (plan) | ~8 300 | ~17 % |
| + Capa 1 + Capa 3 (plantillas) | ~7 300 | **~25–30 %** |

Cálculo: 45 % de aciertos × ~4 000 tokens de la ronda de plan ≈ 1 800 menos; 15 % con plantilla × ~6 000 de la ronda de respuesta ≈ 900 menos.

Más: menos llamadas a proveedores gratuitos con límite diario (Gemini/Groq), menos errores 429 y respuestas 1–2 s más rápidas en los aciertos.
Si el uso real es más repetitivo (p. ej. personal de almacén que pregunta lo mismo cada mañana), el ahorro puede pasar del 40 %.

**Cómo medirlo antes de construir:** agrupar `auditoria.pregunta` normalizada por rol durante 2 semanas y calcular qué porcentaje se repite;
registrar el `usage` de tokens por proveedor en cada respuesta.

## 5. Implementación sugerida (cuando se apruebe)

| Pieza | Cambio |
|---|---|
| `services/cache_plan.py` (nuevo) | Normalización, búsqueda exacta y semántica, marcadores de fecha, invalidación por hash del catálogo. |
| `models/plan_cacheado.py` (nuevo) | Tabla `planes_cacheados(rol, clave, embedding, funcion, parametros, aciertos, creado_en)`. |
| `services/chat_service.py` | Antes de la ronda 1: buscar plan. Al acertar: ejecutar función y pasar directo a la ronda de respuesta (o a plantilla). |
| `herramientas/plantillas.py` (nuevo) | Plantillas de texto para 4–5 funciones frecuentes. |
| `herramientas/cliente_core.py` | Caché por usuario con TTL corto en `get`. |
| `core/config.py` | `ASISTENTE_CACHE_PLAN_ENABLED`, `ASISTENTE_CACHE_PLAN_UMBRAL`, `ASISTENTE_CACHE_DATOS_SEG`. |
| Pruebas | Acierto ejecuta función fresca; fechas relativas se resuelven al día actual; rol distinto no comparte plan; preguntas con contexto no se guardan. |
