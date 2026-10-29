// Constantes compartidas por las pantallas del modulo de capacidad (Idea 3).

// Tipos de vehiculo que acepta el backend, con su etiqueta para la interfaz.
export const TIPOS_VEHICULO = [
  { valor: "pickup", etiqueta: "Pick-up" },
  { valor: "furgoneta", etiqueta: "Furgoneta" },
  { valor: "van", etiqueta: "Van / Combi" },
  { valor: "suv", etiqueta: "SUV" },
  { valor: "sedan", etiqueta: "Sedan" },
  { valor: "hatchback", etiqueta: "Hatchback" },
  { valor: "camion_ligero", etiqueta: "Camion ligero" },
  { valor: "camion_mediano", etiqueta: "Camion mediano" },
  { valor: "camion_pesado", etiqueta: "Camion pesado" },
];

// Diccionario tipo -> etiqueta para tablas y badges.
export const ETIQUETA_TIPO = Object.fromEntries(
  TIPOS_VEHICULO.map((tipo) => [tipo.valor, tipo.etiqueta]),
);

// Estados de pedido que la calculadora puede planificar.
export const ESTADOS_PLANIFICABLES = [
  { valor: "", etiqueta: "Todos los planificables" },
  { valor: "LISTO_PARA_ENVIO", etiqueta: "Listo para envio" },
  { valor: "ASIGNADO", etiqueta: "Asignado" },
  { valor: "POR_RECOGER", etiqueta: "Por recoger" },
];