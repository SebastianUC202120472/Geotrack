// Acciones de una parada: entregar con evidencia (POD) o reportar una falla.
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { marcarEstadoParada, subirEvidencia, crearReporte } from "@/api/conductor";
import { guardarEvidencia } from "@/store/evidenciaCache";
import { urlEvidencia } from "@/api/config";
import { claves } from "@/features/ruta/hooks";

// Registra una entrega con su foto. Devuelve: mutación que recibe
// { pedidoId: number, uriFoto: string }. Marca ENTREGADO, sube la evidencia y
// cachea su URL para el historial.
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

// Reporta una falla en la entrega. Devuelve: mutación que recibe
// { pedidoId, motivo, descripcion? }. Marca la parada FALLIDO y crea el reporte
// que verá el administrador.
export function useReportarFalla() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ pedidoId, motivo, descripcion }: { pedidoId: number; motivo: string; descripcion?: string }) => {
      await marcarEstadoParada(pedidoId, "FALLIDO", motivo);
      return crearReporte(pedidoId, motivo, descripcion);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: claves.manifiesto });
      qc.invalidateQueries({ queryKey: claves.rutaActiva });
      qc.invalidateQueries({ queryKey: ["mis-reportes"] });
    },
  });
}
