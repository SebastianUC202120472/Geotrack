// Estado del servicio de atención para el menú del panel. Archivo liviano a propósito: el menú lo
// importa sin cargar la pantalla de administración. Si el servicio está apagado, la entrada no aparece.
import { useEffect, useState } from "react";
import { obtenerEstado } from "./servicioAtencion";

let promesa = null;

// Hook: true si el servicio de atención está activo y el rol es administrador. Recibe el rol.
export function useAtencionDisponible(rol) {
  const [activo, setActivo] = useState(false);
  useEffect(() => {
    if (rol !== "admin") return undefined;
    let vivo = true;
    promesa ??= obtenerEstado();
    promesa.then((e) => vivo && setActivo(Boolean(e?.activo)));
    return () => {
      vivo = false;
    };
  }, [rol]);
  return rol === "admin" && activo;
}
