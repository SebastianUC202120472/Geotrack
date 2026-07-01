// Cola persistente de acciones de entrega offline; guarda fotos POD en disco.
import AsyncStorage from "@react-native-async-storage/async-storage";
import * as FileSystem from "expo-file-system";

export type TipoAccion = "ENTREGA" | "FALLIDO";

export interface AccionPendiente {
  id: string;
  tipo: TipoAccion;
  pedidoId: number;
  motivo?: string;
  descripcion?: string;
  fotoUri?: string;   // ruta persistida en disco
  creadoEn: number;
  // Progreso por sub-paso para reintentos idempotentes: no se re-ejecutan los POST ya hechos.
  estadoAplicado?: boolean;
  evidenciaSubida?: boolean;
  reporteCreado?: boolean;
}

const CLAVE = "cola_sync_v1";
const DIR_FOTOS = (FileSystem.documentDirectory ?? "") + "pod_pendientes/";

let cache: AccionPendiente[] | null = null;
const suscriptores = new Set<() => void>();

// Serializa escrituras para evitar condiciones de carrera read-modify-write.
let _cadena: Promise<void> = Promise.resolve();
function _serializar<T>(op: () => Promise<T>): Promise<T> {
  const resultado = _cadena.then(op);
  _cadena = resultado.then(() => undefined, () => undefined);
  return resultado;
}

// Lee la cola con caché en memoria. Si el JSON está corrupto reinicia la cola.
async function _leer(): Promise<AccionPendiente[]> {
  if (cache) return cache;
  const raw = await AsyncStorage.getItem(CLAVE);
  try { cache = raw ? (JSON.parse(raw) as AccionPendiente[]) : []; }
  catch { cache = []; }
  return cache;
}

// Persiste la cola y notifica suscriptores.
async function _guardar(items: AccionPendiente[]): Promise<void> {
  cache = items;
  await AsyncStorage.setItem(CLAVE, JSON.stringify(items));
  suscriptores.forEach((cb) => cb());
}

// Crea la carpeta de fotos si no existe.
async function _asegurarDir(): Promise<void> {
  const info = await FileSystem.getInfoAsync(DIR_FOTOS);
  if (!info.exists) await FileSystem.makeDirectoryAsync(DIR_FOTOS, { intermediates: true });
}

// Encola una acción; copia la foto a disco si viene adjunta. Devuelve el ítem encolado.
export function encolar(params: {
  tipo: TipoAccion; pedidoId: number; motivo?: string; descripcion?: string; fotoUri?: string;
}): Promise<AccionPendiente> {
  return _serializar(async () => {
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
        // conserva el uri original si la copia falla
      }
    }
    const item: AccionPendiente = {
      id, tipo: params.tipo, pedidoId: params.pedidoId,
      motivo: params.motivo, descripcion: params.descripcion, fotoUri, creadoEn: Date.now(),
    };
    await _guardar([...items, item]);
    return item;
  });
}

// Devuelve copia de las acciones pendientes en orden FIFO.
export async function listar(): Promise<AccionPendiente[]> {
  return [...(await _leer())];
}

// Elimina el ítem y su foto persistida si existe. Recibe el id del ítem.
export function quitar(id: string): Promise<void> {
  return _serializar(async () => {
    const items = await _leer();
    const item = items.find((i) => i.id === id);
    if (item?.fotoUri && item.fotoUri.startsWith(DIR_FOTOS)) {
      try { await FileSystem.deleteAsync(item.fotoUri, { idempotent: true }); } catch { /* nada */ }
    }
    await _guardar(items.filter((i) => i.id !== id));
  });
}

// Fusiona cambios parciales en el ítem indicado. Recibe id y los cambios.
export function actualizar(id: string, cambios: Partial<AccionPendiente>): Promise<void> {
  return _serializar(async () => {
    const items = await _leer();
    await _guardar(items.map((i) => (i.id === id ? { ...i, ...cambios } : i)));
  });
}

// Cuántas acciones hay pendientes.
export async function contar(): Promise<number> {
  return (await _leer()).length;
}

// Limpia cola, persistencia y fotos. Llamar al cerrar sesion.
export function limpiar(): Promise<void> {
  return _serializar(async () => {
    cache = [];
    try { await AsyncStorage.removeItem(CLAVE); } catch { /* nada */ }
    try { await FileSystem.deleteAsync(DIR_FOTOS, { idempotent: true }); } catch { /* nada */ }
    suscriptores.forEach((cb) => cb());
  });
}

// Suscribe un callback a cambios de la cola. Devuelve la funcion para desuscribir.
export function suscribir(cb: () => void): () => void {
  suscriptores.add(cb);
  return () => { suscriptores.delete(cb); };
}
