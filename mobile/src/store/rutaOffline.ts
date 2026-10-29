// Copia en el teléfono de la última ruta descargada (C27-02). Si la app se abre sin señal, las
// pantallas muestran lo último que se descargó en vez de quedarse vacías. Se borra al cerrar
// sesión y cuando el servidor confirma que ya no hay ruta activa (404).
// Va en AsyncStorage sin cifrar: son los mismos datos que la app muestra en pantalla.
import AsyncStorage from "@react-native-async-storage/async-storage";
import { esErrorDeRed } from "@/api/client";

const PREFIJO = "ruta_offline_v1:";
const CLAVES = ["ruta-activa", "manifiesto", "navegacion", "manifiesto-recojo"] as const;
export type ClaveOffline = (typeof CLAVES)[number];

// True si el error es la respuesta 404 del servidor (el conductor ya no tiene ruta). Recibe el error.
function sinRuta(error: unknown): boolean {
  return (error as { response?: { status?: number } })?.response?.status === 404;
}

// Lee la copia guardada de una consulta, o null si no hay. Recibe la clave.
async function leer<T>(clave: ClaveOffline): Promise<T | null> {
  try {
    const guardado = await AsyncStorage.getItem(PREFIJO + clave);
    return guardado ? (JSON.parse(guardado) as T) : null;
  } catch {
    return null;
  }
}

// Envuelve la consulta de una pantalla: guarda cada respuesta del servidor y, si no hay señal,
// devuelve la última copia guardada. Recibe la clave y la función que consulta al servidor.
export function conCopiaOffline<T>(clave: ClaveOffline, consulta: () => Promise<T>): () => Promise<T> {
  return async () => {
    try {
      const datos = await consulta();
      AsyncStorage.setItem(PREFIJO + clave, JSON.stringify(datos)).catch(() => {});
      return datos;
    } catch (e) {
      if (esErrorDeRed(e)) {
        const copia = await leer<T>(clave);
        if (copia) return copia;
      } else if (sinRuta(e)) {
        AsyncStorage.removeItem(PREFIJO + clave).catch(() => {});
      }
      throw e;
    }
  };
}

// Aplica un cambio local a la copia guardada (p. ej. una entrega hecha sin señal), para que al
// reabrir la app sin red no reaparezca como pendiente. Recibe la clave y la función de cambio.
export async function ajustarCopia<T>(clave: ClaveOffline, cambio: (previa: T) => T): Promise<void> {
  const copia = await leer<T>(clave);
  if (!copia) return;
  try {
    await AsyncStorage.setItem(PREFIJO + clave, JSON.stringify(cambio(copia)));
  } catch {
    // sin espacio o almacenamiento no disponible: la cola offline sigue siendo la fuente de verdad
  }
}

// Borra todas las copias de la ruta. Llamar al cerrar sesión.
export async function limpiarRutaOffline(): Promise<void> {
  try {
    await AsyncStorage.multiRemove(CLAVES.map((c) => PREFIJO + c));
  } catch {
    // nada
  }
}
