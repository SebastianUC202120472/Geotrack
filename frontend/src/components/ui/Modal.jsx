import { useEffect, useState } from "react";
import { createPortal } from "react-dom";

// Modal/overlay animado y reutilizable. Mantiene el contenido montado durante el
// cierre para animar la salida; cierra con Escape o clic fuera del panel.
// Entrada:
//   open (bool): si está visible.
//   onClose (fn): se llama al pedir cierre (Escape, clic fuera).
//   variant ("center" | "right"): centrado con zoom, o panel lateral deslizante.
//   className (string): clases extra para el panel.
//   children: contenido del panel.
const DURACION = 250; // ms; debe coincidir con las transiciones de abajo

const panelBase = {
  center: "w-full max-w-md rounded-card bg-white p-6 shadow-xl",
  right: "flex h-full w-full max-w-md flex-col overflow-y-auto bg-white shadow-xl",
};

export default function Modal({ open, onClose, variant = "center", className = "", children }) {
  const [render, setRender] = useState(open);
  const [visible, setVisible] = useState(false);
  const [contenido, setContenido] = useState(children);

  // Recuerda el último contenido mientras está abierto, para mostrarlo también
  // durante la animación de salida (cuando el padre ya limpió su estado). Se
  // actualiza dentro de un rAF (asíncrono) para no usar setState síncrono en
  // un effect.
  useEffect(() => {
    if (!open) return;
    const r = requestAnimationFrame(() => setContenido(children));
    return () => cancelAnimationFrame(r);
  }, [open, children]);

  useEffect(() => {
    if (open) {
      // Monta y, en el frame siguiente, activa la transición de entrada.
      const r = requestAnimationFrame(() => {
        setRender(true);
        requestAnimationFrame(() => setVisible(true));
      });
      return () => cancelAnimationFrame(r);
    }
    // Cierre: dispara la transición de salida y desmonta al terminar.
    const r = requestAnimationFrame(() => setVisible(false));
    const t = setTimeout(() => setRender(false), DURACION);
    return () => {
      cancelAnimationFrame(r);
      clearTimeout(t);
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const alTeclear = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", alTeclear);
    return () => window.removeEventListener("keydown", alTeclear);
  }, [open, onClose]);

  if (!render) return null;

  const transicion =
    variant === "right"
      ? `transition-transform duration-300 ease-out ${visible ? "translate-x-0" : "translate-x-full"}`
      : `transition-all duration-200 ease-out ${visible ? "opacity-100 scale-100" : "opacity-0 scale-95"}`;

  const posicion = variant === "right" ? "justify-end" : "items-center justify-center p-4";

  // Portal a document.body: el fixed inset-0 se mide contra el viewport real,
  // eliminando las franjas blancas que aparecían cuando el modal estaba dentro
  // del árbol del layout (barra superior, sidebar, wrapper animate-fade-up).
  return createPortal(
    <div className="fixed inset-0 z-50" role="dialog" aria-modal="true">
      <div className={`absolute inset-0 bg-slate-900/50 transition-opacity duration-200 ${visible ? "opacity-100" : "opacity-0"}`} />
      <div
        className={`absolute inset-0 flex ${posicion}`}
        onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      >
        <div className={`relative ${panelBase[variant]} ${transicion} ${className}`}>
          {/* Abierto: render en vivo (sin frame vacío). Cerrando: último snapshot para animar la salida. */}
          {open ? children : contenido}
        </div>
      </div>
    </div>,
    document.body,
  );
}
