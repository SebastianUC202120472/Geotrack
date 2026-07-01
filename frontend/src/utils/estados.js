// Etiquetas y helpers de estado de pedido, separados de componentes para evitar warnings de react-refresh.
export const ETIQUETAS_ESTADO = {
  POR_RECOGER: "Por recoger",
  OBSERVADO: "Observado",
  LISTO_PARA_ENVIO: "Listo para envío",
  GEOCODIFICACION_FALLIDA: "Sin ubicar",
};

// Devuelve la etiqueta legible de un estado. Recibe el codigo de estado (string).
export function etiquetaEstado(estado) {
  if (!estado) return "—";
  return ETIQUETAS_ESTADO[estado] || estado.replaceAll("_", " ").toLowerCase();
}
