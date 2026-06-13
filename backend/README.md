# 🚚 SIOL-SAVA Backend (MVP Logístico)

Backend del Sistema Integrado de Operaciones Logísticas (SIOL-SAVA), para la gestión y
**trazabilidad** de entregas de última milla. Construido con **arquitectura limpia** y
totalmente **contenedorizado** (no necesitas instalar Python ni PostgreSQL en tu PC).

---

## 🛠️ Stack Tecnológico
- **Framework:** FastAPI (Python 3.11)
- **Base de Datos:** PostgreSQL 15
- **ORM / Migraciones:** SQLAlchemy + Alembic
- **Infraestructura:** Docker & Docker Compose
- **Datos:** Pandas (Excel), Geopy (geocodificación)
- **Seguridad:** JWT + Argon2

---

## 📋 Requisitos previos
Solo necesitas **2 cosas** instaladas (NO hace falta Python ni PostgreSQL):
1. [Git](https://git-scm.com/)
2. [Docker Desktop](https://www.docker.com/products/docker-desktop) — **debe estar abierto/ejecutándose**.

---

## 🚀 Cómo levantar el backend (4 pasos)

### Paso 1 — Clonar el repositorio
```bash
git clone https://github.com/SebastianUC202120472/Backend-Geotrack
cd Backend-Geotrack
```

### Paso 2 — Crear el archivo `.env`  ⚠️ (¡el más importante!)
El proyecto necesita un archivo `.env` con la configuración. Ya hay una **plantilla lista**
llamada `.env.example`; solo cópiala con el nombre `.env`:

```bash
# Windows (PowerShell o CMD)
copy .env.example .env

# Linux / Mac
cp .env.example .env
```

> 💡 No tienes que editar nada: los valores por defecto ya funcionan para desarrollo.
> (Más abajo se explica qué es el `.env` y cada variable.)

### Paso 3 — Levantar todo (API + base de datos)
```bash
docker compose up --build
```
Esto descarga todo, crea las tablas y un **usuario administrador inicial** automáticamente.
La primera vez tarda unos minutos. Cuando veas en la consola algo como
`Application startup complete`, ya está listo. **Deja esa ventana abierta.**

### Paso 4 — Abrir la documentación interactiva (Swagger)
En el navegador:
```
http://localhost:8000/docs
```
Desde ahí puedes probar todos los endpoints. Para confirmar que vive: `http://localhost:8000/`
debe responder `{"status":"online"}`.

---

## 🔑 Primer ingreso (login)
Al arrancar se crea solo un administrador con estas credenciales (definidas en el `.env`):
- **Correo:** `admin@siol.com`
- **Contraseña:** `admin123`

En Swagger pulsa **«Authorize»**, escribe el correo en `username` y la contraseña, y listo.
Con ese admin puedes crear más usuarios (conductores) desde `POST /api/auth/registro`.

---

## 📦 ¿Qué es el archivo `.env` y las variables de entorno?
Las **variables de entorno** son ajustes que viven **fuera del código**, en el archivo
`.env`. Ese archivo se queda **solo en tu PC** (está en `.gitignore`, **nunca se sube a GitHub**).
Sirve para dos cosas:
1. **Seguridad:** las contraseñas y claves secretas no quedan escritas en el código público.
2. **Flexibilidad:** el mismo código funciona en cualquier máquina cambiando solo estos valores.

Lo leen **Docker Compose** (para crear la base de datos) y **la app** (para la clave del JWT,
la conexión, etc.). Por eso el Paso 2 es obligatorio.

| Variable | Qué es | Para qué sirve |
|---|---|---|
| `SECRET_KEY` | Clave secreta larga | Firma los tokens JWT para que no se falsifiquen |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Número de minutos | Duración de la sesión (token) antes de re-loguear |
| `POSTGRES_USER` | Usuario de la BD | Docker crea PostgreSQL con este usuario |
| `POSTGRES_PASSWORD` | Contraseña de la BD | Contraseña de ese usuario |
| `POSTGRES_DB` | Nombre de la BD | Nombre de la base de datos a crear |
| `DATABASE_URL` | Cadena de conexión | Cómo se conecta la app a PostgreSQL |
| `CORS_ORIGINS` | Orígenes permitidos | Qué frontends pueden llamar a la API (`*` = todos, en dev) |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Credenciales | El admin que se crea solo al arrancar |

> 🔒 En **producción** estos valores se cambian por otros seguros (clave aleatoria, contraseñas
> fuertes, CORS solo con tu dominio). Ver `SEGURIDAD.md`.

---

## 🔁 Comandos del día a día

| Acción | Comando |
|---|---|
| Levantar el backend | `docker compose up --build` |
| Detenerlo (Ctrl+C y luego) | `docker compose down` |
| **Reiniciar la BD desde cero** (borra los datos) | `docker compose down -v && docker compose up --build` |

> ⚠️ **Importante:** si actualizas el código y se **cambió la estructura de la base de datos**
> (nuevas tablas o columnas), usa la opción con **`-v`** para recrear la base de datos. Si no,
> los datos nuevos no aparecerán. (Para uso normal, basta `docker compose up --build`.)

---

## 🧪 Probar la API
Hay una guía paso a paso con datos de ejemplo en **`GUIA_PRUEBAS.md`** (incluye un Excel de
prueba en `datos_prueba/pedidos_demo.xlsx` y el flujo completo admin → conductor).

---

## ❓ Problemas comunes

| Síntoma | Causa / Solución |
|---|---|
| `docker: command not found` o no levanta | Docker Desktop no está instalado o no está abierto. Ábrelo y reintenta. |
| Error de conexión a la base de datos | Falta el archivo `.env` (Paso 2) o el puerto 5432 está ocupado. |
| El puerto 8000 está en uso | Cierra lo que use ese puerto, o cambia `8000:8000` en `docker-compose.yml`. |
| `401 Unauthorized` en Swagger | No iniciaste sesión o el token expiró. Pulsa «Authorize» de nuevo. |
| Cambié los modelos y no veo las columnas nuevas | Recrea la BD: `docker compose down -v && docker compose up --build`. |

---

## 📚 Documentación adicional
- **`GUIA_PRUEBAS.md`** — cómo probar cada endpoint paso a paso.
- **`SEGURIDAD.md`** — medidas de seguridad (OWASP, secretos, CI/CD).
- **`MANUAL_SIOL_SAVA.pdf`** — manual técnico completo (arquitectura + catálogo de las APIs).

---

## 🧱 Arquitectura (resumen)
Cada petición fluye por capas, de arriba hacia abajo:
```
api/ (router, valida rol)  →  services/ (lógica)  →  repositories/ (BD)  →  models/ (tablas)
                         schemas/ (validación)        core/ (seguridad, config)
```
