import logoRipley from "../../../assets/landing/retail-ripley.png";
import logoFalabella from "../../../assets/landing/retail-falabella.png";
import logoZara from "../../../assets/landing/retail-zara.png";
import logoHm from "../../../assets/landing/retail-hm.png";
import logoTemu from "../../../assets/landing/retail-temu.png";

// Franja "Distribuimos pedidos de": 5 logos de retailers con alturas propias y
// hover de escala. Input: tx (traducción).
export default function Marcas({ tx }) {
  return (
    <section style={{ borderBottom: "1px solid rgba(15,43,74,.08)", background: "#fff", padding: "38px 28px" }}>
      <div style={{ maxWidth: 1200, margin: "0 auto" }}>
        <p
          data-i18n="marcasT"
          style={{
            margin: "0 0 20px",
            textAlign: "center",
            fontSize: 12,
            fontWeight: 600,
            letterSpacing: ".16em",
            textTransform: "uppercase",
            color: "#7288a0",
          }}
        >
          {tx("marcasT", "Distribuimos pedidos de")}
        </p>
        <div style={{ display: "flex", gap: 44, rowGap: 26, flexWrap: "wrap", justifyContent: "center", alignItems: "center" }}>
          <img src={logoRipley} alt="Ripley" className="ldg-logo-marca" style={{ height: 26, width: "auto" }} />
          <img src={logoFalabella} alt="Falabella" className="ldg-logo-marca" style={{ height: 44, width: "auto" }} />
          <img src={logoZara} alt="Zara" className="ldg-logo-marca" style={{ height: 46, width: "auto" }} />
          <img src={logoHm} alt="H&M" className="ldg-logo-marca" style={{ height: 52, width: "auto" }} />
          <img src={logoTemu} alt="Temu" className="ldg-logo-marca" style={{ height: 38, width: "auto" }} />
          <span data-i18n="marcasMas" style={{ fontSize: 13, fontWeight: 600, letterSpacing: ".08em", color: "#2679d8", padding: "0 8px" }}>
            {tx("marcasMas", "Y MÁS RETAILERS")}
          </span>
        </div>
      </div>
    </section>
  );
}
