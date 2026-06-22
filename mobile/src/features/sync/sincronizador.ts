// Motor de sincronización (CUS-27): vacía la cola en orden FIFO reenviando las
// funciones API ya existentes. Ante un error de RED (sin respuesta del servidor)
// detiene el flush y conserva el ítem; ante una respuesta HTTP del servidor lo
// quita (evita reintentos infinitos; marcarEstadoParada es idempotente).
import axios from "axios";
import type { QueryClient } from "@tanstack/react-query";
import { listar, quitar } from "@/store/colaSync";
import { estaOnline } from "@/hooks/useConexion";
import { marcarEstadoParada, subirEvidencia, crearReporte } from "@/api/conductor";
import { claves } from "@/features/ruta/hooks";

// Distingue un error de red (sin respuesta) de una respuesta HTTP del servidor.
function esErrorDeRed(e: unknown): boolean {
  return axios.isAxiosError(e) && !e.response;
}

let sincronizando = false;

// Vacía la cola si hay conexión. Recibe el QueryClient para refrescar al terminar.
export async function sincronizar(qc: QueryClient): Promise<void> {
  if (sincronizando) return;
  if (!(await estaOnline())) return;
  sincronizando = true;
  let huboCambios = false;
  try {
    const pendientes = await listar();
    for (const item of pendientes) {
      try {
        if (item.tipo === "ENTREGA") {
          await marcarEstadoParada(item.pedidoId, "ENTREGADO");
          if (item.fotoUri) {
            try {
              await subirEvidencia(item.pedidoId, item.fotoUri);
            } catch (e) {
              if (esErrorDeRed(e)) throw e;   // sin señal: reintentar luego
              // foto faltante / error no de red: la entrega quedó marcada; omitimos la foto
            }
          }
        } else {
          await marcarEstadoParada(item.pedidoId, "FALLIDO", item.motivo);
          await crearReporte(item.pedidoId, item.motivo ?? "Sin motivo", item.descripcion);
        }
        await quitar(item.id);
        huboCambios = true;
      } catch (e) {
        if (esErrorDeRed(e)) break;   // sin señal: dejamos el resto para el próximo intento
        await quitar(item.id);        // el servidor respondió (4xx/5xx): no reintentar
        huboCambios = true;
      }
    }
  } finally {
    sincronizando = false;
    if (huboCambios) {
      qc.invalidateQueries({ queryKey: claves.rutaActiva });
      qc.invalidateQueries({ queryKey: claves.manifiesto });
      qc.invalidateQueries({ queryKey: ["mis-reportes"] });
    }
  }
}
