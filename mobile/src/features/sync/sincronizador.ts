import type { QueryClient } from "@tanstack/react-query";
import { listar, quitar, actualizar, type AccionPendiente } from "@/store/colaSync";
import { estaOnline } from "@/hooks/useConexion";
import { marcarEstadoParada, subirEvidencia, crearReporte, subirEvidenciaReporte } from "@/api/conductor";
import { esErrorDeRed } from "@/api/client";
import { claves } from "@/features/ruta/hooks";
import type { Coordenadas, Receptor } from "@/types/api";

let sincronizando = false;

// Coordenadas guardadas con la foto del ítem, o null si no hubo GPS. Recibe el ítem de la cola.
function coordsDe(item: AccionPendiente): Coordenadas | null {
  return item.latitud != null && item.longitud != null ? { latitud: item.latitud, longitud: item.longitud } : null;
}

// Quién recibió la entrega encolada, si se registró. Recibe el ítem de la cola.
function receptorDe(item: AccionPendiente): Receptor | undefined {
  return item.receptorNombre && item.receptorDocumento
    ? { nombre: item.receptorNombre, documento: item.receptorDocumento }
    : undefined;
}

// Vacía la cola de sync si hay conexión. Recibe el QueryClient para invalidar queries al terminar.
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
          // La foto debe subirse antes de marcar ENTREGADO (el backend lo exige).
          if (item.fotoUri && !item.evidenciaSubida) {
            await subirEvidencia(item.pedidoId, item.fotoUri, coordsDe(item));
            await actualizar(item.id, { evidenciaSubida: true });
            item.evidenciaSubida = true;
          }
          if (!item.estadoAplicado) {
            await marcarEstadoParada(item.pedidoId, "ENTREGADO", undefined, receptorDe(item));
            await actualizar(item.id, { estadoAplicado: true });
            item.estadoAplicado = true;
          }
        } else {
          if (!item.estadoAplicado) {
            await marcarEstadoParada(item.pedidoId, "FALLIDO", item.motivo);
            await actualizar(item.id, { estadoAplicado: true });
            item.estadoAplicado = true;
          }
          if (!item.reporteCreado) {
            const reporte = await crearReporte(item.pedidoId, item.motivo ?? "Sin motivo", item.descripcion);
            await actualizar(item.id, { reporteCreado: true, reporteId: reporte.id });
            item.reporteCreado = true;
            item.reporteId = reporte.id;
          }
          // La foto que respalda la falla se adjunta al reporte ya creado (C29-01).
          if (item.fotoUri && item.reporteId && !item.evidenciaSubida) {
            await subirEvidenciaReporte(item.reporteId, item.fotoUri, coordsDe(item));
            await actualizar(item.id, { evidenciaSubida: true });
            item.evidenciaSubida = true;
          }
        }
        await quitar(item.id);
        huboCambios = true;
      } catch (e) {
        if (esErrorDeRed(e)) break;   // sin señal: conservamos el ítem (con su progreso) para el próximo intento
        await quitar(item.id);        // el servidor respondió (4xx/5xx): no reintentar
        huboCambios = true;
      }
    }
  } finally {
    sincronizando = false;
    if (huboCambios) {
      qc.invalidateQueries({ queryKey: claves.rutaActiva });
      qc.invalidateQueries({ queryKey: claves.manifiesto });
      qc.invalidateQueries({ queryKey: claves.misReportes });
    }
  }
}
