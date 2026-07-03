import { useEffect } from "react";

// Anima un número de 0 a data-count con easing cubic-out (port fiel del mockup).
// Input: el <span data-count="43" data-prefix="+" data-suffix="%">.
function correrContador(el) {
  const target = parseFloat(el.dataset.count);
  const suf = el.dataset.suffix || "";
  const pre = el.dataset.prefix || "";
  const t0 = performance.now();
  const dur = 1500;
  const step = (t) => {
    const p = Math.min(1, (t - t0) / dur);
    const e = 1 - Math.pow(1 - p, 3);
    el.textContent = pre + Math.round(target * e) + suf;
    if (p < 1 && el.dataset.on) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

// Efectos de scroll del sitio público: revela [data-reveal], dispara contadores y barras.
// Input: ref del contenedor de la página (los efectos solo miran dentro de él).
export function useEfectosScroll(refContenedor) {
  useEffect(() => {
    const cont = refContenedor.current;
    if (!cont) return;

    const els = cont.querySelectorAll("[data-reveal]");

    let ioFired = false;
    let ioDead = false;

    // Fallback: si el observer no responde (contenedor oculto/limitado), mostrar todo
    const ioTimer = setTimeout(() => {
      // Comprueba geometría: si algo visible en viewport sigue oculto, el observer no sirve aquí
      const vh = window.innerHeight || document.documentElement.clientHeight;
      const oculto = Array.from(cont.querySelectorAll("[data-reveal]")).some((el) => {
        const r = el.getBoundingClientRect();
        return r.top < vh && r.bottom > 0 && el.style.opacity === "0";
      });
      if (ioFired && !oculto) return;
      ioDead = true;
      cont.querySelectorAll("[data-reveal]").forEach((el) => {
        el.style.transition = "none";
        el.style.opacity = "1";
        el.style.transform = "none";
        el.querySelectorAll("[data-count]").forEach((c) => {
          if (!c.dataset.on) {
            c.dataset.on = "1";
            correrContador(c);
          }
        });
      });
    }, 800);

    const observer = new IntersectionObserver(
      (entries) => {
        ioFired = true;
        if (ioDead) return;
        entries.forEach((en) => {
          const el = en.target;
          const d = parseInt(el.dataset.reveal || "0", 10);
          if (en.isIntersecting) {
            el.style.transitionDelay = d + "ms";
            el.style.opacity = "1";
            el.style.transform = "none";
            el.querySelectorAll("[data-count]").forEach((c) => {
              if (!c.dataset.on) {
                c.dataset.on = "1";
                correrContador(c);
              }
            });
            if (el.dataset.count && !el.dataset.on) {
              el.dataset.on = "1";
              correrContador(el);
            }
            el.querySelectorAll("[data-barra]").forEach((b) => {
              b.style.width = b.dataset.barra + "%";
            });
          } else {
            el.style.transitionDelay = "0ms";
            el.style.opacity = "0";
            el.style.transform = el.dataset.revealFrom || "translateY(26px)";
            el.querySelectorAll("[data-count]").forEach((c) => {
              delete c.dataset.on;
            });
            if (el.dataset.count) delete el.dataset.on;
            el.querySelectorAll("[data-barra]").forEach((b) => {
              b.style.width = "0%";
            });
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" },
    );
    els.forEach((el) => observer.observe(el));

    return () => {
      observer.disconnect();
      clearTimeout(ioTimer);
    };
  }, [refContenedor]);
}
