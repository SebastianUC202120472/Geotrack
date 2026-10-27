// Asistente virtual con IA del panel (Idea 1). Boton flotante que abre un chat:
// el usuario pregunta por texto o por voz y el asistente responde con datos reales
// del sistema, tablas, graficos y botones a la pantalla exacta del panel.
// Este modulo se carga en diferido y no aparece si el servicio esta apagado.
// En la vista completa (/panel/asistente) el boton se oculta: el chat ya esta en pantalla.
import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import ChatAsistente from "./ChatAsistente";
import IconoAsistente from "./IconoAsistente";
import { ROLES_ASISTENTE, RUTA_PAGINA, useEstadoChat, useServicioAsistente } from "./estadoChat";

// Widget flotante del asistente. Sin props: toma el rol de la sesion.
export default function AsistenteFlotante() {
  const { rol } = useAuth();
  const { pathname } = useLocation();
  const servicio = useServicioAsistente();
  // Mantiene viva la conversacion compartida mientras el panel este abierto.
  const { enviando } = useEstadoChat();
  const [abierto, setAbierto] = useState(false);
  const enPagina = pathname.startsWith(RUTA_PAGINA);
  const visible = abierto && !enPagina;

  // Cierra con Escape mientras esta abierto.
  useEffect(() => {
    if (!visible) return undefined;
    const alPresionar = (e) => e.key === "Escape" && setAbierto(false);
    window.addEventListener("keydown", alPresionar);
    return () => window.removeEventListener("keydown", alPresionar);
  }, [visible]);

  if (!servicio?.activo || !ROLES_ASISTENTE.includes(rol) || enPagina) return null;

  return (
    <>
      {!visible && (
        <button
          type="button"
          onClick={() => setAbierto(true)}
          aria-label="Abrir el asistente virtual"
          title="Asistente virtual"
          className="fixed bottom-5 right-5 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-brand-600 to-brand-700 text-white shadow-[0_8px_24px_rgba(37,99,235,0.45)] ring-1 ring-white/20 transition-transform hover:scale-105 focus:outline-none focus-visible:ring-4 focus-visible:ring-brand-300"
        >
          <IconoAsistente size={28} />
          {enviando && (
            <span className="absolute right-1 top-1 h-3 w-3 animate-pulse rounded-full border-2 border-white bg-success" aria-hidden="true" />
          )}
        </button>
      )}

      {visible && (
        <section
          role="dialog"
          aria-label="Asistente virtual"
          className="fixed inset-0 z-50 flex flex-col bg-canvas sm:inset-auto sm:bottom-5 sm:right-5 sm:h-[min(660px,calc(100vh-2.5rem))] sm:w-[420px] sm:rounded-2xl sm:border sm:border-slate-200 sm:shadow-2xl"
        >
          <ChatAsistente modo="flotante" servicio={servicio} onCerrar={() => setAbierto(false)} />
        </section>
      )}
    </>
  );
}
