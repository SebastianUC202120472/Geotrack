// Endpoints que consume la app del conductor. El backend ya filtra por el
// usuario del token, así que solo se devuelven los datos del propio conductor.
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

// Reporta la falla de un pedido. Recibe: pedidoId (number), motivo (string),
// descripcion opcional (string). Devuelve: el Reporte creado.
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

// CUS-06: motivos de rechazo configurados por el admin (para el reporte de falla).
// Devuelve: lista de textos. Antes esta lista estaba fija en la app.
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

// Marca una parada como ENTREGADO o FALLIDO. Recibe: pedidoId (number),
// estado ("ENTREGADO" | "FALLIDO"), motivoFallo opcional (string).
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

// Sube la foto de evidencia (POD) por multipart. Recibe: pedidoId (number),
// uriFoto (string: uri local de la imagen). Devuelve: GestionParada con url_evidencia.
export async function subirEvidencia(pedidoId: number, uriFoto: string): Promise<GestionParada> {
  const nombre = uriFoto.split("/").pop() ?? `pod_${pedidoId}.jpg`;
  const form = new FormData();
  // En React Native el archivo se envía como { uri, name, type }.
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

// Envía la posición actual del conductor (mapa de flota en vivo del panel admin).
// Recibe: latitud y longitud. Best-effort: no devuelve datos.
export async function enviarUbicacion(latitud: number, longitud: number): Promise<void> {
  await api.post("/conductor/ubicacion", { latitud, longitud });
}

// CUS-30: reporta un auxilio mecánico sobre la ruta activa (la ruta queda pausada).
// Recibe: descripcion opcional, coords opcionales {latitud, longitud} y un flag
// puede_solucionar_solo (el conductor indica si puede resolver la avería él mismo).
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

// CUS-30: sube la foto de la avería (multipart). Recibe: id de incidencia y uri local.
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

// CUS-30: reanuda la ruta cerrando la incidencia. Recibe: id de incidencia y nota opcional.
export async function reanudarRuta(incidenciaId: number, nota?: string): Promise<Incidencia> {
  const { data } = await api.post<Incidencia>(`/conductor/incidencias/${incidenciaId}/reanudar`, {
    nota: nota ?? null,
  });
  return data;
}

// CUS-12: manifiesto de la ruta de recojo activa. Devuelve: ManifiestoRecojo.
export async function obtenerManifiestoRecojo(): Promise<ManifiestoRecojo> {
  const { data } = await api.get<ManifiestoRecojo>("/conductor/recojo/manifiesto");
  return data;
}

// CUS-19 (recojo): optimiza la ruta de recojo desde la ubicación actual. Recibe: rutaId y coords.
export async function optimizarRecojo(rutaId: number, coords: Coordenadas): Promise<OptimizacionResultado> {
  const { data } = await api.post<OptimizacionResultado>("/conductor/recojo/optimizar", {
    ruta_id: rutaId,
    latitud_actual_conductor: coords.latitud,
    longitud_actual_conductor: coords.longitud,
  });
  return data;
}

// CUS-12: registra la recepción (cantidad declarada + varias fotos de evidencia) por multipart.
// Recibe: recojoId, cantidad (>0) y un array de uris locales de las fotos
// (boleta/guía/bultos). Adjunta todas bajo el campo `files`. Devuelve: Recepcion.
export async function registrarRecepcion(recojoId: number, cantidad: number, uris: string[]): Promise<Recepcion> {
  const form = new FormData();
  form.append("cantidad_declarada", String(cantidad));
  // Un append por foto, todas bajo el mismo campo `files` (multipart múltiple).
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
