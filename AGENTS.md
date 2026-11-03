# AGENTS.md — GeoTrack

Monorepo de última milla (backend + panel web + app móvil). **`README.md` de la raíz es la fuente principal**: no la dupliques aquí, remítete a ella y a `docs/CHECKLIST_PRODUCCION.md`. Este archivo solo cubre lo que no es obvio.

## Estructura

- `backend/` — FastAPI + SQLAlchemy + PostgreSQL (Docker). Capas: `api/` (ruteo), `services/` (lógica), `repositories/` (datos), `models/`, `schemas/`, `core/` (config, seguridad), `db/`.
- `frontend/` — React 19 + Vite + Tailwind, **JSX (no TypeScript)**. Se sirve con Nginx en `:8080` y proxieda `/api`, `/media` y `/socket.io` al backend (mismo origen). Librería de UI propia en `src/components/ui/`.
- `mobile/` — Expo SDK 54 + TypeScript + expo-router. **No se dockeriza.**
- `docker-compose.yml` — `db` + `backend` + `frontend` (puertos `8000` y `8080`). El móvil corre aparte.

## Puesta en marcha

- Crear `.env` en la raíz (plantilla en README §5.2). Nunca subirlo. `ACCESS_TOKEN_EXPIRE_MINUTES` **vacío hace que el backend no arranque** (pydantic no parsea un int vacío).
- Levantar: `docker compose up -d --build`. El esquema y el admin inicial se crean solos al arrancar.

## Verificación (orden del CI)

```bash
cd frontend && npm install && npm run build && npm run lint
cd mobile && npm ci && npm run typecheck
cd backend && pip install -r requirements.txt && pip install pytest && pytest -q
```

- Un solo test: `cd backend && pytest tests/test_smoke.py -q`. **`pytest` no está en `requirements.txt`** (el CI lo instala aparte).
- Los tests son de humo y **no necesitan BD**; corren desde `backend/`.
- Importar la app sin Docker: `docker compose run --rm --no-deps backend python -c "import app.main"`.
- CI (`.github/workflows/ci.yml`): el `lint` de frontend y el `pip-audit` **no bloquean** (solo informativos); el build y el `tsc --noEmit` sí.

## Gotchas de build y entorno

- El backend copia su código en la imagen y el frontend es un build estático: para ver un cambio hay que **reconstruir** la imagen (`docker compose up -d --build --no-deps frontend|backend`). `restart` no relee `.env`; para eso hay que recrear (`up -d`).
- `VITE_GOOGLE_MAPS_KEY` y `VITE_API_URL`/`VITE_WS_URL` se hornean en el build de frontend → reconstruir tras cambiarlas.
- Host de la BD en Compose es `db`, **no** `localhost`.
- Scripts de demo se corren dentro del contenedor: `docker compose exec backend python scripts/seed_portal_demo.py`.
- Móvil: `mobile/.env` con `EXPO_PUBLIC_API_URL` (IP real de la PC, no `localhost`) y `EXPO_PUBLIC_GOOGLE_MAPS_KEY`. Expo Go: `npx expo start --go -c`. El mapa nativo de Google y la ubicación en segundo plano **solo en dev build**; EAS no ve `mobile/.env` (definir en expo.dev).
- `CORS_ORIGINS` debe quedar **vacío** en producción (todo llega por Nginx); nunca `*`.
- Modos demo, nunca en producción: `PORTAL_OTP_DEMO`, `ALMACEN_INGRESO_DIRECTO`.
- `ZONA_HORARIA` por defecto `America/Lima` (define el "día" en reportes).
- `.gitattributes` fuerza LF en `*.sh` y `*.yml`: respetarlo (un CRLF rompe los scripts en Linux/Codespaces).

## Esquema de BD (importante)

- El esquema se aplica **al arrancar**: `Base.metadata.create_all` + sentencias idempotentes en `backend/app/db/migraciones.py`. Las migraciones de Alembic (`backend/alembic/`) están versionadas pero **no son lo que aplica el esquema en runtime**.
- Al agregar una columna, además del campo en el modelo debes añadir `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` **al final** de `SENTENCIAS` (nunca reordenar ni borrar entradas). `create_all` no altera tablas ya existentes.

## Git y CI

- Gitflow: `main` (producción) ← `develop` (integración) ← `feature/*`. Integrar features a `develop` con `--no-ff`. CI en push/PR a `develop` y `main`.
- Dependabot revisa semanalmente y abre PRs agrupados; ignora saltos de versión mayor.
- Los comentarios y la documentación del repo están en español; mantener ese idioma.
