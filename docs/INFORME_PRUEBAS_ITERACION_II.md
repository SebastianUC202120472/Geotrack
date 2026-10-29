# Informe de pruebas — Iteración II (GeoTrack · SIOL-SAVA)

Fecha de corte: 29-oct-2026 · Rama: `develop`

## 1. Resumen

| Suite | Herramienta | Pruebas | Resultado |
|---|---|---|---|
| Backend (unitarias e integración ligera) | pytest | 176 | 176 pasan |
| App del conductor | Jest (`jest-expo`) | 14 | 14 pasan |
| Panel web | ESLint + build de Vite | — | 0 errores de lint, build correcto |
| App del conductor | TypeScript (`tsc --noEmit`) | — | sin errores |
| Flujos de punta a punta (manuales, scripts de API) | Python contra backend + PostgreSQL de prueba | 10 recorridos (F1–F10) | todos pasan |

Todo lo automático corre en la integración continua (`.github/workflows/ci.yml`) en cada push y PR: backend (import, pytest, bandit), panel (lint y build) y app (tsc y Jest).

## 2. Pruebas automáticas por módulo

| Módulo | Archivo | Pruebas | Qué verifica |
|---|---|---|---|
| Arranque y rutas | `backend/tests/test_smoke.py` | 9 | La app se construye, las rutas clave existen, JWT y hash de contraseñas |
| Fotos subidas | `backend/tests/test_imagenes.py` | 9 | Tipo real y tamaño máximo de las imágenes (EX-02) |
| Portal de clientes | `backend/tests/test_portal_logica.py`, `test_portal_repo_codigo.py`, `test_portal_demo.py`, `test_portal_ayuda.py`, `test_datos_demo_portal.py` | 49 | Estados visibles al cliente, tokens por pedido y por empresa, búsqueda por código, datos de demostración |
| Almacén y zonas | `backend/tests/test_almacen_directo.py`, `test_pedidos_zonas.py` | 4 | Recepción directa y agrupación por zona |
| Correcciones F1–F10 | `backend/tests/test_correcciones.py` | 105 | Acceso y cuentas, clientes, recojos, geocodificación, despacho concurrente, entrega con foto/GPS/receptor, paradas cerradas, reportes con foto, auxilio, reprogramación, cancelación con motivo, Libro de Reclamaciones y su plazo legal, indicadores, enlaces firmados de fotos, almacenamiento en la nube y retención de datos |
| Cifrado local | `mobile/src/store/__tests__/cifrado.test.ts` | 4 | La cola offline se guarda cifrada (AES-256-GCM), no se puede alterar y lee datos de la versión anterior |
| Ruta sin señal | `mobile/src/store/__tests__/rutaOffline.test.ts` | 4 | La última ruta se muestra sin señal, se borra al terminar la ruta o al cerrar sesión |
| Sincronización | `mobile/src/features/sync/__tests__/sincronizador.test.ts` | 3 | Orden foto → entrega, reporte con foto y reanudación tras corte de señal sin repetir pasos |
| Optimización | `mobile/src/services/__tests__/routeService.test.ts` | 3 | Aviso de km, ahorro y paradas sin ubicación |

## 3. Pruebas de punta a punta

Se corrieron contra un backend con base PostgreSQL vacía (nunca contra la base de producción), con scripts que usan la API como lo hacen el panel, la app y el portal. Cada fase se probó con su recorrido completo: acceso, clientes y portal, recojos y almacén, geocodificación, despacho (incluidos dos despachos simultáneos), entrega en campo, fallidos y reprogramación, reclamos, tablero e indicadores, y archivos protegidos. Además se repitieron F6, F7, F8 y F10 con las dependencias actualizadas (FastAPI 0.143, SQLAlchemy 2.1) y pasaron.

Revisión visual: panel en 375 px, 768 px y escritorio (17 pantallas sin desbordes) y portal en español e inglés.

## 4. Pendientes y alcance

- **Plan PU-01 a PU-15 del Primer Entregable:** este informe agrupa las pruebas por módulo. Falta cruzar cada PU del plan con su prueba automática; requiere el documento del Primer Entregable.
- **Batería (RNF-011):** la app ya mide el consumo en cada jornada y el tablero lo muestra en %/h. El dato real sale con la primera jornada completa de un conductor en la calle.
- **Celular real:** en esta iteración la app se validó con `tsc` y Jest. Falta probarla en un celular y en una jornada con conductores reales (EX-16).
