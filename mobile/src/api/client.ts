// Cliente HTTP central (axios). Inyecta el token en cada request y, si el
// backend responde 401, dispara el cierre de sesión registrado.
import axios from "axios";
import { API_BASE_URL } from "./config";
import { leerToken } from "./tokenStorage";

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

// Callback que el AuthProvider registra para cerrar sesión ante un 401.
let alExpirarSesion: (() => void) | null = null;

// Registra qué hacer cuando el token expira. Recibe: función sin argumentos.
export function registrarCierrePorSesionExpirada(fn: () => void): void {
  alExpirarSesion = fn;
}

// Interceptor de petición: añade Authorization si hay token guardado.
api.interceptors.request.use(async (config) => {
  const token = await leerToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor de respuesta: ante 401, cierra sesión y propaga el error.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401 && alExpirarSesion) {
      alExpirarSesion();
    }
    return Promise.reject(error);
  }
);

// Detecta si el error es de red (sin respuesta del servidor). Recibe: error capturado.
export function esErrorDeRed(error: unknown): boolean {
  return axios.isAxiosError(error) && !error.response;
}

// Extrae un mensaje de error legible del backend. Recibe: error de axios.
export function mensajeDeError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detalle = error.response?.data?.detail;
    if (typeof detalle === "string") return detalle;
    if (Array.isArray(detalle) && detalle[0]?.msg) return detalle[0].msg;
    if (error.response?.status === 404) return "No tienes una ruta asignada todavía.";
  }
  return "Ocurrió un error. Revisa tu conexión e inténtalo de nuevo.";
}
