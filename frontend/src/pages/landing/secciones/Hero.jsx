import { useEffect } from "react";
import MapaHeroIso from "../../../components/publico/MapaHeroIso";
import heroFondo from "../../../assets/landing/hero-fondo.png";

// Hero (#inicio): eyebrow + titular + subtítulo + 2 CTAs a la izquierda, mapa 3D
// animado a la derecha. Fondo con parallax al hacer scroll (useEffect local, sin
// setState). Input: tx (traducción), lang (idioma activo para el HUD bilingüe del mapa).
export default function Hero({ tx, lang }) {
  // Parallax del hero (port de setupParallax, solo la parte de #inicio): el fondo
  // se desplaza a 0.35x del scroll (tope 380px) y el contenido se desvanece/difumina
  // a medida que se aleja. Listener de scroll pasivo, limpiado al desmontar.
  useEffect(() => {
    const onScroll = () => {
      const y = window.scrollY || document.documentElement.scrollTop || 0;
      const vh = window.innerHeight || 800;
      const bg = document.getElementById("heroBg");
      if (bg) bg.style.transform = "translateY(" + Math.min(y * 0.35, 380) + "px)";
      const inner = document.getElementById("heroInner");
      if (inner) {
        const k = Math.min(1, y / (vh * 0.72));
        inner.style.opacity = String(1 - k * 0.92);
        inner.style.filter = k > 0.02 ? "blur(" + (k * 8).toFixed(1) + "px)" : "none";
      }
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Textos del HUD del mapa según idioma activo: las 3 frases interpoladas (en ruta,
  // cerca de una parada, ruta completada) más las etiquetas fijas (EN VIVO / hint).
  const en = lang === "en";
  const textosMapa = {
    mapSava: tx("mapSava", "Centro SAVA"),
    vivo: tx("mapVivo", "EN VIVO"),
    hint: tx("mapHint", "Gire el mapa arrastrándolo · lleve la camioneta para adelantar la ruta"),
    enRuta: (n, total) =>
      en ? "Heading to delivery " + n + " of " + total : "En ruta a la entrega " + n + " de " + total,
    cercaDe: (n, total, nombre) =>
      (en ? "Delivering order " + n + " of " + total : "Entregando pedido " + n + " de " + total) + " · " + nombre,
    completada: (total) =>
      en ? "Route completed · " + total + " orders delivered ✓" : "Ruta completada · " + total + " pedidos entregados ✓",
  };

  return (
    <section id="inicio" style={{ position: "relative", overflow: "hidden", background: "#0c2440" }}>
      <div
        id="heroBg"
        aria-hidden="true"
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: "-14%",
          height: "130%",
          backgroundImage: `url(${heroFondo})`,
          backgroundSize: "cover",
          backgroundPosition: "center 30%",
          willChange: "transform",
        }}
      />
      <div
        aria-hidden="true"
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(100deg,rgba(8,26,47,.96) 0%,rgba(8,26,47,.88) 40%,rgba(8,26,47,.5) 74%,rgba(8,26,47,.7) 100%)",
        }}
      />
      <div
        id="heroInner"
        style={{
          position: "relative",
          maxWidth: 1220,
          margin: "0 auto",
          padding: "120px 28px 60px",
          minHeight: "100vh",
          boxSizing: "border-box",
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(330px, 1fr))",
          gap: 52,
          alignItems: "center",
          alignContent: "center",
        }}
      >
        <div>
          <p
            data-reveal="0"
            style={{
              margin: "0 0 18px",
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              fontSize: 13,
              fontWeight: 600,
              letterSpacing: ".14em",
              textTransform: "uppercase",
              color: "#7cc0f5",
              opacity: 0,
              transform: "translateY(26px)",
              transition: "opacity .7s ease, transform .7s ease",
            }}
          >
            <span style={{ width: 26, height: 2, background: "#7cc0f5", display: "inline-block" }} />
            <span data-i18n="eyebrow">{tx("eyebrow", "Operador logístico · Lima, Perú")}</span>
          </p>
          <h1
            data-reveal="90"
            data-i18n="h1"
            style={{
              margin: 0,
              fontFamily: "Archivo, sans-serif",
              fontWeight: 800,
              fontSize: "clamp(34px, 4.4vw, 56px)",
              lineHeight: 1.05,
              letterSpacing: "-.015em",
              color: "#fff",
              opacity: 0,
              transform: "translateY(26px)",
              transition: "opacity .7s ease, transform .7s ease",
            }}
          >
            {tx("h1", "Los pedidos de su tienda, entregados en la puerta de sus clientes.")}
          </h1>
          <p
            data-reveal="180"
            data-i18n="sub"
            style={{
              margin: "22px 0 0",
              maxWidth: 560,
              fontSize: "clamp(16px, 1.4vw, 18px)",
              lineHeight: 1.65,
              color: "#c3d6ea",
              opacity: 0,
              transform: "translateY(26px)",
              transition: "opacity .7s ease, transform .7s ease",
            }}
          >
            {tx(
              "sub",
              "SAVA recibe cada día los pedidos de retailers como Ripley, Falabella, Zara, H&M y Temu, y los distribuye en todo Lima con rutas propias y seguimiento en vivo. Usted vende; nosotros llegamos.",
            )}
          </p>
          <div
            data-reveal="260"
            style={{
              margin: "32px 0 0",
              display: "flex",
              gap: 14,
              flexWrap: "wrap",
              opacity: 0,
              transform: "translateY(26px)",
              transition: "opacity .7s ease, transform .7s ease",
            }}
          >
            <a
              data-i18n="cta1"
              href="#contacto"
              className="ldg-btn-cta"
              style={{
                textDecoration: "none",
                background: "#2679d8",
                color: "#fff",
                fontWeight: 600,
                fontSize: 15,
                padding: "15px 28px",
                borderRadius: 99,
                boxShadow: "0 12px 30px rgba(9,40,75,.5)",
              }}
            >
              {tx("cta1", "Solicitar una propuesta")}
            </a>
            <a
              data-i18n="cta2"
              href="#como-funciona"
              className="ldg-btn-cta-outline"
              style={{
                textDecoration: "none",
                color: "#fff",
                fontWeight: 600,
                fontSize: 15,
                padding: "15px 28px",
                borderRadius: 99,
                border: "1.5px solid rgba(255,255,255,.4)",
              }}
            >
              {tx("cta2", "Ver cómo trabajamos →")}
            </a>
          </div>
        </div>

        <div
          data-reveal="240"
          style={{ opacity: 0, transform: "translateY(26px)", transition: "opacity .8s ease, transform .8s ease" }}
        >
          <div style={{ position: "relative", width: "112%", margin: "0 -6%", animation: "flotar 7s ease-in-out infinite" }}>
            <MapaHeroIso textos={textosMapa} />
          </div>
        </div>
      </div>
    </section>
  );
}
