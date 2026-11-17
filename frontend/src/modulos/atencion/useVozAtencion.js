// Voz del widget de atención: grabar un mensaje (como en WhatsApp) y leer la respuesta en voz alta.
// Adaptado del asistente del panel (no se importa de allí, para no acoplar los módulos). Diferencias:
// funciona en español o inglés según el idioma del visitante y devuelve también el idioma detectado.
// - Con transcripción en el servidor (Whisper): se graba con MediaRecorder y el audio se descarta tras subirlo.
// - Sin ella: dictado del navegador (Web Speech API, mejor en Chrome y Edge).
import { useCallback, useEffect, useRef, useState } from "react";
import { transcribirAudio } from "./servicioAtencion";

const Reconocimiento = typeof window !== "undefined" ? window.SpeechRecognition || window.webkitSpeechRecognition : null;
const LOCALES = { es: "es-PE", en: "en-US" };

// Elige un formato de grabación que soporte el navegador. Sin parámetros.
function formatoGrabacion() {
  if (typeof MediaRecorder === "undefined") return null;
  for (const tipo of ["audio/webm;codecs=opus", "audio/ogg;codecs=opus", "audio/mp4"]) {
    if (MediaRecorder.isTypeSupported?.(tipo)) return tipo;
  }
  return "";
}

// Hook de grabación. Recibe { vozServidor, maxSeg, idioma, onTexto(texto), onError(mensaje) }.
export function useVozAtencion({ vozServidor, maxSeg = 60, idioma = "es", onTexto, onError }) {
  const [grabando, setGrabando] = useState(false);
  const [transcribiendo, setTranscribiendo] = useState(false);
  const [segundos, setSegundos] = useState(0);
  const grabadora = useRef(null);
  const reconocedor = useRef(null);
  const trozos = useRef([]);
  const reloj = useRef(null);
  const limite = useRef(null);
  const cancelado = useRef(false);

  const conServidor = Boolean(vozServidor && navigator.mediaDevices?.getUserMedia && formatoGrabacion() !== null);
  const disponible = conServidor || Boolean(Reconocimiento);

  // Detiene el contador y el corte automático. Sin parámetros.
  const pararReloj = () => {
    clearInterval(reloj.current);
    clearTimeout(limite.current);
    reloj.current = null;
    limite.current = null;
  };

  // Termina la grabación; si enviar es false, descarta el audio. Recibe enviar (bool).
  const detener = useCallback((enviar = true) => {
    cancelado.current = !enviar;
    pararReloj();
    if (grabadora.current?.state === "recording") grabadora.current.stop();
    if (reconocedor.current) {
      if (enviar) reconocedor.current.stop();
      else reconocedor.current.abort();
    }
    setGrabando(false);
  }, []);

  // Empieza a grabar o a dictar. Sin parámetros.
  const iniciar = useCallback(async () => {
    if (grabando || transcribiendo) return;
    cancelado.current = false;
    setSegundos(0);

    if (conServidor) {
      let flujo;
      try {
        flujo = await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch {
        onError?.("microfono");
        return;
      }
      const tipo = formatoGrabacion();
      const rec = new MediaRecorder(flujo, tipo ? { mimeType: tipo, audioBitsPerSecond: 32000 } : undefined);
      trozos.current = [];
      rec.ondataavailable = (e) => e.data.size && trozos.current.push(e.data);
      rec.onstop = async () => {
        flujo.getTracks().forEach((t) => t.stop());
        const audio = new Blob(trozos.current, { type: rec.mimeType || "audio/webm" });
        trozos.current = [];
        if (cancelado.current || audio.size < 1000) return;
        setTranscribiendo(true);
        try {
          const { texto } = await transcribirAudio(audio);
          onTexto?.(texto);
        } catch (e) {
          onError?.(e.message);
        } finally {
          setTranscribiendo(false);
        }
      };
      grabadora.current = rec;
      rec.start();
    } else if (Reconocimiento) {
      const rec = new Reconocimiento();
      rec.lang = LOCALES[idioma] || LOCALES.es;
      rec.interimResults = false;
      rec.continuous = true;
      let texto = "";
      rec.onresult = (e) => {
        for (let i = e.resultIndex; i < e.results.length; i++) {
          if (e.results[i].isFinal) texto += e.results[i][0].transcript + " ";
        }
      };
      rec.onerror = (e) => {
        if (e.error !== "aborted") onError?.("microfono");
      };
      rec.onend = () => {
        reconocedor.current = null;
        setGrabando(false);
        pararReloj();
        if (!cancelado.current && texto.trim()) onTexto?.(texto.trim());
      };
      reconocedor.current = rec;
      rec.start();
    } else {
      return;
    }

    setGrabando(true);
    reloj.current = setInterval(() => setSegundos((s) => s + 1), 1000);
    // Corta sola la grabación al llegar a la duración máxima.
    limite.current = setTimeout(() => detener(true), maxSeg * 1000);
  }, [grabando, transcribiendo, conServidor, idioma, maxSeg, onTexto, onError, detener]);

  // Libera el micrófono si el componente se desmonta grabando.
  useEffect(() => () => detener(false), [detener]);

  return { disponible, grabando, transcribiendo, segundos, iniciar, detener };
}

export const lecturaDisponible = typeof window !== "undefined" && "speechSynthesis" in window;

// Lee un texto en voz alta con la voz del navegador, en el idioma pedido. Recibe texto e idioma.
export function leerEnVozAlta(texto, idioma = "es") {
  if (!lecturaDisponible) return;
  window.speechSynthesis.cancel();
  const plano = (texto || "").replace(/\*\*/g, "").replace(/^\s*(?:[-*•]|\d+[.)])\s+/gm, "");
  const voz = new SpeechSynthesisUtterance(plano.slice(0, 1500));
  voz.lang = LOCALES[idioma] || LOCALES.es;
  window.speechSynthesis.speak(voz);
}
