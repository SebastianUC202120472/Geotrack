// Voz del asistente: grabar un mensaje (como en WhatsApp) y leer respuestas en voz alta.
// - Con transcripcion en el servidor: se graba con MediaRecorder y se sube el audio.
// - Sin ella: se usa el dictado del navegador (Web Speech API, mejor en Chrome y Edge).
import { useCallback, useEffect, useRef, useState } from "react";
import { transcribirAudio } from "./servicioAsistente";

const Reconocimiento = typeof window !== "undefined" ? window.SpeechRecognition || window.webkitSpeechRecognition : null;

// Elige un formato de grabacion que soporte el navegador. Sin input.
function formatoGrabacion() {
  if (typeof MediaRecorder === "undefined") return null;
  for (const tipo of ["audio/webm;codecs=opus", "audio/ogg;codecs=opus", "audio/mp4"]) {
    if (MediaRecorder.isTypeSupported?.(tipo)) return tipo;
  }
  return "";
}

// Hook de grabacion. Recibe { vozServidor, maxSeg, onTexto, onError }.
export function useGrabadora({ vozServidor, maxSeg = 60, onTexto, onError }) {
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

  // Detiene el contador de segundos y el corte automatico. Sin input.
  const pararReloj = () => {
    clearInterval(reloj.current);
    clearTimeout(limite.current);
    reloj.current = null;
    limite.current = null;
  };

  // Termina la grabacion; si enviar es false, descarta el audio. Recibe enviar (bool).
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

  // Empieza a grabar o a dictar. Sin input.
  const iniciar = useCallback(async () => {
    if (grabando || transcribiendo) return;
    cancelado.current = false;
    setSegundos(0);

    if (conServidor) {
      let flujo;
      try {
        flujo = await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch {
        onError?.("No se pudo usar el micrófono. Revisa los permisos del navegador.");
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
          onTexto?.(await transcribirAudio(audio));
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
      rec.lang = "es-PE";
      rec.interimResults = false;
      rec.continuous = true;
      let texto = "";
      rec.onresult = (e) => {
        for (let i = e.resultIndex; i < e.results.length; i++) {
          if (e.results[i].isFinal) texto += e.results[i][0].transcript + " ";
        }
      };
      rec.onerror = (e) => {
        if (e.error !== "aborted") onError?.("No se pudo usar el dictado del navegador.");
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
    // Corta sola la grabacion al llegar a la duracion maxima.
    limite.current = setTimeout(() => detener(true), maxSeg * 1000);
  }, [grabando, transcribiendo, conServidor, maxSeg, onTexto, onError, detener]);

  // Libera el microfono si el componente se desmonta grabando.
  useEffect(() => () => detener(false), [detener]);

  return { disponible, grabando, transcribiendo, segundos, iniciar, detener };
}

// Quita las marcas de formato para leer la respuesta en voz alta. Recibe el texto.
function textoPlano(texto) {
  return (texto || "").replace(/\*\*/g, "").replace(/^\s*(?:[-*•]|\d+[.)])\s+/gm, "");
}

// Lee un texto en voz alta con la voz del navegador. Recibe el texto.
export function leerEnVozAlta(texto) {
  if (typeof window === "undefined" || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const voz = new SpeechSynthesisUtterance(textoPlano(texto).slice(0, 1500));
  voz.lang = "es-PE";
  voz.rate = 1.05;
  window.speechSynthesis.speak(voz);
}

// Corta la lectura en curso. Sin input.
export function callarVoz() {
  window.speechSynthesis?.cancel();
}

export const lecturaDisponible = typeof window !== "undefined" && "speechSynthesis" in window;
