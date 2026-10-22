// Asistente virtual con IA del panel (Idea 1). Boton flotante que abre un chat:
// el usuario pregunta por texto o por voz y el asistente responde con datos reales
// del sistema, tablas, graficos y botones a la pantalla exacta del panel.
// Este modulo se carga en diferido y no aparece si el servicio esta apagado.
import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  History,
  LoaderCircle,
  Mic,
  Plus,
  SendHorizontal,
  Sparkles,
  Square,
  Trash2,
  Volume2,
  VolumeX,
  X,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import BloquesRespuesta from "./BloqueRespuesta";
import TextoSeguro from "./TextoSeguro";
import {
  eliminarConversacion,
  enviarPregunta,
  listarConversaciones,
  obtenerConversacion,
  obtenerEstado,
} from "./servicioAsistente";
import { callarVoz, lecturaDisponible, leerEnVozAlta, useGrabadora } from "./useVoz";

const SUGERENCIAS = {
  admin: [
    "Resumen del día",
    "¿Qué pedidos fallaron hoy?",
    "¿Dónde están los conductores ahorita?",
    "Grafícame los pedidos por estado",
  ],
  almacen: [
    "Resumen del día",
    "¿Cuántos pedidos observados hay?",
    "¿Qué retornos faltan llegar?",
    "¿Dónde están los conductores de recojo?",
  ],
};
const CLAVE_LEER_VOZ = "asistente_leer_voz";

let contador = 0;
// Genera un id local para los mensajes en pantalla. Sin input.
const idLocal = () => `local-${Date.now()}-${++contador}`;

// Lee una preferencia guardada en este navegador. Recibe la clave.
function leerPreferencia(clave) {
  try {
    return localStorage.getItem(clave) === "1";
  } catch {
    return false;
  }
}

// Formatea la fecha de una conversacion del historial. Recibe la fecha ISO (UTC).
function fechaCorta(iso) {
  const fecha = new Date(iso.endsWith("Z") ? iso : `${iso}Z`);
  return fecha.toLocaleString("es-PE", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

// Burbuja de un mensaje del chat. Recibe el mensaje, el texto de estado y onNavegar.
function Burbuja({ mensaje, estadoTexto, onNavegar }) {
  if (mensaje.rol === "usuario") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-brand-600 px-3.5 py-2 text-sm text-white">
          {mensaje.origen === "voz" && (
            <span className="mb-0.5 flex items-center gap-1 text-[11px] text-brand-100">
              <Mic size={11} /> Entendí:
            </span>
          )}
          <p className="whitespace-pre-wrap break-words">{mensaje.contenido}</p>
        </div>
      </div>
    );
  }
  return (
    <div className="flex justify-start">
      <div
        className={`max-w-[92%] rounded-2xl rounded-bl-md border px-3.5 py-2 text-sm text-slate-700 ${
          mensaje.error ? "border-danger/30 bg-danger-soft" : "border-slate-200 bg-white"
        }`}
      >
        {mensaje.pendiente && !mensaje.contenido && (
          <span className="flex items-center gap-2 text-slate-500">
            <LoaderCircle size={14} className="animate-spin" />
            {estadoTexto || "Pensando…"}
          </span>
        )}
        {mensaje.contenido && <TextoSeguro texto={mensaje.contenido} />}
        {mensaje.pendiente && mensaje.contenido && estadoTexto && (
          <span className="mt-1 flex items-center gap-2 text-xs text-slate-400">
            <LoaderCircle size={12} className="animate-spin" /> {estadoTexto}
          </span>
        )}
        <BloquesRespuesta bloques={mensaje.bloques} onNavegar={onNavegar} />
      </div>
    </div>
  );
}

// Widget flotante del asistente. Sin props: toma el rol de la sesion.
export default function AsistenteFlotante() {
  const { rol } = useAuth();
  const [servicio, setServicio] = useState(null);
  const [abierto, setAbierto] = useState(false);
  const [vista, setVista] = useState("chat");
  const [mensajes, setMensajes] = useState([]);
  const [conversacionId, setConversacionId] = useState(null);
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [estadoTexto, setEstadoTexto] = useState("");
  const [aviso, setAviso] = useState("");
  const [historial, setHistorial] = useState([]);
  const [leerVoz, setLeerVoz] = useState(() => leerPreferencia(CLAVE_LEER_VOZ));
  const cancelador = useRef(null);
  const finDelChat = useRef(null);
  const entrada = useRef(null);

  // Consulta una sola vez si el servicio esta activo.
  useEffect(() => {
    let vivo = true;
    obtenerEstado().then((e) => vivo && setServicio(e));
    return () => {
      vivo = false;
    };
  }, []);

  // Baja al ultimo mensaje cuando llega texto nuevo.
  useEffect(() => {
    finDelChat.current?.scrollIntoView({ block: "end" });
  }, [mensajes, estadoTexto]);

  // Enfoca la caja de texto al abrir y cierra con Escape.
  useEffect(() => {
    if (!abierto) return undefined;
    entrada.current?.focus();
    const alPresionar = (e) => e.key === "Escape" && setAbierto(false);
    window.addEventListener("keydown", alPresionar);
    return () => window.removeEventListener("keydown", alPresionar);
  }, [abierto, vista]);

  // Corta una respuesta en curso al desmontar el widget.
  useEffect(() => () => cancelador.current?.abort(), []);

  // Actualiza el ultimo mensaje del asistente. Recibe su id y una funcion de cambio.
  const actualizar = (id, cambio) =>
    setMensajes((lista) => lista.map((m) => (m.id === id ? { ...m, ...cambio(m) } : m)));

  // Envia una pregunta y va pintando la respuesta mientras llega. Recibe el texto y su origen.
  const enviar = useCallback(
    async (pregunta, origen = "texto") => {
      const limpia = (pregunta || "").trim();
      if (!limpia || enviando) return;
      setAviso("");
      setTexto("");
      setEnviando(true);
      setEstadoTexto("");
      callarVoz();
      const idRespuesta = idLocal();
      setMensajes((lista) => [
        ...lista,
        { id: idLocal(), rol: "usuario", contenido: limpia, origen },
        { id: idRespuesta, rol: "asistente", contenido: "", bloques: [], pendiente: true },
      ]);

      const controlador = new AbortController();
      cancelador.current = controlador;
      let respuestaFinal = "";
      try {
        await enviarPregunta(
          { mensaje: limpia, conversacionId, origen },
          (evento) => {
            if (evento.tipo === "inicio") setConversacionId(evento.conversacion_id);
            else if (evento.tipo === "estado") setEstadoTexto(evento.texto);
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
        setEnviando(false);
        setEstadoTexto("");
        cancelador.current = null;
      }
    },
    [conversacionId, enviando, leerVoz]
  );

  const grabadora = useGrabadora({
    vozServidor: servicio?.voz_servidor,
    maxSeg: servicio?.max_seg_voz || 60,
    onTexto: (t) => enviar(t, "voz"),
    onError: setAviso,
  });

  // Empieza una conversacion nueva. Sin input.
  const nuevaConversacion = () => {
    cancelador.current?.abort();
    callarVoz();
    setMensajes([]);
    setConversacionId(null);
    setVista("chat");
    setAviso("");
  };

  // Abre la lista de conversaciones anteriores. Sin input.
  const abrirHistorial = async () => {
    setVista("historial");
    try {
      setHistorial(await listarConversaciones());
    } catch (e) {
      setAviso(e.message);
    }
  };

  // Retoma una conversacion del historial. Recibe su id.
  const abrirConversacion = async (id) => {
    try {
      const c = await obtenerConversacion(id);
      setMensajes(
        c.mensajes.map((m) => ({ id: `srv-${m.id}`, rol: m.rol, contenido: m.contenido, bloques: m.bloques || [], origen: m.origen }))
      );
      setConversacionId(c.id);
      setVista("chat");
    } catch (e) {
      setAviso(e.message);
    }
  };

  // Borra una conversacion del historial. Recibe su id.
  const borrarConversacion = async (id) => {
    try {
      await eliminarConversacion(id);
      setHistorial((h) => h.filter((c) => c.id !== id));
      if (id === conversacionId) nuevaConversacion();
    } catch (e) {
      setAviso(e.message);
    }
  };

  // Activa o desactiva la lectura en voz alta. Sin input.
  const alternarLectura = () => {
    const nuevo = !leerVoz;
    setLeerVoz(nuevo);
    if (!nuevo) callarVoz();
    try {
      localStorage.setItem(CLAVE_LEER_VOZ, nuevo ? "1" : "0");
    } catch {
      // sin almacenamiento: solo dura esta sesion
    }
  };

  if (!servicio?.activo || !["admin", "almacen"].includes(rol)) return null;

  const maximo = servicio.max_caracteres || 1000;
  const sugerencias = SUGERENCIAS[rol] || [];

  return (
    <>
      {!abierto && (
        <button
          type="button"
          onClick={() => setAbierto(true)}
          aria-label="Abrir el asistente virtual"
          title="Asistente virtual"
          className="fixed bottom-5 right-5 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-brand-600 to-brand-700 text-white shadow-[0_8px_24px_rgba(37,99,235,0.45)] transition-transform hover:scale-105 focus:outline-none focus-visible:ring-4 focus-visible:ring-brand-300"
        >
          <Sparkles size={24} />
        </button>
      )}

      {abierto && (
        <section
          role="dialog"
          aria-label="Asistente virtual"
          className="fixed inset-0 z-50 flex flex-col bg-canvas sm:inset-auto sm:bottom-5 sm:right-5 sm:h-[min(660px,calc(100vh-2.5rem))] sm:w-[420px] sm:rounded-2xl sm:border sm:border-slate-200 sm:shadow-2xl"
        >
          <header className="flex items-center gap-2 border-b border-slate-200 bg-white px-3 py-2.5 sm:rounded-t-2xl">
            {vista === "historial" ? (
              <button type="button" onClick={() => setVista("chat")} aria-label="Volver al chat" className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100">
                <ArrowLeft size={18} />
              </button>
            ) : (
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-50 text-brand-600">
                <Sparkles size={17} />
              </span>
            )}
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-slate-900">{vista === "historial" ? "Conversaciones" : "Asistente GeoTrack"}</p>
              {vista === "chat" && <p className="text-[11px] text-slate-500">Pregúntame por pedidos, rutas, conductores y más</p>}
            </div>
            {lecturaDisponible && (
              <button
                type="button"
                onClick={alternarLectura}
                aria-pressed={leerVoz}
                aria-label={leerVoz ? "Dejar de leer las respuestas en voz alta" : "Leer las respuestas en voz alta"}
                title={leerVoz ? "Lectura en voz alta activada" : "Leer respuestas en voz alta"}
                className={`rounded-lg p-1.5 hover:bg-slate-100 ${leerVoz ? "text-brand-600" : "text-slate-400"}`}
              >
                {leerVoz ? <Volume2 size={18} /> : <VolumeX size={18} />}
              </button>
            )}
            <button type="button" onClick={abrirHistorial} aria-label="Ver conversaciones anteriores" title="Historial" className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100">
              <History size={18} />
            </button>
            <button type="button" onClick={nuevaConversacion} aria-label="Nueva conversación" title="Nueva conversación" className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100">
              <Plus size={18} />
            </button>
            <button type="button" onClick={() => setAbierto(false)} aria-label="Cerrar el asistente" className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100">
              <X size={18} />
            </button>
          </header>

          {aviso && (
            <p role="alert" className="border-b border-warning/30 bg-warning-soft px-3 py-2 text-xs text-warning-strong">
              {aviso}
            </p>
          )}

          {vista === "historial" ? (
            <div className="flex-1 overflow-y-auto p-3">
              {historial.length === 0 ? (
                <p className="py-10 text-center text-sm text-slate-500">Aún no tienes conversaciones guardadas.</p>
              ) : (
                <ul className="space-y-1.5">
                  {historial.map((c) => (
                    <li key={c.id} className="group flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 hover:border-brand-300">
                      <button type="button" onClick={() => abrirConversacion(c.id)} className="min-w-0 flex-1 text-left">
                        <p className="truncate text-sm font-medium text-slate-800">{c.titulo}</p>
                        <p className="text-[11px] text-slate-500">{fechaCorta(c.actualizada_en)}</p>
                      </button>
                      <button
                        type="button"
                        onClick={() => borrarConversacion(c.id)}
                        aria-label={`Borrar la conversación ${c.titulo}`}
                        className="rounded p-1 text-slate-400 hover:bg-danger-soft hover:text-danger"
                      >
                        <Trash2 size={15} />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ) : (
            <>
              <div className="flex-1 space-y-3 overflow-y-auto px-3 py-3" aria-live="polite">
                {mensajes.length === 0 && (
                  <div className="px-2 pt-6 text-center">
                    <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-brand-600">
                      <Sparkles size={24} />
                    </span>
                    <p className="mt-3 text-sm font-semibold text-slate-800">¿En qué te ayudo?</p>
                    <p className="mt-1 text-xs text-slate-500">
                      Escribe o graba tu pregunta con tus propias palabras. Respondo solo con datos reales del sistema.
                    </p>
                    <div className="mt-4 flex flex-col gap-1.5">
                      {sugerencias.map((s) => (
                        <button
                          key={s}
                          type="button"
                          onClick={() => enviar(s)}
                          className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-left text-sm text-slate-700 transition-colors hover:border-brand-300 hover:bg-brand-50"
                        >
                          {s}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {mensajes.map((m) => (
                  <Burbuja key={m.id} mensaje={m} estadoTexto={m.pendiente ? estadoTexto : ""} onNavegar={() => window.innerWidth < 640 && setAbierto(false)} />
                ))}
                <div ref={finDelChat} />
              </div>

              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  enviar(texto);
                }}
                className="border-t border-slate-200 bg-white p-2.5 sm:rounded-b-2xl"
              >
                {grabadora.grabando || grabadora.transcribiendo ? (
                  <div className="flex items-center gap-3 rounded-xl bg-brand-50 px-3 py-2.5">
                    {grabadora.grabando ? (
                      <>
                        <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-danger" />
                        <span className="flex-1 text-sm text-slate-700">
                          Grabando… {grabadora.segundos}s / {servicio.max_seg_voz}s
                        </span>
                        <button type="button" onClick={() => grabadora.detener(false)} className="text-xs font-semibold text-slate-500 hover:text-slate-700">
                          Cancelar
                        </button>
                        <button
                          type="button"
                          onClick={() => grabadora.detener(true)}
                          aria-label="Terminar y enviar el audio"
                          className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-600 text-white hover:bg-brand-700"
                        >
                          <Square size={14} fill="currentColor" />
                        </button>
                      </>
                    ) : (
                      <span className="flex items-center gap-2 text-sm text-slate-600">
                        <LoaderCircle size={15} className="animate-spin" /> Transcribiendo tu audio…
                      </span>
                    )}
                  </div>
                ) : (
                  <div className="flex items-end gap-2">
                    <textarea
                      ref={entrada}
                      value={texto}
                      onChange={(e) => setTexto(e.target.value.slice(0, maximo))}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault();
                          enviar(texto);
                        }
                      }}
                      rows={1}
                      placeholder="Escribe tu pregunta…"
                      aria-label="Pregunta para el asistente"
                      disabled={enviando}
                      className="max-h-32 min-h-[40px] flex-1 resize-none rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:border-brand-300 focus:bg-white focus:outline-none disabled:opacity-60"
                    />
                    {grabadora.disponible && !texto.trim() ? (
                      <button
                        type="button"
                        onClick={grabadora.iniciar}
                        disabled={enviando}
                        aria-label="Grabar un mensaje de voz"
                        title="Grabar mensaje de voz"
                        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-600 text-white transition-colors hover:bg-brand-700 disabled:opacity-50"
                      >
                        <Mic size={18} />
                      </button>
                    ) : (
                      <button
                        type="submit"
                        disabled={enviando || !texto.trim()}
                        aria-label="Enviar la pregunta"
                        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-600 text-white transition-colors hover:bg-brand-700 disabled:opacity-50"
                      >
                        {enviando ? <LoaderCircle size={18} className="animate-spin" /> : <SendHorizontal size={18} />}
                      </button>
                    )}
                  </div>
                )}
              </form>
            </>
          )}
        </section>
      )}
    </>
  );
}
