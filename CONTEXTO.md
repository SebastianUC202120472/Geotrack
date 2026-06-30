# Contexto del proyecto — GeoTrack (SIOL · SAVA)

> **Documento de traspaso.** Reúne todo lo necesario para retomar el proyecto desde cero
> en otra máquina, con otra cuenta o por otra persona: qué es, cómo está construido, el flujo
> completo, las decisiones tomadas, el estado actual y lo que queda pendiente.
> Para **instalar y correr**, ver [`README.md`](README.md) y [`.devcontainer/README.md`](.devcontainer/README.md).

---

## 1. Qué es

Sistema logístico de **última milla** para una operadora de transporte/reparto (SAVA S.A.C.).
Cubre el ciclo completo de un envío con tres roles:

- **Administrador** (panel web): acepta solicitudes, agrupa por zonas, asigna rutas, resuelve
  reportes, manda auxilio, ve KPIs y liquidaciones.
- **Personal de almacén** (panel web): arma rutas de recojo, hace el **ingreso manual** de la
  mercadería que llega (marca faltantes), gestiona retornos.
- **Conductor** (app móvil): recibe su ruta, la optimiza desde su ubicación, recoge con fotos,
  entrega con evidencia (POD), reporta fallas y avisa averías.

---

## 2. Estado actual

- Versión **v1.1.0** en `main` (tag publicado). `main` y `develop` sincronizados con GitHub.
- **Desplegado** en local con Docker (backend + frontend) apuntando a **Supabase**.
- **CI** (GitHub Actions) en verde: backend (import + pytest), seguridad (bandit), frontend
  (lint+build), móvil (typecheck).
- **GitHub Codespaces** configurado (`.devcontainer/`) para correr todo en la nube.
- Los **36 casos de uso** base están implementados; el flujo recojo→entrega es funcional de
  punta a punta (validado E2E: pipeline 100% funcional, 85/85 endpoints).

---

## 3. Arquitectura

```
geotrack/
├── backend/    FastAPI + SQLAlchemy/Alembic + PostgreSQL   (dockerizado)
├── frontend/   React 19 + Vite + Tailwind 4 (Nginx)        (dockerizado)
├── mobile/     Expo SDK 52 + React Native + TypeScript      (NO se dockeriza)
├── docker-compose.yml   db + backend + frontend
└── .devcontainer/       configuración de GitHub Codespaces
```

- **Backend:** capas `api → services → repositories → models` (+ `schemas`, `core`, `db`).
  Auth JWT por header (Argon2). Roles `admin`, `almacen`, `conductor`. Códigos legibles
  (PD-001, RC-001, RT-001, CO-001, IN-001…).
- **Frontend:** SPA servida por Nginx, que hace de reverse proxy a `/api`, `/media`,
  `/socket.io` hacia el backend (mismo origen, sin CORS ni `localhost` en el bundle).
- **Móvil:** React Query con auto-refresh; token cifrado en `expo-secure-store`; cola de
  sincronización offline.

---

## 4. Flujo completo (pipeline) y estados

```
Solicitud (correo + Excel) → admin la ACEPTA → pedidos POR_RECOGER
   → almacén arma ruta de RECOJO → conductor recoge (fotos) → RECOGIDO
   → almacén INGRESO MANUAL: faltante → OBSERVADO ; llegó → LISTO_PARA_ENVIO
   → admin agrupa por ZONA y despacha → ASIGNADO
   → conductor optimiza (VRP propio) → EN_RUTA → ENTREGADO / FALLIDO
   → cierre del día
```

**Estados del pedido:** `POR_RECOGER → OBSERVADO | LISTO_PARA_ENVIO → ASIGNADO → EN_RUTA →
ENTREGADO | FALLIDO`. Un `FALLIDO` puede **reprogramarse** (→ `LISTO_PARA_ENVIO`) o
**cancelarse** (→ `CANCELADO`).

**Auxilio mecánico:** el conductor reporta avería (puede marcar "puedo solucionarlo solo");
su ruta queda **pausada**. El admin solo **manda ayuda**; **únicamente el conductor reanuda**.

---

## 5. Decisiones clave (el porqué)

- **Enrutamiento propio:** el orden de paradas se calcula con *vecino más cercano* (distancia
  Haversine) **desde la ubicación actual del conductor**; calcula km y ahorro. **No** usa Google
  Directions. (`backend/app/services/router.py`.)
- **Geocodificación:** Google Geocoding si hay clave; si no, Nominatim/OSM (gratis). Hay un
  **caché de direcciones** (`geocodificaciones_cache`) para no repetir llamadas (ahorra cuota).
- **Almacén SIN escáner:** el ingreso es **manual** — el almacén revisa las fotos del conductor,
  marca faltantes (→ `OBSERVADO`) y confirma (resto → `LISTO_PARA_ENVIO`). Se eliminó el flujo
  de escaneo de paquetes.
- **Mapas:** panel con Google Maps si hay clave, o **OpenStreetMap/Leaflet** si no. La app móvil
  usa OSM en WebView (o mapa nativo de Google con *dev build*). La navegación real es por
  **deep link a Google Maps/Waze**, parada por parada (no navega dentro de la app).
- **Base de datos:** **Supabase** (PostgreSQL), vía `DATABASE_URL`. El esquema se crea al
  arrancar con `create_all` (las migraciones Alembic están versionadas para entornos gestionados
  con Alembic, pero el contenedor usa `create_all`).
- **Bandeja de correos** (opcional, `MAIL_ENABLED`): lee solicitudes por IMAP y responde por SMTP.
- **Operaciones masivas idempotentes:** aceptar-solicitud y confirmar-ingreso insertan **por lote**
  (un solo flush) y tienen guardas de idempotencia (evitan duplicados ante reintentos/timeouts).

---

## 6. Modelo de datos (22 tablas)

Entidad central: **pedido**. Nace de una **solicitud de recojo** (que puede venir de una
**conversación de correo**), pertenece a un **cliente corporativo** y avanza por estados hasta
la entrega. Las **rutas** (tipo RECOJO o ENTREGA) se componen de **detalles de ruta**; el
**conductor** (usuario + perfil + vehículo) las ejecuta. La trazabilidad va en **historial de
pedidos**, las fotos en **evidencias de recojo/entrega**, las excepciones en **incidencias**
(auxilio) y **reportes** (entregas fallidas). Soporte: **liquidaciones**, **notificaciones**,
**parámetros**, **ubicaciones de conductor**, **solicitudes de restablecimiento** y
**caché de geocodificación**.

> El código del diagrama ER está en los archivos `modelo_bd_dbdiagram.dbml` (para
> [dbdiagram.io](https://dbdiagram.io)) y `modelo_bd_mermaid.txt`. Las tablas se definen en
> `backend/app/models/`.

---

## 7. Cómo correr (resumen — detalle en README)

```bash
# Local con Docker (BD en Supabase vía .env)
cp .env.example .env          # rellena DATABASE_URL y, opcional, las keys de Google
docker compose up --build     # Panel: http://localhost:8080 · API: http://localhost:8000/docs

# Solo reconstruir frontend (cambios web) / backend (cambios de tablas o endpoints)
docker compose up -d --build --no-deps frontend
docker compose up -d --build backend

# App móvil
cd mobile && npx expo start -c   # Expo Go (mismo WiFi); mobile/.env con EXPO_PUBLIC_API_URL
```
- **Codespaces:** ver [`.devcontainer/README.md`](.devcontainer/README.md) (todo se levanta solo;
  credenciales por *Codespaces Secrets*).
- Admin inicial: `admin@siol.com / admin123` (cambiar en producción).

---

## 8. Reglas de trabajo

- **Gitflow:** todo el desarrollo en ramas `feature/<nombre>` desde `develop`; se integra a
  `develop` con `merge --no-ff`; `develop` se promueve a `main` por versión. Borrar la rama
  feature tras el merge.
- **Idioma:** código, nombres y comentarios en **español**. Cada función lleva un comentario
  simple de qué hace y qué recibe.
- **Arquitectura limpia:** respetar las capas (backend) y la separación UI/lógica/datos (móvil).
- **Verificación antes de dar algo por hecho** (no hay tests E2E automáticos):
  - Frontend: `cd frontend && npm run build && npm run lint` (baseline ~9–14 problemas de lint
    preexistentes por "setState síncrono en effect"; no introducir errores nuevos).
  - Backend: importar la app: `docker compose run --rm backend python -c "import app.main"`.
  - Móvil: `cd mobile && npx tsc --noEmit` debe dar exit 0.

---

## 9. Pendientes y mejoras (roadmap)

**Seguridad (prioritario, AÚN NO implementado):**
- `SECRET_KEY` es un placeholder en el `.env`: generar una clave fuerte y aleatoria.
- Admin por defecto `admin@siol.com / admin123` re-sembrado en cada arranque: cambiarlo.
- `/media` se sirve **público sin autenticación** (incluye fotos POD con datos del
  destinatario): servirlo tras autenticación o con URLs firmadas.
- Sin rate-limit/bloqueo en `/login`: añadir throttling.
- Subida de fotos validada solo por extensión: validar MIME real + tamaño máximo.
- Restringir y separar las **keys de Google** (la del mapa viaja al navegador = pública;
  ponerle tope de cuota y, idealmente, usar una key distinta para geocoding).

**Rendimiento (diferido, menor):**
- Endpoints de flota (polling ~15 s) con N+1 por ruta.
- Falta índice único parcial para garantizar "una sola ruta activa" por conductor a nivel de BD
  (hoy se valida en el servicio).

---

## 10. Gotchas (cosas que muerden)

- `get_db` **no auto-commitea**: los servicios deben hacer `commit` explícito.
- El esquema se crea con `create_all` al arrancar (el contenedor **no** corre el CLI de Alembic).
- Reconstruir la imagen del **frontend** tras cambios web (es build estático); el **backend**
  solo cuando cambian dependencias, endpoints o tablas.
- Docker Desktop puede ponerse inestable (reintentar / reiniciar el contenedor si un `up`/`build`
  se cuelga).
- La BD es **compartida** (Supabase): cuidado con datos de demo y reseteos.

---

## 11. Credenciales (NO están en el repositorio)

- El `.env` real está **gitignored** — nunca se sube. En Codespaces se inyecta vía el secreto
  `DOTENV` (o secretos individuales). Ver [`.devcontainer/README.md`](.devcontainer/README.md).
- Lo que vive solo en el `.env` local / secretos: `DATABASE_URL` (Supabase), `SECRET_KEY` y las
  keys de Google.
- Cuenta de admin de demo: `admin@siol.com / admin123` (es el valor por defecto documentado).
  Las cuentas de almacén y conductor tienen una contraseña de demo en la BD; si no la conoces,
  restablécela desde el panel del admin.

---

## 12. Cómo retomar el contexto en otra cuenta o máquina

1. Clona el repositorio y abre el asistente de programación sobre la carpeta del proyecto.
2. Como **primer mensaje**, indícale: *"Lee `CONTEXTO.md` y `README.md` para tener todo el
   contexto y alcance del proyecto antes de empezar."*
3. Con eso, el asistente conoce el qué, el cómo, el flujo, las decisiones, el estado y lo
   pendiente — sin que tengas que re-explicar nada.

> Si sigues en la **misma computadora** y solo cambias de cuenta, la memoria local del proyecto
> (en tu carpeta de usuario, fuera del repo) puede seguir disponible; pero este `CONTEXTO.md`
> es la fuente portable y definitiva para cualquier máquina o persona.
