import { useEffect, useMemo, useState } from "react";
import { CLAVE, EMPRESAS, FILAS, ESTADOS } from "../datos/demo.js";

// ============================================================================
// Vista EMPRESA / RETAIL del portal de clientes (Tarea 11). Port fiel del mockup
// aprobado (portal pagina.html, JSX 729-905 · lógica 1056-1079, 1250-1340, 1389-1411).
// Flujo completo en 3 pasos: credenciales (código de empresa + clave, con chips demo,
// error con sacudir y bloqueo temporal de 45 s) → verificación en dos pasos (OTP de
// 6 dígitos con reenvío y bloqueo a los 3 intentos) → panel corporativo (KPIs
// clicables, avance del día, filtros por estado/distrito/franja/búsqueda/orden,
// toggle de privacidad, tabla con filas expandibles y mini-línea de tiempo, más el
// countdown de sesión que expira sola a los 10 minutos). Demo puro: sin fetch, los
// datos salen de ../datos/demo.js (FILAS es el ROWS de la fuente).
// ============================================================================

// gen6: genera un código OTP de 6 dígitos aleatorio (string "100000".."999999").
// No recibe input. Port de Component.gen6 (fuente línea 1038).
const gen6 = () => String(Math.floor(100000 + Math.random() * 900000));

// horaNum: convierte una hora "HH:MM" a número decimal para comparar/ordenar; "—"
// (aún sin salir) pasa a 99 para caer en la franja "por salir". Input: string de hora.
// Port de la función local `horaNum` de renderVals (fuente 1124).
const horaNum = (h) => {
  if (h === "—") return 99;
  const m = h.split(":");
  return parseInt(m[0], 10) + parseInt(m[1], 10) / 60;
};

// maskN: enmascara el nombre del cliente dejando las 4 primeras letras + "•••".
// Input: string del nombre. Port de `maskN` (fuente 1142).
const maskN = (s) => s.slice(0, 4) + "•••";

// maskD: enmascara la dirección dejando la primera palabra + "••• •••".
// Input: string de dirección. Port de `maskD` (fuente 1143).
const maskD = (s) => s.split(" ")[0] + " ••• •••";

// detalleDe: arma la mini-línea de tiempo de un pedido corporativo según su estado
// (manifiesto + verificación fijos, y luego eventos que dependen del estado).
// Input: fila normalizada `r` y el nombre de la empresa `empN`. Devuelve un array de
// eventos { h, t, color }. Port de Component.detalleDe (fuente 1061-1079).
const detalleDe = (r, empN) => {
  const evs = [
    { h: "08:40", t: "Manifiesto de " + empN, color: "#2679d8" },
    { h: "10:30", t: "Verificado en centro SAVA", color: "#2679d8" },
  ];
  if (r.estado === "ENTREGADO") {
    evs.push({ h: "11:30", t: "Salió a reparto", color: "#2679d8" });
    evs.push({ h: r.h, t: "Entregado · POD con foto en GeoTrack", color: "#22a35e" });
  } else if (r.estado === "EN_RUTA") {
    evs.push({ h: r.h, t: "En ruta · " + r.extra, color: "#2679d8" });
  } else if (r.estado === "POR_SALIR") {
    evs.push({ h: "—", t: r.extra, color: "#7288a0" });
  } else if (r.estado === "OBSERVADO") {
    evs.push({ h: r.h, t: r.extra + " · en gestión por el equipo SAVA", color: "#d97a1f" });
  } else {
    evs.push({ h: "Ayer", t: r.extra, color: "#d97a1f" });
  }
  return evs;
};

// Orden de prioridad de los botones-filtro de estado (los que tengan >0 se muestran).
// Port de la constante ORDEN de renderVals (fuente 1141).
const ORDEN = ["ENTREGADO", "EN_RUTA", "POR_SALIR", "OBSERVADO", "REPROGRAMADO"];

// PanelEmpresa: vista corporativa del portal para clientes retail.
// Input: prop `avisar(texto, ms)` para mostrar el toast del portal.
export default function PanelEmpresa({ avisar }) {
  // --- Estado del flujo (port del bloque de estado empresa del mockup) ---
  const [paso, setPaso] = useState(0); // 0 credenciales · 1 OTP · 2 panel
  const [codEmp, setCodEmp] = useState(""); // input del código de empresa
  const [claveEmp, setClaveEmp] = useState(""); // input de la clave de acceso
  const [cargando, setCargando] = useState(false); // "Verificando…" mientras valida
  const [error, setError] = useState(false); // credenciales incorrectas (aviso + sacudir)
  const [intentos, setIntentos] = useState(0); // intentos fallidos de credenciales
  const [bloqueoHasta, setBloqueoHasta] = useState(0); // timestamp fin del bloqueo (45 s)
  const [pendiente, setPendiente] = useState(null); // código validado, a la espera del OTP
  const [otpCode, setOtpCode] = useState(null); // OTP generado (el "enviado" por correo)
  const [otpInput, setOtpInput] = useState(""); // input del OTP (solo dígitos)
  const [otpError, setOtpError] = useState(false); // OTP incorrecto (aviso + sacudir)
  const [otpIntentos, setOtpIntentos] = useState(0); // intentos fallidos de OTP
  const [empresa, setEmpresa] = useState(null); // empresa con sesión iniciada (o null)
  const [sesionFin, setSesionFin] = useState(0); // timestamp de expiración de la sesión
  const [filtro, setFiltro] = useState("TODOS"); // filtro de estado activo
  const [q, setQ] = useState(""); // búsqueda libre
  const [fDist, setFDist] = useState("TODOS"); // filtro de distrito
  const [fFranja, setFFranja] = useState("TODAS"); // filtro de franja horaria
  const [fOrden, setFOrden] = useState("hora"); // criterio de orden
  const [privado, setPrivado] = useState(false); // ocultar datos personales (privacidad)
  const [abierta, setAbierta] = useState(null); // código de la fila expandida (o null)
  const [ahora, setAhora] = useState(() => Date.now()); // reloj para countdowns/expiración

  // hoyTxt: fecha de hoy ("Lunes, 3 de julio") capitalizada. Se calcula UNA vez con el
  // inicializador de useState para no llamar a new Date() en el cuerpo del render
  // (regla react-hooks/purity de React 19). Port de `hoyTxt` (fuente 1323-1326).
  const [hoyTxt] = useState(() => {
    const s = new Date().toLocaleDateString("es-PE", { weekday: "long", day: "numeric", month: "long" });
    return s.charAt(0).toUpperCase() + s.slice(1);
  });

  // cerrarSesionEmp: cierra la sesión corporativa, resetea todos los filtros y el flujo
  // a credenciales y (opcional) muestra el motivo por toast. Input: `motivo` (string o
  // vacío). Se declara antes del reloj porque este la invoca al expirar la sesión.
  // Port de Component.cerrarSesionEmp (fuente 1055-1058).
  const cerrarSesionEmp = (motivo) => {
    setPaso(0);
    setEmpresa(null);
    setPendiente(null);
    setSesionFin(0);
    setClaveEmp("");
    setOtpInput("");
    setOtpCode(null);
    setAbierta(null);
    setFiltro("TODOS");
    setQ("");
    setFDist("TODOS");
    setFFranja("TODAS");
    setFOrden("hora");
    setPrivado(false);
    if (motivo) avisar(motivo, 5000);
  };

  // Reloj de 1 s: solo hace falta con la sesión activa (countdown + expiración) o con un
  // bloqueo vigente (countdown de 45 s). El setState va DENTRO del callback del interval
  // (no en el cuerpo del effect), así no dispara la regla de lint "setState síncrono en
  // effect". Se limpia al desmontar o cuando ya no hace falta el reloj.
  // Port de Component.tic + su setInterval (fuente 1391, 1402-1411).
  useEffect(() => {
    const sesionActiva = paso === 2 && sesionFin > 0;
    const bloqueoActivo = bloqueoHasta > Date.now();
    if (!sesionActiva && !bloqueoActivo) return undefined;
    const id = setInterval(() => {
      const t = Date.now();
      // La sesión expiró: cierra por seguridad con el aviso exacto de la fuente.
      if (paso === 2 && sesionFin > 0 && t >= sesionFin) {
        clearInterval(id);
        cerrarSesionEmp("Sesión expirada por seguridad — vuelva a ingresar");
        return;
      }
      setAhora(t);
      // El bloqueo venció y no hay sesión: ya no hace falta el reloj.
      if (!(paso === 2 && sesionFin > 0) && t >= bloqueoHasta) clearInterval(id);
    }, 1000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paso, sesionFin, bloqueoHasta]);

  // onCodEmp / onClaveEmp: sincronizan los inputs y limpian el error de credenciales.
  // Input: evento del <input>. Port de onCodEmp/onClaveEmp (fuente 1254, 1256).
  const onCodEmp = (e) => {
    setCodEmp(e.target.value);
    setError(false);
  };
  const onClaveEmp = (e) => {
    setClaveEmp(e.target.value);
    setError(false);
  };

  // onCreds: valida credenciales tras un pequeño retardo (simula ida al servidor). Si
  // EMPRESAS[c] existe y la clave coincide → genera OTP, pasa al paso 1 y "envía" el
  // código por toast (11 s). Si no, suma un intento; a los 3 bloquea 45 s. No actúa si
  // hay bloqueo vigente o ya está cargando. Input: evento submit.
  // Port de onCreds (fuente 1263-1286).
  const onCreds = (e) => {
    e.preventDefault();
    const t = Date.now();
    if (bloqueoHasta > t || cargando) return;
    const c = codEmp.trim().toUpperCase();
    setCargando(true);
    setError(false);
    setTimeout(() => {
      const ok = EMPRESAS[c] && claveEmp === CLAVE;
      if (ok) {
        const otp = gen6();
        setCargando(false);
        setPendiente(c);
        setPaso(1);
        setOtpCode(otp);
        setOtpInput("");
        setOtpError(false);
        setOtpIntentos(0);
        setIntentos(0);
        setCodEmp(c);
        avisar("Correo al administrador de " + EMPRESAS[c].nombre + " — código de verificación: " + otp, 11000);
      } else {
        const n = intentos + 1;
        if (n >= 3) {
          setCargando(false);
          setIntentos(0);
          setError(false);
          setBloqueoHasta(Date.now() + 45000);
          setClaveEmp("");
          avisar("Demasiados intentos — acceso pausado 45 segundos", 5000);
        } else {
          setCargando(false);
          setError(true);
          setIntentos(n);
        }
      }
    }, 700);
  };

  // usarChip: autocompleta código + clave demo desde un chip y limpia el error.
  // Input: código de empresa `c`. Port de chipsEmp[].usar (fuente 1287-1289).
  const usarChip = (c) => {
    setCodEmp(c);
    setClaveEmp(CLAVE);
    setError(false);
  };

  // onOtpInput: solo admite dígitos y limpia el error del OTP. Input: evento del <input>.
  // Port de onOtpInput (fuente 1292).
  const onOtpInput = (e) => {
    setOtpInput(e.target.value.replace(/[^0-9]/g, ""));
    setOtpError(false);
  };

  // onOtp: valida el OTP ingresado contra el generado. Si acierta → inicia sesión
  // (paso 2), fija la expiración en 10 min, resetea filtros y avisa. Si falla suma un
  // intento; a los 3 vuelve a credenciales y bloquea 45 s. Input: evento submit.
  // Port de onOtp (fuente 1294-1309).
  const onOtp = (e) => {
    e.preventDefault();
    if (otpInput && otpInput === otpCode) {
      setPaso(2);
      setEmpresa(pendiente);
      setSesionFin(Date.now() + 600000);
      setAhora(Date.now()); // sincroniza el reloj: evita mostrar un countdown viejo el primer segundo
      setOtpError(false);
      setAbierta(null);
      setFiltro("TODOS");
      setQ("");
      setFDist("TODOS");
      setFFranja("TODAS");
      setFOrden("hora");
      setPrivado(false);
      avisar("Sesión segura iniciada — expira automáticamente en 10 minutos", 5000);
    } else {
      const n = otpIntentos + 1;
      if (n >= 3) {
        setPaso(0);
        setPendiente(null);
        setOtpCode(null);
        setOtpInput("");
        setOtpIntentos(0);
        setOtpError(false);
        setBloqueoHasta(Date.now() + 45000);
        setClaveEmp("");
        avisar("Verificación fallida — vuelva a ingresar sus credenciales", 5000);
      } else {
        setOtpError(true);
        setOtpIntentos(n);
      }
    }
  };

  // reenviarOtp: genera y "envía" un OTP nuevo por toast (11 s). No actúa fuera del
  // paso 1 o sin empresa pendiente. Port de reenviarOtp (fuente 1310-1316).
  const reenviarOtp = () => {
    if (paso !== 1 || !pendiente) return;
    const otp = gen6();
    setOtpCode(otp);
    setOtpInput("");
    setOtpError(false);
    avisar("Nuevo código para " + EMPRESAS[pendiente].nombre + ": " + otp, 11000);
  };

  // volverCreds: regresa del OTP a credenciales, descartando el código pendiente.
  // Port de volverCreds (fuente 1317).
  const volverCreds = () => {
    setPaso(0);
    setPendiente(null);
    setOtpCode(null);
    setOtpInput("");
    setOtpError(false);
  };

  // salirEmpresa: cierre de sesión manual desde el panel. Port de salirEmpresa (1318).
  const salirEmpresa = () => cerrarSesionEmp("Sesión cerrada correctamente");

  // togglePrivado: alterna el modo privacidad (enmascara nombres/direcciones).
  // Port de togglePrivado (fuente 1357).
  const togglePrivado = () => setPrivado((v) => !v);

  // limpiarFiltros: restablece todos los filtros a su valor por defecto (menos la
  // privacidad, igual que la fuente) y cierra la fila abierta. Port de limpiarFiltros
  // (fuente 1363).
  const limpiarFiltros = () => {
    setFiltro("TODOS");
    setQ("");
    setFDist("TODOS");
    setFFranja("TODAS");
    setFOrden("hora");
    setAbierta(null);
  };

  // --- Derivados de filtrado (equivalente a la rama empresa de renderVals) ---
  const empMeta = empresa ? EMPRESAS[empresa] : null; // meta (nombre/inicial) de la sesión
  const empBloq = bloqueoHasta > ahora; // ¿acceso bloqueado ahora mismo? (usa el reloj)

  // todos: filas de la empresa normalizadas a objetos. useMemo para no rehacerlas en
  // cada render/tic. Port del map de ROWS (fuente 1118-1120).
  const todos = useMemo(
    () =>
      (empresa ? FILAS[empresa] : []).map((t) => ({
        cod: t[0], cliente: t[1], dir: t[2], dist: t[3], estado: t[4], h: t[5], extra: t[6] || "",
      })),
    [empresa]
  );

  // contadores: nº de pedidos por estado + incidencias (OBSERVADO ∪ REPROGRAMADO).
  // useMemo dependiente solo de `todos`. Port de nDe/inc (fuente 1121-1122).
  const { nDe, inc } = useMemo(() => {
    const cuenta = (e) => todos.filter((r) => r.estado === e).length;
    return { nDe: cuenta, inc: cuenta("OBSERVADO") + cuenta("REPROGRAMADO") };
  }, [todos]);

  // distritos: lista única y ordenada de distritos para el select. Port de distOpts
  // (fuente 1349).
  const distritos = useMemo(() => Array.from(new Set(todos.map((r) => r.dist))).sort(), [todos]);

  // filtrados: aplica filtro de estado (INCIDENCIA = OBSERVADO ∪ REPROGRAMADO), distrito,
  // franja (MAÑANA h<12 / TARDE 12≤h≠99 / PORSALIR h===99), búsqueda libre y orden
  // (hora/cod/cliente/dist). useMemo con todas las dependencias de filtro. Port del
  // filter+sort de renderVals (fuente 1123-1140).
  const filtrados = useMemo(() => {
    const t = q.trim().toLowerCase();
    const base = todos.filter(
      (r) =>
        (filtro === "TODOS" ||
          (filtro === "INCIDENCIA" ? r.estado === "OBSERVADO" || r.estado === "REPROGRAMADO" : r.estado === filtro)) &&
        (fDist === "TODOS" || r.dist === fDist) &&
        (fFranja === "TODAS" ||
          (fFranja === "MANANA" && horaNum(r.h) < 12) ||
          (fFranja === "TARDE" && horaNum(r.h) >= 12 && horaNum(r.h) !== 99) ||
          (fFranja === "PORSALIR" && horaNum(r.h) === 99)) &&
        (!t || (r.cod + " " + r.cliente + " " + r.dist + " " + r.dir).toLowerCase().includes(t))
    );
    return base.slice().sort((a, b) => {
      if (fOrden === "hora") return horaNum(a.h) - horaNum(b.h);
      const ka = fOrden === "cod" ? a.cod : fOrden === "cliente" ? a.cliente : a.dist;
      const kb = fOrden === "cod" ? b.cod : fOrden === "cliente" ? b.cliente : b.dist;
      return ka.localeCompare(kb);
    });
  }, [todos, filtro, fDist, fFranja, fOrden, q]);

  // ¿hay algún filtro/búsqueda activo? (para mostrar "Limpiar filtros"). El orden por
  // hora es el default, así que no cuenta salvo que cambie. Port de filtrosActivos
  // (fuente 1144).
  const filtrosActivos = filtro !== "TODOS" || fDist !== "TODOS" || fFranja !== "TODAS" || fOrden !== "hora" || !!q.trim();

  // segRest / sesionTxt: segundos restantes de sesión y su formato "M:SS" a partir del
  // reloj `ahora` (nunca Date.now() en render). Port de segRest/sesionTxt (1145, 1319).
  const segRest = sesionFin ? Math.max(0, Math.floor((sesionFin - ahora) / 1000)) : 0;
  const sesionTxt = Math.floor(segRest / 60) + ":" + String(segRest % 60).padStart(2, "0");

  // Chips demo de la fuente (fuente 1287).
  const chipsEmp = ["RIPLEY-24", "FALABELLA-24", "ZARA-24"];

  // KPIs clicables: cada uno filtra la tabla por su estado al pulsarse. Port de kpis
  // (fuente 1327-1332).
  const kpis = empresa
    ? [
        { n: "Pedidos de hoy", v: todos.length, color: "#0f2b4a", f: "TODOS" },
        { n: "Entregados", v: nDe("ENTREGADO"), color: "#1e7a43", f: "ENTREGADO" },
        { n: "En ruta", v: nDe("EN_RUTA"), color: "#1b5fb3", f: "EN_RUTA" },
        { n: "Incidencias", v: inc, color: "#b35c12", f: "INCIDENCIA" },
      ]
    : [];

  // Avance del día: % de entregados + su resumen textual. Port de empPct/empResumen
  // (fuente 1333-1334).
  const empPct = todos.length ? Math.round((nDe("ENTREGADO") / todos.length) * 100) + "%" : "0%";
  const empResumen =
    nDe("ENTREGADO") + " entregados · " + nDe("EN_RUTA") + " en ruta · " + nDe("POR_SALIR") + " por salir" +
    (inc ? " · " + inc + " con incidencia" : "");

  // Botones-filtro de estado: "Todos" + los estados con >0 pedidos (según ORDEN),
  // con el nombre capitalizado desde ESTADOS[e].tx. Port de filtros (fuente 1335-1346).
  const filtros = empresa
    ? [{ id: "TODOS", n: "Todos", c: todos.length }].concat(
        ORDEN.filter((e) => nDe(e) > 0).map((e) => ({
          id: e, c: nDe(e), n: ESTADOS[e].tx.charAt(0) + ESTADOS[e].tx.slice(1).toLowerCase(),
        }))
      )
    : [];

  return (
    <section
      data-psec="1"
      style={{ maxWidth: 1140, margin: "0 auto", padding: "26px 24px 8px", width: "100%", boxSizing: "border-box", animation: "aparecer .45s ease both" }}
    >
      {/* Paso 0: credenciales */}
      {paso === 0 && (
        <Credenciales
          codEmp={codEmp}
          claveEmp={claveEmp}
          onCodEmp={onCodEmp}
          onClaveEmp={onClaveEmp}
          onCreds={onCreds}
          cargando={cargando}
          empBloq={empBloq}
          bloqueoHasta={bloqueoHasta}
          ahora={ahora}
          error={error}
          intentos={intentos}
          chipsEmp={chipsEmp}
          usarChip={usarChip}
        />
      )}

      {/* Paso 1: verificación en dos pasos (OTP) */}
      {paso === 1 && (
        <VerificacionOtp
          empPendNombre={pendiente && EMPRESAS[pendiente] ? EMPRESAS[pendiente].nombre : ""}
          otpInput={otpInput}
          onOtpInput={onOtpInput}
          onOtp={onOtp}
          otpError={otpError}
          reenviarOtp={reenviarOtp}
          volverCreds={volverCreds}
        />
      )}

      {/* Paso 2: panel corporativo */}
      {paso === 2 && !!empresa && (
        <div style={{ animation: "aparecer .5s ease both" }}>
          {/* Header: avatar + nombre + "Pedidos de hoy" + EN VIVO + sesión + cerrar */}
          <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            <span style={{ flex: "none", width: 48, height: 48, borderRadius: 14, background: "#0f2b4a", color: "#fff", display: "grid", placeItems: "center", fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: 19 }}>
              {empMeta ? empMeta.ini : ""}
            </span>
            <div style={{ flex: 1, minWidth: 180 }}>
              <h2 style={{ margin: 0, fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: 23 }}>{empMeta ? empMeta.nombre : ""}</h2>
              <p style={{ margin: "2px 0 0", fontSize: 13, color: "#7288a0" }}>Pedidos de hoy · {hoyTxt}</p>
            </div>
            <span style={{ background: "#e3f2e8", color: "#1e7a43", fontSize: 11, fontWeight: 700, letterSpacing: ".06em", padding: "5px 12px", borderRadius: 99, animation: "latido 1.9s ease-in-out infinite" }}>EN VIVO</span>
            <span style={{ display: "inline-flex", alignItems: "center", gap: 8, border: "1.5px solid rgba(15,43,74,.14)", background: "#fff", borderRadius: 99, padding: "7px 14px", fontSize: 12, fontWeight: 600, color: "#3d5570" }}>
              <span style={{ width: 7, height: 7, borderRadius: 99, background: "#22a35e", flex: "none", animation: "latido 2s ease-in-out infinite" }} />
              <span>Sesión expira en {sesionTxt}</span>
            </span>
            <button
              type="button"
              onClick={salirEmpresa}
              className="ptl-btn-salir-emp"
              style={{ border: "1.5px solid rgba(15,43,74,.16)", background: "#fff", color: "#3d5570", fontFamily: "Inter, sans-serif", fontSize: 13, fontWeight: 600, padding: "9px 18px", borderRadius: 99, cursor: "pointer", transition: "border-color .2s ease, color .2s ease" }}
            >
              Cerrar sesión
            </button>
          </div>

          {/* KPIs clicables */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(150px,1fr))", gap: 12, margin: "18px 0 0" }}>
            {kpis.map((k) => (
              <button
                key={k.n}
                type="button"
                onClick={() => {
                  setFiltro(k.f);
                  setAbierta(null);
                }}
                className="ptl-kpi-emp"
                style={{ textAlign: "left", cursor: "pointer", fontFamily: "Inter, sans-serif", background: "#fff", border: "1px solid rgba(15,43,74,.09)", borderRadius: 18, padding: "18px 20px", transition: "border-color .2s ease" }}
              >
                <span style={{ display: "block", fontSize: 12.5, fontWeight: 600, color: "#7288a0" }}>{k.n}</span>
                <span data-count={k.v} style={{ display: "block", marginTop: 4, fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: 31, lineHeight: 1, color: k.color }}>{k.v}</span>
              </button>
            ))}
          </div>

          {/* Avance del día */}
          <div data-ppanel="1" style={{ margin: "12px 0 0", background: "#fff", border: "1px solid rgba(15,43,74,.09)", borderRadius: 18, padding: "18px 20px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
              <span style={{ fontSize: 13, fontWeight: 700, color: "#0f2b4a" }}>Avance del día</span>
              <span style={{ fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: 19, color: "#22a35e" }}>{empPct}</span>
            </div>
            <div style={{ margin: "10px 0 0", height: 8, borderRadius: 99, background: "#e8f0f8", overflow: "hidden" }}>
              <div style={{ height: "100%", borderRadius: 99, width: empPct, background: "linear-gradient(90deg,#2679d8,#22a35e)", transition: "width 1.2s ease .1s" }} />
            </div>
            <p style={{ margin: "8px 0 0", fontSize: 12.5, color: "#7288a0" }}>{empResumen} — se actualiza en vivo</p>
          </div>

          {/* Fila 1 de filtros: botones de estado + búsqueda */}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", margin: "18px 0 0", alignItems: "center" }}>
            {filtros.map((f) => (
              <button
                key={f.id}
                type="button"
                onClick={() => {
                  setFiltro(f.id);
                  setAbierta(null);
                }}
                style={{
                  border: `1.5px solid ${filtro === f.id ? "#0f2b4a" : "rgba(15,43,74,.14)"}`,
                  background: filtro === f.id ? "#0f2b4a" : "#fff",
                  color: filtro === f.id ? "#fff" : "#3d5570",
                  fontFamily: "Inter, sans-serif", fontSize: 12.5, fontWeight: 600, padding: "8px 14px", borderRadius: 99, cursor: "pointer",
                  transition: "background .2s ease, color .2s ease, border-color .2s ease",
                }}
              >
                {f.n} · {f.c}
              </button>
            ))}
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              aria-label="Buscar pedido"
              placeholder="Buscar código, cliente, dirección o distrito…"
              className="ptl-buscar-emp"
              style={{ marginLeft: "auto", flex: 1, minWidth: 200, maxWidth: 300, boxSizing: "border-box", fontFamily: "Inter, sans-serif", fontSize: 13.5, padding: "10px 15px", border: "1.5px solid rgba(15,43,74,.14)", borderRadius: 99, background: "#fff", color: "#0f2b4a", outline: "none" }}
            />
          </div>

          {/* Fila 2 de filtros: selects + privacidad + limpiar + contador */}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", margin: "10px 0 0", alignItems: "center" }}>
            <select
              value={fDist}
              onChange={(e) => {
                setFDist(e.target.value);
                setAbierta(null);
              }}
              aria-label="Filtrar por distrito"
              className="ptl-select-emp"
              style={SELECT_ESTILO}
            >
              <option value="TODOS">Distrito: todos</option>
              {distritos.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
            <select
              value={fFranja}
              onChange={(e) => {
                setFFranja(e.target.value);
                setAbierta(null);
              }}
              aria-label="Filtrar por franja horaria"
              className="ptl-select-emp"
              style={SELECT_ESTILO}
            >
              <option value="TODAS">Franja: todas</option>
              <option value="MANANA">Mañana (antes de 12 pm)</option>
              <option value="TARDE">Tarde (12 pm en adelante)</option>
              <option value="PORSALIR">Aún por salir</option>
            </select>
            <select
              value={fOrden}
              onChange={(e) => setFOrden(e.target.value)}
              aria-label="Ordenar"
              className="ptl-select-emp"
              style={SELECT_ESTILO}
            >
              <option value="hora">Ordenar: hora</option>
              <option value="cod">Ordenar: código</option>
              <option value="cliente">Ordenar: cliente</option>
              <option value="dist">Ordenar: distrito</option>
            </select>
            <button
              type="button"
              onClick={togglePrivado}
              style={{
                border: `1.5px solid ${privado ? "#0f2b4a" : "rgba(15,43,74,.14)"}`,
                background: privado ? "#0f2b4a" : "#fff",
                color: privado ? "#fff" : "#3d5570",
                fontFamily: "Inter, sans-serif", fontSize: 12.5, fontWeight: 600, padding: "9px 14px", borderRadius: 99, cursor: "pointer",
                transition: "background .25s ease, color .25s ease, border-color .25s ease",
              }}
            >
              {privado ? "Datos ocultos ●" : "Ocultar datos"}
            </button>
            {filtrosActivos && (
              <button
                type="button"
                onClick={limpiarFiltros}
                className="ptl-limpiar-emp"
                style={{ border: 0, background: "none", cursor: "pointer", fontFamily: "Inter, sans-serif", fontSize: 12.5, fontWeight: 600, color: "#c8362b", padding: "9px 6px", animation: "aparecer .3s ease both" }}
              >
                Limpiar filtros ✕
              </button>
            )}
            <span style={{ marginLeft: "auto", fontSize: 12, color: "#8ba0b6" }}>Mostrando {filtrados.length} de {todos.length}</span>
          </div>

          {/* Tabla de pedidos */}
          <div style={{ margin: "12px 0 0", background: "#fff", border: "1px solid rgba(15,43,74,.09)", borderRadius: 18, overflow: "hidden" }}>
            <div id="rowHead" style={{ display: "grid", gridTemplateColumns: "112px 1fr 128px 128px 64px", gap: 12, padding: "12px 18px", fontSize: 11, fontWeight: 700, letterSpacing: ".08em", color: "#7288a0", textTransform: "uppercase", background: "#f8fbfe" }}>
              <span>Código</span>
              <span>Cliente</span>
              <span>Distrito</span>
              <span>Estado</span>
              <span style={{ textAlign: "right" }}>Hora</span>
            </div>
            {filtrados.map((r) => (
              <FilaPedido
                key={r.cod}
                r={r}
                privado={privado}
                abierta={abierta}
                setAbierta={setAbierta}
                empNombre={empMeta ? empMeta.nombre : "la tienda"}
              />
            ))}
            {filtrados.length === 0 && (
              <p style={{ margin: 0, padding: "26px 18px", textAlign: "center", fontSize: 13.5, color: "#7288a0", borderTop: "1px solid rgba(15,43,74,.06)" }}>
                Ningún pedido coincide con esos filtros o búsqueda.
              </p>
            )}
          </div>

          {/* Aviso de auditoría / privacidad */}
          <p style={{ margin: "12px 0 0", fontSize: 12, lineHeight: 1.6, color: "#8ba0b6", display: "flex", gap: 8, alignItems: "flex-start" }}>
            <span style={{ flex: "none", width: 7, height: 7, borderRadius: 99, background: "#22a35e", marginTop: 5, animation: "latido 2.2s ease-in-out infinite" }} />
            <span>Acceso auditado · Los datos de los destinatarios se muestran únicamente a {empMeta ? empMeta.nombre : ""} · Active «Ocultar datos» si comparte pantalla · El histórico y los reportes completos viven en GeoTrack.</span>
          </p>
        </div>
      )}
    </section>
  );
}

// Estilo compartido de los tres <select> de filtros (flecha CSS, píldora). Extraído
// para no repetir el objeto de estilo en cada select. Port del inline del mockup
// (fuente 826, 832, 838).
const SELECT_ESTILO = {
  fontFamily: "Inter, sans-serif",
  fontSize: 12.5,
  fontWeight: 600,
  color: "#3d5570",
  padding: "9px 30px 9px 14px",
  border: "1.5px solid rgba(15,43,74,.14)",
  borderRadius: 99,
  background: "#fff",
  cursor: "pointer",
  outline: "none",
  backgroundImage: "linear-gradient(45deg,transparent 50%,#7288a0 50%),linear-gradient(135deg,#7288a0 50%,transparent 50%)",
  backgroundPosition: "calc(100% - 17px) 55%,calc(100% - 12px) 55%",
  backgroundSize: "5px 5px",
  backgroundRepeat: "no-repeat",
};

// ----------------------------------------------------------------------------
// Credenciales: paso 0 del flujo corporativo. Panel con el título, el aviso de bloqueo
// temporal (si aplica), el formulario código+clave, el error de credenciales (con
// sacudir), los chips demo que autocompletan y el aviso de conexión cifrada.
// Input: valores/handlers de los inputs, estado de carga/bloqueo/error/intentos, el
// reloj `ahora` (para el countdown del bloqueo) y los chips demo.
// ----------------------------------------------------------------------------
function Credenciales({ codEmp, claveEmp, onCodEmp, onClaveEmp, onCreds, cargando, empBloq, bloqueoHasta, ahora, error, intentos, chipsEmp, usarChip }) {
  const bloqueoTxt = "Demasiados intentos fallidos. Por seguridad, el acceso está pausado " + Math.ceil(Math.max(0, bloqueoHasta - ahora) / 1000) + " s.";
  const intentosTxt = String(Math.max(0, 3 - intentos));

  return (
    <div data-ppanel="1" style={{ maxWidth: 560, margin: "0 auto", background: "#fff", border: "1px solid rgba(15,43,74,.1)", borderRadius: 22, padding: "30px 28px", boxShadow: "0 16px 40px rgba(15,43,74,.08)" }}>
      <div style={{ display: "flex", gap: 14, alignItems: "center" }}>
        {/* Icono de candado */}
        <span aria-hidden="true" style={{ flex: "none", width: 44, height: 44, borderRadius: 14, background: "#eaf3fc", display: "grid", placeItems: "center" }}>
          <span style={{ width: 15, height: 12, borderRadius: 3, background: "#1b5fb3", position: "relative" }}>
            <span style={{ position: "absolute", top: -7, left: 2.5, width: 10, height: 9, border: "2.5px solid #1b5fb3", borderBottom: 0, borderRadius: "6px 6px 0 0", boxSizing: "border-box" }} />
          </span>
        </span>
        <div>
          <p style={{ margin: 0, fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: 21 }}>Panel corporativo</p>
          <p style={{ margin: "3px 0 0", fontSize: 12.5, color: "#7288a0" }}>Acceso con credenciales + verificación en dos pasos</p>
        </div>
      </div>

      {empBloq && (
        <div style={{ margin: "18px 0 0", background: "#fdeedd", border: "1px solid rgba(217,122,31,.35)", borderRadius: 12, padding: "13px 16px", fontSize: 13.5, fontWeight: 600, color: "#b35c12", animation: "aparecer .3s ease both" }}>
          {bloqueoTxt}
        </div>
      )}

      {!empBloq && (
        <>
          <form onSubmit={onCreds} style={{ margin: "18px 0 0", display: "grid", gap: 10 }}>
            <input
              value={codEmp}
              onChange={onCodEmp}
              aria-label="Código de empresa"
              placeholder="Código de empresa · ej. RIPLEY-24"
              className="ptl-input-emp"
              style={{ boxSizing: "border-box", fontFamily: "Inter, sans-serif", fontSize: 14.5, padding: "13px 15px", border: "1.5px solid rgba(15,43,74,.16)", borderRadius: 12, background: "#f8fafc", color: "#0f2b4a", outline: "none" }}
            />
            <input
              type="password"
              value={claveEmp}
              onChange={onClaveEmp}
              aria-label="Clave de acceso"
              placeholder="Clave de acceso"
              className="ptl-input-emp"
              style={{ boxSizing: "border-box", fontFamily: "Inter, sans-serif", fontSize: 14.5, padding: "13px 15px", border: "1.5px solid rgba(15,43,74,.16)", borderRadius: 12, background: "#f8fafc", color: "#0f2b4a", outline: "none" }}
            />
            <button
              type="submit"
              className="ptl-btn-creds"
              style={{ border: 0, cursor: "pointer", background: "#2679d8", color: "#fff", fontFamily: "Inter, sans-serif", fontWeight: 600, fontSize: 14.5, padding: "13px 22px", borderRadius: 12, transition: "background .2s ease" }}
            >
              {cargando ? "Verificando…" : "Continuar"}
            </button>
          </form>
          {error && (
            <p style={{ margin: "12px 0 0", fontSize: 13, fontWeight: 600, color: "#c8362b", animation: "sacudir .4s ease both" }}>
              Credenciales incorrectas · le quedan {intentosTxt} intentos antes del bloqueo temporal
            </p>
          )}
        </>
      )}

      <div style={{ margin: "16px 0 0", display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
        <span style={{ fontSize: 12, color: "#7288a0" }}>Demostración:</span>
        {chipsEmp.map((c) => (
          <button
            key={c}
            type="button"
            onClick={() => usarChip(c)}
            className="ptl-chip-emp"
            style={{ border: "1px solid rgba(38,121,216,.3)", background: "#f2f7fc", color: "#1b5fb3", fontFamily: "Inter, sans-serif", fontSize: 12.5, fontWeight: 600, padding: "7px 13px", borderRadius: 99, cursor: "pointer", transition: "background .2s ease, border-color .2s ease" }}
          >
            {c}
          </button>
        ))}
        <span style={{ fontSize: 11.5, color: "#8ba0b6" }}>clave demo: DEMO-2026</span>
      </div>

      <p style={{ margin: "18px 0 0", fontSize: 12, lineHeight: 1.6, color: "#8ba0b6", display: "flex", gap: 8, alignItems: "flex-start" }}>
        <span style={{ flex: "none", width: 7, height: 7, borderRadius: 99, background: "#22a35e", marginTop: 5, animation: "latido 2.2s ease-in-out infinite" }} />
        Conexión cifrada. Cada acceso queda registrado y auditado. Las credenciales las entrega su ejecutivo SAVA.
      </p>
    </div>
  );
}

// ----------------------------------------------------------------------------
// VerificacionOtp: paso 1 del flujo. Panel con el mensaje (con el nombre de la empresa
// pendiente), el input de OTP de 6 dígitos, el botón de validar, el error (con sacudir)
// y las acciones de reenviar código / volver. Input: nombre de la empresa pendiente,
// valor/handlers del OTP, bandera de error y los handlers de reenviar/volver.
// ----------------------------------------------------------------------------
function VerificacionOtp({ empPendNombre, otpInput, onOtpInput, onOtp, otpError, reenviarOtp, volverCreds }) {
  return (
    <div data-ppanel="1" style={{ maxWidth: 560, margin: "0 auto", background: "#fff", border: "1.5px solid rgba(38,121,216,.3)", borderRadius: 22, padding: "30px 28px", boxShadow: "0 16px 40px rgba(15,43,74,.08)", animation: "aparecer .4s ease both" }}>
      <p style={{ margin: 0, fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: 21 }}>Verificación en dos pasos</p>
      <p style={{ margin: "8px 0 0", fontSize: 14, lineHeight: 1.6, color: "#4f6580" }}>
        Enviamos un código de 6 dígitos al correo del administrador de <strong>{empPendNombre}</strong>. En esta demo, el código llega como notificación aquí mismo.
      </p>
      <form onSubmit={onOtp} style={{ margin: "18px 0 0", display: "flex", gap: 10, flexWrap: "wrap" }}>
        <input
          value={otpInput}
          onChange={onOtpInput}
          inputMode="numeric"
          maxLength={6}
          aria-label="Código de verificación"
          placeholder="Código de 6 dígitos"
          className="ptl-input-otp"
          style={{ flex: 1, minWidth: 180, boxSizing: "border-box", fontFamily: "Inter, sans-serif", fontSize: 16, letterSpacing: ".2em", padding: "13px 15px", border: "1.5px solid rgba(15,43,74,.16)", borderRadius: 12, background: "#f8fafc", color: "#0f2b4a", outline: "none" }}
        />
        <button
          type="submit"
          className="ptl-btn-otp"
          style={{ border: 0, cursor: "pointer", background: "#2679d8", color: "#fff", fontFamily: "Inter, sans-serif", fontWeight: 600, fontSize: 14.5, padding: "13px 22px", borderRadius: 12, transition: "background .2s ease" }}
        >
          Validar código
        </button>
      </form>
      {otpError && (
        <p style={{ margin: "12px 0 0", fontSize: 13, fontWeight: 600, color: "#c8362b", animation: "sacudir .4s ease both" }}>
          Código incorrecto · verifique la notificación y vuelva a intentar
        </p>
      )}
      <div style={{ margin: "16px 0 0", display: "flex", gap: "8px 18px", flexWrap: "wrap", alignItems: "center" }}>
        <button
          type="button"
          onClick={reenviarOtp}
          className="ptl-link-reenviar"
          style={{ border: 0, background: "none", cursor: "pointer", padding: 0, fontFamily: "Inter, sans-serif", fontSize: 13, fontWeight: 600, color: "#2679d8", textDecoration: "underline" }}
        >
          Reenviar código
        </button>
        <button
          type="button"
          onClick={volverCreds}
          className="ptl-link-volver-creds"
          style={{ border: 0, background: "none", cursor: "pointer", padding: 0, fontFamily: "Inter, sans-serif", fontSize: 13, fontWeight: 600, color: "#7288a0", textDecoration: "underline" }}
        >
          ← Volver
        </button>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------------
// FilaPedido: una fila de la tabla de pedidos, clicable, que al abrirse despliega la
// mini-línea de tiempo del pedido (detalleDe) + la dirección completa (o el aviso de
// datos ocultos si la privacidad está activa). Aplica el enmascarado de nombre y
// dirección cuando `privado`. Los atributos data-* ([data-row]/[data-c1]/[data-c2]/
// [data-cd]/[data-badge]) los usan las media queries del portal para la vista ≤680px.
// Input: fila normalizada `r`, bandera `privado`, código de la fila abierta `abierta`,
// el setter `setAbierta` y el nombre de la empresa `empNombre` (para la línea de tiempo).
// ----------------------------------------------------------------------------
function FilaPedido({ r, privado, abierta, setAbierta, empNombre }) {
  const m = ESTADOS[r.estado];
  const abierto = abierta === r.cod;
  const cliente = privado ? maskN(r.cliente) : r.cliente;
  const dir = privado ? maskD(r.dir) : r.dir;
  const dirFull = privado
    ? "Datos personales ocultos — desactive «Ocultar datos» para ver la dirección completa."
    : r.dir + ", " + r.dist + (r.extra ? " — " + r.extra : "");
  const detalle = detalleDe(r, empNombre);

  return (
    <div style={{ borderTop: "1px solid rgba(15,43,74,.06)" }}>
      <button
        type="button"
        data-row="1"
        onClick={() => setAbierta(abierto ? null : r.cod)}
        className="ptl-fila-emp"
        style={{ width: "100%", textAlign: "left", fontFamily: "Inter, sans-serif", display: "grid", gridTemplateColumns: "112px 1fr 128px 128px 64px", gap: 12, alignItems: "center", padding: "13px 18px", border: 0, background: abierto ? "#f8fbfe" : "#fff", cursor: "pointer", boxSizing: "border-box", transition: "background .2s ease" }}
      >
        <span data-c1="1" style={{ fontWeight: 700, fontSize: 13.5, color: "#0f2b4a" }}>{r.cod}</span>
        <span data-c2="1" style={{ fontSize: 13.5, color: "#3d5570", minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {cliente} <span data-cd="1" style={{ color: "#8ba0b6" }}>· {dir}</span>
        </span>
        <span data-cd="1" style={{ fontSize: 13, color: "#4f6580" }}>{r.dist}</span>
        <span data-badge="1">
          <span style={{ background: m.bg, color: m.fg, fontSize: 10.5, fontWeight: 700, letterSpacing: ".05em", padding: "5px 11px", borderRadius: 99, whiteSpace: "nowrap" }}>{m.tx}</span>
        </span>
        <span data-cd="1" style={{ fontSize: 12.5, fontWeight: 600, color: "#8ba0b6", textAlign: "right" }}>{r.h}</span>
      </button>
      {abierto && (
        <div style={{ padding: "2px 18px 16px", background: "#f8fbfe", animation: "aparecer .3s ease both" }}>
          <p style={{ margin: "0 0 10px", fontSize: 12.5, color: "#4f6580" }}>{dirFull}</p>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {detalle.map((dv, i) => (
              <span key={i} style={{ display: "inline-flex", gap: 8, alignItems: "center", background: "#fff", border: "1px solid rgba(15,43,74,.1)", borderRadius: 99, padding: "7px 13px", fontSize: 12, color: "#3d5570" }}>
                <span style={{ width: 7, height: 7, borderRadius: 99, background: dv.color, flex: "none" }} />
                <span style={{ fontWeight: 700, color: "#7288a0" }}>{dv.h}</span> {dv.t}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
