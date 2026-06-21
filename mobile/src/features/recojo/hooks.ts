// Hooks de React Query para la ruta de RECOJO del conductor: manifiesto, iniciar
// (optimizar) y registrar la recepción condicionada (CUS-12).
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { obtenerManifiestoRecojo, optimizarRecojo, registrarRecepcion } from "@/api/conductor";
import { claves as clavesRuta } from "@/features/ruta/hooks";
import type { Coordenadas } from "@/types/api";

export const clavesRecojo = { manifiesto: ["manifiesto-recojo"] as const };

const INTERVALO = 10_000;
const sinReintentarEn404 = (intentos: number, error: unknown): boolean => {
  const status = (error as { response?: { status?: number } })?.response?.status;
  if (status === 404) return false;
  return intentos < 2;
};

// Manifiesto de la ruta de recojo activa. Devuelve: query de ManifiestoRecojo.
export function useManifiestoRecojo() {
  return useQuery({ queryKey: clavesRecojo.manifiesto, queryFn: obtenerManifiestoRecojo, retry: sinReintentarEn404, refetchInterval: INTERVALO, refetchOnMount: "always" });
}

// Inicia/optimiza la ruta de recojo desde la ubicación actual.
export function useIniciarRecojo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ rutaId, coords }: { rutaId: number; coords: Coordenadas }) => optimizarRecojo(rutaId, coords),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: clavesRuta.rutaActiva });
      qc.invalidateQueries({ queryKey: clavesRecojo.manifiesto });
    },
  });
}

// Registra la recepción condicionada (cantidad + foto de la guía) y refresca.
export function useRegistrarRecepcion() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ recojoId, cantidad, uriFoto }: { recojoId: number; cantidad: number; uriFoto: string }) =>
      registrarRecepcion(recojoId, cantidad, uriFoto),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: clavesRuta.rutaActiva });
      qc.invalidateQueries({ queryKey: clavesRecojo.manifiesto });
    },
  });
}
