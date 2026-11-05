# Guía de Demostración: Notificaciones Automáticas (Correo y Telegram)

Esta guía describe el paso a paso para realizar las demostraciones en vivo:
1. **Flujo 1 (Correo)**: Notificación transaccional automática disparada desde el sistema con plantilla HTML.
2. **Flujo 2 (Telegram)**: Verificación de mecánico y asignación de auxilio mecánico con botones en vivo.
3. **Flujo 3 (Telegram)**: El destinatario se suscribe a los avisos de su pedido desde el portal.

---

## Preparación previa

1. En el `.env` de la raíz (nunca en el repositorio):
   ```env
   NOTIFICACIONES_HABILITADAS=true
   MAIL_ENABLED=true            # con MAIL_ADDRESS y MAIL_PASSWORD (contraseña de aplicación)
   TELEGRAM_BOT_TOKEN=<token que entrega @BotFather>
   TELEGRAM_BOT_USERNAME=<usuario del bot, sin @>
   TELEGRAM_WEBHOOK_SECRET=<texto largo al azar>
   ```
2. Levanta el sistema (el servicio `notificador` detecta los eventos y envía los avisos):
   ```bash
   docker compose up -d --build backend frontend notificador
   ```
3. **Registra el webhook de Telegram** para que los botones `VOY` / `NO PUEDO` y el comando
   `/start` lleguen al sistema. Telegram necesita una URL pública (por ejemplo, el puerto 8000 de un
   Codespace en *Public* o un túnel de ngrok) y el mismo `secret_token` del `.env`; sin él, el
   backend rechaza la llamada con 403. Antes de registrarlo, obtén los chat ID que necesites con
   `backend/scripts/telegram_obtener_chat_id.py` (con el webhook activo Telegram ya no los entrega así):
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<url-publica>/api/notificaciones/webhook/telegram&secret_token=<TELEGRAM_WEBHOOK_SECRET>"
   ```
4. Ten abiertos:
   * **Panel Web**: [http://localhost:8080/panel](http://localhost:8080/panel)
   * **Portal de Rastreo**: [http://localhost:8080/portal](http://localhost:8080/portal)
   * **Telegram** con el chat del bot y tu bandeja de correo de prueba.

---

## Flujo 1: Generación de Correo Automático (Reclamo nuevo)

Este flujo demuestra cómo un evento del sistema dispara un correo automático sin intervención manual,
con diseño HTML y registro en la bitácora.

### Pasos en vivo:

1. **Abrir el Libro de Reclamaciones** desde el pie de la página principal.
2. **Llenar el formulario con datos de prueba** (nunca datos reales):
   * **Nombre completo**: `Juan Pérez Demostración`
   * **DNI / CE**: `12345678`
   * **Correo electrónico**: `<tu correo de prueba>`
   * **Teléfono**: `999888777`
   * **Tipo de bien**: `Servicio` · **Monto**: `50.00` · **Tipo**: `Reclamo`
   * **Detalle**: `Demostración de notificación automática por correo.`
3. **Enviar**: verás el código generado del reclamo.

### ¿Qué mostrar?
* En el correo del administrador llega el aviso *"Nuevo reclamo …"* con la plantilla HTML de GeoTrack.

---

## Flujo 2: Auxilio Mecánico por Telegram

Muestra el directorio de mecánicos con número verificado, la propuesta del mecánico más cercano, la
confirmación del administrador con 1 clic y la respuesta del mecánico con botones `[ VOY ]` / `[ NO PUEDO ]`.

#### Parte A: Alta y verificación del mecánico
1. Entra a **Centro de Notificaciones → Directorio de Mecánicos** y pulsa **«+ Nuevo Proveedor»**:
   * **Nombre**: `Taller Móvil San Isidro` · **Tipo de servicio**: `Mecánico`
   * **Teléfono**: `+51999888777`
   * **Chat ID de Telegram**: `<tu chat ID>` (lo obtienes con `backend/scripts/telegram_obtener_chat_id.py`)
   * **Dirección**: `Av. República de Panamá 3500, San Isidro`
2. En su tarjeta pulsa **«Verificar número»**: el bot te envía un código de 6 dígitos (vence en 15 min).
   Ingrésalo y la tarjeta pasa a **«Verificado · Listo para auxilio»**.

#### Parte B: Asignación del auxilio
1. Entra a **Auxilio mecánico** y abre una incidencia abierta.
2. Verás la tarjeta **«Mecánico sugerido por cercanía»** (a X km de la avería).
3. Pulsa **«Confirmar y enviar auxilio a …»**: se registra la ayuda y el bot le envía al mecánico la
   placa, la falla, el conductor, el mapa de la avería y los botones `[ ✅ VOY ]` / `[ ❌ NO PUEDO ]`.
4. Pulsa **`✅ VOY`**: si el conductor vinculó su Telegram (pestaña **Conductores en Telegram**),
   recibe *"Tu auxilio va en camino"*. Solo cuenta la respuesta del mecánico asignado.
5. Si pulsas **`❌ NO PUEDO`** (o pasan 10 minutos sin respuesta), el administrador recibe un correo y
   la tarjeta muestra al **siguiente mecánico sugerido** para enviarle el auxilio con otro clic.

---

## Flujo 3: El destinatario se suscribe desde el portal

1. En el **Portal**, rastrea un pedido en curso con su código y verifica la identidad con el DNI.
2. Aparece la tarjeta **«Reciba los avisos de su pedido por Telegram»**: pulsa **«Activar avisos en
   Telegram»** y luego **«Iniciar»** en el bot. El enlace es personal, va firmado y vence en 24 horas.
3. Desde ese momento llegan los avisos del pedido (programado, en camino, está cerca, entregado…).
   Escribir `STOP` al bot da de baja el chat (Ley 29733); `AYUDA` devuelve el enlace al portal.

---

## Cierre: Bitácora y Plantillas
1. En **Centro de Notificaciones → Bitácora de Envíos Externos** se ven los avisos con su evento, canal,
   estado (`ENVIADO`, `PENDIENTE`, `FALLIDO`) y el destino enmascarado.
2. En **Plantillas y Canales** se apaga un aviso o se edita su texto; el cambio se aplica a los
   próximos avisos de ese evento.
