import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useEfectosScroll } from "../../hooks/useEfectosScroll";
import RastreoPersonal from "./vistas/RastreoPersonal";
import logo from "../../assets/logo.png";
import "./portal.css";

// Página del portal de clientes: header sticky + hero + selector de perfil
// (persona natural / empresa) + hueco de la vista elegida (Tareas 10 y 11) +
// CTA de equipo + footer. Sin i18n (el mockup del portal es solo español).
export default function Portal() {
  const [modo, setModo] = useState(null); // null | "personal" | "empresa"
  const [toast, setToast] = useState("");
  const contRef = useRef(null);
  const timerToast = useRef(null);
  useEfectosScroll(contRef);

  // Título de la pestaña al entrar al portal.
  useEffect(() => {
    document.title = "Portal de clientes — SAVA";
  }, []);

  // Limpia el timer del toast al desmontar la página (evita setState tras unmount).
  useEffect(() => {
    return () => clearTimeout(timerToast.current);
  }, []);

  // Muestra un aviso flotante `ms` milisegundos (por defecto 3600, igual que el
  // mockup) y lo oculta solo; reinicia el timer si ya había uno en curso. La consume
  // RastreoPersonal (Tarea 10) por props; la Tarea 11 (PanelEmpresa) la usará también.
  const avisar = (texto, ms) => {
    setToast(texto);
    clearTimeout(timerToast.current);
    timerToast.current = setTimeout(() => setToast(""), ms || 3600);
  };

  // Handlers del selector: cambian el perfil activo (persona natural / empresa).
  const irPersonal = () => setModo("personal");
  const irEmpresa = () => setModo("empresa");

  return (
    <div ref={contRef} className="ptl-pagina">
      {/* TOPBAR */}
      <header
        style={{
          position: "sticky",
          top: 0,
          zIndex: 50,
          background: "rgba(245,248,251,.9)",
          backdropFilter: "blur(12px)",
          borderBottom: "1px solid rgba(15,43,74,.08)",
        }}
      >
        <div id="pTop" style={{ maxWidth: 1140, margin: "0 auto", padding: "0 24px", height: 64, display: "flex", alignItems: "center", gap: 14 }}>
          <Link to="/" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none", color: "#0f2b4a" }}>
            <img src={logo} alt="SAVA" style={{ width: 30, height: 32, objectFit: "contain" }} />
            <span style={{ fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: 17 }}>SAVA</span>
          </Link>
          <span style={{ background: "#eaf3fc", color: "#1b5fb3", fontSize: 10.5, fontWeight: 700, letterSpacing: ".08em", padding: "5px 11px", borderRadius: 99, whiteSpace: "nowrap" }}>
            PORTAL DE CLIENTES
          </span>
          <div style={{ marginLeft: "auto", display: "flex", gap: 12, alignItems: "center" }}>
            <Link
              data-hide-m="1"
              to="/"
              className="ptl-link-volver"
              style={{ textDecoration: "none", color: "#3d5570", fontSize: 13.5, fontWeight: 500, whiteSpace: "nowrap", transition: "color .2s ease" }}
            >
              ← Volver a sava.pe
            </Link>
            <Link
              to="/panel/login"
              className="ptl-btn-trabajador"
              style={{
                textDecoration: "none",
                background: "#0f2b4a",
                color: "#fff",
                fontSize: 13,
                fontWeight: 600,
                padding: "9px 16px",
                borderRadius: 99,
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                whiteSpace: "nowrap",
                transition: "background .2s ease",
              }}
            >
              <span style={{ width: 7, height: 7, borderRadius: 99, background: "#5db1f0", flex: "none", animation: "latido 2.2s ease-in-out infinite" }} />
              Soy trabajador · GeoTrack ↗
            </Link>
          </div>
        </div>
      </header>

      {/* HERO */}
      <section id="pHero" style={{ background: "#0c2440", color: "#fff", position: "relative", overflow: "hidden", padding: "52px 24px 104px" }}>
        <div aria-hidden="true" style={{ position: "absolute", top: -120, right: -80, width: 420, height: 420, borderRadius: "99em", background: "radial-gradient(circle,rgba(38,121,216,.35),rgba(38,121,216,0) 65%)" }} />
        <div aria-hidden="true" style={{ position: "absolute", bottom: -160, left: -100, width: 460, height: 460, borderRadius: "99em", background: "radial-gradient(circle,rgba(93,177,240,.16),rgba(93,177,240,0) 65%)" }} />
        <div style={{ maxWidth: 1140, margin: "0 auto", position: "relative" }}>
          <p style={{ margin: "0 0 14px", display: "inline-flex", alignItems: "center", gap: 10, fontSize: 12.5, fontWeight: 600, letterSpacing: ".14em", textTransform: "uppercase", color: "#7cc0f5", animation: "aparecer .6s ease both" }}>
            <span style={{ width: 8, height: 8, borderRadius: 99, background: "#22a35e", animation: "latido 1.8s ease-in-out infinite" }} />
            Seguimiento en vivo · datos de GeoTrack
          </p>
          <h1 style={{ margin: 0, fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: "clamp(30px,4.5vw,48px)", lineHeight: 1.06, letterSpacing: "-.015em", animation: "aparecer .6s ease .08s both" }}>
            ¿Dónde está mi pedido?
          </h1>
          <p style={{ margin: "16px 0 0", maxWidth: 620, fontSize: "clamp(15px,1.3vw,17px)", lineHeight: 1.6, color: "#c3d6ea", animation: "aparecer .6s ease .16s both" }}>
            Elija su perfil para seguir sus entregas en tiempo real. Sus datos están protegidos: cada consulta se verifica y cada acceso queda registrado.
          </p>
        </div>
      </section>

      {/* SELECTOR DE PERFIL */}
      <div data-psec="1" style={{ maxWidth: 1140, margin: "-64px auto 0", padding: "0 24px", position: "relative", zIndex: 2, width: "100%", boxSizing: "border-box" }}>
        <div id="selModo" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          <button
            type="button"
            onClick={irPersonal}
            className="ptl-card-modo"
            style={{
              textAlign: "left",
              cursor: "pointer",
              fontFamily: "Inter, sans-serif",
              background: "#fff",
              border: `2px solid ${modo === "personal" ? "#2679d8" : "rgba(15,43,74,.1)"}`,
              boxShadow: modo === "personal" ? "0 14px 32px rgba(38,121,216,.18)" : "0 10px 26px rgba(15,43,74,.06)",
              borderRadius: 20,
              padding: "22px 24px",
              display: "flex",
              alignItems: "center",
              gap: 16,
              transition: "border-color .3s ease, box-shadow .3s ease, transform .2s ease",
              animation: "aparecer .55s ease .2s both",
            }}
          >
            <span style={{ flex: "none", width: 46, height: 46, borderRadius: 99, background: "#eaf3fc", display: "grid", placeItems: "center" }}>
              <span style={{ width: 15, height: 15, borderRadius: 99, background: "#2679d8" }} />
            </span>
            <span style={{ flex: 1, minWidth: 0 }}>
              <span style={{ display: "block", fontSize: 11, fontWeight: 700, letterSpacing: ".1em", color: "#7288a0" }}>PERSONA NATURAL</span>
              <span style={{ display: "block", marginTop: 3, fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: 18, color: "#0f2b4a" }}>Sigo mi pedido</span>
              <span style={{ display: "block", marginTop: 3, fontSize: 13, color: "#4f6580" }}>Trazabilidad con su código + verificación de identidad</span>
            </span>
            <span style={{ flex: "none", width: 22, height: 22, borderRadius: 99, border: `2px solid ${modo === "personal" ? "#2679d8" : "#c7d5e3"}`, display: "grid", placeItems: "center", transition: "border-color .3s ease" }}>
              <span style={{ width: 10, height: 10, borderRadius: 99, background: modo === "personal" ? "#2679d8" : "transparent", transition: "background .3s ease" }} />
            </span>
          </button>
          <button
            type="button"
            onClick={irEmpresa}
            className="ptl-card-modo"
            style={{
              textAlign: "left",
              cursor: "pointer",
              fontFamily: "Inter, sans-serif",
              background: "#fff",
              border: `2px solid ${modo === "empresa" ? "#2679d8" : "rgba(15,43,74,.1)"}`,
              boxShadow: modo === "empresa" ? "0 14px 32px rgba(38,121,216,.18)" : "0 10px 26px rgba(15,43,74,.06)",
              borderRadius: 20,
              padding: "22px 24px",
              display: "flex",
              alignItems: "center",
              gap: 16,
              transition: "border-color .3s ease, box-shadow .3s ease, transform .2s ease",
              animation: "aparecer .55s ease .3s both",
            }}
          >
            <span style={{ flex: "none", width: 46, height: 46, borderRadius: 14, background: "#eaf3fc", display: "grid", placeItems: "center" }}>
              <span style={{ width: 15, height: 15, borderRadius: 4, background: "#0f2b4a" }} />
            </span>
            <span style={{ flex: 1, minWidth: 0 }}>
              <span style={{ display: "block", fontSize: 11, fontWeight: 700, letterSpacing: ".1em", color: "#7288a0" }}>EMPRESA / RETAIL</span>
              <span style={{ display: "block", marginTop: 3, fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: 18, color: "#0f2b4a" }}>Estado de mis pedidos</span>
              <span style={{ display: "block", marginTop: 3, fontSize: 13, color: "#4f6580" }}>Acceso con credenciales y verificación en dos pasos</span>
            </span>
            <span style={{ flex: "none", width: 22, height: 22, borderRadius: 99, border: `2px solid ${modo === "empresa" ? "#2679d8" : "#c7d5e3"}`, display: "grid", placeItems: "center", transition: "border-color .3s ease" }}>
              <span style={{ width: 10, height: 10, borderRadius: 99, background: modo === "empresa" ? "#2679d8" : "transparent", transition: "background .3s ease" }} />
            </span>
          </button>
        </div>
      </div>

      {/* Vista según el perfil elegido */}
      {modo === "personal" && <RastreoPersonal avisar={avisar} />}
      {/* Tarea 11: {modo === "empresa" && <PanelEmpresa avisar={avisar} />} */}

      {/* CTA EQUIPO */}
      <div data-psec="1" style={{ maxWidth: 1140, margin: "56px auto 0", padding: "0 24px", width: "100%", boxSizing: "border-box" }}>
        <div
          style={{
            background: "#eaf3fc",
            borderRadius: 20,
            padding: "26px 28px",
            display: "flex",
            alignItems: "center",
            gap: 18,
            flexWrap: "wrap",
          }}
        >
          <span style={{ flex: 1, minWidth: 220 }}>
            <span style={{ display: "block", fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: 16, color: "#0f2b4a" }}>¿Es parte del equipo SAVA?</span>
            <span style={{ display: "block", marginTop: 4, fontSize: 13.5, color: "#4f6580" }}>Ingrese a GeoTrack para gestionar rutas, pedidos y flota.</span>
          </span>
          <Link
            to="/panel/login"
            className="ptl-btn-trabajador"
            style={{
              textDecoration: "none",
              background: "#0f2b4a",
              color: "#fff",
              fontSize: 13.5,
              fontWeight: 600,
              padding: "11px 20px",
              borderRadius: 99,
              whiteSpace: "nowrap",
              transition: "background .2s ease",
            }}
          >
            Entrar a GeoTrack ↗
          </Link>
        </div>
      </div>

      {/* FOOTER */}
      <footer style={{ borderTop: "1px solid rgba(15,43,74,.08)", background: "#fff", marginTop: "auto" }}>
        <div style={{ maxWidth: 1140, margin: "0 auto", padding: 24, display: "flex", alignItems: "center", gap: "14px 22px", flexWrap: "wrap" }}>
          <img src={logo} alt="SAVA" style={{ width: 22, height: 24, objectFit: "contain" }} />
          <span style={{ fontFamily: "Archivo, sans-serif", fontWeight: 700, fontSize: 14, color: "#0f2b4a" }}>SAVA S.A.C.</span>
          <span style={{ fontSize: 12.5, color: "#7288a0" }}>Portal de clientes · datos en vivo desde GeoTrack</span>
          <div style={{ marginLeft: "auto", display: "flex", gap: 18, flexWrap: "wrap" }}>
            <Link to="/#reclamos" className="ptl-ft-link" style={{ fontSize: 13, fontWeight: 600, color: "#3d5570", textDecoration: "none", transition: "color .2s ease" }}>
              Reclamos
            </Link>
            <Link to="/" className="ptl-ft-volver" style={{ fontSize: 13, fontWeight: 600, color: "#2679d8", textDecoration: "none", transition: "color .2s ease" }}>
              ← Volver a sava.pe
            </Link>
          </div>
        </div>
      </footer>

      {/* TOAST */}
      {toast && (
        <div
          style={{
            position: "fixed",
            left: "50%",
            bottom: 26,
            transform: "translateX(-50%)",
            zIndex: 80,
            background: "#0f2b4a",
            color: "#fff",
            padding: "14px 22px",
            borderRadius: 14,
            boxShadow: "0 20px 50px rgba(3,15,30,.4)",
            display: "flex",
            gap: 11,
            alignItems: "center",
            fontSize: 14,
            fontWeight: 600,
            animation: "toastIn .35s ease both",
            maxWidth: "calc(100vw - 40px)",
            boxSizing: "border-box",
          }}
        >
          <span style={{ flex: "none", width: 20, height: 20, borderRadius: 99, background: "#22a35e", display: "grid", placeItems: "center", fontSize: 11 }}>✓</span>
          {toast}
        </div>
      )}
    </div>
  );
}
