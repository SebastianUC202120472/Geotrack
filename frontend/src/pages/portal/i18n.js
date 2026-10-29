// Inglés del portal de clientes (EX-18). El diccionario va por el texto en español: t("Rastrear")
// devuelve "Track" en inglés y el mismo texto si no hay traducción. Incluye los textos fijos que
// manda el backend (estado, nota, eventos de la línea de tiempo y motivos de rechazo).
import { createContext, useContext } from "react";

export const EN = {
  // Cabecera, selector y pie
  "PORTAL DE CLIENTES": "CUSTOMER PORTAL",
  "← Volver a sava.pe": "← Back to sava.pe",
  "Soy trabajador · GeoTrack ↗": "I work here · GeoTrack ↗",
  "Seguimiento en vivo · datos de GeoTrack": "Live tracking · GeoTrack data",
  "¿Dónde está mi pedido?": "Where is my order?",
  "Elija su perfil para seguir sus entregas en tiempo real. Sus datos están protegidos: cada consulta se verifica y cada acceso queda registrado.":
    "Choose your profile to follow your deliveries in real time. Your data is protected: every lookup is verified and every access is logged.",
  "PERSONA NATURAL": "INDIVIDUAL",
  "Sigo mi pedido": "Track my order",
  "Trazabilidad con su código + verificación de identidad": "Tracking with your code + identity check",
  "EMPRESA / RETAIL": "BUSINESS / RETAIL",
  "Estado de mis pedidos": "My orders' status",
  "Acceso con credenciales y verificación en dos pasos": "Sign in with credentials and two-step verification",
  "Portal de clientes · datos en vivo desde GeoTrack": "Customer portal · live data from GeoTrack",
  "Reclamos": "Complaints",
  "Portal de clientes — SAVA": "Customer portal — SAVA",
  // Búsqueda y verificación
  "Código de seguimiento": "Tracking code",
  "Código de seguimiento · ej. PD-001 o SGF-DEMO-01": "Tracking code · e.g. PD-001 or SGF-DEMO-01",
  "Buscando…": "Searching…",
  "Rastrear": "Track",
  "Buscando su paquete en GeoTrack…": "Looking for your package in GeoTrack…",
  "No encontramos el código": "We could not find the code",
  "Revise que esté igual que en el correo o SMS de su tienda (con guion, ej. SGF-DEMO-01 o PD-001). Si acaba de recibir la confirmación, el código puede tardar unos minutos en activarse.":
    "Check that it matches the email or text from your store (with the hyphen, e.g. SGF-DEMO-01 or PD-001). If you just got the confirmation, the code may take a few minutes to become active.",
  "Su código está en el correo o SMS de su tienda": "Your code is in the email or text from your store",
  "Cuando su tienda confirma su envío con SAVA, le llega un código. Sirve el de la tienda (como SGF-DEMO-01) o el de SAVA (como PD-001). Por su seguridad, además del código le pediremos verificar su identidad.":
    "When your store confirms the shipment with SAVA, you get a code. Either the store's (like SGF-DEMO-01) or SAVA's (like PD-001) works. For your security, besides the code we will ask you to verify your identity.",
  "pero no podemos verificar su identidad en línea": "but we cannot verify your identity online",
  "Encontramos el pedido": "We found the order",
  "Su tienda no registró un documento para este envío, así que por seguridad no podemos mostrar el detalle aquí. Escríbanos con su código y le damos el estado:":
    "Your store did not register an ID for this shipment, so for security we cannot show the details here. Write to us with your code and we will tell you the status:",
  "Estado actual:": "Current status:",
  "destino": "destination",
  "Verifique que el pedido es suyo para ver el detalle": "Verify the order is yours to see the details",
  "Por su seguridad, la dirección y los datos completos solo se muestran al destinatario. Ingrese los últimos 4 dígitos del DNI del destinatario registrado en el pedido.":
    "For your security, the address and full details are only shown to the recipient. Enter the last 4 digits of the recipient's ID (DNI) registered on the order.",
  "Últimos 4 dígitos del DNI": "Last 4 digits of the ID (DNI)",
  "Verificar": "Verify",
  "Código por SMS (disponible próximamente)": "Code by text message (coming soon)",
  "Ingrese el DNI del destinatario que figura en el pedido": "Enter the recipient's ID shown on the order",
  "Dato incorrecto · intentos restantes antes del bloqueo temporal:": "Incorrect · attempts left before a temporary lock:",
  "Demasiados intentos fallidos. Por su seguridad, espere": "Too many failed attempts. For your security, wait",
  "para volver a intentar. Cada nuevo bloqueo dura más.": "before trying again. Each new lock lasts longer.",
  "Identidad verificada — datos desbloqueados": "Identity verified — details unlocked",
  "Demasiados intentos — acceso pausado": "Too many attempts — access paused",
  "Identidad verificada": "Identity verified",
  "Cerrar y proteger datos": "Close and protect my data",
  // Detalle
  "PEDIDO": "ORDER",
  "de": "from",
  "Recibido": "Received",
  "Verificado": "Verified",
  "Reprogramado": "Rescheduled",
  "En ruta": "On the way",
  "Entregado": "Delivered",
  "EN RUTA": "ON THE WAY",
  "ENTREGADO": "DELIVERED",
  "REPROGRAMADO": "RESCHEDULED",
  "POR SALIR": "READY TO GO",
  "OBSERVADO": "UNDER REVIEW",
  "CANCELADO": "CANCELLED",
  "Recorrido de hoy": "Today's route",
  "Mapa del recorrido del pedido": "Map of the order's route",
  "Centro SAVA": "SAVA hub",
  "Su dirección": "Your address",
  "Línea de tiempo": "Timeline",
  "· su repartidor": "· your courier",
  "Camioneta placa": "Van plate",
  "EN VIVO": "LIVE",
  "✓ Entrega confirmada": "✓ Delivery confirmed",
  "El conductor registró la evidencia en GeoTrack al momento de entregar. Solo el destinatario verificado puede verla.":
    "The driver recorded the proof in GeoTrack at the moment of delivery. Only the verified recipient can see it.",
  "Foto de entrega (POD)": "Delivery photo (POD)",
  "Entregado en la dirección de destino.": "Delivered at the destination address.",
  "Recibido por": "Received by",
  "va en la parada": "is at stop",
  // Textos fijos del backend
  "Llega hoy": "Arrives today",
  "Necesita nueva fecha": "Needs a new date",
  "Por salir": "Ready to go",
  "En gestion": "Being handled",
  "Cancelado": "Cancelled",
  "En proceso": "In progress",
  "Su pedido va en camino. La posicion se actualiza desde GeoTrack.": "Your order is on its way. The position updates from GeoTrack.",
  "Ruta completada — su paquete fue entregado con evidencia.": "Route completed — your package was delivered with proof.",
  "El paquete esta seguro en el centro SAVA, listo para volver a salir en la fecha que elija.":
    "The package is safe at the SAVA hub, ready to go out again on the date you choose.",
  "Su pedido esta preparado y saldra a reparto en el proximo bloque.": "Your order is ready and will go out for delivery in the next round.",
  "Su pedido tiene una incidencia en gestion por el equipo SAVA.": "Your order has an issue being handled by the SAVA team.",
  "Este pedido fue cancelado. Contacte a su tienda para mas informacion.": "This order was cancelled. Contact your store for more information.",
  "Pedido recibido por SAVA": "Order received by SAVA",
  "Verificado en el centro SAVA": "Checked at the SAVA hub",
  "empaque conforme": "packaging OK",
  "Programado para reparto": "Scheduled for delivery",
  "En camino a su direccion": "On the way to your address",
  "evidencia registrada": "proof recorded",
  "Intento de entrega sin exito": "Unsuccessful delivery attempt",
  "se dejo constancia de visita": "a visit notice was left",
  "Incidencia registrada": "Issue recorded",
  "en gestion por el equipo SAVA": "being handled by the SAVA team",
  "Pedido cancelado": "Order cancelled",
  "Verificando direccion de entrega": "Checking the delivery address",
  "Actualizacion del envio": "Shipment update",
  "No se pudo entregar en el intento anterior": "It could not be delivered on the previous attempt",
  "Cliente ausente": "Recipient not home",
  "Dirección incorrecta": "Wrong address",
  "Pedido rechazado": "Order refused",
  "Zona inaccesible": "Area not accessible",
  "Domicilio cerrado": "Nobody at the address",
  "Otro": "Other",
  // Reprogramación
  "Necesitamos una nueva fecha": "We need a new date",
  "¿No estará para recibirlo?": "Won't be home to receive it?",
  "Elija cuándo prefiere que volvamos; la central revisará su solicitud.": "Choose when you would like us to come back; our team will review your request.",
  "Puede pedir otra franja de entrega antes de la visita. La central revisará su solicitud y le confirmaremos.":
    "You can ask for another delivery window before the visit. Our team will review your request and confirm.",
  "Solicitud recibida — pidió": "Request received — you asked for",
  "La revisaremos y le confirmaremos la nueva visita.": "We will review it and confirm the new visit.",
  "Solicitud recibida:": "Request received:",
  "Está en revisión por la central.": "Our team is reviewing it.",
  "Elegir otra franja": "Choose another window",
  "Solicitud aceptada — su pedido saldrá": "Request accepted — your order will go out",
  "No pudimos atender la franja": "We could not take the window",
  "Elija otra o comuníquese con su tienda.": "Choose another one or contact your store.",
  "Enviar solicitud:": "Send request:",
  "Solicitud recibida — le confirmaremos la nueva visita": "Request received — we will confirm the new visit",
  "No se pudo registrar la solicitud — intente de nuevo": "The request could not be saved — please try again",
  "Mañana": "Tomorrow",
  "Sábado": "Saturday",
  // Ayuda de la demostración
  "Rastrear con el código de SAVA": "Track with the SAVA code",
  "Rastrear con el código de la tienda": "Track with the store code",
};

// Crea la función t para un idioma. Recibe "es" o "en".
export function crearT(lang) {
  return (texto) => (lang === "en" && EN[texto]) || texto;
}

// Franjas configuradas por SAVA ("Mañana · 9 am – 1 pm"): se traducen por partes. Recibe la franja y t.
export function traducirFranja(franja, t) {
  return (franja || "").split(" · ").map((parte) => t(parte)).join(" · ");
}

// "Recibido por Ana Pérez · Doc. ****912." y "va en la parada 3 de 10" vienen del backend con datos:
// se traduce solo la parte fija. Recibe el texto y t.
export function traducirDinamico(texto, t) {
  if (!texto) return texto;
  return texto
    .replace(/^Recibido por /, `${t("Recibido por")} `)
    .replace(/^va en la parada (\d+) de (\d+)$/, (_, a, b) => `${t("va en la parada")} ${a} ${t("de") === "from" ? "of" : "de"} ${b}`);
}

export const IdiomaPortal = createContext({ lang: "es", t: (texto) => texto });

// Hook con el idioma y la función t del portal. Sin parámetros.
export const useIdioma = () => useContext(IdiomaPortal);
