// Tarea en segundo plano: envía cada posición GPS al backend. Requiere build de desarrollo.
import * as TaskManager from "expo-task-manager";
import * as Location from "expo-location";
import { enviarUbicacion } from "@/api/conductor";

export const TAREA_UBICACION = "geotrack-ubicacion";

interface DatosUbicacion {
  locations: Location.LocationObject[];
}

// Registra la tarea con TaskManager. Recibe data/error del runtime de expo-location.
TaskManager.defineTask(TAREA_UBICACION, async ({ data, error }) => {
  if (error) return;
  const { locations } = (data ?? {}) as DatosUbicacion;
  if (!locations?.length) return;
  for (const loc of locations) {
    try {
      await enviarUbicacion(loc.coords.latitude, loc.coords.longitude);
    } catch {
      // Ignora errores de red para no detener el rastreo.
    }
  }
});
