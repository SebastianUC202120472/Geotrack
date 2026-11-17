# Asistente virtual con IA de atención al cliente (Idea 2)

Servicio aparte que atiende, en la landing y en el portal, a destinatarios y empresas que **no tienen cuenta**. Responde en español o en inglés sobre SAVA usando una base de conocimiento propia y, desde la semana 14, rastrea, reprograma y registra contactos con los endpoints públicos del portal que ya existen.

Es independiente del asistente del panel (`asistente/`, Idea 1): no comparte código importado, tablas ni interruptor. Cada uno se apaga con su variable (`ATENCION_ENABLED` / `ASISTENTE_ENABLED`).

## Estado por semana

| Semana | Contenido | Estado |
|---|---|---|
| 13 | Servicio base, token de conversación anónima, aviso de privacidad, base de conocimiento (semilla ES/EN + BM25), conversación natural ES/EN, respaldo sin IA, límites, retención | **Hecho** |
| 14 | Rastreo con verificación por DNI, reprogramación, captación de empresas, derivación a una persona, voz | **Hecho** |
| 15 | Widget en landing y portal, administración (base de conocimiento, bandeja, métricas), batería de 50+ ataques, prueba de trabajo en JS | Pendiente |

## Cómo está armado

```
app/
  api/            endpoints públicos (/api/atencion/...) y controles (origen, token)
  conocimiento/   semilla.json (FAQ ES/EN), aviso_privacidad.json, buscador BM25
  core/           configuración, tokens firmados, IP/huella, límites, fechas
  db/ models/ repositories/   tablas propias en el esquema "atencion"
  herramientas/   lista cerrada de funciones que el modelo puede pedir
  ia/             capa de proveedores con respaldo (copia adaptada de la Idea 1) y prompt
  services/       conversación, defensa (LLM01), privacidad, idioma, salida segura
docs/             borradores para el gerente y hallazgos del núcleo
scripts/          generar borradores, probar con IA real por tandas
tests/            pytest (SQLite temporal, IA simulada)
```

**Capa de IA sin acoplar.** `app/ia/proveedores.py` es una copia adaptada de la de la Idea 1. La diferencia es que recibe su configuración por parámetro (`ConfigIA`, `DefinicionProveedor`) y no lee ningún `settings` global, así que no conoce las variables de ninguno de los dos servicios. `app/ia/fabrica.py` traduce las variables `ATENCION_*` a esa capa. Si el gerente lo aprueba, en la semana 16 se puede extraer a un paquete común.

**Claves.** Las variables `ATENCION_GROQ_API_KEY`, `ATENCION_GEMINI_API_KEY` y `ATENCION_OPENROUTER_API_KEY`, si están vacías, usan `GROQ_API_KEY`, `GEMINI_API_KEY` y `OPENROUTER_API_KEY` (las de la Idea 1). Así se decidió por ahora.

## Endpoints

| Método y ruta | Para qué | Controles |
|---|---|---|
| `GET /api/atencion/estado` | El widget sabe si mostrarse | — |
| `GET /api/atencion/privacidad?idioma=es` | Aviso de privacidad (Ley 29733) | Módulo activo |
| `POST /api/atencion/conversaciones` | Abre una conversación anónima | Origen del sitio, aceptación del aviso vigente, honeypot, 10 por hora por IP |
| `POST /api/atencion/chat` | Mensaje y respuesta en tiempo real (SSE) | Origen, token `X-Conversacion` firmado, 8/min y 80/día por IP, 30 turnos por conversación, tiempo mínimo del primer mensaje, tope diario global (al llegar, responde sin IA) |
| `POST /api/atencion/verificar` | Formulario de los últimos 4 dígitos del DNI (no pasa por el modelo) | Token, 6 por conversación, más el bloqueo progresivo del núcleo |
| `POST /api/atencion/acciones/{id}/confirmar` · `/cancelar` | Clic en la tarjeta de reprogramar o de contacto | Token de la misma conversación, 3 acciones por conversación, propuesta vigente 10 min |
| `POST /api/atencion/derivaciones` | Botón «Hablar con una persona» (con contacto opcional) | Token, una derivación pendiente por conversación |
| `POST /api/atencion/voz` | Transcribe un audio con Whisper; el audio se descarta | Token, formato real, 1 MB, 60 s, 4 por minuto por IP, 10 por conversación |
| `GET /api/atencion/salud` | Salud para Docker | — |

La documentación interactiva (`/docs`) está apagada a propósito porque el servicio es público.

## Seguridad implementada en la semana 13

- **Prompt injection y jailbreak (LLM01).** Detecta intentos en español e inglés: olvidar reglas, cambiar de rol, «modo desarrollador», pedir el prompt, suplantar a un desarrollador, letras separadas. Esos mensajes viajan con un aviso del sistema y quedan marcados. La base de conocimiento llega al modelo como datos delimitados (`datos_de_sava`), y si un artículo trae órdenes, esas órdenes se omiten. El prompt lleva una marca canario secreta: si la respuesta la muestra o repite frases de las reglas, se descarta y se reemplaza por una respuesta segura.
- **Funciones cerradas.** Solo existen 5 funciones (`buscar_conocimiento`, `rastrear_pedido`, `reprogramar_entrega`, `registrar_contacto`, `derivar_a_persona`), con argumentos validados; una función inventada se rechaza sin ejecutarse.
- **Datos personales.** El DNI, los últimos dígitos del DNI escritos en el texto, los teléfonos y los correos se ocultan antes de enviarse al modelo y antes de guardarse. La IP no se guarda: solo su huella HMAC.
- **Salida segura.** Se quita el HTML. Solo se permiten enlaces a `ATENCION_DOMINIOS_PERMITIDOS` y a rutas del sitio (`/portal`); los demás se quitan, incluidos `sava.pe@otro.com`, `//otro.com` y `javascript:`. El filtro trabaja en streaming sin dejar pasar un enlace partido entre fragmentos.
- **CORS y origen.** Solo se aceptan los orígenes de `ATENCION_CORS_ORIGINS`. Un POST sin `Origin` o con un origen ajeno recibe 403.
- **Ley 29733.** Para chatear hay que aceptar la versión vigente del aviso. Las conversaciones se borran solas a los `ATENCION_RETENCION_DIAS` días.
- **Disponibilidad.** Si no queda ningún proveedor o se llega al tope diario global, el chat responde con los artículos de la base de conocimiento y el contacto humano.

## Semana 14: el portal desde el chat

- **Rastreo.** `rastrear_pedido` devuelve solo la tienda y el estado. Para ver el detalle, el widget recibe el evento `verificar` y muestra un formulario de los últimos 4 dígitos del DNI, que va **directo** al portal (`POST /verificar`): los dígitos nunca pasan por el modelo ni se guardan. El token de portal (15 min) queda en la memoria del servidor, atado a la conversación. El detalle pasa por una lista blanca: nunca salen la dirección, la placa, los apellidos del conductor, quién recibió el paquete ni el texto del motivo con órdenes ocultas.
- **Reprogramar y contacto.** El modelo solo **propone**: el widget recibe una tarjeta (`propuesta`) y el cambio se hace con el clic en Confirmar, que llama al portal sin pasar por el modelo. Las franjas salen del portal; una inventada se rechaza.
- **Datos de la empresa.** El correo y el teléfono que escribe el visitante viajan al modelo como `[CORREO_1]` y `[TEL_1]`. El valor real queda en la memoria del servidor, la tarjeta se lo muestra al mismo visitante y se envía al formulario de contacto existente. Un correo que el modelo invente se rechaza.
- **Derivación.** Puede derivar el modelo (`derivar_a_persona`), el visitante (botón) o, tras 2 mensajes seguidos sin respuesta útil, el widget lo ofrece (`ofrecer_derivacion`). Queda en la tabla `derivacion` (bandeja propia; la pantalla llega en la semana 15).
- **IP del visitante.** Cada llamada al portal lleva el `X-Real-IP` del visitante para que los límites del núcleo cuenten por persona y no por contenedor (ver `docs/hallazgos_nucleo.md`, punto 2).
- **Voz.** Whisper de Groq detecta el idioma (español o inglés). El formato se valida por su contenido real y el audio se descarta.

Eventos que emite el chat (SSE): `inicio`, `texto`, `reemplazar`, `verificar`, `propuesta`, `derivada`, `ofrecer_derivacion`, `fin` y `error`.

## Probar

```bash
cd atencion
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt pytest bandit
.venv/Scripts/python -m pytest -q
.venv/Scripts/python -m bandit -r app scripts
```

Prueba con IA real y por tandas, sin Ollama ni Docker. Lee las claves del `.env` de la raíz, no las imprime y usa una base SQLite temporal:

```bash
.venv/Scripts/python scripts/probar_preguntas.py --proveedores groq,groq_respaldo,gemini
.venv/Scripts/python scripts/probar_preguntas.py --desde 1 --hasta 5 --pausa 3
```

Contra Ollama (opcional, apagado por defecto; útil para baterías largas sin gastar cuota):

```bash
.venv/Scripts/python scripts/probar_preguntas.py --proveedores ollama --ollama-url http://localhost:11434 --ollama-modelo qwen2.5:7b
.venv/Scripts/python scripts/probar_preguntas.py --proveedores ollama --ollama-url http://localhost:11434 --ollama-modelo qwen2.5:3b
```

Borradores para el gerente, generados desde los mismos JSON que usa el servicio:

```bash
.venv/Scripts/python scripts/generar_borradores.py   # docs/faq_borrador.md y docs/aviso_privacidad_borrador.md
```

## Integración con el sistema

- `docker-compose.yml`: servicio `atencion`, sin `ports`; solo se llega a él a través de Nginx.
- `frontend/nginx.conf`: `location /api/atencion/` con resolución diferida. Si el contenedor no existe, Nginx arranca igual.
- Semana 15: widget diferido en `Landing.jsx` y `Portal.jsx`, y la ruta y la entrada de la administración en `App.jsx` y `Sidebar.jsx`.

Variables: ver `ejemplo.env`.
