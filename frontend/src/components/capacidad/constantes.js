
/**
 * Constantes compartidas del módulo de capacidad.
 *
 * Proyecto: GeoTrack
 * Módulo: Idea 3 - Catálogo de vehículos y capacidad
 * Iteración: Semanas 9 y 10
 *
 * Este archivo contiene únicamente constantes.
 * No realiza modificaciones en el núcleo del sistema.
 */

// ============================================================
// TIPOS DE VEHÍCULOS
// ============================================================

/**
 * Tipos de vehículos que acepta el backend.
 *
 * Los valores deben coincidir exactamente con
 * TipoVehiculoEnum de app/schemas/capacidad.py.
 */
export const TIPOS_VEHICULO = [
  {
    valor: "pickup",
    etiqueta: "Pick-up",
  },
  {
    valor: "furgoneta",
    etiqueta: "Furgoneta",
  },
  {
    valor: "van",
    etiqueta: "Van / Combi",
  },
  {
    valor: "suv",
    etiqueta: "SUV",
  },
  {
    valor: "sedan",
    etiqueta: "Sedán",
  },
  {
    valor: "hatchback",
    etiqueta: "Hatchback",
  },
  {
    valor: "camion_ligero",
    etiqueta: "Camión ligero",
  },
  {
    valor: "camion_mediano",
    etiqueta: "Camión mediano",
  },
  {
    valor: "camion_pesado",
    etiqueta: "Camión pesado",
  },
];

// ============================================================
// ETIQUETAS DE TIPOS DE VEHÍCULOS
// ============================================================

/**
 * Convierte el código de un tipo de vehículo
 * en una etiqueta legible para el usuario.
 *
 * Ejemplo:
 * ETIQUETA_TIPO["camion_ligero"]
 * Resultado: "Camión ligero"
 */
export const ETIQUETA_TIPO = Object.fromEntries(
  TIPOS_VEHICULO.map((tipo) => [
    tipo.valor,
    tipo.etiqueta,
  ]),
);

// ============================================================
// ESTADOS DE PEDIDOS PLANIFICABLES
// ============================================================

/**
 * Estados permitidos para nuevos despachos.
 *
 * Los pedidos ASIGNADO o EN_RUTA no deben
 * incorporarse nuevamente en otra planificación.
 *
 * La opción vacía representa todos los pedidos
 * con estado LISTO_PARA_ENVIO.
 */
export const ESTADOS_PLANIFICABLES = [
  {
    valor: "",
    etiqueta: "Todos los pedidos listos",
  },
  {
    valor: "LISTO_PARA_ENVIO",
    etiqueta: "Listo para envío",
  },
];
