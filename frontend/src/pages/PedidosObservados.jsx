import { useEffect, useMemo, useState } from "react";
import { AlertOctagon, CheckCircle2, AlertCircle, Clock, Search } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import DataTable from "../components/ui/DataTable";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import ConfirmDialog from "../components/ui/ConfirmDialog";
import { listarObservados, resolverObservado } from "../services/api";

// Tono de la antigüedad del caso: más de 3 días en rojo, más de 1 en ámbar. Recibe los días.
const tonoDias = (d) => (d > 3 ? "danger" : d >= 1 ? "warning" : "neutral");

// Vista de almacén con TODOS los pedidos observados (faltantes al ingresar), sin tener que
// entrar lote por lote (C15-01). Permite marcar un caso como resuelto. Sin props.
export default function PedidosObservados() {
  const [items, setItems] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [q, setQ] = useState("");
  const [aviso, setAviso] = useState(null);
  const [resolviendo, setResolviendo] = useState(null); // pedido a resolver (dialogo)
  const [trabajando, setTrabajando] = useState(false);
  const [version, setVersion] = useState(0); // fuerza la recarga tras resolver

  useEffect(() => {
    let activo = true;
    listarObservados()
      .then((d) => activo && setItems(d))
      .catch((err) => activo && setAviso({ ok: false, texto: err.message }))
      .finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, [version]);

  const filtrados = useMemo(() => {
    const t = q.trim().toLowerCase();
    if (!t) return items;
    return items.filter((p) =>
      [p.codigo, p.referencia, p.cliente, p.destinatario, p.lote].filter(Boolean).join(" ").toLowerCase().includes(t)
    );
  }, [items, q]);

  const kpis = useMemo(() => ({
    total: items.length,
    antiguos: items.filter((p) => p.dias > 3).length,
    lotes: new Set(items.map((p) => p.lote).filter(Boolean)).size,
  }), [items]);

  // Marca el pedido como resuelto (vuelve a Listo para envío) tras confirmarlo.
  const resolver = async () => {
    if (!resolviendo) return;
    setTrabajando(true);
    setAviso(null);
    try {
      const r = await resolverObservado(resolviendo.pedido_id);
      setAviso({ ok: true, texto: r.mensaje || `Pedido ${resolviendo.codigo} resuelto.` });
      setResolviendo(null);
      setVersion((v) => v + 1);
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
    } finally {
      setTrabajando(false);
    }
  };

  const columnas = [
    { key: "codigo", header: "Pedido", render: (p) => (
      <div>
        <p className="font-medium text-slate-800 nums">{p.codigo || "—"}</p>
        <p className="text-xs text-slate-400">Ref. {p.referencia || "—"}</p>
      </div>
    ) },
    { key: "cliente", header: "Cliente", render: (p) => <span className="text-slate-700">{p.cliente}</span> },
    { key: "destinatario", header: "Destinatario", render: (p) => (
      <div className="max-w-xs">
        <p className="text-slate-700">{p.destinatario || "—"}</p>
        <p className="truncate text-xs text-slate-400">{p.direccion_destino}</p>
      </div>
    ) },
    { key: "lote", header: "Lote", render: (p) => <span className="nums text-slate-600">{p.lote || "—"}</span> },
    { key: "dias", header: "Antigüedad", render: (p) => (
      <Badge tono={tonoDias(p.dias)}><Clock size={12} />{p.dias === 0 ? "Hoy" : `${p.dias} día${p.dias !== 1 ? "s" : ""}`}</Badge>
    ) },
    { key: "acciones", header: "", render: (p) => (
      <Button size="sm" variant="secondary" icon={CheckCircle2} onClick={(e) => { e.stopPropagation(); setResolviendo(p); }}>
        Resolver
      </Button>
    ) },
  ];

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader titulo="Pedidos observados" subtitulo="Paquetes que faltaron al ingresar un lote. Ubícalos y márcalos como resueltos." />

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 animate-fade-up">
        <KpiCard label="Observados" value={kpis.total} icon={AlertOctagon} tone="danger" />
        <KpiCard label="Con más de 3 días" value={kpis.antiguos} icon={Clock} tone="warning" />
        <KpiCard label="Lotes afectados" value={kpis.lotes} icon={AlertOctagon} tone="brand" />
      </div>

      {aviso && (
        <div className={`flex items-center gap-2 rounded-xl px-4 py-3 text-sm ${aviso.ok ? "bg-success-soft text-success-strong" : "bg-danger-soft text-danger-strong"}`}>
          {aviso.ok ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
          <span>{aviso.texto}</span>
        </div>
      )}

      <div className="relative max-w-sm animate-fade-up">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Buscar pedido, referencia, cliente o lote…"
          aria-label="Buscar observados"
          className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-9 pr-3 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
        />
      </div>

      <DataTable
        columns={columnas}
        rows={filtrados}
        rowKey={(p) => p.pedido_id}
        loading={cargando}
        empty={{ icon: CheckCircle2, title: "No hay pedidos observados", description: "Todos los lotes ingresaron completos." }}
      />

      <ConfirmDialog
        open={!!resolviendo}
        titulo={`¿Resolver ${resolviendo?.codigo || "el pedido"}?`}
        mensaje="Confírmalo solo si el paquete ya está físicamente en el almacén: pasará a Listo para envío y entrará a la agrupación por zonas."
        textoConfirmar="Sí, resolver"
        icono={CheckCircle2}
        cargando={trabajando}
        onConfirmar={resolver}
        onCancelar={() => setResolviendo(null)}
      />
    </div>
  );
}
