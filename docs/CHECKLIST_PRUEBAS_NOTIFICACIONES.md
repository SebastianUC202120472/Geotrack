# Checklist de eventos de notificaciones

Marca cada evento después de ejecutar el flujo, comprobar que llegó el mensaje y verificar su registro en `notificaciones_envios`.

## Eventos implementados

| Hecho | Evento | Cómo dispararlo | Canal / destinatario | Resultado esperado |
| :--: | :-- | :-- | :-- | :-- |
| [ ] | `PEDIDO_PROGRAMADO` | Asignar un pedido a una ruta. | Telegram / destinatario | Llega aviso de pedido programado. |
| [ ] | `PEDIDO_EN_CAMINO` | Optimizar o iniciar una ruta desde la app del conductor. | Telegram / destinatario | Llega aviso con el orden de parada. |
| [ ] | `PEDIDO_ESTA_CERCA` | Mover al conductor hasta la proximidad configurada del pedido. | Telegram / destinatario | Llega aviso de proximidad. |
| [ ] | `PEDIDO_ENTREGADO` | Marcar una parada como entregada. | Telegram / destinatario | Llega confirmación de entrega. |
| [ ] | `PEDIDO_NO_ENTREGADO` | Marcar una parada como fallida e indicar motivo. | Telegram / destinatario | Llega aviso con el motivo del fallo. |
| [ ] | `PEDIDO_REPROGRAMADO` | Reprogramar o reabrir un pedido fallido. | Telegram / destinatario | Llega aviso de reprogramación. |
| [ ] | `RECOJO_COMPLETADO` | Registrar la recepción del recojo con evidencias. | Correo / cliente y almacén | Llegan dos correos HTML. |
| [ ] | `PAQUETES_FALTANTES` | Confirmar ingreso con paquetes faltantes. | Correo / cliente y administrador | Llegan dos correos HTML con el detalle. |
| [ ] | `RETORNOS_ALMACEN` | Finalizar una ruta con pedidos fallidos. | Correo / almacén | Llega aviso de retornos. |
| [ ] | `AUXILIO_MECANICO` | Reportar una avería mecánica desde la app. | Correo y Telegram / administrador | Llegan avisos por los canales configurados. |
| [ ] | `RECLAMO_NUEVO` | Enviar un reclamo o queja desde el landing. | Correo / administrador | Llega aviso con código y detalle. |

Los avisos al destinatario por Telegram requieren que antes active los avisos desde el portal
(pedido verificado con su DNI → "Activar avisos en Telegram").

## Auxilio mecánico y resumen diario

| Hecho | Evento | Cómo dispararlo | Requisito adicional | Resultado esperado |
| :--: | :-- | :-- | :-- | :-- |
| [ ] | `AYUDA_ASIGNADA` | En Auxilio mecánico, abrir la incidencia y pulsar "Confirmar y enviar auxilio a …". | Mecánico activo, verificado y con chat de Telegram. | Llega aviso al mecánico sugerido. |
| [ ] | `AYUDA_EN_CAMINO` | El mecánico asignado responde `VOY` desde Telegram. | Webhook registrado con `TELEGRAM_WEBHOOK_SECRET`. | Llega aviso al conductor. |
| [ ] | `RESUMEN_DEL_DIA` | Esperar a las 20:00 (`America/Lima`) con el `notificador` encendido. | Cliente corporativo con correo. | Llega el resumen del día. |

## Otros correos automáticos existentes

| Hecho | Flujo | Cómo dispararlo | Canal / destinatario |
| :--: | :-- | :-- | :-- |
| [ ] | OTP del portal | Iniciar sesión empresarial con credenciales válidas. | Correo / cliente corporativo |
| [ ] | Formulario de contacto | Enviar el formulario de contacto del landing. | Correo / ventas o administrador |
| [ ] | Acuse de reclamo | Enviar reclamo con correo del consumidor. | Correo / consumidor |
| [ ] | Confirmación de recojo | Aceptar una solicitud desde la Bandeja. | Correo / cliente |
