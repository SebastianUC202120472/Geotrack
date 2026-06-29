import { useState, useEffect, useCallback } from "react";
import { obtenerNotificaciones, marcarNotificacionesVistas } from "../services/api";

// Trae el historial de notificaciones del admin cada 20 s.
// Devuelve { no_vistas, items, marcarVistas }.
// Entrada: activo (boolean) — si es false, no hace polling (para roles sin campana).
export function useNotificaciones(activo) {
  const [data, setData] = useState({ no_vistas: 0, items: [] });

  // Pide el feed y actualiza el estado (setState en .then para evitar el error de lint).
  const traer = useCallback(() => {
    obtenerNotificaciones()
      .then((d) => setData(d))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!activo) return;
    let vivo = true;
    // Solo actualizamos si el componente sigue montado.
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

  // Llama al endpoint de marcado y luego refresca el feed para bajar no_vistas a 0.
  const marcarVistas = useCallback(() => {
    marcarNotificacionesVistas()
      .then(() => traer())
      .catch(() => {});
  }, [traer]);

  return { ...data, marcarVistas };
}
