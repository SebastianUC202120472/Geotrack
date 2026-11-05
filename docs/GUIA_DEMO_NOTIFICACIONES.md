# Guía de Demostración: Notificaciones Automáticas (Correo y Telegram)

Esta guía describe el paso a paso exacto para realizar **2 demostraciones en vivo** durante tu presentación:
1. **Flujo 1 (Correo)**: Notificación transaccional automática disparada desde el sistema con plantilla HTML.
2. **Flujo 2 (Telegram)**: Verificación de mecánico y asignación interactiva de auxilio mecánico con botones en vivo.

---

## Preparación previa (1 minuto antes de exponer)

Asegúrate de que los contenedores estén corriendo:
```bash
docker compose up -d
```
* **Panel Web**: [http://localhost:8080/panel](http://localhost:8080/panel)
* **Portal de Rastreo y Landing**: [http://localhost:8080](http://localhost:8080)
* **Telegram**: Ten abierta tu aplicación de Telegram en tu teléfono o en la PC con el chat de **`@geotrack_demo_bot`**.
* **Correo**: Ten abierta tu bandeja de entrada de Gmail (`rios.jader.20.04@gmail.com`).

---

## Flujo 1: Generación de Correo Automático (Reclamo Legal / Acuse Transaccional)

Este flujo demuestra el evento **EVT-13** de la especificación: cómo un evento externo dispara correos automáticos sin intervención manual, con diseño profesional HTML y registro en el sistema.

### Pasos en vivo:

1. **Abrir el Libro de Reclamaciones**:
   * En tu navegador, ingresa a: **[http://localhost:8080/reclamos](http://localhost:8080/reclamos)** (o haz clic en *"Libro de Reclamaciones"* al pie de la página principal).

2. **Llenar el formulario con datos de prueba**:
   * **Nombre completo**: `Juan Pérez Demostración`
   * **DNI / CE**: `12345678`
   * **Correo electrónico**: `rios.jader.20.04@gmail.com` *(tu correo para que lo veas llegar)*
   * **Teléfono**: `999888777`
   * **Tipo de bien**: Selecciona `Servicio`
   * **Monto reclamado**: `50.00`
   * **Tipo**: Selecciona `Reclamo`
   * **Detalle del reclamo**: `Demostración de notificación automática por correo: paquete entregado fuera de franja horaria pactada.`

3. **Enviar**:
   * Pulsa el botón **«Enviar Reclamo»**.
   * Verás en pantalla el código oficial generado: **`LR-2026-XXXX`**.

### ¿Qué mostrar a los evaluadores?
* Abre tu bandeja de Gmail (`rios.jader.20.04@gmail.com`):
  * **Correo recibido**: Verás el correo transaccional de GeoTrack con el asunto *"Nuevo reclamo LR-2026-XXXX"* y el acuse al cliente.
  * Muestra la **plantilla HTML responsive**: encabezado azul de GeoTrack, badge de estado, tipografía corporativa y pie legal según Ley 29571.

---

## Flujo 2: Mensajería en Vivo por Telegram (Auxilio Mecánico y Verificación)

Este flujo demuestra las funcionalidades clave de la **Idea 5**:
* Directorio de mecánicos protegidos con número verificado mediante código OTP.
* Propuesta automática del mecánico más cercano por coordenadas.
* Asignación con 1 clic y mensaje con botones interactivos `[ VOY ]` / `[ NO PUEDO ]`.

### Pasos en vivo:

#### Parte A: Alta y Verificación del Mecánico en 1 clic
1. **Ingresar al Panel de Notificaciones**:
   * Entra a: **[http://localhost:8080/panel/notificaciones](http://localhost:8080/panel/notificaciones)** (inicia sesión con tu usuario administrador si te lo pide).
2. **Ir a la pestaña «Directorio de Mecánicos»**:
   * Haz clic en la 3ra pestaña: **Directorio de Mecánicos**.
   * Pulsa el botón **«+ Nuevo Proveedor»** e ingresa:
     * **Nombre**: `Taller Móvil San Isidro`
     * **Empresa / Taller**: `Auxilio Mecánico Rápido`
     * **Tipo de servicio**: `Mecánico`
     * **Teléfono WhatsApp**: `+51999888777`
     * **Chat ID de Telegram**: `8965045745` *(tu Chat ID verificado)*
     * **Dirección**: `Av. República de Panamá 3500, San Isidro`
     * **Distritos**: `San Isidro, Miraflores, Surquillo`
   * Pulsa **«Registrar Mecánico»**. Aparecerá en la tarjeta con estado en amarillo *"No verificado"*.
3. **Verificar el número**:
   * En la tarjeta del mecánico creado, haz clic en **«Verificar número»**.
   * **¡Mira tu Telegram!** Te llegará un mensaje de `@geotrack_demo_bot`:
     > *"Hola Taller Móvil San Isidro, tu código de verificación para GeoTrack Auxilio Mecánico es: XXXXXX. Expira en 15 minutos."*
   * Copia ese código de 6 dígitos, pégalo en el modal de la pantalla web y pulsa **«Confirmar Verificación»**.
   * La tarjeta cambiará al badge verde: **«Verificado · Listo para auxilio»**.

#### Parte B: Asignación de Auxilio con Botones Interactivos
1. **Ir al módulo de Auxilio Mecánico**:
   * Entra en el menú lateral a: **Auxilio mecánico** ([http://localhost:8080/panel/auxilio](http://localhost:8080/panel/auxilio)).
2. **Seleccionar una incidencia**:
   * Haz clic en una de las incidencias mecánicas abiertas (o en el botón *"Atender"* de la avería).
3. **Observar la tarjeta inteligente**:
   * Verás la tarjeta destacada:
     > **MECÁNICO SUGERIDO POR CERCANÍA**  
     > **Taller Móvil San Isidro** (A X.X km de la avería)
4. **Confirmar con 1 clic**:
   * Haz clic en el botón: **«Confirmar y enviar auxilio a Taller Móvil San Isidro»**.
5. **Comprobar la llegada a Telegram**:
   * Abre tu Telegram: te llegará en tiempo real la alerta urgente con:
     * Placa del vehículo.
     * Falla reportada.
     * Nombre y teléfono del conductor.
     * Enlace directo a Google Maps con la ubicación exacta de la avería.
     * Dos botones interactivos en Telegram: **`[ ✅ VOY ]`** y **`[ ❌ NO PUEDO ]`**.
6. **Interactuar**:
   * Pulsa el botón **`✅ VOY`** desde Telegram para simular la confirmación del proveedor.

---

## Bonus: Mostrar la Bitácora de Auditoría en el Panel
Para cerrar tu presentación demostrando el cumplimiento de los requisitos de observabilidad:
1. Regresa a **[http://localhost:8080/panel/notificaciones](http://localhost:8080/panel/notificaciones)**.
2. Entra a la pestaña **«Bitácora de Envíos Externos»**:
   * Muestra la tabla en vivo: se verán los mensajes recién enviados con su evento (`AUXILIO_MECANICO`, `VERIFICACION_NUMERO`, etc.), el canal (`telegram` / `correo`), el estado en verde `ENVIADO`, la fecha y los teléfonos protegidos con enmascaramiento por privacidad (`+51****77`).
3. Muestra la pestaña **«Plantillas y Canales»**:
   * Muestra cómo se pueden activar/desactivar avisos con interruptores y editar los textos sin necesidad de programar.
