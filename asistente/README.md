# Asistente virtual con IA del panel

Servicio aparte (FastAPI, puerto interno `8100`) que responde preguntas del panel administrativo
consultando el backend con el token del usuario. Nginx lo publica en `/api/asistente/`
(ver `frontend/nginx.conf`) y se activa con `ASISTENTE_ENABLED=true` en el `.env` de la raíz.

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
- **`ERROR 503: El asistente no está disponible`**: ningún proveedor de IA respondió. Revisa
  `docker logs geotrack-asistente-1`: si dice que el modelo no existe o no está disponible,
  actualiza `GEMINI_MODELO`, `GROQ_MODELO` u `OPENROUTER_MODELO` en el `.env` y reinicia con
  `docker compose up -d asistente`.
- **`falta el conductor ...` al correr `preparar_demo.py`**: vuelve a correr el paso 2.
