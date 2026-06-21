// Hooks de React Query para el auxilio mecánico (CUS-30): reportar y reanudar.
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { reportarIncidencia, subirEvidenciaIncidencia, reanudarRuta } from "@/api/conductor";
import { claves } from "@/features/ruta/hooks";

// Reporta un auxilio (con foto y coords opcionales) y refresca la ruta (queda pausada).
// Devuelve: mutación que recibe { descripcion?, coords?, uriFoto? }.
export function useReportarAuxilio() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ descripcion, coords, uriFoto }: { descripcion?: string; coords?: { latitud: number; longitud: number }; uriFoto?: string }) => {
      const inc = await reportarIncidencia(descripcion, coords);
      if (uriFoto) return subirEvidenciaIncidencia(inc.id, uriFoto);
      return inc;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: claves.rutaActiva });
      qc.invalidateQueries({ queryKey: claves.manifiesto });
    },
  });
}

// Reanuda la ruta (cierra la incidencia) y refresca el estado.
// Devuelve: mutación que recibe { incidenciaId, nota? }.
export function useReanudarRuta() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ incidenciaId, nota }: { incidenciaId: number; nota?: string }) => reanudarRuta(incidenciaId, nota),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: claves.rutaActiva });
      qc.invalidateQueries({ queryKey: claves.manifiesto });
    },
  });
}
