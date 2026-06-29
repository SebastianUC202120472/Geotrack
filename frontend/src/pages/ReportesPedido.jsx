import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { ClipboardList, Search, CheckCircle2, MessageSquare, X, AlertTriangle } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import SectionCard from "../components/ui/SectionCard";
import DataTable from "../components/ui/DataTable";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import Modal from "../components/ui/Modal";
import { listarReportes, responderReporte } from "../services/api";

// Fecha legible corta (es-PE). Entrada: fecha ISO. Salida: "dd/mm/aa hh:mm" o "—".
const fmt = (f) => (f ? new Date(f).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" }) : "—");

// Badge del estado del reporte (ABIERTO/RESUELTO) con tono semántico.
function BadgeEstado({ estado }) {
  if (estado === "RESUELTO") return <Badge tono="success">Resuelto</Badge>;
  return <Badge tono="warning">Abierto</Badge>;
}

// Reportes de pedido (trazabilidad): tabla con TODOS los reportes que los
// conductores levantan sobre los pedidos, con filtros de estado + búsqueda. Al
// hacer clic en una fila se abre un panel lateral con el detalle y, si el
// reporte está ABIERTO, el formulario para responder y marcarlo resuelto.
export default function ReportesPedido() {
  const [params] = useSearchParams();
  const [reportes, setReportes] = useState([]);
  const [cargando, setCargando] = useState(true);
  // Estado inicial leído de los query params (una sola vez, sin setState en effect):
  // ?pendientes=1 o ?estado=ABIERTO preseleccionan ABIERTO; ?pedido=<codigo> precarga la búsqueda.
  const [estado, setEstado] = useState(() =>
    params.get("pendientes") === "1" || params.get("estado") === "ABIERTO" ? "ABIERTO" : "TODOS"
  ); // TODOS | ABIERTO | RESUELTO
  const [busqueda, setBusqueda] = useState(() => params.get("pedido") || "");
  // Reporte seleccionado para mostrar el panel de detalle/resolución.
  const [seleccionado, setSeleccionado] = useState(null);

  // Carga inicial: trae TODOS los reportes (sin filtro de estado). El filtrado es
  // client-side. setState en callbacks de promesa (evita el lint de effect).
  useEffect(() => {
    let activo = true;
    listarReportes()
      .then((d) => activo && setReportes(Array.isArray(d) ? d : []))
      .catch(() => {})
      .finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, []);

  // Recarga la lista de reportes (tras responder uno) sin tocar el spinner inicial.
  const recargar = () => {
    listarReportes()
      .then((d) => setReportes(Array.isArray(d) ? d : []))
      .catch(() => {});
  };

  // KPIs derivados de la lista cargada (sin fetch extra).
  const kpis = useMemo(() => ({
    total: reportes.length,
    abiertos: reportes.filter((r) => r.estado === "ABIERTO").length,
    resueltos: reportes.filter((r) => r.estado === "RESUELTO").length,
  }), [reportes]);

  // Aplica los filtros de estado y búsqueda sobre la lista (client-side).
  const filtrados = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    return reportes.filter((r) => {
      if (estado !== "TODOS" && r.estado !== estado) return false;
      if (!q) return true;
      return (
        (r.pedido_codigo || "").toLowerCase().includes(q) ||
        (r.conductor_nombre || "").toLowerCase().includes(q)
      );
    });
  }, [reportes, estado, busqueda]);

  const columnas = [
    { key: "pedido_codigo", header: "Pedido", render: (r) => (
      <div>
        <p className="font-medium text-slate-800 nums">{r.pedido_codigo || "—"}</p>
        <p className="text-xs text-slate-500 line-clamp-1">{r.direccion_destino || ""}</p>
      </div>
    ) },
    { key: "conductor_nombre", header: "Conductor", render: (r) => <span className="text-slate-700">{r.conductor_nombre || "—"}</span> },
    { key: "motivo", header: "Motivo", render: (r) => (
      <div>
        <p className="font-medium text-slate-700">{r.motivo || "—"}</p>
        {r.descripcion && <p className="text-xs text-slate-500 line-clamp-2">{r.descripcion}</p>}
      </div>
    ) },
    { key: "estado", header: "Estado", render: (r) => <BadgeEstado estado={r.estado} /> },
    { key: "respuesta", header: "Respuesta del admin", render: (r) => (
      r.respuesta
        ? <div className="flex items-start gap-1.5 text-slate-600"><MessageSquare size={14} className="mt-0.5 shrink-0 text-slate-400" /><span className="line-clamp-2 text-xs">{r.respuesta}</span></div>
        : <span className="text-xs text-slate-400">Sin respuesta</span>
    ) },
    { key: "creado_en", header: "Fecha", render: (r) => (
      <div className="text-xs text-slate-500 nums">
        <p>{fmt(r.creado_en)}</p>
        {r.respondido_en && <p className="text-slate-400">Resp. {fmt(r.respondido_en)}</p>}
      </div>
    ) },
  ];

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader titulo="Reportes de pedido" subtitulo="Reportes que los conductores levantan sobre los pedidos. Ábrelos para responder y marcarlos resueltos." />

      <div className="grid grid-cols-3 gap-4 animate-fade-up">
        <KpiCard label="Total" value={kpis.total} icon={ClipboardList} tone="brand" />
        <KpiCard label="Abiertos" value={kpis.abiertos} icon={ClipboardList} tone="warning" />
        <KpiCard label="Resueltos" value={kpis.resueltos} icon={CheckCircle2} tone="success" />
      </div>

      <SectionCard className="animate-fade-up" title="Reportes" subtitle={`${filtrados.length} de ${reportes.length}`}
        action={
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <div className="relative">
              <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <Input value={busqueda} onChange={(e) => setBusqueda(e.target.value)} placeholder="Código de pedido o conductor" className="pl-9" />
            </div>
            <Input as="select" value={estado} onChange={(e) => setEstado(e.target.value)}>
              <option value="TODOS">Todos los estados</option>
              <option value="ABIERTO">Abiertos</option>
              <option value="RESUELTO">Resueltos</option>
            </Input>
          </div>
        }
      >
        <DataTable columns={columnas} rows={filtrados} rowKey={(r) => r.id} loading={cargando}
          onRowClick={(r) => setSeleccionado(r)}
          empty={{ icon: ClipboardList, title: "Sin reportes", description: "No hay reportes que coincidan con el filtro." }} />
      </SectionCard>

      {/* Panel lateral con el detalle del reporte y la resolución */}
      <Modal open={!!seleccionado} onClose={() => setSeleccionado(null)} variant="right">
        {seleccionado && (
          <DetalleReporte
            reporte={seleccionado}
            onCerrar={() => setSeleccionado(null)}
            onResuelto={() => { setSeleccionado(null); recargar(); }}
          />
        )}
      </Modal>
    </div>
  );
}

// Panel de detalle de un reporte. Muestra pedido/conductor/motivo/descripción y,
// si está ABIERTO, un formulario (respuesta obligatoria + acción opcional) para
// marcarlo resuelto. Si ya está RESUELTO, muestra la respuesta en solo lectura.
// Entrada: reporte (objeto), onCerrar (fn), onResuelto (fn tras marcar resuelto).
function DetalleReporte({ reporte: r, onCerrar, onResuelto }) {
  const [respuesta, setRespuesta] = useState("");
  const [accion, setAccion] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState("");

  // Marca el reporte resuelto con la respuesta (obligatoria) y la acción (opcional).
  const marcarResuelto = () => {
    if (!respuesta.trim()) return;
    setGuardando(true);
    setError("");
    responderReporte(r.id, { respuesta: respuesta.trim(), accion: accion.trim() || undefined })
      .then(() => onResuelto())
      .catch((e) => { setError(e.message); setGuardando(false); });
  };

  return (
    <>
      <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
        <div className="flex items-center gap-2">
          <AlertTriangle size={20} className="text-warning-strong shrink-0" />
          <div>
            <h2 className="font-bold text-slate-900 nums">{r.pedido_codigo || "Reporte"}</h2>
            <BadgeEstado estado={r.estado} />
          </div>
        </div>
        <button onClick={onCerrar} aria-label="Cerrar" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"><X size={20} /></button>
      </div>

      <div className="space-y-4 px-6 py-5">
        <Dato etiqueta="Pedido" valor={r.pedido_codigo || "—"} />
        {r.direccion_destino && <Dato etiqueta="Dirección" valor={r.direccion_destino} />}
        <Dato etiqueta="Conductor" valor={r.conductor_nombre || "—"} />
        <Dato etiqueta="Motivo" valor={r.motivo || "—"} />
        {r.descripcion && <Dato etiqueta="Descripción" valor={r.descripcion} />}
        <Dato etiqueta="Reportado" valor={fmt(r.creado_en)} />

        {error && (
          <p className="rounded-xl bg-danger-soft px-4 py-2.5 text-sm text-danger-strong">{error}</p>
        )}

        {/* Reporte ABIERTO: formulario de resolución */}
        {r.estado === "ABIERTO" && (
          <div className="space-y-3 rounded-xl border border-warning/40 bg-warning-soft p-4">
            <p className="text-sm font-semibold text-warning-strong">Responder y resolver</p>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-500">Respuesta <span className="text-danger">*</span></label>
              <textarea
                value={respuesta}
                onChange={(e) => setRespuesta(e.target.value)}
                placeholder="Escribe la respuesta o instrucción para el conductor…"
                rows={3}
                className="w-full rounded-xl border border-slate-200 bg-white p-3 text-sm text-slate-800 placeholder:text-slate-400 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30 resize-none"
              />
            </div>
            <Input label="Acción tomada (opcional)" value={accion} onChange={(e) => setAccion(e.target.value)}
              placeholder="Ej. Reprogramado para mañana" />
            <Button icon={CheckCircle2} block onClick={marcarResuelto} disabled={guardando || !respuesta.trim()}>
              {guardando ? "Guardando…" : "Marcar resuelto"}
            </Button>
          </div>
        )}

        {/* Reporte RESUELTO: respuesta en solo lectura */}
        {r.estado === "RESUELTO" && (
          <div className="space-y-2 rounded-xl border border-success/30 bg-success-soft p-4">
            <p className="flex items-center gap-1.5 text-sm font-semibold text-success-strong">
              <CheckCircle2 size={16} /> Resuelto {r.respondido_en ? `· ${fmt(r.respondido_en)}` : ""}
            </p>
            <p className="text-sm text-slate-700">{r.respuesta || "Sin respuesta registrada."}</p>
            {r.accion && <p className="text-xs text-slate-500"><span className="font-medium">Acción:</span> {r.accion}</p>}
          </div>
        )}
      </div>
    </>
  );
}

// Fila de dato simple con etiqueta + valor (para el panel de detalle).
function Dato({ etiqueta, valor }) {
  return (
    <div className="text-sm">
      <p className="text-slate-400">{etiqueta}</p>
      <p className="font-medium text-slate-700">{valor}</p>
    </div>
  );
}
