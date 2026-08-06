import limaAerea from "../../../assets/landing/lima-aerea.jpg";

// Nosotros (#nosotros): foto a la izquierda (reemplaza el image-slot del mockup) y
// texto institucional a la derecha. Input: tx (traducción).
export default function Nosotros({ tx }) {
  return (
    <section id="nosotros" data-sec="p" style={{ maxWidth: 1200, margin: "0 auto", padding: "110px 28px 0" }}>
      <div data-rg="1" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 48, alignItems: "center" }}>
        <div
          data-reveal="0"
          style={{ opacity: 0, transform: "translateY(26px)", transition: "opacity .7s ease, transform .7s ease" }}
        >
          <img src={limaAerea} alt="Operación de SAVA en Lima" className="ldg-nosotros-foto" />
        </div>
        <div
          data-reveal="120"
          style={{ opacity: 0, transform: "translateY(26px)", transition: "opacity .7s ease, transform .7s ease" }}
        >
          <p data-i18n="nosE" style={{ margin: "0 0 12px", fontSize: 13, fontWeight: 600, letterSpacing: ".14em", textTransform: "uppercase", color: "#2679d8" }}>
            {tx("nosE", "Quiénes somos")}
          </p>
          <h2 data-i18n="nosT" style={{ margin: 0, fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: "clamp(30px, 3.6vw, 44px)", lineHeight: 1.1, letterSpacing: "-.01em" }}>
            {tx("nosT", "Una empresa limeña que trata cada paquete como si fuera propio.")}
          </h2>
          <p data-i18n="nosD" style={{ margin: "18px 0 0", fontSize: 16, lineHeight: 1.65, color: "#4f6580" }}>
            {tx(
              "nosD",
              "SAVA S.A.C. nació en Independencia, Lima Norte, y hoy es el aliado de última milla de algunos de los retailers más grandes que operan en el Perú. Combinamos flota propia, un equipo que conoce cada distrito y tecnología desarrollada en casa.",
            )}
          </p>
          <p data-i18n="nosD2" style={{ margin: "14px 0 0", fontSize: 16, lineHeight: 1.65, color: "#4f6580" }}>
            {tx("nosD2", "Para el retail somos capacidad confiable; para su cliente, la persona amable que le toca la puerta.")}
          </p>
        </div>
      </div>
    </section>
  );
}
