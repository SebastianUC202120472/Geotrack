import { useEffect } from "react";
import { Alert } from "react-native";
import * as Location from "expo-location";
import { TAREA_UBICACION } from "@/tasks/ubicacionBackground";

let avisoMostrado = false;

// Inicia el rastreo de ubicación en segundo plano. Pide permisos y arranca el servicio.
async function iniciarRastreo(): Promise<void> {
  try {
    const fg = await Location.requestForegroundPermissionsAsync();
    if (fg.status !== "granted") {
      avisarUnaVez();
      return;
    }
    const bg = await Location.requestBackgroundPermissionsAsync();
    if (bg.status !== "granted") {
      avisarUnaVez();
      return;
    }

    const yaActiva = await Location.hasStartedLocationUpdatesAsync(TAREA_UBICACION);
    if (yaActiva) return;

    await Location.startLocationUpdatesAsync(TAREA_UBICACION, {
      accuracy: Location.Accuracy.High,
      timeInterval: 25000,
      distanceInterval: 0,
      pausesUpdatesAutomatically: false,
      foregroundService: {
        notificationTitle: "GeoTrack",
        notificationBody: "Rastreando tu ruta activa",
        notificationColor: "#2563eb",
      },
    });
  } catch {
    avisarUnaVez();
  }
}

// Detiene el servicio de ubicación si estaba activo.
async function detenerRastreo(): Promise<void> {
  try {
    const activa = await Location.hasStartedLocationUpdatesAsync(TAREA_UBICACION);
    if (activa) await Location.stopLocationUpdatesAsync(TAREA_UBICACION);
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
    "Para que el panel vea tu posición en tiempo real, activa el permiso de ubicación \"Permitir siempre\" en los ajustes. La app seguirá funcionando sin él."
  );
}

// Hook que mantiene el rastreo en segundo plano mientras activa sea true. Recibe activa (boolean).
export function useRastreoUbicacion(activa: boolean): void {
  useEffect(() => {
    if (activa) {
      iniciarRastreo();
    } else {
      detenerRastreo();
    }
    return () => {
      if (activa) detenerRastreo();
    };
  }, [activa]);
}
