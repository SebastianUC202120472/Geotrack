# 🧪 Guía de Pruebas — SIOL-SAVA Backend (sin frontend)

Tu "frontend" para probar es **Swagger UI**: `http://localhost:8000/docs`.
Desde ahí puedes ejecutar cada endpoint con el botón **"Try it out"**.

> ⚠️ **Importante (orden):** los endpoints dependen unos de otros. Hay que
> seguir el flujo: **Admin** carga y arma rutas → **Conductor** las ejecuta.

---

## ✅ 0. Requisitos previos (checklist)

- [ ] **Docker Desktop** abierto y corriendo.
- [ ] Levantar el entorno **con volumen fresco** (porque la Fase 3 añadió columnas):
  ```bash
  docker compose down -v
  docker compose up --build
  ```
- [ ] Abrir `http://localhost:8000/` → debe responder `{"status":"online", ...}`.
- [ ] Abrir `http://localhost:8000/docs` → ves todos los endpoints.
- [ ] Tener a mano el archivo **`datos_prueba/pedidos_demo.xlsx`** (ya creado).
- [ ] Tener una **foto cualquiera** (`.jpg` o `.png`) en tu PC para la evidencia POD.

---

## 🔑 Cómo funciona la autenticación en Swagger

Casi todos los endpoints tienen un **candado 🔒**: necesitan un token JWT.

1. Pulsa el botón verde **"Authorize"** (arriba a la derecha).
2. En el formulario escribe el **correo** (campo `username`) y la **contraseña**.
   (los campos `client_id`/`client_secret` se dejan vacíos).
3. Pulsa **Authorize** → Swagger guarda el token y lo manda solo en cada llamada.

> 🔁 **Swagger solo guarda UN token a la vez.** Para cambiar de Admin a
> Conductor: pulsa **Authorize → Logout** y vuelve a entrar con el otro usuario.

---

## 👥 1. Crear los usuarios (Fase 1 — CUS-01)

Endpoint: `POST /api/auth/registro` (está **abierto**, no necesita token).

**Crea un ADMIN** — pulsa "Try it out" y envía este body:
```json
{ "correo": "admin@siol.com", "contrasena": "admin123", "rol": "admin" }
```
**Crea un CONDUCTOR**:
```json
{ "correo": "conductor@siol.com", "contrasena": "conductor123", "rol": "conductor" }
```

✅ **Qué verificar:** la respuesta (200) devuelve `id`, `correo`, `rol`, `estado:true`
y **NO** muestra la contraseña.
📝 **Anota el `id` del conductor** (ej. `2`): lo necesitarás como `conductor_id`.

---

## 🧑‍💼 2. FLUJO ADMIN (Fase 2 — panel web)

> Primero **Authorize** como `admin@siol.com` / `admin123`.

### 2.1 Cargar pedidos desde Excel — `POST /api/pedidos/upload` (CUS-13)
- "Try it out" → en `file` selecciona **`datos_prueba/pedidos_demo.xlsx`** → Execute.
- ✅ Esperado: `{ "mensaje": "Carga masiva exitosa", "pedidos_nuevos": 5, "total_filas_leidas": 5 }`.
- 💡 Si lo subes 2 veces, `pedidos_nuevos` será 0 (no duplica por `numero_tracking`).
- 📋 El Excel ahora trae: `numero_tracking`, `razon_social_cliente`, `ruc_cliente`,
  `direccion_destino`, `nombre_destinatario`, `telefono_destinatario`, `dni_destinatario`,
  `peso_kg`, `volumen_m3`. Al cargar, **los clientes se crean solos** y se enlazan al pedido.

### 2.1b Ver clientes — `GET /api/clientes/` (Fase 4)
- ✅ Esperado: las empresas cliente creadas desde el Excel (con su RUC).
- 💡 También puedes registrar un cliente a mano con `POST /api/clientes/`.

### 2.2 Ver los pedidos — `GET /api/pedidos/`
- ✅ Esperado: lista con 5 pedidos en estado `PENDIENTE`, sin coordenadas todavía.

### 2.3 Geocodificar — `POST /api/pedidos/geocodificar` (CUS-15)
- ⏳ Tarda ~1 segundo por pedido (límite de Nominatim). Paciencia.
- ✅ Esperado: `{ "mensaje": "...finalizado", "pedidos_exitosos": 5, "pedidos_fallidos": 0 }`.
- 💡 Si alguno falla (`pedidos_fallidos > 0`), Nominatim no encontró esa dirección;
  no rompe nada, ese pedido queda como `GEOCODIFICACION_FALLIDA`.

### 2.4 Ver zonas — `GET /api/pedidos/zonas` (CUS-16)
- ✅ Esperado: `San Miguel` con 3 pedidos y `Miraflores` con 2.

### 2.5 Armar la ruta — `POST /api/rutas/asignar-bloque` (CUS-18)
Body (usa el `conductor_id` que anotaste, ej. `2`):
```json
{ "nombre_ruta": "Ruta San Miguel - Mañana", "distrito": "San Miguel", "conductor_id": 2 }
```
- ✅ Esperado: `{ "mensaje": "3 pedidos asignados...", "ruta_id": 1 }`.
- 📝 **Anota el `ruta_id`** (ej. `1`).
- 💡 Los 3 pedidos de San Miguel pasan a estado `ASIGNADO`.

---

## 🚚 3. FLUJO CONDUCTOR (Fase 3 — App Móvil)

> Cambia de usuario: **Authorize → Logout** y entra como
> `conductor@siol.com` / `conductor123`.

### 3.1 Optimizar la secuencia — `POST /api/rutas/conductor/optimizar` (CUS-19)
Body (el `ruta_id` que anotaste + tu posición actual de ejemplo):
```json
{ "ruta_id": 1, "latitud_actual_conductor": -12.077, "longitud_actual_conductor": -77.083 }
```
- ✅ Esperado: `{ "mensaje": "Ruta optimizada matemáticamente", "total_paradas": 3 }`.
- 💡 Verás `403` si intentas optimizar una ruta que **no es tuya** (seguridad OK).

### 3.2 Consultar ruta activa — `GET /api/conductor/ruta-activa` (CUS-21)
- ✅ Esperado: resumen con `total_paradas: 3`, `pendientes: 3`, `entregadas: 0`, `fallidas: 0`.

### 3.3 Manifiesto — `GET /api/conductor/ruta-activa/manifiesto` (CUS-24)
- ✅ Esperado: lista de 3 paradas **ordenadas por `secuencia` (1, 2, 3)** con tracking,
  cliente, dirección y coordenadas.
- 📝 **Anota un `pedido_id`** y un `numero_tracking` de la lista.

### 3.4 Navegación — `GET /api/conductor/ruta-activa/navegacion` (CUS-25)
- ✅ Esperado: los waypoints (solo `secuencia` + `lat/lng`) para el mapa.

### 3.5 Validar QR en almacén — `POST /api/conductor/almacen/validar-qr` (CUS-22)
Body (con el **código PD-001** de TU ruta — lo ves en el manifiesto):
```json
{ "codigo": "PD-001" }
```
- ✅ Esperado: `{ "pertenece": true, "mensaje": "Paquete validado...", "parada": {...} }`.
- 🧪 Prueba el caso negativo con un `codigo` de Miraflores (otra ruta):
  → `{ "pertenece": false, "mensaje": "Este paquete NO pertenece a tu ruta de hoy" }`.

### 3.6 Marcar ENTREGADO — `PATCH /api/conductor/paradas/{pedido_id}/estado` (CUS-26)
- En `pedido_id` pon el id que anotaste. Body:
```json
{ "estado": "ENTREGADO" }
```
- ✅ Esperado: `estado_entrega: "ENTREGADO"` y `fecha_gestion` con la hora.
- 🧪 Prueba un FALLIDO (exige motivo) en otro pedido:
```json
{ "estado": "FALLIDO", "motivo_fallo": "Cliente ausente" }
```
- 💡 Si mandas `FALLIDO` **sin** `motivo_fallo` → `400` (validación OK).
- 💡 Tras la primera gestión, la ruta pasa de `CREADA` a `EN_PROGRESO`.

### 3.7 Subir foto POD — `POST /api/conductor/paradas/{pedido_id}/evidencia` (CUS-29)
- En `file` selecciona una foto `.jpg`/`.png` → Execute.
- ✅ Esperado: `url_evidencia: "/media/evidencias/pod_1_<pedido>.jpg"`.
- 👀 **Para ver la foto:** abre en el navegador `http://localhost:8000` + esa URL.
- 💡 Si subes un `.pdf`/`.txt` → `400` (solo imágenes).

### 3.8 Cerrar la ruta — `POST /api/conductor/ruta-activa/finalizar` (CUS-28)
- ✅ Esperado: `estado: "FINALIZADA"`, `fecha_fin` con la hora y el resumen
  (entregadas / fallidas / pendientes).
- 💡 Tras cerrar, `GET /ruta-activa` devolverá `404` (ya no hay ruta activa). ✔️ correcto.

---

## ❗ Errores comunes y cómo resolverlos

| Código | Qué significa | Solución |
|---|---|---|
| **401** Unauthorized | No mandaste token o expiró (dura 30 min) | Pulsa **Authorize** y vuelve a iniciar sesión |
| **403** Forbidden | Tu rol no puede usar ese endpoint | Admin para `/pedidos` y `/asignar-bloque`; conductor para `/conductor/*` |
| **422** Unprocessable | El body JSON está mal escrito o falta un campo | Revisa nombres y tipos del ejemplo |
| **404** Not Found | No hay ruta activa / id inexistente | Verifica que hiciste `asignar-bloque` y que el id es correcto |
| **400** Bad Request | Excel sin columnas, FALLIDO sin motivo, archivo no-imagen | Lee el `detail` del error, te dice qué falta |

---

## 🗺️ Resumen del orden correcto (mapa mental)

```
[ADMIN]                                   [CONDUCTOR]
registro(admin) ─┐
registro(conductor) ─→ anota conductor_id
Authorize(admin)
  upload(excel) ──→ geocodificar ──→ zonas
  asignar-bloque ──→ anota ruta_id
                                          Authorize(conductor)
                                            optimizar(ruta_id)
                                            ruta-activa
                                            manifiesto ──→ anota pedido_id
                                            navegacion
                                            validar-qr(tracking)
                                            estado(pedido_id)  [ENTREGADO/FALLIDO]
                                            evidencia(pedido_id, foto)
                                            finalizar
```

✔️ Si completas este recorrido sin errores rojos, **las 4 fases del backend
funcionan de punta a punta.**

---

## 📊 4. FLUJO ADMIN — Trazabilidad (Fase 4)

> Vuelve a **Authorize** como `admin@siol.com`. Estos endpoints son del panel web.

### 4.1 KPIs globales — `GET /api/dashboard/resumen` (CUS-33)
- ✅ Esperado: `total_pedidos`, `pedidos_por_estado` (ej. `{"ENTREGADO":1,"FALLIDO":1,...}`),
  `rutas_activas`, `rutas_finalizadas`.

### 4.2 Estado de la flota — `GET /api/dashboard/flota` (CUS-33)
- ✅ Esperado: lista de rutas con su `avance_porcentaje`, conteo de
  entregadas/fallidas/pendientes y el correo del conductor.
- 💡 Si cerraste la ruta antes, la verás como `FINALIZADA` con su `fecha_fin`.

### 4.3 Historial de un paquete — `GET /api/dashboard/pedidos/{codigo}/historial` (CUS-35)
- Pon el **código** de un paquete que ya gestionaste (ej. `PD-001`).
- ✅ Esperado: la línea de tiempo **real** (`eventos`, leída de `historial_pedidos`):
  `PENDIENTE → ASIGNADO → EN_RUTA → ENTREGADO/FALLIDO`, cada evento con su
  **fecha** y el **`realizado_por`** (correo de quién lo hizo: admin o conductor),
  más la ruta, secuencia y la `url_evidencia` si subiste foto.
- 💡 Esto es trazabilidad real: si un pedido pasa por varios estados, verás
  **todos** los pasos, no solo el último.

---

## ⚙️ 5. CI/CD (Fase 4.3) — GitHub Actions

No se prueba en Swagger; se prueba **subiendo código a GitHub**:
1. Haz `git push` a la rama `develop` (o abre un Pull Request).
2. Entra a tu repo en GitHub → pestaña **"Actions"**.
3. Verás el flujo **"CI - SIOL-SAVA Backend"** corriendo: instala dependencias,
   importa la app y ejecuta `pytest`.
4. ✅ Check verde = el código corre correctamente. ❌ X roja = algo se rompió
   (haz clic para ver el log).

> 💡 Para correr las mismas pruebas en tu PC: `pytest -q` (necesitas `pip install pytest`).
