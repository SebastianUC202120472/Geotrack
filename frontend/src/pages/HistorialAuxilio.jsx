import { useEffect, useMemo, useState } from "react";
import { Wrench, CheckCircle2 } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import SectionCard from "../components/ui/SectionCard";
import DataTable from "../components/ui/DataTable";
import Input from "../components/ui/Input";
import Badge from "../components/ui/Badge";
import { listarIncidencias } from "../services/api";

// Fecha legible corta (es-PE). Entrada: fecha ISO. Salida: "dd/mm/aa hh:mm" o "—".
const fmt = (f) => (f ? new Date(f).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" }) : "—");

// Badge del estado de la incidencia (ABIERTA/RESUELTA) con tono semántico.
function BadgeEstado({ estado }) {
  if (estado === "RESUELTA") return <Badge tono="success">Resuelta</Badge>;
  return <Badge tono="danger">Abierta</Badge>;
}

// Historial de auxilio mecánico (CUS-30): tabla con TODAS las incidencias de la
// flota y filtros por conductor (dropdown armado con la data) + estado. Es solo
// historial, sin acciones de resolver aquí.
export default function HistorialAuxilio() {
  const [incidencias, setIncidencias] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [conductorId, setConductorId] = useState("TODOS"); // id (string) o "TODOS"
  const [estado, setEstado] = useState("TODAS"); // TODAS | ABIERTA | RESUELTA

  // Carga inicial: trae TODAS las incidencias (sin filtro). El filtrado es
  // client-side. setState en callbacks de promesa (evita el lint de effect).
  useEffect(() => {
    let activo = true;
    listarIncidencias()
      .then((d) => activo && setIncidencias(Array.isArray(d) ? d : []))
      .catch(() => {})
      .finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, []);

  // Conductores distintos presentes en la data (para armar el dropdown de filtro).
  const conductores = useMemo(() => {
    const mapa = new Map();
    incidencias.forEach((i) => {
      if (i.conductor_id != null && !mapa.has(i.conductor_id)) {
        mapa.set(i.conductor_id, i.conductor_nombre || `Conductor ${i.conductor_id}`);
      }
    });
    return [...mapa.entries()].map(([id, nombre]) => ({ id, nombre }));
  }, [incidencias]);

  // KPIs derivados de la lista cargada (sin fetch extra).
  const kpis = useMemo(() => ({
    total: incidencias.length,
    abiertas: incidencias.filter((i) => i.estado === "ABIERTA").length,
    resueltas: incidencias.filter((i) => i.estado === "RESUELTA").length,
  }), [incidencias]);

  // Aplica los filtros de conductor y estado sobre la lista (client-side).
  const filtradas = useMemo(() => {
    return incidencias.filter((i) => {
      if (estado !== "TODAS" && i.estado !== estado) return false;
      if (conductorId !== "TODOS" && String(i.conductor_id) !== String(conductorId)) return false;
      return true;
    });
  }, [incidencias, conductorId, estado]);

  const columnas = [
    { key: "codigo", header: "Código", render: (i) => <span className="font-medium text-slate-800 nums">{i.codigo || "—"}</span> },
    { key: "conductor_nombre", header: "Conductor", render: (i) => (
      <div>
        <p className="font-medium text-slate-700">{i.conductor_nombre || "—"}</p>
        <p className="text-xs text-slate-500">{i.vehiculo_placa || "Sin vehículo"}</p>
      </div>
    ) },
    { key: "ruta_nombre", header: "Ruta", render: (i) => <span className="text-slate-600">{i.ruta_nombre || "—"}</span> },
    { key: "tipo", header: "Incidencia", render: (i) => (
      <div>
        <p className="font-medium text-slate-700">{i.tipo || "—"}</p>
        {i.descripcion && <p className="text-xs text-slate-500 line-clamp-2">{i.descripcion}</p>}
      </div>
    ) },
    { key: "estado", header: "Estado", render: (i) => <BadgeEstado estado={i.estado} /> },
    { key: "nota_resolucion", header: "Resolución", render: (i) => (
      i.nota_resolucion
        ? <span className="line-clamp-2 text-xs text-slate-600">{i.nota_resolucion}</span>
        : <span className="text-xs text-slate-400">—</span>
    ) },
    { key: "creado_en", header: "Fecha", render: (i) => (
      <div className="text-xs text-slate-500 nums">
        <p>{fmt(i.creado_en)}</p>
        {i.resuelto_en && <p className="text-slate-400">Res. {fmt(i.resuelto_en)}</p>}
      </div>
    ) },
  ];

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader titulo="Historial de Auxilio" subtitulo="Incidencias mecánicas reportadas por los conductores en ruta." />

      <div className="grid grid-cols-3 gap-4 animate-fade-up">
        <KpiCard label="Total" value={kpis.total} icon={Wrench} tone="brand" />
        <KpiCard label="Abiertas" value={kpis.abiertas} icon={Wrench} tone="danger" />
        <KpiCard label="Resueltas" value={kpis.resueltas} icon={CheckCircle2} tone="success" />
      </div>

      <SectionCard className="animate-fade-up" title="Incidencias" subtitle={`${filtradas.length} de ${incidencias.length}`}
        action={
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <Input as="select" value={conductorId} onChange={(e) => setConductorId(e.target.value)}>
              <option value="TODOS">Todos los conductores</option>
              {conductores.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
            </Input>
            <Input as="select" value={estado} onChange={(e) => setEstado(e.target.value)}>
              <option value="TODAS">Todos los estados</option>
              <option value="ABIERTA">Abiertas</option>
              <option value="RESUELTA">Resueltas</option>
            </Input>
          </div>
        }
      >
        <DataTable columns={columnas} rows={filtradas} rowKey={(i) => i.id} loading={cargando}
          empty={{ icon: Wrench, title: "Sin incidencias", description: "No hay incidencias que coincidan con el filtro." }} />
      </SectionCard>
    </div>
  );
}
