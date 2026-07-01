import { useEffect, useState } from "react";
import NetInfo from "@react-native-community/netinfo";

// Hook reactivo: devuelve { online } y se actualiza al cambiar la red.
export function useConexion(): { online: boolean } {
  const [online, setOnline] = useState(true);
  useEffect(() => {
    const desuscribir = NetInfo.addEventListener((estado) => {
      setOnline(Boolean(estado.isConnected) && estado.isInternetReachable !== false);
    });
    return () => desuscribir();
  }, []);
  return { online };
}

// Consulta imperativa (para decidir dentro de una mutación si encolar o enviar).
export async function estaOnline(): Promise<boolean> {
  const estado = await NetInfo.fetch();
  return Boolean(estado.isConnected) && estado.isInternetReachable !== false;
}
