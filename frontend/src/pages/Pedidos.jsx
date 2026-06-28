import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Search, X, Package, MapPin, Eye, ChevronLeft, ChevronRight, Loader2, RotateCcw, User, Truck, Filter } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import DataTable from "../components/ui/DataTable";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import { EstadoBadge } from "../components/ui/Badge";
import Modal from "../components/ui/Modal";
import ResolverDireccionModal from "../components/ResolverDireccionModal";
import { listarPedidos, listarZonas, obtenerHistorial, reabrirPedido } from "../services/api";

const POR_PAGINA = 12;
const fmt = (f) => (f ? new Date(f).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" }) : "—");
const fmtDia = (f) => (f ? new Date(f).toLocaleDateString("es-PE", { day: "2-digit", month: "2-digit" }) : "—");

// Filtra una fecha según el rango elegido (hoy / últimos 7 días / todos).
function enRango(fechaStr, modo) {
  if (modo === "todos" || !fechaStr) return true;
  const f = new Date(fechaStr);
  const ahora = new Date();
  if (modo === "hoy") return f.toDateString() === ahora.toDateString();
  if (modo === "semana") return ahora - f <= 7 * 24 * 3600 * 1000;
  return true;
}

// Explorador de pedidos: buscar, filtrar (zona, estado, fecha) y abrir el detalle
// con su ruta/conductor y línea de tiempo. Pensado para manejar cientos de pedidos.
export default function Pedidos() {
  const [params, setParams] = useSearchParams();
  const [pedidos, setPedidos] = useState([]);
  const [zonas, setZonas] = useState([]);
  const [cargando, setCargando] = useState(true);

  const [busqueda, setBusqueda] = useState("");
  const [distrito, setDistrito] = useState(params.get("distrito") || "");
  const [estado, setEstado] = useState(params.get("estado") || "");
  const [fecha, setFecha] = useState("todos");
  const [sinUbicar, setSinUbicar] = useState(false);
  const [pagina, setPagina] = useState(1);
  const [seleccionado, setSeleccionado] = useState(null);

  const cargar = async () => {
    setCargando(true);
    try {
      const [ped, z] = await Promise.all([listarPedidos(), listarZonas()]);
      setPedidos(ped);
      setZonas(z.zonas_operativas || []);
    } catch (err) {
      console.error("Error al cargar pedidos:", err.message);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargar();
  }, []);

  // Mantiene los filtros sincronizados con la URL (para enlaces desde Dashboard/Zonas).
  useEffect(() => {
    setDistrito(params.get("distrito") || "");
    setEstado(params.get("estado") || "");
  }, [params]);

  const estados = useMemo(
    () => [...new Set(pedidos.map((p) => p.estado).filter(Boolean))].sort(),
    [pedidos]
  );

  // KPIs calculados desde el array ya cargado (sin petición extra).
  const kpis = useMemo(() => {
    const total = pedidos.length;
    const pendientes = pedidos.filter((p) => p.estado === "PENDIENTE").length;
    const enRuta = pedidos.filter((p) => p.estado === "EN_RUTA").length;
    const entregados = pedidos.filter((p) => p.estado === "ENTREGADO").length;
    const fallidos = pedidos.filter((p) => p.estado === "FALLIDO").length;
    return { total, pendientes, enRuta, entregados, fallidos };
  }, [pedidos]);

  const filtrados = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    return pedidos.filter((p) => {
      if (distrito && (p.distrito || "") !== distrito) return false;
      if (estado && p.estado !== estado) return false;
      if (!enRango(p.fecha_creacion, fecha)) return false;
      // Filtro "Sin ubicar": muestra solo pedidos con lat/lng nulos.
      if (sinUbicar && !(p.latitud == null || p.longitud == null)) return false;
      if (!q) return true;
      return [p.codigo, p.cliente_origen, p.nombre_destinatario, p.direccion_destino, p.conductor_nombre]
        .some((v) => (v || "").toLowerCase().includes(q));
    });
  }, [pedidos, busqueda, distrito, estado, fecha, sinUbicar]);

  // Resetea paginación al cambiar filtros (dentro de callbacks, sin riesgo de lint)
  const aplicarBusqueda = (v) => { setBusqueda(v); setPagina(1); };
  const aplicarFecha = (v) => { setFecha(v); setPagina(1); };

  useEffect(() => { setPagina(1); }, [busqueda, distrito, estado, fecha]);

  const totalPaginas = Math.max(1, Math.ceil(filtrados.length / POR_PAGINA));
  const visibles = filtrados.slice((pagina - 1) * POR_PAGINA, pagina * POR_PAGINA);

  const setParam = (clave, valor) => {
    const nuevos = new URLSearchParams(params);
    if (valor) nuevos.set(clave, valor);
    else nuevos.delete(clave);
    setParams(nuevos);
  };

  const limpiar = () => {
    setBusqueda(""); setFecha("todos"); setSinUbicar(false); setParams({});
  };

  const hayFiltros = busqueda || distrito || estado || fecha !== "todos" || sinUbicar;

  // Columnas para DataTable
  const columnas = [
    {
      key: "codigo",
      header: "Código",
      render: (p) => <span className="font-medium text-slate-800 nums">{p.codigo}</span>,
    },
    {
      key: "nombre_destinatario",
      header: "Destinatario",
      render: (p) => <span className="text-slate-600">{p.nombre_destinatario || "—"}</span>,
    },
    {
      key: "distrito",
      header: "Distrito",
      render: (p) => <span className="text-slate-600">{p.distrito || "—"}</span>,
    },
    {
      key: "conductor_nombre",
      header: "Conductor",
      render: (p) =>
        p.conductor_nombre
          ? <span className="text-slate-600">{p.conductor_nombre}</span>
          : <span className="text-slate-400">Sin asignar</span>,
    },
    {
      key: "fecha_creacion",
      header: "Fecha",
      render: (p) => <span className="text-slate-500 nums">{fmtDia(p.fecha_creacion)}</span>,
    },
    {
      key: "estado",
      header: "Estado",
      render: (p) => <EstadoBadge estado={p.estado} />,
    },
    {
      key: "ver",
      header: "",
      className: "text-right",
      render: () => <Eye size={16} className="inline text-brand-600" />,
    },
  ];

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader
        titulo="Pedidos"
        subtitulo="Busca, filtra por zona/estado/fecha y abre la trazabilidad de cada pedido."
      />

      {/* KPIs derivados de los pedidos cargados */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5 animate-fade-up">
        <KpiCard label="Total" value={kpis.total} icon={Package} tone="brand" />
        <KpiCard label="Pendientes" value={kpis.pendientes} icon={Filter} tone="warning" />
        <KpiCard label="En ruta" value={kpis.enRuta} icon={Truck} tone="info" />
        <KpiCard label="Entregados" value={kpis.entregados} icon={Package} tone="success" />
        <KpiCard label="Fallidos" value={kpis.fallidos} icon={Package} tone="danger" />
      </div>

      {/* Filtros */}
      <div className="rounded-card border border-slate-200 bg-white p-5 shadow-card animate-fade-up" style={{ animationDelay: "60ms" }}>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="sm:col-span-2">
            <div className="relative">
              <Search size={18} className="pointer-events-none absolute left-3.5 top-3 text-slate-400" />
              <input
                value={busqueda}
                onChange={(e) => aplicarBusqueda(e.target.value)}
                placeholder="Buscar por código, cliente, destinatario, dirección o conductor…"
                aria-label="Buscar pedidos"
                className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-10 pr-3.5 text-sm text-slate-800 placeholder:text-slate-400 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
              />
            </div>
          </div>
          <Input as="select" value={distrito} onChange={(e) => setParam("distrito", e.target.value)} aria-label="Filtrar por zona">
            <option value="">Todas las zonas</option>
            {zonas.map((z, i) => <option key={i} value={z.distrito}>{z.distrito} ({z.total_pedidos})</option>)}
          </Input>
          <Input as="select" value={estado} onChange={(e) => setParam("estado", e.target.value)} aria-label="Filtrar por estado">
            <option value="">Todos los estados</option>
            {estados.map((e) => <option key={e} value={e}>{e.replaceAll("_", " ").toLowerCase()}</option>)}
          </Input>
        </div>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-500">Fecha:</span>
              {[["hoy", "Hoy"], ["semana", "7 días"], ["todos", "Todos"]].map(([v, l]) => (
                <button key={v} onClick={() => aplicarFecha(v)}
                  className={`rounded-lg px-3 py-1.5 text-sm font-medium transition ${fecha === v ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}>
                  {l}
                </button>
              ))}
            </div>
            {/* Toggle para mostrar solo pedidos sin coordenadas geocodificadas */}
            <button
              onClick={() => { setSinUbicar((v) => !v); setPagina(1); }}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition ${sinUbicar ? "bg-warning-soft text-warning-strong ring-1 ring-warning/40" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}
            >
              <MapPin size={14} />
              Sin ubicar
            </button>
          </div>
          <div className="flex items-center gap-3 text-sm text-slate-500">
            <span className="nums">{filtrados.length} pedido(s)</span>
            {hayFiltros && (
              <button onClick={limpiar} className="flex items-center gap-1 text-brand-600 hover:underline">
                <X size={14} /> Limpiar
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Tabla principal */}
      <div className="animate-fade-up" style={{ animationDelay: "120ms" }}>
        <DataTable
          columns={columnas}
          rows={visibles}
          rowKey={(p) => p.id}
          loading={cargando}
          empty={{
            icon: Package,
            title: "No hay pedidos que coincidan",
            description: "Prueba ajustando los filtros de búsqueda o cambia el rango de fechas.",
          }}
          onRowClick={(p) => setSeleccionado(p)}
        />
      </div>

      {/* Paginación */}
      {!cargando && totalPaginas > 1 && (
        <div className="flex items-center justify-between text-sm text-slate-500">
          <span>Página {pagina} de {totalPaginas}</span>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" icon={ChevronLeft} disabled={pagina === 1} onClick={() => setPagina((p) => p - 1)}>Anterior</Button>
            <Button variant="secondary" size="sm" disabled={pagina === totalPaginas} onClick={() => setPagina((p) => p + 1)}>
              Siguiente <ChevronRight size={16} />
            </Button>
          </div>
        </div>
      )}

      <Modal open={!!seleccionado} onClose={() => setSeleccionado(null)} variant="right">
        {seleccionado && (
          <DetallePedido
            pedido={seleccionado}
            onCerrar={() => setSeleccionado(null)}
            onReabierto={() => { setSeleccionado(null); cargar(); }}
            onDireccionResuelta={() => { setSeleccionado(null); cargar(); }}
          />
        )}
      </Modal>
    </div>
  );
}

// Panel lateral con el detalle del pedido, su ruta/conductor y línea de tiempo.
function DetallePedido({ pedido, onCerrar, onReabierto, onDireccionResuelta }) {
  const [historial, setHistorial] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [reabriendo, setReabriendo] = useState(false);
  // Controla si se muestra el modal de resolución de dirección.
  const [mostrarResolver, setMostrarResolver] = useState(false);

  useEffect(() => {
    let activo = true;
    setCargando(true);
    obtenerHistorial(pedido.codigo)
      .then((h) => activo && setHistorial(h))
      .catch((e) => activo && setError(e.message))
      .finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, [pedido.codigo]);

  const reabrir = async () => {
    setReabriendo(true);
    try {
      await reabrirPedido(pedido.id);
      onReabierto();
    } catch (e) {
      setError(e.message);
      setReabriendo(false);
    }
  };

  return (
    <>
      <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
        <div>
          <h2 className="font-bold text-slate-900 nums">{pedido.codigo}</h2>
          <EstadoBadge estado={pedido.estado} />
        </div>
        <button onClick={onCerrar} aria-label="Cerrar" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"><X size={20} /></button>
      </div>

      <div className="space-y-4 px-6 py-5">
        <Dato etiqueta="Cliente" valor={pedido.cliente_origen} />
        <Dato etiqueta="Destinatario" valor={pedido.nombre_destinatario || "—"} />
        <Dato etiqueta="Dirección" valor={pedido.direccion_destino} icono={MapPin} />
        <Dato etiqueta="Distrito" valor={pedido.distrito || "—"} />
        <Dato etiqueta="Ruta asignada" valor={pedido.ruta_nombre || historial?.ruta_asignada || "Sin asignar"} icono={Truck} />
        <Dato etiqueta="Conductor" valor={pedido.conductor_nombre || historial?.conductor_asignado || "Sin asignar"} icono={User} />

        {pedido.estado === "FALLIDO" && (
          <div className="rounded-xl border border-warning/30 bg-warning-soft p-4">
            <p className="text-sm text-warning-strong">Este pedido está fallido. Puedes reabrirlo para reasignarlo.</p>
            <div className="mt-3">
              <Button variant="secondary" icon={RotateCcw} onClick={reabrir} disabled={reabriendo}>
                {reabriendo ? "Reabriendo…" : "Reabrir → Pendiente"}
              </Button>
            </div>
          </div>
        )}

        {/* Si el pedido no tiene coordenadas, ofrecer resolución contextual */}
        {(pedido.latitud == null || pedido.longitud == null) && (
          <div className="rounded-xl border border-brand-200 bg-brand-50 p-4">
            <p className="text-sm text-brand-800">Este pedido no tiene ubicación geocodificada.</p>
            <div className="mt-3">
              <Button icon={MapPin} onClick={() => setMostrarResolver(true)}>
                Resolver dirección
              </Button>
            </div>
          </div>
        )}

        <div className="border-t border-slate-100 pt-4">
          <h3 className="mb-3 text-sm font-semibold text-slate-700">Línea de tiempo</h3>
          {cargando ? (
            <p className="flex items-center gap-2 text-sm text-slate-500"><Loader2 className="animate-spin" size={16} /> Cargando…</p>
          ) : error ? (
            <p className="text-sm text-slate-400">{error}</p>
          ) : historial?.eventos?.length ? (
            <ol className="relative ml-2 space-y-5 border-l-2 border-slate-100">
              {historial.eventos.map((ev, i) => (
                <li key={i} className="ml-5">
                  <span className="absolute -left-[9px] h-4 w-4 rounded-full border-2 border-white bg-brand-600" />
                  <p className="text-sm font-semibold text-slate-800">{ev.evento}</p>
                  <p className="text-sm text-slate-500">{ev.descripcion}</p>
                  <p className="mt-0.5 text-xs text-slate-400">{fmt(ev.fecha)}{ev.realizado_por ? ` · ${ev.realizado_por}` : ""}</p>
                </li>
              ))}
            </ol>
          ) : (
            <p className="text-sm text-slate-400">Sin eventos registrados.</p>
          )}
        </div>
      </div>

      {/* Modal de resolución de dirección (se abre sobre el panel lateral) */}
      <Modal open={mostrarResolver} onClose={() => setMostrarResolver(false)} variant="center">
        {mostrarResolver && (
          <ResolverDireccionModal
            pedido={pedido}
            onClose={() => setMostrarResolver(false)}
            onGuardado={() => {
              setMostrarResolver(false);
              onDireccionResuelta && onDireccionResuelta();
            }}
          />
        )}
      </Modal>
    </>
  );
}

function Dato({ etiqueta, valor, icono: Icono }) {
  return (
    <div className="flex items-start gap-2 text-sm">
      {Icono && <Icono size={16} className="mt-0.5 text-slate-400" />}
      <div>
        <p className="text-slate-400">{etiqueta}</p>
        <p className="font-medium text-slate-700">{valor}</p>
      </div>
    </div>
  );
}
