// Cliente HTTP central. Inyecta token en cada request y cierra sesión ante 401.
import axios from "axios";
import { API_BASE_URL } from "./config";
import { leerToken } from "./tokenStorage";

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

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

// Interceptor de respuesta: un 401 de una petición que llevaba token significa que la
// sesión venció; sin token (login fallido o app recién abierta) no hay sesión que cerrar.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const llevabaToken = !!error?.config?.headers?.Authorization;
    if (error?.response?.status === 401 && llevabaToken && alExpirarSesion) {
      alExpirarSesion();
    }
    return Promise.reject(error);
  }
);

// Detecta si el error es de red (sin respuesta del servidor). Recibe: error capturado.
export function esErrorDeRed(error: unknown): boolean {
  return axios.isAxiosError(error) && !error.response;
}

// Extrae un mensaje de error legible del backend o de errores locales. Recibe: error capturado.
export function mensajeDeError(error: unknown): string {
  if (error instanceof Error && !axios.isAxiosError(error)) {
    return error.message;
  }
  if (axios.isAxiosError(error)) {
    const detalle = error.response?.data?.detail;
    if (typeof detalle === "string") return detalle;
    if (Array.isArray(detalle) && detalle[0]?.msg) return detalle[0].msg;
    if (error.response?.status === 404) return "No tienes una ruta asignada todavía.";
  }
  return "Ocurrió un error. Revisa tu conexión e inténtalo de nuevo.";
}
