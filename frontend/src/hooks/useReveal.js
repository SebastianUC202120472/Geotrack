import { useEffect, useRef, useState } from "react";

// Activa una entrada animada cuando el elemento aparece en viewport.
// Devuelve { ref, visible }: pon ref en el contenedor y usa la clase
// "reveal" + (visible ? "is-revealed" : ""). Respeta prefers-reduced-motion:
// si está activo, arranca ya visible (estado inicial perezoso) — así NO se
// hace setState síncrono dentro del effect (evita el error de lint del repo).
export default function useReveal() {
  const ref = useRef(null);
  const [visible, setVisible] = useState(
    () => window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false,
  );

  useEffect(() => {
    const nodo = ref.current;
    if (!nodo || visible) return; // ya visible (reduce-motion) → no observar
    const obs = new IntersectionObserver(
      (entradas) => {
        // setState dentro del callback del observer (no síncrono en effect).
        if (entradas[0]?.isIntersecting) {
          setVisible(true);
          obs.disconnect();
        }
      },
      { threshold: 0.08 },
    );
    obs.observe(nodo);
    return () => obs.disconnect();
  }, [visible]);

  return { ref, visible };
}
