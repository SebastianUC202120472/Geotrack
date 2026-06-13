// Endpoint de autenticación. El backend usa OAuth2 (form-urlencoded).
import { api } from "./client";
import type { TokenResponse } from "@/types/api";

// Inicia sesión con correo + contraseña. Recibe: correo (string), contrasena
// (string). Devuelve: el TokenResponse con el access_token.
export async function login(correo: string, contrasena: string): Promise<TokenResponse> {
  const cuerpo = new URLSearchParams();
  cuerpo.append("username", correo);
  cuerpo.append("password", contrasena);

  const { data } = await api.post<TokenResponse>("/auth/login", cuerpo.toString(), {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
}
