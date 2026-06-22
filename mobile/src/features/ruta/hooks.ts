// Hooks de React Query para la ruta del conductor: consultas (ruta activa,
// manifiesto, navegación) y acciones (iniciar/optimizar y finalizar).
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  obtenerRutaActiva,
  obtenerManifiesto,
  obtenerNavegacion,
  finalizarRuta,
} from "@/api/conductor";
import { optimizarDesdeUbicacion } from "@/services/routeService";
import type { Coordenadas } from "@/types/api";

// Claves de caché para invalidar tras una acción.
export const claves = {
  rutaActiva: ["ruta-activa"] as const,
  manifiesto: ["manifiesto"] as const,
  navegacion: ["navegacion"] as const,
  // MINOR 4: clave centralizada para la query de reportes (evita literales dispersos).
  misReportes: ["mis-reportes"] as const,
};

// Si no hay ruta (404), no reintentar en bucle.
const sinReintentarEn404 = (intentos: number, error: unknown): boolean => {
  const status = (error as { response?: { status?: number } })?.response?.status;
  if (status === 404) return false;
  return intentos < 2;
};

// Refresco automático cada 10 s (además del refresco al enfocar la pantalla/app).
const INTERVALO = 10_000;

// Resumen de la ruta activa. Devuelve: query de RutaActiva.
export function useRutaActiva() {
  return useQuery({ queryKey: claves.rutaActiva, queryFn: obtenerRutaActiva, retry: sinReintentarEn404, refetchInterval: INTERVALO, refetchOnMount: "always" });
}

// Manifiesto (paradas). Devuelve: query de Manifiesto.
export function useManifiesto() {
  return useQuery({ queryKey: claves.manifiesto, queryFn: obtenerManifiesto, retry: sinReintentarEn404, refetchInterval: INTERVALO, refetchOnMount: "always" });
}

// Waypoints para el mapa. Devuelve: query de Navegacion.
export function useNavegacion() {
  return useQuery({ queryKey: claves.navegacion, queryFn: obtenerNavegacion, retry: sinReintentarEn404, refetchInterval: INTERVALO, refetchOnMount: "always" });
}

// Inicia/optimiza la ruta desde la ubicación actual y refresca los datos.
// Devuelve: mutación que recibe { rutaId, coords }.
export function useIniciarRuta() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ rutaId, coords }: { rutaId: number; coords: Coordenadas }) =>
      optimizarDesdeUbicacion(rutaId, coords),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: claves.rutaActiva });
      qc.invalidateQueries({ queryKey: claves.manifiesto });
      qc.invalidateQueries({ queryKey: claves.navegacion });
    },
  });
}

// Finaliza la ruta del día y refresca el resumen.
export function useFinalizarRuta() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: finalizarRuta,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: claves.rutaActiva });
      qc.invalidateQueries({ queryKey: claves.manifiesto });
    },
  });
}
