import { Platform } from "react-native";

let envUrl = process.env.EXPO_PUBLIC_API_URL ?? "http://10.0.2.2:8000/api";

// 1. Si se configuró el puerto 8080 (servidor web Vite), corregir automáticamente al puerto 8000 del backend FastAPI
if (envUrl.includes(":8080")) {
  envUrl = envUrl.replace(":8080", ":8000");
}

// 2. Si estamos en emulador de Android (Platform.OS === 'android') y la URL apunta a localhost / 127.0.0.1, convertir a 10.0.2.2
if (Platform.OS === "android" && (envUrl.includes("localhost") || envUrl.includes("127.0.0.1"))) {
  envUrl = envUrl.replace("localhost", "10.0.2.2").replace("127.0.0.1", "10.0.2.2");
}

export const API_BASE_URL = envUrl;
export const MEDIA_BASE_URL = envUrl.replace(/\/api\/?$/, "");

// Construye la URL absoluta de un recurso /media. Recibe ruta relativa o null.
export function urlMedia(ruta?: string | null): string | undefined {
  if (!ruta) return undefined;
  if (ruta.startsWith("http")) return ruta;
  return `${MEDIA_BASE_URL}${ruta}`;
}

// Alias retrocompatible para evidencias POD.
export const urlEvidencia = urlMedia;
