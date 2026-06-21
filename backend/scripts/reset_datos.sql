-- Reset total de datos del sistema (operación administrativa puntual).
-- Conserva: usuario(s) admin + bandeja de correos (solicitudes de recojo: correo_*).
-- Borra todo lo demás y reinicia los IDs. Tras correrlo, reiniciar el backend para
-- que se re-siembren los catálogos (motivos de rechazo y parámetros de combustible).
BEGIN;
TRUNCATE TABLE
  pedidos, rutas, ruta_detalles, incidencias, reportes, evidencias_entrega,
  ubicaciones_conductor, historial_pedidos, liquidaciones, vehiculos,
  clientes_corporativos, conductor_perfiles, solicitudes_restablecimiento,
  parametros_sistema
  RESTART IDENTITY CASCADE;
DELETE FROM usuarios WHERE rol <> 'admin';
COMMIT;
