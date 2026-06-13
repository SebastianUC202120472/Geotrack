// Guarda el token JWT de forma SEGURA (cifrado) con expo-secure-store.
// Nunca en texto plano ni en logs.
import * as SecureStore from "expo-secure-store";

const CLAVE_TOKEN = "geotrack_token";

// Lee el token guardado. Devuelve: el token o null si no hay sesión.
export async function leerToken(): Promise<string | null> {
  return SecureStore.getItemAsync(CLAVE_TOKEN);
}

// Guarda el token. Recibe: token (string).
export async function guardarToken(token: string): Promise<void> {
  await SecureStore.setItemAsync(CLAVE_TOKEN, token);
}

// Borra el token (cierre de sesión).
export async function borrarToken(): Promise<void> {
  await SecureStore.deleteItemAsync(CLAVE_TOKEN);
}
