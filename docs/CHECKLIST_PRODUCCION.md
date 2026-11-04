# Lista de verificación de producción — GeoTrack

Revisar antes de cada despliegue real (no en la demo). Al arrancar, el backend escribe en su
registro un aviso `PRODUCCIÓN: …` por cada punto que siga pendiente; con el registro limpio, la
configuración está lista.

```bash
docker compose logs backend | grep "PRODUCCIÓN"
```

## 1. Cuentas y claves

- [ ] **Clave del administrador.** La cuenta `admin@siol.com` nace con la clave de fábrica
      `admin123`, publicada en el repositorio. Entrar al panel → botón de perfil (arriba a la
      derecha) → **Cambiar contraseña**. Mientras siga la de fábrica, el panel muestra un aviso.
      Cambiar `ADMIN_PASSWORD` en `.env` **no** cambia la clave de un admin ya creado.
- [ ] **`SECRET_KEY`** larga y aleatoria (firma los tokens de sesión):
      `python -c "import secrets; print(secrets.token_hex(32))"`. Cambiarla cierra todas las sesiones.
- [ ] Cuentas de prueba (`@prueba.com`, `Clave12345!`) desactivadas o con clave nueva.

## 2. Red

- [ ] **`CORS_ORIGINS` vacío.** El panel, el portal y el landing llegan por Nginx (mismo origen) y
      la app móvil no usa CORS. Solo si otro dominio debe llamar a la API, listarlo:
      `CORS_ORIGINS=https://panel.sava.pe`. Nunca `*`.
- [ ] HTTPS delante de Nginx (lo da el proveedor de la nube o un proxy con certificado).

## 3. Modos de demostración apagados

| Variable | Producción | Qué hace encendida |
| --- | --- | --- |
| `PORTAL_OTP_DEMO` | `false` | El portal muestra en pantalla el código OTP y credenciales de ejemplo. |
| `ALMACEN_INGRESO_DIRECTO` | `false` | El almacén recibe la solicitud sin ruta de recojo ni fotos. |

## 4. Correo

- [ ] `MAIL_ENABLED=true` con `MAIL_ADDRESS` y `MAIL_PASSWORD` (contraseña de aplicación de
      Gmail, nunca la clave personal). Sin correo no salen los OTP del portal, las constancias del
      Libro de Reclamaciones ni las respuestas de la Bandeja.

## 5. Proceso del backend

- El contenedor arranca **sin `--reload`** (modo producción).
- `WEB_CONCURRENCY` fija cuántos procesos atiende uvicorn (por defecto 1). El arranque es seguro
  con varios (un candado en Postgres evita que dos procesos creen la misma tabla), pero el
  limitador de intentos de login vive en la memoria de cada proceso: con 2 procesos el tope real
  es el doble. Con el pooler de Supabase en **modo sesión** (puerto 5432, tope de 15 clientes)
  dejarlo en 1; con el **modo transacción** (puerto 6543) se puede subir.

## 6. Registro de errores

- Los errores no controlados quedan en `logs/geotrack.log` (volumen `backend_logs`, rota a los
  5 MB, guarda 5 archivos) con fecha, ruta y traza. El usuario ve un **código de referencia**;
  para encontrarlo: `docker compose exec backend grep <código> logs/geotrack.log`.

## 7. Claves de Google

- [ ] La clave del mapa (`VITE_GOOGLE_MAPS_KEY`) viaja al navegador: restringirla por dominio.
- [ ] La de geocodificación (`GOOGLE_GEOCODING_KEY`) solo en el servidor, restringida a la
      Geocoding API, y con tope de cuota en Google Cloud.
