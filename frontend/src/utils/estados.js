// Etiquetas y helpers de estado de pedido, centralizados para reusar en badges,
// filtros y tablas sin acoplarlos a un componente (evita el warning de react-refresh
// "only-export-components" al compartir funciones desde un archivo de componentes).

// Estado -> etiqueta legible (para los que no se ven bien con el auto-formato).
// El resto usa estado.replaceAll("_"," ").toLowerCase() (+ capitalize en el badge).
export const ETIQUETAS_ESTADO = {
  POR_RECOGER: "Por recoger",
  OBSERVADO: "Observado",
  LISTO_PARA_ENVIO: "Listo para envío",
  GEOCODIFICACION_FALLIDA: "Sin ubicar",
};

// Devuelve el texto legible de un estado (usado en badges, filtros y tablas).
// Entrada: el código de estado (string). Salida: etiqueta amigable en español.
export function etiquetaEstado(estado) {
  if (!estado) return "—";
  return ETIQUETAS_ESTADO[estado] || estado.replaceAll("_", " ").toLowerCase();
}
