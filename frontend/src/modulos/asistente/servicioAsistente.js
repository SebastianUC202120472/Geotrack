// Cliente HTTP del asistente virtual. Habla con su propio servicio (/api/asistente),
// enviando el MISMO token del usuario conectado: el asistente no tiene permisos propios.
import { getToken } from "../../services/api";

const BASE =
  import.meta.env.VITE_ASISTENTE_URL || `${(import.meta.env.VITE_API_URL || "/api").replace(/\/$/, "")}/asistente`;

// Cabeceras con el token de la sesion. Recibe cabeceras extra opcionales.
function cabeceras(extra = {}) {
  const token = getToken();
  return token ? { ...extra, Authorization: `Bearer ${token}` } : extra;
}

// Lee el mensaje de error de una respuesta fallida. Recibe la respuesta fetch.
async function leerError(respuesta) {
  try {
    const datos = await respuesta.json();
    if (typeof datos?.detail === "string") return datos.detail;
    if (Array.isArray(datos?.detail)) return "El mensaje no es válido.";
  } catch {
    // respuesta sin JSON
  }
  if (respuesta.status === 401) return "Tu sesión expiró. Vuelve a iniciar sesión.";
  if (respuesta.status === 429) return "Vas muy rápido: espera un momento.";
  return "El asistente no está disponible en este momento.";
}

// Pide JSON al servicio. Recibe ruta y opciones de fetch.
async function pedirJson(ruta, opciones = {}) {
  const respuesta = await fetch(`${BASE}${ruta}`, { ...opciones, headers: cabeceras(opciones.headers) });
  if (!respuesta.ok) {
    const error = new Error(await leerError(respuesta));
    error.status = respuesta.status;
    throw error;
  }
  return respuesta.status === 204 ? null : respuesta.json();
}

// Dice si el asistente esta activo y si transcribe voz en el servidor. Sin input.
export async function obtenerEstado() {
  try {
    const respuesta = await fetch(`${BASE}/estado`);
    if (!respuesta.ok) return { activo: false };
    return await respuesta.json();
  } catch {
    return { activo: false };
  }
}

// Envia una pregunta y entrega cada evento del streaming a onEvento. Recibe datos, callback y señal de cancelacion.
export async function enviarPregunta({ mensaje, conversacionId, origen = "texto" }, onEvento, signal) {
  const respuesta = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: cabeceras({ "Content-Type": "application/json" }),
    body: JSON.stringify({ mensaje, conversacion_id: conversacionId || undefined, origen }),
    signal,
  });
  if (!respuesta.ok) throw new Error(await leerError(respuesta));

  const lector = respuesta.body.getReader();
  const decodificador = new TextDecoder();
  let pendiente = "";
  for (;;) {
    const { value, done } = await lector.read();
    if (done) break;
    pendiente += decodificador.decode(value, { stream: true });
    let corte;
    while ((corte = pendiente.indexOf("\n\n")) >= 0) {
      const bloque = pendiente.slice(0, corte);
      pendiente = pendiente.slice(corte + 2);
      if (bloque.startsWith("data: ")) {
        try {
          onEvento(JSON.parse(bloque.slice(6)));
        } catch {
          // evento mal formado: se ignora
        }
      }
    }
  }
}

// Sube un audio y devuelve el texto transcrito. Recibe el Blob grabado.
export async function transcribirAudio(audio) {
  const formulario = new FormData();
  const extension = audio.type.includes("mp4") ? "m4a" : audio.type.includes("ogg") ? "ogg" : "webm";
  formulario.append("audio", audio, `mensaje.${extension}`);
  const datos = await pedirJson("/voz", { method: "POST", body: formulario });
  return datos.texto;
}

// Confirma o cancela una accion propuesta por el asistente. Solo se llama desde el clic en la
// tarjeta; la cabecera propia del widget la exige el servidor. Recibe el id de la propuesta.
const CABECERA_ACCION = { "X-Asistente-Confirmacion": "si" };
export const confirmarAccion = (id) =>
  pedirJson(`/acciones/${encodeURIComponent(id)}/confirmar`, { method: "POST", headers: CABECERA_ACCION });
export const cancelarAccion = (id) =>
  pedirJson(`/acciones/${encodeURIComponent(id)}/cancelar`, { method: "POST", headers: CABECERA_ACCION });

export const listarConversaciones = () => pedirJson("/conversaciones");

// Mensajes de una conversacion propia. Recibe su id.
export const obtenerConversacion = (id) => pedirJson(`/conversaciones/${encodeURIComponent(id)}`);

// Borra una conversacion propia. Recibe su id.
export const eliminarConversacion = (id) =>
  pedirJson(`/conversaciones/${encodeURIComponent(id)}`, { method: "DELETE" });
