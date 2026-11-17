# Hallazgos del núcleo detectados durante la Idea 2

**Para:** gerente del proyecto · **De:** responsable de la Idea 2 (asistente de atención al cliente)
**Rama:** `feature/asistente-atencion-cliente` · **Fecha:** 17/11/2026

Estos puntos se encontraron al revisar el código del núcleo mientras se diseñaba el asistente de atención. **No se corrigió ninguno**: según las reglas comunes, el núcleo no se modifica desde un módulo. Cada uno trae una propuesta de solución para que el gerente decida.

| # | Hallazgo | Severidad | Afecta a la Idea 2 |
|---|---|---|---|
| 1 | El backend publica el puerto 8000 hacia afuera | Alta | Sí, indirectamente |
| 2 | El limitador confía en `X-Real-IP` venga de quien venga | Alta (junto con el 1) | Sí |
| 3 | `POST /portal/pedidos/{codigo}/reprogramar` no tiene límite de peticiones | Media | Sí |
| 4 | No existe una página de política de privacidad (el enlace del footer va a `#`) | Media (legal) | Sí |

---

## 1. El backend publica el puerto 8000 hacia afuera

**Dónde:** `docker-compose.yml`, servicio `backend`, línea `- "8000:8000"`.

**Qué pasa:** además de llegar al backend a través de Nginx (puerto 8080), cualquiera que alcance el servidor puede llamarlo directo en el puerto 8000. Al saltarse Nginx, también se saltan sus cabeceras (`X-Real-IP`, límites de tamaño, `proxy_read_timeout`).

**Riesgo:** combinado con el hallazgo 2, permite falsificar la IP y saltarse los límites por IP de los endpoints públicos del portal: verificación por DNI, login de empresa, contacto y reclamos.

**Propuesta:** en producción, quitar `ports` del backend o publicarlo solo en local (`"127.0.0.1:8000:8000"`) y dejar Nginx como única puerta de entrada. Si el equipo necesita el puerto para desarrollar, moverlo a un `docker-compose.override.yml` que no se use en producción.

## 2. El limitador confía en `X-Real-IP` venga de quien venga

**Dónde:** `backend/app/core/rate_limit.py`, función `_ip_cliente`.

**Qué pasa:** la IP que cuenta el limitador se toma de la cabecera `X-Real-IP` si trae una IP válida, sin comprobar que la petición venga de Nginx. Detrás de Nginx es correcto, porque Nginx sobrescribe esa cabecera. Pero si se llega directo al backend (hallazgo 1), el cliente puede mandar una IP distinta en cada petición.

**Riesgo:** los límites públicos (`limite_publico`) quedan sin efecto para un atacante que llegue directo al backend. Por ejemplo, la verificación por DNI de 10 por minuto por IP se puede repetir sin límite cambiando la cabecera. El bloqueo progresivo por pedido (`verificacion_portal_service`) sigue protegiendo los 4 dígitos, pero los demás endpoints quedan expuestos.

**Propuesta:** aceptar `X-Real-IP` solo cuando la petición venga de una red de confianza (la red interna de Docker, configurable, por ejemplo `PROXIES_DE_CONFIANZA=172.16.0.0/12`); en cualquier otro caso, usar `request.client.host`. Con el hallazgo 1 resuelto el riesgo baja mucho, pero conviene corregir los dos.

**Relación con la Idea 2:** el asistente de atención llama al portal desde su propio contenedor. Si no reenviara nada, todos los visitantes del chat compartirían la IP del contenedor y un solo límite de 10 verificaciones por minuto para todo el sitio. Por eso, en la semana 14 el servicio reenviará al backend el `X-Real-IP` del visitante, que recibe de Nginx. Eso depende del comportamiento actual de `_ip_cliente`: **si se corrige el hallazgo 2, la red interna de Docker tiene que figurar entre las de confianza**, o el chat volverá a compartir un único límite.

## 3. `reprogramar` no tiene límite de peticiones

**Dónde:** `backend/app/api/portal.py`, `POST /portal/pedidos/{codigo}/reprogramar`, que llama a `portal_service.registrar_reprogramacion`.

**Qué pasa:** el endpoint exige el token de persona (15 minutos), pero no tiene `limite_publico`. Cada llamada crea una solicitud de reprogramación nueva y una notificación en la campana del panel.

**Riesgo:** quien verifica un pedido una vez puede, durante los 15 minutos del token, mandar cientos de solicitudes. Eso llena la tabla de reprogramaciones y la campana del administrador (denegación de servicio sobre la atención y ruido para el operador).

**Propuesta:** agregar `dependencies=[Depends(limite_publico(5, 60))]` y, de preferencia, no crear una solicitud nueva si ya hay una PENDIENTE para el mismo pedido (actualizar la franja de la existente). La Idea 2 pondrá su propio límite de reprogramaciones por conversación, pero eso no protege al endpoint si se llama directo.

## 4. No existe una página de política de privacidad

**Dónde:** `frontend/src/pages/landing/secciones/FooterLanding.jsx`: los enlaces «Política de privacidad» y «Términos del servicio» apuntan a `#`.

**Qué pasa:** el sitio no publica su política de privacidad. La Ley 29733 y su Reglamento piden informar, antes de recoger datos, quién es el responsable, para qué se usan los datos, a quién se transfieren, cuánto tiempo se conservan y cómo ejercer los derechos ARCO. Esto ya aplica hoy a los formularios de contacto y de reclamos, no solo al chat.

**Relación con la Idea 2:** el aviso del chat (`atencion/docs/aviso_privacidad_borrador.md`) cubre lo propio del chat, pero no puede enlazar a una política general porque no existe (el campo `enlace_politica` queda vacío). Faltan además datos que solo puede dar la empresa: RUC, inscripción del banco de datos ante la ANPD y el correo para los derechos ARCO.

**Propuesta:** publicar la política de privacidad (y los términos) en una ruta del sitio, por ejemplo `/privacidad`, validada por asesoría legal. Cuando exista, se pone en el aviso del chat sin tocar código: basta con editar `enlace_politica` en `app/conocimiento/aviso_privacidad.json`.
