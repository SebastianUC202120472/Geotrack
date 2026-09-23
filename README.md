# GeoTrack — Plataforma logística de última milla

Sistema de reparto de última milla para una operadora de transporte y distribución. Cubre el ciclo completo de un envío: el **cliente** solicita el recojo por correo, el **administrador** lo acepta e importa los pedidos, el **almacén** valida la mercadería que llega y el **conductor** recoge, reparte y cierra su ruta — cada estado queda trazado, desde un panel web y una app móvil.

Diseñé y construí todo el sistema como su único ingeniero — backend, panel web, app móvil e infraestructura — y después actué como mi propio ingeniero de seguridad: modelado de amenazas, diseño de controles, búsqueda de vulnerabilidades, remediación y nueva verificación.

**Stack:** Python · FastAPI · PostgreSQL · React 19 · React Native (Expo) + TypeScript · Docker · Nginx · GitHub Actions

> **¿Solo quieres levantarlo?** Ve directo a la [guía para correr todo](#5-guía-para-correr-todo).

---

## 1. Qué hace

GeoTrack coordina tres roles alrededor de un mismo pedido:

| Rol | Dónde trabaja | Qué hace |
| --- | --- | --- |
| **Administrador** | Panel web | Acepta solicitudes (Excel), agrupa por zonas, asigna rutas, resuelve reportes de incidencias, envía auxilio mecánico, revisa KPIs y liquidaciones. |
| **Almacén** | Panel web | Arma rutas de recojo, hace el ingreso manual de lo recogido (marcando faltantes) y gestiona los retornos. |
| **Conductor** | App móvil | Recibe su ruta, optimiza el orden de las paradas desde su ubicación, recoge con fotos, entrega con prueba de entrega (POD) y reporta fallas y averías. |

Además hay un **sitio público**: una landing con estadísticas reales de la operación y un **portal de clientes**, donde una persona rastrea su pedido y una empresa entra a su panel corporativo.

### Ciclo de un pedido

```
Solicitud (correo + Excel)
      │  el admin la ACEPTA
      ▼
POR_RECOGER ──────────────► el almacén arma la ruta de recojo
      │                        │  el conductor recoge (fotos)
      │                        ▼
      │                    RECOGIDO ──► el almacén hace el INGRESO MANUAL
      │                                     │  faltante → OBSERVADO
      ▼                                     ▼  completo → LISTO_PARA_ENVIO
(geocodificación en 2.º plano)                 │  el admin agrupa por ZONA y despacha
                                               ▼
                                          ASIGNADO ──► el conductor optimiza ──► EN_RUTA
                                                                                   │
                                                                      entrega ◄────┤
                                                              ENTREGADO / FALLIDO  │
                                                                                   ▼
                                                                          cierre del día
```

Un pedido `FALLIDO` puede **reprogramarse** (vuelve a `LISTO_PARA_ENVIO`) o **cancelarse** (`CANCELADO`).

### Decisiones de diseño que vale la pena destacar

- **Enrutamiento propio, no una API de pago.** El orden de las paradas se calcula con un algoritmo de vecino más cercano sobre distancia Haversine, **desde la posición real del conductor**. No depende de Google Directions: menor costo, sin límites de cuota y control total sobre la heurística.
- **Geocodificación que se degrada con elegancia.** Google Geocoding cuando hay clave de API, Nominatim/OSM como respaldo gratuito, y un caché de direcciones para no pagar dos veces la misma dirección.
- **Auxilio mecánico con una separación de autoridad deliberada.** Cuando un conductor reporta una avería, su propia ruta queda en pausa. El admin puede *enviar ayuda*, pero **no puede reanudar la ruta** — solo el conductor puede. Es una decisión de separación de funciones, no una limitación de la interfaz: quien conoce el estado real del vehículo es el único que puede declarar que es seguro continuar.
- **La navegación se delega.** La navegación giro a giro se abre por *deep link* en Google Maps o Waze, parada por parada, en lugar de reimplementarla.

---

## 2. Arquitectura

```
geotrack/
├── backend/    API REST — FastAPI + PostgreSQL + SQLAlchemy/Alembic          (dockerizado)
├── frontend/   Landing, portal de clientes y panel — React 19 + Vite + Tailwind (Nginx, dockerizado)
├── mobile/     App del conductor — Expo SDK 52 + React Native + TypeScript    (no se dockeriza)
├── .devcontainer/   Configuración para GitHub Codespaces
└── docker-compose.yml   db + backend + frontend
```

| Capa | Tecnologías |
| --- | --- |
| **Backend** | FastAPI · SQLAlchemy · Alembic · PostgreSQL · JWT (Argon2) · geopy |
| **Frontend** | React 19 · Vite · Tailwind CSS 4 · React Router · Recharts · Google Maps / Leaflet |
| **Móvil** | Expo SDK 52 · React Native · TypeScript · expo-router · React Query · react-native-maps |
| **Infra** | Docker Compose · proxy inverso Nginx · CI en GitHub Actions |

**El navegador nunca habla directamente con la API.** Nginx (puerto `8080`) sirve la SPA y redirige `/api`, `/media` y `/socket.io` al backend. Todo es del mismo origen: no hay configuración de CORS que se pueda equivocar ni un `localhost` fijo dentro del bundle de producción.

| Ruta | Qué es |
| --- | --- |
| `/` | Landing pública con estadísticas reales |
| `/portal` | Portal de clientes: rastreo por código + DNI y panel corporativo |
| `/panel` | Panel de administración y almacén (requiere inicio de sesión) |

### Sistema de diseño

El panel web está construido sobre **frontend-geotrack**, una librería de componentes propia (12 componentes: `Button`, `Card`, `StatCard`, `EstadoBadge`, `Modal`, `PageHeader`, `Input`, `PasswordInput`, `Badge`, `Logo`, `Skeleton`, `SkeletonStat`) con 120 *design tokens*. Los componentes se configuran por props en lugar de clases utilitarias sueltas, así el lenguaje visual se mantiene coherente a medida que crece el panel. `EstadoBadge`, en particular, recibe el código de estado de un pedido y deriva su propio color, de modo que el estado se ve idéntico en todas partes.

---

## 3. Seguridad

La seguridad se diseñó desde el inicio en lugar de añadirse al final. Esta sección documenta el modelo de amenazas, los controles y el trabajo de vulnerabilidades que hice sobre mi propio código.

### Modelo de amenazas

| Amenaza | Por qué importa aquí | Control |
| --- | --- | --- |
| Acceso no autorizado a datos de envíos | Las rutas, las direcciones de clientes y las liquidaciones son información comercial sensible | Autenticación JWT + RBAC en los tres roles |
| Robo de credenciales | Los conductores usan la app en celulares personales, en la calle | Contraseñas con Argon2; tokens guardados con `expo-secure-store`, nunca en almacenamiento plano |
| Escalada de privilegios entre roles | Un conductor que llegue a endpoints de admin podría reasignar o cancelar entregas | Verificación de rol en el servidor en cada endpoint protegido |
| Inyección mediante datos del usuario | Hay endpoints con búsqueda libre, direcciones y datos importados desde Excel | Consultas parametrizadas en todo el código; validación de esquemas en el borde de la API |
| Mal uso interno por usuarios legítimos | Un usuario autenticado puede reasignar, reprogramar o cancelar pedidos | Registro de auditoría de cada transición de estado |
| Abuso de claves de API | Las claves de Google Maps/Geocoding generan cobros | Claves restringidas por referente y por API, con topes de cuota |

### Control de acceso

- **Autenticación JWT** (`Authorization: Bearer`) con control de acceso por roles: `admin`, `almacen` y `conductor`.
- **Separación de funciones** aplicada en la lógica de dominio, no solo en la interfaz — la división avería/reanudación descrita arriba es el ejemplo más claro.
- **Mínimo privilegio:** los endpoints de cada rol exponen solo las operaciones que ese rol necesita.

### Criptografía

- **Contraseñas:** Argon2 — elegido frente a bcrypt por su resistencia en memoria al *cracking* acelerado por GPU.
- **En tránsito:** TLS terminado en el proxy inverso.
- **Token en el móvil:** `expo-secure-store` (Keychain / Keystore), no `AsyncStorage`.
- **Secretos:** inyectados por variables de entorno, nunca versionados. `.env` está en `.gitignore`.

### Registro de auditoría

Cada transición de estado de un pedido escribe un registro de auditoría con el actor, la acción, el objetivo y la fecha y hora. Así se puede reconstruir quién cambió qué y cuándo, y detectar patrones — como una sola cuenta que cancela un número inusual de entregas — que ninguna petición aislada revelaría.

### Gestión de vulnerabilidades

Las pruebas fueron **manuales** — sin escáneres automáticos. Revisé a mano endpoints, flujos de la aplicación y código contra el OWASP Top 10, clasifiqué lo que encontré, lo corregí y volví a probar para confirmar que la corrección se sostenía. Automatizar esto en el CI está en la hoja de ruta (ver Brechas conocidas).

**Hallazgo — posiciones de la flota en tiempo real expuestas en la landing pública**

| | |
| --- | --- |
| **Severidad** | Alta |
| **Categoría** | Control de acceso roto · Diseño inseguro (OWASP 1 y 6) |
| **Dónde** | Landing pública, sin autenticación |

La landing es la puerta de entrada a varios portales y mostraba un mapa en vivo de vehículos moviéndose por sus rutas. Estaba ahí para enganchar al visitante — el producto luciendo lo que hace — y funcionaba exactamente como se diseñó.

Ese era el problema. El mapa servía **posiciones reales de vehículos de reparto cargados a cualquier persona en internet**, sin iniciar sesión. Un flujo que se actualiza continuamente con dónde está la carga, mientras se mueve, es reconocimiento para un robo dirigido. No faltaba ninguna verificación de autorización en sentido técnico: la función estaba diseñada para ser pública, y el diseño en sí era la vulnerabilidad.

**Remediación:** el mapa público ahora usa **datos simulados**. Sigue mostrando lo que hace la plataforma, así que conserva su valor comercial, pero las posiciones reales de los vehículos solo se sirven dentro de los portales autenticados, a los roles que las operan.

**Verificado:** ✅ Probado de nuevo — el endpoint público ya no devuelve datos reales de la flota.

> Este hallazgo no salió de leer código ni de correr una herramienta. Salió de preguntarse a quién beneficia que estos datos sean visibles, y notar que la respuesta incluía a gente que el operador no querría mirando. Un escáner no puede marcar "esta función hace exactamente lo que se diseñó y ese es el problema".

### Cobertura del OWASP Top 10 (2025)

Probadas y atendidas **8 de 10** categorías:

| # | Categoría | Estado |
| --- | --- | --- |
| 1 | Control de acceso roto | ✅ Probado — el hallazgo de arriba entra aquí |
| 2 | Configuración de seguridad incorrecta | ✅ Probado |
| 3 | Fallas en la cadena de suministro de software | ❌ No cubierto — sin escaneo de dependencias |
| 4 | Fallas criptográficas | ✅ Probado — Argon2, TLS, almacenamiento seguro del token |
| 5 | Inyección | ✅ Probado — consultas parametrizadas, validación en el borde |
| 6 | Diseño inseguro | ✅ Probado — separación de funciones en el flujo de auxilio |
| 7 | Fallas de autenticación | ✅ Probado — vigencia del JWT, manejo de contraseñas |
| 8 | Fallas de integridad de software y datos | ❌ No cubierto |
| 9 | Fallas de registro y alertas | ✅ Probado — trazabilidad de auditoría en las transiciones de estado |
| 10 | Mal manejo de condiciones excepcionales | ✅ Probado — las respuestas de error no revelan detalles internos |

Las categorías 3 y 8 no están probadas. Ambas necesitan herramientas que aún no integro — escaneo de dependencias y de artefactos —, no un análisis que me haya saltado.

### Brechas conocidas

Dichas sin rodeos, porque un documento de seguridad que dice estar completo no es creíble:

- **Pruebas automatizadas mínimas.** Hay pruebas de humo con pytest (seguridad, enrutamiento, validaciones) y del portal, pero no cubren los flujos completos; el resto se verifica con build y typecheck (ver la sección 5.9). Es la brecha más grande.
- **Todas las pruebas de seguridad son manuales.** No se vuelven a correr en cada cambio, así que una regresión podría llegar a `main` sin que nadie lo note.
- **Sin escaneo de dependencias ni de artefactos**, por eso las categorías 3 y 8 de OWASP no están probadas.
- **Sin agregación centralizada de logs.** Los registros de auditoría viven en la base de datos; enviarlos a un SIEM haría que la detección de anomalías fuera continua y no manual.
- **Nada de esto está conectado al CI todavía.** GitHub Actions ya corre verificaciones de build y calidad; añadir escaneo de dependencias y SAST ahí es el siguiente paso obvio.
- **La autorización se aplica en cada handler.** Un middleware de políticas haría estructuralmente imposible olvidar una verificación en un endpoint nuevo.

---

## 4. Requisitos

| Para correr… | Necesitas |
| --- | --- |
| Backend + web (landing, portal y panel) | **Docker Desktop** (Compose v2). Python y Node corren dentro de los contenedores. |
| Base de datos | Incluida (contenedor `db`, PostgreSQL 15) **o** una propia, por ejemplo **Supabase**, vía `DATABASE_URL`. |
| App móvil (desarrollo) | **Node 18+** (el CI usa Node 22), la app **Expo Go** en el celular, y la PC y el celular en la **misma red WiFi**. |
| App móvil con mapa nativo y ubicación en 2.º plano | Un **dev build** de Expo (`eas build`) y una cuenta en expo.dev. |
| Google Maps / Geocoding (opcional) | Un proyecto de Google Cloud con facturación activa + claves de API restringidas. |
| Bandeja de correos (opcional) | Un buzón IMAP/SMTP (en Gmail, una *contraseña de aplicación*). |

---

## 5. Guía para correr todo

### 5.1 Resumen rápido

Si ya tienes Docker Desktop abierto:

```bash
git clone https://github.com/SebastianUC202120472/Geotrack.git
cd Geotrack
# 1. Crea el archivo .env en la raíz con la plantilla de la sección 5.2
# 2. Levanta la base de datos, el backend y la web:
docker compose up --build
```

La primera vez tarda unos minutos (compila las imágenes). Cuando termine:

| Qué | URL |
| --- | --- |
| Landing pública | http://localhost:8080 |
| Portal de clientes | http://localhost:8080/portal |
| Panel admin / almacén | http://localhost:8080/panel |
| API + Swagger | http://localhost:8000/docs |

Entra al panel con el `ADMIN_EMAIL` y `ADMIN_PASSWORD` de tu `.env`. Para la app del conductor, sigue la [sección 5.6](#56-app-móvil-del-conductor).

### 5.2 Crear el `.env`

El repositorio no trae un `.env` (está en `.gitignore` y nunca debe subirse). Crea un archivo llamado `.env` en la raíz con este contenido y cambia los valores marcados:

```dotenv
# --- Base de datos (Postgres local del docker compose) ---
POSTGRES_USER=sava_admin
POSTGRES_PASSWORD=sava_password123
POSTGRES_DB=siol_sava_db
# El host es "db" (el nombre del servicio en Compose), NO localhost.
DATABASE_URL=postgresql://sava_admin:sava_password123@db:5432/siol_sava_db

# --- Seguridad / JWT ---
SECRET_KEY=cambia-esto-por-una-clave-larga-y-aleatoria
ACCESS_TOKEN_EXPIRE_MINUTES=480
CORS_ORIGINS=*

# --- Admin inicial (se crea en el primer arranque si no existe) ---
ADMIN_EMAIL=admin@siol.com
ADMIN_PASSWORD=cambia-esta-clave

# --- Mapas y geocodificación (opcionales; vacías = OpenStreetMap / Nominatim, gratis) ---
VITE_GOOGLE_MAPS_KEY=
GOOGLE_GEOCODING_KEY=

# --- Correo (opcional; en false la Bandeja queda inactiva y todo lo demás funciona) ---
MAIL_ENABLED=false
MAIL_ADDRESS=
MAIL_PASSWORD=

# --- Portal: muestra el código OTP en pantalla cuando no hay correo (SOLO para demos) ---
PORTAL_OTP_DEMO=false
```

| Grupo | Variables | Notas |
| --- | --- | --- |
| **Base de datos** | `POSTGRES_*`, `DATABASE_URL` | Obligatorias. Ver la sección 5.3 para usar Supabase. |
| **Seguridad / JWT** | `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `CORS_ORIGINS` | Defínelas siempre: Compose las pasa tal cual y, por ejemplo, con `ACCESS_TOKEN_EXPIRE_MINUTES` vacía el backend no arranca. Genera la clave con `python -c "import secrets; print(secrets.token_hex(32))"`. |
| **Admin inicial** | `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Solo se usan para **crear** el admin si no existe; cambiarlas después no cambia la contraseña de un admin ya creado. |
| **Mapas del panel** | `VITE_GOOGLE_MAPS_KEY` | Vacía = OpenStreetMap. Con clave = Google Maps. Va dentro del build: tras cambiarla, reconstruye el frontend. |
| **Geocodificación** | `GOOGLE_GEOCODING_KEY` | Vacía = Nominatim/OSM (gratis, menos preciso). Con clave = Google. |
| **Correo** | `MAIL_ENABLED`, `MAIL_ADDRESS`, `MAIL_PASSWORD` y opcionales `IMAP_HOST`, `IMAP_PORT`, `SMTP_HOST`, `SMTP_PORT`, `MAIL_FOLDER`, `MAIL_FROM_NAME`, `MAIL_SIGNATURE` | Por defecto apunta a Gmail. Sin correo, el login de empresa del portal responde 503 (no puede enviar el OTP), salvo que actives `PORTAL_OTP_DEMO`. |
| **Demo del portal** | `PORTAL_OTP_DEMO` | En `true` y sin correo, el backend devuelve el OTP y el portal lo muestra. **Nunca en producción:** expone un factor de autenticación. |

> **Nunca subas `.env`.** Restringe tus claves de Google por referente y por API, y ponles tope de cuota: una clave facturable sin restringir en un repo público es la forma más rápida de perder una cuenta de Google Cloud.

### 5.3 Elegir la base de datos

- **Local (por defecto):** deja `DATABASE_URL` apuntando a `db`. El contenedor corre PostgreSQL 15 con un volumen persistente. Empieza vacía: solo con el admin inicial.
- **Remota (Supabase u otra):** reemplaza `DATABASE_URL` por la cadena de conexión de tu proveedor, por ejemplo:

  ```
  DATABASE_URL=postgresql://postgres.<ref>:<password>@aws-...pooler.supabase.com:5432/postgres?sslmode=require
  ```

  Codifica los caracteres especiales de la contraseña (`@` se escribe `%40`). El contenedor `db` sigue arrancando, pero queda sin uso.

El esquema se crea solo al arrancar (`create_all`) y se siembra el admin inicial. Las migraciones de Alembic están versionadas para entornos que ya se gestionan con Alembic.

> **Supabase en plan gratuito se pausa tras ~7 días sin uso.** Si el backend arranca y se cae con `ENOTFOUND` / `tenant/user ... not found`, no es un bug: reactiva el proyecto desde el dashboard de Supabase y reinicia el backend (`docker compose restart backend`).

### 5.4 Levantar backend + web

```bash
docker compose up --build        # en primer plano, con logs
docker compose up -d --build     # o en segundo plano
docker compose ps                # comprobar que db, backend y frontend están "running"
```

Con la base vacía, prepara lo mínimo desde el panel (http://localhost:8080/panel):

1. **Conductores** → crea al menos un conductor (su correo y contraseña son los que usará en la app).
2. **Flota** → registra un vehículo y asígnaselo al conductor. Sin vehículo no se le pueden asignar rutas.
3. **Usuarios** → opcional: crea cuentas con rol de almacén.

### 5.5 Datos de ejemplo (opcional)

Los scripts de `backend/scripts/` se corren **dentro del contenedor** del backend:

| Quiero… | Comando |
| --- | --- |
| Una solicitud de recojo en la Bandeja (Zara, 50 pedidos) para recorrer el flujo completo a mano | `docker compose exec backend python scripts/seed_solicitud_zara.py` |
| Llenar el portal de clientes (5 empresas, 250 pedidos del día con fotos de entrega) | `docker compose exec backend python scripts/seed_portal_demo.py` |
| Ver las credenciales y códigos de ejemplo que generó el script anterior | `docker compose exec backend cat scripts/salida/credenciales_portal_demo.md` |
| Regenerar esa hoja sin tocar la base (se pierde al reconstruir la imagen) | `docker compose exec backend python scripts/seed_portal_demo.py --solo-hoja` |

- `seed_solicitud_zara.py` **no borra nada**: solo deja el correo en la Bandeja; los pedidos los crea el admin al aceptar la solicitud.
- `seed_portal_demo.py` **vacía los datos operativos** (pedidos, rutas, historial…) y conserva usuarios, vehículos, parámetros y la Bandeja. Exige que existan, cada uno con su vehículo, los conductores `juan@prueba.com`, `rosa.medina@sava.pe`, `luis.chavez@sava.pe` y `marta.silva@sava.pe`. `juan@prueba.com` queda sin ruta a propósito, para poder demostrar un despacho en vivo.
- Para entrar como empresa al portal sin configurar correo, pon `PORTAL_OTP_DEMO=true` en `.env` y recrea el backend con `docker compose up -d backend`. Con el modo demostración activo, el propio portal muestra las credenciales y códigos de ejemplo.

### 5.6 App móvil del conductor

La app no se dockeriza: corre con Expo desde tu PC y se abre en el celular.

**1. Instalar dependencias**

```bash
cd mobile
npm install
```

**2. Crear `mobile/.env`** con la IP de tu PC en la red local (no `localhost`: para el celular, `localhost` es el propio celular):

```dotenv
EXPO_PUBLIC_API_URL=http://192.168.x.x:8000/api
# Vacía = mapa OpenStreetMap (funciona en Expo Go). Con clave = mapa nativo de Google (requiere dev build).
EXPO_PUBLIC_GOOGLE_MAPS_KEY=
```

Tu IP: en Windows, `ipconfig` (campo *Dirección IPv4*); en macOS, `ipconfig getifaddr en0`; en Linux, `hostname -I`. Si usas el **emulador de Android**, pon `http://10.0.2.2:8000/api` (así ve el emulador a tu PC).

**3a. Correr en Expo Go (lo más rápido)**

```bash
npx expo start --go -c
```

Escanea el QR con **Expo Go** (Android) o con la cámara (iOS), con el celular en la misma WiFi que la PC. El `--go` es necesario porque el proyecto incluye `expo-dev-client`: sin él, Expo espera un dev build instalado. `-c` limpia la caché (úsalo siempre después de instalar un módulo). En Expo Go funciona todo menos el mapa nativo de Google y la ubicación en segundo plano.

**3b. Dev build (mapa nativo de Google + ubicación en 2.º plano)**

```bash
npm install -g eas-cli
eas login
eas build --profile development --platform android   # genera un APK; instálalo en el celular
npx expo start --dev-client -c                        # y abre ese APK escaneando el QR
```

- EAS compila en la nube y **no ve `mobile/.env`** (está en `.gitignore`): define `EXPO_PUBLIC_GOOGLE_MAPS_KEY` en *Environment variables* de tu proyecto en expo.dev.
- El `projectId` de `app.config.js` (`extra.eas.projectId`) pertenece a la cuenta original; con otra cuenta de Expo, reemplázalo por el de tu proyecto.

**3c. APK autónomo (sin `expo start`)**

Para instalar la app y usarla sin la PC, el backend tiene que estar en una URL pública. Define `EXPO_PUBLIC_API_URL` con esa URL en el entorno *preview* de expo.dev y compila:

```bash
eas build --profile preview --platform android
```

Inicia sesión en la app con el conductor que creaste en el panel.

### 5.7 En la nube con GitHub Codespaces

El repositorio trae `.devcontainer/`, así que todo puede correr en un Codespace sin instalar nada:

1. En GitHub → *Settings → Secrets and variables → Codespaces*, crea un secreto **`DOTENV`** con el contenido completo de tu `.env`. Sin él, el Codespace usa valores por defecto y un Postgres local vacío.
2. Crea el Codespace. Al crearse genera `.env` y `mobile/.env` (apuntando a la URL pública del Codespace) e instala las dependencias del móvil; en cada arranque levanta backend + web con Docker.
3. En la pestaña **PORTS**, verifica que el puerto **8000** esté en visibilidad **Public** (clic derecho → *Port Visibility → Public*): si no, el celular no alcanza la API. La web está en el puerto **8080**.
4. Para la app móvil, usa el modo túnel (el Codespace no está en tu WiFi):

   ```bash
   cd mobile
   npx expo start --go --tunnel           # con Expo Go
   npx expo start --dev-client --tunnel   # con el dev build instalado
   ```

   Conéctate escaneando el QR: la pantalla *Searching for development servers* del dev build no encuentra un Codespace por sí sola.

### 5.8 Comandos habituales

| Quiero… | Comando |
| --- | --- |
| Levantar todo | `docker compose up --build` |
| Levantar en segundo plano | `docker compose up -d --build` |
| Reconstruir solo la web (cambios en `frontend/`) | `docker compose up -d --build --no-deps frontend` |
| Reconstruir solo el backend (cambios en `backend/`) | `docker compose up -d --build backend` |
| Aplicar cambios del `.env` | `docker compose up -d` (recrea los contenedores; `restart` no relee el `.env`) |
| Ver logs en vivo | `docker compose logs -f backend` |
| Entrar al contenedor del backend | `docker compose exec backend bash` |
| Parar todo | `docker compose down` |
| Parar y **borrar la base local** | `docker compose down -v` |
| Correr la app móvil | `cd mobile && npx expo start --go -c` |

La web es un build estático servido por Nginx y el código del backend se copia dentro de su imagen: en ambos casos, para ver un cambio hay que **reconstruir** la imagen correspondiente.

### 5.9 Verificación antes de dar algo por terminado

```bash
cd frontend && npm install && npm run build && npm run lint                            # Web
docker compose run --rm --no-deps backend python -c "import app.main"                  # Backend: la app importa
docker compose run --rm --no-deps backend sh -c "pip install -q pytest && pytest -q"   # Backend: pruebas
cd mobile && npx tsc --noEmit                                                          # Móvil: typecheck
```

GitHub Actions corre estas mismas verificaciones en cada push o PR a `develop` y `main`.

### 5.10 Problemas frecuentes

| Síntoma | Causa y solución |
| --- | --- |
| El backend se cae con `ENOTFOUND` / `tenant/user ... not found` | El proyecto de Supabase está pausado por inactividad. Reactívalo en su dashboard y corre `docker compose restart backend`. |
| No puedo entrar al panel | Usa el `ADMIN_EMAIL` / `ADMIN_PASSWORD` con los que se **creó** el admin; cambiarlos luego en `.env` no altera un admin existente. Revisa también `docker compose logs backend`. |
| Cambié algo en la web y no se ve | Reconstruye: `docker compose up -d --build --no-deps frontend`. |
| El celular no se conecta a la API | Misma WiFi que la PC, IP real en `EXPO_PUBLIC_API_URL` (no `localhost`) y el puerto 8000 permitido en el firewall de la PC. En Codespaces, el puerto 8000 en **Public**. |
| Expo dice *No development build … is installed* | Arranca con `npx expo start --go` para usar Expo Go, o instala el dev build (sección 5.6). |
| El mapa no carga en Expo Go | Deja `EXPO_PUBLIC_GOOGLE_MAPS_KEY` vacía: el mapa nativo de Google solo funciona en un dev build. El mapa de calles además necesita internet en el celular. |
| El login de empresa del portal responde 503 | No hay correo configurado para enviar el OTP. Activa el correo (`MAIL_*`) o, solo para demos, `PORTAL_OTP_DEMO=true`. |

---

## 6. Recorrido de punta a punta

1. **Solicitud.** Un cliente envía por correo un Excel con sus pedidos. Llega a la **Bandeja** del panel (o siémbrala con `seed_solicitud_zara.py`).
2. **Aceptar (admin).** El admin abre la conversación y la acepta → los pedidos se crean en `POR_RECOGER` y se geocodifican en segundo plano.
3. **Armar la ruta de recojo (almacén).** Las solicitudes se asignan a un conductor y un vehículo.
4. **Recoger (conductor).** El conductor abre la ruta de recojo, la optimiza desde su ubicación y registra la recepción con fotos → `RECOGIDO`.
5. **Ingreso manual (almacén).** El almacén revisa la galería de fotos, marca los faltantes (→ `OBSERVADO`) y confirma; el resto pasa a `LISTO_PARA_ENVIO`.
6. **Despachar (admin).** En **Agrupación por zonas**, el admin elige un distrito y crea una ruta de entrega → `ASIGNADO`.
7. **Entregar (conductor).** El conductor optimiza la ruta, navega parada por parada y marca `ENTREGADO` con prueba de entrega o `FALLIDO` con un motivo.
8. **Reportes y auxilio.** El admin resuelve los reportes y reprograma o cancela los fallidos. Ante una avería, el conductor la reporta (la ruta se pausa), el admin envía ayuda y el conductor reanuda.
9. **Cierre del día.** Cuando no quedan paradas pendientes, el conductor cierra la ruta.

A lo largo del flujo, el panel muestra un tablero de KPIs, el seguimiento de la flota en vivo, la trazabilidad de cada pedido y las liquidaciones por cliente.

> **Probar el lado del conductor sin la app:** el flujo del conductor también se puede recorrer con los endpoints `/api/conductor/*` (login → manifiesto → optimizar → marcar entregado/fallido → reportar → auxilio → reanudar). Todo se refleja en el panel. Ver Swagger en http://localhost:8000/docs.

---

## 7. Flujo de trabajo con Git

El repositorio sigue **Gitflow**: `main` (producción) ← `develop` (integración) ← ramas `feature/*`. Las features se integran a `develop` con `--no-ff` para conservar la topología de ramas; `develop` se promueve a `main` en cada versión. Más de 480 commits a la fecha, con verificaciones de build y calidad en GitHub Actions.

---

Hecho por **Sebastián Urteaga Castañeda** — [LinkedIn](https://www.linkedin.com/in/sebastian-urteaga/)
