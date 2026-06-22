// Acciones de una parada: entregar con evidencia (POD) o reportar una falla.
// Offline-aware (CUS-27): si no hay conexión (o la llamada falla por red), la
// acción se ENCOLA y se actualiza el manifiesto de forma optimista; el motor de
// sync la sube al reconectar. Devuelven { encolado } para que la UI avise.
import { useMutation, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { marcarEstadoParada, subirEvidencia, crearReporte } from "@/api/conductor";
import { guardarEvidencia } from "@/store/evidenciaCache";
import { urlEvidencia } from "@/api/config";
import { claves } from "@/features/ruta/hooks";
import { estaOnline } from "@/hooks/useConexion";
import { encolar } from "@/store/colaSync";
// MINOR 3: esErrorDeRed centralizado en client (sin duplicar).
import { esErrorDeRed } from "@/api/client";
import type { Manifiesto } from "@/types/api";

// UI optimista: marca la parada como gestionada en el cache del manifiesto, para
// que la pantalla la muestre resuelta de inmediato (offline) sin tocar contadores.
function marcarOptimista(qc: QueryClient, pedidoId: number, estado: "ENTREGADO" | "FALLIDO"): void {
  qc.setQueryData<Manifiesto>(claves.manifiesto, (prev: Manifiesto | undefined) =>
    prev
      ? { ...prev, paradas: prev.paradas.map((p) => (p.pedido_id === pedidoId ? { ...p, estado_entrega: estado } : p)) }
      : prev
  );
}

// Registra una entrega con su foto. { pedidoId, uriFoto }. Online: marca ENTREGADO,
// sube la evidencia y cachea su URL. Offline/fallo de red: encola + optimista.
export function useEntregarConEvidencia() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ pedidoId, uriFoto }: { pedidoId: number; uriFoto: string }): Promise<{ encolado: boolean }> => {
      if (await estaOnline()) {
        try {
          await marcarEstadoParada(pedidoId, "ENTREGADO");
          const resultado = await subirEvidencia(pedidoId, uriFoto);
          const url = urlEvidencia(resultado.url_evidencia);
          if (url) guardarEvidencia(pedidoId, url);
          return { encolado: false };
        } catch (e) {
          if (!esErrorDeRed(e)) throw e;   // error real del servidor: propaga
          // error de red: cae a encolar
        }
      }
      await encolar({ tipo: "ENTREGA", pedidoId, fotoUri: uriFoto });
      marcarOptimista(qc, pedidoId, "ENTREGADO");
      return { encolado: true };
    },
    onSuccess: (res) => {
      // Solo invalidamos si la acción llegó al servidor; si se encoló (offline),
      // dejamos el estado optimista (un refetch traería PENDIENTE y lo borraría).
      if (!res.encolado) {
        qc.invalidateQueries({ queryKey: claves.manifiesto });
        qc.invalidateQueries({ queryKey: claves.rutaActiva });
      }
    },
  });
}

// Reporta una falla. { pedidoId, motivo, descripcion? }. Online: marca FALLIDO y
// crea el reporte. Offline/fallo de red: encola + optimista.
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
