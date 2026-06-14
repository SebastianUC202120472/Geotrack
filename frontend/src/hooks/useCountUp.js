import { useEffect, useRef, useState } from "react";

// Anima un número desde 0 hasta `valor` en `duracion` ms (requestAnimationFrame).
// Entrada: valor (number | cualquier cosa), duracion en ms (opcional, 700 por defecto).
// Si `valor` NO es número finito, devuelve el valor tal cual (ej. el guion "—").
// Respeta prefers-reduced-motion (si está activo, muestra el número final al instante).
export default function useCountUp(valor, duracion = 700) {
  const esNumero = typeof valor === "number" && Number.isFinite(valor);
  const [actual, setActual] = useState(esNumero ? 0 : valor);
  const rafRef = useRef(0);

  useEffect(() => {
    if (!esNumero) {
      setActual(valor);
      return;
    }
    const sinMovimiento = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (sinMovimiento) {
      setActual(valor);
      return;
    }
    let inicio = null;
    const paso = (t) => {
      if (inicio === null) inicio = t;
      const progreso = Math.min((t - inicio) / duracion, 1);
      // easing easeOutCubic para que desacelere al final
      const eased = 1 - Math.pow(1 - progreso, 3);
      setActual(Math.round(valor * eased));
      if (progreso < 1) rafRef.current = requestAnimationFrame(paso);
    };
    rafRef.current = requestAnimationFrame(paso);
    return () => cancelAnimationFrame(rafRef.current);
  }, [valor, duracion, esNumero]);

  return actual;
}
