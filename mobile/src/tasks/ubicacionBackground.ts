// Tarea de ubicación en SEGUNDO PLANO (TaskManager). Se define a nivel de módulo
// para que el sistema pueda invocarla aunque la app esté en background. Por cada
// posición recibida la envía al backend (mapa de flota en vivo del panel). NO
// funciona en Expo Go: requiere un build de desarrollo.
import * as TaskManager from "expo-task-manager";
import * as Location from "expo-location";
import { enviarUbicacion } from "@/api/conductor";

// Nombre único de la tarea, compartido por el registro y el inicio/detención.
export const TAREA_UBICACION = "geotrack-ubicacion";

// Forma de los datos que entrega expo-location al callback de la tarea.
interface DatosUbicacion {
  locations: Location.LocationObject[];
}

// Define la tarea: por cada ubicación recibida, la envía al backend. Best-effort:
// ignora errores de red para no detener el rastreo. No recibe parámetros propios
// (los recibe el runtime de TaskManager).
TaskManager.defineTask(TAREA_UBICACION, async ({ data, error }) => {
  if (error) return; // error del sistema de ubicación: nada que hacer aquí
  const { locations } = (data ?? {}) as DatosUbicacion;
  if (!locations?.length) return;
  for (const loc of locations) {
    try {
      await enviarUbicacion(loc.coords.latitude, loc.coords.longitude);
    } catch {
      // Sin conexión / error del servidor: se omite esta posición y se sigue.
    }
  }
});
