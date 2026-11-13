# Módulo de mantenimiento y documentos de la flota (Idea 4)

Este documento explica la **semana 13** del módulo: el backend que registra los
mantenimientos preventivos/correctivos, los documentos legales de la flota
(SOAT, revisión técnica, tarjeta de circulación, seguro y permisos) y las
licencias de los conductores, calcula sus vencimientos, entrega la ficha de
estado de cada unidad y las alertas que usará el panel.

El módulo vive en sus propios archivos y tablas. **Solo lee** las tablas
`vehiculos` y `conductor_perfiles` del núcleo; no modifica pedidos, rutas,
usuarios ni licencias.

## 1. Alcance de la semana 13

| Entregable | Dónde verlo |
| --- | --- |
| Tablas propias: documentos, mantenimientos, configuración y auditoría | `backend/app/models/mantenimiento.py` |
| Contratos y validaciones (placas, fechas, costos, estados) | `backend/app/schemas/mantenimiento.py` |
| Consultas a base de datos (incluye licencias del núcleo, solo lectura) | `backend/app/repositories/mantenimiento_repository.py` |
| Reglas: vencimientos, alertas 30/15/7, ficha y estado de flota | `backend/app/services/mantenimiento_service.py` |
| API REST con permisos | `backend/app/api/mantenimiento.py` |
| Pruebas del módulo | `backend/tests/test_modulo_mantenimiento.py` |
| Bandera de apagado | `MODULO_MANTENIMIENTO_ENABLED` |

El frontend del módulo (pestañas de documentos, mantenimientos y alertas) se
trabaja en la semana 14. La semana 13 deja la API lista y verificada para que la
semana 14 solo consuma endpoints.

## 2. Arquitectura

```
backend/app/
  api/mantenimiento.py                    # endpoints + bandera MODULO_MANTENIMIENTO_ENABLED
  models/mantenimiento.py                 # 4 tablas propias del módulo
  schemas/mantenimiento.py                # contratos Pydantic de entrada/salida
  repositories/mantenimiento_repository.py
  services/mantenimiento_service.py

backend/tests/
  test_modulo_mantenimiento.py

docs/
  MODULO_MANTENIMIENTO.md
```

Capas:

- **Router**: autenticación, roles y códigos HTTP. No contiene reglas de negocio.
- **Service**: estados calculados, alertas, resumen, validación de placa y
  coherencia de fechas.
- **Repository**: consultas y operaciones sobre las tablas del módulo.
- **Modelos**: solo tablas del módulo; la tabla `vehiculos` se lee, no se escribe.

### Tablas propias

| Tabla | Para qué sirve |
| --- | --- |
| `mantenimiento_documentos` | SOAT, revisión técnica, tarjeta de circulación, seguro y permisos. Cada renovación es una fila nueva. |
| `mantenimiento_registros` | Órdenes preventivas y correctivas, con fecha, kilometraje, costo, taller y estado. |
| `mantenimiento_configuracion` | Fila única: días de aviso de documentos y mantenimientos, moneda y banderas de alertas. |
| `mantenimiento_auditoria` | Altas, ediciones, bajas, cierres y cambios de configuración. |

Las tablas se crean con el `create_all` que el backend ya ejecuta al arrancar
(`preparar_esquema`). No se agregó una revisión de Alembic porque el proyecto no
usa migraciones versionadas para el resto del esquema.

## 3. Reglas de negocio

### Documentos

- La placa debe existir en la flota y estar activa (sin baja lógica).
- Formato de placa: `ABC-123` (se normaliza a mayúsculas).
- `fecha_vencimiento` debe ser posterior a `fecha_emision`.
- No se permite el mismo `tipo_documento` + `numero` dos veces para la misma
  placa. Sí se permite una renovación con otro número.
- El estado **no se guarda**: se calcula con la fecha de vencimiento y los días
  de aviso:

| Condición | Estado |
| --- | --- |
| `fecha_vencimiento < hoy` | `VENCIDO` |
| `0 <= días <= días_aviso_documento` | `POR_VENCER` |
| `días > días_aviso_documento` | `VIGENTE` |

- Documentos obligatorios para el estado de flota: `SOAT` y
  `REVISION_TECNICA`.
- **Renovaciones**: cada fila nueva reemplaza a la anterior del mismo tipo. Para
  el estado y las alertas manda el documento con el vencimiento más lejano; los
  anteriores quedan en `/documentos` como historial y no generan alertas.
- Los contadores (`documentos_total`, `documentos_vencidos`, `por_tipo`, etc.)
  usan el documento actual de cada tipo, no el historial.

### Licencias de conductores

- La licencia vive en el núcleo (`conductor_perfiles.licencia_numero` y
  `licencia_vencimiento`). Este módulo **no la edita**: solo la lee y calcula su
  estado con las mismas reglas que un documento.
- `GET /licencias` es **exclusivo del administrador**, porque son datos
  personales. El almacén no puede verlas.
- Una licencia sin fecha de vencimiento se reporta como `SIN_DOCUMENTO`.
- Las alertas de licencias solo se agregan a `/alertas` cuando quien consulta es
  administrador.

### Umbrales de aviso: 30, 15 y 7 días

Un documento o licencia por vencer genera una severidad escalonada según los
días que faltan:

| Días restantes | Severidad | `umbral` |
| --- | --- | --- |
| `0` a `7` | `ALTA` | `7` |
| `8` a `15` | `MEDIA` | `15` |
| `16` a `30` | `BAJA` | `30` |
| `> 30` | sin alerta | — |
| negativo (ya venció) | `ALTA` | `null` |

La comparación se hace contra `dias_aviso_documento` (30 por defecto) para
decidir si el documento está `POR_VENCER`; los umbrales 30/15/7 definen la
severidad de la alerta.

### Mantenimientos

- La placa debe existir y estar activa.
- Estados: `PROGRAMADO`, `EN_PROCESO`, `COMPLETADO`, `CANCELADO`.
- Un mantenimiento `COMPLETADO` debe tener `fecha_ejecucion`. Al usar
  `/completar`, si no se envía, se toma la fecha del día.
- Un mantenimiento abierto con `fecha_programada` pasada se marca `vencido` en
  la respuesta y genera alerta.
- La moneda del registro se toma de la configuración (`PEN` por defecto).

### Alertas calculadas

No hay tabla de alertas: se calculan en cada consulta para que nunca queden
desactualizadas.

1. Documento actual `VENCIDO` → severidad `ALTA`, sin umbral.
2. Documento actual `POR_VENCER` → severidad `BAJA`/`MEDIA`/`ALTA` según los
   umbrales 30/15/7 descritos arriba. Las renovaciones anteriores no avisan.
3. Vehículo sin `SOAT` o sin `REVISION_TECNICA` → severidad `MEDIA`.
4. Licencia `VENCIDA` → `ALTA`; licencia `POR_VENCER` → severidad escalonada
   30/15/7. **Solo se incluyen si quien consulta es administrador.**
5. Mantenimiento abierto con fecha pasada → `ALTA`.
6. Mantenimiento abierto para hoy → `ALTA`.
7. Mantenimiento abierto dentro de los días de aviso → `MEDIA`.

Las alertas de documentos y de mantenimientos se pueden apagar por separado con
`alertas_documentos` y `alertas_mantenimientos`. En `/resumen`, `alertas_total`
incluye las licencias solo cuando el usuario es administrador.

### Estado general de la flota

| Estado | Cuándo |
| --- | --- |
| `SIN_DOCUMENTOS` | El vehículo no tiene ningún documento registrado. |
| `VENCIDO` | Al menos un documento está vencido. |
| `INCOMPLETO` | Tiene documentos, pero falta SOAT o revisión técnica. |
| `POR_VENCER` | Todos los obligatorios están presentes y alguno está por vencer. |
| `AL_DIA` | Documentos obligatorios presentes y vigentes. |

### Marca «no apto para salir»

`/flota` y `/flota/{placa}` devuelven `apto_para_salir` y `motivos_no_apto`.
La marca es **una alerta visible**: no bloquea la asignación de rutas del núcleo.

- `apto_para_salir = false` si hay al menos un documento **actual** vencido o si
  falta un documento obligatorio. Una renovación vigente neutraliza al registro
  anterior del mismo tipo.
- `motivos_no_apto` explica cada causa, por ejemplo
  `["SOAT vencido"]` o `["Falta REVISION_TECNICA"]`.
- Sin documentos, la unidad tampoco es apta.

### Ficha de estado de una unidad

`GET /flota/{placa}` junta en una sola vista:

- Datos del vehículo (solo lectura): placa, marca, código, estado y odómetro
  estimado con el mayor kilometraje registrado en sus mantenimientos.
- Sus documentos, con estado y días restantes. El arreglo conserva el historial
  completo; los contadores usan la renovación más reciente de cada tipo.
- Sus mantenimientos, con `vencido` y días para la fecha programada.
- Sus costos: total, del mes, número de mantenimientos completados y costo por
  kilómetro cuando hay al menos dos lecturas de kilometraje.
- El estado documental, `apto_para_salir` y `motivos_no_apto`.

La exportación a PDF de la ficha se trabaja en la semana 15.

## 4. API

Todas las rutas cuelgan de `/api/modulo-mantenimiento`. Lectura: admin y
almacén. Escritura: solo admin. **Las licencias de conductores son solo para
admin.**

| Método | Ruta | Rol | Descripción |
| --- | --- | --- | --- |
| GET | `/salud` | público | Estado del módulo |
| GET | `/resumen` | admin/almacén | KPIs de documentos, mantenimientos y costos; cuenta licencias solo al admin |
| GET | `/flota` | admin/almacén | Estado documental, `apto_para_salir` y motivos por vehículo |
| GET | `/flota/{placa}` | admin/almacén | Ficha de la unidad: documentos, mantenimientos y costos |
| GET | `/alertas` | admin/almacén | Vencidos, por vencer y faltantes; suma licencias solo al admin |
| GET | `/licencias` | **admin** | Licencias de conductores con estado y nivel de alerta |
| GET | `/documentos` | admin/almacén | Filtros `placa`, `tipo`, `estado`, `limite` |
| POST | `/documentos` | admin | Registra un documento (201/404/409/422) |
| GET | `/documentos/{id}` | admin/almacén | Detalle de un documento |
| PATCH | `/documentos/{id}` | admin | Edita un documento (auditado) |
| DELETE | `/documentos/{id}` | admin | Baja lógica |
| GET | `/mantenimientos` | admin/almacén | Filtros `placa`, `tipo`, `estado`, `desde`, `hasta`, `limite` |
| POST | `/mantenimientos` | admin | Programa o registra un mantenimiento (201) |
| GET | `/mantenimientos/{id}` | admin/almacén | Detalle de un mantenimiento |
| PATCH | `/mantenimientos/{id}` | admin | Edita un mantenimiento |
| POST | `/mantenimientos/{id}/completar` | admin | Cierra con fecha, costo y kilometraje |
| DELETE | `/mantenimientos/{id}` | admin | Baja lógica |
| GET | `/configuracion` | admin/almacén | Días de aviso, moneda y banderas |
| PUT | `/configuracion` | admin | Actualiza la configuración (auditado) |
| GET | `/auditoria` | admin | Últimos movimientos (máx. 500) |

### Ejemplo: registrar un SOAT

```json
POST /api/modulo-mantenimiento/documentos
{
  "placa": "ABC-123",
  "tipo_documento": "SOAT",
  "numero": "SOAT-2026-001",
  "entidad_emisora": "La Positiva",
  "fecha_emision": "2026-01-15",
  "fecha_vencimiento": "2027-01-15",
  "archivo_url": "/media/documentos/soat-abc-123.pdf"
}
```

### Ejemplo: programar un mantenimiento

```json
POST /api/modulo-mantenimiento/mantenimientos
{
  "placa": "ABC-123",
  "tipo": "PREVENTIVO",
  "categoria": "ACEITE",
  "descripcion": "Cambio de aceite y filtros",
  "prioridad": "MEDIA",
  "fecha_programada": "2026-11-20",
  "kilometraje": 48200
}
```

### Ejemplo: completar un mantenimiento

```json
POST /api/modulo-mantenimiento/mantenimientos/1/completar
{
  "fecha_ejecucion": "2026-11-20",
  "kilometraje": 48310,
  "costo": 320.50,
  "taller": "Taller Central"
}
```

### Ejemplo: ficha de estado de una unidad

```json
GET /api/modulo-mantenimiento/flota/ABC-123
{
  "placa": "ABC-123",
  "marca": "Toyota",
  "codigo": "VE-001",
  "estado_vehiculo": "DISPONIBLE",
  "odometro_actual": 48310,
  "documentos": [ ... ],
  "mantenimientos": [ ... ],
  "costos": {
    "costo_total": 320.5,
    "costo_mes": 320.5,
    "costo_por_kilometro": null,
    "moneda": "PEN",
    "mantenimientos_completados": 1,
    "ultimo_kilometraje": 48310
  },
  "documentos_total": 2,
  "documentos_faltantes": [],
  "estado_general": "POR_VENCER",
  "apto_para_salir": true,
  "motivos_no_apto": []
}
```

### Ejemplo: licencias (solo admin)

```json
GET /api/modulo-mantenimiento/licencias
[
  {
    "conductor_id": 1,
    "usuario_id": 4,
    "nombre": "Ana Torres",
    "correo": "ana@siol.com",
    "licencia_numero": "Q12345678",
    "licencia_vencimiento": "2026-12-03",
    "estado": "POR_VENCER",
    "dias_para_vencer": 20,
    "nivel_alerta": "BAJA",
    "umbral": 30
  }
]
```

## 5. Bandera de apagado

`MODULO_MANTENIMIENTO_ENABLED` (por defecto `true`).

- En `false`, el router no se registra: las rutas responden 404 y el resto del
  sistema sigue funcionando igual.
- Se configura en `.env` y se pasa por `docker-compose.yml`.

```env
MODULO_MANTENIMIENTO_ENABLED=false
```

## 6. Cómo probarlo

### Backend con pytest

```bash
cd backend
python -m pytest tests/test_modulo_mantenimiento.py -q
python -m pytest -q
```

### Con Docker

```bash
docker compose exec backend pip install -q pytest httpx
docker compose exec backend python -m pytest tests/test_modulo_mantenimiento.py -q
```

### Comprobar la API

```bash
curl http://localhost:8000/api/modulo-mantenimiento/salud
# {"modulo":"mantenimiento","habilitado":true}
```

Documentación interactiva: `http://localhost:8000/docs` → sección
**Modulo mantenimiento**.

## 7. Seguridad y límites

- Escrituras solo con `get_current_admin`; lecturas con `get_current_almacen`.
- Las licencias de conductores son datos personales: `GET /licencias` usa
  `get_current_admin` y `/alertas` agrega licencias solo cuando el rol es admin.
  El módulo **no edita** `conductor_perfiles`, solo lo lee.
- No se guardan secretos ni archivos binarios en las tablas: `archivo_url`
  referencia un enlace ya existente (por ejemplo, una URL firmada de `/media`).
- El módulo no modifica la tabla `vehiculos`: la usa para validar la placa y
  mostrar marca/estado.
- Las bajas son lógicas (`eliminado_en`): se conserva el historial y la
  auditoría.
- Los estados se calculan al consultar; si cambia la fecha del servidor o los
  días de aviso, las alertas se ajustan solas.
- No se agregó migración Alembic: las tablas nacen con `create_all`. Si el
  proyecto adopta migraciones, hay que generar la revisión de estas 4 tablas.