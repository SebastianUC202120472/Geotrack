# 🔐 Seguridad del Backend — SIOL-SAVA

Documento de las medidas de seguridad implementadas y cómo operarlas. Sirve como
evidencia para la tesis (OWASP Top 10, gestión de vulnerabilidades, criptografía,
mínimo privilegio).

---

## 1. Gestión de secretos (OWASP A02 / A05)

Los secretos **ya no están en el código**. Se leen de variables de entorno a
través de `app/core/config.py` (módulo central con `pydantic-settings`).

- **Configurar:** copia `.env.example` a `.env` y rellena los valores. El `.env`
  está en `.gitignore` (nunca se sube).
- **Generar una clave fuerte:**
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
  Pégala en `SECRET_KEY` del `.env`.
- Variables clave: `SECRET_KEY`, `DATABASE_URL`, `CORS_ORIGINS`,
  `ACCESS_TOKEN_EXPIRE_MINUTES`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`.

> Los valores por defecto en el código son **solo para desarrollo**. En
> producción se DEBEN sobreescribir por entorno.

## 2. Autenticación y mínimo privilegio (OWASP A01 / A07)

- **Contraseñas:** hash con **Argon2** (estándar moderno). Nunca se guardan en texto.
- **JWT** firmado (HS256) con expiración configurable.
- **Roles** (`admin` / `conductor`) validados con un `Enum`: un rol inventado se
  rechaza con error 422.
- **Control de acceso por rol** en cada endpoint (`get_current_admin` /
  `get_current_conductor`) y verificación de **propiedad** (un conductor solo
  accede a SU ruta).
- **Registro cerrado:** `POST /api/auth/registro` ahora exige rol `admin`. Antes
  estaba abierto y aceptaba el `rol` del cliente → cualquiera podía crearse admin
  (escalada de privilegios). **Corregido.**
- **Admin inicial:** se crea solo al arrancar (de `ADMIN_EMAIL`/`ADMIN_PASSWORD`),
  para poder entrar y dar de alta al resto desde el panel.

## 3. CORS (OWASP A05)

Configurable por entorno (`CORS_ORIGINS`). Se usa `allow_credentials=False`
porque la autenticación va por el header `Authorization: Bearer` (no cookies);
así el frontend funciona sin fricción. **En producción**, en vez de `*`, pon los
orígenes reales:
```
CORS_ORIGINS=https://mi-frontend.com,https://admin.mi-frontend.com
```

## 4. Inyección y subida de archivos (OWASP A03)

- Todo el acceso a datos usa el **ORM de SQLAlchemy** (consultas parametrizadas):
  no hay SQL armado con strings → sin inyección SQL.
- La carga de Excel valida extensión `.xlsx`; la evidencia POD valida que sea imagen.

## 5. Gestión de vulnerabilidades (OWASP A06)

- **Dependencias pineadas** en `requirements.txt` (versión fija) → rastreables.
- **CI de seguridad** (`.github/workflows/ci.yml`, job `seguridad`):
  - **bandit**: análisis estático de seguridad de nuestro código.
  - **pip-audit**: busca CVEs conocidos en las dependencias (informativo).
- **Dependabot** (`.github/dependabot.yml`): abre PRs semanales con actualizaciones.

## 6. Trazabilidad / auditoría (OWASP A09)

La tabla `historial_pedidos` registra cada cambio de estado con **fecha y
usuario** que lo hizo → rastro de auditoría de las operaciones.

---

## ✅ Activar en GitHub (se hace en la web, una sola vez)

1. **Secret Scanning + Push Protection** (avisa/bloquea si subes un secreto):
   Repo → **Settings** → **Code security and analysis** → activar
   *Secret scanning* y *Push protection*.
2. **Dependabot alerts**: misma pantalla → activar *Dependabot alerts* y
   *Dependabot security updates*.
3. **Actions**: el job `seguridad` corre solo en cada push (pestaña *Actions*).

---

## 🔭 Pendiente (mejoras de producción, fuera del MVP)

| Tema | Mejora |
|---|---|
| A01 | Servir las evidencias `/media` por un endpoint autenticado (hoy son públicas para no complicar el frontend) |
| A04/A07 | Rate-limiting en login (anti fuerza bruta) y límite de tamaño en subida de fotos |
| A05 | Cabeceras de seguridad (HSTS, X-Content-Type-Options...) y **HTTPS/TLS** en el despliegue |
| A07 | Política de contraseñas, bloqueo de cuenta y refresh tokens |
| A05 | Usar servidor de producción (sin `--reload`) y un usuario de BD con permisos mínimos |
