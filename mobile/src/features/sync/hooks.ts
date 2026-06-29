// Hooks de la cola de sincronización para la UI.
import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { contar, listar, suscribir } from "@/store/colaSync";
import { sincronizar } from "@/features/sync/sincronizador";

// Cuenta reactiva de acciones pendientes en la cola.
export function useCola(): { pendientes: number } {
  const [pendientes, setPendientes] = useState(0);
  useEffect(() => {
    let activo = true;
    const refrescar = () => contar().then((n) => activo && setPendientes(n)).catch(() => {});
    refrescar();
    const desuscribir = suscribir(refrescar);
    return () => { activo = false; desuscribir(); };
  }, []);
  return { pendientes };
}

// Mapa reactivo pedidoId -> estado encolado ("ENTREGADO" | "FALLIDO"). Sirve para
// superponer la cola sobre el manifiesto: una parada gestionada offline sigue
// mostrándose resuelta aunque el poll del servidor la devuelva como PENDIENTE.
export function usePendientesPorPedido(): Map<number, "ENTREGADO" | "FALLIDO"> {
  const [mapa, setMapa] = useState<Map<number, "ENTREGADO" | "FALLIDO">>(new Map());
  useEffect(() => {
    let activo = true;
    const refrescar = () =>
      listar()
        .then((items) => {
          if (!activo) return;
          const m = new Map<number, "ENTREGADO" | "FALLIDO">();
          items.forEach((i) => m.set(i.pedidoId, i.tipo === "ENTREGA" ? "ENTREGADO" : "FALLIDO"));
          setMapa(m);
        })
        .catch(() => {});
    refrescar();
    const desuscribir = suscribir(refrescar);
    return () => { activo = false; desuscribir(); };
  }, []);
  return mapa;
}

// Devuelve una función para sincronizar manualmente (botón "Sincronizar ahora").
export function useSincronizar(): () => void {
  const qc = useQueryClient();
  return () => { sincronizar(qc); };
}
