# Diseño: acciones con confirmación en el asistente (OWASP LLM06)

> **Estado: SOLO DISEÑO — pendiente de aprobación del gerente.** No hay código de esto en el repositorio.
> Hoy el asistente es de solo lectura: `cliente_core.py` solo hace `GET` a una lista cerrada de rutas.

## 1. Objetivo

Permitir que el asistente **proponga** 2–3 acciones de bajo riesgo que el usuario ya puede hacer en el panel,
sin que la IA pueda ejecutarlas por su cuenta. Es la mitigación recomendada para **OWASP LLM06 (Excessive Agency)**:
el modelo no tiene permisos propios, la lista de acciones es cerrada y toda escritura exige un clic humano.

## 2. Principios

| Principio | Cómo se cumple |
|---|---|
| El modelo solo propone | Las funciones de acción **no llaman al núcleo**: devuelven una *propuesta* que el servidor guarda y convierte en una tarjeta. |
| Confirmación humana | La tarjeta muestra Confirmar / Cancelar. Solo el clic en **Confirmar** dispara la escritura, por un endpoint distinto del chat. |
| Sin permisos propios | Se ejecuta con el **token del usuario conectado**; el núcleo vuelve a validar rol y estado. |
| Lista cerrada | Un diccionario fijo `ACCIONES` (nombre → método, ruta, rol, validador). Ruta y cuerpo los arma el servidor, nunca el modelo. |
| Auditoría | Cada propuesta, confirmación, cancelación, vencimiento y resultado queda en una tabla de auditoría. |
| Interruptor | `ASISTENTE_ACCIONES_ENABLED=false` por defecto. Apagado, las funciones de acción ni siquiera se le ofrecen al modelo. |

## 3. Endpoints del núcleo (verificados en `backend/app/api/`)

| Acción pedida | ¿Existe? | Endpoint | Rol | Observaciones |
|---|---|---|---|---|
| **Confirmar pedido** | ❌ No como acción por pedido | — | — | Lo más cercano: `POST /api/almacen/recojos/{recojo_id}/confirmar-ingreso` (confirma **todo un recojo**, con lista de faltantes; geocodifica en segundo plano) y `POST /api/almacen/pedidos/{pedido_id}/resolver-observado` (pasa un OBSERVADO a LISTO_PARA_ENVIO). Hay que **definir con el gerente** qué significa "confirmar pedido". |
| **Marcar llegada a almacén** | ⚠️ Parcial | `POST /api/almacen/retornos/rutas/{ruta_id}/escanear` · body `{codigo}` | almacén | Marca un paquete **fallido devuelto** como retornado. Para la llegada de un **recojo** es `confirmar-ingreso` (arriba). |
| **Reprogramar pedido fallido** | ✅ Sí | `POST /api/pedidos/{pedido_id}/reprogramar` (sin body) | admin | Solo acepta pedidos FALLIDO; lo saca de la ruta, lo deja LISTO_PARA_ENVIO, registra historial y cierra su reporte abierto. |
| **Asignar pedido a ruta** | ⚠️ No para un pedido suelto | `POST /api/rutas/asignar-bloque` · body `{distrito, conductor_id, nombre_ruta?}` · `PATCH /api/rutas/{ruta_id}/paradas/{pedido_id}/mover` · body `{ruta_destino_id}` | admin | `asignar-bloque` crea una ruta con **todos** los pedidos de un distrito (riesgo medio, no lo propondría). `mover` cambia una parada pendiente de una ruta a otra. No hay "agregar un pedido LISTO a una ruta existente". |

Nota: los endpoints usan `pedido_id` (numérico) y el asistente trabaja con **códigos** (`PD-001`). El servidor
debe resolver el código → id con un `GET /api/pedidos/?busqueda=...` y exigir coincidencia exacta y única.

## 4. Acciones propuestas para la primera versión (bajo riesgo)

1. **`reprogramar_pedido`** (admin) → `POST /pedidos/{id}/reprogramar`. Reversible en la práctica (el pedido vuelve a su zona), el núcleo exige estado FALLIDO.
2. **`resolver_observado`** (almacén) → `POST /almacen/pedidos/{id}/resolver-observado`. Un solo pedido, el núcleo exige estado OBSERVADO.
3. **`registrar_retorno`** (almacén) → `POST /almacen/retornos/rutas/{ruta_id}/escanear` con `{codigo}`. Un paquete a la vez, idéntico a escanearlo en pantalla.

Quedan **fuera**: cancelar pedido (terminal), asignar bloque (afecta muchos pedidos), confirmar ingreso de un recojo completo
(cambia muchos estados y dispara geocodificación), cualquier acción sobre usuarios, conductores o correos.

## 5. Flujo

```
Usuario: "reprograma el PD-014"
  │
  ▼
Modelo ──llama──► reprogramar_pedido({codigo:"PD-014"})        (función de PROPUESTA, no escribe)
  │
  ▼
Servidor del asistente
  1. ASISTENTE_ACCIONES_ENABLED y rol permitido
  2. valida argumentos (esquema cerrado, regex de código)
  3. GET /pedidos/?busqueda=PD-014 → exactamente 1, estado FALLIDO   (precondición)
  4. guarda PropuestaAccion{id, usuario_id, accion, pedido_id, resumen, vence_en=+5 min, estado=PENDIENTE}
  5. emite bloque {"tipo":"accion", "id":..., "titulo":"Reprogramar PD-014", "detalle":"Pasará de FALLIDO a LISTO_PARA_ENVIO..."}
  │
  ▼
Widget: tarjeta  [ Confirmar ]  [ Cancelar ]      ← el texto lo arma el SERVIDOR, no el modelo
  │ clic Confirmar
  ▼
POST /api/asistente/acciones/{id}/confirmar   (token del usuario, cabecera anti-CSRF del panel)
  Servidor: misma persona, PENDIENTE, no vencida → marca EN_CURSO (una sola vez)
            → POST /api/pedidos/{pedido_id}/reprogramar con el token del usuario
            → guarda resultado y auditoría → responde a la tarjeta (✔ / ✖ con el mensaje del núcleo)
```

Puntos clave:

- **El modelo no ve ni elige la ruta HTTP ni el cuerpo.** Solo nombra la acción y el código; el resto sale de `ACCIONES`.
- **Una propuesta = una ejecución** (idempotencia): el cambio PENDIENTE → EN_CURSO es atómico en BD.
- **Vence a los 5 minutos** y se invalida si el usuario cierra sesión o cambia de conversación.
- **El resultado se le informa al modelo** en el siguiente turno solo como dato ("el usuario confirmó; el núcleo respondió X").
- **Inyección indirecta:** si el texto de un correo o reporte pide "reprograma todo", el modelo podría proponerlo, pero
  nada pasa sin el clic; además se limita a **1 propuesta por respuesta** y a N confirmaciones por minuto.

## 6. Cambios necesarios (cuando se apruebe)

| Pieza | Cambio |
|---|---|
| `core/config.py` | `ASISTENTE_ACCIONES_ENABLED: bool = False`, `ASISTENTE_ACCION_VENCE_SEG = 300`, `ASISTENTE_ACCIONES_POR_MINUTO = 5`. |
| `herramientas/acciones.py` (nuevo) | Diccionario cerrado `ACCIONES`, validadores de precondición y función `proponer(...)`. |
| `herramientas/catalogo.py` | Definiciones de las 3 funciones de propuesta, solo si el interruptor está activo y según rol. |
| `herramientas/cliente_core.py` | Nuevo método `post_accion(nombre, ...)` con **su propia** lista cerrada de rutas de escritura; el `get` sigue sin cambios. |
| `models/propuesta_accion.py` (nuevo) | Tabla `propuestas_accion` (id aleatorio, usuario, acción, objetivo, estado, vence_en, resultado). |
| `models/auditoria.py` | Nueva tabla o columna `tipo` para registrar `propuesta / confirmada / cancelada / vencida / error`. |
| `api/acciones.py` (nuevo) | `POST /acciones/{id}/confirmar` y `POST /acciones/{id}/cancelar`. |
| `prompt.py` | Regla: "nunca digas que hiciste un cambio; solo propón y espera la confirmación". |
| Frontend (`modulos/asistente/`) | Bloque `accion` en `BloqueRespuesta.jsx` con la tarjeta Confirmar/Cancelar y su estado. |
| Pruebas | Sin interruptor no hay funciones; el modelo no puede ejecutar; doble clic ejecuta una vez; vencida/ajena/otro rol → rechazo; inyección en un correo no ejecuta nada. |

**Núcleo:** no requiere cambios para las 3 acciones propuestas. Sí requeriría endpoints nuevos si el gerente quiere
"confirmar un pedido suelto" o "agregar un pedido a una ruta existente".

## 7. Preguntas para el gerente

1. ¿Qué significa exactamente **"confirmar pedido"**? (¿ingreso de un recojo?, ¿resolver un observado?, ¿otra cosa?)
2. ¿"Asignar pedido a ruta" es **mover una parada** entre rutas existentes, o agregar un pedido nuevo a una ruta? Lo segundo no existe en el núcleo.
3. ¿Aprueba empezar solo con **reprogramar** (admin) y **resolver observado / registrar retorno** (almacén)?
4. ¿Cuánto tiempo debe vivir una propuesta sin confirmar? (propuesta: 5 minutos)
