import { useEffect, useState } from "react";
import geotrackLogo from "../../../assets/logo.png";
import MapaFlotaIso from "../../../components/publico/MapaFlotaIso";
import { estadisticasPublicas } from "../../portal/servicios/portal.js";
import { ESTADOS } from "../../portal/datos/portalUi.js";

// Chips de features de GeoTrack: clave i18n + texto en español.
const FEATURES = [
  { clave: "gtc1", texto: "Estado en vivo" },
  { clave: "gtc2", texto: "Foto de entrega" },
  { clave: "gtc3", texto: "Reportes por retail" },
  { clave: "gtc4", texto: "Rutas con IA" },
];

// Etapas del seguimiento. Se muestran cuando NO hay datos en vivo (backend caído o
// sin operación del día): describen el proceso, sin horas ni lugares inventados.
// Con datos reales se usan los eventos del historial del pedido.
const ETAPAS = [
  { claveT: "gtw1", claveD: "gtw1b", detalle: "El conductor retira el paquete" },
  { claveT: "gtw2", claveD: "gtw2b", detalle: "Control de empaque y destino" },
  { claveT: "gtw3", claveD: "gtw3b", detalle: "Camino a la dirección del cliente" },
  { claveT: "gtw4", claveD: "gtw4b", detalle: "Con foto y confirmación" },
];

// formatoDia: pasa una fecha ISO (AAAA-MM-DD) a "12 de agosto". Input: la cadena ISO.
const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
function formatoDia(iso) {
  if (!iso) return "";
  const [, m, d] = iso.split("-");
  return `${Number(d)} de ${MESES[Number(m) - 1] || ""}`;
}

// Textos en español de las 4 etapas (usados como fallback de tx).
const TEXTOS_ETAPAS = {
  gtw1: "Recogido en tienda",
  gtw2: "Verificado en centro SAVA",
  gtw3: "En ruta de reparto",
  gtw4: "Entregado al cliente",
};

// SeccionGeoTrack (#geotrack): presenta la plataforma propia — descripción + chips,
// panel "Reporte de hoy" y tarjeta del pedido conectados a datos REALES del backend
// (agregados y enmascarados, sin datos personales; con fallback demo si no hay
// backend), tarjeta de IA debajo del estado del pedido, y el mapa de flota SIMULADO
// (a propósito: no se expone la ubicación real de los conductores). Input: tx.
export default function SeccionGeoTrack({ tx }) {
  // Estadísticas públicas reales (null = modo demo). Se cargan al montar y se
  // refrescan cada 15 s; el setState va dentro del callback de la promesa.
  const [datos, setDatos] = useState(null);
  useEffect(() => {
    let activo = true;
    const cargar = () => {
      estadisticasPublicas()
        .then((d) => {
          // Solo se usa el dato real si HAY actividad (total > 0): una BD vacia no
          // debe volcar el landing a "0 entregados · 0%" — en ese caso queda la demo.
          if (activo && d && d.reporte && d.reporte.total > 0) setDatos(d);
        })
        .catch(() => {}); // sin backend: el landing sigue con la demo
    };
    cargar();
    const id = setInterval(cargar, 15000);
    return () => {
      activo = false;
      clearInterval(id);
    };
  }, []);

  // Derivados del reporte. Sin datos en vivo NO se inventan cifras: se informa
  // que el reporte no está disponible y la barra queda en cero.
  const rep = datos ? datos.reporte : null;
  const pct = rep ? rep.pct : 0;
  // El backend informa de qué día operativo son las cifras. Si no es hoy, se dice:
  // rotular como "de hoy" un día anterior sería tan falso como inventar el número.
  const esHoy = rep ? rep.esHoy !== false : true;
  const tituloReporte = esHoy
    ? tx("repT", "Reporte de hoy, en vivo")
    : tx("repTUlt", "Último día operativo");
  const resumen = rep
    ? `${rep.entregados} entregados · ${rep.enRuta} en ruta · ${rep.porSalir} por salir` +
      (rep.incidencias ? ` · ${rep.incidencias} con incidencia` : "") +
      (esHoy ? " — se actualiza en vivo" : ` — cierre del ${formatoDia(rep.fecha)}`)
    : tx("repD", "Reporte en vivo no disponible en este momento.");

  // Derivados de la tarjeta del pedido (real enmascarado u demo).
  const ped = datos && datos.pedido ? datos.pedido : null;
  const badge = ped ? ESTADOS[ped.estado] || ESTADOS.POR_SALIR : null;
  const eventos = ped && ped.eventos && ped.eventos.length ? ped.eventos : null;

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
              <span data-i18n={esHoy ? "repT" : "repTUlt"} style={{ fontSize: 13, fontWeight: 700, color: "#0f2b4a" }}>
                {tituloReporte}
              </span>
              <span style={{ fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: 19, color: rep ? "#22a35e" : "#9db3c9" }}>
                {rep ? <span data-count={pct} data-suffix="%">{`${pct}%`}</span> : <span>—</span>}
              </span>
            </div>
            <div style={{ margin: "10px 0 0", height: 8, borderRadius: 99, background: "#e8f0f8", overflow: "hidden" }}>
              <div
                data-barra={pct}
                style={{
                  height: "100%",
                  width: rep ? `${pct}%` : "0%",
                  borderRadius: 99,
                  background: "linear-gradient(90deg, #2679d8, #22a35e)",
                  transition: "width 1.4s ease .2s",
                }}
              />
            </div>
            <p data-i18n={rep ? undefined : "repD"} style={{ margin: "8px 0 0", fontSize: 12.5, color: "#7288a0" }}>
              {resumen}
            </p>
          </div>
        </div>

        {/* Columna derecha: estado del pedido y, DEBAJO, la tarjeta de IA. */}
        <div>
          <div data-tilt="1" style={{ background: "#fff", border: "1px solid rgba(15,43,74,.1)", borderRadius: 22, boxShadow: "0 24px 60px rgba(15,43,74,.14)", padding: 22, maxWidth: 420, margin: "0 auto" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", margin: "0 0 16px" }}>
              <span data-i18n={ped ? undefined : "gtwT"} style={{ fontFamily: "Archivo, sans-serif", fontWeight: 700, fontSize: 14, color: "#0f2b4a" }}>
                {ped ? `Pedido ${ped.codigo} · ${ped.retail}` : tx("gtwT", "Seguimiento de un envío")}
              </span>
              <span
                data-i18n={ped ? undefined : "gtwE"}
                style={{
                  background: badge ? badge.bg : "#eef2f6",
                  color: badge ? badge.fg : "#52708e",
                  fontSize: 11.5,
                  fontWeight: 700,
                  padding: "4px 10px",
                  borderRadius: 99,
                  whiteSpace: "nowrap",
                  animation: "latido 2.2s ease-in-out infinite",
                }}
              >
                {ped ? (badge ? badge.tx : ped.estado) : tx("gtwE", "ETAPAS")}
              </span>
            </div>
            <div style={{ display: "grid", gap: 0 }}>
              {eventos
                ? eventos.map((ev, i) => (
                    <div key={i} style={{ display: "flex", gap: 14 }}>
                      <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                        <span
                          style={{
                            width: 11,
                            height: 11,
                            borderRadius: 99,
                            background: ev.alerta ? "#d97a1f" : "#2679d8",
                            flex: "none",
                            boxShadow: ev.vivo ? "0 0 0 5px rgba(38,121,216,.18)" : "none",
                          }}
                        />
                        {i < eventos.length - 1 && <span style={{ width: 2, flex: 1, background: "#2679d8" }} />}
                      </div>
                      <div style={{ padding: i < eventos.length - 1 ? "0 0 18px" : 0 }}>
                        <p style={{ margin: 0, fontSize: 13.5, fontWeight: 600, color: "#0f2b4a" }}>{ev.t}</p>
                        <p style={{ margin: "2px 0 0", fontSize: 12, color: "#8ba0b6" }}>
                          {ev.h}
                          {ev.d ? ` · ${ev.d}` : ""}
                        </p>
                      </div>
                    </div>
                  ))
                : ETAPAS.map((e, i) => (
                    <div key={e.claveT} style={{ display: "flex", gap: 14 }}>
                      <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                        <span style={{ width: 11, height: 11, borderRadius: 99, background: "#9db3c9", flex: "none" }} />
                        {i < ETAPAS.length - 1 && <span style={{ width: 2, flex: 1, background: "#dce8f4" }} />}
                      </div>
                      <div style={{ padding: i < ETAPAS.length - 1 ? "0 0 18px" : 0 }}>
                        <p data-i18n={e.claveT} style={{ margin: 0, fontSize: 13.5, fontWeight: 600, color: "#4f6580" }}>
                          {tx(e.claveT, TEXTOS_ETAPAS[e.claveT])}
                        </p>
                        <p data-i18n={e.claveD} style={{ margin: "2px 0 0", fontSize: 12, color: "#8ba0b6" }}>
                          {tx(e.claveD, e.detalle)}
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
                {tx("flotaPill", "Así se ve la flota en GeoTrack")}
              </span>
            </div>
          </div>
          <p data-i18n="gtMapa" style={{ margin: "14px 0 0", textAlign: "center", fontSize: 13.5, lineHeight: 1.6, color: "#4f6580" }}>
            {tx("gtMapa", "Cada conductor registra la evidencia en la app GeoTrack y sigue al siguiente cliente — SAVA visualiza todo en tiempo real")}
          </p>
        </div>
      </div>
    </section>
  );
}
