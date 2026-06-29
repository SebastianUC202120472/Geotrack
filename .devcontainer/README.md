# Correr GeoTrack en GitHub Codespaces

Este `.devcontainer/` deja todo listo para correr **backend + frontend + móvil** en un
Codespace (en la nube), igual que en tu PC con Docker, usando tu **BD de Supabase**.

---

## Paso único (hazlo UNA vez, desde casa)

Las credenciales NO van en el repositorio (por seguridad quedarían en el historial). Se
guardan como **Codespaces Secrets** y quedan disponibles en todos tus Codespaces para siempre.

1. Entra a: **GitHub → tu repo `Geotrack` → Settings → Secrets and variables → Codespaces → New repository secret**.
   (O directo: `https://github.com/SebastianUC202120472/Geotrack/settings/secrets/codespaces`)
2. Agrega estos secretos (copia los valores de tu archivo local `C:\geotrack\.env`):

   | Secreto | Obligatorio | De dónde sale |
   |---------|-------------|----------------|
   | `DATABASE_URL` | **Sí** (para ver tus datos de Supabase) | la línea `DATABASE_URL=...` de tu `.env` |
   | `GOOGLE_GEOCODING_KEY` | Opcional | tu `.env` (si está vacío usa Nominatim/OSM) |
   | `VITE_GOOGLE_MAPS_KEY` | Opcional | tu `.env` (si está vacío usa OpenStreetMap) |
   | `SECRET_KEY` | Opcional | tu `.env` (si no, usa uno por defecto de demo) |

   > Si NO pones `DATABASE_URL`, la app igual corre pero contra una base local vacía
   > (sin la solicitud de Ripley ni los datos de demo).

Listo. Ya no tocas más las llaves.

---

## Día de la presentación (en la universidad)

1. En el repo, botón verde **Code → Codespaces → Create codespace on `main`**
   (o reusa el que ya tengas).
2. Espera a que termine de prepararse. **El backend y el panel se levantan solos.**
   - La **primera vez** compila las imágenes Docker (unos minutos). Las siguientes es rápido.
   - Consejo: créalo unos minutos antes para que ya esté caliente.
3. Abre la pestaña **PORTS** (abajo en VS Code):
   - **8080** → el **Panel web** (admin / almacén). Click en el globo 🌐 para abrirlo.
   - **8000** → la **API / Swagger** (`.../docs`).
   - Login admin: **admin@siol.com / admin123**.

### App móvil (Expo Go en tu teléfono)
1. En la pestaña **PORTS**, pon el puerto **8000** en visibilidad **Public**
   (click derecho en 8000 → *Port Visibility* → *Public*) para que el teléfono alcance la API.
2. En una terminal del Codespace:
   ```bash
   bash .devcontainer/mobile.sh
   ```
   Esto inicia Expo en **modo túnel** (porque el Codespace está en la nube, no en tu WiFi).
3. Escanea el **QR** con **Expo Go**. La app ya apunta sola a la API pública del Codespace.

---

## Si algo no levanta (plan B manual)
```bash
bash .devcontainer/setup.sh      # regenera los .env
docker compose up -d --build backend frontend
docker compose logs -f backend   # ver logs
```

## Notas
- La BD es **Supabase** (externa): el Codespace se conecta por internet, no necesita Postgres local.
- El mapa de la app móvil funciona con **OpenStreetMap** sin clave; el mapa nativo de Google
  requiere un *dev build* (no aplica en Expo Go).
- Los `.env` los genera el devcontainer en cada Codespace; nunca se suben al repo.
