import { useEffect, useState } from "react";
import { obtenerEstadoAuditoria } from "./servicioAuditoria";

let promesaEstado = null;

export function useAuditoriaDisponible(rol) {
  const [activo, setActivo] = useState(false);

  useEffect(() => {
    if (rol !== "admin") return;
    let vivo = true;
    promesaEstado ??= obtenerEstadoAuditoria();
    promesaEstado.then((res) => {
      if (vivo) setActivo(Boolean(res?.activo));
    });
    return () => {
      vivo = false;
    };
  }, [rol]);

  return rol === "admin" && activo;
}
