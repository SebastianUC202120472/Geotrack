import { useEffect, useState } from "react";
import { AlertTriangle, Package, User, Loader2, CheckCircle2, Clock, FileX, MessageSquare } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import SectionCard from "../components/ui/SectionCard";
import KpiCard from "../components/ui/KpiCard";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import EmptyState from "../components/ui/EmptyState";
import { listarReportes, responderReporte } from "../services/api";

const fmt = (f) => (f ? new Date(f).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" }) : "—");
const ACCIONES = ["Traer a base", "Reprogramar entrega", "Reintentar hoy", "Cerrar sin acción"];

// Pantalla de reportes de incidencia: los conductores reportan pedidos con falla
// y el admin responde con una solución.
export default function Reportes() {
  const [reportes, setReportes] = useState([]);
  const [filtro, setFiltro] = useState(""); // "", ABIERTO, RESUELTO
  const [cargando, setCargando] = useState(true);
  const [sel, setSel] = useState(null);
  const [respuesta, setRespuesta] = useState("");
  const [accion, setAccion] = useState(ACCIONES[0]);
  const [enviando, setEnviando] = useState(false);
  const [aviso, setAviso] = useState(null);

  const cargar = async () => {
    setCargando(true);
    try {
      setReportes(await listarReportes(filtro || undefined));
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargar();
  }, [filtro]);

  const abrir = (r) => {
    setSel(r);
    setRespuesta(r.respuesta || "");
    setAccion(r.accion || ACCIONES[0]);
    setAviso(null);
  };

  const responder = async (e) => {
    e.preventDefault();
    if (!respuesta.trim()) return;
    setEnviando(true);
    setAviso(null);
    try {
      await responderReporte(sel.id, { respuesta: respuesta.trim(), accion, estado: "RESUELTO" });
      setAviso({ ok: true, texto: "Reporte respondido y marcado como resuelto." });
      await cargar();
      setSel(null);
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
    } finally {
      setEnviando(false);
    }
  };

  // Derivados de los datos existentes (sin inventar nada)
  const abiertos = reportes.filter((r) => r.estado === "ABIERTO").length;
  const resueltos = reportes.filter((r) => r.estado === "RESUELTO").length;
  const total = reportes.length;

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-up">
      {/* Cabecera */}
      <PageHeader titulo="Reportes de Incidencias" subtitulo="Pedidos con falla reportados por los conductores.">
        <Input as="select" value={filtro} onChange={(e) => setFiltro(e.target.value)} aria-label="Filtrar por estado">
          <option value="">Todos</option>
          <option value="ABIERTO">Abiertos</option>
          <option value="RESUELTO">Resueltos</option>
        </Input>
      </PageHeader>

      {/* KPIs — solo cuando hay datos cargados */}
      {!cargando && (
        <div className="grid gap-4 sm:grid-cols-3 animate-fade-up">
          <KpiCard label="Total reportes" value={total} icon={FileX} tone="brand" />
          <KpiCard label="Abiertos" value={abiertos} icon={AlertTriangle} tone="warning" />
          <KpiCard label="Resueltos" value={resueltos} icon={CheckCircle2} tone="success" />
        </div>
      )}

      {/* Aviso de operación */}
      {aviso && (
        <div className={`flex items-center gap-2 rounded-xl px-4 py-3 text-sm ${aviso.ok ? "bg-success-soft text-success-strong" : "bg-danger-soft text-danger-strong"}`}>
          {aviso.ok ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
          <span>{aviso.texto}</span>
        </div>
      )}

      {/* Panel principal: lista + detalle */}
      <div className="grid gap-6 lg:grid-cols-3 animate-fade-up">
        {/* Lista de reportes */}
        <SectionCard
          className="lg:col-span-1"
          title="Reportes"
          subtitle="Selecciona uno para ver el detalle"
          action={
            <Badge tono="warning">{abiertos} abiertos</Badge>
          }
        >
          {cargando ? (
            <p className="py-10 text-center text-sm text-slate-500">Cargando…</p>
          ) : reportes.length === 0 ? (
            <EmptyState
              icon={FileX}
              title="Sin reportes"
              description="No hay reportes que coincidan con el filtro seleccionado."
            />
          ) : (
            <ul className="-m-2 divide-y divide-slate-50">
              {reportes.map((r) => (
                <li key={r.id}>
                  <button
                    onClick={() => abrir(r)}
                    className={`flex w-full flex-col gap-1 rounded-lg p-3 text-left transition-colors ${sel?.id === r.id ? "bg-brand-50" : "hover:bg-slate-50"}`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-800 nums">{r.pedido_codigo || `#${r.pedido_id}`}</span>
                      <Badge tono={r.estado === "ABIERTO" ? "warning" : "success"}>
                        {r.estado === "ABIERTO" ? "Abierto" : "Resuelto"}
                      </Badge>
                    </div>
                    <span className="truncate text-sm text-slate-600">{r.motivo}</span>
                    <span className="text-xs text-slate-400">{r.conductor_nombre || `Conductor ${r.conductor_id}`} · {fmt(r.creado_en)}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </SectionCard>

        {/* Panel de detalle y respuesta */}
        <SectionCard
          className="lg:col-span-2"
          title={sel ? `Reporte · ${sel.pedido_codigo || sel.pedido_id}` : "Detalle del reporte"}
          subtitle={sel ? `Estado: ${sel.estado === "ABIERTO" ? "Abierto — pendiente de respuesta" : "Resuelto"}` : undefined}
        >
          {!sel ? (
            <EmptyState
              icon={MessageSquare}
              title="Selecciona un reporte"
              description="Haz clic en un reporte de la lista para ver el detalle y responder."
            />
          ) : (
            <div className="space-y-4">
              <Dato icono={Package} etiqueta="Pedido" valor={`${sel.pedido_codigo || sel.pedido_id} — ${sel.direccion_destino || ""}`} />
              <Dato icono={User} etiqueta="Conductor" valor={sel.conductor_nombre || `id ${sel.conductor_id}`} />
              <Dato icono={Clock} etiqueta="Reportado" valor={fmt(sel.creado_en)} />

              <div className="rounded-xl bg-slate-50 p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Motivo</p>
                <p className="font-medium text-slate-800">{sel.motivo}</p>
                {sel.descripcion && <p className="mt-1 text-sm text-slate-600">{sel.descripcion}</p>}
              </div>

              {sel.estado === "RESUELTO" ? (
                <div className="rounded-xl border border-success/30 bg-success-soft p-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-success-strong">Respuesta ({sel.accion})</p>
                  <p className="mt-1 text-sm text-slate-700">{sel.respuesta}</p>
                  <p className="mt-1 text-xs text-slate-400">{fmt(sel.respondido_en)}</p>
                </div>
              ) : (
                <form onSubmit={responder} className="space-y-3 border-t border-slate-100 pt-4">
                  <Input as="select" label="Acción" value={accion} onChange={(e) => setAccion(e.target.value)}>
                    {ACCIONES.map((a) => <option key={a} value={a}>{a}</option>)}
                  </Input>
                  <div className="space-y-1.5">
                    <label className="block text-sm font-medium text-slate-700">Respuesta / solución</label>
                    <textarea
                      value={respuesta}
                      onChange={(e) => setRespuesta(e.target.value)}
                      rows={3}
                      placeholder="Ej. Coordinamos recojo a base mañana 9am…"
                      className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
                    />
                  </div>
                  <Button type="submit" disabled={enviando || !respuesta.trim()}>
                    {enviando ? <Loader2 className="animate-spin" size={18} /> : "Responder y marcar resuelto"}
                  </Button>
                </form>
              )}
            </div>
          )}
        </SectionCard>
      </div>
    </div>
  );
}

function Dato({ etiqueta, valor, icono: Icono }) {
  return (
    <div className="flex items-start gap-2 text-sm">
      <Icono size={16} className="mt-0.5 text-slate-400" />
      <div>
        <p className="text-slate-400">{etiqueta}</p>
        <p className="font-medium text-slate-700">{valor}</p>
      </div>
    </div>
  );
}
