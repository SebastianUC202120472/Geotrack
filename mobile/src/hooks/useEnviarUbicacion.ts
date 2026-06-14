// Envía la posición del conductor al backend mientras tenga una ruta activa.
import { useEffect } from "react";
import * as Location from "expo-location";
import { enviarUbicacion } from "@/api/conductor";

// Mientras `activa` sea true, observa la posición (foreground / app abierta) y la
// envía al backend cada ~12 s. Best-effort: ignora errores de permiso o de red
// para no interrumpir la operación del conductor. No devuelve nada.
export function useEnviarUbicacion(activa: boolean): void {
  useEffect(() => {
    if (!activa) return;

    let suscripcion: Location.LocationSubscription | null = null;
    let cancelado = false;

    (async () => {
      try {
        const permiso = await Location.requestForegroundPermissionsAsync();
        if (permiso.status !== "granted" || cancelado) return;

        suscripcion = await Location.watchPositionAsync(
          { accuracy: Location.Accuracy.High, timeInterval: 12000, distanceInterval: 20 },
          (pos) => {
            // No esperamos la respuesta ni rompemos si falla (best-effort).
            enviarUbicacion(pos.coords.latitude, pos.coords.longitude).catch(() => {});
          }
        );
      } catch {
        // Sin GPS o permiso denegado: no enviamos nada.
      }
    })();

    return () => {
      cancelado = true;
      suscripcion?.remove();
    };
  }, [activa]);
}
