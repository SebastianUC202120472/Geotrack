// Hooks para entregar (POD) o reportar falla en una parada; encola si no hay red.
import { useMutation, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { marcarEstadoParada, subirEvidencia, crearReporte, subirEvidenciaReporte } from "@/api/conductor";
import { guardarEvidencia } from "@/store/evidenciaCache";
import { urlEvidencia } from "@/api/config";
import { claves } from "@/features/ruta/hooks";
import { estaOnline } from "@/hooks/useConexion";
import { encolar } from "@/store/colaSync";
import { ajustarCopia } from "@/store/rutaOffline";
import { esErrorDeRed } from "@/api/client";
import type { FotoConGps } from "@/hooks/useFotoConGps";
import type { Manifiesto, Receptor } from "@/types/api";

// Actualiza el cache del manifiesto (y su copia en el teléfono) con el nuevo estado de la parada
// (optimista). Recibe qc, pedidoId, estado.
function marcarOptimista(qc: QueryClient, pedidoId: number, estado: "ENTREGADO" | "FALLIDO"): void {
  const aplicar = (prev: Manifiesto): Manifiesto => ({
    ...prev,
    paradas: prev.paradas.map((p) => (p.pedido_id === pedidoId ? { ...p, estado_entrega: estado } : p)),
  });
  qc.setQueryData<Manifiesto>(claves.manifiesto, (prev: Manifiesto | undefined) => (prev ? aplicar(prev) : prev));
  ajustarCopia<Manifiesto>("manifiesto", aplicar);
}

// Sube la evidencia (con su GPS) y marca ENTREGADO con quién recibió; encola si no hay red.
// Recibe pedidoId, la foto tomada con la cámara y el receptor.
export function useEntregarConEvidencia() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ pedidoId, foto, receptor }: { pedidoId: number; foto: FotoConGps; receptor: Receptor }): Promise<{ encolado: boolean }> => {
      if (await estaOnline()) {
        try {
          const resultado = await subirEvidencia(pedidoId, foto.uri, foto.coords);
          await marcarEstadoParada(pedidoId, "ENTREGADO", undefined, receptor);
          const url = urlEvidencia(resultado.url_evidencia);
          if (url) guardarEvidencia(pedidoId, url);
          return { encolado: false };
        } catch (e) {
          if (!esErrorDeRed(e)) throw e;
        }
      }
      await encolar({
        tipo: "ENTREGA", pedidoId, fotoUri: foto.uri,
        latitud: foto.coords?.latitud, longitud: foto.coords?.longitud,
        receptorNombre: receptor.nombre, receptorDocumento: receptor.documento,
      });
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

// Marca FALLIDO, crea el reporte y le adjunta la foto opcional (C29-01); encola si no hay red.
// Recibe pedidoId, motivo, descripcion y foto opcionales.
export function useReportarFalla() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ pedidoId, motivo, descripcion, foto }: {
      pedidoId: number; motivo: string; descripcion?: string; foto?: FotoConGps | null;
    }): Promise<{ encolado: boolean }> => {
      if (await estaOnline()) {
        try {
          await marcarEstadoParada(pedidoId, "FALLIDO", motivo);
          const reporte = await crearReporte(pedidoId, motivo, descripcion);
          if (foto) await subirEvidenciaReporte(reporte.id, foto.uri, foto.coords);
          return { encolado: false };
        } catch (e) {
          if (!esErrorDeRed(e)) throw e;
        }
      }
      await encolar({
        tipo: "FALLIDO", pedidoId, motivo, descripcion,
        fotoUri: foto?.uri, latitud: foto?.coords?.latitud, longitud: foto?.coords?.longitud,
      });
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
