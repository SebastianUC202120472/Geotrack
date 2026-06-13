// Caché en memoria de las evidencias subidas en esta sesión, indexadas por
// pedido_id. El manifiesto del backend no incluye la url_evidencia, así que la
// guardamos aquí al subirla para poder mostrarla en el Historial.
// TODO: cuando el backend exponga la evidencia en el manifiesto/historial del
//       conductor, leerla de ahí en vez de esta caché local.
const evidenciasPorPedido = new Map<number, string>();

// Guarda la URL de evidencia de un pedido. Recibe: pedidoId (number), url (string).
export function guardarEvidencia(pedidoId: number, url: string): void {
  evidenciasPorPedido.set(pedidoId, url);
}

// Lee la URL de evidencia cacheada. Recibe: pedidoId (number).
// Devuelve: la URL o undefined si no se subió en esta sesión.
export function obtenerEvidencia(pedidoId: number): string | undefined {
  return evidenciasPorPedido.get(pedidoId);
}
