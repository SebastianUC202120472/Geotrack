// Motor de sincronización (CUS-27): vacía la cola en orden FIFO reenviando las
// funciones API ya existentes. Ante un error de RED (sin respuesta del servidor)
// detiene el flush y conserva el ítem; ante una respuesta HTTP del servidor lo
// quita (evita reintentos infinitos; marcarEstadoParada es idempotente).
import type { QueryClient } from "@tanstack/react-query";
import { listar, quitar, actualizar } from "@/store/colaSync";
import { estaOnline } from "@/hooks/useConexion";
import { marcarEstadoParada, subirEvidencia, crearReporte } from "@/api/conductor";
// MINOR 3: esErrorDeRed centralizado en client (sin duplicar).
import { esErrorDeRed } from "@/api/client";
import { claves } from "@/features/ruta/hooks";

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
          // Sub-paso 1: subir la foto POD (NO idempotente). Va PRIMERO porque el backend
          // exige que la evidencia exista antes de aceptar el ENTREGADO. Solo si hay foto
          // y no se subió aún.
          if (item.fotoUri && !item.evidenciaSubida) {
            await subirEvidencia(item.pedidoId, item.fotoUri);
            await actualizar(item.id, { evidenciaSubida: true });
            item.evidenciaSubida = true;
          }
          // Sub-paso 2: marcar ENTREGADO (idempotente en el backend). Solo si no se aplicó.
          if (!item.estadoAplicado) {
            await marcarEstadoParada(item.pedidoId, "ENTREGADO");
            await actualizar(item.id, { estadoAplicado: true });
            item.estadoAplicado = true;
          }
        } else {
          // Sub-paso 1: marcar FALLIDO (idempotente). Solo si no se aplicó.
          if (!item.estadoAplicado) {
            await marcarEstadoParada(item.pedidoId, "FALLIDO", item.motivo);
            await actualizar(item.id, { estadoAplicado: true });
            item.estadoAplicado = true;
          }
          // Sub-paso 2: crear el reporte (NO idempotente). Solo si no se creó.
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
