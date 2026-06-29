import { useEffect, useMemo, useState } from "react";
import { ClipboardList, Search, CheckCircle2, MessageSquare } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import SectionCard from "../components/ui/SectionCard";
import DataTable from "../components/ui/DataTable";
import Input from "../components/ui/Input";
import Badge from "../components/ui/Badge";
import { listarReportes } from "../services/api";

// Fecha legible corta (es-PE). Entrada: fecha ISO. Salida: "dd/mm/aa hh:mm" o "—".
const fmt = (f) => (f ? new Date(f).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" }) : "—");

// Badge del estado del reporte (ABIERTO/RESUELTO) con tono semántico.
function BadgeEstado({ estado }) {
  if (estado === "RESUELTO") return <Badge tono="success">Resuelto</Badge>;
  return <Badge tono="warning">Abierto</Badge>;
}

// Historial de reportes de incidencia de pedidos (trazabilidad): tabla con TODOS
// los reportes y filtros de estado + búsqueda por código de pedido o conductor.
// Es solo lectura; la respuesta del admin se gestiona en la Bandeja/operación.
export default function HistorialReportes() {
  const [reportes, setReportes] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [estado, setEstado] = useState("TODOS"); // TODOS | ABIERTO | RESUELTO
  const [busqueda, setBusqueda] = useState("");

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
      <PageHeader titulo="Historial de Reportes" subtitulo="Reportes de incidencia que los conductores levantan sobre los pedidos." />

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
          empty={{ icon: ClipboardList, title: "Sin reportes", description: "No hay reportes que coincidan con el filtro." }} />
      </SectionCard>
    </div>
  );
}
