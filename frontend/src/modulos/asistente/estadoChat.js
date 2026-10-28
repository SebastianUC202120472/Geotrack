// Estado del chat compartido entre el widget flotante y la vista completa "Asistente IA":
// la conversacion sigue igual al pasar de uno a otro. Pertenece a la sesion que la empezo:
// si cambia el usuario conectado, se ve vacia y se reinicia al escribir.
import { useSyncExternalStore } from "react";
import { getToken } from "../../services/api";
import { enviarPregunta } from "./servicioAsistente";
import { callarVoz, leerEnVozAlta } from "./useVoz";

export { ROLES_ASISTENTE, useServicioAsistente } from "./estadoServicio";
export const RUTA_PAGINA = "/panel/asistente";

const VACIO = Object.freeze({ mensajes: [], conversacionId: null, enviando: false, estadoTexto: "" });
let estado = { ...VACIO, dueno: null };
const oyentes = new Set();
let cancelador = null;

let contador = 0;
// Genera un id local para los mensajes en pantalla. Sin input.
const idLocal = () => `local-${Date.now()}-${++contador}`;

// Foto actual del chat; vacia si pertenece a otra sesion. Sin input.
const instantanea = () => (estado.dueno === getToken() ? estado : VACIO);

// Aplica un cambio y avisa a las vistas. Recibe un objeto parcial o una funcion (estado) => parcial.
function cambiar(parcial) {
  const token = getToken();
  const base = estado.dueno === token ? estado : { ...VACIO, dueno: token };
  estado = { ...base, ...(typeof parcial === "function" ? parcial(base) : parcial) };
  oyentes.forEach((avisar) => avisar());
}

// Registra una vista. Si ya no queda ninguna (se cerro sesion), corta la respuesta en curso. Recibe el aviso.
function suscribir(avisar) {
  oyentes.add(avisar);
  return () => {
    oyentes.delete(avisar);
    if (oyentes.size === 0) cancelador?.abort();
  };
}

// Hook: devuelve { mensajes, conversacionId, enviando, estadoTexto }. Sin input.
export const useEstadoChat = () => useSyncExternalStore(suscribir, instantanea);

// Cambia un mensaje por su id. Recibe el id y una funcion (mensaje) => parcial.
const actualizar = (id, cambio) =>
  cambiar((e) => ({ mensajes: e.mensajes.map((m) => (m.id === id ? { ...m, ...cambio(m) } : m)) }));

// Envia una pregunta y va pintando la respuesta mientras llega. Recibe el texto, su origen y si se lee en voz alta.
export async function enviarMensaje(pregunta, { origen = "texto", leerVoz = false } = {}) {
  const limpia = (pregunta || "").trim();
  if (!limpia || instantanea().enviando) return;
  callarVoz();
  const idRespuesta = idLocal();
  cambiar((e) => ({
    enviando: true,
    estadoTexto: "",
    mensajes: [
      ...e.mensajes,
      { id: idLocal(), rol: "usuario", contenido: limpia, origen },
      { id: idRespuesta, rol: "asistente", contenido: "", bloques: [], pendiente: true },
    ],
  }));

  const controlador = new AbortController();
  cancelador = controlador;
  let respuestaFinal = "";
  try {
    await enviarPregunta(
      { mensaje: limpia, conversacionId: instantanea().conversacionId, origen },
      (evento) => {
        if (evento.tipo === "inicio") cambiar({ conversacionId: evento.conversacion_id });
        else if (evento.tipo === "estado") cambiar({ estadoTexto: evento.texto });
        else if (evento.tipo === "texto") {
          respuestaFinal += evento.texto;
          actualizar(idRespuesta, (m) => ({ contenido: m.contenido + evento.texto }));
        } else if (evento.tipo === "bloque") {
          actualizar(idRespuesta, (m) => ({ bloques: [...(m.bloques || []), evento.bloque] }));
        } else if (evento.tipo === "error") {
          actualizar(idRespuesta, () => ({ contenido: evento.texto, error: true }));
        }
      },
      controlador.signal
    );
    if (leerVoz && respuestaFinal) leerEnVozAlta(respuestaFinal);
  } catch (e) {
    if (e.name !== "AbortError") actualizar(idRespuesta, () => ({ contenido: e.message, error: true }));
  } finally {
    actualizar(idRespuesta, () => ({ pendiente: false }));
    if (cancelador === controlador) {
      cancelador = null;
      cambiar({ enviando: false, estadoTexto: "" });
    }
  }
}

// Cambia el estado de una tarjeta de accion en todos los mensajes (widget y vista completa ven lo mismo).
// Recibe el id de la propuesta y los campos a cambiar.
export function actualizarAccion(idAccion, cambios) {
  cambiar((e) => ({
    mensajes: e.mensajes.map((m) =>
      m.bloques?.some((b) => b.tipo === "accion" && b.id === idAccion)
        ? { ...m, bloques: m.bloques.map((b) => (b.tipo === "accion" && b.id === idAccion ? { ...b, ...cambios } : b)) }
        : m
    ),
  }));
}

// Empieza una conversacion nueva y corta la respuesta en curso. Sin input.
export function reiniciarChat() {
  cancelador?.abort();
  cancelador = null;
  callarVoz();
  cambiar({ ...VACIO });
}

// Carga una conversacion guardada. Recibe la conversacion del servidor.
export function cargarConversacion(c) {
  cancelador?.abort();
  cancelador = null;
  cambiar({
    ...VACIO,
    conversacionId: c.id,
    mensajes: c.mensajes.map((m) => ({
      id: `srv-${m.id}`,
      rol: m.rol,
      contenido: m.contenido,
      bloques: m.bloques || [],
      origen: m.origen,
    })),
  });
}
