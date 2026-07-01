// Endpoints de la app del conductor; el backend filtra por token.
import { api } from "./client";
import type {
  RutaActiva,
  Manifiesto,
  Navegacion,
  GestionParada,
  CierreRuta,
  PerfilConductor,
  Reporte,
  Incidencia,
  ManifiestoRecojo,
  Recepcion,
  OptimizacionResultado,
  Coordenadas,
} from "@/types/api";

// Perfil del propio conductor (nombre, teléfono, DNI, vehículo). GET /conductor/perfil.
export async function obtenerPerfil(): Promise<PerfilConductor> {
  const { data } = await api.get<PerfilConductor>("/conductor/perfil");
  return data;
}

// Reporta la falla de un pedido. Recibe pedidoId, motivo y descripcion opcional.
export async function crearReporte(
  pedidoId: number,
  motivo: string,
  descripcion?: string
): Promise<Reporte> {
  const { data } = await api.post<Reporte>("/conductor/reportes", {
    pedido_id: pedidoId,
    motivo,
    descripcion: descripcion ?? null,
  });
  return data;
}

// Lista los reportes del propio conductor (para ver la respuesta del admin).
export async function obtenerMisReportes(): Promise<Reporte[]> {
  const { data } = await api.get<Reporte[]>("/conductor/reportes");
  return data;
}

// Obtiene los motivos de rechazo configurados por el admin.
export async function obtenerMotivos(): Promise<string[]> {
  const { data } = await api.get<string[]>("/conductor/motivos");
  return data;
}

// Resumen de la ruta activa. Devuelve: RutaActiva (lanza 404 si no tiene ruta).
export async function obtenerRutaActiva(): Promise<RutaActiva> {
  const { data } = await api.get<RutaActiva>("/conductor/ruta-activa");
  return data;
}

// Manifiesto con las paradas ordenadas por secuencia. Devuelve: Manifiesto.
export async function obtenerManifiesto(): Promise<Manifiesto> {
  const { data } = await api.get<Manifiesto>("/conductor/ruta-activa/manifiesto");
  return data;
}

// Waypoints (lat/lng) para el mapa. Devuelve: Navegacion.
export async function obtenerNavegacion(): Promise<Navegacion> {
  const { data } = await api.get<Navegacion>("/conductor/ruta-activa/navegacion");
  return data;
}

// Marca una parada como ENTREGADO o FALLIDO. Recibe pedidoId, estado y motivoFallo opcional.
export async function marcarEstadoParada(
  pedidoId: number,
  estado: "ENTREGADO" | "FALLIDO",
  motivoFallo?: string
): Promise<GestionParada> {
  const { data } = await api.patch<GestionParada>(`/conductor/paradas/${pedidoId}/estado`, {
    estado,
    motivo_fallo: motivoFallo ?? null,
  });
  return data;
}

// Sube la foto de evidencia (POD) por multipart. Recibe pedidoId y uri local de la imagen.
export async function subirEvidencia(pedidoId: number, uriFoto: string): Promise<GestionParada> {
  const nombre = uriFoto.split("/").pop() ?? `pod_${pedidoId}.jpg`;
  const form = new FormData();
  form.append("file", { uri: uriFoto, name: nombre, type: "image/jpeg" } as unknown as Blob);

  const { data } = await api.post<GestionParada>(
    `/conductor/paradas/${pedidoId}/evidencia`,
    form,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return data;
}

// Finaliza la ruta del día. Devuelve: CierreRuta con el resumen final.
export async function finalizarRuta(): Promise<CierreRuta> {
  const { data } = await api.post<CierreRuta>("/conductor/ruta-activa/finalizar");
  return data;
}

// Envía la posición actual al backend (mapa de flota). Recibe latitud y longitud.
export async function enviarUbicacion(latitud: number, longitud: number): Promise<void> {
  await api.post("/conductor/ubicacion", { latitud, longitud });
}

// Reporta una avería mecánica y pausa la ruta. Recibe descripcion, coords y flag puedeSolucionarSolo.
export async function reportarIncidencia(
  descripcion?: string,
  coords?: { latitud: number; longitud: number },
  puedeSolucionarSolo: boolean = false
): Promise<Incidencia> {
  const { data } = await api.post<Incidencia>("/conductor/incidencias", {
    tipo: "AVERIA_MECANICA",
    descripcion: descripcion ?? null,
    latitud: coords?.latitud ?? null,
    longitud: coords?.longitud ?? null,
    puede_solucionar_solo: puedeSolucionarSolo,
  });
  return data;
}

// Sube la foto de la avería por multipart. Recibe incidenciaId y uri local.
export async function subirEvidenciaIncidencia(incidenciaId: number, uriFoto: string): Promise<Incidencia> {
  const nombre = uriFoto.split("/").pop() ?? `inc_${incidenciaId}.jpg`;
  const form = new FormData();
  form.append("file", { uri: uriFoto, name: nombre, type: "image/jpeg" } as unknown as Blob);
  const { data } = await api.post<Incidencia>(
    `/conductor/incidencias/${incidenciaId}/evidencia`,
    form,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return data;
}

// Reanuda la ruta cerrando la incidencia. Recibe incidenciaId y nota opcional.
export async function reanudarRuta(incidenciaId: number, nota?: string): Promise<Incidencia> {
  const { data } = await api.post<Incidencia>(`/conductor/incidencias/${incidenciaId}/reanudar`, {
    nota: nota ?? null,
  });
  return data;
}

// Obtiene el manifiesto de la ruta de recojo activa.
export async function obtenerManifiestoRecojo(): Promise<ManifiestoRecojo> {
  const { data } = await api.get<ManifiestoRecojo>("/conductor/recojo/manifiesto");
  return data;
}

// Optimiza la ruta de recojo desde la ubicacion actual. Recibe rutaId y coords.
export async function optimizarRecojo(rutaId: number, coords: Coordenadas): Promise<OptimizacionResultado> {
  const { data } = await api.post<OptimizacionResultado>("/conductor/recojo/optimizar", {
    ruta_id: rutaId,
    latitud_actual_conductor: coords.latitud,
    longitud_actual_conductor: coords.longitud,
  });
  return data;
}

// Registra la recepcion con cantidad declarada y fotos de evidencia por multipart. Recibe recojoId, cantidad y uris.
export async function registrarRecepcion(recojoId: number, cantidad: number, uris: string[]): Promise<Recepcion> {
  const form = new FormData();
  form.append("cantidad_declarada", String(cantidad));
  uris.forEach((uri, i) => {
    const nombre = uri.split("/").pop() ?? `guia_${recojoId}_${i}.jpg`;
    form.append("files", { uri, name: nombre, type: "image/jpeg" } as unknown as Blob);
  });
  const { data } = await api.post<Recepcion>(
    `/conductor/recojo/${recojoId}/recepcion`,
    form,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return data;
}
