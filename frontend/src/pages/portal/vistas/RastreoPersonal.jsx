import { useEffect, useRef, useState } from "react";
import { PEDIDOS, ESTADOS, OPCIONES } from "../datos/demo.js";

// ============================================================================
// Vista PERSONA NATURAL del portal de clientes (Tarea 10). Port fiel del mockup
// aprobado (portal pagina.html, JSX 506-728 · lógica 1040-1249). Flujo completo:
// búsqueda por código → verificación de identidad (DNI/SMS con bloqueo) → detalle
// del pedido (estado + mapa del recorrido + línea de tiempo + reprogramación).
// Demo puro: sin fetch, los datos salen de ../datos/demo.js.
// ============================================================================

// gen6: genera un código SMS de 6 dígitos aleatorio (string "100000".."999999").
// No recibe input. Port de Component.gen6 (fuente línea 1038).
const gen6 = () => String(Math.floor(100000 + Math.random() * 900000));

// RastreoPersonal: vista de rastreo para el destinatario final.
// Input: prop `avisar(texto, ms)` para mostrar el toast del portal.
export default function RastreoPersonal({ avisar }) {
  // Estado de la vista (port del bloque de estado personal del mockup).
  const [codigo, setCodigo] = useState(""); // texto del input de código
  const [buscando, setBuscando] = useState(false); // spinner "Buscando…"
  const [encontrado, setEncontrado] = useState(null); // código del pedido hallado (o null)
  const [errorCod, setErrorCod] = useState(""); // código que NO existe (para el aviso de error)
  const [verificado, setVerificado] = useState(false); // identidad confirmada → muestra detalle
  const [verInput, setVerInput] = useState(""); // input de DNI/SMS (solo numérico)
  const [verError, setVerError] = useState(false); // marca el último intento como fallido
  const [intentos, setIntentos] = useState(0); // intentos fallidos acumulados (bloqueo a los 3)
  const [bloqueoHasta, setBloqueoHasta] = useState(0); // timestamp fin del bloqueo temporal
  const [smsCode, setSmsCode] = useState(null); // código SMS generado (alternativa al DNI)
  const [reprog, setReprog] = useState(-1); // índice de franja elegida al reprogramar (-1 = ninguna)
  const [reprogOk, setReprogOk] = useState(false); // reprogramación ya confirmada
  const [ahora, setAhora] = useState(() => Date.now()); // reloj para el countdown del bloqueo

  const timerBuscar = useRef(null); // timeout de la búsqueda (900 ms)

  // Reloj de 1 s: solo hace falta cuando hay un bloqueo vigente (para el countdown).
  // El setState va DENTRO del callback del interval (no en el cuerpo del effect), así
  // no dispara la regla de lint "setState síncrono en effect". Se limpia al desmontar
  // o cuando ya no hay bloqueo activo.
  useEffect(() => {
    if (bloqueoHasta <= Date.now()) return undefined;
    const id = setInterval(() => {
      const t = Date.now();
      setAhora(t);
      if (t >= bloqueoHasta) clearInterval(id); // el bloqueo venció: detén el reloj
    }, 1000);
    return () => clearInterval(id);
  }, [bloqueoHasta]);

  // Limpia el timeout de la búsqueda al desmontar (evita setState tras unmount).
  useEffect(() => () => clearTimeout(timerBuscar.current), []);

  // buscarCodigo: dispara la búsqueda de un pedido por su código `c` (ya en mayúsculas).
  // Resetea el flujo de verificación y, tras 900 ms, marca encontrado o error según
  // exista en PEDIDOS. El setState final va dentro del callback (regla de lint OK).
  // Port de Component.buscarCodigo (fuente 1040-1047).
  const buscarCodigo = (c) => {
    setBuscando(true);
    setErrorCod("");
    setEncontrado(null);
    setVerificado(false);
    setVerInput("");
    setVerError(false);
    setIntentos(0);
    setSmsCode(null);
    setReprog(-1);
    setReprogOk(false);
    setCodigo(c);
    clearTimeout(timerBuscar.current);
    timerBuscar.current = setTimeout(() => {
      if (PEDIDOS[c]) {
        setBuscando(false);
        setEncontrado(c);
      } else {
        setBuscando(false);
        setErrorCod(c);
      }
    }, 900);
  };

  // onCodigo: sincroniza el input de código con el estado. Input: evento del <input>.
  const onCodigo = (e) => setCodigo(e.target.value);

  // onBuscar: submit del formulario de búsqueda; normaliza (trim + mayúsculas) y busca
  // si hay texto y no hay una búsqueda en curso. Port de onBuscar (fuente 1162).
  const onBuscar = (e) => {
    e.preventDefault();
    const c = codigo.trim().toUpperCase();
    if (c && !buscando) buscarCodigo(c);
  };

  // onVerInput: solo admite dígitos y limpia el error previo. Input: evento del <input>.
  // Port de onVerInput (fuente 1179).
  const onVerInput = (e) => {
    setVerInput(e.target.value.replace(/[^0-9]/g, ""));
    setVerError(false);
  };

  // onVerificar: valida DNI (últimos 4) o código SMS del pedido encontrado. A los 3
  // intentos fallidos bloquea 30 s y avisa. Port de onVerificar (fuente 1185-1202).
  const onVerificar = (e) => {
    e.preventDefault();
    const t = Date.now();
    if (bloqueoHasta > t || !encontrado) return;
    const v = verInput.trim();
    const p = PEDIDOS[encontrado];
    if (v && (v === p.dni || (smsCode && v === smsCode))) {
      setVerificado(true);
      setVerError(false);
      setIntentos(0);
      avisar("Identidad verificada — datos desbloqueados", 3500);
    } else {
      const n = intentos + 1;
      if (n >= 3) {
        setIntentos(0);
        setVerError(false);
        setBloqueoHasta(t + 30000);
        setVerInput("");
        avisar("Demasiados intentos — acceso pausado 30 segundos", 4500);
      } else {
        setIntentos(n);
        setVerError(true);
      }
    }
  };

  // enviarSms: genera un código de 6 dígitos y lo "envía" por toast (demo). No actúa
  // si no hay pedido o si el acceso está bloqueado. Port de enviarSms (fuente 1204-1210).
  const enviarSms = () => {
    if (!encontrado || bloqueoHasta > Date.now()) return;
    const code = gen6();
    setSmsCode(code);
    avisar(
      "SMS enviado al " + PEDIDOS[encontrado].telMask + " — su código es " + code,
      10000
    );
  };

  // cerrarPedido: cierra el detalle y limpia los datos sensibles, volviendo a la
  // búsqueda vacía ("Cerrar y proteger datos"). Port de cerrarPedido (fuente 1211).
  const cerrarPedido = () => {
    setEncontrado(null);
    setVerificado(false);
    setVerInput("");
    setCodigo("");
    setSmsCode(null);
    setReprog(-1);
    setReprogOk(false);
  };

  // confirmarReprog: confirma la franja elegida y avisa por toast. Port de
  // confirmarReprog (fuente 1245-1248).
  const confirmarReprog = () => {
    setReprogOk(true);
    avisar("Reprogramación confirmada — le avisaremos cuando salga en ruta");
  };

  // --- valores derivados (equivalente a renderVals, rama personal) ---
  const now = ahora; // el reloj ya arranca en Date.now(); el countdown usa `ahora`
  const enc = encontrado ? PEDIDOS[encontrado] : null; // pedido hallado (sin verificar)
  const ped = enc && verificado ? enc : null; // pedido visible solo si verificado
  const em = enc ? ESTADOS[enc.estado] : ESTADOS.EN_RUTA; // meta de estado (colores/texto)
  const verBloq = bloqueoHasta > now; // ¿acceso bloqueado ahora mismo? (usa el reloj `ahora`)

  // Chips demo: código + etiqueta; al pulsar lanzan la búsqueda (fuente 1164-1166).
  const demoChips = [
    ["PD-2481", "en ruta"],
    ["PD-1073", "entregado"],
    ["PD-3316", "reprogramado"],
  ];

  const sinBusqueda = !enc && !buscando && !errorCod; // estado inicial (aún sin buscar)
  const porVerificar = !!enc && !verificado; // hay pedido pero falta verificar identidad

  return (
    <>
      {/* Formulario de búsqueda + chips demo */}
      <section
        data-psec="1"
        style={{ maxWidth: 920, margin: "0 auto", padding: "26px 24px 8px", width: "100%", boxSizing: "border-box", animation: "aparecer .45s ease both" }}
      >
        <form
          onSubmit={onBuscar}
          data-ppanel="1"
          style={{ background: "#fff", border: "1px solid rgba(15,43,74,.1)", borderRadius: 20, padding: 22, boxShadow: "0 16px 40px rgba(15,43,74,.08)", display: "flex", gap: 12, flexWrap: "wrap" }}
        >
          <input
            value={codigo}
            onChange={onCodigo}
            aria-label="Código de seguimiento"
            placeholder="Código de seguimiento · ej. PD-2481"
            className="ptl-input-buscar"
            style={{ flex: 1, minWidth: 200, boxSizing: "border-box", fontFamily: "Inter, sans-serif", fontSize: 15, padding: "14px 16px", border: "1.5px solid rgba(15,43,74,.16)", borderRadius: 12, background: "#f8fafc", color: "#0f2b4a", outline: "none" }}
          />
          <button
            type="submit"
            className="ptl-btn-rastrear"
            style={{ border: 0, cursor: "pointer", background: "#2679d8", color: "#fff", fontFamily: "Inter, sans-serif", fontWeight: 600, fontSize: 15, padding: "14px 28px", borderRadius: 12, transition: "background .2s ease" }}
          >
            {buscando ? "Buscando…" : "Rastrear"}
          </button>
          <div style={{ width: "100%", display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
            <span style={{ fontSize: 12, color: "#7288a0" }}>Pruebe con:</span>
            {demoChips.map(([cod, tag]) => (
              <button
                key={cod}
                type="button"
                onClick={() => buscarCodigo(cod)}
                className="ptl-chip-demo"
                style={{ border: "1px solid rgba(38,121,216,.3)", background: "#f2f7fc", color: "#1b5fb3", fontFamily: "Inter, sans-serif", fontSize: 12.5, fontWeight: 600, padding: "7px 13px", borderRadius: 99, cursor: "pointer", transition: "background .2s ease, border-color .2s ease" }}
              >
                {cod} · {tag}
              </button>
            ))}
          </div>
        </form>
      </section>

      {/* Estado: buscando (spinner girar) */}
      {buscando && (
        <div style={{ maxWidth: 920, margin: "0 auto", padding: "34px 24px", display: "flex", gap: 14, alignItems: "center", justifyContent: "center", color: "#4f6580", fontSize: 14.5, animation: "aparecer .3s ease both" }}>
          <span aria-hidden="true" style={{ width: 22, height: 22, borderRadius: 99, border: "3px solid #d7e4f1", borderTopColor: "#2679d8", animation: "girar .8s linear infinite", flex: "none" }} />
          Buscando su paquete en GeoTrack…
        </div>
      )}

      {/* Estado: código no encontrado */}
      {!!errorCod && (
        <section data-psec="1" style={{ maxWidth: 920, margin: "0 auto", padding: "10px 24px 20px", width: "100%", boxSizing: "border-box" }}>
          <div data-ppanel="1" style={{ background: "#fff", border: "1.5px solid rgba(217,122,31,.35)", borderRadius: 18, padding: "22px 24px", animation: "aparecer .4s ease both" }}>
            <p style={{ margin: 0, fontSize: 15, fontWeight: 700, color: "#0f2b4a" }}>No encontramos el código «{errorCod}»</p>
            <p style={{ margin: "8px 0 0", fontSize: 13.5, lineHeight: 1.6, color: "#4f6580" }}>
              Revise que esté igual que en el correo o SMS de su tienda (con guion, ej. PD-2481). Si acaba de recibir la confirmación, el código puede tardar unos minutos en activarse.
            </p>
          </div>
        </section>
      )}

      {/* Estado inicial: sin búsqueda */}
      {sinBusqueda && (
        <section data-psec="1" style={{ maxWidth: 920, margin: "0 auto", padding: "10px 24px 20px", width: "100%", boxSizing: "border-box" }}>
          <div style={{ border: "1.5px dashed rgba(38,121,216,.35)", borderRadius: 18, padding: "28px 24px", textAlign: "center", animation: "aparecer .5s ease .1s both" }}>
            <p style={{ margin: 0, fontSize: 15, fontWeight: 700, color: "#0f2b4a" }}>Su código está en el correo o SMS de su tienda</p>
            <p style={{ margin: "8px 0 0", fontSize: 13.5, lineHeight: 1.6, color: "#4f6580", maxWidth: 540, display: "inline-block" }}>
              Cuando Ripley, Falabella u otra tienda confirma su envío con SAVA, le llega un código como{" "}
              <span style={{ fontWeight: 700, color: "#1b5fb3" }}>PD-2481</span>. Por su seguridad, además del código le pediremos verificar su identidad.
            </p>
          </div>
        </section>
      )}

      {/* Tarjeta de verificación de identidad */}
      {porVerificar && (
        <Verificacion
          enc={enc}
          em={em}
          encCod={encontrado}
          verInput={verInput}
          onVerInput={onVerInput}
          onVerificar={onVerificar}
          verError={verError}
          verBloq={verBloq}
          intentos={intentos}
          bloqueoHasta={bloqueoHasta}
          now={now}
          enviarSms={enviarSms}
        />
      )}

      {/* Detalle del pedido (solo tras verificar) */}
      {!!ped && (
        <section data-psec="1" style={{ maxWidth: 920, margin: "0 auto", padding: "10px 24px 20px", width: "100%", boxSizing: "border-box" }}>
          {/* Barra de identidad verificada + cerrar */}
          <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap", margin: "0 0 12px", animation: "aparecer .4s ease both" }}>
            <span style={{ display: "inline-flex", gap: 9, alignItems: "center", background: "#e3f2e8", color: "#1e7a43", fontSize: 12.5, fontWeight: 700, padding: "8px 15px", borderRadius: 99 }}>
              <span style={{ flex: "none", width: 16, height: 16, borderRadius: 99, background: "#22a35e", color: "#fff", display: "grid", placeItems: "center", fontSize: 10 }}>✓</span>
              <span>Identidad verificada · DNI ***{enc.dni}</span>
            </span>
            <button
              type="button"
              onClick={cerrarPedido}
              className="ptl-btn-cerrar"
              style={{ border: "1.5px solid rgba(15,43,74,.16)", background: "#fff", color: "#3d5570", fontFamily: "Inter, sans-serif", fontSize: 12.5, fontWeight: 600, padding: "8px 15px", borderRadius: 99, cursor: "pointer", transition: "border-color .2s ease, color .2s ease" }}
            >
              Cerrar y proteger datos
            </button>
          </div>

          <PanelEstado ped={ped} encCod={encontrado} em={em} />

          {/* Mapa + línea de tiempo */}
          <div data-prg="1" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(300px,1fr))", gap: 16, margin: "16px 0 0" }}>
            <MapaRecorrido ped={ped} em={em} />
            <TimelinePedido ped={ped} />
          </div>

          {/* Repartidor (en ruta) */}
          {ped.estado === "EN_RUTA" && <Repartidor ped={ped} />}

          {/* Evidencia (entregado) */}
          {ped.estado === "ENTREGADO" && <Evidencia ped={ped} />}

          {/* Reprogramación (reprogramado) */}
          {ped.estado === "REPROGRAMADO" && (
            <Reprogramacion
              ped={ped}
              reprog={reprog}
              reprogOk={reprogOk}
              onElegir={setReprog}
              confirmarReprog={confirmarReprog}
            />
          )}
        </section>
      )}
    </>
  );
}

// ----------------------------------------------------------------------------
// Verificacion: tarjeta con el resumen enmascarado del pedido + el form de DNI/SMS,
// el aviso de bloqueo con countdown y el hint de demo. Input: pedido `enc`, meta de
// estado `em`, código, valor/handlers del input, estado de error/bloqueo/intentos,
// el reloj `now` y el disparador de SMS.
// ----------------------------------------------------------------------------
function Verificacion({ enc, em, encCod, verInput, onVerInput, onVerificar, verError, verBloq, intentos, bloqueoHasta, now, enviarSms }) {
  const bloqueoTxt =
    "Demasiados intentos fallidos. Por su seguridad, espere " +
    Math.ceil(Math.max(0, bloqueoHasta - now) / 1000) +
    " s para volver a intentar.";
  const intentosTxt = String(Math.max(0, 3 - intentos));

  return (
    <section data-psec="1" style={{ maxWidth: 920, margin: "0 auto", padding: "10px 24px 20px", width: "100%", boxSizing: "border-box" }}>
      <div data-ppanel="1" style={{ background: "#fff", border: "1.5px solid rgba(38,121,216,.3)", borderRadius: 22, padding: 26, boxShadow: "0 16px 40px rgba(15,43,74,.08)", animation: "aparecer .45s ease both" }}>
        <div style={{ display: "flex", gap: 16, alignItems: "flex-start", flexWrap: "wrap" }}>
          {/* Icono de candado */}
          <span aria-hidden="true" style={{ flex: "none", width: 46, height: 46, borderRadius: 14, background: "#eaf3fc", display: "grid", placeItems: "center" }}>
            <span style={{ width: 16, height: 13, borderRadius: 3, background: "#1b5fb3", position: "relative" }}>
              <span style={{ position: "absolute", top: -8, left: 2.5, width: 11, height: 10, border: "2.5px solid #1b5fb3", borderBottom: 0, borderRadius: "7px 7px 0 0", boxSizing: "border-box" }} />
            </span>
          </span>
          <div style={{ flex: 1, minWidth: 220 }}>
            <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
              <p style={{ margin: 0, fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: 19 }}>Pedido {encCod} encontrado</p>
              <span style={{ background: em.bg, color: em.fg, fontSize: 11, fontWeight: 700, letterSpacing: ".05em", padding: "6px 12px", borderRadius: 99, animation: "latido 2.6s ease-in-out infinite" }}>{em.tx}</span>
            </div>
            <p style={{ margin: "6px 0 0", fontSize: 13.5, color: "#4f6580" }}>de {enc.retail} · {enc.destinoMask}</p>
          </div>
        </div>

        <div style={{ margin: "18px 0 0", background: "#f2f7fc", borderRadius: 14, padding: "18px 20px" }}>
          <p style={{ margin: 0, fontSize: 14.5, fontWeight: 700, color: "#0f2b4a" }}>Verifique que el pedido es suyo para ver el detalle</p>
          <p style={{ margin: "6px 0 0", fontSize: 13, lineHeight: 1.6, color: "#4f6580" }}>
            Por su seguridad, la dirección y los datos completos solo se muestran al destinatario. Ingrese los <strong>últimos 4 dígitos del DNI</strong> del destinatario, o pida un <strong>código SMS</strong> al celular que termina en {enc.telMask}.
          </p>

          {verBloq && (
            <div style={{ margin: "14px 0 0", background: "#fdeedd", border: "1px solid rgba(217,122,31,.35)", borderRadius: 12, padding: "13px 16px", fontSize: 13.5, fontWeight: 600, color: "#b35c12", animation: "aparecer .3s ease both" }}>
              {bloqueoTxt}
            </div>
          )}

          {!verBloq && (
            <>
              <form onSubmit={onVerificar} style={{ margin: "14px 0 0", display: "flex", gap: 10, flexWrap: "wrap" }}>
                <input
                  value={verInput}
                  onChange={onVerInput}
                  inputMode="numeric"
                  maxLength={6}
                  aria-label="DNI o código SMS"
                  placeholder="DNI (4 dígitos) o código SMS (6)"
                  className="ptl-input-ver"
                  style={{ flex: 1, minWidth: 200, boxSizing: "border-box", fontFamily: "Inter, sans-serif", fontSize: 14.5, letterSpacing: ".06em", padding: "13px 15px", border: "1.5px solid rgba(15,43,74,.16)", borderRadius: 12, background: "#fff", color: "#0f2b4a", outline: "none" }}
                />
                <button
                  type="submit"
                  className="ptl-btn-verificar"
                  style={{ border: 0, cursor: "pointer", background: "#0f2b4a", color: "#fff", fontFamily: "Inter, sans-serif", fontWeight: 600, fontSize: 14, padding: "13px 24px", borderRadius: 12, transition: "background .2s ease" }}
                >
                  Verificar
                </button>
              </form>
              {verError && (
                <p style={{ margin: "10px 0 0", fontSize: 13, fontWeight: 600, color: "#c8362b", animation: "sacudir .4s ease both" }}>
                  Dato incorrecto · le quedan {intentosTxt} intentos antes del bloqueo temporal
                </p>
              )}
              <div style={{ margin: "12px 0 0", display: "flex", gap: "8px 18px", flexWrap: "wrap", alignItems: "center" }}>
                <button
                  type="button"
                  onClick={enviarSms}
                  className="ptl-link-sms"
                  style={{ border: 0, background: "none", cursor: "pointer", padding: 0, fontFamily: "Inter, sans-serif", fontSize: 13, fontWeight: 600, color: "#2679d8", textDecoration: "underline" }}
                >
                  Enviarme un código por SMS
                </button>
                <span style={{ fontSize: 11.5, color: "#8ba0b6" }}>Para esta demo: DNI que termina en {enc.dni}</span>
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  );
}

// ----------------------------------------------------------------------------
// PanelEstado: cabecera del detalle con código, retail/destino, badge de estado
// animado, ETA y la barra de progreso de 4 pasos (dot pulsante en el paso actual).
// Input: pedido `ped`, su código `encCod` y la meta de estado `em`.
// ----------------------------------------------------------------------------
function PanelEstado({ ped, encCod, em }) {
  // Pasos del progreso: en ENTREGADO el paso actual es el 3 (Entregado), en el resto el 2.
  const idx = ped.estado === "ENTREGADO" ? 3 : 2;
  const nombres = ["Recibido", "Verificado", ped.estado === "REPROGRAMADO" ? "Reprogramado" : "En ruta", "Entregado"];
  const pasos = nombres.map((n, i) => {
    const ep = i < idx ? "done" : i === idx ? "actual" : "pend";
    return {
      n,
      color: ep === "pend" ? "#dce8f4" : ep === "actual" ? em.trazo : "#2679d8",
      halo: ep === "actual" ? "0 0 0 5px " + em.trazo + "2e" : "none",
      fg: ep === "pend" ? "#8ba0b6" : "#0f2b4a",
      peso: ep === "actual" ? 700 : 600,
    };
  });

  return (
    <div data-ppanel="1" style={{ background: "#fff", border: "1px solid rgba(15,43,74,.08)", borderRadius: 22, padding: 26, boxShadow: "0 14px 36px rgba(15,43,74,.07)", animation: "aparecer .45s ease both" }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap", alignItems: "flex-start" }}>
        <div>
          <p style={{ margin: 0, fontSize: 11.5, fontWeight: 700, letterSpacing: ".12em", color: "#7288a0" }}>PEDIDO</p>
          <h2 style={{ margin: "2px 0 0", fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: 28, letterSpacing: ".01em" }}>{encCod}</h2>
          <p style={{ margin: "6px 0 0", fontSize: 13.5, color: "#4f6580" }}>de {ped.retail} · {ped.destino}</p>
        </div>
        <span style={{ background: em.bg, color: em.fg, fontSize: 12, fontWeight: 700, letterSpacing: ".06em", padding: "8px 15px", borderRadius: 99, animation: "latido 2.6s ease-in-out infinite" }}>{em.tx}</span>
      </div>

      <div style={{ margin: "18px 0 0", background: "#f2f7fc", border: "1px solid rgba(38,121,216,.16)", borderRadius: 14, padding: "14px 18px", display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <span style={{ width: 9, height: 9, borderRadius: 99, background: em.trazo, flex: "none", animation: "latido 2s ease-in-out infinite" }} />
        <p style={{ margin: 0, fontSize: 15, fontWeight: 700, color: "#0f2b4a" }}>
          {ped.etaT} <span style={{ fontWeight: 500, color: "#4f6580" }}>{ped.eta}</span>
        </p>
      </div>

      <div style={{ margin: "22px 0 0" }}>
        <div style={{ height: 7, borderRadius: 99, background: "#e8f0f8", overflow: "hidden" }}>
          <div style={{ height: "100%", borderRadius: 99, width: ped.pct, background: em.barra, transition: "width 1.3s ease .15s" }} />
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 6, margin: "12px 0 0" }}>
          {pasos.map((pa) => (
            <div key={pa.n} style={{ display: "grid", gap: 6, justifyItems: "start" }}>
              <span style={{ width: 11, height: 11, borderRadius: 99, background: pa.color, boxShadow: pa.halo }} />
              <span style={{ fontSize: 12, fontWeight: pa.peso, color: pa.fg, lineHeight: 1.25 }}>{pa.n}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------------
// MapaRecorrido: mapa SVG estático del recorrido (manzanas + ruta con animación CSS
// `dashflow`), con el trazo real recortado por `pedDash` (según pct) y la camioneta
// posicionada sobre la ruta por `van` (solo visible EN_RUTA). Input: pedido `ped` y
// la meta de estado `em` (para el color del trazo).
// ----------------------------------------------------------------------------
function MapaRecorrido({ ped, em }) {
  const rutaD = "M 34 206 L 148 206 L 148 128 L 262 128 L 262 62 L 340 62 L 340 158 L 424 158";
  const pedDash = parseInt(ped.pct, 10) + " 100"; // trazo del avance (pathLength=100)
  const esEnRuta = ped.estado === "EN_RUTA";

  return (
    <div data-ppanel="1" style={{ background: "#fff", border: "1px solid rgba(15,43,74,.08)", borderRadius: 20, padding: 20, animation: "aparecer .5s ease .1s both" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10, margin: "0 0 12px" }}>
        <span style={{ fontFamily: "Archivo, sans-serif", fontWeight: 700, fontSize: 14.5 }}>Recorrido de hoy</span>
        {esEnRuta && (
          <span style={{ background: "#e3f2e8", color: "#1e7a43", fontSize: 10.5, fontWeight: 700, letterSpacing: ".06em", padding: "4px 10px", borderRadius: 99, animation: "latido 1.9s ease-in-out infinite" }}>EN VIVO</span>
        )}
      </div>
      <svg viewBox="0 0 460 250" style={{ width: "100%", height: "auto", display: "block" }} aria-label="Mapa del recorrido del pedido">
        <rect x="0" y="0" width="460" height="250" rx="14" fill="#eef4fa" />
        <g fill="#e0eaf4">
          <rect x="14" y="16" width="120" height="96" rx="8" />
          <rect x="162" y="16" width="84" height="96" rx="8" />
          <rect x="278" y="78" width="46" height="34" rx="8" />
          <rect x="356" y="16" width="90" height="126" rx="8" />
          <rect x="14" y="122" width="120" height="68" rx="8" />
          <rect x="162" y="142" width="84" height="48" rx="8" />
          <rect x="278" y="190" width="76" height="44" rx="8" />
        </g>
        <path d={rutaD} fill="none" stroke="#dce8f4" strokeWidth="9" strokeLinecap="round" strokeLinejoin="round" />
        <path d={rutaD} fill="none" stroke="#b9d3ec" strokeWidth="3" strokeDasharray="5 9" strokeLinecap="round" strokeLinejoin="round" style={{ animation: "dashflow 1.2s linear infinite" }} />
        <path d={rutaD} pathLength="100" fill="none" stroke={em.trazo} strokeWidth="5" strokeDasharray={pedDash} strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="34" cy="206" r="14" fill="#2679d8" opacity=".14" style={{ transformBox: "fill-box", transformOrigin: "center", animation: "pulso 2.6s ease-out infinite" }} />
        <circle cx="34" cy="206" r="8" fill="#0f2b4a" stroke="#fff" strokeWidth="2.5" />
        <circle cx="424" cy="158" r="15" fill={em.trazo} opacity=".15" style={{ transformBox: "fill-box", transformOrigin: "center", animation: "pulso 2.2s ease-out infinite" }} />
        <circle cx="424" cy="158" r="9" fill="#fff" stroke={em.trazo} strokeWidth="3" />
        <circle cx="424" cy="158" r="3.5" fill={em.trazo} />
        <g style={{ offsetPath: `path('${rutaD}')`, offsetDistance: ped.van, offsetRotate: "auto", display: esEnRuta ? "inline" : "none", transition: "offset-distance 1.4s ease" }}>
          <circle r="16" fill="#2679d8" opacity=".15" style={{ transformBox: "fill-box", transformOrigin: "center", animation: "pulso 2.4s ease-out infinite" }} />
          <rect x="-12" y="-8" width="24" height="16" rx="4" fill="#0f2b4a" />
          <rect x="4" y="-6" width="6" height="12" rx="2" fill="#5db1f0" />
        </g>
        <text x="30" y="194" style={{ fontFamily: "Inter, sans-serif", fontSize: 11, fontWeight: 700, fill: "#0f2b4a", paintOrder: "stroke", stroke: "#eef4fa", strokeWidth: "4px" }}>Centro SAVA</text>
        <text x="430" y="186" textAnchor="end" style={{ fontFamily: "Inter, sans-serif", fontSize: 11, fontWeight: 700, fill: "#0f2b4a", paintOrder: "stroke", stroke: "#eef4fa", strokeWidth: "4px" }}>Su dirección</text>
        <text x="30" y="236" style={{ fontFamily: "Inter, sans-serif", fontSize: 10.5, fontWeight: 600, fill: "#8ba0b6" }}>Independencia</text>
        <text x="252" y="44" style={{ fontFamily: "Inter, sans-serif", fontSize: 10.5, fontWeight: 600, fill: "#8ba0b6" }}>San Isidro</text>
        <text x="446" y="236" textAnchor="end" style={{ fontFamily: "Inter, sans-serif", fontSize: 10.5, fontWeight: 600, fill: "#8ba0b6" }}>Miraflores</text>
      </svg>
      <p style={{ margin: "12px 0 0", fontSize: 12.5, lineHeight: 1.55, color: "#4f6580" }}>{ped.nota}</p>
    </div>
  );
}

// ----------------------------------------------------------------------------
// TimelinePedido: línea de tiempo de eventos del pedido, con dot por tipo (azul
// normal / naranja alerta / verde ok), halo en el evento en vivo y línea de unión
// (transparente en el último). Input: pedido `ped` (usa ped.eventos).
// ----------------------------------------------------------------------------
function TimelinePedido({ ped }) {
  const eventos = ped.eventos.map((ev, i) => ({
    t: ev.t,
    d: ev.d,
    h: ev.h,
    color: ev.alerta ? "#d97a1f" : ev.ok ? "#22a35e" : "#2679d8",
    halo: ev.vivo ? "0 0 0 5px rgba(38,121,216,.18)" : "none",
    linea: i === ped.eventos.length - 1 ? "transparent" : "#dce8f4",
    delay: i * 110 + "ms",
  }));

  return (
    <div data-ppanel="1" style={{ background: "#fff", border: "1px solid rgba(15,43,74,.08)", borderRadius: 20, padding: "20px 20px 6px", animation: "aparecer .5s ease .18s both" }}>
      <p style={{ margin: "0 0 16px", fontFamily: "Archivo, sans-serif", fontWeight: 700, fontSize: 14.5 }}>Línea de tiempo</p>
      {eventos.map((ev, i) => (
        <div key={i} style={{ display: "flex", gap: 14, animation: "aparecer .5s ease both", animationDelay: ev.delay }}>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
            <span style={{ width: 12, height: 12, borderRadius: 99, flex: "none", marginTop: 3, background: ev.color, boxShadow: ev.halo }} />
            <span style={{ width: 2, flex: 1, background: ev.linea, minHeight: 12 }} />
          </div>
          <div style={{ padding: "0 0 16px" }}>
            <p style={{ margin: 0, fontSize: 14, fontWeight: 600, color: "#0f2b4a" }}>{ev.t}</p>
            <p style={{ margin: "2px 0 0", fontSize: 12.5, color: "#7288a0" }}>{ev.d}</p>
            <p style={{ margin: "3px 0 0", fontSize: 11.5, fontWeight: 600, color: "#8ba0b6" }}>{ev.h}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

// ----------------------------------------------------------------------------
// Repartidor: tarjeta del conductor asignado (iniciales, nombre, placa y parada)
// con badge EN VIVO. Solo se muestra cuando el pedido está EN_RUTA. Input: `ped`.
// ----------------------------------------------------------------------------
function Repartidor({ ped }) {
  const ini = ped.conductor.split(" ").map((w) => w.charAt(0)).join("");
  return (
    <div data-ppanel="1" style={{ margin: "16px 0 0", background: "#fff", border: "1px solid rgba(15,43,74,.08)", borderRadius: 20, padding: "20px 22px", display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap", animation: "aparecer .5s ease .26s both" }}>
      <span style={{ flex: "none", width: 52, height: 52, borderRadius: 99, background: "#eaf3fc", display: "grid", placeItems: "center", fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: 17, color: "#1b5fb3" }}>{ini}</span>
      <div style={{ flex: 1, minWidth: 200 }}>
        <p style={{ margin: 0, fontSize: 15, fontWeight: 700, color: "#0f2b4a" }}>
          {ped.conductor} <span style={{ fontWeight: 500, color: "#7288a0", fontSize: 13 }}>· su repartidor</span>
        </p>
        <p style={{ margin: "3px 0 0", fontSize: 13, color: "#4f6580" }}>Camioneta placa {ped.placa} · {ped.parada}</p>
      </div>
      <span style={{ background: "#e3f2e8", color: "#1e7a43", fontSize: 11, fontWeight: 700, letterSpacing: ".06em", padding: "5px 12px", borderRadius: 99, animation: "latido 2s ease-in-out infinite" }}>EN VIVO</span>
    </div>
  );
}

// ----------------------------------------------------------------------------
// Evidencia: confirmación de entrega con "Recibido por" y placeholder de la foto POD.
// Solo se muestra cuando el pedido está ENTREGADO. Input: `ped`.
// ----------------------------------------------------------------------------
function Evidencia({ ped }) {
  return (
    <div data-ppanel="1" style={{ margin: "16px 0 0", background: "#fff", border: "1px solid rgba(34,163,94,.3)", borderRadius: 20, padding: 22, display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(240px,1fr))", gap: 20, alignItems: "center", animation: "aparecer .5s ease .26s both" }}>
      <div>
        <p style={{ margin: 0, fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: 18, color: "#1e7a43" }}>✓ Entrega confirmada</p>
        <p style={{ margin: "8px 0 0", fontSize: 14, lineHeight: 1.6, color: "#4f6580" }}>{ped.recibido}</p>
        <p style={{ margin: "6px 0 0", fontSize: 12.5, color: "#8ba0b6" }}>El conductor registró la evidencia en GeoTrack al momento de entregar. Solo el destinatario verificado puede verla.</p>
      </div>
      {/* Placeholder de la foto de entrega (POD) — sin imagen real en la demo */}
      <div className="ptl-pod" style={{ width: "100%", height: 180, borderRadius: 14, background: "#eef4fa", border: "1px dashed rgba(15,43,74,.16)", display: "grid", placeItems: "center", color: "#8ba0b6", fontSize: 12.5, fontWeight: 600 }}>
        Foto de entrega (POD)
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------------
// Reprogramacion: panel para elegir una franja horaria (OPCIONES) y confirmar la
// nueva visita, o el aviso de éxito si ya se confirmó. Solo se muestra en estado
// REPROGRAMADO. Input: pedido `ped`, índice elegido `reprog`, bandera `reprogOk`,
// el selector `onElegir` y el confirmador `confirmarReprog`.
// ----------------------------------------------------------------------------
function Reprogramacion({ ped, reprog, reprogOk, onElegir, confirmarReprog }) {
  const reprogTxt = reprog >= 0 ? OPCIONES[reprog].toLowerCase() : "";
  return (
    <div data-ppanel="1" style={{ margin: "16px 0 0", background: "#fff", border: "1.5px solid rgba(217,122,31,.35)", borderRadius: 20, padding: 22, animation: "aparecer .5s ease .26s both" }}>
      <p style={{ margin: 0, fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: 18, color: "#b35c12" }}>Necesitamos una nueva fecha</p>
      <p style={{ margin: "8px 0 0", fontSize: 14, lineHeight: 1.6, color: "#4f6580" }}>{ped.motivo}. Elija cuándo volvemos a tocar su puerta:</p>

      {!reprogOk && (
        <>
          <div style={{ margin: "14px 0 0", display: "flex", gap: 8, flexWrap: "wrap" }}>
            {OPCIONES.map((n, i) => (
              <button
                key={n}
                type="button"
                onClick={() => onElegir(i)}
                style={{ border: `1.5px solid ${reprog === i ? "#2679d8" : "rgba(15,43,74,.16)"}`, background: reprog === i ? "#eaf3fc" : "#fff", color: reprog === i ? "#1b5fb3" : "#3d5570", fontFamily: "Inter, sans-serif", fontSize: 13, fontWeight: 600, padding: "11px 16px", borderRadius: 12, cursor: "pointer", transition: "border-color .2s ease, background .2s ease" }}
              >
                {n}
              </button>
            ))}
          </div>
          {reprog >= 0 && (
            <button
              type="button"
              onClick={confirmarReprog}
              className="ptl-btn-confirmar-reprog"
              style={{ margin: "14px 0 0", border: 0, cursor: "pointer", background: "#2679d8", color: "#fff", fontFamily: "Inter, sans-serif", fontWeight: 600, fontSize: 14, padding: "13px 24px", borderRadius: 99, animation: "aparecer .3s ease both", transition: "background .2s ease" }}
            >
              Confirmar visita: {reprogTxt}
            </button>
          )}
        </>
      )}

      {reprogOk && (
        <div style={{ margin: "14px 0 0", background: "#e3f2e8", borderRadius: 12, padding: "14px 18px", fontSize: 14, fontWeight: 600, color: "#1e7a43", animation: "aparecer .35s ease both" }}>
          ✓ Listo — su pedido saldrá {reprogTxt}. Le avisaremos por SMS cuando esté en ruta.
        </div>
      )}
    </div>
  );
}
