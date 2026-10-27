// Chat del asistente virtual: cabecera, historial, mensajes y caja de texto/voz.
// Se usa en el widget flotante (modo "flotante") y en la vista completa del menu
// lateral (modo "pagina", con graficos mas grandes y enlaces a la fuente).
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowDown,
  ArrowLeft,
  History,
  LoaderCircle,
  Maximize2,
  Mic,
  Plus,
  SendHorizontal,
  Square,
  Trash2,
  Volume2,
  VolumeX,
  X,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import BloquesRespuesta from "./BloqueRespuesta";
import IconoAsistente from "./IconoAsistente";
import TextoSeguro from "./TextoSeguro";
import { cargarConversacion, enviarMensaje, reiniciarChat, RUTA_PAGINA, useEstadoChat } from "./estadoChat";
import { eliminarConversacion, listarConversaciones, obtenerConversacion } from "./servicioAsistente";
import { callarVoz, lecturaDisponible, useGrabadora } from "./useVoz";

const SUGERENCIAS = {
  admin: [
    "Resumen del día",
    "¿Qué pedidos fallaron hoy y por qué?",
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
// Distancia (px) al final del chat por debajo de la cual se considera que el usuario esta "abajo".
const UMBRAL_ABAJO = 80;

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

// Burbuja de un mensaje del chat. Recibe el mensaje, el texto de estado, onNavegar y si es la vista grande.
function Burbuja({ mensaje, estadoTexto, onNavegar, grande }) {
  if (mensaje.rol === "usuario") {
    return (
      <div className="flex justify-end">
        <div className={`${grande ? "max-w-[70%]" : "max-w-[85%]"} rounded-2xl rounded-br-md bg-brand-600 px-3.5 py-2 text-sm text-white`}>
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
        className={`${grande ? "w-full max-w-4xl" : "max-w-[92%]"} rounded-2xl rounded-bl-md border px-3.5 py-2 text-sm text-slate-700 ${
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
        <BloquesRespuesta bloques={mensaje.bloques} onNavegar={onNavegar} grande={grande} />
      </div>
    </div>
  );
}

// Chat completo. Recibe modo ("flotante" | "pagina"), servicio (estado del backend) y onCerrar (solo flotante).
export default function ChatAsistente({ modo = "flotante", servicio, onCerrar }) {
  const grande = modo === "pagina";
  const { rol } = useAuth();
  const navigate = useNavigate();
  const { mensajes, enviando, estadoTexto, conversacionId } = useEstadoChat();
  const [vista, setVista] = useState("chat");
  const [texto, setTexto] = useState("");
  const [aviso, setAviso] = useState("");
  const [historial, setHistorial] = useState([]);
  const [leerVoz, setLeerVoz] = useState(() => leerPreferencia(CLAVE_LEER_VOZ));
  const [lejosDelFinal, setLejosDelFinal] = useState(false);
  const lista = useRef(null);
  const contenido = useRef(null);
  const pegadoAbajo = useRef(true);
  const entrada = useRef(null);

  // Lleva el chat al ultimo mensaje. Sin input.
  const bajar = useCallback(() => {
    const el = lista.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, []);

  // Al abrir el chat (o volver del historial) siempre se muestra el ultimo mensaje.
  useLayoutEffect(() => {
    if (vista !== "chat") return;
    pegadoAbajo.current = true;
    bajar();
  }, [vista, bajar]);

  // Con texto nuevo se baja solo si el usuario no subio a leer mensajes anteriores.
  useLayoutEffect(() => {
    if (pegadoAbajo.current) bajar();
  }, [mensajes, estadoTexto, bajar]);

  // Tablas y graficos terminan de medirse despues de pintarse: si el alto cambia y el
  // usuario estaba abajo, se vuelve a bajar.
  useEffect(() => {
    if (vista !== "chat" || !contenido.current || typeof ResizeObserver === "undefined") return undefined;
    const observador = new ResizeObserver(() => pegadoAbajo.current && bajar());
    observador.observe(contenido.current);
    return () => observador.disconnect();
  }, [vista, bajar]);

  // Enfoca la caja de texto al abrir el chat.
  useEffect(() => {
    if (vista === "chat") entrada.current?.focus();
  }, [vista]);

  // Recuerda si el usuario esta abajo o subio a proposito. Sin input (evento de scroll).
  const alDesplazar = () => {
    const el = lista.current;
    if (!el) return;
    const abajo = el.scrollHeight - el.scrollTop - el.clientHeight < UMBRAL_ABAJO;
    pegadoAbajo.current = abajo;
    setLejosDelFinal(!abajo);
  };

  // Envia la pregunta y vuelve al final del chat. Recibe el texto y su origen.
  const enviar = (pregunta, origen = "texto") => {
    if (!(pregunta || "").trim() || enviando) return;
    setAviso("");
    setTexto("");
    pegadoAbajo.current = true;
    setLejosDelFinal(false);
    enviarMensaje(pregunta, { origen, leerVoz });
  };

  const grabadora = useGrabadora({
    vozServidor: servicio?.voz_servidor,
    maxSeg: servicio?.max_seg_voz || 60,
    onTexto: (t) => enviar(t, "voz"),
    onError: setAviso,
  });

  // Empieza una conversacion nueva. Sin input.
  const nuevaConversacion = () => {
    reiniciarChat();
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
      cargarConversacion(await obtenerConversacion(id));
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

  // En el celular, al ir a otra pantalla se cierra el widget para que se vea. Sin input.
  const alNavegar = () => {
    if (!grande && window.innerWidth < 640) onCerrar?.();
  };

  const maximo = servicio?.max_caracteres || 1000;
  const sugerencias = SUGERENCIAS[rol] || [];
  const boton = "rounded-lg p-1.5 text-slate-500 hover:bg-slate-100";

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header className={`flex items-center gap-2 border-b border-slate-200 bg-white px-3 py-2.5 ${grande ? "rounded-t-2xl" : "sm:rounded-t-2xl"}`}>
        {vista === "historial" ? (
          <button type="button" onClick={() => setVista("chat")} aria-label="Volver al chat" className={boton}>
            <ArrowLeft size={18} />
          </button>
        ) : (
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-50 text-brand-600">
            <IconoAsistente size={18} />
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
        <button type="button" onClick={abrirHistorial} aria-label="Ver conversaciones anteriores" title="Historial" className={boton}>
          <History size={18} />
        </button>
        <button type="button" onClick={nuevaConversacion} aria-label="Nueva conversación" title="Nueva conversación" className={boton}>
          <Plus size={18} />
        </button>
        {!grande && (
          <>
            <button
              type="button"
              onClick={() => {
                navigate(RUTA_PAGINA);
                onCerrar?.();
              }}
              aria-label="Abrir el asistente en vista completa"
              title="Vista completa"
              className={`hidden sm:block ${boton}`}
            >
              <Maximize2 size={17} />
            </button>
            <button type="button" onClick={onCerrar} aria-label="Cerrar el asistente" className={boton}>
              <X size={18} />
            </button>
          </>
        )}
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
          <div className="relative min-h-0 flex-1">
            <div ref={lista} onScroll={alDesplazar} className="h-full overflow-y-auto px-3 py-3" aria-live="polite">
              <div ref={contenido} className={`space-y-3 ${grande ? "mx-auto max-w-5xl" : ""}`}>
                {mensajes.length === 0 && (
                  <div className="px-2 pt-6 text-center">
                    <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-brand-600">
                      <IconoAsistente size={26} />
                    </span>
                    <p className="mt-3 text-sm font-semibold text-slate-800">¿En qué te ayudo?</p>
                    <p className="mt-1 text-xs text-slate-500">
                      Escribe o graba tu pregunta con tus propias palabras. Respondo solo con datos reales del sistema.
                    </p>
                    <div className={`mt-4 ${grande ? "mx-auto grid max-w-2xl gap-2 sm:grid-cols-2" : "flex flex-col gap-1.5"}`}>
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
                  <Burbuja key={m.id} mensaje={m} estadoTexto={m.pendiente ? estadoTexto : ""} onNavegar={alNavegar} grande={grande} />
                ))}
              </div>
            </div>
            {lejosDelFinal && mensajes.length > 0 && (
              <button
                type="button"
                onClick={() => {
                  pegadoAbajo.current = true;
                  setLejosDelFinal(false);
                  bajar();
                }}
                aria-label="Bajar al último mensaje"
                title="Bajar al último mensaje"
                className="absolute bottom-3 left-1/2 flex h-8 w-8 -translate-x-1/2 items-center justify-center rounded-full border border-slate-200 bg-white text-brand-600 shadow-md hover:bg-brand-50"
              >
                <ArrowDown size={16} />
              </button>
            )}
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              enviar(texto);
            }}
            className={`border-t border-slate-200 bg-white p-2.5 ${grande ? "rounded-b-2xl" : "sm:rounded-b-2xl"}`}
          >
            <div className={grande ? "mx-auto max-w-5xl" : ""}>
              {grabadora.grabando || grabadora.transcribiendo ? (
                <div className="flex items-center gap-3 rounded-xl bg-brand-50 px-3 py-2.5">
                  {grabadora.grabando ? (
                    <>
                      <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-danger" />
                      <span className="flex-1 text-sm text-slate-700">
                        Grabando… {grabadora.segundos}s / {servicio?.max_seg_voz}s
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
            </div>
          </form>
        </>
      )}
    </div>
  );
}
