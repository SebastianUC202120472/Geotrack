import { api } from "./client";
import type { TokenResponse } from "@/types/api";

// Inicia sesion con correo y contrasena. Recibe: correo, contrasena. Devuelve: TokenResponse.
export async function login(correo: string, contrasena: string): Promise<TokenResponse> {
  const cuerpo = `username=${encodeURIComponent(correo)}&password=${encodeURIComponent(contrasena)}`;

  const { data } = await api.post<TokenResponse>("/auth/login", cuerpo, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
}

// Solicita restablecimiento de contrasena. Recibe: correo.
export async function solicitarRestablecimiento(correo: string): Promise<{ mensaje: string }> {
  const { data } = await api.post<{ mensaje: string }>("/auth/solicitar-restablecimiento", { correo });
  return data;
}
