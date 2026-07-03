// Convierte una ruta interna del panel (guardada en la BD sin prefijo, ej. "/bandeja")
// a su ruta real bajo /panel. Input: ruta string o null.
export function haciaPanel(ruta) {
  if (!ruta) return "/panel";
  return ruta.startsWith("/panel") ? ruta : `/panel${ruta}`;
}
