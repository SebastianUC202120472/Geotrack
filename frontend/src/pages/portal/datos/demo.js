// Datos de DEMOSTRACIÓN del portal (Fase 1). En la Fase 2 este módulo se reemplaza
// por services/portal.js consumiendo los endpoints públicos; la forma de los datos
// ya coincide con el contrato documentado en el spec.

// Código de demo válido para el flujo de verificación (persona natural).
export const CLAVE = "DEMO-2026";

// Catálogo de estados de pedido: texto, colores de fondo/letra, color de trazo
// (línea de tiempo) y el degradado/color de barra de progreso.
export const ESTADOS = {
  EN_RUTA: { tx: "EN RUTA", bg: "#e4effc", fg: "#1b5fb3", trazo: "#2679d8", barra: "linear-gradient(90deg,#2679d8,#5db1f0)" },
  ENTREGADO: { tx: "ENTREGADO", bg: "#e3f2e8", fg: "#1e7a43", trazo: "#22a35e", barra: "linear-gradient(90deg,#2679d8,#22a35e)" },
  REPROGRAMADO: { tx: "REPROGRAMADO", bg: "#fdeedd", fg: "#b35c12", trazo: "#d97a1f", barra: "linear-gradient(90deg,#2679d8,#d97a1f)" },
  POR_SALIR: { tx: "POR SALIR", bg: "#eef2f6", fg: "#52708e", trazo: "#7288a0", barra: "#9db3c9" },
  OBSERVADO: { tx: "OBSERVADO", bg: "#fdeedd", fg: "#b35c12", trazo: "#d97a1f", barra: "linear-gradient(90deg,#2679d8,#d97a1f)" },
};

// Pedidos de ejemplo para la vista de rastreo (persona natural), uno por cada estado
// relevante de la demo: en ruta, entregado y reprogramado; cada uno con su línea de
// tiempo de eventos completa.
export const PEDIDOS = {
  "PD-2481": {
    retail: "Ripley",
    destino: "Av. Larco 812, Miraflores",
    destinoMask: "Av. L•••• 8••, Miraflores",
    dni: "7364",
    telMask: "+51 9** *** *21",
    estado: "EN_RUTA",
    etaT: "Llega hoy",
    eta: "entre 2:00 y 4:30 pm",
    conductor: "Luis Campos",
    placa: "ABX-731",
    parada: "va en la parada 12 de 28 · a 6 paradas de usted",
    pct: "62%",
    van: "62%",
    nota: "El conductor va por la parada 12 de 28, a 6 paradas de su dirección. La posición se actualiza en vivo desde GeoTrack.",
    eventos: [
      { t: "Ripley entregó su pedido a SAVA", d: "CD Villa El Salvador · 1 bulto", h: "09:12" },
      { t: "Verificado en el centro SAVA", d: "Independencia · empaque conforme", h: "11:40" },
      { t: "Salió a reparto", d: "Ruta Lima Centro 04 · conductor Luis Campos", h: "13:20" },
      { t: "En camino a su dirección", d: "Miraflores · parada 12 de 28", h: "14:05", vivo: true },
    ],
  },
  "PD-1073": {
    retail: "Falabella",
    destino: "Jr. Huiracocha 1540, Jesús María",
    destinoMask: "Jr. H•••••••• 15••, Jesús María",
    dni: "4821",
    telMask: "+51 9** *** *74",
    estado: "ENTREGADO",
    etaT: "Entregado hoy",
    eta: "a las 12:47 pm",
    recibido: "Recibido por M. Torres (DNI ***4821), en puerta principal.",
    pct: "100%",
    van: "100%",
    nota: "Ruta completada — su paquete fue entregado a las 12:47 pm con foto de evidencia.",
    eventos: [
      { t: "Falabella entregó su pedido a SAVA", d: "CD Lurín · 1 bulto", h: "08:05" },
      { t: "Verificado en el centro SAVA", d: "Independencia · empaque conforme", h: "10:22" },
      { t: "Salió a reparto", d: "Ruta Lima Centro 02", h: "11:10" },
      { t: "Entregado", d: "Recibido por M. Torres · foto registrada", h: "12:47", ok: true },
    ],
  },
  "PD-3316": {
    retail: "Zara",
    destino: "Ca. Los Nogales 233, San Isidro",
    destinoMask: "Ca. Los N•••••• 2••, San Isidro",
    dni: "5502",
    telMask: "+51 9** *** *56",
    estado: "REPROGRAMADO",
    etaT: "Necesita nueva fecha",
    eta: "— elija abajo cuándo volvemos",
    motivo: "Nadie respondió en la dirección en el primer intento (ayer, 4:32 pm)",
    pct: "48%",
    van: "0%",
    nota: "El paquete está seguro en el centro SAVA, listo para volver a salir en la fecha que usted elija.",
    eventos: [
      { t: "Zara entregó su pedido a SAVA", d: "Tienda Jockey Plaza · 1 bulto", h: "Ayer 10:40 am" },
      { t: "Salió a reparto", d: "Ruta Lima Centro 03", h: "Ayer 1:15 pm" },
      { t: "Intento de entrega sin éxito", d: "Nadie respondió · se dejó constancia de visita", h: "Ayer 4:32 pm", alerta: true },
      { t: "De vuelta en el centro SAVA", d: "A la espera de una nueva fecha", h: "Ayer 7:05 pm" },
    ],
  },
};

// Empresas clientes con acceso al panel (login por código de empresa + clave).
export const EMPRESAS = {
  "RIPLEY-24": { nombre: "Ripley", ini: "R" },
  "FALABELLA-24": { nombre: "Falabella", ini: "F" },
  "ZARA-24": { nombre: "Zara", ini: "Z" },
};

// Filas de la tabla de pedidos por empresa (panel empresa): [código, cliente,
// dirección, distrito, estado, hora, detalle opcional de parada/motivo].
export const FILAS = {
  "RIPLEY-24": [
    ["PD-2450", "R. Paredes", "Av. Brasil 1120", "Jesús María", "ENTREGADO", "10:12"],
    ["PD-2453", "C. Núñez", "Ca. Schell 340", "Miraflores", "ENTREGADO", "10:58"],
    ["PD-2461", "M. Salas", "Av. Aviación 2890", "San Borja", "ENTREGADO", "11:24"],
    ["PD-2466", "J. Rivas", "Jr. Camaná 615", "Cercado", "ENTREGADO", "11:51"],
    ["PD-2470", "L. Chávez", "Av. Arenales 990", "Lince", "ENTREGADO", "12:16"],
    ["PD-2474", "P. Gamarra", "Av. Pardo 610", "Miraflores", "ENTREGADO", "12:40"],
    ["PD-2477", "S. Rojas", "Ca. Las Begonias 415", "San Isidro", "ENTREGADO", "13:05"],
    ["PD-2481", "A. Quispe", "Av. Larco 812", "Miraflores", "EN_RUTA", "14:05", "Parada 12 de 28"],
    ["PD-2483", "V. Mendoza", "Av. Salaverry 2255", "Jesús María", "EN_RUTA", "14:05", "Parada 14 de 28"],
    ["PD-2488", "E. Castro", "Jr. Manuel Segura 105", "Lince", "EN_RUTA", "14:05", "Parada 17 de 28"],
    ["PD-2492", "D. Herrera", "Av. Javier Prado Este 1420", "San Isidro", "POR_SALIR", "—", "Sale en el bloque de 3:30 pm"],
    ["PD-2495", "K. Flores", "Ca. Los Pinos 220", "Miraflores", "POR_SALIR", "—", "Sale en el bloque de 3:30 pm"],
    ["PD-2497", "G. Torres", "Av. Petit Thouars 3300", "San Isidro", "OBSERVADO", "13:42", "Dirección incompleta"],
    ["PD-2499", "N. Vargas", "Jr. Risso 180", "Lince", "OBSERVADO", "13:55", "Cliente pidió cambio de fecha"],
  ],
  "FALABELLA-24": [
    ["PD-1058", "T. Aguilar", "Av. Universitaria 1801", "San Miguel", "ENTREGADO", "09:48"],
    ["PD-1062", "B. León", "Av. La Marina 2355", "San Miguel", "ENTREGADO", "10:15"],
    ["PD-1067", "F. Palacios", "Av. Sucre 545", "Pueblo Libre", "ENTREGADO", "10:52"],
    ["PD-1073", "M. Torres", "Jr. Huiracocha 1540", "Jesús María", "ENTREGADO", "12:47"],
    ["PD-1078", "H. Medina", "Av. Bolívar 880", "Pueblo Libre", "ENTREGADO", "13:10"],
    ["PD-1081", "I. Campos", "Av. Brasil 3420", "Magdalena", "EN_RUTA", "14:02", "Parada 9 de 24"],
    ["PD-1084", "O. Silva", "Jr. Castilla 720", "Magdalena", "EN_RUTA", "14:02", "Parada 11 de 24"],
    ["PD-1088", "U. Ramos", "Av. Elmer Faucett 310", "Callao", "POR_SALIR", "—", "Sale en el bloque de 4:00 pm"],
    ["PD-1090", "Y. Paz", "Av. Óscar Benavides 3550", "Bellavista", "POR_SALIR", "—", "Sale en el bloque de 4:00 pm"],
    ["PD-1093", "W. Soto", "Ca. Colina 145", "La Perla", "POR_SALIR", "—", "Sale en el bloque de 4:00 pm"],
    ["PD-1095", "Z. Reyes", "Av. Sáenz Peña 1210", "Callao", "OBSERVADO", "13:28", "Dirección sin numeración clara"],
  ],
  "ZARA-24": [
    ["PD-3302", "C. Ibarra", "Av. Primavera 1650", "Surco", "ENTREGADO", "10:34"],
    ["PD-3305", "R. Fuentes", "Av. Caminos del Inca 390", "Surco", "ENTREGADO", "11:02"],
    ["PD-3309", "L. Ponce", "Av. El Polo 740", "Surco", "ENTREGADO", "11:47"],
    ["PD-3312", "A. Delgado", "Av. Angamos Este 2681", "Surquillo", "ENTREGADO", "12:20"],
    ["PD-3316", "S. Barrios", "Ca. Los Nogales 233", "San Isidro", "REPROGRAMADO", "—", "Reintento según fecha del cliente"],
    ["PD-3320", "M. Cornejo", "Av. Tomás Marsano 1102", "Surquillo", "EN_RUTA", "14:08", "Parada 7 de 19"],
    ["PD-3324", "J. Espino", "Av. Ayacucho 660", "Surco", "EN_RUTA", "14:08", "Parada 10 de 19"],
    ["PD-3327", "D. Lazo", "Jr. Monterrey 281", "Surco", "POR_SALIR", "—", "Sale en el bloque de 3:45 pm"],
    ["PD-3330", "P. Vega", "Av. Benavides 4890", "Surco", "POR_SALIR", "—", "Sale en el bloque de 3:45 pm"],
  ],
};

// Opciones de franja horaria ofrecidas al reprogramar una entrega.
export const OPCIONES = ["Mañana · 9 am – 1 pm", "Mañana · 2 pm – 6 pm", "Sábado · 9 am – 1 pm"];
