// Cifrado de lo que la app guarda en el teléfono (cola offline y copia de la ruta): AES-256-GCM
// con una clave aleatoria que vive en el almacenamiento seguro del sistema (Keychain / Keystore).
// Así la "cola local cifrada" del documento es real (EX-23).
import { gcm } from "@noble/ciphers/aes";
import { utf8ToBytes, bytesToUtf8 } from "@noble/ciphers/utils";
import * as Crypto from "expo-crypto";
import * as SecureStore from "expo-secure-store";

const NOMBRE_CLAVE = "geotrack_clave_local_v1";
const PREFIJO = "v1:";
let clave: Uint8Array | null = null;

// Convierte bytes a base64 (por tramos para no desbordar con textos largos). Recibe los bytes.
function aBase64(bytes: Uint8Array): string {
  let texto = "";
  for (let i = 0; i < bytes.length; i += 0x8000) {
    texto += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  }
  return btoa(texto);
}

// Convierte base64 a bytes. Recibe el texto en base64.
function deBase64(texto: string): Uint8Array {
  const binario = atob(texto);
  const bytes = new Uint8Array(binario.length);
  for (let i = 0; i < binario.length; i++) bytes[i] = binario.charCodeAt(i);
  return bytes;
}

// Clave de 32 bytes del teléfono: se crea la primera vez y se guarda en SecureStore.
async function obtenerClave(): Promise<Uint8Array> {
  if (clave) return clave;
  let guardada = await SecureStore.getItemAsync(NOMBRE_CLAVE);
  if (!guardada) {
    guardada = aBase64(Crypto.getRandomBytes(32));
    await SecureStore.setItemAsync(NOMBRE_CLAVE, guardada);
  }
  clave = deBase64(guardada);
  return clave;
}

// Cifra un texto. Devuelve "v1:<nonce>:<cifrado>" en base64. Recibe el texto.
export async function cifrar(texto: string): Promise<string> {
  const nonce = Crypto.getRandomBytes(12);
  const cifrado = gcm(await obtenerClave(), nonce).encrypt(utf8ToBytes(texto));
  return `${PREFIJO}${aBase64(nonce)}:${aBase64(cifrado)}`;
}

// Descifra lo guardado. Un texto sin prefijo es de una versión anterior (sin cifrar) y se devuelve
// tal cual; si no se puede descifrar (clave borrada) devuelve null. Recibe el valor guardado.
export async function descifrar(valor: string): Promise<string | null> {
  if (!valor.startsWith(PREFIJO)) return valor;
  try {
    const [nonce, cifrado] = valor.slice(PREFIJO.length).split(":");
    return bytesToUtf8(gcm(await obtenerClave(), deBase64(nonce)).decrypt(deBase64(cifrado)));
  } catch {
    return null;
  }
}
