import { useEffect, useState } from "react";

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

  // Mientras está abierto recuerda el último contenido, para mostrarlo también
  // durante la animación de salida (cuando el padre ya limpió su estado).
  useEffect(() => {
    if (open) setContenido(children);
  }, [open, children]);

  useEffect(() => {
    if (open) {
      setRender(true);
      const r = requestAnimationFrame(() => requestAnimationFrame(() => setVisible(true)));
      return () => cancelAnimationFrame(r);
    }
    setVisible(false);
    const t = setTimeout(() => setRender(false), DURACION);
    return () => clearTimeout(t);
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

  return (
    <div className="fixed inset-0 z-50" role="dialog" aria-modal="true">
      <div className={`absolute inset-0 bg-slate-900/50 transition-opacity duration-200 ${visible ? "opacity-100" : "opacity-0"}`} />
      <div
        className={`absolute inset-0 flex ${posicion}`}
        onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      >
        <div className={`relative ${panelBase[variant]} ${transicion} ${className}`}>
          {contenido}
        </div>
      </div>
    </div>
  );
}
