// Rastreo de ubicación en SEGUNDO PLANO mientras la ruta esté activa. Sustituye
// a useEnviarUbicacion (foreground/watchPositionAsync): pide permisos foreground
// y background, e inicia/detiene un servicio de ubicación que sigue enviando la
// posición al backend aunque la app esté minimizada. Requiere dev build (no
// funciona en Expo Go).
import { useEffect } from "react";
import { Alert } from "react-native";
import * as Location from "expo-location";
import { TAREA_UBICACION } from "@/tasks/ubicacionBackground";

// Aviso suave de permiso denegado (una sola vez por arranque). Evita molestar
// al conductor con varias alertas si los permisos no se conceden.
let avisoMostrado = false;

// Inicia el servicio de ubicación en segundo plano. Pide permiso foreground y
// background; si se conceden, arranca las actualizaciones con el foreground
// service (Android). Best-effort: si algo falla, muestra un aviso suave una vez
// y no rompe la app. No recibe parámetros. No devuelve nada.
async function iniciarRastreo(): Promise<void> {
  try {
    const fg = await Location.requestForegroundPermissionsAsync();
    if (fg.status !== "granted") {
      avisarUnaVez();
      return;
    }
    const bg = await Location.requestBackgroundPermissionsAsync();
    if (bg.status !== "granted") {
      // Sin permiso de fondo no se puede usar el servicio en background; se avisa
      // suavemente y se deja de intentar (el conductor seguirá visible al abrir la app).
      avisarUnaVez();
      return;
    }

    // Evita arrancar dos veces el mismo servicio (idempotente).
    const yaActiva = await Location.hasStartedLocationUpdatesAsync(TAREA_UBICACION);
    if (yaActiva) return;

    await Location.startLocationUpdatesAsync(TAREA_UBICACION, {
      accuracy: Location.Accuracy.High,
      timeInterval: 25000,
      distanceInterval: 0,
      pausesUpdatesAutomatically: false,
      // Notificación persistente del servicio en primer plano (obligatoria en Android).
      foregroundService: {
        notificationTitle: "GeoTrack",
        notificationBody: "Rastreando tu ruta activa",
        notificationColor: "#2563eb",
      },
    });
  } catch {
    // GPS apagado u otro error: aviso suave y seguimos sin rastreo.
    avisarUnaVez();
  }
}

// Detiene el servicio de ubicación si estaba activo. Best-effort. No recibe nada.
async function detenerRastreo(): Promise<void> {
  try {
    const activa = await Location.hasStartedLocationUpdatesAsync(TAREA_UBICACION);
    if (activa) await Location.stopLocationUpdatesAsync(TAREA_UBICACION);
  } catch {
    // Ignorar: si no estaba activa o el módulo no responde, no hay nada que detener.
  }
}

// Muestra el aviso de permiso solo la primera vez en la sesión.
function avisarUnaVez(): void {
  if (avisoMostrado) return;
  avisoMostrado = true;
  Alert.alert(
    "Ubicación en segundo plano",
    "Para que el panel vea tu posición en tiempo real, activa el permiso de ubicación \"Permitir siempre\" en los ajustes. La app seguirá funcionando sin él."
  );
}

// Hook: mientras `activa` sea true, mantiene el rastreo en segundo plano; al
// dejar de estar activa (o al desmontar) lo detiene. Recibe: activa (boolean).
// No devuelve nada.
export function useRastreoUbicacion(activa: boolean): void {
  useEffect(() => {
    if (activa) {
      iniciarRastreo();
    } else {
      detenerRastreo();
    }
    // Al desmontar o cambiar `activa` a false, asegura detener el servicio.
    return () => {
      if (activa) detenerRastreo();
    };
  }, [activa]);
}
