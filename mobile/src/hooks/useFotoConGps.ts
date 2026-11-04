// Toma fotos de evidencia SOLO con la cámara y registra dónde se tomaron (GPS).
// La galería no se ofrece: una evidencia debe capturarse en el lugar (C13-01, C26-01).
import { useCallback, useState } from "react";
import * as ImagePicker from "expo-image-picker";
import * as Location from "expo-location";
import type { Coordenadas } from "@/types/api";

export interface FotoConGps {
  uri: string;
  coords: Coordenadas | null;
}

interface ResultadoFoto {
  tomar: () => Promise<FotoConGps | null>;
  tomando: boolean;
  error: string | null;
}

const ESPERA_GPS_MS = 8000;

// Obtiene la posición actual; si tarda, usa la última conocida. Devuelve null sin permiso o sin señal.
async function posicionActual(): Promise<Coordenadas | null> {
  const permiso = await Location.requestForegroundPermissionsAsync();
  if (permiso.status !== "granted") return null;
  try {
    const pos = await Promise.race([
      Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced }),
      new Promise<null>((resolver) => setTimeout(() => resolver(null), ESPERA_GPS_MS)),
    ]);
    const final = pos ?? (await Location.getLastKnownPositionAsync());
    return final ? { latitud: final.coords.latitude, longitud: final.coords.longitude } : null;
  } catch {
    return null;
  }
}

// Hook que abre la cámara y devuelve { tomar, tomando, error }. tomar() resuelve con la foto
// y sus coordenadas (o null si se canceló o no hubo permiso de cámara).
export function useFotoConGps(): ResultadoFoto {
  const [tomando, setTomando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const tomar = useCallback(async (): Promise<FotoConGps | null> => {
    setError(null);
    const permiso = await ImagePicker.requestCameraPermissionsAsync();
    if (!permiso.granted) {
      setError("Necesitamos permiso de cámara para tomar la evidencia.");
      return null;
    }
    const res = await ImagePicker.launchCameraAsync({ quality: 0.6 });
    if (res.canceled || !res.assets.length) return null;
    setTomando(true);
    try {
      const coords = await posicionActual();
      if (!coords) setError("No se pudo leer el GPS: la foto se guardará sin ubicación.");
      return { uri: res.assets[0].uri, coords };
    } finally {
      setTomando(false);
    }
  }, []);

  return { tomar, tomando, error };
}
