// Estado del servicio del asistente (activo, voz, limites). Se consulta UNA vez por carga
// del panel y lo comparten el boton flotante, la vista completa y la entrada del menu
// lateral. Si el servicio esta apagado (ASISTENTE_ENABLED=false) o caido, activo es false.
// Archivo liviano a proposito: el menu lo importa sin cargar el chat.
import { useEffect, useState } from "react";
import { obtenerEstado } from "./servicioAsistente";

export const ROLES_ASISTENTE = ["admin", "almacen"];
let promesaServicio = null;

// Hook: estado del servicio; null mientras se consulta. Sin input.
export function useServicioAsistente() {
  const [servicio, setServicio] = useState(null);
  useEffect(() => {
    let vivo = true;
    promesaServicio ??= obtenerEstado();
    promesaServicio.then((e) => vivo && setServicio(e));
    return () => {
      vivo = false;
    };
  }, []);
  return servicio;
}

// Hook: dice si el asistente esta disponible para un rol (false mientras se consulta). Recibe el rol.
export function useAsistenteDisponible(rol) {
  const servicio = useServicioAsistente();
  return Boolean(servicio?.activo) && ROLES_ASISTENTE.includes(rol);
}
