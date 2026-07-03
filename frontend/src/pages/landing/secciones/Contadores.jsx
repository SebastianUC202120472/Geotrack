// Cifras clave de SAVA: 3 KPIs animados por conteo (data-count, hook de scroll) más
// el indicador fijo 24/7. Input: tx (traducción).
export default function Contadores({ tx }) {
  return (
    <section data-sec="m" style={{ maxWidth: 1200, margin: "96px auto 0", padding: "0 28px" }}>
      <div
        data-reveal="0"
        data-panel="1"
        style={{
          background: "#0f2b4a",
          borderRadius: 24,
          padding: "56px 48px",
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 36,
          opacity: 0,
          transform: "translateY(26px)",
          transition: "opacity .7s ease, transform .7s ease",
        }}
      >
        <div>
          <div style={{ fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: "clamp(44px, 4.5vw, 58px)", color: "#fff", lineHeight: 1 }}>
            <span data-count="300">0</span>
          </div>
          <p data-i18n="c1" style={{ margin: "10px 0 0", fontSize: 14.5, color: "#9fc0e2", lineHeight: 1.5 }}>
            {tx("c1", "pedidos distribuidos cada día")}
          </p>
        </div>
        <div>
          <div style={{ fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: "clamp(44px, 4.5vw, 58px)", color: "#fff", lineHeight: 1 }}>
            <span data-count="43">0</span>
          </div>
          <p data-i18n="c2" style={{ margin: "10px 0 0", fontSize: 14.5, color: "#9fc0e2", lineHeight: 1.5 }}>
            {tx("c2", "distritos de Lima con cobertura")}
          </p>
        </div>
        <div>
          <div style={{ fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: "clamp(44px, 4.5vw, 58px)", color: "#fff", lineHeight: 1 }}>
            <span data-count="5" data-suffix="+">0</span>
          </div>
          <p data-i18n="c3" style={{ margin: "10px 0 0", fontSize: 14.5, color: "#9fc0e2", lineHeight: 1.5 }}>
            {tx("c3", "retailers confían sus entregas a SAVA")}
          </p>
        </div>
        <div>
          <div
            style={{
              fontFamily: "Archivo, sans-serif",
              fontWeight: 800,
              fontSize: "clamp(44px, 4.5vw, 58px)",
              color: "#5db1f0",
              lineHeight: 1,
              animation: "latido 2.4s ease-in-out infinite",
            }}
          >
            24/7
          </div>
          <p data-i18n="c4" style={{ margin: "10px 0 0", fontSize: 14.5, color: "#9fc0e2", lineHeight: 1.5 }}>
            {tx("c4", "seguimiento en vivo con GeoTrack")}
          </p>
        </div>
      </div>
    </section>
  );
}
