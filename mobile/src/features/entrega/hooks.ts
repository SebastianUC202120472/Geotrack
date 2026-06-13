// Acción de entrega: marca la parada como ENTREGADO y sube la foto de evidencia
// (POD). Maneja el orden de las dos llamadas y refresca la ruta al terminar.
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { marcarEstadoParada, subirEvidencia } from "@/api/conductor";
import { guardarEvidencia } from "@/store/evidenciaCache";
import { urlEvidencia } from "@/api/config";
import { claves } from "@/features/ruta/hooks";

// Registra una entrega con su foto. Devuelve: mutación que recibe
// { pedidoId: number, uriFoto: string }. Primero marca ENTREGADO y luego sube
// la evidencia; cachea la URL para el historial.
export function useEntregarConEvidencia() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ pedidoId, uriFoto }: { pedidoId: number; uriFoto: string }) => {
      await marcarEstadoParada(pedidoId, "ENTREGADO");
      const resultado = await subirEvidencia(pedidoId, uriFoto);
      const url = urlEvidencia(resultado.url_evidencia);
      if (url) guardarEvidencia(pedidoId, url);
      return resultado;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: claves.manifiesto });
      qc.invalidateQueries({ queryKey: claves.rutaActiva });
    },
  });
}
