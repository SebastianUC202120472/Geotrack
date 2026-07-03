import { useEffect, useRef } from "react";

// Datos de las 4 tarjetas de pasos (número, claves i18n de título/descripción,
// lado donde aparece la tarjeta y de dónde entra al hacer reveal).
const PASOS = [
  { n: "01", claveT: "p1t", claveD: "p1d", lado: "izq", relleno: false },
  { n: "02", claveT: "p2t", claveD: "p2d", lado: "der", relleno: false },
  { n: "03", claveT: "p3t", claveD: "p3d", lado: "izq", relleno: false },
  { n: "04", claveT: "p4t", claveD: "p4d", lado: "der", relleno: true },
];
const TEXTOS_ES = {
  p1t: "Recepción del pedido",
  p1d: "Recogemos los pedidos en tienda o centro de distribución del retail, con manifiesto firmado y conteo bulto por bulto.",
  p2t: "Verificación y rutas",
  p2d: "En nuestro centro, cada paquete se valida, se registra en GeoTrack y se asigna a una ruta por zona de Lima.",
  p3t: "Distribución en ruta",
  p3d: "Nuestra flota sale a reparto por todo Lima. El retail ve el avance de sus pedidos en vivo, parada por parada.",
  p4t: "Entrega con evidencia",
  p4d: "Entregamos al cliente final con foto y confirmación. Lo no entregado se gestiona y reprograma, con reporte al retail.",
};

// Mini-hook: inclinación 3D de tarjetas [data-tilt] siguiendo el cursor (port de
// setupTilt). Input: ref del contenedor donde buscar las tarjetas.
function useTilt(contRef) {
  useEffect(() => {
    const cont = contRef.current;
    if (!cont) return;
    const tarjetas = Array.from(cont.querySelectorAll("[data-tilt]"));

    const onMove = (e) => {
      const el = e.currentTarget;
      const r = el.getBoundingClientRect();
      const rx = ((e.clientY - r.top) / r.height - 0.5) * -7;
      const ry = ((e.clientX - r.left) / r.width - 0.5) * 7;
      el.style.transitionDuration = "0s";
      el.style.transform = "perspective(700px) rotateX(" + rx.toFixed(2) + "deg) rotateY(" + ry.toFixed(2) + "deg) translateY(-4px)";
    };
    const onLeave = (e) => {
      const el = e.currentTarget;
      el.style.transitionDuration = "";
      el.style.transform = "translateY(0px)";
    };

    tarjetas.forEach((el) => {
      el.addEventListener("pointermove", onMove);
      el.addEventListener("pointerleave", onLeave);
    });
    return () => {
      tarjetas.forEach((el) => {
        el.removeEventListener("pointermove", onMove);
        el.removeEventListener("pointerleave", onLeave);
      });
    };
  }, [contRef]);
}

// ComoFunciona (#como-funciona): 4 pasos del servicio conectados por una curva SVG
// que se dibuja y una flecha que la recorre según el scroll (resto de setupParallax),
// más tilt 3D en las tarjetas. Input: tx (traducción).
export default function ComoFunciona({ tx }) {
  const flujoRef = useRef(null);
  useTilt(flujoRef);

  // Dibuja la curva del flujo y mueve la flecha según el progreso de scroll de #flujo.
  // Port fiel de la parte "Flujo del paso a paso" de setupParallax: dash-offset de
  // #flujoPath, posición/rotación de #flujoTip vía getPointAtLength, y aparición de
  // las flechas fijas [data-flecha] por umbral de progreso.
  useEffect(() => {
    const onScroll = () => {
      const flujo = document.getElementById("flujo");
      const fp = document.getElementById("flujoPath");
      if (!flujo || !fp) return;
      const vh = window.innerHeight || 800;
      const fr = flujo.getBoundingClientRect();
      let p = (vh * 0.82 - fr.top) / (fr.height + vh * 0.3);
      p = Math.max(0, Math.min(1, p));
      fp.setAttribute("stroke-dashoffset", String(1 - p));

      const L = fp.getTotalLength();
      const W = flujo.clientWidth || 1;
      const H = flujo.clientHeight || 1;
      const tip = document.getElementById("flujoTip");
      if (tip) {
        const pt = fp.getPointAtLength(L * p);
        const pt2 = fp.getPointAtLength(Math.min(L, L * p + 0.6));
        tip.style.left = pt.x + "%";
        tip.style.top = pt.y + "%";
        const ang = (Math.atan2((pt2.y - pt.y) * H, (pt2.x - pt.x) * W) * 180) / Math.PI;
        tip.style.transform = "rotate(" + ang.toFixed(1) + "deg)";
        tip.style.opacity = p > 0.005 && p < 0.995 ? "1" : "0";
      }

      flujo.querySelectorAll("[data-flecha]").forEach((f) => {
        const t = parseFloat(f.dataset.flecha);
        if (!f.dataset.pos) {
          f.dataset.pos = "1";
          const q = fp.getPointAtLength(L * t);
          const q2 = fp.getPointAtLength(Math.min(L, L * t + 0.6));
          f.style.left = q.x + "%";
          f.style.top = q.y + "%";
          f.dataset.ang = String((Math.atan2((q2.y - q.y) * H, (q2.x - q.x) * W) * 180) / Math.PI);
        }
        const on = p >= t;
        f.style.opacity = on ? "1" : "0";
        f.style.transform = (on ? "scale(1)" : "scale(.4)") + " rotate(" + (+f.dataset.ang).toFixed(1) + "deg)";
      });
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <section id="como-funciona" data-sec="p" style={{ maxWidth: 1200, margin: "0 auto", padding: "110px 28px 0" }}>
      <div
        data-reveal="0"
        style={{ maxWidth: 640, opacity: 0, transform: "translateY(26px)", transition: "opacity .7s ease, transform .7s ease" }}
      >
        <p data-i18n="pasosE" style={{ margin: "0 0 12px", fontSize: 13, fontWeight: 600, letterSpacing: ".14em", textTransform: "uppercase", color: "#2679d8" }}>
          {tx("pasosE", "El servicio, paso a paso")}
        </p>
        <h2 data-i18n="pasosT" style={{ margin: 0, fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: "clamp(30px, 3.6vw, 44px)", lineHeight: 1.1, letterSpacing: "-.01em" }}>
          {tx("pasosT", "Del centro de distribución del retail a la puerta del cliente.")}
        </h2>
      </div>

      <div id="flujo" ref={flujoRef} style={{ margin: "64px auto 0", position: "relative", maxWidth: 920 }}>
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ position: "absolute", inset: 0, width: "100%", height: "100%", overflow: "visible" }} aria-hidden="true">
          <path
            d="M 50 0 C 50 6, 25 6, 25 12 C 25 20, 75 28, 75 38 C 75 48, 25 52, 25 62 C 25 72, 75 78, 75 88 C 75 94, 50 94, 50 100"
            fill="none"
            stroke="#d7e4f1"
            strokeWidth="3"
            vectorEffect="non-scaling-stroke"
            strokeLinecap="round"
          />
          <path
            id="flujoPath"
            pathLength="1"
            d="M 50 0 C 50 6, 25 6, 25 12 C 25 20, 75 28, 75 38 C 75 48, 25 52, 25 62 C 25 72, 75 78, 75 88 C 75 94, 50 94, 50 100"
            fill="none"
            stroke="#2679d8"
            strokeWidth="3"
            vectorEffect="non-scaling-stroke"
            strokeLinecap="round"
            strokeDasharray="1"
            strokeDashoffset="1"
          />
        </svg>
        <div
          id="flujoTip"
          style={{
            position: "absolute",
            left: "50%",
            top: 0,
            width: 30,
            height: 30,
            margin: "-15px 0 0 -15px",
            borderRadius: 99,
            background: "#2679d8",
            color: "#fff",
            display: "grid",
            placeItems: "center",
            fontSize: 13,
            boxShadow: "0 6px 16px rgba(15,43,74,.35)",
            zIndex: 1,
            pointerEvents: "none",
          }}
        >
          ➤
        </div>
        {[0.27, 0.52, 0.77].map((umbral) => (
          <div
            key={umbral}
            data-flecha={umbral}
            style={{
              position: "absolute",
              width: 26,
              height: 26,
              margin: "-13px 0 0 -13px",
              borderRadius: 99,
              background: "#fff",
              border: "2px solid #2679d8",
              color: "#2679d8",
              display: "grid",
              placeItems: "center",
              fontSize: 11,
              zIndex: 2,
              opacity: 0,
              transform: "scale(.4)",
              transition: "opacity .4s ease, transform .4s ease",
              pointerEvents: "none",
            }}
          >
            ➤
          </div>
        ))}

        {PASOS.map((paso) => (
          <div
            key={paso.n}
            data-reveal="0"
            data-reveal-from={paso.lado === "izq" ? "translateX(-46px)" : "translateX(46px)"}
            data-tilt="1"
            className="ldg-paso-card"
            style={{
              position: "relative",
              zIndex: 2,
              width: "clamp(280px, 54%, 440px)",
              margin: paso.lado === "izq" ? "0 auto 52px 0" : "0 0 52px auto",
              background: "#fff",
              border: "1px solid rgba(15,43,74,.08)",
              borderRadius: 24,
              padding: 26,
              boxShadow: "0 10px 30px rgba(15,43,74,.06)",
              opacity: 0,
              transform: paso.lado === "izq" ? "translateX(-46px)" : "translateX(46px)",
              transition: "opacity .7s ease, transform .7s ease",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "0 0 12px" }}>
              <span
                style={{
                  flex: "none",
                  width: 46,
                  height: 46,
                  borderRadius: 99,
                  background: paso.relleno ? "#2679d8" : "#eaf3fc",
                  border: paso.relleno ? "none" : "2px solid #2679d8",
                  display: "grid",
                  placeItems: "center",
                  fontFamily: "Archivo, sans-serif",
                  fontWeight: 800,
                  fontSize: 17,
                  color: paso.relleno ? "#fff" : "#2679d8",
                }}
              >
                {paso.n}
              </span>
              <h3 data-i18n={paso.claveT} style={{ margin: 0, fontFamily: "Archivo, sans-serif", fontWeight: 700, fontSize: 19 }}>
                {tx(paso.claveT, TEXTOS_ES[paso.claveT])}
              </h3>
            </div>
            <p data-i18n={paso.claveD} style={{ margin: 0, fontSize: 14.5, lineHeight: 1.6, color: "#4f6580" }}>
              {tx(paso.claveD, TEXTOS_ES[paso.claveD])}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
