import { useEffect } from "react";
import * as Location from "expo-location";
import { enviarUbicacion } from "@/api/conductor";

// Envía la ubicacion del conductor al backend cada ~12 s mientras `activa` sea true.
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
          { accuracy: Location.Accuracy.High, timeInterval: 12000, distanceInterval: 0 },
          (pos) => {
            enviarUbicacion(pos.coords.latitude, pos.coords.longitude).catch(() => {});
          }
        );
      } catch {
        // Sin GPS o permiso denegado.
      }
    })();

    return () => {
      cancelado = true;
      suscripcion?.remove();
    };
  }, [activa]);
}
