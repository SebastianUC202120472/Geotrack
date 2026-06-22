// Cola PERSISTENTE de acciones de entrega hechas sin conexión (CUS-27). Se guarda
// en AsyncStorage para sobrevivir al cierre de la app; las fotos POD se copian a
// disco (expo-file-system) para que no se pierdan si el caché del picker se limpia.
import AsyncStorage from "@react-native-async-storage/async-storage";
import * as FileSystem from "expo-file-system";

export type TipoAccion = "ENTREGA" | "FALLIDO";

export interface AccionPendiente {
  id: string;
  tipo: TipoAccion;
  pedidoId: number;
  motivo?: string;
  descripcion?: string;
  fotoUri?: string;   // ruta persistida en disco (documentDirectory) si es ENTREGA con foto
  creadoEn: number;
  // Progreso por sub-paso para que un reintento sea idempotente (CUS-27): no se
  // re-ejecutan los POST ya hechos (evita evidencia/reporte duplicados).
  estadoAplicado?: boolean;   // el PATCH de estado ya llegó al servidor
  evidenciaSubida?: boolean;  // la foto POD (multipart) ya se subió
  reporteCreado?: boolean;    // el reporte de falla (POST) ya se creó
}

const CLAVE = "cola_sync_v1";
const DIR_FOTOS = FileSystem.documentDirectory + "pod_pendientes/";

let cache: AccionPendiente[] | null = null;
const suscriptores = new Set<() => void>();

// Lee la cola (con caché en memoria para no golpear AsyncStorage en cada render).
async function _leer(): Promise<AccionPendiente[]> {
  if (cache) return cache;
  const raw = await AsyncStorage.getItem(CLAVE);
  cache = raw ? (JSON.parse(raw) as AccionPendiente[]) : [];
  return cache;
}

// Persiste la cola y notifica a los suscriptores (la UI reacciona).
async function _guardar(items: AccionPendiente[]): Promise<void> {
  cache = items;
  await AsyncStorage.setItem(CLAVE, JSON.stringify(items));
  suscriptores.forEach((cb) => cb());
}

// Asegura que exista la carpeta de fotos pendientes.
async function _asegurarDir(): Promise<void> {
  const info = await FileSystem.getInfoAsync(DIR_FOTOS);
  if (!info.exists) await FileSystem.makeDirectoryAsync(DIR_FOTOS, { intermediates: true });
}

// Encola una acción. Si trae foto, la copia a disco persistente. Recibe los datos
// de la acción; devuelve el ítem encolado.
export async function encolar(params: {
  tipo: TipoAccion; pedidoId: number; motivo?: string; descripcion?: string; fotoUri?: string;
}): Promise<AccionPendiente> {
  const items = await _leer();
  const id = `${Date.now()}_${params.pedidoId}`;
  let fotoUri = params.fotoUri;
  if (fotoUri) {
    try {
      await _asegurarDir();
      const destino = `${DIR_FOTOS}${id}.jpg`;
      await FileSystem.copyAsync({ from: fotoUri, to: destino });
      fotoUri = destino;
    } catch {
      // Si la copia falla, conservamos el uri original (mejor que perder la foto).
    }
  }
  const item: AccionPendiente = {
    id, tipo: params.tipo, pedidoId: params.pedidoId,
    motivo: params.motivo, descripcion: params.descripcion, fotoUri, creadoEn: Date.now(),
  };
  await _guardar([...items, item]);
  return item;
}

// Devuelve una copia de las acciones pendientes (orden FIFO de inserción).
export async function listar(): Promise<AccionPendiente[]> {
  return [...(await _leer())];
}

// Quita un ítem (y borra su foto persistida, si la tenía bajo nuestra carpeta).
export async function quitar(id: string): Promise<void> {
  const items = await _leer();
  const item = items.find((i) => i.id === id);
  if (item?.fotoUri && item.fotoUri.startsWith(DIR_FOTOS)) {
    try { await FileSystem.deleteAsync(item.fotoUri, { idempotent: true }); } catch { /* nada */ }
  }
  await _guardar(items.filter((i) => i.id !== id));
}

// Fusiona cambios en el ítem indicado (por id) y persiste. Sirve para guardar el
// progreso por sub-paso del sincronizador. Recibe: id (string) y cambios parciales.
export async function actualizar(id: string, cambios: Partial<AccionPendiente>): Promise<void> {
  const items = await _leer();
  await _guardar(items.map((i) => (i.id === id ? { ...i, ...cambios } : i)));
}

// Cuántas acciones hay pendientes.
export async function contar(): Promise<number> {
  return (await _leer()).length;
}

// Limpia toda la cola (caché + persistencia + fotos). Se llama al cerrar sesión
// para que las acciones de un conductor no se reenvíen bajo el token de otro.
export async function limpiar(): Promise<void> {
  cache = [];
  try { await AsyncStorage.removeItem(CLAVE); } catch { /* nada */ }
  try { await FileSystem.deleteAsync(DIR_FOTOS, { idempotent: true }); } catch { /* nada */ }
  suscriptores.forEach((cb) => cb());
}

// Suscribe un callback a los cambios de la cola. Devuelve la función para desuscribir.
export function suscribir(cb: () => void): () => void {
  suscriptores.add(cb);
  return () => { suscriptores.delete(cb); };
}
