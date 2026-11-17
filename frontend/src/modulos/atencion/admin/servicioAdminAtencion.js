// Cliente HTTP de la administración del asistente de atención (solo administradores del panel).
// Usa el token del panel; el servicio lo valida contra el núcleo (/usuarios/yo).
import { getToken } from "../../../services/api";

const BASE =
  import.meta.env.VITE_ATENCION_URL || `${(import.meta.env.VITE_API_URL || "/api").replace(/\/$/, "")}/atencion`;

// Pide JSON a la administración. Recibe ruta, método y cuerpo opcional.
async function pedir(ruta, { method = "GET", body } = {}) {
  const headers = { Authorization: `Bearer ${getToken() || ""}` };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const respuesta = await fetch(`${BASE}/admin${ruta}`, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  const datos = await respuesta.json().catch(() => null);
  if (!respuesta.ok) {
    const detalle = datos?.detail;
    const mensaje = typeof detalle === "string" ? detalle
      : Array.isArray(detalle) ? detalle.map((d) => d.msg).join(" · ")
      : "El servicio de atención no respondió.";
    const error = new Error(mensaje);
    error.status = respuesta.status;
    throw error;
  }
  return datos;
}

// Artículos de la base de conocimiento. Recibe idioma y texto (opcionales).
export const listarArticulos = (idioma, q) => {
  const p = new URLSearchParams();
  if (idioma) p.set("idioma", idioma);
  if (q) p.set("q", q);
  return pedir(`/articulos${p.toString() ? `?${p}` : ""}`);
};
// Crea un artículo. Recibe sus datos.
export const crearArticulo = (datos) => pedir("/articulos", { method: "POST", body: datos });
// Edita un artículo. Recibe id y datos.
export const editarArticulo = (id, datos) => pedir(`/articulos/${id}`, { method: "PUT", body: datos });
// Activa o desactiva un artículo. Recibe id y activo.
export const cambiarEstadoArticulo = (id, activo) => pedir(`/articulos/${id}/estado`, { method: "POST", body: { activo } });
// Historial de versiones. Recibe el id.
export const historialArticulo = (id) => pedir(`/articulos/${id}/historial`);
// Qué artículos recuperaría el asistente para una pregunta. Recibe consulta e idioma.
export const probarBusqueda = (consulta, idioma) => pedir("/probar", { method: "POST", body: { consulta, idioma } });
// Bandeja de derivaciones. Recibe el estado (opcional).
export const listarDerivaciones = (estado) => pedir(`/derivaciones${estado ? `?estado=${estado}` : ""}`);
// Derivación con sus mensajes. Recibe el id.
export const detalleDerivacion = (id) => pedir(`/derivaciones/${id}`);
// Marca una derivación como atendida. Recibe el id.
export const atenderDerivacion = (id) => pedir(`/derivaciones/${id}/atender`, { method: "POST" });
// Métricas de los últimos días. Recibe cuántos días.
export const obtenerMetricas = (dias) => pedir(`/metricas?dias=${dias}`);
