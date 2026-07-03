import { useState } from "react";
import { Link } from "react-router-dom";
import logo from "../../../assets/logo.png";

// Barra de navegación pública de SAVA: logo, links de ancla, selector ES/EN,
// accesos a portal de clientes / login de empleados y menú móvil con overlay.
// Input: lang/setLang (idioma activo), tx (función de traducción de i18n.js).
export default function NavBarLanding({ lang, setLang, tx }) {
  const [menuAbierto, setMenuAbierto] = useState(false);

  // Abre o cierra el menú móvil (handler de click, no en efecto).
  const alternarMenu = () => setMenuAbierto((v) => !v);
  const cerrarMenu = () => setMenuAbierto(false);

  return (
    <>
      <header
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          zIndex: 60,
          backdropFilter: "blur(14px)",
          background: "rgba(245,248,251,.85)",
          borderBottom: "1px solid rgba(15,43,74,.08)",
        }}
      >
        <div
          id="navBar"
          style={{
            maxWidth: 1200,
            margin: "0 auto",
            padding: "0 28px",
            height: 70,
            display: "flex",
            alignItems: "center",
            gap: 24,
          }}
        >
          <a
            href="#inicio"
            style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none", color: "#0f2b4a" }}
          >
            <img src={logo} alt="SAVA" style={{ width: 36, height: 38, objectFit: "contain" }} />
            <span style={{ fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: 19, letterSpacing: ".02em" }}>
              SAVA{" "}
              <span data-sac="1" style={{ fontWeight: 500, color: "#4f6580", fontSize: 12, letterSpacing: ".08em" }}>S.A.C.</span>
            </span>
          </a>

          <nav id="navLinks" style={{ display: "flex", gap: 22, marginLeft: "auto", alignItems: "center" }}>
            <a href="#como-funciona" className="ldg-link-nav" style={{ textDecoration: "none", color: "#3d5570", fontSize: 14, fontWeight: 500 }}>
              {tx("nav1", "El servicio")}
            </a>
            <a href="#cobertura" className="ldg-link-nav" style={{ textDecoration: "none", color: "#3d5570", fontSize: 14, fontWeight: 500 }}>
              {tx("nav2", "Cobertura")}
            </a>
            <a href="#geotrack" className="ldg-link-nav" style={{ textDecoration: "none", color: "#3d5570", fontSize: 14, fontWeight: 500 }}>
              {tx("nav3", "GeoTrack")}
            </a>
            <a href="#nosotros" className="ldg-link-nav" style={{ textDecoration: "none", color: "#3d5570", fontSize: 14, fontWeight: 500 }}>
              {tx("nav4", "Nosotros")}
            </a>
            <Link to="/portal" className="ldg-link-nav-cta" style={{ textDecoration: "none", color: "#2679d8", fontSize: 14, fontWeight: 600 }}>
              {tx("nav5", "Portal de clientes ↗")}
            </Link>
          </nav>

          <div style={{ display: "flex", alignItems: "center", gap: 6, background: "#e9f1f9", borderRadius: 99, padding: 3 }}>
            <button
              type="button"
              onClick={() => setLang("es")}
              style={{
                border: 0,
                cursor: "pointer",
                fontFamily: "Inter, sans-serif",
                fontSize: 12,
                fontWeight: 600,
                padding: "5px 11px",
                borderRadius: 99,
                background: lang === "es" ? "#2679d8" : "transparent",
                color: lang === "es" ? "#fff" : "#3d5570",
              }}
            >
              ES
            </button>
            <button
              type="button"
              onClick={() => setLang("en")}
              style={{
                border: 0,
                cursor: "pointer",
                fontFamily: "Inter, sans-serif",
                fontSize: 12,
                fontWeight: 600,
                padding: "5px 11px",
                borderRadius: 99,
                background: lang === "en" ? "#2679d8" : "transparent",
                color: lang === "en" ? "#fff" : "#3d5570",
              }}
            >
              EN
            </button>
          </div>

          <Link
            id="navEmp"
            to="/panel/login"
            className="ldg-btn-emp"
            style={{
              textDecoration: "none",
              color: "#0f2b4a",
              fontSize: 13.5,
              fontWeight: 600,
              padding: "9px 16px",
              borderRadius: 99,
              border: "1.5px solid rgba(15,43,74,.2)",
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              whiteSpace: "nowrap",
              transition: "border-color .2s ease, color .2s ease",
            }}
          >
            <span style={{ width: 7, height: 7, borderRadius: 99, background: "#22a35e", flex: "none", animation: "latido 2.2s ease-in-out infinite" }} />
            <span>{tx("navEmp", "Soy trabajador ↗")}</span>
          </Link>

          <a
            id="navCta"
            href="#contacto"
            className="ldg-btn-cta"
            style={{
              textDecoration: "none",
              background: "#2679d8",
              color: "#fff",
              fontSize: 14,
              fontWeight: 600,
              padding: "10px 20px",
              borderRadius: 99,
            }}
          >
            {tx("navCta", "Hablemos")}
          </a>

          <button
            id="btnBurger"
            type="button"
            aria-label="Menú"
            onClick={alternarMenu}
            style={{
              display: "none",
              border: 0,
              cursor: "pointer",
              background: "#0f2b4a",
              color: "#fff",
              width: 42,
              height: 42,
              borderRadius: 12,
              placeItems: "center",
              fontSize: 17,
              lineHeight: 1,
              padding: 0,
              fontFamily: "Inter, sans-serif",
              flex: "none",
            }}
          >
            {menuAbierto ? "✕" : "☰"}
          </button>
        </div>
      </header>

      {menuAbierto && (
        <>
          <div
            onClick={cerrarMenu}
            aria-hidden="true"
            style={{
              position: "fixed",
              top: 70,
              left: 0,
              right: 0,
              bottom: 0,
              zIndex: 58,
              background: "rgba(9,28,50,.45)",
              backdropFilter: "blur(4px)",
            }}
          />
          <div
            style={{
              position: "fixed",
              top: 70,
              left: 0,
              right: 0,
              zIndex: 59,
              background: "#fff",
              borderBottom: "1px solid rgba(15,43,74,.1)",
              boxShadow: "0 32px 60px rgba(9,28,50,.28)",
              animation: "menuIn .28s ease both",
              maxHeight: "calc(100vh - 70px)",
              overflow: "auto",
            }}
          >
            <nav style={{ display: "grid", gap: 2, padding: "14px 16px 20px" }}>
              <a onClick={cerrarMenu} href="#como-funciona" className="ldg-menu-item" style={{ textDecoration: "none", color: "#0f2b4a", fontSize: 16, fontWeight: 600, padding: "13px 12px", borderRadius: 12 }}>
                {tx("nav1", "El servicio")}
              </a>
              <a onClick={cerrarMenu} href="#cobertura" className="ldg-menu-item" style={{ textDecoration: "none", color: "#0f2b4a", fontSize: 16, fontWeight: 600, padding: "13px 12px", borderRadius: 12 }}>
                {tx("nav2", "Cobertura")}
              </a>
              <a onClick={cerrarMenu} href="#geotrack" className="ldg-menu-item" style={{ textDecoration: "none", color: "#0f2b4a", fontSize: 16, fontWeight: 600, padding: "13px 12px", borderRadius: 12 }}>
                {tx("nav3", "GeoTrack")}
              </a>
              <a onClick={cerrarMenu} href="#nosotros" className="ldg-menu-item" style={{ textDecoration: "none", color: "#0f2b4a", fontSize: 16, fontWeight: 600, padding: "13px 12px", borderRadius: 12 }}>
                {tx("nav4", "Nosotros")}
              </a>
              <a onClick={cerrarMenu} href="#reclamos" className="ldg-menu-item" style={{ textDecoration: "none", color: "#0f2b4a", fontSize: 16, fontWeight: 600, padding: "13px 12px", borderRadius: 12 }}>
                {tx("navRec", "Reclamos")}
              </a>
              <div aria-hidden="true" style={{ height: 1, background: "rgba(15,43,74,.08)", margin: "8px 4px" }} />
              <Link to="/portal" onClick={cerrarMenu} className="ldg-menu-item" style={{ textDecoration: "none", color: "#2679d8", fontSize: 16, fontWeight: 700, padding: "13px 12px", borderRadius: 12 }}>
                {tx("menuPortal", "Portal de clientes · seguir mi pedido ↗")}
              </Link>
              <Link to="/panel/login" onClick={cerrarMenu} className="ldg-menu-item" style={{ textDecoration: "none", color: "#3d5570", fontSize: 15, fontWeight: 600, padding: "13px 12px", borderRadius: 12 }}>
                {tx("menuGt", "Empleados · Entrar a GeoTrack ↗")}
              </Link>
              <a
                onClick={cerrarMenu}
                href="#contacto"
                style={{
                  margin: "10px 4px 0",
                  textAlign: "center",
                  textDecoration: "none",
                  background: "#2679d8",
                  color: "#fff",
                  fontSize: 15,
                  fontWeight: 600,
                  padding: 14,
                  borderRadius: 99,
                }}
              >
                {tx("navCta", "Hablemos")}
              </a>
            </nav>
          </div>
        </>
      )}
    </>
  );
}
