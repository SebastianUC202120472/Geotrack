import { useEffect, useMemo, useState } from "react";
import { BookText, Search } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import SectionCard from "../components/ui/SectionCard";
import DataTable from "../components/ui/DataTable";
import Input from "../components/ui/Input";
import { listarReclamos } from "../services/api";

// Fecha legible corta (es-PE). Entrada: fecha ISO. Salida: "dd/mm/aa hh:mm" o "—".
const fmt = (f) => (f ? new Date(f).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" }) : "—");

// Pantalla de solo lectura del Libro de Reclamaciones (reclamos enviados desde el portal).
export default function LibroReclamaciones() {
  const [reclamos, setReclamos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [busqueda, setBusqueda] = useState("");

  useEffect(() => {
    let activo = true;
    listarReclamos()
      .then((d) => activo && setReclamos(Array.isArray(d) ? d : []))
      .catch(() => {})
      .finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, []);

  const kpis = useMemo(() => ({
    total: reclamos.length,
    reclamos: reclamos.filter((r) => r.tipo === "RECLAMO").length,
    quejas: reclamos.filter((r) => r.tipo === "QUEJA").length,
  }), [reclamos]);

  const filtrados = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    if (!q) return reclamos;
    return reclamos.filter((r) =>
      (r.codigo || "").toLowerCase().includes(q) ||
      (r.consumidor || "").toLowerCase().includes(q) ||
      (r.pedido || "").toLowerCase().includes(q)
    );
  }, [reclamos, busqueda]);

  const columnas = [
    { key: "codigo", header: "Código", render: (r) => <span className="font-medium text-slate-800 nums">{r.codigo || "—"}</span> },
    { key: "tipo", header: "Tipo", render: (r) => <span className="text-slate-700">{r.tipo === "QUEJA" ? "Queja" : "Reclamo"}</span> },
    { key: "consumidor", header: "Consumidor", render: (r) => (
      <div>
        <p className="font-medium text-slate-700">{r.consumidor || "—"}</p>
        <p className="text-xs text-slate-500">{r.dni ? `DNI ${r.dni}` : r.email || ""}</p>
      </div>
    ) },
    { key: "pedido", header: "Pedido", render: (r) => <span className="text-slate-600 nums">{r.pedido || "—"}</span> },
    { key: "detalle", header: "Detalle", render: (r) => <span className="text-xs text-slate-600 line-clamp-2">{r.detalle || "—"}</span> },
    { key: "creado_en", header: "Fecha", render: (r) => <span className="text-xs text-slate-500 nums">{fmt(r.creado_en)}</span> },
  ];

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader titulo="Libro de Reclamaciones" subtitulo="Reclamos y quejas enviados por los clientes desde el portal público." />

      <div className="grid grid-cols-3 gap-4 animate-fade-up">
        <KpiCard label="Total" value={kpis.total} icon={BookText} tone="brand" />
        <KpiCard label="Reclamos" value={kpis.reclamos} icon={BookText} tone="warning" />
        <KpiCard label="Quejas" value={kpis.quejas} icon={BookText} tone="info" />
      </div>

      <SectionCard className="animate-fade-up" title="Reclamos" subtitle={`${filtrados.length} de ${reclamos.length}`}
        action={
          <div className="relative">
            <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <Input value={busqueda} onChange={(e) => setBusqueda(e.target.value)} placeholder="Código, consumidor o pedido" className="pl-9" />
          </div>
        }
      >
        <DataTable columns={columnas} rows={filtrados} rowKey={(r) => r.id} loading={cargando}
          empty={{ icon: BookText, title: "Sin reclamos", description: "Aún no se han registrado reclamos desde el portal." }} />
      </SectionCard>
    </div>
  );
}
