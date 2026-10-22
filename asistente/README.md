# Asistente virtual con IA del panel

Servicio aparte (FastAPI, puerto interno `8100`) que responde preguntas del panel administrativo
consultando el backend con el token del usuario. Nginx lo publica en `/api/asistente/`
(ver `frontend/nginx.conf`) y se activa con `ASISTENTE_ENABLED=true` en el `.env` de la raíz.

## Modelos de IA por defecto

Todos los modelos se llaman con function calling (herramientas) por la API compatible con
OpenAI de cada proveedor.

| Nombre en `ASISTENTE_PROVEEDORES` | Variable del modelo     | Valor por defecto        | Nota |
|-----------------------------------|-------------------------|--------------------------|------|
| `gemini`                          | `GEMINI_MODELO`         | `gemini-3.5-flash-lite`  | `gemini-2.5-flash` ya no se habilita en proyectos nuevos (404). `gemini-3.8-flash` también sirve, pero suele dar 503 por alta demanda. |
| `groq`                            | `GROQ_MODELO`           | `openai/gpt-oss-120b`    | `llama-3.3-70b-versatile` puede no estar disponible en tu cuenta (404 `model_not_found`). |
| `groq_respaldo`                   | `GROQ_MODELO_RESPALDO`  | `openai/gpt-oss-20b`     | Misma `GROQ_API_KEY`. Groq pone los límites por modelo: cuando el 120b da 429, este suele seguir libre. Déjalo vacío para no usarlo. |
| `openrouter`                      | `OPENROUTER_MODELO`     | `meta-llama/llama-3.3-70b-instruct:free` | Solo si hay `OPENROUTER_API_KEY`. |
| `ollama`                          | `OLLAMA_MODELO`         | `qwen2.5:7b`             | Solo si hay `OLLAMA_URL`. |

### Orden y respaldo

`ASISTENTE_PROVEEDORES` define el orden; por defecto es
`gemini,groq,groq_respaldo,openrouter,ollama`. Los que no tienen clave (o modelo) se omiten solos.
Para que Groq sea el principal en una demo:

```env
ASISTENTE_PROVEEDORES=groq,groq_respaldo,gemini,openrouter,ollama
```

Un proveedor pasa al siguiente, y queda en pausa unos segundos, cuando responde 429 (límite), 5xx
o no empieza a responder dentro de `ASISTENTE_IA_PRIMER_FRAGMENTO_SEG` (20 s por defecto). El
plazo solo cuenta hasta el primer fragmento: una respuesta que ya empezó a mostrarse no se corta ni
cambia de proveedor a mitad. Entre fragmentos se espera como máximo `ASISTENTE_IA_TIMEOUT_SEG`
(20 s) y la conexión, 5 s. Si fallan todos, el usuario ve "El asistente está saturado, intenta en
unos segundos." y el detalle técnico queda solo en `docker logs geotrack-asistente-1`.

Los modelos que ve cada cuenta cambian con el tiempo. Para listar los tuyos sin imprimir las claves:

```bash
docker exec geotrack-asistente-1 python -c "import os,httpx; print(*sorted(m['id'] for m in httpx.get('https://api.groq.com/openai/v1/models', headers={'Authorization': 'Bearer '+os.environ['GROQ_API_KEY']}).json()['data']), sep='\n')"
docker exec geotrack-asistente-1 python -c "import os,httpx; print(*sorted(m['name'][7:] for m in httpx.get('https://generativelanguage.googleapis.com/v1beta/models', params={'key': os.environ['GEMINI_API_KEY'], 'pageSize': 1000}).json()['models']), sep='\n')"
```

Para cambiar de modelo, define `GEMINI_MODELO` o `GROQ_MODELO` en el `.env` de la raíz y aplica el
cambio con `docker compose up -d asistente`.

## Preparar la demo en cualquier PC

Los scripts de `asistente/scripts/` usan solo la librería estándar de Python (3.9 o superior):
no hace falta instalar nada ni activar un entorno virtual. Del `.env` de la raíz leen **solo**
`ADMIN_EMAIL` y `ADMIN_PASSWORD`, y nunca imprimen la contraseña ni el token.

1. **Levanta todo** desde la raíz del repo, con `ASISTENTE_ENABLED=true` y al menos una clave de
   proveedor de IA (`GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY`) en el `.env`:

   ```bash
   docker compose up -d --build
   ```

2. **Crea los conductores de la demo** (4 vehículos y 4 conductores, cada uno con su vehículo):

   ```bash
   python asistente/scripts/crear_conductores.py
   ```

   | Conductor   | Correo                | Vehículo |
   |-------------|-----------------------|----------|
   | Juan Pérez  | `juan@prueba.com`     | ABC-101  |
   | Rosa Medina | `rosa.medina@sava.pe` | ABC-102  |
   | Luis Chávez | `luis.chavez@sava.pe` | ABC-103  |
   | Marta Silva | `marta.silva@sava.pe` | ABC-104  |

   Son los que exige `backend/scripts/preparar_demo.py`. El script se puede correr varias veces:
   no duplica nada y solo corrige la asignación de vehículos si hace falta. Los conductores nuevos
   entran a la app con `Conductor2026!` (cámbiala con `--clave-conductores "Otra2026!"`).

3. **Siembra los datos de la demo** (pedidos de hoy, rutas y el correo pendiente en la Bandeja):

   ```bash
   docker exec geotrack-backend-1 python scripts/preparar_demo.py --si
   ```

4. **Prueba el asistente** con las preguntas de `asistente/scripts/preguntas.txt`:

   ```bash
   python asistente/scripts/probar_asistente.py
   python asistente/scripts/probar_asistente.py "¿Cómo va el día de hoy?"     # preguntas sueltas
   python asistente/scripts/probar_asistente.py --misma-conversacion          # prueba el contexto
   ```

   Por cada pregunta imprime la respuesta, los bloques (tablas, gráficos y enlaces), los pasos de
   consulta y los errores; al final dice cuántas salieron sin errores (código de salida 1 si alguna
   falló). Entre preguntas espera 7 s (`--pausa`) para no chocar con el límite de 10 por minuto.

Opciones comunes: `--url` (por defecto `http://localhost:8080`, la URL de Nginx) y `--env` (ruta
de otro `.env`).

### Si algo falla

- **`no se pudo conectar`**: los contenedores no están levantados o Nginx usa otro puerto (`--url`).
- **`demasiados intentos de login`**: el login admite 5 intentos por minuto; espera y repite.
- **`ERROR 503: El asistente está saturado`**: ningún proveedor de IA respondió. Revisa
  `docker logs geotrack-asistente-1`:
  - Si dice `429` (límite de uso) o `503` (alta demanda), espera unos segundos o pon primero
    otro proveedor en `ASISTENTE_PROVEEDORES`.
  - Si dice que el modelo no existe o no está disponible (404), actualiza `GEMINI_MODELO`,
    `GROQ_MODELO`, `GROQ_MODELO_RESPALDO` u `OPENROUTER_MODELO` en el `.env`.

  En ambos casos aplica los cambios con `docker compose up -d asistente`.
- **`falta el conductor ...` al correr `preparar_demo.py`**: vuelve a correr el paso 2.
