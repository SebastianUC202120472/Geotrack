import { Link } from "react-router-dom";
import logo from "../../../assets/logo.png";

// Pie de página público de SAVA: 4 columnas (marca+social, navegación, clientes,
// contacto) y barra legal inferior. Input: tx (función de traducción de i18n.js).
export default function FooterLanding({ tx }) {
  return (
    <footer style={{ background: "#0c2440", color: "#c3d6ea" }}>
      <div style={{ maxWidth: 1200, margin: "0 auto", padding: "70px 28px 0" }}>
        <div data-rg="1" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))", gap: 44 }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <img src={logo} alt="SAVA" style={{ width: 32, height: 34, objectFit: "contain" }} />
              <span style={{ fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: 19, color: "#fff" }}>
                SAVA <span style={{ fontWeight: 500, color: "#9fc0e2", fontSize: 12, letterSpacing: ".08em" }}>S.A.C.</span>
              </span>
            </div>
            <p style={{ margin: "16px 0 0", fontSize: 13.5, lineHeight: 1.7, color: "#9fc0e2", maxWidth: 300 }}>
              {tx(
                "ftDesc",
                "Operador logístico de última milla nacido en Independencia, Lima. Distribuimos los pedidos de los retailers más grandes del Perú con flota propia y tecnología GeoTrack.",
              )}
            </p>
            <p style={{ margin: "24px 0 0", fontSize: 11.5, fontWeight: 700, letterSpacing: ".12em", textTransform: "uppercase", color: "#7cc0f5" }}>
              {tx("ftSocial", "Síganos")}
            </p>
            <div style={{ margin: "12px 0 0", display: "flex", gap: 10 }}>
              <a href="#" aria-label="Facebook" title="Facebook" className="ldg-social" style={socialEstilo}>f</a>
              <a href="#" aria-label="Instagram" title="Instagram" className="ldg-social" style={{ ...socialEstilo, fontSize: 13 }}>ig</a>
              <a href="#" aria-label="LinkedIn" title="LinkedIn" className="ldg-social" style={{ ...socialEstilo, fontSize: 13 }}>in</a>
              <a
                href="https://wa.me/51922507593"
                target="_blank"
                rel="noreferrer"
                aria-label="WhatsApp"
                title="WhatsApp"
                className="ldg-social-wa"
                style={{ ...socialEstilo, fontSize: 12 }}
              >
                wa
              </a>
            </div>
          </div>

          <div>
            <p style={tituloColStyle}>{tx("ftNav", "Navegación")}</p>
            <div style={{ display: "grid", gap: 11, justifyItems: "start" }}>
              <a href="#como-funciona" className="ldg-ft-link" style={linkColStyle}>{tx("nav1", "El servicio")}</a>
              <a href="#cobertura" className="ldg-ft-link" style={linkColStyle}>{tx("nav2", "Cobertura")}</a>
              <a href="#geotrack" className="ldg-ft-link" style={linkColStyle}>{tx("nav3", "GeoTrack")}</a>
              <a href="#nosotros" className="ldg-ft-link" style={linkColStyle}>{tx("nav4", "Nosotros")}</a>
              <a href="#contacto" className="ldg-ft-link" style={linkColStyle}>{tx("navCta", "Hablemos")}</a>
            </div>
          </div>

          <div>
            <p style={tituloColStyle}>{tx("ftCli", "Clientes")}</p>
            <div style={{ display: "grid", gap: 11, justifyItems: "start" }}>
              <Link to="/portal" className="ldg-ft-link" style={linkColStyle}>{tx("ftRastrear", "Rastrear mi pedido ↗")}</Link>
              <Link to="/portal" className="ldg-ft-link" style={linkColStyle}>{tx("nav5", "Portal de clientes ↗")}</Link>
              <a href="#reclamos" className="ldg-ft-link" style={linkColStyle}>{tx("navRec", "Reclamos")}</a>
              <Link to="/panel/login" className="ldg-ft-link" style={linkColStyle}>{tx("menuGt", "Empleados · Entrar a GeoTrack ↗")}</Link>
            </div>
          </div>

          <div>
            <p style={tituloColStyle}>{tx("ftCon", "Contacto")}</p>
            <div style={{ display: "grid", gap: 14 }}>
              <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                <span style={{ width: 8, height: 8, borderRadius: 99, background: "#5db1f0", marginTop: 6, flex: "none" }} />
                <p style={{ margin: 0, fontSize: 13.5, lineHeight: 1.6, color: "#c3d6ea" }}>
                  Calle Los Sinchis Nro. 166,
                  <br />
                  Urb. Tahuantinsuyo Zona III,
                  <br />
                  Independencia, Lima
                </p>
              </div>
              <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                <span style={{ width: 8, height: 8, borderRadius: 99, background: "#5db1f0", marginTop: 6, flex: "none" }} />
                <a href="tel:+51922507593" className="ldg-ft-tel" style={{ margin: 0, fontSize: 13.5, color: "#c3d6ea", textDecoration: "none", transition: "color .2s ease" }}>
                  +51 922 507 593
                </a>
              </div>
              <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                <span style={{ width: 8, height: 8, borderRadius: 99, background: "#22a35e", marginTop: 6, flex: "none", animation: "latido 2.2s ease-in-out infinite" }} />
                <p style={{ margin: 0, fontSize: 13.5, lineHeight: 1.6, color: "#c3d6ea" }}>
                  {tx("conHorD", "Recepción y reparto de lunes a sábado")}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div style={{ margin: "52px 0 0", borderTop: "1px solid rgba(255,255,255,.12)", padding: "22px 0 28px", display: "flex", alignItems: "center", gap: "12px 26px", flexWrap: "wrap" }}>
          <span style={{ fontSize: 12.5, color: "#7f9cbd" }}>
            © 2026 SAVA S.A.C. · {tx("ftG", "Seguimiento por")} GeoTrack
          </span>
          <div style={{ marginLeft: "auto", display: "flex", gap: 20, flexWrap: "wrap" }}>
            <a href="#reclamos" className="ldg-ft-legal" style={legalStyle}>{tx("ftLR", "Libro de Reclamaciones")}</a>
            <a href="#" className="ldg-ft-legal" style={legalStyle}>{tx("ftTerm", "Términos del servicio")}</a>
            <a href="#" className="ldg-ft-legal" style={legalStyle}>{tx("ftPriv", "Política de privacidad")}</a>
          </div>
        </div>
      </div>
    </footer>
  );
}

// Estilos compartidos entre los ítems de las columnas (evita repetir objetos inline).
const socialEstilo = {
  width: 40,
  height: 40,
  borderRadius: 99,
  border: "1.5px solid rgba(255,255,255,.22)",
  display: "grid",
  placeItems: "center",
  textDecoration: "none",
  color: "#dbe9f8",
  fontFamily: "Archivo, sans-serif",
  fontWeight: 800,
  fontSize: 15,
  transition: "background .25s ease, border-color .25s ease, transform .25s ease",
};

const tituloColStyle = {
  margin: "0 0 16px",
  fontSize: 11.5,
  fontWeight: 700,
  letterSpacing: ".12em",
  textTransform: "uppercase",
  color: "#7cc0f5",
};

const linkColStyle = {
  display: "inline-block",
  textDecoration: "none",
  color: "#c3d6ea",
  fontSize: 14,
  transition: "color .2s ease, transform .2s ease",
};

const legalStyle = {
  fontSize: 12.5,
  color: "#9fc0e2",
  textDecoration: "none",
  transition: "color .2s ease",
};
