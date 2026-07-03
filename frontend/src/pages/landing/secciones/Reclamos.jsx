import { useState } from "react";

// Reclamos (#reclamos): texto + puntos de valor a la izquierda y Libro de
// Reclamaciones Virtual (formulario demo) a la derecha. Input: tx (traducción).
export default function Reclamos({ tx }) {
  // Estado local: tipo de solicitud (reclamo/queja) y resultado del envío demo.
  const [estado, setEstado] = useState({ tipo: "reclamo", enviado: false, numero: "" });

  // Registra el reclamo en modo demo: genera un código LR local y muestra confirmación.
  // Input: evento submit del formulario.
  const onReclamo = (e) => {
    e.preventDefault();
    setEstado((prev) => ({ ...prev, enviado: true, numero: `LR-2026-${Math.floor(1000 + Math.random() * 9000)}` }));
  };

  // Cambia el tipo de solicitud a "reclamo". Input: click del botón izquierdo.
  const elegirReclamo = () => setEstado((prev) => ({ ...prev, tipo: "reclamo" }));
  // Cambia el tipo de solicitud a "queja". Input: click del botón derecho.
  const elegirQueja = () => setEstado((prev) => ({ ...prev, tipo: "queja" }));

  const esReclamo = estado.tipo === "reclamo";

  return (
    <section id="reclamos" data-sec="p" style={{ maxWidth: 1200, margin: "0 auto", padding: "110px 28px 0" }}>
      <div data-rg="1" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 44, alignItems: "start" }}>
        <div>
          <div data-reveal="0" style={{ opacity: 0, transform: "translateY(26px)", transition: "opacity .7s ease, transform .7s ease" }}>
            <p data-i18n="recE" style={{ margin: "0 0 12px", fontSize: 13, fontWeight: 600, letterSpacing: ".14em", textTransform: "uppercase", color: "#2679d8" }}>
              {tx("recE", "Atención al cliente")}
            </p>
            <h2 data-i18n="recT" style={{ margin: 0, fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: "clamp(30px, 3.6vw, 44px)", lineHeight: 1.1, letterSpacing: "-.01em" }}>
              {tx("recT", "¿Algo salió mal? Cuéntenoslo.")}
            </h2>
            <p data-i18n="recD" style={{ margin: "18px 0 0", fontSize: 16, lineHeight: 1.65, color: "#4f6580" }}>
              {tx("recD", "Registre su queja o reclamo en nuestro Libro de Reclamaciones virtual. Llega directo al equipo de operaciones de SAVA, con código de seguimiento y respuesta garantizada.")}
            </p>
          </div>
          <div style={{ margin: "30px 0 0", display: "grid", gap: 14 }}>
            <div data-reveal="80" style={{ display: "flex", gap: 14, alignItems: "flex-start", background: "#fff", border: "1px solid rgba(15,43,74,.08)", borderRadius: 16, padding: "16px 20px", opacity: 0, transform: "translateY(26px)", transition: "opacity .6s ease, transform .6s ease" }}>
              <span style={{ width: 9, height: 9, borderRadius: 99, background: "#2679d8", marginTop: 6, flex: "none" }} />
              <div>
                <h3 data-i18n="recB1t" style={{ margin: 0, fontFamily: "Archivo, sans-serif", fontWeight: 700, fontSize: 15.5 }}>
                  {tx("recB1t", "Respuesta en máximo 15 días hábiles")}
                </h3>
                <p data-i18n="recB1d" style={{ margin: "4px 0 0", fontSize: 13.5, lineHeight: 1.55, color: "#7288a0" }}>
                  {tx("recB1d", "Como exige la normativa peruana de protección al consumidor.")}
                </p>
              </div>
            </div>
            <div data-reveal="150" style={{ display: "flex", gap: 14, alignItems: "flex-start", background: "#fff", border: "1px solid rgba(15,43,74,.08)", borderRadius: 16, padding: "16px 20px", opacity: 0, transform: "translateY(26px)", transition: "opacity .6s ease, transform .6s ease" }}>
              <span style={{ width: 9, height: 9, borderRadius: 99, background: "#2679d8", marginTop: 6, flex: "none" }} />
              <div>
                <h3 data-i18n="recB2t" style={{ margin: 0, fontFamily: "Archivo, sans-serif", fontWeight: 700, fontSize: 15.5 }}>
                  {tx("recB2t", "Código LR para hacer seguimiento")}
                </h3>
                <p data-i18n="recB2d" style={{ margin: "4px 0 0", fontSize: 13.5, lineHeight: 1.55, color: "#7288a0" }}>
                  {tx("recB2d", "Cada reclamo genera un código único para consultar su estado.")}
                </p>
              </div>
            </div>
            <div data-reveal="220" style={{ display: "flex", gap: 14, alignItems: "flex-start", background: "#fff", border: "1px solid rgba(15,43,74,.08)", borderRadius: 16, padding: "16px 20px", opacity: 0, transform: "translateY(26px)", transition: "opacity .6s ease, transform .6s ease" }}>
              <span style={{ width: 9, height: 9, borderRadius: 99, background: "#22a35e", marginTop: 6, flex: "none", animation: "latido 2.2s ease-in-out infinite" }} />
              <div>
                <h3 data-i18n="recB3t" style={{ margin: 0, fontFamily: "Archivo, sans-serif", fontWeight: 700, fontSize: 15.5 }}>
                  {tx("recB3t", "Canal directo")}
                </h3>
                <p data-i18n="recB3d" style={{ margin: "4px 0 0", fontSize: 13.5, lineHeight: 1.55, color: "#7288a0" }}>
                  {tx("recB3d", "¿Prefiere conversar? WhatsApp +51 922 507 593, de lunes a sábado.")}
                </p>
              </div>
            </div>
          </div>
          <p data-i18n="recLegal" data-reveal="260" style={{ margin: "18px 0 0", fontSize: 12, lineHeight: 1.6, color: "#8ba0b6", opacity: 0, transform: "translateY(26px)", transition: "opacity .6s ease, transform .6s ease" }}>
            {tx("recLegal", "Libro de Reclamaciones virtual conforme a la Ley N.º 29571, Código de Protección y Defensa del Consumidor.")}
          </p>
        </div>

        <form
          data-reveal="140"
          data-panel="1"
          onSubmit={onReclamo}
          style={{ background: "#fff", border: "1px solid rgba(15,43,74,.08)", borderRadius: 24, padding: 36, display: "grid", gap: 16, boxShadow: "0 18px 44px rgba(15,43,74,.09)", opacity: 0, transform: "translateY(26px)", transition: "opacity .7s ease, transform .7s ease" }}
        >
          <span data-i18n="recLibro" style={{ justifySelf: "start", border: "1.5px solid #c8362b", color: "#c8362b", fontSize: 11, fontWeight: 700, letterSpacing: ".1em", padding: "7px 14px", borderRadius: 99 }}>
            {tx("recLibro", "LIBRO DE RECLAMACIONES VIRTUAL")}
          </span>

          <div data-cols2="1" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <button
              type="button"
              onClick={elegirReclamo}
              style={{ textAlign: "left", cursor: "pointer", fontFamily: "Inter, sans-serif", border: `2px solid ${esReclamo ? "#2679d8" : "rgba(15,43,74,.14)"}`, background: esReclamo ? "#eef5fc" : "#f8fafc", borderRadius: 14, padding: "14px 16px", transition: "border-color .25s ease, background .25s ease" }}
            >
              <span data-i18n="recTipoR" style={{ display: "block", fontWeight: 700, fontSize: 14.5, color: "#0f2b4a" }}>
                {tx("recTipoR", "Reclamo")}
              </span>
              <span data-i18n="recTipoRd" style={{ display: "block", marginTop: 3, fontSize: 12, lineHeight: 1.45, color: "#7288a0" }}>
                {tx("recTipoRd", "Sobre el servicio: entrega, paquete, plazos")}
              </span>
            </button>
            <button
              type="button"
              onClick={elegirQueja}
              style={{ textAlign: "left", cursor: "pointer", fontFamily: "Inter, sans-serif", border: `2px solid ${!esReclamo ? "#2679d8" : "rgba(15,43,74,.14)"}`, background: !esReclamo ? "#eef5fc" : "#f8fafc", borderRadius: 14, padding: "14px 16px", transition: "border-color .25s ease, background .25s ease" }}
            >
              <span data-i18n="recTipoQ" style={{ display: "block", fontWeight: 700, fontSize: 14.5, color: "#0f2b4a" }}>
                {tx("recTipoQ", "Queja")}
              </span>
              <span data-i18n="recTipoQd" style={{ display: "block", marginTop: 3, fontSize: 12, lineHeight: 1.45, color: "#7288a0" }}>
                {tx("recTipoQd", "Sobre la atención recibida")}
              </span>
            </button>
          </div>

          <div data-cols2="1" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <label style={{ display: "grid", gap: 6 }}>
              <span data-i18n="fN" style={{ fontSize: 13, fontWeight: 600, color: "#3d5570" }}>{tx("fN", "Nombre")}</span>
              <input required placeholder={tx("fNph", "Su nombre")} className="ldg-input" />
            </label>
            <label style={{ display: "grid", gap: 6 }}>
              <span data-i18n="recDoc" style={{ fontSize: 13, fontWeight: 600, color: "#3d5570" }}>{tx("recDoc", "DNI / CE")}</span>
              <input required placeholder="00000000" className="ldg-input" />
            </label>
          </div>

          <div data-cols2="1" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <label style={{ display: "grid", gap: 6 }}>
              <span data-i18n="fC" style={{ fontSize: 13, fontWeight: 600, color: "#3d5570" }}>{tx("fC", "Correo")}</span>
              <input type="email" required placeholder="nombre@correo.com" className="ldg-input" />
            </label>
            <label style={{ display: "grid", gap: 6 }}>
              <span data-i18n="recPed" style={{ fontSize: 13, fontWeight: 600, color: "#3d5570" }}>{tx("recPed", "Código de pedido (opcional)")}</span>
              <input placeholder="Ej. PD-2481" className="ldg-input" />
            </label>
          </div>

          <label style={{ display: "grid", gap: 6 }}>
            <span data-i18n="recDet" style={{ fontSize: 13, fontWeight: 600, color: "#3d5570" }}>{tx("recDet", "Cuéntenos qué pasó")}</span>
            <textarea required rows={4} placeholder={tx("recDetPh", "Describa lo ocurrido con su pedido o con nuestro servicio…")} className="ldg-textarea" />
          </label>

          <button type="submit" className="ldg-btn-enviar" style={{ justifySelf: "start" }}>
            {estado.enviado ? tx("btnReclamoOk", "Registrado en el libro ✓") : tx("btnReclamo", "Enviar al Libro de Reclamaciones")}
          </button>

          {estado.enviado && (
            <div style={{ background: "#e3f2e8", border: "1px solid rgba(34,163,94,.35)", borderRadius: 14, padding: "16px 20px", animation: "aparecerRec .45s ease both" }}>
              <p style={{ margin: 0, fontSize: 14.5, fontWeight: 700, color: "#1e7a43" }}>
                <span data-i18n="recOk1">{tx("recOk1", "✓ ¡Recibido! Su código de seguimiento es")}</span> {estado.numero}
              </p>
              <p data-i18n="recOk2" style={{ margin: "6px 0 0", fontSize: 13, lineHeight: 1.55, color: "#3d6b4e" }}>
                {tx("recOk2", "Enviamos una copia a su correo. Le responderemos en un máximo de 15 días hábiles.")}
              </p>
            </div>
          )}
        </form>
      </div>
    </section>
  );
}
