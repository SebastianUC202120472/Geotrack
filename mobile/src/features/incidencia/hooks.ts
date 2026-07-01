// Hooks de React Query para el auxilio mecánico: reportar y reanudar.
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { reportarIncidencia, subirEvidenciaIncidencia, reanudarRuta } from "@/api/conductor";
import { claves } from "@/features/ruta/hooks";

// Reporta un auxilio (con foto y coords opcionales) y refresca la ruta. Recibe descripcion, coords, uriFoto, puedeSolucionarSolo.
export function useReportarAuxilio() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ descripcion, coords, uriFoto, puedeSolucionarSolo }: { descripcion?: string; coords?: { latitud: number; longitud: number }; uriFoto?: string; puedeSolucionarSolo?: boolean }) => {
      const inc = await reportarIncidencia(descripcion, coords, puedeSolucionarSolo ?? false);
      if (uriFoto) return subirEvidenciaIncidencia(inc.id, uriFoto);
      return inc;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: claves.rutaActiva });
      qc.invalidateQueries({ queryKey: claves.manifiesto });
    },
  });
}

// Reanuda la ruta cerrando la incidencia. Recibe incidenciaId y nota opcional.
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
