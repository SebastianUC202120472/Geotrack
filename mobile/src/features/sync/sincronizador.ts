import type { QueryClient } from "@tanstack/react-query";
import { listar, quitar, actualizar } from "@/store/colaSync";
import { estaOnline } from "@/hooks/useConexion";
import { marcarEstadoParada, subirEvidencia, crearReporte } from "@/api/conductor";
import { esErrorDeRed } from "@/api/client";
import { claves } from "@/features/ruta/hooks";

let sincronizando = false;

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
            await subirEvidencia(item.pedidoId, item.fotoUri);
            await actualizar(item.id, { evidenciaSubida: true });
            item.evidenciaSubida = true;
          }
          if (!item.estadoAplicado) {
            await marcarEstadoParada(item.pedidoId, "ENTREGADO");
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
            await crearReporte(item.pedidoId, item.motivo ?? "Sin motivo", item.descripcion);
            await actualizar(item.id, { reporteCreado: true });
            item.reporteCreado = true;
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
