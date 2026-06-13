// Servicio de ruta: encapsula la optimización del orden de paradas para poder
// cambiar el proveedor sin tocar la UI.
import type { Coordenadas, ParadaManifiesto } from "@/types/api";
import { optimizarRuta } from "@/api/rutas";

// Optimiza en el SERVIDOR la ruta desde la ubicación actual del conductor.
// Recibe: rutaId (number), coords ({latitud, longitud}).
// Devuelve: número total de paradas reordenadas.
export async function optimizarDesdeUbicacion(
  rutaId: number,
  coords: Coordenadas
): Promise<number> {
  const resultado = await optimizarRuta(rutaId, coords);
  return resultado.total_paradas;
}

// Orden local por cercanía (Vecino Más Cercano) para una vista previa instantánea
// en el mapa antes de que responda el servidor. Recibe: paradas (ParadaManifiesto[])
// con lat/lng y origen ({latitud, longitud}). Devuelve: las paradas reordenadas.
// TODO: reemplazar por un proveedor de rutas real (p. ej. Google Directions) si
//       se necesita orden por calles reales en vez de distancia en línea recta.
export function ordenarPorCercania(
  paradas: ParadaManifiesto[],
  origen: Coordenadas
): ParadaManifiesto[] {
  const conCoords = paradas.filter((p) => p.latitud != null && p.longitud != null);
  const restantes = [...conCoords];
  const ordenadas: ParadaManifiesto[] = [];
  let actual = origen;

  while (restantes.length > 0) {
    let idxCercano = 0;
    let menorDistancia = Number.POSITIVE_INFINITY;
    restantes.forEach((p, i) => {
      const d = distanciaAlCuadrado(actual, { latitud: p.latitud!, longitud: p.longitud! });
      if (d < menorDistancia) {
        menorDistancia = d;
        idxCercano = i;
      }
    });
    const [siguiente] = restantes.splice(idxCercano, 1);
    ordenadas.push(siguiente);
    actual = { latitud: siguiente.latitud!, longitud: siguiente.longitud! };
  }
  return ordenadas;
}

// Distancia euclídea al cuadrado (sirve solo para comparar, sin raíz).
// Recibe: dos coordenadas. Devuelve: number.
function distanciaAlCuadrado(a: Coordenadas, b: Coordenadas): number {
  const dLat = a.latitud - b.latitud;
  const dLng = a.longitud - b.longitud;
  return dLat * dLat + dLng * dLng;
}
