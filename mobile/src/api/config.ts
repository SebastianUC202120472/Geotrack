// Configuración de red. La URL base viene de EXPO_PUBLIC_API_URL (igual que la
// web). MEDIA_BASE_URL es el host sin "/api" para abrir las fotos de /media.

const API_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000/api";

export const API_BASE_URL = API_URL;
export const MEDIA_BASE_URL = API_URL.replace(/\/api\/?$/, "");

// Diagnóstico en desarrollo: muestra en el terminal qué URL usa la app. Si dice
// "localhost", el .env no se cargó (reinicia con `npx expo start -c`).
if (__DEV__) console.log("[GeoTrack] API base URL:", API_BASE_URL);

// Construye la URL absoluta de un recurso /media a partir de la ruta del backend.
// Recibe: ruta relativa o null. Devuelve: URL o undefined.
export function urlMedia(ruta?: string | null): string | undefined {
  if (!ruta) return undefined;
  if (ruta.startsWith("http")) return ruta;
  return `${MEDIA_BASE_URL}${ruta}`;
}

// Alias retrocompatible (usado por las evidencias POD).
export const urlEvidencia = urlMedia;
