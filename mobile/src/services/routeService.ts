import type { Coordenadas, OptimizacionResultado, ParadaManifiesto } from "@/types/api";
import { optimizarRuta } from "@/api/rutas";

// Llama al servidor para optimizar el orden de paradas. Recibe rutaId y coords del conductor.
export async function optimizarDesdeUbicacion(
  rutaId: number,
  coords: Coordenadas
): Promise<OptimizacionResultado> {
  return optimizarRuta(rutaId, coords);
}

// Texto del aviso tras optimizar: paradas ordenadas, km y ahorro (C20-01) y las paradas que
// quedaron fuera por no tener ubicación (C20-03). Recibe el resultado y cómo llamar a las paradas.
export function mensajeOptimizacion(r: OptimizacionResultado, nombre = "paradas"): string {
  const lineas = [`Se ordenaron ${r.total_paradas} ${nombre} desde tu ubicación.`];
  if (r.km_estimado != null) {
    const ahorro = r.km_ahorrado && r.km_ahorrado > 0
      ? ` Ahorras ${r.km_ahorrado.toFixed(1)} km frente al orden de carga.`
      : "";
    lineas.push(`Recorrido estimado: ${r.km_estimado.toFixed(1)} km.${ahorro}`);
  }
  const sinUbicacion = r.paradas_sin_ubicacion ?? 0;
  if (sinUbicacion > 0) {
    const codigos = (r.codigos_sin_ubicacion ?? []).join(", ");
    lineas.push(
      `⚠️ ${sinUbicacion} ${sinUbicacion === 1 ? "parada no tiene" : "paradas no tienen"} ubicación en el mapa` +
      `${codigos ? ` (${codigos})` : ""} y quedaron al final de la lista. Avisa a la central.`
    );
  }
  return lineas.join("\n\n");
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
