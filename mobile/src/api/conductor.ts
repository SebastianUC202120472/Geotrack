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
