// Caché en memoria de URLs de evidencia por pedido_id (el backend no las expone en el manifiesto).
const evidenciasPorPedido = new Map<number, string>();

// Guarda la URL de evidencia de un pedido. Recibe pedidoId y url.
export function guardarEvidencia(pedidoId: number, url: string): void {
  evidenciasPorPedido.set(pedidoId, url);
}

// Devuelve la URL de evidencia cacheada. Recibe pedidoId.
export function obtenerEvidencia(pedidoId: number): string | undefined {
  return evidenciasPorPedido.get(pedidoId);
}
