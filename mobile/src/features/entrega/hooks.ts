// Hooks para entregar (POD) o reportar falla en una parada; encola si no hay red.
import { useMutation, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { marcarEstadoParada, subirEvidencia, crearReporte } from "@/api/conductor";
import { guardarEvidencia } from "@/store/evidenciaCache";
import { urlEvidencia } from "@/api/config";
import { claves } from "@/features/ruta/hooks";
import { estaOnline } from "@/hooks/useConexion";
import { encolar } from "@/store/colaSync";
import { esErrorDeRed } from "@/api/client";
import type { Manifiesto } from "@/types/api";

// Actualiza el cache del manifiesto con el nuevo estado de la parada (optimista). Recibe qc, pedidoId, estado.
function marcarOptimista(qc: QueryClient, pedidoId: number, estado: "ENTREGADO" | "FALLIDO"): void {
  qc.setQueryData<Manifiesto>(claves.manifiesto, (prev: Manifiesto | undefined) =>
    prev
      ? { ...prev, paradas: prev.paradas.map((p) => (p.pedido_id === pedidoId ? { ...p, estado_entrega: estado } : p)) }
      : prev
  );
}

// Sube la evidencia y marca ENTREGADO; encola si no hay red. Recibe pedidoId y uriFoto.
export function useEntregarConEvidencia() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ pedidoId, uriFoto }: { pedidoId: number; uriFoto: string }): Promise<{ encolado: boolean }> => {
      if (await estaOnline()) {
        try {
          const resultado = await subirEvidencia(pedidoId, uriFoto);
          await marcarEstadoParada(pedidoId, "ENTREGADO");
          const url = urlEvidencia(resultado.url_evidencia);
          if (url) guardarEvidencia(pedidoId, url);
          return { encolado: false };
        } catch (e) {
          if (!esErrorDeRed(e)) throw e;
        }
      }
      await encolar({ tipo: "ENTREGA", pedidoId, fotoUri: uriFoto });
      marcarOptimista(qc, pedidoId, "ENTREGADO");
      return { encolado: true };
    },
    onSuccess: (res) => {
      if (!res.encolado) {
        qc.invalidateQueries({ queryKey: claves.manifiesto });
        qc.invalidateQueries({ queryKey: claves.rutaActiva });
      }
    },
  });
}

// Marca FALLIDO y crea el reporte; encola si no hay red. Recibe pedidoId, motivo y descripcion opcional.
export function useReportarFalla() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ pedidoId, motivo, descripcion }: { pedidoId: number; motivo: string; descripcion?: string }): Promise<{ encolado: boolean }> => {
      if (await estaOnline()) {
        try {
          await marcarEstadoParada(pedidoId, "FALLIDO", motivo);
          await crearReporte(pedidoId, motivo, descripcion);
          return { encolado: false };
        } catch (e) {
          if (!esErrorDeRed(e)) throw e;
        }
      }
      await encolar({ tipo: "FALLIDO", pedidoId, motivo, descripcion });
      marcarOptimista(qc, pedidoId, "FALLIDO");
      return { encolado: true };
    },
    onSuccess: (res) => {
      if (!res.encolado) {
        qc.invalidateQueries({ queryKey: claves.manifiesto });
        qc.invalidateQueries({ queryKey: claves.rutaActiva });
        qc.invalidateQueries({ queryKey: claves.misReportes });
      }
    },
  });
}
