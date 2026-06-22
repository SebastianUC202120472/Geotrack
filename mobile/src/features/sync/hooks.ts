// Hooks de la cola de sincronización para la UI.
import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { contar, suscribir } from "@/store/colaSync";
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

// Devuelve una función para sincronizar manualmente (botón "Sincronizar ahora").
export function useSincronizar(): () => void {
  const qc = useQueryClient();
  return () => { sincronizar(qc); };
}
