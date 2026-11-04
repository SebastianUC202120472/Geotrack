// Rastreo GPS ÚNICO mientras hay una ruta en curso (EX-15). Antes corrían dos a la vez (uno en
// segundo plano cada 25 s y otro en primer plano cada 12 s); ahora hay uno solo:
//  1) si hay permiso "Permitir siempre", el servicio en segundo plano (sigue con la app minimizada);
//  2) si no (o el entorno no lo soporta, como Expo Go), un único seguimiento en primer plano.
import { useEffect } from "react";
import { Alert } from "react-native";
import * as Location from "expo-location";
import { TAREA_UBICACION } from "@/tasks/ubicacionBackground";
import { enviarUbicacion } from "@/api/conductor";
import { nivelBateria } from "@/services/bateria";

// Cada cuánto se toma y envía la posición. Alta precisión: el mapa de flota la necesita a nivel de calle.
const INTERVALO_MS = 15000;

let avisoMostrado = false;

// Intenta arrancar el servicio en segundo plano. Devuelve true si quedó activo (o ya lo estaba).
async function iniciarSegundoPlano(): Promise<boolean> {
  try {
    const bg = await Location.requestBackgroundPermissionsAsync();
    if (bg.status !== "granted") {
      avisarUnaVez();
      return false;
    }
    if (await Location.hasStartedLocationUpdatesAsync(TAREA_UBICACION)) return true;
    await Location.startLocationUpdatesAsync(TAREA_UBICACION, {
      accuracy: Location.Accuracy.High,
      timeInterval: INTERVALO_MS,
      distanceInterval: 0,
      pausesUpdatesAutomatically: false,
      foregroundService: {
        notificationTitle: "GeoTrack",
        notificationBody: "Rastreando tu ruta activa",
        notificationColor: "#2563eb",
      },
    });
    return true;
  } catch {
    return false;
  }
}

// Detiene el servicio de ubicación en segundo plano si estaba activo.
async function detenerSegundoPlano(): Promise<void> {
  try {
    if (await Location.hasStartedLocationUpdatesAsync(TAREA_UBICACION)) {
      await Location.stopLocationUpdatesAsync(TAREA_UBICACION);
    }
  } catch {
    // ignorar
  }
}

// Muestra alerta de permiso denegado una sola vez por sesion.
function avisarUnaVez(): void {
  if (avisoMostrado) return;
  avisoMostrado = true;
  Alert.alert(
    "Ubicación en segundo plano",
    "Para que el panel vea tu posición aunque minimices la app, activa el permiso de ubicación \"Permitir siempre\" en los ajustes. Mientras tanto se enviará solo con la app abierta."
  );
}

// Hook que mantiene un único rastreo GPS mientras activa sea true. Recibe activa (boolean).
export function useRastreoUbicacion(activa: boolean): void {
  useEffect(() => {
    if (!activa) {
      detenerSegundoPlano();
      return;
    }
    let cancelado = false;
    let suscripcion: Location.LocationSubscription | null = null;

    (async () => {
      try {
        const fg = await Location.requestForegroundPermissionsAsync();
        if (fg.status !== "granted" || cancelado) return;
        if (await iniciarSegundoPlano()) return;
        if (cancelado) return;
        // Respaldo: un solo seguimiento en primer plano.
        suscripcion = await Location.watchPositionAsync(
          { accuracy: Location.Accuracy.High, timeInterval: INTERVALO_MS, distanceInterval: 0 },
          (pos) => {
            nivelBateria()
              .then((b) => enviarUbicacion(pos.coords.latitude, pos.coords.longitude, b))
              .catch(() => {});
          }
        );
        if (cancelado) suscripcion.remove();
      } catch {
        // Sin GPS o permiso denegado: la app sigue funcionando sin enviar posición.
      }
    })();

    return () => {
      cancelado = true;
      suscripcion?.remove();
      detenerSegundoPlano();
    };
  }, [activa]);
}
