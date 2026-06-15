# GeoTrack — SIOL · SAVA

Sistema logístico de última milla para una empresa de transporte/reparto. Cubre
todo el flujo: el cliente solicita el recojo por correo, el administrador importa
y enruta los pedidos desde un panel web, y el conductor ejecuta la ruta y registra
las entregas desde una app móvil.

## Estructura del monorepo

```
geotrack/
├── backend/    API REST (FastAPI + PostgreSQL + SQLAlchemy/Alembic), dockerizada
├── frontend/   Panel web del administrador (React 19 + Vite + Tailwind), Nginx
├── mobile/     App del conductor (Expo / React Native + TypeScript) — no se dockeriza
├── docker-compose.yml   Levanta db + backend + frontend con un comando
├── .env.example         Variables combinadas (copiar a .env)
└── GITFLOW.md           Flujo de trabajo de ramas del proyecto
```

## Tecnologías

- **Backend:** FastAPI, PostgreSQL, SQLAlchemy, Alembic, JWT (auth por header).
- **Frontend (admin):** React 19, Vite, Tailwind CSS 4, React Router, Recharts.
- **App móvil (conductor):** Expo (SDK 52), React Native, TypeScript, expo-router,
  React Query, react-native-maps, expo-location, expo-image-picker.
- **Infra:** Docker Compose; Nginx como reverse proxy del frontend (sirve la SPA y
  redirige `/api`, `/media` y `/socket.io` al backend).

## Requisitos

- Docker Desktop (para backend + frontend).
- Node 18+ y la app **Expo Go** (para la app móvil en desarrollo).

## 1) Levantar backend + frontend (Docker)

```bash
cp .env.example .env        # y ajusta los valores (ver abajo)
docker compose up --build
```

| Servicio | URL |
|---|---|
| Panel web (admin) | http://localhost:8080 |
| API / Swagger | http://localhost:8000/docs |

Credenciales del admin inicial (definidas en `.env`): **admin@siol.com / admin123**
(cámbialas antes de producción).

### Variables clave del `.env`
- `POSTGRES_*` / `DATABASE_URL` — base de datos (host `db`).
- `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES` — JWT.
- `ADMIN_EMAIL`, `ADMIN_PASSWORD` — admin inicial.
- `MAIL_*` — bandeja de correos (IMAP/SMTP). Con `MAIL_ENABLED=false` queda inactiva
  sin romper nada. Para Gmail usa una **contraseña de aplicación**.
- `VITE_GOOGLE_MAPS_KEY` — clave de Google Maps del panel. Vacía = OpenStreetMap; con
  clave = Google Maps (ver abajo).

### Google Maps (opcional)
Los mapas funcionan **sin** Google Maps (panel con OpenStreetMap; móvil con la clave de
Expo en Expo Go). Para usar tu propia clave de Google Maps:
1. En **Google Cloud Console** crea un proyecto, activa **facturación** y habilita
   **Maps JavaScript API** (panel) y **Maps SDK for Android/iOS** (app).
2. Crea una **clave de API** y restríngela (referentes HTTP para el panel; paquete
   `com.siolsava.geotrack` + SHA-1 para Android).
3. Pega la clave donde corresponda y reconstruye:
   - **Panel:** `VITE_GOOGLE_MAPS_KEY` en `.env` → `docker compose up -d --build frontend`.
   - **App móvil:** `EXPO_PUBLIC_GOOGLE_MAPS_KEY` en `mobile/.env` (se inyecta vía
     `app.config.js`; aplica en `eas build`).
Si dejas la clave vacía, todo sigue funcionando con los mapas gratuitos.

## 2) Correr la app móvil del conductor

```bash
cd mobile
npm install
npx expo install --check     # alinea versiones nativas con el SDK
# copia .env.example a .env y pon la IP de tu PC (no localhost):
#   EXPO_PUBLIC_API_URL=http://192.168.x.x:8000/api
npx expo start               # escanea el QR con Expo Go (mismo WiFi que la PC)
```

Compilar binario nativo (no se dockeriza): `eas build --platform android|ios`.
Ver `mobile/README.md` para el detalle.

## Funcionalidades

**Panel web (administrador)**
- Importar pedidos por Excel (se geocodifican automáticamente al subir).
- Agrupación por zonas, asignación de rutas a conductores, optimización de secuencia.
- Explorador de pedidos: búsqueda, filtros (zona/estado/fecha) y trazabilidad por pedido.
- Gestión de flota y conductores (con su ficha: nombre, teléfono, DNI).
- Dashboard con KPIs y gráficos; seguimiento de la flota.
- Bandeja de correos (solicitudes de recojo) y reportes de incidencia.

**App móvil (conductor)**
- Login JWT (sin registro; las cuentas las crea el admin).
- Ruta asignada como secuencia de paradas + mapa del recorrido.
- Iniciar ruta desde la ubicación actual (optimiza el orden).
- Marcar entregado con evidencia (foto/POD) y reportar fallas.
- Perfil con tema claro/oscuro + colores, historial y contacto a coordinación.

## Flujo de trabajo (Git)

El repositorio sigue **Gitflow** (`main` producción, `develop` integración,
ramas `feature/*`). Detalles en [GITFLOW.md](GITFLOW.md).

## Seguridad

- Secretos por variables de entorno (nunca en el repo); `.env` está en `.gitignore`.
- Autenticación JWT por header `Authorization: Bearer`; el token móvil se guarda
  cifrado (`expo-secure-store`). Acceso por roles (`admin` / `conductor`).
