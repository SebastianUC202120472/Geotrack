import { useRef, useEffect, useState } from "react";
import { Bell } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useNotificaciones } from "../hooks/useNotificaciones";

// Devuelve una cadena legible del tiempo transcurrido desde una fecha ISO.
// Entrada: fechaIso (string). Salida: "hace X minutos/horas/días".
function tiempoRelativo(fechaIso) {
  const diff = Date.now() - new Date(fechaIso).getTime();
  const min = Math.floor(diff / 60000);
  if (min < 1) return "ahora mismo";
  if (min < 60) return `hace ${min} min`;
  const hrs = Math.floor(min / 60);
  if (hrs < 24) return `hace ${hrs} h`;
  const dias = Math.floor(hrs / 24);
  return `hace ${dias} día${dias > 1 ? "s" : ""}`;
}

// Campana de notificaciones del admin: ícono con badge de no vistas, parpadea si hay pendientes.
// Al abrir marca todo como visto; el popover lista el historial cronológico con resaltado de no vistas.
// Entrada: ninguna (solo se monta cuando rol === "admin").
export default function CampanaNotificaciones() {
  const navigate = useNavigate();
  const { no_vistas, items, marcarVistas } = useNotificaciones(true);
  const [abierto, setAbierto] = useState(false);
  const panelRef = useRef(null);

  // Cierra el popover al hacer click fuera de él.
  useEffect(() => {
    if (!abierto) return;
    const manejarClickFuera = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target)) {
        setAbierto(false);
      }
    };
    document.addEventListener("mousedown", manejarClickFuera);
    return () => document.removeEventListener("mousedown", manejarClickFuera);
  }, [abierto]);

  // Cierra el popover con la tecla Escape.
  useEffect(() => {
    if (!abierto) return;
    const manejarEscape = (e) => {
      if (e.key === "Escape") setAbierto(false);
    };
    document.addEventListener("keydown", manejarEscape);
    return () => document.removeEventListener("keydown", manejarEscape);
  }, [abierto]);

  // Abre/cierra el popover; al abrir, marca las notificaciones como vistas.
  const alternarPanel = () => {
    setAbierto((v) => {
      const nuevoEstado = !v;
      if (nuevoEstado && no_vistas > 0) marcarVistas();
      return nuevoEstado;
    });
  };

  // Navega a la ruta del ítem y cierra el popover.
  const irA = (ruta) => {
    setAbierto(false);
    navigate(ruta);
  };

  return (
    <div ref={panelRef} className="relative">
      {/* Botón de campana con badge de notificaciones no vistas */}
      <button
        onClick={alternarPanel}
        aria-label="Notificaciones"
        className={`relative flex items-center justify-center rounded-lg p-2 text-slate-300 transition-colors hover:bg-slate-700 hover:text-white focus:outline-none${no_vistas > 0 ? " parpadeo-alerta" : ""}`}
      >
        <Bell size={20} />
        {no_vistas > 0 && (
          <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white leading-none">
            {no_vistas > 99 ? "99+" : no_vistas}
          </span>
        )}
      </button>

      {/* Popover con el historial de notificaciones (cronológico, recientes primero) */}
      {abierto && (
        <div className="absolute left-0 top-full z-50 mt-2 w-80 rounded-xl border border-[#2b3543] bg-[#1a2230] shadow-2xl">
          <div className="border-b border-[#2b3543] px-4 py-3">
            <p className="text-sm font-semibold text-white">Notificaciones</p>
          </div>
          <ul className="max-h-80 overflow-y-auto py-2">
            {items.length === 0 ? (
              <li className="px-4 py-4 text-center text-sm text-slate-400">
                Sin novedades
              </li>
            ) : (
              items.map((item) => (
                <li key={item.id} className={item.visto_en === null ? "bg-slate-700/40" : ""}>
                  <button
                    onClick={() => irA(item.ruta)}
                    className="flex w-full flex-col gap-0.5 px-4 py-3 text-left text-sm transition-colors hover:bg-slate-700/70"
                  >
                    <span className={`font-medium ${item.visto_en === null ? "text-white" : "text-slate-300"}`}>
                      {item.titulo}
                    </span>
                    <span className="text-xs text-slate-400 line-clamp-2">{item.mensaje}</span>
                    <span className="mt-0.5 text-[11px] text-slate-500">
                      {tiempoRelativo(item.creado_en)}
                    </span>
                  </button>
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
