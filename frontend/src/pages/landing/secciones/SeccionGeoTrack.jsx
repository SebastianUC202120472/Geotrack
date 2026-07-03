import { Link } from "react-router-dom";
import geotrackLogo from "../../../assets/logo.png";
import MapaFlotaIso from "../../../components/publico/MapaFlotaIso";

// Chips de features de GeoTrack: clave i18n + texto en español.
const FEATURES = [
  { clave: "gtc1", texto: "Estado en vivo" },
  { clave: "gtc2", texto: "Foto de entrega" },
  { clave: "gtc3", texto: "Reportes por retail" },
  { clave: "gtc4", texto: "Rutas con IA" },
];

// Los 4 hitos del timeline demo del pedido PD-2481 · Ripley: clave de título,
// clave de detalle (u opcional detD para la última fila sin hora), y si ya ocurrió.
const HITOS = [
  { claveT: "gtw1", detalle: "09:12 · CD Villa El Salvador", hecho: true, enCurso: false },
  { claveT: "gtw2", detalle: "11:40 · Independencia", hecho: true, enCurso: false },
  { claveT: "gtw3", detalle: "14:05 · Parada 12 de 28 · Miraflores", hecho: false, enCurso: true },
  { claveT: "gtw4", claveD: "gtw4b", detalle: "Con foto y confirmación", hecho: false, enCurso: false },
];

// SeccionGeoTrack (#geotrack): presenta la plataforma propia — descripción + chips,
// panel "Reporte de hoy" con barra animada, timeline demo de un pedido, tarjeta de
// IA y el mapa de flota en vivo (MapaFlotaIso). Input: tx (traducción).
export default function SeccionGeoTrack({ tx }) {
  return (
    <section id="geotrack" data-sec="p" style={{ maxWidth: 1200, margin: "0 auto", padding: "110px 28px 0" }}>
      <div
        data-reveal="0"
        data-panel="1"
        data-rg="1"
        style={{
          background: "linear-gradient(135deg, #eaf3fc, #f5f8fb)",
          border: "1px solid rgba(38,121,216,.18)",
          borderRadius: 24,
          padding: "56px 48px",
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: 44,
          alignItems: "center",
          opacity: 0,
          transform: "translateY(26px)",
          transition: "opacity .7s ease, transform .7s ease",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "0 0 16px" }}>
            <img src={geotrackLogo} alt="GeoTrack" style={{ width: 34, height: 36, objectFit: "contain" }} />
            <span style={{ fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: 20, color: "#0f2b4a" }}>
              GeoTrack{" "}
              <span data-i18n="gtDe" style={{ fontWeight: 500, fontSize: 13, color: "#7288a0" }}>
                {tx("gtDe", "· plataforma propia de SAVA")}
              </span>
            </span>
          </div>
          <h2
            data-i18n="gtT"
            style={{
              margin: 0,
              fontFamily: "Archivo, sans-serif",
              fontWeight: 800,
              fontSize: "clamp(25px, 2.6vw, 33px)",
              lineHeight: 1.16,
              letterSpacing: "-.01em",
              color: "#0f2b4a",
            }}
          >
            {tx("gtT", "Cada pedido, visible desde que sale de tienda hasta que se entrega.")}
          </h2>
          <p data-i18n="gtD" style={{ margin: "18px 0 0", fontSize: 16, lineHeight: 1.65, color: "#4f6580" }}>
            {tx(
              "gtD",
              "El retail no llama a preguntar dónde está su pedido: lo ve. GeoTrack muestra el estado de cada bulto en vivo, con evidencia de entrega y reportes diarios por tienda.",
            )}
          </p>

          <div style={{ margin: "24px 0 0", display: "flex", gap: 10, flexWrap: "wrap" }}>
            {FEATURES.map((f) => (
              <span
                key={f.clave}
                data-i18n={f.clave}
                style={{
                  background: "#fff",
                  border: "1px solid rgba(38,121,216,.25)",
                  color: "#1b5fb3",
                  fontSize: 13,
                  fontWeight: 600,
                  padding: "8px 14px",
                  borderRadius: 99,
                }}
              >
                {tx(f.clave, f.texto)}
              </span>
            ))}
          </div>

          <div
            data-reveal="140"
            style={{
              margin: "24px 0 0",
              background: "#fff",
              border: "1px solid rgba(15,43,74,.08)",
              borderRadius: 16,
              padding: "16px 18px",
              opacity: 0,
              transform: "translateY(26px)",
              transition: "opacity .7s ease, transform .7s ease",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
              <span data-i18n="repT" style={{ fontSize: 13, fontWeight: 700, color: "#0f2b4a" }}>
                {tx("repT", "Reporte de hoy, en vivo")}
              </span>
              <span style={{ fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: 19, color: "#22a35e" }}>
                <span data-count="92" data-suffix="%">0%</span>
              </span>
            </div>
            <div style={{ margin: "10px 0 0", height: 8, borderRadius: 99, background: "#e8f0f8", overflow: "hidden" }}>
              <div data-barra="92" style={{ height: "100%", width: "0%", borderRadius: 99, background: "linear-gradient(90deg, #2679d8, #22a35e)", transition: "width 1.4s ease .2s" }} />
            </div>
            <p data-i18n="repD" style={{ margin: "8px 0 0", fontSize: 12.5, color: "#7288a0" }}>
              {tx("repD", "276 entregados · 16 en ruta · 8 por salir — se actualiza en vivo")}
            </p>
          </div>
        </div>

        <div data-tilt="1" style={{ background: "#fff", border: "1px solid rgba(15,43,74,.1)", borderRadius: 22, boxShadow: "0 24px 60px rgba(15,43,74,.14)", padding: 22, maxWidth: 420, margin: "0 auto" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", margin: "0 0 16px" }}>
            <span data-i18n="gtwT" style={{ fontFamily: "Archivo, sans-serif", fontWeight: 700, fontSize: 14, color: "#0f2b4a" }}>
              {tx("gtwT", "Pedido PD-2481 · Ripley")}
            </span>
            <span
              data-i18n="gtwE"
              style={{
                background: "#e3f2e8",
                color: "#1e7a43",
                fontSize: 11.5,
                fontWeight: 700,
                padding: "4px 10px",
                borderRadius: 99,
                animation: "latido 2.2s ease-in-out infinite",
              }}
            >
              {tx("gtwE", "EN RUTA")}
            </span>
          </div>
          <div style={{ display: "grid", gap: 0 }}>
            {HITOS.map((h, i) => (
              <div key={h.claveT} style={{ display: "flex", gap: 14 }}>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                  <span
                    style={{
                      width: 11,
                      height: 11,
                      borderRadius: 99,
                      background: h.hecho || h.enCurso ? "#2679d8" : "#dce8f4",
                      flex: "none",
                      boxShadow: h.enCurso ? "0 0 0 5px rgba(38,121,216,.18)" : "none",
                    }}
                  />
                  {i < HITOS.length - 1 && (
                    <span style={{ width: 2, flex: 1, background: h.hecho ? "#2679d8" : "#dce8f4" }} />
                  )}
                </div>
                <div style={{ padding: i < HITOS.length - 1 ? "0 0 18px" : 0 }}>
                  <p data-i18n={h.claveT} style={{ margin: 0, fontSize: 13.5, fontWeight: 600, color: h.hecho || h.enCurso ? "#0f2b4a" : "#8ba0b6" }}>
                    {tx(h.claveT, TEXTOS_HITOS[h.claveT])}
                  </p>
                  <p
                    data-i18n={h.claveD || undefined}
                    style={{ margin: "2px 0 0", fontSize: 12, color: h.hecho || h.enCurso ? "#8ba0b6" : "#b7c6d6" }}
                  >
                    {h.claveD ? tx(h.claveD, h.detalle) : h.detalle}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div data-reveal="140" style={{ opacity: 0, transform: "translateY(26px)", transition: "opacity .7s ease, transform .7s ease" }}>
          <div
            style={{
              margin: "18px auto 0",
              maxWidth: 420,
              background: "#fff",
              border: "1px solid rgba(38,121,216,.25)",
              borderRadius: 16,
              padding: "18px 20px",
              display: "flex",
              gap: 14,
              alignItems: "flex-start",
              boxSizing: "border-box",
            }}
          >
            <span
              style={{
                flex: "none",
                background: "#0f2b4a",
                color: "#5db1f0",
                fontFamily: "Archivo, sans-serif",
                fontWeight: 800,
                fontSize: 13,
                letterSpacing: ".08em",
                padding: "6px 10px",
                borderRadius: 8,
                animation: "latido 2.6s ease-in-out infinite",
              }}
            >
              IA
            </span>
            <div>
              <h3 data-i18n="gtIAt" style={{ margin: "0 0 6px", fontFamily: "Archivo, sans-serif", fontWeight: 700, fontSize: 16, color: "#0f2b4a" }}>
                {tx("gtIAt", "Inteligencia artificial en cada ruta")}
              </h3>
              <p data-i18n="gtIAd" style={{ margin: 0, fontSize: 14, lineHeight: 1.6, color: "#4f6580" }}>
                {tx(
                  "gtIAd",
                  "Usamos IA para agrupar pedidos por zona, anticipar el tráfico de Lima y recortar el tiempo de distribución: aprende de cada reparto para que el siguiente llegue antes.",
                )}
              </p>
            </div>
          </div>
        </div>

        <div data-reveal="120" style={{ gridColumn: "1/-1", margin: "10px 0 0", opacity: 0, transform: "translateY(26px)", transition: "opacity .8s ease, transform .8s ease" }}>
          <div style={{ position: "relative" }}>
            <MapaFlotaIso />
            <div
              style={{
                position: "absolute",
                top: 14,
                left: 14,
                display: "flex",
                alignItems: "center",
                gap: 9,
                background: "rgba(255,255,255,.94)",
                backdropFilter: "blur(6px)",
                border: "1px solid rgba(15,43,74,.08)",
                borderRadius: 99,
                padding: "8px 15px",
                boxShadow: "0 8px 22px rgba(3,15,30,.14)",
                pointerEvents: "none",
              }}
            >
              <span style={{ width: 8, height: 8, borderRadius: 99, background: "#22a35e", animation: "latido 1.8s ease-in-out infinite" }} />
              <span data-i18n="flotaPill" style={{ fontSize: 12.5, fontWeight: 600, color: "#0f2b4a" }}>
                {tx("flotaPill", "Flota SAVA en vivo · 3 conductores en ruta")}
              </span>
            </div>
          </div>
          <p data-i18n="gtMapa" style={{ margin: "14px 0 0", textAlign: "center", fontSize: 13.5, lineHeight: 1.6, color: "#4f6580" }}>
            {tx("gtMapa", "Cada conductor registra la evidencia en la app GeoTrack y sigue al siguiente cliente — SAVA visualiza todo en tiempo real")}
          </p>
        </div>

        <div
          data-reveal="80"
          style={{
            gridColumn: "1/-1",
            margin: "8px 0 0",
            background: "#0f2b4a",
            borderRadius: 18,
            padding: "24px 28px",
            display: "flex",
            alignItems: "center",
            gap: 18,
            flexWrap: "wrap",
            opacity: 0,
            transform: "translateY(26px)",
            transition: "opacity .7s ease, transform .7s ease",
          }}
        >
          <div style={{ flex: 1, minWidth: 240 }}>
            <h3 data-i18n="accT" style={{ margin: 0, fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: 19, color: "#fff" }}>
              {tx("accT", "¿Espera un pedido o ya trabaja con SAVA?")}
            </h3>
            <p data-i18n="accD" style={{ margin: "6px 0 0", fontSize: 14, lineHeight: 1.55, color: "#9fc0e2" }}>
              {tx("accD", "Siga sus entregas en el portal de clientes, sin llamadas ni correos. El personal de SAVA entra directo a GeoTrack.")}
            </p>
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <Link
              data-i18n="accB1"
              to="/portal"
              className="ldg-btn-cta"
              style={{ textDecoration: "none", background: "#2679d8", color: "#fff", fontSize: 14, fontWeight: 600, padding: "13px 22px", borderRadius: 99 }}
            >
              {tx("accB1", "Portal de clientes ↗")}
            </Link>
            <Link
              data-i18n="accB2"
              to="/panel/login"
              className="ldg-btn-cta-outline"
              style={{ textDecoration: "none", color: "#dbe9f8", fontSize: 14, fontWeight: 600, padding: "13px 22px", borderRadius: 99, border: "1.5px solid rgba(255,255,255,.35)" }}
            >
              {tx("accB2", "Soy empleado · GeoTrack")}
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

// Textos en español de los 4 hitos del timeline (usados como fallback de tx).
const TEXTOS_HITOS = {
  gtw1: "Recogido en tienda",
  gtw2: "Verificado en centro SAVA",
  gtw3: "En ruta de reparto",
  gtw4: "Entregado al cliente",
};
