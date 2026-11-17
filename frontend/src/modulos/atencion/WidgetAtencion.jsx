// Asistente virtual de atención al cliente (Idea 2): botón flotante en la landing y en el portal.
// Se carga en diferido y no aparece si el servicio está apagado (ATENCION_ENABLED=false).
// Flujo: aviso de privacidad (Ley 29733) → conversación anónima → respuestas en tiempo real, con:
//   - formulario de los últimos 4 dígitos del DNI (va directo al portal, nunca pasa por la IA),
//   - tarjetas de Confirmar/Cancelar para reprogramar o enviar datos de empresa (la IA solo propone),
//   - botón "Hablar con una persona" y mensajes de voz.
import { useCallback, useEffect, useRef, useState } from "react";
import { Bot, Mic, Send, Square, UserRound, Volume2, X } from "lucide-react";
import TextoAtencion from "./TextoAtencion";
import { textosDe } from "./textos";
import { lecturaDisponible, leerEnVozAlta, useVozAtencion } from "./useVozAtencion";
import {
  abrirConversacion, cancelarPropuesta, confirmarPropuesta, enviarMensaje, obtenerAviso, obtenerEstado,
  pedirPersona, tokenGuardado, verificarPedido,
} from "./servicioAtencion";
import "./atencion.css";

let siguienteId = 1;
// Id local de un elemento del chat. Sin parámetros.
const nuevoId = () => siguienteId++;

// Formulario de verificación del pedido con los últimos 4 dígitos del DNI. Recibe la tarjeta, textos y callbacks.
function TarjetaVerificar({ tarjeta, t, onVerificado, onCambio }) {
  const [digitos, setDigitos] = useState("");
  const [enviando, setEnviando] = useState(false);

  // Envía los dígitos al portal (no a la IA). Recibe el evento del formulario.
  const enviar = async (e) => {
    e.preventDefault();
    if (!/^\d{4}$/.test(digitos) || enviando) return;
    setEnviando(true);
    try {
      const r = await verificarPedido(tarjeta.codigo, digitos);
      onCambio({ estado: "ok", error: "" });
      onVerificado(r.mensaje_sugerido);
    } catch (err) {
      const d = err.detalle || {};
      const error =
        err.status === 401 && d.intentos_restantes != null ? t.intentos(d.intentos_restantes)
        : err.status === 429 && d.bloqueado_segundos ? t.bloqueado(d.bloqueado_segundos)
        : err.message;
      onCambio({ error });
    } finally {
      setDigitos("");
      setEnviando(false);
    }
  };

  if (tarjeta.estado === "ok") return null;
  return (
    <form className="atn-tarjeta" onSubmit={enviar}>
      <p className="atn-tarjeta-titulo">{t.verificarTitulo} {tarjeta.codigo}</p>
      <p className="atn-tarjeta-texto">{t.verificarTexto}</p>
      <div className="atn-fila">
        <input
          className="atn-input atn-digitos"
          inputMode="numeric"
          autoComplete="off"
          maxLength={4}
          pattern="\d{4}"
          aria-label={t.digitos}
          placeholder="••••"
          value={digitos}
          onChange={(e) => setDigitos(e.target.value.replace(/\D/g, "").slice(0, 4))}
        />
        <button type="submit" className="atn-boton" disabled={digitos.length !== 4 || enviando}>
          {enviando ? t.verificando : t.verificar}
        </button>
      </div>
      {tarjeta.error && <p className="atn-error" role="alert">{tarjeta.error}</p>}
    </form>
  );
}

// Tarjeta de una propuesta (reprogramar o contacto) con Confirmar y Cancelar. Recibe la tarjeta, textos y callbacks.
function TarjetaPropuesta({ tarjeta, t, onResultado, onCambio }) {
  const [enviando, setEnviando] = useState(false);
  const cerrada = tarjeta.estado && tarjeta.estado !== "PENDIENTE";

  // Confirma o cancela con un clic del visitante. Recibe si confirma (bool).
  const decidir = async (confirma) => {
    setEnviando(true);
    try {
      const r = confirma ? await confirmarPropuesta(tarjeta.id) : await cancelarPropuesta(tarjeta.id);
      onCambio({ estado: r.estado });
      onResultado(r.mensaje);
    } catch (err) {
      onCambio({ estado: "ERROR" });
      onResultado(err.message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className={`atn-tarjeta${cerrada ? " atn-tarjeta-cerrada" : ""}`}>
      <p className="atn-tarjeta-titulo">{tarjeta.titulo}</p>
      <ul className="atn-lineas">
        {tarjeta.lineas.map((l) => <li key={l}>{l}</li>)}
      </ul>
      {!cerrada && (
        <>
          <div className="atn-fila">
            <button type="button" className="atn-boton" disabled={enviando} onClick={() => decidir(true)}>{t.confirmar}</button>
            <button type="button" className="atn-boton atn-boton-sec" disabled={enviando} onClick={() => decidir(false)}>{t.cancelar}</button>
          </div>
          <p className="atn-nota">{t.vence}</p>
        </>
      )}
    </div>
  );
}

// Formulario "Hablar con una persona". Recibe textos y callbacks de enviar y cerrar.
function FormularioPersona({ t, onEnviado, onCerrar }) {
  const [motivo, setMotivo] = useState("");
  const [contacto, setContacto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState("");

  // Envía la derivación al equipo. Recibe el evento del formulario.
  const enviar = async (e) => {
    e.preventDefault();
    setEnviando(true);
    setError("");
    try {
      const r = await pedirPersona(motivo.trim(), contacto.trim());
      onEnviado(r.mensaje);
    } catch (err) {
      setError(err.status === 422 ? t.contactoInvalido : err.message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <form className="atn-tarjeta" onSubmit={enviar}>
      <p className="atn-tarjeta-titulo">{t.personaTitulo}</p>
      <p className="atn-tarjeta-texto">{t.personaTexto}</p>
      <input className="atn-input" aria-label={t.motivo} placeholder={t.motivo} maxLength={300} value={motivo}
             onChange={(e) => setMotivo(e.target.value)} />
      <input className="atn-input" aria-label={t.contacto} placeholder={t.contacto} maxLength={120} value={contacto}
             autoComplete="email" onChange={(e) => setContacto(e.target.value)} />
      {error && <p className="atn-error" role="alert">{error}</p>}
      <div className="atn-fila">
        <button type="submit" className="atn-boton" disabled={enviando}>{t.pedir}</button>
        <button type="button" className="atn-boton atn-boton-sec" onClick={onCerrar}>{t.cancelar}</button>
      </div>
    </form>
  );
}

// Aviso de privacidad que se acepta antes de chatear. Recibe el aviso, textos y callback de aceptar.
function AvisoPrivacidad({ aviso, t, onAceptar, abriendo, error }) {
  const [sitioWeb, setSitioWeb] = useState(""); // honeypot: una persona nunca lo ve ni lo llena
  if (!aviso) return <p className="atn-cargando">{error || t.cargando}</p>;
  return (
    <div className="atn-aviso">
      <p className="atn-aviso-titulo">{aviso.titulo}</p>
      <p>{aviso.resumen}</p>
      <ul>
        {aviso.puntos.map((p) => <li key={p}>{p}</li>)}
      </ul>
      <input className="atn-oculto" tabIndex={-1} autoComplete="off" aria-hidden="true" name="sitio_web"
             value={sitioWeb} onChange={(e) => setSitioWeb(e.target.value)} />
      {error && <p className="atn-error" role="alert">{error}</p>}
      <button type="button" className="atn-boton atn-boton-ancho" disabled={abriendo} onClick={() => onAceptar(sitioWeb)}>
        {aviso.aceptar}
      </button>
    </div>
  );
}

// Widget flotante de atención. Recibe lang ("es"|"en", el de la página) y pagina ("landing"|"portal").
export default function WidgetAtencion({ lang = "es", pagina = "landing" }) {
  const t = textosDe(lang);
  const [servicio, setServicio] = useState(null);
  const [abierto, setAbierto] = useState(false);
  // Aviso de privacidad cargado, con el idioma en que se pidió (si cambia el idioma, se pide otra vez).
  const [avisoCargado, setAvisoCargado] = useState(null);
  const aviso = avisoCargado?.lang === lang ? avisoCargado.datos : null;
  const [conversando, setConversando] = useState(() => Boolean(tokenGuardado()));
  const [abriendo, setAbriendo] = useState(false);
  const [error, setError] = useState("");
  const [elementos, setElementos] = useState([]);
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [idiomaRespuesta, setIdiomaRespuesta] = useState(lang);
  const [formPersona, setFormPersona] = useState(false);
  const lista = useRef(null);
  const entrada = useRef(null);
  const corte = useRef(null);

  // Estado del servicio: una sola consulta por carga de página.
  useEffect(() => {
    let vivo = true;
    obtenerEstado().then((e) => vivo && setServicio(e));
    return () => {
      vivo = false;
    };
  }, []);

  // Al abrir sin conversación, trae el aviso de privacidad en el idioma de la página.
  useEffect(() => {
    if (!abierto || conversando || aviso) return undefined;
    let vivo = true;
    obtenerAviso(lang)
      .then((datos) => vivo && setAvisoCargado({ lang, datos }))
      .catch(() => vivo && setError(t.errorAbrir));
    return () => {
      vivo = false;
    };
  }, [abierto, conversando, aviso, lang, t.errorAbrir]);

  // Cierra con Escape y baja la lista al último mensaje.
  useEffect(() => {
    if (!abierto) return undefined;
    // Cierra el chat con la tecla Escape. Recibe el evento del teclado.
    const alPresionar = (e) => e.key === "Escape" && setAbierto(false);
    window.addEventListener("keydown", alPresionar);
    return () => window.removeEventListener("keydown", alPresionar);
  }, [abierto]);
  useEffect(() => {
    lista.current?.scrollTo({ top: lista.current.scrollHeight, behavior: "smooth" });
  }, [elementos, formPersona]);

  // Agrega un elemento al chat. Recibe el elemento.
  const agregar = useCallback((el) => setElementos((xs) => [...xs, { id: nuevoId(), ...el }]), []);
  // Actualiza un elemento por id. Recibe id y cambios.
  const actualizar = useCallback((id, cambios) => setElementos((xs) => xs.map((x) => (x.id === id ? { ...x, ...cambios } : x))), []);

  // Acepta el aviso y abre la conversación. Recibe el honeypot.
  const aceptar = async (sitioWeb) => {
    setAbriendo(true);
    setError("");
    try {
      const r = await abrirConversacion({ version: aviso.version, idioma: lang, pagina, sitioWeb });
      setConversando(true);
      setElementos([{ id: nuevoId(), tipo: "mensaje", rol: "asistente", texto: r.saludo }]);
      setTimeout(() => entrada.current?.focus(), 50);
    } catch {
      setError(t.errorAbrir);
    } finally {
      setAbriendo(false);
    }
  };

  // Envía un mensaje y pinta la respuesta mientras llega. Recibe el texto y su origen (texto|voz).
  const enviar = useCallback(async (mensaje, origen = "texto") => {
    const limpio = (mensaje || "").trim();
    if (!limpio || enviando) return;
    setTexto("");
    agregar({ tipo: "mensaje", rol: "usuario", texto: limpio });
    const idRespuesta = nuevoId();
    setElementos((xs) => [...xs, { id: idRespuesta, tipo: "mensaje", rol: "asistente", texto: "", escribiendo: true }]);
    setEnviando(true);
    corte.current = new AbortController();
    try {
      await enviarMensaje({ mensaje: limpio, origen }, (ev) => {
        if (ev.tipo === "inicio") setIdiomaRespuesta(ev.idioma);
        else if (ev.tipo === "texto") setElementos((xs) => xs.map((x) => (x.id === idRespuesta ? { ...x, texto: x.texto + ev.texto } : x)));
        else if (ev.tipo === "reemplazar") actualizar(idRespuesta, { texto: ev.texto });
        else if (ev.tipo === "verificar") {
          setElementos((xs) => (xs.some((x) => x.tipo === "verificar" && x.codigo === ev.codigo && x.estado !== "ok")
            ? xs : [...xs, { id: nuevoId(), tipo: "verificar", codigo: ev.codigo }]));
        } else if (ev.tipo === "propuesta") agregar({ tipo: "propuesta", ...ev, idPropuesta: ev.id, estado: "PENDIENTE" });
        else if (ev.tipo === "ofrecer_derivacion") {
          setElementos((xs) => (xs.some((x) => x.tipo === "ofrecer") ? xs : [...xs, { id: nuevoId(), tipo: "ofrecer" }]));
        } else if (ev.tipo === "error") actualizar(idRespuesta, { texto: ev.mensaje });
      }, corte.current.signal);
    } catch (err) {
      if (err.status === 401) setConversando(false);
      actualizar(idRespuesta, { texto: err.message });
    } finally {
      actualizar(idRespuesta, { escribiendo: false });
      setEnviando(false);
    }
  }, [enviando, agregar, actualizar]);

  const voz = useVozAtencion({
    vozServidor: servicio?.voz_servidor,
    maxSeg: servicio?.max_seg_voz || 60,
    idioma: lang,
    onTexto: (dicho) => enviar(dicho, "voz"),
    onError: (e) => agregar({ tipo: "mensaje", rol: "sistema", texto: e === "microfono" ? t.sinMicrofono : e }),
  });

  // Corta una respuesta en curso si se cierra el widget.
  useEffect(() => () => corte.current?.abort(), []);

  if (!servicio?.activo) return null;

  return (
    <div className="atn-raiz" lang={lang}>
      {!abierto && (
        <button type="button" className="atn-lanzador" onClick={() => setAbierto(true)} aria-label={t.abrir} title={t.titulo}>
          <Bot size={28} aria-hidden="true" />
        </button>
      )}

      {abierto && (
        <section className="atn-ventana" role="dialog" aria-label={t.titulo}>
          <header className="atn-cabecera">
            <span className="atn-avatar" aria-hidden="true"><Bot size={20} /></span>
            <div className="atn-cabecera-textos">
              <p className="atn-titulo">{t.titulo}</p>
              <p className="atn-subtitulo">{t.subtitulo}</p>
            </div>
            <button type="button" className="atn-icono" onClick={() => setAbierto(false)} aria-label={t.cerrar}>
              <X size={20} />
            </button>
          </header>

          {!conversando ? (
            <div className="atn-cuerpo">
              <AvisoPrivacidad aviso={aviso} t={t} onAceptar={aceptar} abriendo={abriendo} error={error} />
            </div>
          ) : (
            <>
              <div className="atn-cuerpo" ref={lista} aria-live="polite">
                {elementos.length === 0 && <div className="atn-burbuja atn-asistente"><TextoAtencion texto={t.subtitulo} /></div>}
                {elementos.map((el) => {
                  if (el.tipo === "verificar") {
                    return <TarjetaVerificar key={el.id} tarjeta={el} t={t} onCambio={(c) => actualizar(el.id, c)}
                                             onVerificado={(m) => enviar(m)} />;
                  }
                  if (el.tipo === "propuesta") {
                    return <TarjetaPropuesta key={el.id} tarjeta={{ ...el, id: el.idPropuesta }} t={t}
                                             onCambio={(c) => actualizar(el.id, c)}
                                             onResultado={(m) => agregar({ tipo: "mensaje", rol: "asistente", texto: m })} />;
                  }
                  if (el.tipo === "ofrecer") {
                    return (
                      <div key={el.id} className="atn-ofrecer">
                        <span>{t.ofrecer}</span>
                        <button type="button" className="atn-boton atn-boton-sec" onClick={() => setFormPersona(true)}>{t.persona}</button>
                      </div>
                    );
                  }
                  return (
                    <div key={el.id} className={`atn-burbuja atn-${el.rol}`}>
                      {el.escribiendo && !el.texto ? <span className="atn-escribiendo">{t.pensando}</span> : <TextoAtencion texto={el.texto} />}
                      {el.rol === "asistente" && el.texto && !el.escribiendo && lecturaDisponible && (
                        <button type="button" className="atn-leer" onClick={() => leerEnVozAlta(el.texto, idiomaRespuesta)} aria-label={t.leer} title={t.leer}>
                          <Volume2 size={14} />
                        </button>
                      )}
                    </div>
                  );
                })}
                {formPersona && (
                  <FormularioPersona t={t} onCerrar={() => setFormPersona(false)}
                                     onEnviado={(m) => { setFormPersona(false); agregar({ tipo: "mensaje", rol: "asistente", texto: m }); }} />
                )}
              </div>

              <form className="atn-pie" onSubmit={(e) => { e.preventDefault(); enviar(texto); }}>
                <button type="button" className="atn-persona" onClick={() => setFormPersona(true)} disabled={formPersona}>
                  <UserRound size={14} aria-hidden="true" /> {t.persona}
                </button>
                <div className="atn-fila">
                  <textarea
                    ref={entrada}
                    className="atn-input atn-entrada"
                    rows={1}
                    maxLength={servicio.max_caracteres || 500}
                    placeholder={voz.grabando ? t.escuchando : voz.transcribiendo ? t.transcribiendo : t.escribir}
                    aria-label={t.escribir}
                    value={texto}
                    disabled={voz.grabando || voz.transcribiendo}
                    onChange={(e) => setTexto(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        enviar(texto);
                      }
                    }}
                  />
                  {voz.disponible && !texto.trim() ? (
                    <button type="button" className={`atn-icono-envio${voz.grabando ? " atn-grabando" : ""}`}
                            onClick={() => (voz.grabando ? voz.detener(true) : voz.iniciar())}
                            disabled={enviando || voz.transcribiendo} aria-label={voz.grabando ? t.detener : t.grabar}>
                      {voz.grabando ? <Square size={18} /> : <Mic size={18} />}
                    </button>
                  ) : (
                    <button type="submit" className="atn-icono-envio" disabled={enviando || !texto.trim()} aria-label={t.enviar}>
                      <Send size={18} />
                    </button>
                  )}
                </div>
              </form>
            </>
          )}
        </section>
      )}
    </div>
  );
}
