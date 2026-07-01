import { useEffect, useState } from "react";
import { createPortal } from "react-dom";

// Modal animado reutilizable. Recibe open, onClose, variant ("center"|"right"), className, children.
const DURACION = 250;

const panelBase = {
  center: "w-full max-w-md rounded-card bg-white p-6 shadow-xl",
  right: "flex h-full w-full max-w-md flex-col overflow-y-auto bg-white shadow-xl",
};

export default function Modal({ open, onClose, variant = "center", className = "", children }) {
  const [render, setRender] = useState(open);
  const [visible, setVisible] = useState(false);
  const [contenido, setContenido] = useState(children);

  // Conserva el contenido durante la animación de salida.
  useEffect(() => {
    if (!open) return;
    const r = requestAnimationFrame(() => setContenido(children));
    return () => cancelAnimationFrame(r);
  }, [open, children]);

  useEffect(() => {
    if (open) {
      const r = requestAnimationFrame(() => {
        setRender(true);
        requestAnimationFrame(() => setVisible(true));
      });
      return () => cancelAnimationFrame(r);
    }
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

  // Portal a body para que el fixed inset-0 se mida contra el viewport real.
  return createPortal(
    <div className="fixed inset-0 z-50" role="dialog" aria-modal="true">
      <div className={`absolute inset-0 bg-slate-900/50 transition-opacity duration-200 ${visible ? "opacity-100" : "opacity-0"}`} />
      <div
        className={`absolute inset-0 flex ${posicion}`}
        onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      >
        <div className={`relative ${panelBase[variant]} ${transicion} ${className}`}>
          {open ? children : contenido}
        </div>
      </div>
    </div>,
    document.body,
  );
}
