// Endpoint de autenticación. El backend usa OAuth2 (form-urlencoded).
import { api } from "./client";
import type { TokenResponse } from "@/types/api";

// Inicia sesión con correo + contraseña. Recibe: correo (string), contrasena
// (string). Devuelve: el TokenResponse con el access_token.
// El backend espera form-urlencoded; armamos el cuerpo a mano para no depender
// del polyfill de URLSearchParams de React Native.
export async function login(correo: string, contrasena: string): Promise<TokenResponse> {
  const cuerpo = `username=${encodeURIComponent(correo)}&password=${encodeURIComponent(contrasena)}`;

  const { data } = await api.post<TokenResponse>("/auth/login", cuerpo, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
}

// Extra CUS-04: el conductor que olvidó su clave pide que el admin la restablezca.
// Endpoint público (no requiere token). Recibe: el correo. Devuelve: { mensaje }
// genérico (el backend nunca revela si el correo existe o no).
export async function solicitarRestablecimiento(correo: string): Promise<{ mensaje: string }> {
  const { data } = await api.post<{ mensaje: string }>("/auth/solicitar-restablecimiento", { correo });
  return data;
}
