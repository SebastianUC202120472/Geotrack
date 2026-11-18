# Borrador de preguntas frecuentes (ES/EN) del asistente de atención

**Estado:** borrador para validar por el gerente · **34 preguntas** en español e inglés · **3 con datos por confirmar** (marcadas con ⚠).

Este documento se genera solo desde `app/conocimiento/semilla.json`, que es lo que el asistente carga la primera vez. Para corregir una respuesta, indíquelo aquí o edítela en el JSON. Desde la semana 15 también se podrá editar desde la pantalla de administración del panel.

Fuente de los datos: textos de la landing (cobertura, servicio, contacto, reclamos) y comportamiento del portal (verificación por DNI, reprogramación, portal de empresas). Los días de reparto, los plazos de entrega, el manejo de entregas fallidas, el cambio de dirección, el horario de atención y el origen del código del pedido los confirmó el gerente. Lo que sigue sin confirmar no se inventó: quedó redactado de forma prudente y marcado con ⚠.

## Datos por confirmar

- **¿Cuánto cuesta el servicio?** (`tarifas`): Confirmar que no se publican tarifas al público.
- **¿Cómo me comunico con SAVA?** (`contacto`): Horario confirmado (9:00 a 18:00). Falta confirmar si los días de atención son de lunes a sábado (como dice la landing) y si hay un correo público de atención.
- **¿Dónde están ubicados?** (`direccion`): Confirmar si se atiende al público en esa dirección o si es solo almacén.

## Cobertura

### 1. ¿A qué distritos llegan?

**ES:** SAVA cubre los 43 distritos de Lima Metropolitana y el Callao, de Ancón a Pucusana y de La Molina al Callao, con rutas diarias organizadas por zonas. Si una tienda necesita una zona con horario especial, se arman rutas dedicadas según su volumen.

**EN — Which districts do you cover?** SAVA covers all 43 districts of Metropolitan Lima plus Callao, from Ancón to Pucusana and from La Molina to Callao, with daily routes organized by zone. If a store needs a zone with special hours, dedicated routes are built based on its volume.

### 2. Zonas de reparto y sus distritos

**ES:** Lima Norte: Independencia, Comas, Los Olivos, SMP, Carabayllo, Puente Piedra, Ancón. Lima Centro: Cercado, Jesús María, Lince, Miraflores, San Isidro, Surquillo, San Borja. Lima Este: SJL, Santa Anita, Ate, La Molina, El Agustino, Chaclacayo. Lima Sur: Surco, SJM, VMT, Villa El Salvador, Chorrillos, Lurín, Pucusana. Callao: Callao, Bellavista, La Perla, Ventanilla, Mi Perú. Estos son los distritos de referencia de cada zona; la cobertura es de los 43 distritos de Lima Metropolitana y el Callao.

**EN — Delivery zones and their districts** North Lima: Independencia, Comas, Los Olivos, SMP, Carabayllo, Puente Piedra, Ancón. Central Lima: Cercado, Jesús María, Lince, Miraflores, San Isidro, Surquillo, San Borja. East Lima: SJL, Santa Anita, Ate, La Molina, El Agustino, Chaclacayo. South Lima: Surco, SJM, VMT, Villa El Salvador, Chorrillos, Lurín, Pucusana. Callao: Callao, Bellavista, La Perla, Ventanilla, Mi Perú. These are each zone's reference districts; coverage includes all 43 districts of Metropolitan Lima plus Callao.


## Contacto

### 3. ¿Cómo me comunico con SAVA? ⚠

**ES:** Por teléfono o WhatsApp al +51 922 507 593, de lunes a sábado, de 9:00 a 18:00. También puede pedir en este chat que una persona del equipo revise su caso.

**EN — How do I contact SAVA?** By phone or WhatsApp at +51 922 507 593, Monday to Saturday, from 9:00 a.m. to 6:00 p.m. You can also ask in this chat for a team member to review your case.

> ⚠ Por confirmar: Horario confirmado (9:00 a 18:00). Falta confirmar si los días de atención son de lunes a sábado (como dice la landing) y si hay un correo público de atención.

### 4. ¿Dónde están ubicados? ⚠

**ES:** Calle Los Sinchis Nro. 166, Urb. Tahuantinsuyo Zona III, Independencia, Lima.

**EN — Where are you located?** Calle Los Sinchis Nro. 166, Urb. Tahuantinsuyo Zona III, Independencia, Lima.

> ⚠ Por confirmar: Confirmar si se atiende al público en esa dirección o si es solo almacén.


## Empresa

### 5. ¿Qué es SAVA?

**ES:** SAVA S.A.C. es un operador logístico de última milla nacido en Independencia, Lima Norte. Recibe los pedidos de tiendas retail como Ripley, Falabella, Zara, H&M y Temu y los reparte en todo Lima con flota propia y seguimiento en vivo con su plataforma GeoTrack. La tienda vende; SAVA entrega.

**EN — What is SAVA?** SAVA S.A.C. is a last-mile logistics operator born in Independencia, North Lima. It receives orders from retailers such as Ripley, Falabella, Zara, H&M and Temu and delivers them across Lima with its own fleet and live tracking through its GeoTrack platform. The store sells; SAVA delivers.

### 6. ¿Con qué tiendas trabajan?

**ES:** SAVA distribuye pedidos de retails como Ripley, Falabella, Zara, H&M y Temu, entre otros.

**EN — Which stores do you work with?** SAVA distributes orders from retailers such as Ripley, Falabella, Zara, H&M and Temu, among others.

### 7. ¿Qué es GeoTrack?

**ES:** GeoTrack es la plataforma propia de SAVA: muestra en vivo el estado de cada paquete desde que sale de la tienda hasta que se entrega, con foto de entrega y reportes diarios por tienda. Además usa inteligencia artificial para agrupar pedidos por zona y acortar los tiempos de reparto.

**EN — What is GeoTrack?** GeoTrack is SAVA's own platform: it shows every package's status live from the moment it leaves the store until it is delivered, with a delivery photo and daily reports per store. It also uses artificial intelligence to group orders by zone and shorten delivery times.


## Empresas

### 8. ¿Cómo funciona el recojo para tiendas?

**ES:** SAVA recoge los pedidos en la tienda o en el centro de distribución del retail, con manifiesto firmado y conteo paquete por paquete. Luego se verifican en el almacén de SAVA y se asignan a rutas por zona. Para coordinar recojos para su empresa, deje sus datos y el equipo comercial le escribe.

**EN — How does pickup work for stores?** SAVA collects orders at the retailer's store or distribution center, with a signed manifest and package-by-package count. They are then verified at SAVA's hub and assigned to routes by zone. To arrange pickups for your company, leave your details and the sales team will write to you.

### 9. ¿Cómo contrato el servicio para mi empresa?

**ES:** Cuéntenos su volumen diario de pedidos y las zonas donde reparte, y SAVA le responde con una propuesta en 24 horas. Puede dejar sus datos en este chat (nombre, empresa, correo, teléfono y volumen estimado) o en el formulario de contacto de la página.

**EN — How do I hire the service for my company?** Tell us your daily order volume and the zones you deliver to, and SAVA will reply with a proposal within 24 hours. You can leave your details in this chat (name, company, email, phone and estimated volume) or in the contact form on the website.

### 10. ¿Cuánto cuesta el servicio? ⚠

**ES:** SAVA arma una propuesta a la medida de cada empresa según su volumen diario y sus zonas, y la envía en 24 horas. Si quiere una propuesta, deje sus datos y el equipo comercial se comunica con usted.

**EN — How much does the service cost?** SAVA builds a tailored proposal for each company based on its daily volume and zones, and sends it within 24 hours. If you would like a proposal, leave your details and the sales team will contact you.

> ⚠ Por confirmar: Confirmar que no se publican tarifas al público.

### 11. ¿Tienen rutas dedicadas?

**ES:** Sí. Si una tienda necesita una zona con horario especial, SAVA arma rutas diarias dedicadas según su volumen.

**EN — Do you offer dedicated routes?** Yes. If a store needs a zone with special hours, SAVA builds dedicated daily routes based on its volume.

### 12. Portal para empresas clientes

**ES:** Las empresas clientes ingresan al portal (/portal) con su código de acceso y su clave, y confirman con un código que llega a su correo. Ahí ven el estado de sus pedidos por fecha, con su línea de tiempo, y pueden descargarlos en Excel. Se puede consultar hasta un año atrás.

**EN — Portal for business clients** Business clients log in to the portal (/portal) with their access code and password, and confirm with a code sent to their email. There they see the status of their orders by date, with their timeline, and can download them to Excel. Up to one year back can be consulted.


## Incidencias

### 13. Mi pedido no llega

**ES:** Lo primero es rastrearlo con su código para ver en qué etapa está. Si figura en ruta, el conductor está repartiendo y se ve en qué parada va. Si figura reprogramado, hubo un intento sin éxito y puede elegir una franja para el nuevo intento. Si figura entregado y usted no lo recibió, puede presentar un reclamo en el Libro de Reclamaciones o escribir al WhatsApp +51 922 507 593.

**EN — My order has not arrived** First, track it with its code to see which stage it is in. If it shows out for delivery, the driver is on the way and you can see which stop they are at. If it shows rescheduled, there was an unsuccessful attempt and you can choose a time slot for the new attempt. If it shows delivered and you did not receive it, you can file a claim in the Complaints Book or write to WhatsApp +51 922 507 593.

### 14. ¿Qué pasa si no estaba cuando vinieron?

**ES:** Si el conductor no pudo entregar, deja constancia de la visita. Luego la oficina de SAVA evalúa cada caso y decide si se hace un nuevo intento otro día o si el paquete regresa a la tienda. Desde el portal o desde este chat, verificando el pedido, puede pedir que se reprograme en una de las franjas disponibles.

**EN — What happens if I wasn't home?** If the driver could not deliver, the visit is recorded. SAVA's office then reviews each case and decides whether to make a new attempt on another day or return the package to the store. From the portal or from this chat, after verifying the order, you can ask to reschedule it in one of the available time slots.

### 15. ¿Puedo cambiar la dirección de entrega?

**ES:** SAVA no puede cambiar la dirección de entrega, porque la registra la tienda donde se hizo la compra. Para cambiarla, comuníquese con esa tienda.

**EN — Can I change the delivery address?** SAVA cannot change the delivery address, because it is registered by the store where the purchase was made. To change it, please contact that store.


## Privacidad

### 16. ¿Qué hacen con mis datos en este chat?

**ES:** Las conversaciones se usan solo para atender su consulta y mejorar el servicio. Los DNI, teléfonos y correos se guardan enmascarados, los audios se descartan apenas se transcriben y las conversaciones se borran solas después de un tiempo.

**EN — What do you do with my data in this chat?** Conversations are used only to answer your request and improve the service. DNIs, phone numbers and emails are stored masked, voice messages are discarded as soon as they are transcribed, and conversations are deleted automatically after a while.


## Rastreo

### 17. ¿Cómo rastreo mi pedido?

**ES:** Con el código de su pedido se puede consultar su estado en el portal de clientes (/portal) o en este chat. Para ver el detalle se pide verificar la identidad con los últimos 4 dígitos del DNI del destinatario. Si el pedido está en ruta, se muestra en qué parada va el conductor.

**EN — How do I track my order?** With your order code you can check its status in the client portal (/portal) or in this chat. To see the details you are asked to verify your identity with the last 4 digits of the recipient's DNI (ID). If the order is out for delivery, you can see which stop the driver is at.

### 18. ¿Por qué me piden los últimos 4 dígitos del DNI?

**ES:** Para proteger los datos del destinatario: antes de mostrar el detalle de un pedido se verifica que quien consulta lo conoce. Solo se piden los últimos 4 dígitos del DNI del destinatario y no se guardan. Sin esa verificación solo se muestra un resumen con los datos enmascarados.

**EN — Why am I asked for the last 4 digits of the DNI?** To protect the recipient's data: before showing an order's details we check that the person asking knows it. Only the last 4 digits of the recipient's DNI (ID) are requested and they are not stored. Without this verification only a summary with masked data is shown.

### 19. Me equivoqué con el DNI y quedó bloqueado

**ES:** Por seguridad, después de 3 intentos fallidos la consulta de ese pedido se bloquea por un tiempo, y cada bloqueo seguido dura más. Espere el tiempo indicado y vuelva a intentarlo con los últimos 4 dígitos del DNI del destinatario (no del comprador, si son personas distintas).

**EN — I entered the wrong DNI and it got locked** For security, after 3 failed attempts the lookup of that order is locked for a while, and each consecutive lock lasts longer. Wait for the indicated time and try again with the last 4 digits of the recipient's DNI (not the buyer's, if they are different people).

### 20. ¿Qué significa el estado de mi pedido?

**ES:** Por salir: el pedido está en el almacén de SAVA preparándose para su ruta. En ruta: el conductor ya salió y está repartiendo. Entregado: se entregó con foto de evidencia. Reprogramado: no se pudo entregar en el intento anterior y se programará un nuevo intento. Observado: el paquete está en revisión en el almacén. Cancelado: el envío se canceló.

**EN — What does my order status mean?** Getting ready: the order is at SAVA's hub being prepared for its route. Out for delivery: the driver has left and is delivering. Delivered: it was delivered with a photo as proof. Rescheduled: it could not be delivered on the previous attempt and a new attempt will be scheduled. Under review: the package is being checked at the hub. Cancelled: the shipment was cancelled.

### 21. ¿Hay prueba de la entrega?

**ES:** Sí. Cada entrega se registra con foto y confirmación en la app del conductor. Después de verificar el pedido en el portal se puede ver la foto de evidencia y quién lo recibió.

**EN — Is there proof of delivery?** Yes. Every delivery is recorded with a photo and confirmation in the driver's app. After verifying the order in the portal you can see the proof photo and who received it.

### 22. ¿Puedo recibir avisos de mi pedido?

**ES:** Sí. Después de verificar el pedido en el portal aparece un enlace para recibir por Telegram los avisos de ese pedido (por ejemplo, cuando sale a reparto o se entrega).

**EN — Can I get updates about my order?** Yes. After verifying the order in the portal, a link appears to receive that order's updates on Telegram (for example, when it is out for delivery or delivered).

### 23. ¿Quién me trae el pedido?

**ES:** Un conductor de la flota propia de SAVA. Cuando el pedido está en ruta, el portal muestra el nombre del conductor, la placa y en qué parada va, después de verificar el pedido.

**EN — Who brings my order?** A driver from SAVA's own fleet. When the order is out for delivery, the portal shows the driver's name, the plate and which stop they are at, after verifying the order.

### 24. Mi pedido antiguo ya no aparece

**ES:** Por la política de retención de datos, los pedidos muy antiguos ya no se pueden consultar: sus datos personales se retiran pasado un tiempo. Si necesita información de un pedido antiguo, comuníquese por WhatsApp al +51 922 507 593.

**EN — My old order no longer shows up** Due to the data retention policy, very old orders can no longer be looked up: their personal data is removed after some time. If you need information about an old order, contact us on WhatsApp at +51 922 507 593.

### 25. ¿Dónde encuentro el código de mi pedido?

**ES:** El código del pedido lo entrega la tienda al momento de la compra (por ejemplo, Ripley), y SAVA recibe ese mismo código, así que sirve para rastrearlo aquí. Si no lo tiene, consulte con la tienda donde compró.

**EN — Where do I find my order code?** The order code is given by the store at the time of purchase (for example, Ripley), and SAVA receives that same code, so you can use it to track the order here. If you don't have it, check with the store where you bought.


## Reclamos

### 26. ¿Cómo presento un reclamo?

**ES:** En el Libro de Reclamaciones virtual de la página principal (sección Reclamos: /#reclamos), no en el portal. Se completan los datos del consumidor, el bien contratado y el detalle de lo ocurrido. Al registrarlo se entrega un código LR para el seguimiento y llega una constancia al correo. Este chat no registra reclamos: se hacen en el Libro de Reclamaciones, según la Ley N.º 29571.

**EN — How do I file a claim?** In the virtual Complaints Book on the main website (Claims section: /#reclamos), not in the portal. You fill in the consumer's details, the contracted good and what happened. When registered you get an LR code to follow up and a receipt is sent to your email. This chat does not register claims: they are filed in the Complaints Book, under Law No. 29571.

### 27. ¿Reclamo o queja?

**ES:** Reclamo: es sobre el servicio (la entrega, el paquete, los tiempos). Queja: es sobre la atención recibida.

**EN — Claim or complaint?** Claim: about the service (the delivery, the package, the times). Complaint: about the attention received.

### 28. ¿En cuánto tiempo responden un reclamo?

**ES:** En un plazo máximo de 15 días hábiles, como exigen las normas de protección al consumidor del Perú. Con el código LR puede hacer seguimiento.

**EN — How long does it take to answer a claim?** Within 15 business days at most, as required by Peruvian consumer protection rules. You can follow up with the LR code.

### 29. Mi paquete llegó dañado o incompleto

**ES:** Lamentamos lo ocurrido. Puede registrarlo en el Libro de Reclamaciones de la página, indicando el código del pedido, para que el equipo de operaciones lo revise con la evidencia de entrega. También puede escribir al WhatsApp +51 922 507 593.

**EN — My package arrived damaged or incomplete** We are sorry about that. You can register it in the Complaints Book on the website, including the order code, so the operations team reviews it with the proof of delivery. You can also write to WhatsApp +51 922 507 593.


## Reprogramacion

### 30. ¿Cómo reprogramo la entrega?

**ES:** Rastree el pedido con su código, verifique con los últimos 4 dígitos del DNI y elija una de las franjas disponibles. La solicitud queda registrada y el equipo de SAVA la atiende. No se puede reprogramar un pedido ya entregado o cancelado.

**EN — How do I reschedule the delivery?** Track the order with its code, verify with the last 4 digits of the DNI and choose one of the available time slots. The request is registered and the SAVA team handles it. An order that was already delivered or cancelled cannot be rescheduled.

### 31. ¿Qué franjas horarias hay?

**ES:** Las franjas para reprogramar las define SAVA y pueden cambiar; se muestran al momento de reprogramar en el portal o en este chat.

**EN — Which time slots are available?** Rescheduling time slots are set by SAVA and may change; they are shown when you reschedule in the portal or in this chat.


## Servicio

### 32. ¿Cómo funciona el servicio?

**ES:** 1) Recojo: se recogen los pedidos en la tienda o el centro de distribución del retail, con manifiesto firmado y conteo paquete por paquete. 2) Verificación y ruteo: en el almacén de SAVA cada paquete se valida, se registra en GeoTrack y se asigna a una ruta por zona de Lima. 3) Reparto: la flota sale a todo Lima y el retail ve el avance en vivo, parada por parada. 4) Entrega con evidencia: se entrega al cliente final con foto y confirmación; las entregas fallidas se gestionan y reprograman, con reporte al retail.

**EN — How does the service work?** 1) Pickup: orders are collected at the retailer's store or distribution center, with a signed manifest and package-by-package count. 2) Verification and routing: at SAVA's hub every package is validated, registered in GeoTrack and assigned to a route by Lima zone. 3) Out for delivery: the fleet goes out across Lima and the retailer watches progress live, stop by stop. 4) Delivery with proof: the package is delivered to the end customer with a photo and confirmation; failed deliveries are managed and rescheduled, with a report to the retailer.

### 33. ¿Qué días reparten?

**ES:** El reparto se realiza de lunes a domingo, incluidos los feriados, en el horario regular de reparto.

**EN — Which days do you deliver?** Delivery runs Monday to Sunday, including public holidays, during regular delivery hours.

### 34. ¿Cuánto demora la entrega?

**ES:** La tienda donde se hizo la compra informa un plazo de 1 a 5 días hábiles. Desde que SAVA recibe el paquete de la tienda, lo entrega en un máximo de 3 días hábiles. Para saber en qué etapa está un pedido, lo más preciso es rastrearlo con su código: cuando está en ruta se ve en qué parada va el conductor.

**EN — How long does delivery take?** The store where the purchase was made states a delivery time of 1 to 5 business days. Once SAVA receives the package from the store, it delivers it within 3 business days at most. To know which stage an order is in, the most accurate way is to track it with its code: when it is out for delivery you can see which stop the driver is at.
