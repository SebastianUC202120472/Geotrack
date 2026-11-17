// Cliente HTTP del asistente de atención al cliente (Idea 2). Habla con su propio servicio
// (/api/atencion). El visitante es anónimo: NO se envía el token del panel; lo identifica el
// token firmado de su conversación, que se guarda solo en esta pestaña (sessionStorage).
const BASE =
  import.meta.env.VITE_ATENCION_URL || `${(import.meta.env.VITE_API_URL || "/api").replace(/\/$/, "")}/atencion`;
const CLAVE_TOKEN = "atn_conversacion";

// Token de la conversación de esta pestaña (o null). Sin parámetros.
export function tokenGuardado() {
  try {
    return sessionStorage.getItem(CLAVE_TOKEN);
  } catch {
    return null;
  }
}

// Guarda u olvida el token de la conversación. Recibe el token (o null para olvidarlo).
export function guardarToken(token) {
  try {
    if (token) sessionStorage.setItem(CLAVE_TOKEN, token);
    else sessionStorage.removeItem(CLAVE_TOKEN);
  } catch {
    // sin almacenamiento: la conversación dura lo que la página abierta
  }
}

// Cabeceras con el token de la conversación. Recibe cabeceras extra.
function cabeceras(extra = {}) {
  const token = tokenGuardado();
  return token ? { ...extra, "X-Conversacion": token } : extra;
}

// Error con estado HTTP y detalle del servidor. Recibe la respuesta fetch.
async function errorDe(respuesta) {
  let detalle = null;
  try {
    detalle = (await respuesta.json())?.detail;
  } catch {
    // respuesta sin JSON
  }
  const texto = typeof detalle === "string" ? detalle : detalle?.mensaje;
  const error = new Error(texto || (respuesta.status === 429 ? "Vas muy rápido: espera un momento." : "El asistente no está disponible ahora."));
  error.status = respuesta.status;
  error.detalle = detalle;
  if (respuesta.status === 401) guardarToken(null); // conversación vencida: se abre otra
  return error;
}

// Pide JSON al servicio. Recibe ruta y opciones de fetch.
async function pedirJson(ruta, opciones = {}) {
  const respuesta = await fetch(`${BASE}${ruta}`, { ...opciones, headers: cabeceras(opciones.headers) });
  if (!respuesta.ok) throw await errorDe(respuesta);
  return respuesta.json();
}

// Dice si el chat está activo (si no, el widget no aparece). Sin parámetros.
export async function obtenerEstado() {
  try {
    const respuesta = await fetch(`${BASE}/estado`);
    return respuesta.ok ? await respuesta.json() : { activo: false };
  } catch {
    return { activo: false };
  }
}

// Aviso de privacidad en el idioma pedido. Recibe "es" o "en".
export const obtenerAviso = (idioma) => pedirJson(`/privacidad?idioma=${idioma === "en" ? "en" : "es"}`);

// Abre una conversación tras aceptar el aviso. Recibe la versión del aviso, idioma, página y el honeypot.
export async function abrirConversacion({ version, idioma, pagina, sitioWeb }) {
  const datos = await pedirJson("/conversaciones", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ acepta_privacidad: true, version_aviso: version, idioma, pagina, sitio_web: sitioWeb || null }),
  });
  guardarToken(datos.token);
  return datos;
}

// Envía un mensaje y entrega cada evento del streaming a onEvento. Recibe mensaje, origen, callback y señal.
export async function enviarMensaje({ mensaje, origen = "texto" }, onEvento, signal) {
  const respuesta = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: cabeceras({ "Content-Type": "application/json" }),
    body: JSON.stringify({ mensaje, origen }),
    signal,
  });
  if (!respuesta.ok) throw await errorDe(respuesta);
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

// Verifica un pedido con los últimos 4 dígitos del DNI (va directo al portal, no pasa por la IA). Recibe código y dígitos.
export const verificarPedido = (codigo, digitos) =>
  pedirJson("/verificar", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ codigo, digitos }) });

// Confirma una propuesta (reprogramar o contacto). Recibe su id.
export const confirmarPropuesta = (id) => pedirJson(`/acciones/${encodeURIComponent(id)}/confirmar`, { method: "POST" });

// Cancela una propuesta. Recibe su id.
export const cancelarPropuesta = (id) => pedirJson(`/acciones/${encodeURIComponent(id)}/cancelar`, { method: "POST" });

// Pide hablar con una persona. Recibe el motivo y un contacto opcional (correo o teléfono).
export const pedirPersona = (motivo, contacto) =>
  pedirJson("/derivaciones", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ motivo: motivo || null, contacto: contacto || null }),
  });

// Sube un audio y devuelve {texto, idioma}. Recibe el Blob grabado.
export async function transcribirAudio(audio) {
  const formulario = new FormData();
  const extension = audio.type.includes("mp4") ? "m4a" : audio.type.includes("ogg") ? "ogg" : "webm";
  formulario.append("audio", audio, `mensaje.${extension}`);
  return pedirJson("/voz", { method: "POST", body: formulario });
}
