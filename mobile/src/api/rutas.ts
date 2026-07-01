import { api } from "./client";
import type { Coordenadas, OptimizacionResultado } from "@/types/api";

// Optimiza el orden de paradas de la ruta. Recibe rutaId y coords del conductor.
export async function optimizarRuta(
  rutaId: number,
  coords: Coordenadas
): Promise<OptimizacionResultado> {
  const { data } = await api.post<OptimizacionResultado>("/rutas/conductor/optimizar", {
    ruta_id: rutaId,
    latitud_actual_conductor: coords.latitud,
    longitud_actual_conductor: coords.longitud,
  });
  return data;
}
