import { useEffect, useRef, useState } from "react";

// Devuelve { ref, visible } para animar un elemento al entrar al viewport; respeta prefers-reduced-motion.
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
