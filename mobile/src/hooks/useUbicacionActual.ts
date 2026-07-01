// Obtiene la ubicación actual del conductor pidiendo permiso con expo-location.
import { useCallback, useState } from "react";
import * as Location from "expo-location";
import type { Coordenadas } from "@/types/api";

interface ResultadoUbicacion {
  obtener: () => Promise<Coordenadas | null>;
  cargando: boolean;
  error: string | null;
}

// Hook que pide permiso de ubicación y devuelve { obtener, cargando, error }.
export function useUbicacionActual(): ResultadoUbicacion {
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const obtener = useCallback(async (): Promise<Coordenadas | null> => {
    setCargando(true);
    setError(null);
    try {
      const permiso = await Location.requestForegroundPermissionsAsync();
      if (permiso.status !== "granted") {
        setError("Necesitamos tu ubicación para iniciar la ruta. Actívala en los ajustes.");
        return null;
      }
      const pos = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.High,
      });
      return { latitud: pos.coords.latitude, longitud: pos.coords.longitude };
    } catch {
      setError("No se pudo obtener tu ubicación. Revisa el GPS.");
      return null;
    } finally {
      setCargando(false);
    }
  }, []);

  return { obtener, cargando, error };
}
