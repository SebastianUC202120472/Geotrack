import { useEffect, useRef, useState } from "react";

// Anima un número de 0 hasta `valor` en `duracion` ms; si no es número o hay prefers-reduced-motion, devuelve el valor directo.
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
      const eased = 1 - Math.pow(1 - progreso, 3);
      setActual(Math.round(valor * eased));
      if (progreso < 1) rafRef.current = requestAnimationFrame(paso);
    };
    rafRef.current = requestAnimationFrame(paso);
    return () => cancelAnimationFrame(rafRef.current);
  }, [valor, duracion, esNumero]);

  return actual;
}
