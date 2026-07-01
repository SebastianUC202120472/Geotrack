// Componente sin UI: dispara sincronización al montar, al reconectar y al volver a primer plano.
import { useEffect } from "react";
import { AppState } from "react-native";
import NetInfo from "@react-native-community/netinfo";
import { useQueryClient } from "@tanstack/react-query";
import { sincronizar } from "@/features/sync/sincronizador";

export function MotorSync(): null {
  const qc = useQueryClient();
  useEffect(() => {
    sincronizar(qc);   // intento inicial (por si quedó cola de una sesión previa)
    const desNet = NetInfo.addEventListener((estado) => {
      if (estado.isConnected && estado.isInternetReachable !== false) sincronizar(qc);
    });
    const subApp = AppState.addEventListener("change", (s) => { if (s === "active") sincronizar(qc); });
    return () => { desNet(); subApp.remove(); };
  }, [qc]);
  return null;
}
