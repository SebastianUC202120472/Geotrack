import { useEffect, useState } from "react";
import { RefreshCw, MapPin, Wifi, WifiOff, Wrench, Search, ChevronLeft, ChevronRight, Route as RouteIcon, KeyRound, Truck } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import EmptyState from "../components/ui/EmptyState";
import LiveBadge from "../components/ui/LiveBadge";
import Button from "../components/ui/Button";
import { EstadoBadge } from "../components/ui/Badge";
import MapaFlota from "../components/MapaFlota";
import useCountUp from "../hooks/useCountUp";
import { obtenerUbicacionesFlota } from "../services/api";
import { haceCuanto } from "../utils/formatoFecha";

const REFRESCO_MS = 15000; // intervalo de polling en ms
const POR_PAGINA = 4; // conductores visibles en la lista; el resto se ve con las flechas

// Colores por conductor; se comparten con sus marcadores en el mapa.
const COLORES = ["#2563EB", "#DC2626", "#059669", "#D97706", "#7C3AED", "#DB2777", "#0891B2", "#65A30D"];

// Colores del icono de cada indicador de la franja inferior.
const TONOS = {
  brand: "bg-brand-50 text-brand-600",
  info: "bg-info-soft text-info-strong",
  success: "bg-success-soft text-success-strong",
  warning: "bg-warning-soft text-warning-strong",
  danger: "bg-danger-soft text-danger-strong",
};

// Normaliza un texto para buscar sin importar mayúsculas ni tildes. Recibe el texto.
const normalizar = (t) => String(t ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

// Dice si alguno de los campos contiene lo buscado. Recibe la búsqueda y la lista de campos.
const coincide = (busqueda, campos) => !busqueda || campos.some((c) => normalizar(c).includes(busqueda));

// Seguimiento en vivo de la página de Conductores: cabecera con acciones, lista de conductores
// (en ruta o todos, con búsqueda y de 4 en 4), mapa de flota y franja con los indicadores.
// Recibe titulo, acciones (botones extra junto a Actualizar), todos (conductores
// registrados), onAbrirConductor (abre la ficha de uno), indicadores (los del registro, que van
// primero en la franja) y children (avisos entre la cabecera y la lista).
export default function SeguimientoConductores({ titulo, acciones, todos = [], onAbrirConductor, indicadores = [], children }) {
  const [ubicaciones, setUbicaciones] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [seleccionado, setSeleccionado] = useState(null); // conductor_id seleccionado; null = todos
  const [filtroCapa, setFiltroCapa] = useState("TODO");   // TODO | CONDUCTORES | PEDIDOS
  const [lista, setLista] = useState("RUTA");             // RUTA (en ruta) | TODOS (registrados)
  const [busqueda, setBusqueda] = useState("");
  const [pagina, setPagina] = useState(0);

  // Recarga manualmente los datos del mapa. Sin input.
  const actualizar = () => {
    setCargando(true);
    obtenerUbicacionesFlota()
      .then(setUbicaciones)
      .catch((err) => console.error("No se pudo cargar el mapa:", err.message))
      .finally(() => setCargando(false));
  };

  // Carga inicial y polling cada 15 s; setState solo en callbacks para evitar warnings.
  useEffect(() => {
    let activo = true;
    const traer = () =>
      obtenerUbicacionesFlota()
        .then((u) => activo && setUbicaciones(u))
        .catch(() => {})
        .finally(() => activo && setCargando(false));
    traer();
    const id = setInterval(traer, REFRESCO_MS);
    return () => {
      activo = false;
      clearInterval(id);
    };
  }, []);

  // Cambia entre "En ruta" y "Todos" y vuelve a la primera página. Recibe el modo.
  const cambiarLista = (modo) => { setLista(modo); setPagina(0); };
  // Actualiza la búsqueda y vuelve a la primera página. Recibe el evento del input.
  const buscar = (e) => { setBusqueda(e.target.value); setPagina(0); };

  // Métricas derivadas de los datos cargados.
  const enRuta = ubicaciones.length;
  const enLinea = ubicaciones.filter((c) => c.en_linea).length;
  const pendientesDe = (c) => c.paradas?.filter((p) => (p.estado || "PENDIENTE") === "PENDIENTE").length ?? 0;
  const totalParadas = ubicaciones.reduce((acc, c) => acc + pendientesDe(c), 0);
  const pausados = ubicaciones.filter((u) => u.pausado).length;

  const conductores = ubicaciones.map((c, i) => ({ ...c, _color: COLORES[i % COLORES.length] }));
  // Si hay seleccionado, el mapa muestra solo ese conductor.
  const conductoresVisibles = seleccionado != null ? conductores.filter((c) => c.conductor_id === seleccionado) : conductores;

  // Lista filtrada por la búsqueda y la página que se ve.
  const q = normalizar(busqueda.trim());
  const filtrados = lista === "RUTA"
    ? conductores.filter((c) => coincide(q, [c.conductor, c.placa, c.ruta]))
    : todos.filter((c) => coincide(q, [c.nombre, c.codigo, c.vehiculo?.placa, c.correo, c.dni, c.telefono]));
  const totalPaginas = Math.max(1, Math.ceil(filtrados.length / POR_PAGINA));
  const paginaActual = Math.min(pagina, totalPaginas - 1);
  const visibles = filtrados.slice(paginaActual * POR_PAGINA, (paginaActual + 1) * POR_PAGINA);

  const franja = [
    ...indicadores,
    { label: "En ruta", value: enRuta, icon: RouteIcon, tone: "brand" },
    { label: "En línea", value: enLinea, icon: Wifi, tone: "success" },
    { label: "Sin señal", value: enRuta - enLinea, icon: WifiOff, tone: enRuta - enLinea > 0 ? "warning" : "info" },
    { label: "Paradas pendientes", value: totalParadas, icon: MapPin, tone: "info" },
    { label: "Pausados", value: pausados, icon: Wrench, tone: pausados > 0 ? "danger" : "info" },
  ];

  return (
    <div className="space-y-6">
      <div className="animate-fade-up">
        <PageHeader titulo={titulo}>
          {/* Selector de capa del mapa */}
          <div className="flex rounded-lg border border-slate-200 bg-white p-0.5 text-xs font-semibold" role="group" aria-label="Filtrar mapa">
            {[["TODO", "Todo"], ["CONDUCTORES", "Conductores"], ["PEDIDOS", "Pedidos"]].map(([valor, etiqueta]) => (
              <button
                key={valor}
                type="button"
                onClick={() => setFiltroCapa(valor)}
                className={`rounded-md px-2.5 py-1.5 transition-colors ${
                  filtroCapa === valor ? "bg-brand-600 text-white" : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                {etiqueta}
              </button>
            ))}
          </div>
          <LiveBadge tone="success">En vivo</LiveBadge>
          <Button variant="secondary" icon={RefreshCw} onClick={actualizar}>
            Actualizar
          </Button>
          {acciones}
        </PageHeader>
      </div>

      {children}

      <div className="flex flex-col gap-4 lg:flex-row animate-fade-up">
        {/* Lista de conductores: misma altura que el mapa */}
        <section className="flex w-full shrink-0 flex-col rounded-card border border-slate-200 bg-white shadow-card lg:h-[520px] lg:w-80">
          <header className="space-y-2.5 border-b border-slate-100 px-4 py-3">
            <div className="flex items-center gap-3">
              <h2 className="text-sm font-bold text-slate-900">Conductores</h2>
              <label className="relative min-w-0 flex-1">
                <Search size={15} className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="search"
                  value={busqueda}
                  onChange={buscar}
                  placeholder="Buscar…"
                  aria-label="Buscar conductor"
                  className="w-full rounded-lg border border-slate-200 bg-slate-50 py-1.5 pl-8 pr-2 text-sm text-slate-800 placeholder:text-slate-400 focus:border-brand-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-100"
                />
              </label>
            </div>
            <div className="flex items-center justify-between gap-2">
              <div className="flex rounded-lg bg-slate-100 p-0.5 text-xs font-semibold" role="group" aria-label="Qué conductores ver">
                {[["RUTA", `En ruta · ${enRuta}`], ["TODOS", `Todos · ${todos.length}`]].map(([valor, etiqueta]) => (
                  <button
                    key={valor}
                    type="button"
                    onClick={() => cambiarLista(valor)}
                    aria-pressed={lista === valor}
                    className={`rounded-md px-3 py-1 transition-colors ${
                      lista === valor ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-800"
                    }`}
                  >
                    {etiqueta}
                  </button>
                ))}
              </div>
              {lista === "RUTA" && seleccionado != null && (
                <button type="button" onClick={() => setSeleccionado(null)} className="text-xs font-semibold text-brand-600 hover:text-brand-700">
                  Ver todos en el mapa
                </button>
              )}
            </div>
          </header>

          <ul className="flex-1 divide-y divide-slate-100 overflow-y-auto">
            {visibles.length === 0 && (
              <li className="px-4 py-10 text-center text-sm text-slate-400">
                {q ? "Ningún conductor coincide con la búsqueda." : lista === "RUTA" ? "No hay conductores en ruta ahora mismo." : "Aún no hay conductores registrados."}
              </li>
            )}
            {lista === "RUTA"
              ? visibles.map((c) => (
                  <ItemEnRuta
                    key={c.conductor_id}
                    c={c}
                    pendientes={pendientesDe(c)}
                    activo={seleccionado === c.conductor_id}
                    onClick={() => setSeleccionado(seleccionado === c.conductor_id ? null : c.conductor_id)}
                  />
                ))
              : visibles.map((c) => <ItemRegistrado key={c.usuario_id} c={c} onClick={() => onAbrirConductor?.(c)} />)}
          </ul>

          {totalPaginas > 1 && (
            <footer className="flex items-center justify-between border-t border-slate-100 px-4 py-2">
              <button
                type="button"
                onClick={() => setPagina(paginaActual - 1)}
                disabled={paginaActual === 0}
                aria-label="Conductores anteriores"
                className="rounded-lg p-1.5 text-slate-600 transition-colors hover:bg-slate-100 disabled:opacity-30 disabled:hover:bg-transparent"
              >
                <ChevronLeft size={18} />
              </button>
              <span className="text-xs font-semibold text-slate-500 nums">
                {paginaActual * POR_PAGINA + 1}–{Math.min(filtrados.length, (paginaActual + 1) * POR_PAGINA)} de {filtrados.length}
              </span>
              <button
                type="button"
                onClick={() => setPagina(paginaActual + 1)}
                disabled={paginaActual >= totalPaginas - 1}
                aria-label="Conductores siguientes"
                className="rounded-lg p-1.5 text-slate-600 transition-colors hover:bg-slate-100 disabled:opacity-30 disabled:hover:bg-transparent"
              >
                <ChevronRight size={18} />
              </button>
            </footer>
          )}
        </section>

        <div className="min-w-0 flex-1">
          {cargando ? (
            <div className="flex h-[520px] items-center justify-center rounded-card border border-slate-200 bg-white text-sm text-slate-500 shadow-card">
              Cargando mapa…
            </div>
          ) : ubicaciones.length === 0 ? (
            <div className="flex h-[520px] items-center justify-center rounded-card border border-slate-200 bg-white shadow-card">
              <EmptyState
                icon={MapPin}
                title="Sin conductores en ruta"
                description="No hay conductores con ruta activa enviando su ubicación ahora mismo."
                action={<Button variant="secondary" icon={RefreshCw} onClick={actualizar}>Volver a intentar</Button>}
              />
            </div>
          ) : (
            <MapaFlota conductores={conductoresVisibles} seleccionado={seleccionado} mostrar={filtroCapa} />
          )}
        </div>
      </div>

      {/* Datos generales: todos los indicadores en una sola franja, con el mismo ancho */}
      <section
        aria-label="Datos generales de los conductores"
        className="grid grid-cols-3 overflow-hidden rounded-card border border-slate-200 bg-white shadow-card sm:grid-cols-3 xl:grid-cols-9 animate-fade-up"
      >
        {franja.map((k) => <Indicador key={k.label} {...k} />)}
      </section>
    </div>
  );
}

// Un indicador de la franja inferior: icono y valor animado arriba, etiqueta debajo (puede ocupar
// dos líneas para no cortarse). Recibe label, value, icon y tone.
function Indicador({ label, value, icon: Icon, tone = "brand" }) {
  const animado = useCountUp(value);
  return (
    <div className="-ml-px -mt-px flex min-w-0 flex-col gap-2 border-l border-t border-slate-100 px-4 py-3.5">
      <div className="flex items-center gap-2.5">
        <span className={`shrink-0 rounded-chip p-1.5 ${TONOS[tone] || TONOS.brand}`}>
          <Icon size={16} />
        </span>
        <p className="text-2xl font-bold leading-none text-slate-900 nums">{animado}</p>
      </div>
      <p className="text-[11px] font-semibold uppercase leading-tight tracking-wide text-slate-500">{label}</p>
    </div>
  );
}

// Fila de un conductor en ruta: color del mapa, placa, ruta, paradas, señal y avance. Recibe el
// conductor, sus paradas pendientes, si está seleccionado y el clic (lo enfoca en el mapa).
function ItemEnRuta({ c, pendientes, activo, onClick }) {
  return (
    <li>
      <button
        type="button"
        onClick={onClick}
        className={`flex w-full items-start gap-3 px-4 py-2 text-left transition-colors ${activo ? "bg-brand-50" : "hover:bg-slate-50"}`}
      >
        <span
          className={`mt-1 h-3 w-3 shrink-0 rounded-full border border-white shadow ${c.en_linea ? "live-dot" : ""}`}
          style={{ backgroundColor: c._color, opacity: c.en_linea ? 1 : 0.5 }}
          aria-hidden="true"
        />
        <div className="min-w-0 flex-1">
          <p className="flex items-center gap-1.5 text-sm font-semibold text-slate-900">
            <span className="truncate">{c.conductor || "Conductor"}</span>
            {c.placa && <span className="shrink-0 rounded-md bg-slate-100 px-1.5 py-0.5 text-[11px] font-semibold text-slate-600 nums">{c.placa}</span>}
            {c.pausado && (
              <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-danger-soft px-1.5 py-0.5 text-[11px] font-semibold text-danger-strong">
                <Wrench size={11} /> Pausado
              </span>
            )}
          </p>
          <p className="truncate text-xs text-slate-500">{c.ruta || "Sin ruta"}</p>
          <p className="mt-0.5 truncate text-xs text-slate-400">
            {pendientes} parada{pendientes !== 1 ? "s" : ""} pendiente{pendientes !== 1 ? "s" : ""} ·{" "}
            {c.en_linea ? "en línea" : c.actualizado_en ? `sin señal hace ${haceCuanto(c.actualizado_en).replace(/^hace /, "")}` : "sin señal"}
          </p>
          {c.total_paradas > 0 && (
            <div className="mt-1.5 flex items-center gap-2" title={`${c.gestionadas} de ${c.total_paradas} gestionadas`}>
              <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
                <span className="block h-full rounded-full bg-success" style={{ width: `${c.avance_porcentaje}%` }} />
              </span>
              <span className="text-[11px] font-semibold text-slate-600 nums">{c.gestionadas}/{c.total_paradas}</span>
            </div>
          )}
        </div>
      </button>
    </li>
  );
}

// Fila de un conductor registrado: código, vehículo, estado y avisos. Recibe el conductor y el
// clic (abre su ficha para ver, modificar o eliminar).
function ItemRegistrado({ c, onClick }) {
  return (
    <li>
      <button type="button" onClick={onClick} className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-slate-50">
        <div className="min-w-0 flex-1">
          <p className="flex items-center gap-1.5 text-sm font-semibold text-slate-900">
            <span className="truncate">{c.nombre || "Conductor"}</span>
            {c.solicito_restablecimiento && (
              <KeyRound size={13} className="shrink-0 text-warning-strong" aria-label="Solicitó restablecer su contraseña" />
            )}
          </p>
          <p className="mt-0.5 flex items-center gap-1.5 truncate text-xs text-slate-500">
            <span className="nums">{c.codigo || "—"}</span>
            <span aria-hidden="true">·</span>
            {c.vehiculo
              ? <span className="inline-flex items-center gap-1 nums"><Truck size={12} />{c.vehiculo.placa}</span>
              : <span className="text-slate-400">Sin vehículo</span>}
          </p>
        </div>
        <EstadoBadge estado={!c.estado ? "INACTIVO" : c.en_ruta ? "EN_RUTA" : "DISPONIBLE"} />
      </button>
    </li>
  );
}
