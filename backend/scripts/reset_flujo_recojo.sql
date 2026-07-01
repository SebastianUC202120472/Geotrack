-- Reset para probar el flujo recojo -> entrega de cero.
-- CONSERVA: usuarios admin/almacen/conductor + perfiles de conductor + vehículos
--           + la BANDEJA de correos (solicitudes del cliente: correo_*).
-- BORRA todo lo demás (pedidos, recojos, rutas, almacén, reportes, incidencias,
-- notificaciones, clientes, ubicaciones, etc.) y reinicia los IDs.
-- Tras correrlo, REINICIA el backend para que se re-siembren los catálogos
-- (motivos de rechazo y parámetros de combustible en parametros_sistema).
--
-- OJO: la aceptación de una solicitud requiere un CLIENTE registrado con dirección
-- de recojo geocodificada. Como este reset borra los clientes, primero registra un
-- cliente (con su dirección) en el panel y luego acepta la solicitud con el Excel.
BEGIN;
TRUNCATE TABLE
  pedidos,
  ruta_detalles,
  rutas,
  solicitudes_recojo,
  reportes,
  incidencias,
  notificaciones,
  historial_pedidos,
  evidencias_entrega,
  liquidaciones,
  ubicaciones_conductor,
  clientes_corporativos,
  solicitudes_restablecimiento,
  parametros_sistema
  RESTART IDENTITY CASCADE;
-- (Se conservan correo_conversaciones / correo_mensajes / correo_adjuntos = la bandeja.)

-- Por si quedara algún usuario con rol fuera de los tres vigentes.
DELETE FROM usuarios WHERE rol NOT IN ('admin', 'almacen', 'conductor');
COMMIT;
