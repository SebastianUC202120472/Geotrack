# Módulo de catálogo de vehículos y capacidad (Idea 3)

Este documento explica el módulo de las semanas 9, 10 y 11: qué hace, cómo se
prueba, cómo se apaga y qué límites tiene. El módulo vive en su propia carpeta
del backend y en su propia carpeta del frontend; solo **lee** pedidos y flota del
núcleo y guarda sus cambios en tablas propias.

## 1. Alcance por semana

| Semana | Entregable | Dónde verlo |
| --- | --- | --- |
| 9 | Catálogo de vehículos con fichas técnicas, filtros, alta/edición y vinculación de placas | Pestañas **Catálogo** y **Flota y vinculaciones** |
| 10 | Calculadora de capacidad por cajas S/M/L, por pedidos reales o por escenario demo | Pestaña **Calculadora** |
| 11 | Planificación diaria, topes de paradas/viajes, alertas y caso de 700 pedidos | Pestaña **Planificación** y endpoint `/planificacion` |

## 2. Arquitectura

```
backend/app/
  api/modulo_capacidad/
    __init__.py
    router.py                 # endpoints + bandera MODULO_CAPACIDAD_ENABLED
    catalogo_vehiculos.json   # catálogo base versionado (79 modelos)
  models/capacidad.py         # 4 tablas propias del módulo
  schemas/capacidad.py        # contratos Pydantic de entrada/salida
  repositories/capacidad_repository.py
  services/capacidad_service.py

backend/tests/
  test_modulo_capacidad.py

frontend/src/
  pages/ModuloCapacidadPage.jsx
  components/capacidad/
    FormularioModelo.jsx
    VisorCarga3D.jsx          # Three.js bajo demanda + respaldo SVG
    constantes.js
```

Capas:

- **Router**: autenticación, permisos y códigos HTTP. No contiene reglas de negocio.
- **Service**: catálogo, vinculaciones, cálculo y planificación.
- **Repository**: consultas a pedidos/flota del núcleo y a las tablas del módulo.
- **Modelos**: solo tablas del módulo; no se modifican tablas del núcleo.

### Tablas propias

| Tabla | Para qué sirve |
| --- | --- |
| `vinculaciones_placa` | Relación placa → modelo, con usuario y fecha. Una placa activa por vez. |
| `modelos_personalizados` | Copias editadas de modelos base y modelos creados desde el panel. |
| `configuracion_capacidad` | Fila única con factor de aprovechamiento y topes. |
| `auditoria_capacidad` | Registro de altas, ediciones, vinculaciones y cambios de configuración. |

Las tablas se crean con el `create_all` que el backend ya ejecuta al arrancar
(`preparar_esquema`). No se agregó una revisión de Alembic porque el proyecto no
usa migraciones versionadas para el resto del esquema.

## 3. Catálogo base

- Archivo: `backend/app/api/modulo_capacidad/catalogo_vehiculos.json` (versión 1.2.0).
- 79 modelos de 29 marcas: pick-up, furgoneta, van/combi, SUV, sedán, hatchback,
  camión ligero, camión mediano y camión pesado.
- Incluye Jetour, DFSK y Changan, pedidos en la revisión.
- Cada ficha tiene `fuente`, `fuente_url`, dimensiones, volumen útil, carga útil y
  bandera `verificado`.
- Los 60 modelos originales quedan como `verificado: true`; los 19 agregados para
  completar marcas/tipos quedan como referencia (`verificado: false`) y se pueden
  validar desde el panel.
- Reglas de validación: el volumen útil debe estar entre el 80% y el 120% del
  producto largo × ancho × alto.

Editar un modelo base **no** modifica el JSON: el backend guarda una copia en
`modelos_personalizados`. Los modelos base no se pueden borrar, solo editar.

## 4. API

Todas las rutas cuelgan de `/api/modulo-capacidad`. Lectura: admin y almacén.
Escritura: solo admin.

| Método | Ruta | Rol | Descripción |
| --- | --- | --- | --- |
| GET | `/salud` | público | Estado del módulo (`habilitado`) |
| GET | `/catalogo` | admin/almacén | Lista con filtros `busqueda`, `marca`, `tipo`, `solo_verificados` |
| GET | `/catalogo/{id}` | admin/almacén | Ficha de un modelo |
| POST | `/catalogo` | admin | Crea un modelo propio |
| PATCH | `/catalogo/{id}` | admin | Edita (copia si es base) |
| DELETE | `/catalogo/{id}` | admin | Borra solo modelos propios |
| GET | `/flota` | admin/almacén | Flota con su modelo vinculado |
| GET | `/vinculaciones` | admin/almacén | Historial de placas vinculadas |
| POST | `/vinculaciones` | admin | Vincula placa y modelo (201/404/409/422) |
| DELETE | `/vinculaciones/{id}` | admin | Desvincula |
| GET | `/configuracion` | admin/almacén | Factor y topes |
| PUT | `/configuracion` | admin | Actualiza factor y topes (auditado) |
| POST | `/calcular` | admin/almacén | Capacidad para un modelo o placa |
| GET | `/planificacion` | admin/almacén | Plan diario real o demo |
| GET | `/auditoria` | admin | Últimos cambios (máx. 500) |

### Cuerpo de `/calcular`

```json
{
  "modelo_id": "toyota-hilux-2024",
  "cantidades": { "S": 40, "M": 20, "L": 10 },
  "factor_aprovechamiento": 0.85,
  "max_paradas_por_viaje": 25,
  "max_viajes_por_dia": 3
}
```

Alternativas a `cantidades`:

- `"pedido_ids": [1, 2, 3]` para pedidos concretos.
- `"filtros": { "estado": "LISTO_PARA_ENVIO", "distrito": "Lima", "limite": 200 }`.
- `"demo_pedidos": 700` para el escenario sintético.
- `"placa": "ABC-123"` en lugar de `modelo_id` (la placa debe estar vinculada).

### Parámetros de `/planificacion`

`estado`, `distrito`, `fecha`, `limite`, `demo_pedidos`, `demo_vehiculos`,
`factor_aprovechamiento`, `max_paradas_por_viaje`, `max_viajes_por_dia`.

## 5. Cómo calcula

1. Cada pedido aporta peso (`pedidos.peso_kg`) y volumen (`pedidos.volumen_m3`).
2. Si un pedido no tiene esos datos, se usa una talla estándar S/M/L y el plan
   responde con `pedidos_estimados > 0` y la alerta `datos_estimados`.
3. La capacidad efectiva de un vehículo es:
   `volumen_util_m3 × factor_aprovechamiento` y
   `carga_util_kg × factor_aprovechamiento`.
4. Se llenan viajes por volumen y peso. El máximo de viajes por día es un
   **límite duro**; si no alcanza, aparece `capacidad_insuficiente` y
   `pedidos_sin_asignar`.
5. El tope de paradas por viaje es una **alerta** (`tope_paradas_viaje`), no un
   límite que descarte carga. Así se puede representar el caso de 700 pedidos y
   avisar que conviene dividir el viaje o sumar un vehículo.
6. La jornada acumulada por vehículo también alerta (`jornada_excedida`).

### Caso de la semana 11: 700 pedidos

- Demo desde la interfaz: pestaña **Planificación** → **Probar demo 700 pedidos**
  (6 vehículos por defecto).
- API: `GET /api/modulo-capacidad/planificacion?demo_pedidos=700&demo_vehiculos=6`.
- Resultado esperado: 700 pedidos asignados (0 sin asignar), 5-6 vehículos
  usados, alertas `tope_paradas_viaje` y `jornada_excedida` porque el volumen
  obliga a viajes con muchas paradas.
- En la calculadora, con **un solo vehículo**, el mismo caso muestra
  `capacidad_insuficiente`: es correcto, un vehículo no puede con 700 pedidos en
  un día.

## 6. Interfaz

Ruta: `/panel/capacidad`. Pestañas:

1. **Catálogo**: KPIs, búsqueda, filtros por tipo/marca/verificado, tabla con
   fuente enlazada y estado. Admin puede agregar, editar y borrar modelos propios.
2. **Flota y vinculaciones**: formulario placa → modelo, tabla de flota con su
   modelo y capacidad, historial de vinculaciones.
3. **Calculadora**: elige modelo o placa; carga cajas S/M/L, pedidos reales o
   demo; ajusta factor y topes; muestra viajes, uso, alertas y visor 3D.
4. **Planificación**: pedidos reales o demo de 700; resumen por vehículo, detalle
   de viajes y alertas.
5. **Configuración**: factor y topes (solo admin) y auditoría (solo admin).

El visor 3D usa Three.js cargado bajo demanda (`import("three")`), dibuja solo
cuando se interactúa y cae a una vista SVG si WebGL no está disponible. Three.js
queda en un chunk aparte, no en el bundle principal.

### Roles

- **Admin**: lectura y escritura.
- **Almacén**: lectura del módulo desde `/panel/capacidad` (se agregó la ruta a
  `ProtectedRoute` y un acceso en el menú de Almacén). No ve botones de alta,
  edición ni configuración; el backend además responde 403 en las escrituras.

## 7. Bandera de apagado

`MODULO_CAPACIDAD_ENABLED` (por defecto `true`).

- En `false`, el router no se registra: las rutas responden 404 y el frontend
  muestra “Módulo desactivado”.
- Se configura en `.env` y se pasa por `docker-compose.yml`.

```env
MODULO_CAPACIDAD_ENABLED=false
```

## 8. Cómo probarlo

### Backend

```bash
cd backend
python -m pytest tests/test_modulo_capacidad.py -q
python -m pytest -q
```

Sin Python local, con Docker:

```bash
docker run --rm -v "$PWD/backend:/app" -w /app geotrack-backend \
  sh -c "pip install -q pytest; python -m pytest -q"
```

Resultado de referencia: **40 pruebas del módulo** y **150 pruebas del backend**
en verde.

### Frontend

```bash
cd frontend
npm install
npm run lint
npm run build
```

Lint: los 9 errores que ya existían en el repositorio siguen ahí; los archivos
del módulo no agregan errores. Build: correcto, con un chunk separado de Three.js.

### Docker

```bash
docker compose up -d --build
curl http://localhost:8000/api/modulo-capacidad/salud
# {"modulo":"capacidad","habilitado":true}
```

Panel: `http://localhost:8080/panel/capacidad`.
Credenciales de la demo local: `admin@prueba.local` / `Admin12345!` (cámbialas en
tu `.env`; usa un correo con dominio válido, por ejemplo `admin@geotrack.pe`,
porque `@prueba.local` no pasa la validación de `EmailStr` en `/usuarios/yo`).

## 9. Seguridad y límites

- Escrituras solo con `get_current_admin`; lecturas con `get_current_almacen`.
- No se guardan secretos en el frontend ni en el repositorio; la configuración
  sensible sigue en `.env`.
- CORS: `CORS_ORIGINS` vacío deja solo el mismo origen (el panel llama a `/api`
  por Nginx). En el entorno local se usa una lista explícita
  (`http://localhost:8080,http://127.0.0.1:8080`); nunca se publica `*`.
- El módulo no modifica tablas del núcleo: pedidos y flota se leen, no se escriben.
- El tope de paradas por viaje es una recomendación operativa, no una restricción
  física. El límite duro es `max_viajes_por_dia`.
- La estimación S/M/L es una aproximación cuando el pedido no trae peso/volumen;
  el plan lo advierte explícitamente.
- No se agregó migración Alembic: las tablas nacen con `create_all`. Si el
  proyecto adopta migraciones, hay que generar la revisión de estas 4 tablas.
