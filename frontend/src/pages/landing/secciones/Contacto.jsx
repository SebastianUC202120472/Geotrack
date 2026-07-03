import { useState } from "react";

// Contacto (#contacto): panel oscuro con datos de contacto a la izquierda y
// formulario demo con slider de volumen diario a la derecha. Input: tx (traducción).
export default function Contacto({ tx }) {
  // Estado local: volumen diario (slider) y si ya se envió el formulario demo.
  const [estado, setEstado] = useState({ vol: 300, enviado: false });

  // Actualiza el volumen diario según el slider. Input: evento change del range.
  const onVol = (e) => setEstado((prev) => ({ ...prev, vol: Number(e.target.value) }));

  // Envía el formulario en modo demo: solo cambia el botón a "enviado".
  // Input: evento submit del formulario.
  const onEnviar = (e) => {
    e.preventDefault();
    setEstado((prev) => ({ ...prev, enviado: true }));
  };

  const rutas = Math.max(1, Math.ceil(estado.vol / 45));
  const volTxt = estado.vol >= 1000 ? "1000+" : String(estado.vol);

  return (
    <section id="contacto" data-sec="f" style={{ maxWidth: 1200, margin: "110px auto 0", padding: "0 28px 90px" }}>
      <div
        data-reveal="0"
        data-rg="1"
        style={{ background: "#fff", border: "1px solid rgba(15,43,74,.08)", borderRadius: 24, overflow: "hidden", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", opacity: 0, transform: "translateY(26px)", transition: "opacity .7s ease, transform .7s ease" }}
      >
        <div data-panel="1" style={{ background: "#0f2b4a", padding: "52px 44px", color: "#eaf2fa" }}>
          <p data-i18n="conE" style={{ margin: "0 0 12px", fontSize: 13, fontWeight: 600, letterSpacing: ".14em", textTransform: "uppercase", color: "#5db1f0" }}>
            {tx("conE", "Contacto")}
          </p>
          <h2 data-i18n="conT" style={{ margin: 0, fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: "clamp(28px, 3vw, 38px)", lineHeight: 1.12 }}>
            {tx("conT", "Conversemos sobre las entregas de su tienda.")}
          </h2>
          <p data-i18n="conD" style={{ margin: "16px 0 0", fontSize: 15, lineHeight: 1.65, color: "#9fc0e2" }}>
            {tx("conD", "Cuéntenos su volumen diario y sus zonas; le respondemos con una propuesta en 24 horas.")}
          </p>
          <div style={{ margin: "36px 0 0", display: "grid", gap: 18 }}>
            <div style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
              <span style={{ width: 9, height: 9, borderRadius: 99, background: "#5db1f0", marginTop: 6, flex: "none" }} />
              <div>
                <p data-i18n="conDirT" style={{ margin: 0, fontSize: 13, fontWeight: 700, letterSpacing: ".06em", textTransform: "uppercase", color: "#9fc0e2" }}>
                  {tx("conDirT", "Dirección")}
                </p>
                <p style={{ margin: "4px 0 0", fontSize: 15, lineHeight: 1.55, color: "#eaf2fa" }}>
                  Calle Los Sinchis Nro. 166, Urb. Tahuantinsuyo Zona III,
                  <br />
                  Independencia, Lima
                </p>
              </div>
            </div>
            <div style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
              <span style={{ width: 9, height: 9, borderRadius: 99, background: "#5db1f0", marginTop: 6, flex: "none" }} />
              <div>
                <p data-i18n="conTelT" style={{ margin: 0, fontSize: 13, fontWeight: 700, letterSpacing: ".06em", textTransform: "uppercase", color: "#9fc0e2" }}>
                  {tx("conTelT", "Teléfono / WhatsApp")}
                </p>
                <a href="tel:+51922507593" className="ldg-ft-tel" style={{ display: "inline-block", margin: "4px 0 0", fontSize: 15, color: "#eaf2fa", textDecoration: "none" }}>
                  +51 922 507 593
                </a>
              </div>
            </div>
            <div style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
              <span style={{ width: 9, height: 9, borderRadius: 99, background: "#5db1f0", marginTop: 6, flex: "none" }} />
              <div>
                <p data-i18n="conHorT" style={{ margin: 0, fontSize: 13, fontWeight: 700, letterSpacing: ".06em", textTransform: "uppercase", color: "#9fc0e2" }}>
                  {tx("conHorT", "Operación")}
                </p>
                <p data-i18n="conHorD" style={{ margin: "4px 0 0", fontSize: 15, lineHeight: 1.55, color: "#eaf2fa" }}>
                  {tx("conHorD", "Recepción y reparto de lunes a sábado")}
                </p>
              </div>
            </div>
          </div>
        </div>

        <form data-panel="1" onSubmit={onEnviar} style={{ padding: "52px 44px", display: "grid", gap: 16, alignContent: "start" }}>
          <div style={{ background: "#eef5fc", border: "1px solid rgba(38,121,216,.22)", borderRadius: 18, padding: "18px 20px", display: "grid", gap: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "baseline", flexWrap: "wrap" }}>
              <span data-i18n="cotT" style={{ fontSize: 13.5, fontWeight: 700, color: "#0f2b4a" }}>
                {tx("cotT", "¿Cuántos pedidos al día maneja su tienda?")}
              </span>
              <span style={{ fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: 22, color: "#2679d8" }}>{volTxt}</span>
            </div>
            <input type="range" min={50} max={1000} step={10} value={estado.vol} onChange={onVol} style={{ width: "100%", accentColor: "#2679d8", cursor: "pointer", margin: 0 }} />
            <p style={{ margin: 0, fontSize: 12.5, color: "#4f6580" }}>
              ≈ {rutas} {tx("rutasTxt", "rutas diarias dedicadas para su tienda · propuesta en 24 h")}
            </p>
          </div>

          <div data-cols2="1" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <label style={{ display: "grid", gap: 6 }}>
              <span data-i18n="fN" style={{ fontSize: 13, fontWeight: 600, color: "#3d5570" }}>{tx("fN", "Nombre")}</span>
              <input required placeholder={tx("fNph", "Su nombre")} className="ldg-input" />
            </label>
            <label style={{ display: "grid", gap: 6 }}>
              <span data-i18n="fE" style={{ fontSize: 13, fontWeight: 600, color: "#3d5570" }}>{tx("fE", "Empresa / retail")}</span>
              <input placeholder={tx("fEph", "Nombre de su empresa")} className="ldg-input" />
            </label>
          </div>

          <div data-cols2="1" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <label style={{ display: "grid", gap: 6 }}>
              <span data-i18n="fC" style={{ fontSize: 13, fontWeight: 600, color: "#3d5570" }}>{tx("fC", "Correo")}</span>
              <input type="email" required placeholder="nombre@empresa.com" className="ldg-input" />
            </label>
            <label style={{ display: "grid", gap: 6 }}>
              <span data-i18n="fT" style={{ fontSize: 13, fontWeight: 600, color: "#3d5570" }}>{tx("fT", "Teléfono")}</span>
              <input placeholder="+51 …" className="ldg-input" />
            </label>
          </div>

          <label style={{ display: "grid", gap: 6 }}>
            <span data-i18n="fM" style={{ fontSize: 13, fontWeight: 600, color: "#3d5570" }}>{tx("fM", "¿Qué necesita distribuir?")}</span>
            <textarea rows={5} placeholder={tx("fMph", "Ej.: 120 pedidos diarios desde nuestro CD en Ate, con reparto en Lima Centro y Sur…")} className="ldg-textarea" />
          </label>

          <button type="submit" className="ldg-btn-enviar" style={{ justifySelf: "start" }}>
            {estado.enviado ? tx("btnEnviadoOk", "¡Enviado, gracias!") : tx("btnEnviar", "Enviar mensaje")}
          </button>
        </form>
      </div>
    </section>
  );
}
