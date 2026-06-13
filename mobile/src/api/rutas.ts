// Endpoint de optimización de la ruta del conductor (Vecino Más Cercano en el
// backend). Reordena la secuencia de paradas partiendo de la posición actual.
import { api } from "./client";
import type { Coordenadas, OptimizacionResultado } from "@/types/api";

// Optimiza la ruta desde la ubicación del conductor. Recibe: rutaId (number),
// coords ({latitud, longitud}). Devuelve: OptimizacionResultado.
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
