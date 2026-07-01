import type { Coordenadas, ParadaManifiesto } from "@/types/api";
import { optimizarRuta } from "@/api/rutas";

// Llama al servidor para optimizar el orden de paradas. Recibe rutaId y coords del conductor.
export async function optimizarDesdeUbicacion(
  rutaId: number,
  coords: Coordenadas
): Promise<number> {
  const resultado = await optimizarRuta(rutaId, coords);
  return resultado.total_paradas;
}

// Ordena paradas localmente por vecino más cercano. Recibe paradas con lat/lng y origen.
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
