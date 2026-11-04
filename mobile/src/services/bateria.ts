// Nivel de batería del celular para medir el consumo de la jornada (EX-15).
import * as Battery from "expo-battery";

// Devuelve la batería entre 0 y 1, o null si el sistema no la informa (emulador, permisos).
export async function nivelBateria(): Promise<number | null> {
  try {
    const nivel = await Battery.getBatteryLevelAsync();
    return nivel >= 0 && nivel <= 1 ? nivel : null;
  } catch {
    return null;
  }
}
