import { useRef, useEffect, useState } from "react";
import { Bell } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useNotificaciones } from "../hooks/useNotificaciones";

// Campana de notificaciones del admin: ícono con badge, parpadea cuando hay pendientes.
// Al hacer click abre un popover con la lista de ítems; cada ítem navega a su ruta.
// Entrada: ninguna (usa el hook interno; solo se monta cuando rol === "admin").
export default function CampanaNotificaciones() {
  const navigate = useNavigate();
  const { total, items } = useNotificaciones(true);
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

  // Navega a la ruta del ítem y cierra el popover.
  const irA = (ruta) => {
    setAbierto(false);
    navigate(ruta);
  };

  return (
    <div ref={panelRef} className="relative">
      {/* Botón de campana con badge de total */}
      <button
        onClick={() => setAbierto((v) => !v)}
        aria-label="Notificaciones"
        className={`relative flex items-center justify-center rounded-lg p-2 text-slate-300 transition-colors hover:bg-slate-700 hover:text-white focus:outline-none${total > 0 ? " parpadeo-alerta" : ""}`}
      >
        <Bell size={20} />
        {total > 0 && (
          <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white leading-none">
            {total > 99 ? "99+" : total}
          </span>
        )}
      </button>

      {/* Popover con la lista de notificaciones */}
      {abierto && (
        <div className="absolute left-0 top-full z-50 mt-2 w-72 rounded-xl border border-[#2b3543] bg-[#1a2230] shadow-2xl">
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
                <li key={item.tipo}>
                  <button
                    onClick={() => irA(item.ruta)}
                    className="flex w-full items-center justify-between px-4 py-3 text-left text-sm text-slate-300 transition-colors hover:bg-slate-700 hover:text-white"
                  >
                    <span>{item.etiqueta}</span>
                    <span className="ml-2 shrink-0 rounded-full bg-red-500 px-2 py-0.5 text-[11px] font-bold text-white">
                      {item.count}
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
