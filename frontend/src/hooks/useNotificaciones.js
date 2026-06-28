import { useState, useEffect } from "react";
import { obtenerNotificaciones } from "../services/api";

// Trae el feed de notificaciones del admin cada 20 s. Devuelve { total, items }.
// Entrada: activo (boolean) — si es false, no hace polling (para roles distintos de admin).
export function useNotificaciones(activo) {
  const [data, setData] = useState({ total: 0, items: [] });

  useEffect(() => {
    if (!activo) return;
    let vivo = true;
    const traer = () =>
      obtenerNotificaciones()
        .then((d) => { if (vivo) setData(d); })
        .catch(() => {});
    traer();
    const id = setInterval(traer, 20000);
    return () => {
      vivo = false;
      clearInterval(id);
    };
  }, [activo]);

  return data;
}
