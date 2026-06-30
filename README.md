# GeoTrack — SIOL · SAVA

**Sistema logístico de última milla** para una operadora de transporte y reparto (SAVA S.A.C.).
Cubre el ciclo completo de un envío: el **cliente** solicita el recojo por correo, el **administrador**
lo acepta e importa los pedidos, el **almacén** valida la mercadería que llega, y el **conductor**
recoge, reparte y cierra su ruta — todo trazado, estado por estado, desde un panel web y una app móvil.

> 📋 ¿Retomas el proyecto desde cero (otra máquina/persona)? Lee [`CONTEXTO.md`](CONTEXTO.md):
> reúne el flujo completo, las decisiones, el estado actual y lo pendiente.

---

## 1. ¿Qué es?

GeoTrack coordina a tres roles alrededor de un mismo pedido:

| Rol | Dónde trabaja | Qué hace |
|-----|---------------|----------|
| **Administrador** | Panel web | Acepta solicitudes (Excel), agrupa por zonas, asigna rutas, resuelve reportes, manda auxilio, ve KPIs y liquidaciones. |
| **Almacén** | Panel web | Arma rutas de recojo, hace el **ingreso manual** de lo recogido (marca faltantes), gestiona retornos. |
| **Conductor** | App móvil | Recibe su ruta, optimiza el orden desde su ubicación, recoge con fotos, entrega con evidencia (POD), reporta fallas y avisa averías. |

### El pipeline de un pedido

```
  Solicitud (correo + Excel)
        │  el admin la ACEPTA
        ▼
  POR_RECOGER ──────────────► almacén arma ruta de recojo
        │                         │  el conductor recoge (fotos)
        │                         ▼
        │                     RECOGIDO ──► almacén hace INGRESO MANUAL
        │                                     │  faltante → OBSERVADO
        ▼                                     ▼  llegó    → LISTO_PARA_ENVIO
  (geocodificación en 2.º plano)                 │  el admin agrupa por ZONA y despacha
                                                 ▼
                                            ASIGNADO ──► el conductor optimiza ──► EN_RUTA
                                                                                      │
                                                                          entrega ◄───┤
                                                                  ENTREGADO / FALLIDO │
                                                                                      ▼
                                                                            cierre del día
```

**Estados del pedido:** `POR_RECOGER → OBSERVADO | LISTO_PARA_ENVIO → ASIGNADO → EN_RUTA → ENTREGADO | FALLIDO`
(un `FALLIDO` puede **reprogramarse** → vuelve a `LISTO_PARA_ENVIO`, o **cancelarse** → `CANCELADO`).

### Detalles que vale la pena saber
- **Enrutamiento propio:** el orden de las paradas se calcula con un algoritmo de *vecino más cercano*
  (distancia Haversine) **desde la ubicación actual del conductor**. No usa Google Directions.
- **Geocodificación:** convierte cada dirección en coordenadas con **Google Geocoding** (si hay clave)
  o **Nominatim/OSM** (gratis) como respaldo, con un **caché de direcciones** para no repetir llamadas.
- **Auxilio mecánico:** el conductor reporta una avería (puede marcar "puedo solucionarlo solo"); su
  ruta queda **pausada**. El admin solo **manda ayuda**; **únicamente el conductor reanuda**.
- **Mapas:** el panel usa Google Maps si hay clave, o OpenStreetMap si no. La navegación real se delega
  por *deep link* a Google Maps / Waze, parada por parada.

---

## 2. Arquitectura

```
geotrack/
├── backend/    API REST — FastAPI + PostgreSQL + SQLAlchemy/Alembic   (dockerizado)
├── frontend/   Panel web del admin/almacén — React 19 + Vite + Tailwind (Nginx, dockerizado)
├── mobile/     App del conductor — Expo (SDK 52) + React Native + TypeScript (NO se dockeriza)
├── docker-compose.yml   Levanta db + backend + frontend con un comando
└── .env.example         Plantilla de variables (copiar a .env)
```

| Capa | Tecnologías |
|------|-------------|
| **Backend** | FastAPI · SQLAlchemy · Alembic · PostgreSQL · JWT (Argon2) · geopy (Google/Nominatim) |
| **Frontend** | React 19 · Vite · Tailwind CSS 4 · React Router · Recharts · `@react-google-maps/api` / Leaflet |
| **Móvil** | Expo SDK 52 · React Native · TypeScript · expo-router · React Query · react-native-maps · expo-location |
| **Infra** | Docker Compose · Nginx (reverse proxy: sirve la SPA y redirige `/api`, `/media`, `/socket.io` al backend) |

> El navegador del panel **no** llama al backend en `:8000` directamente: Nginx (puerto `8080`) hace de
> *reverse proxy*, así que todo es el mismo origen (sin CORS ni `localhost` hardcodeado en el bundle).

---

## 3. ¿Qué se necesita? (Requisitos)

| Para… | Necesitas |
|-------|-----------|
| Backend + Panel web | **Docker Desktop** (Compose v2). Nada más: Python y Node corren dentro de los contenedores. |
| Base de datos | Incluida (contenedor `db`, PostgreSQL 15) **o** una propia (p. ej. **Supabase**) vía `DATABASE_URL`. |
| App móvil (desarrollo) | **Node 18+**, la app **Expo Go** en el teléfono y la PC en la **misma red WiFi**. |
| App móvil (mapa nativo y ubicación en 2.º plano) | Un **dev build** de Expo (`eas build`); Expo Go no soporta mapas nativos. |
| Mapas/geocoding de Google (opcional) | Proyecto en **Google Cloud** con facturación + claves de API (ver §4.4). |
| Bandeja de correos (opcional) | Una cuenta de correo con IMAP/SMTP (en Gmail, una *contraseña de aplicación*). |

---

## 4. Instalación detallada

### 4.1 Clonar y preparar el `.env`
```bash
git clone https://github.com/SebastianUC202120472/Geotrack.git
cd Geotrack
cp .env.example .env        # Windows:  copy .env.example .env
```
Abre `.env` y ajusta los valores. Grupos de variables:

| Grupo | Variables | Notas |
|-------|-----------|-------|
| **Base de datos** | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DATABASE_URL` | El host es `db` (nombre del servicio en Compose), **no** `localhost`. |
| **Seguridad / JWT** | `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES` | Genera una clave fuerte: `python -c "import secrets; print(secrets.token_hex(32))"`. |
| **Admin inicial** | `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Se crea solo al arrancar si no existe. **Cámbialos antes de producción.** |
| **Mapas panel** | `VITE_GOOGLE_MAPS_KEY` | Vacía = OpenStreetMap (gratis). Con clave = Google Maps. |
| **Geocoding backend** | `GOOGLE_GEOCODING_KEY` | Vacía = Nominatim/OSM (gratis, menos preciso). Con clave = Google (preciso). |
| **Correo (opcional)** | `MAIL_ENABLED`, `MAIL_*`, `IMAP_*`, `SMTP_*` | Con `MAIL_ENABLED=false` la bandeja queda inactiva y el resto funciona igual. |

### 4.2 Elegir la base de datos
- **Opción A — local (por defecto):** deja `DATABASE_URL` apuntando a `db` (lo que trae `.env.example`).
  El contenedor `db` levanta un PostgreSQL con volumen persistente.
- **Opción B — Supabase u otra remota:** reemplaza `DATABASE_URL` por la cadena de tu proveedor, p. ej.:
  ```
  DATABASE_URL=postgresql://postgres.<ref>:<password>@aws-...pooler.supabase.com:5432/postgres?sslmode=require
  ```
  (En Supabase, si la contraseña tiene `@`, escríbelo como `%40`.) El contenedor `db` puede seguir
  arrancando pero quedará sin uso.

> El esquema se crea solo al arrancar (`create_all`) y se siembra el admin inicial. Las migraciones de
> Alembic están versionadas para entornos ya gestionados con Alembic.

### 4.3 Levantar backend + panel
```bash
docker compose up --build
```
| Servicio | URL |
|----------|-----|
| **Panel web** (admin / almacén) | http://localhost:8080 |
| **API + Swagger** | http://localhost:8000/docs |

Inicia sesión en el panel con el admin de tu `.env` (por defecto **admin@siol.com / admin123**).

### 4.4 Claves de Google (opcional)
Todo funciona **sin** Google (panel con OSM; geocoding con Nominatim). Para activarlo:
1. En **Google Cloud Console**: crea un proyecto, activa **facturación** y habilita
   **Maps JavaScript API** (panel), **Geocoding API** (backend) y **Maps SDK for Android/iOS** (app).
2. Crea claves y **restríngelas** (referentes HTTP para el panel; API concreta + tope de cuota para geocoding).
3. Pega cada clave donde corresponde y reconstruye:
   - Panel → `VITE_GOOGLE_MAPS_KEY` en `.env` → `docker compose up -d --build frontend`.
   - Backend → `GOOGLE_GEOCODING_KEY` en `.env` → `docker compose up -d --build backend`.
   - Móvil → `EXPO_PUBLIC_GOOGLE_MAPS_KEY` en `mobile/.env` (aplica en `eas build`).

### 4.5 App móvil del conductor
```bash
cd mobile
npm install
npx expo install --check          # alinea versiones nativas con el SDK
cp .env.example .env              # y pon la IP de tu PC (no localhost):
#   EXPO_PUBLIC_API_URL=http://192.168.x.x:8000/api
npx expo start -c                 # escanea el QR con Expo Go (misma WiFi)
```
Para el **mapa nativo** y la **ubicación en segundo plano** se necesita un *dev build*:
`eas build --platform android` (ver `mobile/README.md`).

---

## 5. Comandos habituales (desarrollo y despliegue)

| Quiero… | Comando |
|---------|---------|
| Levantar todo (1.ª vez o tras cambios) | `docker compose up --build` |
| Levantar en segundo plano | `docker compose up -d --build` |
| Reconstruir **solo el panel** (cambios de frontend) | `docker compose up -d --build --no-deps frontend` |
| Reconstruir **solo el backend** (cambios de API/tablas) | `docker compose up -d --build backend` |
| Reconstruir backend **y** panel | `docker compose up -d --build backend frontend` |
| Ver logs en vivo | `docker compose logs -f backend` |
| Parar todo | `docker compose down` |
| Parar y **borrar la BD local** | `docker compose down -v` |
| Correr la app móvil | `cd mobile && npx expo start -c` |

> El panel es un **build estático** servido por Nginx: para ver cambios web hay que **reconstruir** su
> imagen. El backend solo necesita reconstruirse cuando cambian dependencias, endpoints o tablas.

**Verificación antes de dar algo por hecho** (no hay tests automatizados; se valida con build/typecheck):
```bash
# Frontend
cd frontend && npm run build && npm run lint
# Backend (sintaxis + importación de la app dentro de la imagen)
docker compose run --rm backend python -c "import app.main"
# Móvil (TypeScript)
cd mobile && npx tsc --noEmit
```

---

## 6. ¿Cómo se usa?

Recorrido de punta a punta de un envío:

1. **Solicitud (Bandeja).** Llega un correo del cliente con un Excel de pedidos. Aparece en la **Bandeja**
   del panel.
2. **Aceptar (admin).** El admin abre la conversación y la **acepta** subiendo el Excel → se crean los
   pedidos en `POR_RECOGER` y se geocodifican en segundo plano. La conversación queda `ATENDIDA`.
3. **Armar recojo (almacén).** En **Armar ruta de recojo**, el almacén asigna las solicitudes a un
   conductor + vehículo.
4. **Recoger (conductor).** El conductor abre su ruta de recojo, **optimiza** desde su ubicación y
   **registra la recepción** con varias fotos → el recojo queda `RECOGIDO`.
5. **Ingreso manual (almacén).** En **Ingreso de almacén**, el almacén ve la galería de fotos, marca lo
   **faltante** (→ `OBSERVADO`) y **confirma**: el resto pasa a `LISTO_PARA_ENVIO`. Los observados se
   resuelven cuando se aclaran.
6. **Despachar (admin).** En **Agrupación por zonas**, el admin elige una zona (distrito) y crea una
   **ruta de entrega** para un conductor. Los pedidos pasan a `ASIGNADO`.
7. **Entregar (conductor).** El conductor **optimiza** la ruta, navega parada por parada (deep link a
   Google Maps), marca **ENTREGADO** con foto (POD) o **FALLIDO** con motivo (genera un reporte).
8. **Reportes y auxilio (admin/conductor).** El admin **responde** los reportes y **reprograma o cancela**
   los fallidos. Ante una avería, el conductor reporta auxilio (ruta pausada), el admin **manda ayuda** y
   el conductor **reanuda**.
9. **Cierre del día (conductor).** Cuando no quedan paradas pendientes, el conductor **cierra la ruta**.

A lo largo del flujo, el panel muestra el **Dashboard** (KPIs y gráficos), el **Seguimiento de
conductores** (mapa de flota en vivo), la **Trazabilidad** por pedido y las **Liquidaciones** por cliente.

> **Probar el lado conductor sin la app:** mientras no haya *dev build*, el flujo del conductor se puede
> ejercitar por los endpoints `/api/conductor/*` (login → manifiesto → optimizar → marcar
> entregado/fallido → reportar → auxilio → reanudar). Todo se refleja en el panel. Ver Swagger en
> http://localhost:8000/docs.

---

## 7. Notas de seguridad (antes de producción)

- **Genera un `SECRET_KEY` fuerte y aleatorio** y **cambia `ADMIN_PASSWORD`** — no dejes los valores de
  ejemplo.
- Mantén `.env` fuera del repositorio (ya está en `.gitignore`) y **restringe** las claves de Google con
  topes de cuota.
- La autenticación es por **JWT** (`Authorization: Bearer`) con control por roles (`admin`, `almacen`,
  `conductor`); en la app el token se guarda cifrado (`expo-secure-store`).

---

## 8. Flujo de trabajo (Git)

El repositorio sigue **Gitflow**: `main` (producción) ← `develop` (integración) ← ramas `feature/*`.
Las features se integran a `develop` con `merge --no-ff`; `develop` se promueve a `main` para cada versión.
