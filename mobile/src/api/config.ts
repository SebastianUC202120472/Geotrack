// URL base desde EXPO_PUBLIC_API_URL; MEDIA_BASE_URL es el host sin "/api".

const API_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000/api";

export const API_BASE_URL = API_URL;
export const MEDIA_BASE_URL = API_URL.replace(/\/api\/?$/, "");

if (__DEV__) console.log("[GeoTrack] API base URL:", API_BASE_URL);

// Construye la URL absoluta de un recurso /media. Recibe ruta relativa o null.
export function urlMedia(ruta?: string | null): string | undefined {
  if (!ruta) return undefined;
  if (ruta.startsWith("http")) return ruta;
  return `${MEDIA_BASE_URL}${ruta}`;
}

// Alias retrocompatible para evidencias POD.
export const urlEvidencia = urlMedia;
