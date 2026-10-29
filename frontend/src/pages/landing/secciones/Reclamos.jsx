import { useEffect, useState } from "react";
import { enviarReclamo, datosLibro } from "../../portal/servicios/portal.js";

// Datos del proveedor si el servidor no responde (los reales vienen de /api/portal/libro).
const PROVEEDOR_RESPALDO = {
  razonSocial: "SAVA S.A.C.",
  ruc: null,
  direccion: "Calle Los Sinchis Nro. 166, Urb. Tahuantinsuyo Zona III, Independencia, Lima",
};

const VACIO = {
  tipo: "reclamo", nombre: "", dni: "", domicilio: "", telefono: "", email: "",
  esMenor: false, apoderadoNombre: "", apoderadoDni: "",
  bienTipo: "SERVICIO", bienDescripcion: "Servicio de entrega a domicilio", monto: "",
  pedido: "", detalle: "", pedidoConsumidor: "", hp: "",
};

const etiqueta = { fontSize: 13, fontWeight: 600, color: "#3d5570" };
const grupo = { display: "grid", gap: 6 };
const dosColumnas = { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 };

// Abre la constancia (copia completa del reclamo) en una ventana para imprimirla o guardarla
// como PDF (C40-02). Se arma con nodos y textContent: el texto del consumidor nunca se
// interpreta como HTML. Recibe la constancia que devuelve el servidor.
function imprimirConstancia(c) {
  const ventana = window.open("", "_blank", "width=820,height=900");
  if (!ventana) return;
  const doc = ventana.document;
  const nodo = (tag, texto, estilo) => {
    const el = doc.createElement(tag);
    if (texto != null) el.textContent = texto;
    if (estilo) el.setAttribute("style", estilo);
    return el;
  };
  const con = c.consumidor;
  const filas = [
    ["Fecha", new Date(c.fecha).toLocaleString("es-PE")],
    ["Tipo", c.tipo === "QUEJA" ? "Queja" : "Reclamo"],
    ["Consumidor", `${con.nombre} · Doc. ${con.documento}`],
    ["Domicilio", con.domicilio],
    ["Teléfono / correo", `${con.telefono} · ${con.email}`],
    ...(con.esMenor ? [["Padre o madre", `${con.apoderadoNombre} · Doc. ${con.apoderadoDni}`]] : []),
    ["Bien contratado", `${c.bien.tipo === "PRODUCTO" ? "Producto" : "Servicio"}: ${c.bien.descripcion}`],
    ["Monto reclamado", c.bien.monto != null ? `S/ ${Number(c.bien.monto).toFixed(2)}` : "—"],
    ["Pedido SAVA", c.pedido || "—"],
    ["Detalle", c.detalle],
    ["Pedido del consumidor", c.pedidoConsumidor],
    ["Respuesta a más tardar el", new Date(`${c.venceEl}T12:00:00`).toLocaleDateString("es-PE")],
  ];
  doc.title = `Constancia ${c.codigo}`;
  doc.body.setAttribute("style", "font-family:Arial,sans-serif;color:#0f2b4a;margin:32px");
  doc.body.appendChild(nodo("h1", `Hoja de Reclamación ${c.codigo}`, "font-size:18px;margin:0 0 4px"));
  doc.body.appendChild(nodo("p", `${c.proveedor.razonSocial}${c.proveedor.ruc ? ` · RUC ${c.proveedor.ruc}` : ""}`, "margin:2px 0;font-size:13px"));
  doc.body.appendChild(nodo("p", c.proveedor.direccion, "margin:2px 0;font-size:13px"));
  const tabla = nodo("table", null, "border-collapse:collapse;width:100%;margin-top:16px;font-size:13px");
  const celda = "border:1px solid #d5dde7;padding:7px 9px;vertical-align:top";
  filas.forEach(([k, v]) => {
    const tr = nodo("tr");
    tr.appendChild(nodo("th", k, `${celda};text-align:left;width:34%;background:#f3f6fa`));
    tr.appendChild(nodo("td", v ?? "", celda));
    tabla.appendChild(tr);
  });
  doc.body.appendChild(tabla);
  doc.body.appendChild(nodo("p", "Libro de Reclamaciones virtual · Ley N.º 29571 y D.S. 011-2011-PCM.", "margin-top:14px;font-size:11px;color:#6b7f95"));
  ventana.focus();
  ventana.print();
}

// Reclamos (#reclamos): texto + puntos de valor a la izquierda y Libro de Reclamaciones
// Virtual a la derecha, con todos los datos que exige el D.S. 011-2011-PCM (C40-01) y los
// datos de SAVA (C40-02). Input: tx (traducción).
export default function Reclamos({ tx }) {
  const [f, setF] = useState(VACIO);
  const [envio, setEnvio] = useState({ enviando: false, error: "", constancia: null, numero: "" });
  const [proveedor, setProveedor] = useState(PROVEEDOR_RESPALDO);

  // Pide razón social, RUC y dirección de SAVA. El setState va dentro del .then (regla de lint).
  useEffect(() => {
    let activo = true;
    datosLibro().then((d) => activo && d && setProveedor(d)).catch(() => {});
    return () => { activo = false; };
  }, []);

  // Actualiza un campo del formulario. Recibe el nombre del campo y devuelve el manejador del evento.
  const campo = (nombre) => (e) => {
    const valor = e.target.type === "checkbox" ? e.target.checked : e.target.value;
    setF((prev) => ({ ...prev, [nombre]: valor }));
  };

  // Registra la hoja de reclamación y muestra la constancia con su copia. Input: evento submit.
  const onReclamo = (e) => {
    e.preventDefault();
    if (envio.enviando || envio.numero) return;
    setEnvio((p) => ({ ...p, enviando: true, error: "" }));
    enviarReclamo({
      tipo: f.tipo === "reclamo" ? "RECLAMO" : "QUEJA",
      consumidor: {
        nombre: f.nombre, dni: f.dni, domicilio: f.domicilio, telefono: f.telefono, email: f.email,
        esMenor: f.esMenor,
        apoderadoNombre: f.esMenor ? f.apoderadoNombre : null,
        apoderadoDni: f.esMenor ? f.apoderadoDni : null,
      },
      bien: { tipo: f.bienTipo, descripcion: f.bienDescripcion, monto: f.monto === "" ? null : Number(f.monto) },
      detalle: f.detalle,
      pedidoConsumidor: f.pedidoConsumidor,
      pedido: f.pedido || null,
      hp: f.hp,
    })
      .then((resp) => setEnvio({ enviando: false, error: "", constancia: resp.constancia || null, numero: resp.codigo }))
      .catch((err) => {
        const detalle = err?.data?.detail;
        const msg = Array.isArray(detalle) && detalle[0]?.msg ? detalle[0].msg.replace(/^Value error, /, "") : "";
        setEnvio((p) => ({ ...p, enviando: false, error: msg || tx("recErr", "No pudimos registrar su reclamo. Intente nuevamente en unos minutos.") }));
      });
  };

  const esReclamo = f.tipo === "reclamo";
  const enviado = !!envio.numero;
  const botonTipo = (activo) => ({
    textAlign: "left", cursor: "pointer", fontFamily: "Inter, sans-serif",
    border: `2px solid ${activo ? "#2679d8" : "rgba(15,43,74,.14)"}`, background: activo ? "#eef5fc" : "#f8fafc",
    borderRadius: 14, padding: "14px 16px", transition: "border-color .25s ease, background .25s ease",
  });

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
            {[
              ["recB1t", "Respuesta en máximo 15 días hábiles", "recB1d", "Como exige la normativa peruana de protección al consumidor.", "#2679d8", 80],
              ["recB2t", "Código LR para hacer seguimiento", "recB2d", "Cada reclamo genera un código único para consultar su estado.", "#2679d8", 150],
              ["recB3t", "Canal directo", "recB3d", "¿Prefiere conversar? WhatsApp +51 922 507 593, de lunes a sábado.", "#22a35e", 220],
            ].map(([kt, t, kd, d, color, retraso]) => (
              <div key={kt} data-reveal={retraso} style={{ display: "flex", gap: 14, alignItems: "flex-start", background: "#fff", border: "1px solid rgba(15,43,74,.08)", borderRadius: 16, padding: "16px 20px", opacity: 0, transform: "translateY(26px)", transition: "opacity .6s ease, transform .6s ease" }}>
                <span style={{ width: 9, height: 9, borderRadius: 99, background: color, marginTop: 6, flex: "none", animation: color === "#22a35e" ? "latido 2.2s ease-in-out infinite" : undefined }} />
                <div>
                  <h3 data-i18n={kt} style={{ margin: 0, fontFamily: "Archivo, sans-serif", fontWeight: 700, fontSize: 15.5 }}>{tx(kt, t)}</h3>
                  <p data-i18n={kd} style={{ margin: "4px 0 0", fontSize: 13.5, lineHeight: 1.55, color: "#7288a0" }}>{tx(kd, d)}</p>
                </div>
              </div>
            ))}
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

          {/* Datos del proveedor (C40-02) */}
          <div style={{ background: "#f6f9fc", borderRadius: 12, padding: "12px 16px", fontSize: 13, lineHeight: 1.55, color: "#3d5570" }}>
            <b style={{ color: "#0f2b4a" }}>{proveedor.razonSocial}</b>
            {proveedor.ruc ? ` · RUC ${proveedor.ruc}` : ""}
            <br />
            {proveedor.direccion}
          </div>

          <div data-cols2="1" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <button type="button" onClick={() => setF((p) => ({ ...p, tipo: "reclamo" }))} style={botonTipo(esReclamo)}>
              <span data-i18n="recTipoR" style={{ display: "block", fontWeight: 700, fontSize: 14.5, color: "#0f2b4a" }}>{tx("recTipoR", "Reclamo")}</span>
              <span data-i18n="recTipoRd" style={{ display: "block", marginTop: 3, fontSize: 12, lineHeight: 1.45, color: "#7288a0" }}>{tx("recTipoRd", "Sobre el servicio: entrega, paquete, plazos")}</span>
            </button>
            <button type="button" onClick={() => setF((p) => ({ ...p, tipo: "queja" }))} style={botonTipo(!esReclamo)}>
              <span data-i18n="recTipoQ" style={{ display: "block", fontWeight: 700, fontSize: 14.5, color: "#0f2b4a" }}>{tx("recTipoQ", "Queja")}</span>
              <span data-i18n="recTipoQd" style={{ display: "block", marginTop: 3, fontSize: 12, lineHeight: 1.45, color: "#7288a0" }}>{tx("recTipoQd", "Sobre la atención recibida")}</span>
            </button>
          </div>

          <p data-i18n="recSecCon" style={{ margin: "4px 0 0", fontSize: 12, fontWeight: 700, letterSpacing: ".08em", textTransform: "uppercase", color: "#7288a0" }}>{tx("recSecCon", "1. Identificación del consumidor")}</p>
          <div data-cols2="1" style={dosColumnas}>
            <label style={grupo}>
              <span data-i18n="fN" style={etiqueta}>{tx("fN", "Nombre")}</span>
              <input required minLength={3} maxLength={150} value={f.nombre} onChange={campo("nombre")} placeholder={tx("fNph", "Su nombre")} className="ldg-input" />
            </label>
            <label style={grupo}>
              <span data-i18n="recDoc" style={etiqueta}>{tx("recDoc", "DNI / CE")}</span>
              <input required pattern="[A-Za-z0-9]{8,12}" maxLength={12} value={f.dni} onChange={campo("dni")} placeholder="00000000" className="ldg-input" />
            </label>
          </div>
          <label style={grupo}>
            <span data-i18n="recDom" style={etiqueta}>{tx("recDom", "Domicilio")}</span>
            <input required minLength={5} maxLength={255} value={f.domicilio} onChange={campo("domicilio")} placeholder={tx("recDomPh", "Calle, número, distrito")} className="ldg-input" />
          </label>
          <div data-cols2="1" style={dosColumnas}>
            <label style={grupo}>
              <span data-i18n="fT" style={etiqueta}>{tx("fT", "Teléfono")}</span>
              <input required type="tel" maxLength={30} value={f.telefono} onChange={campo("telefono")} placeholder="987 654 321" className="ldg-input" />
            </label>
            <label style={grupo}>
              <span data-i18n="fC" style={etiqueta}>{tx("fC", "Correo")}</span>
              <input type="email" required value={f.email} onChange={campo("email")} placeholder="nombre@correo.com" className="ldg-input" />
            </label>
          </div>
          <label style={{ display: "flex", gap: 10, alignItems: "center", fontSize: 13.5, color: "#3d5570", cursor: "pointer" }}>
            <input type="checkbox" checked={f.esMenor} onChange={campo("esMenor")} style={{ width: 16, height: 16 }} />
            <span data-i18n="recMenor">{tx("recMenor", "Soy menor de edad")}</span>
          </label>
          {f.esMenor && (
            <div data-cols2="1" style={dosColumnas}>
              <label style={grupo}>
                <span data-i18n="recApoNom" style={etiqueta}>{tx("recApoNom", "Nombre del padre o madre")}</span>
                <input required minLength={3} maxLength={150} value={f.apoderadoNombre} onChange={campo("apoderadoNombre")} className="ldg-input" />
              </label>
              <label style={grupo}>
                <span data-i18n="recApoDoc" style={etiqueta}>{tx("recApoDoc", "DNI / CE del padre o madre")}</span>
                <input required pattern="[A-Za-z0-9]{8,12}" maxLength={12} value={f.apoderadoDni} onChange={campo("apoderadoDni")} placeholder="00000000" className="ldg-input" />
              </label>
            </div>
          )}

          <p data-i18n="recSecBien" style={{ margin: "4px 0 0", fontSize: 12, fontWeight: 700, letterSpacing: ".08em", textTransform: "uppercase", color: "#7288a0" }}>{tx("recSecBien", "2. Bien contratado")}</p>
          <div data-cols2="1" style={dosColumnas}>
            <label style={grupo}>
              <span data-i18n="recBien" style={etiqueta}>{tx("recBien", "Tipo")}</span>
              <select value={f.bienTipo} onChange={campo("bienTipo")} className="ldg-input">
                <option value="SERVICIO">{tx("recBienS", "Servicio")}</option>
                <option value="PRODUCTO">{tx("recBienP", "Producto")}</option>
              </select>
            </label>
            <label style={grupo}>
              <span data-i18n="recMonto" style={etiqueta}>{tx("recMonto", "Monto reclamado S/ (opcional)")}</span>
              <input type="number" min="0" step="0.01" value={f.monto} onChange={campo("monto")} placeholder="0.00" className="ldg-input" />
            </label>
          </div>
          <div data-cols2="1" style={dosColumnas}>
            <label style={grupo}>
              <span data-i18n="recBienDesc" style={etiqueta}>{tx("recBienDesc", "Descripción")}</span>
              <input required minLength={3} maxLength={500} value={f.bienDescripcion} onChange={campo("bienDescripcion")} className="ldg-input" />
            </label>
            <label style={grupo}>
              <span data-i18n="recPed" style={etiqueta}>{tx("recPed", "Código de pedido (opcional)")}</span>
              <input maxLength={20} value={f.pedido} onChange={campo("pedido")} placeholder="Ej. PD-2481" className="ldg-input" />
            </label>
          </div>

          <p data-i18n="recSecDet" style={{ margin: "4px 0 0", fontSize: 12, fontWeight: 700, letterSpacing: ".08em", textTransform: "uppercase", color: "#7288a0" }}>{tx("recSecDet", "3. Detalle de la reclamación")}</p>
          <label style={grupo}>
            <span data-i18n="recDet" style={etiqueta}>{tx("recDet", "Cuéntenos qué pasó")}</span>
            <textarea required minLength={10} maxLength={4000} rows={4} value={f.detalle} onChange={campo("detalle")} placeholder={tx("recDetPh", "Describa lo ocurrido con su pedido o con nuestro servicio…")} className="ldg-textarea" />
          </label>
          <label style={grupo}>
            <span data-i18n="recPide" style={etiqueta}>{tx("recPide", "¿Qué solicita?")}</span>
            <textarea required minLength={5} maxLength={2000} rows={2} value={f.pedidoConsumidor} onChange={campo("pedidoConsumidor")} placeholder={tx("recPidePh", "Ej. que entreguen mi pedido o me devuelvan el costo del envío")} className="ldg-textarea" />
          </label>

          {/* Honeypot: campo invisible para personas; si un bot lo llena, el backend rechaza el envío. */}
          <input type="text" name="sitio_web" value={f.hp} onChange={campo("hp")} style={{ display: "none" }} tabIndex={-1} autoComplete="off" aria-hidden="true" />

          <button type="submit" disabled={envio.enviando || enviado} className="ldg-btn-enviar" style={{ justifySelf: "start" }}>
            {enviado ? tx("btnReclamoOk", "Registrado en el libro ✓") : tx("btnReclamo", "Enviar al Libro de Reclamaciones")}
          </button>

          {envio.error && (
            <p role="alert" style={{ margin: 0, fontSize: 13.5, fontWeight: 600, color: "#c8362b" }}>{envio.error}</p>
          )}

          {enviado && (
            <div style={{ background: "#e3f2e8", border: "1px solid rgba(34,163,94,.35)", borderRadius: 14, padding: "16px 20px", animation: "aparecerRec .45s ease both" }}>
              <p style={{ margin: 0, fontSize: 14.5, fontWeight: 700, color: "#1e7a43" }}>
                <span data-i18n="recOk1">{tx("recOk1", "✓ ¡Recibido! Su código de seguimiento es")}</span> {envio.numero}
              </p>
              <p data-i18n="recOk2" style={{ margin: "6px 0 0", fontSize: 13, lineHeight: 1.55, color: "#3d6b4e" }}>
                {tx("recOk2", "Enviamos una copia a su correo. Le responderemos en un máximo de 15 días hábiles.")}
              </p>
              {envio.constancia && (
                <button type="button" onClick={() => imprimirConstancia(envio.constancia)}
                  style={{ margin: "12px 0 0", border: "1.5px solid #1e7a43", background: "#fff", color: "#1e7a43", fontFamily: "Inter, sans-serif", fontWeight: 600, fontSize: 13.5, padding: "9px 16px", borderRadius: 99, cursor: "pointer" }}>
                  {tx("recImprimir", "Ver e imprimir la constancia")}
                </button>
              )}
            </div>
          )}
        </form>
      </div>
    </section>
  );
}
