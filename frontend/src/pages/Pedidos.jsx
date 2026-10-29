import { useEffect, useMemo, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Search, X, Package, MapPin, Eye, ChevronLeft, ChevronRight, Loader2, RotateCcw, User, Truck, Filter, List, Building2, AlertTriangle, Ban, RefreshCw, CheckCircle2 } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import DataTable from "../components/ui/DataTable";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import { EstadoBadge } from "../components/ui/Badge";
import { etiquetaEstado } from "../utils/estados";
import Modal from "../components/ui/Modal";
import ResolverDireccionModal from "../components/ResolverDireccionModal";
import VistaPorRuta from "../components/seguimiento/VistaPorRuta";
import VistaPorCliente from "../components/seguimiento/VistaPorCliente";
import TabTrazabilidad from "../components/TabTrazabilidad";
import SolicitudesReprogramacion from "../components/SolicitudesReprogramacion";
import ConfirmDialog from "../components/ui/ConfirmDialog";
import { listarTodosLosPedidos, listarZonas, obtenerHistorial, reprogramarPedido, cancelarPedido, listarReportes, reprocesarDirecciones } from "../services/api";

const POR_PAGINA = 12;
const fmt = (f) => (f ? new Date(f).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" }) : "—");
const fmtDia = (f) => (f ? new Date(f).toLocaleDateString("es-PE", { day: "2-digit", month: "2-digit" }) : "—");

// Comprueba si fechaStr cae dentro del rango indicado. Recibe fechaStr (ISO) y modo ("hoy"/"semana"/"todos").
function enRango(fechaStr, modo) {
  if (modo === "todos" || !fechaStr) return true;
  const f = new Date(fechaStr);
  const ahora = new Date();
  if (modo === "hoy") return f.toDateString() === ahora.toDateString();
  if (modo === "semana") return ahora - f <= 7 * 24 * 3600 * 1000;
  return true;
}

const VISTAS = [
  { id: "lista", label: "Lista", icon: List },
  { id: "ruta", label: "Por ruta", icon: Truck },
  { id: "cliente", label: "Por cliente", icon: Building2 },
  { id: "trazabilidad", label: "Trazabilidad", icon: Search },
];

// Estados que el servidor reprocesa al pulsar «Reprocesar direcciones pendientes».
const ESTADOS_REPROCESABLES = ["LISTO_PARA_ENVIO", "GEOCODIFICACION_FALLIDA"];
// Un pedido entregado o cancelado ya no admite corregir su ubicación.
const ESTADOS_CERRADOS = ["ENTREGADO", "CANCELADO"];

// Página de pedidos con filtros, KPIs, tabla paginada y detalle lateral.
export default function Pedidos() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const [pedidos, setPedidos] = useState([]);
  const [zonas, setZonas] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [vista, setVista] = useState("lista");
  const [reportePorPedido, setReportePorPedido] = useState({});

  const [busqueda, setBusqueda] = useState("");
  // Zona y estado viven en la URL: un enlace (o el tablero) abre la lista ya filtrada.
  const distrito = params.get("distrito") || "";
  const estado = params.get("estado") || "";
  const [fecha, setFecha] = useState("todos");
  const [sinUbicar, setSinUbicar] = useState(false);
  const [pagina, setPagina] = useState(1);
  const [seleccionado, setSeleccionado] = useState(null);
  const [reprocesando, setReprocesando] = useState(false);
  const [avisoReproceso, setAvisoReproceso] = useState(null);

  // Pedido a abrir desde la URL (?codigo=PD-001), p. ej. al pulsar el aviso de una reprogramación (C37-02).
  const codigoUrl = (params.get("codigo") || "").toUpperCase();
  const pedidoDeUrl = useMemo(
    () => (codigoUrl ? pedidos.find((p) => (p.codigo || "").toUpperCase() === codigoUrl) || null : null),
    [codigoUrl, pedidos]
  );
  const abierto = seleccionado || pedidoDeUrl;

  // Cierra el detalle y quita el código de la URL para no volver a abrirlo. Sin parámetros.
  const cerrarDetalle = () => {
    setSeleccionado(null);
    if (codigoUrl) {
      const siguientes = new URLSearchParams(params);
      siguientes.delete("codigo");
      setParams(siguientes, { replace: true });
    }
  };

  // Carga reportes abiertos y construye mapa pedido_id → reporte.
  const cargarReportes = () => {
    listarReportes("ABIERTO").then((lista) => {
      const mapa = {};
      (lista || []).forEach((r) => { mapa[r.pedido_id] = r; });
      setReportePorPedido(mapa);
    }).catch((err) => console.error("Error al cargar reportes:", err.message));
  };

  // Carga pedidos y zonas. Las recargas son silenciosas (la tabla no parpadea); el estado se
  // fija dentro de los callbacks de la promesa (regla de lint "setState en effect").
  const cargar = () =>
    Promise.all([listarTodosLosPedidos(), listarZonas()])
      .then(([ped, z]) => { setPedidos(ped); setZonas(z.zonas_operativas || []); })
      .catch((err) => console.error("Error al cargar pedidos:", err.message))
      .finally(() => setCargando(false));

  // Recarga completa: pedidos + zonas + reportes abiertos.
  const cargarTodo = () => { cargar(); cargarReportes(); };

  useEffect(() => {
    cargar();
    cargarReportes();
  }, []);

  const estados = useMemo(
    () => [...new Set(pedidos.map((p) => p.estado).filter(Boolean))].sort(),
    [pedidos]
  );

  // KPIs calculados desde el array ya cargado (sin petición extra).
  const kpis = useMemo(() => {
    const total = pedidos.length;
    const pendientes = pedidos.filter((p) => p.estado === "LISTO_PARA_ENVIO").length;
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
      if (sinUbicar && !(p.latitud == null || p.longitud == null)) return false;
      if (!q) return true;
      return [p.codigo, p.cliente_origen, p.nombre_destinatario, p.direccion_destino, p.conductor_nombre]
        .some((v) => (v || "").toLowerCase().includes(q));
    });
  }, [pedidos, busqueda, distrito, estado, fecha, sinUbicar]);

  // Pedidos que esperan ser despachados y aún no tienen ubicación (los que reprocesa el servidor).
  const porUbicar = useMemo(
    () => pedidos.filter((p) => (p.latitud == null || p.longitud == null) && ESTADOS_REPROCESABLES.includes(p.estado)).length,
    [pedidos]
  );

  // Pide al servidor que vuelva a geocodificar una tanda de direcciones pendientes (C16-03).
  const reprocesar = () => {
    setReprocesando(true);
    setAvisoReproceso(null);
    reprocesarDirecciones()
      .then((r) => {
        const ubicados = r.pedidos_exitosos || 0;
        const sinUbicar = r.pedidos_fallidos || 0;
        const partes = [`${ubicados} pedido(s) ubicado(s)`];
        if (sinUbicar) partes.push(`${sinUbicar} siguen sin ubicar: ábrelos y usa «Resolver dirección»`);
        if (r.pedidos_restantes) partes.push(`quedan ${r.pedidos_restantes} para la siguiente tanda`);
        setAvisoReproceso({ ok: sinUbicar === 0, texto: `${partes.join("; ")}.` });
        cargar();
      })
      .catch((err) => setAvisoReproceso({ ok: false, texto: err.message }))
      .finally(() => setReprocesando(false));
  };

  const aplicarBusqueda = (v) => { setBusqueda(v); setPagina(1); };
  const aplicarFecha = (v) => { setFecha(v); setPagina(1); };


  const totalPaginas = Math.max(1, Math.ceil(filtrados.length / POR_PAGINA));
  const visibles = filtrados.slice((pagina - 1) * POR_PAGINA, pagina * POR_PAGINA);

  const setParam = (clave, valor) => {
    const nuevos = new URLSearchParams(params);
    if (valor) nuevos.set(clave, valor);
    else nuevos.delete(clave);
    setParams(nuevos);
    setPagina(1);
  };

  const limpiar = () => {
    setBusqueda(""); setFecha("todos"); setSinUbicar(false); setParams({}); setPagina(1);
  };

  const hayFiltros = busqueda || distrito || estado || fecha !== "todos" || sinUbicar;

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
      // Pedido FALLIDO con reporte abierto: badge parpadeante + ícono de prioridad.
      render: (p) => {
        const tieneReporte = p.estado === "FALLIDO" && reportePorPedido[p.id];
        return (
          <span className={`inline-flex items-center gap-1.5${tieneReporte ? " parpadeo-alerta" : ""}`}>
            <EstadoBadge estado={p.estado} />
            {tieneReporte && (
              <span title="Reporte pendiente de resolución">
                <AlertTriangle size={14} className="text-warning-strong" />
              </span>
            )}
          </span>
        );
      },
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
      >
        {vista === "lista" && (
          <Button variant="secondary" icon={reprocesando ? Loader2 : RefreshCw} onClick={reprocesar}
            disabled={reprocesando || porUbicar === 0}
            className={`shrink-0 whitespace-nowrap ${reprocesando ? "[&>svg]:animate-spin" : ""}`}
            title={porUbicar === 0 ? "No hay direcciones pendientes de ubicar" : undefined}>
            {reprocesando ? "Reprocesando…" : "Reprocesar direcciones pendientes"}
            {!reprocesando && porUbicar > 0 && (
              <span className="rounded-full bg-warning-soft px-2 py-0.5 text-xs font-bold text-warning-strong nums">{porUbicar}</span>
            )}
          </Button>
        )}
      </PageHeader>

      {vista === "lista" && avisoReproceso && (
        <div className={`flex items-start gap-3 rounded-xl px-4 py-3 text-sm animate-fade-up ${
          avisoReproceso.ok
            ? "bg-success-soft text-success-strong border border-success/20"
            : "bg-warning-soft text-warning-strong border border-warning/30"
        }`}>
          {avisoReproceso.ok ? <CheckCircle2 size={18} className="mt-0.5 shrink-0" /> : <AlertTriangle size={18} className="mt-0.5 shrink-0" />}
          <span className="flex-1">{avisoReproceso.texto}</span>
          <button onClick={() => setAvisoReproceso(null)} aria-label="Cerrar aviso" className="rounded p-0.5 opacity-70 hover:opacity-100">
            <X size={16} />
          </button>
        </div>
      )}

      <div className="animate-fade-up">
        <div className="inline-flex max-w-full items-center gap-1 overflow-x-auto rounded-2xl border border-warm-200 bg-white p-1 shadow-card">
          {VISTAS.map((v) => {
            const Ico = v.icon;
            const activo = vista === v.id;
            return (
              <button
                key={v.id}
                onClick={() => setVista(v.id)}
                className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-all duration-200 ${
                  activo
                    ? "bg-brand-600 text-white shadow-sm"
                    : "text-slate-500 hover:bg-slate-50 hover:text-slate-800"
                }`}
              >
                <Ico size={15} />
                {v.label}
              </button>
            );
          })}
        </div>
      </div>

      {vista === "ruta" && <VistaPorRuta />}
      {vista === "cliente" && <VistaPorCliente />}
      {vista === "trazabilidad" && <TabTrazabilidad />}

      {vista === "lista" && <>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5 animate-fade-up">
        <KpiCard label="Total" value={kpis.total} icon={Package} tone="brand" />
        <KpiCard label="Listo p/envío" value={kpis.pendientes} icon={Filter} tone="warning" />
        <KpiCard label="En ruta" value={kpis.enRuta} icon={Truck} tone="info" />
        <KpiCard label="Entregados" value={kpis.entregados} icon={Package} tone="success" />
        <KpiCard label="Fallidos" value={kpis.fallidos} icon={Package} tone="danger" />
      </div>

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
            {estados.map((e) => <option key={e} value={e}>{etiquetaEstado(e)}</option>)}
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

      <Modal open={!!abierto} onClose={cerrarDetalle} variant="right">
        {abierto && (
          <DetallePedido
            key={abierto.id}
            pedido={abierto}
            reporte={reportePorPedido[abierto.id] || null}
            onCerrar={cerrarDetalle}
            onIrARuta={() => { cerrarDetalle(); setVista("ruta"); }}
            onAccion={() => { cerrarDetalle(); cargarTodo(); }}
            onDireccionResuelta={() => { cerrarDetalle(); cargar(); }}
            onVerReporte={(codigo) => navigate(`/panel/reportes?pedido=${encodeURIComponent(codigo)}`)}
          />
        )}
      </Modal>
      </>}
    </div>
  );
}

// Panel lateral de detalle. Recibe pedido, reporte abierto (o null) y callbacks de acción.
function DetallePedido({ pedido, reporte, onCerrar, onIrARuta, onAccion, onDireccionResuelta, onVerReporte }) {
  const [historial, setHistorial] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [accionando, setAccionando] = useState(false);
  const [mostrarResolver, setMostrarResolver] = useState(false);
  const [confirmarCancelar, setConfirmarCancelar] = useState(false);
  const [motivo, setMotivo] = useState("");
  const sinUbicacion = pedido.latitud == null || pedido.longitud == null;
  const corregible = !ESTADOS_CERRADOS.includes(pedido.estado);

  // El detalle se monta de nuevo por pedido (key), asi que "cargando" ya arranca en true.
  useEffect(() => {
    let activo = true;
    obtenerHistorial(pedido.codigo)
      .then((h) => { if (activo) setHistorial(h); })
      .catch((e) => { if (activo) setError(e.message); })
      .finally(() => { if (activo) setCargando(false); });
    return () => { activo = false; };
  }, [pedido.codigo]);

  // Reprograma el pedido (vuelve a LISTO_PARA_ENVIO) y resuelve el reporte asociado.
  const reprogramar = () => {
    setAccionando(true);
    reprogramarPedido(pedido.id)
      .then(() => onAccion())
      .catch((e) => { setError(e.message); setAccionando(false); });
  };

  // Cancela el pedido con el motivo escrito (C31-02) y resuelve el reporte asociado.
  const cancelar = () => {
    setAccionando(true);
    cancelarPedido(pedido.id, motivo.trim())
      .then(() => onAccion())
      .catch((e) => { setError(e.message); setAccionando(false); setConfirmarCancelar(false); });
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
        <div className="flex items-center justify-between">
          <Dato etiqueta="Ruta asignada" valor={pedido.ruta_nombre || historial?.ruta_asignada || "Sin asignar"} icono={Truck} />
          {onIrARuta && (pedido.ruta_nombre || historial?.ruta_asignada) && (
            <button
              onClick={onIrARuta}
              className="rounded-lg bg-brand-50 px-2.5 py-1 text-xs font-semibold text-brand-700 hover:bg-brand-100"
            >
              Ver en Por ruta →
            </button>
          )}
        </div>
        <Dato etiqueta="Conductor" valor={pedido.conductor_nombre || historial?.conductor_asignado || "Sin asignar"} icono={User} />

        {pedido.estado === "FALLIDO" && reporte && (
          <div className="rounded-xl border border-warning/40 bg-warning-soft p-4 space-y-3">
            <div className="flex items-center gap-2">
              <AlertTriangle size={16} className="text-warning-strong shrink-0" />
              <p className="text-sm font-semibold text-warning-strong">Este pedido tiene un reporte abierto</p>
            </div>
            {reporte.motivo && (
              <p className="text-sm text-slate-700"><span className="font-medium">Motivo:</span> {reporte.motivo}</p>
            )}
            {error && <p className="text-xs text-red-600">{error}</p>}

            <div className="flex flex-wrap gap-2 pt-1">
              <Button size="sm" icon={RotateCcw} onClick={reprogramar} disabled={accionando}>
                {accionando ? "Procesando…" : "Reprogramar"}
              </Button>
              <Button size="sm" variant="danger" icon={Ban} onClick={() => setConfirmarCancelar(true)} disabled={accionando}>
                Cancelar pedido
              </Button>
              <Button size="sm" variant="secondary" icon={Eye}
                onClick={() => onVerReporte && onVerReporte(pedido.codigo)} disabled={accionando}>
                Ver reporte
              </Button>
            </div>
          </div>
        )}

        {pedido.estado === "FALLIDO" && !reporte && (
          <div className="rounded-xl border border-warning/30 bg-warning-soft p-4">
            <p className="text-sm text-warning-strong">Este pedido está fallido. Puedes reprogramarlo para reasignarlo o cancelarlo.</p>
            {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
            <div className="mt-3 flex flex-wrap gap-2">
              <Button variant="secondary" icon={RotateCcw} onClick={reprogramar} disabled={accionando}>
                {accionando ? "Procesando…" : "Reprogramar → Listo p/envío"}
              </Button>
              <Button variant="danger" icon={Ban} onClick={() => setConfirmarCancelar(true)} disabled={accionando}>
                Cancelar pedido
              </Button>
            </div>
          </div>
        )}

        {pedido.estado === "CANCELADO" && pedido.motivo_cancelacion && (
          <Dato etiqueta="Motivo de la cancelación" valor={pedido.motivo_cancelacion} icono={Ban} />
        )}

        <SolicitudesReprogramacion
          pedidoId={pedido.id}
          pedidoEstado={pedido.estado}
          permitirAtender={pedido.estado !== "FALLIDO" && corregible}
          onAtendida={() => onAccion()}
        />

        {sinUbicacion ? (
          <div className="rounded-xl border border-brand-200 bg-brand-50 p-4">
            <p className="text-sm text-brand-800">Este pedido no tiene ubicación geocodificada.</p>
            <div className="mt-3">
              <Button icon={MapPin} onClick={() => setMostrarResolver(true)}>
                Resolver dirección
              </Button>
            </div>
          </div>
        ) : corregible && (
          <div className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
            <p className="text-sm text-slate-600">¿El punto en el mapa está mal?</p>
            <Button size="sm" variant="secondary" icon={MapPin} className="shrink-0 whitespace-nowrap" onClick={() => setMostrarResolver(true)}>
              Corregir ubicación
            </Button>
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

      <ConfirmDialog
        open={confirmarCancelar}
        titulo={`¿Cancelar el pedido ${pedido.codigo}?`}
        mensaje="El pedido queda cancelado de forma definitiva y sale de su ruta. Indica el motivo: quedará en su historial."
        textoConfirmar="Cancelar pedido"
        tono="danger"
        cargando={accionando}
        deshabilitado={motivo.trim().length < 5}
        onConfirmar={cancelar}
        onCancelar={() => setConfirmarCancelar(false)}
      >
        <Input
          as="textarea"
          label="Motivo de la cancelación"
          rows={3}
          maxLength={255}
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          placeholder="Ej. El cliente desistió de la compra"
          hint="Mínimo 5 caracteres."
        />
      </ConfirmDialog>

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
