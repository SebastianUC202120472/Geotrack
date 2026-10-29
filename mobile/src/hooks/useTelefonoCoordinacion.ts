// Teléfono de coordinación para Ayuda y Reportar un error (EX-13).
import { useQuery } from "@tanstack/react-query";
import { obtenerContacto } from "@/api/conductor";

// Respaldo del build (EXPO_PUBLIC_COORDINACION_TEL) si el panel aún no lo configuró o no hay red.
const TELEFONO_DEL_BUILD = (process.env.EXPO_PUBLIC_COORDINACION_TEL ?? "").trim() || null;

// Devuelve el teléfono que configuró el administrador en Parámetros, o el del build, o null si no hay
// ninguno (las pantallas muestran entonces un aviso en vez de llamar a un número de ejemplo).
export function useTelefonoCoordinacion(): { telefono: string | null; cargando: boolean } {
  const consulta = useQuery({ queryKey: ["contacto"], queryFn: obtenerContacto, staleTime: 5 * 60_000 });
  return {
    telefono: consulta.data?.telefono_coordinacion || TELEFONO_DEL_BUILD,
    cargando: consulta.isLoading,
  };
}
