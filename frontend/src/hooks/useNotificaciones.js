import { useState, useEffect, useCallback } from "react";
import { obtenerNotificaciones, marcarNotificacionesVistas } from "../services/api";

// Hook de notificaciones con polling cada 20 s. Recibe activo (boolean).
export function useNotificaciones(activo) {
  const [data, setData] = useState({ no_vistas: 0, items: [] });

  const traer = useCallback(() => {
    obtenerNotificaciones()
      .then((d) => setData(d))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!activo) return;
    let vivo = true;
    const traerSiVivo = () =>
      obtenerNotificaciones()
        .then((d) => { if (vivo) setData(d); })
        .catch(() => {});
    traerSiVivo();
    const id = setInterval(traerSiVivo, 20000);
    return () => {
      vivo = false;
      clearInterval(id);
    };
  }, [activo]);

  // Marca vistas y refresca el feed.
  const marcarVistas = useCallback(() => {
    marcarNotificacionesVistas()
      .then(() => traer())
      .catch(() => {});
  }, [traer]);

  return { ...data, marcarVistas };
}
