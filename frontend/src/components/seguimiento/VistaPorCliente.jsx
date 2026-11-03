import { useEffect, useState } from "react";
import { Building2, FileSpreadsheet, Loader2, Download, History } from "lucide-react";
import Card from "../ui/Card";
import SectionCard from "../ui/SectionCard";
import EmptyState from "../ui/EmptyState";
import Button from "../ui/Button";
import Input from "../ui/Input";
import { obtenerSeguimientoClientes, generarLiquidacion, descargarLiquidacion, historialLiquidaciones } from "../../services/api";

// Fecha corta dd/mm/aaaa de una fecha ISO (sin desfase de zona). Recibe la fecha.
const dia = (f) => (f ? new Date(f.length === 10 ? `${f}T12:00:00` : f).toLocaleDateString("es-PE") : "—");

// Muestra repartos agrupados por empresa. Sin props; carga datos al montar.
export default function VistaPorCliente() {
  const [clientes, setClientes] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [historial, setHistorial] = useState([]);

  // Recarga el historial de liquidaciones (C36-02). Sin parámetros.
  const cargarHistorial = () => historialLiquidaciones().then((h) => setHistorial(h || [])).catch(() => {});

  useEffect(() => {
    let activo = true;
    historialLiquidaciones().then((h) => activo && setHistorial(h || [])).catch(() => {});
    return () => { activo = false; };
  }, []);

  useEffect(() => {
    let activo = true;
    obtenerSeguimientoClientes()
      .then((data) => { if (activo) setClientes(data || []); })
      .catch((err) => {
        console.error("No se pudo cargar los clientes:", err.message);
        if (activo) setClientes([]);
      })
      .finally(() => { if (activo) setCargando(false); });
    return () => { activo = false; };
  }, []);

  if (cargando) {
    return (
      <SectionCard>
        <div className="flex justify-center py-12 text-slate-400">
          <Loader2 className="animate-spin" size={24} />
        </div>
      </SectionCard>
    );
  }

  if (!clientes || clientes.length === 0) {
    return (
      <SectionCard title="Clientes">
        <EmptyState
          icon={Building2}
          title="Sin pedidos de clientes"
          description="Los repartos agrupados por empresa aparecerán aquí."
        />
      </SectionCard>
    );
  }

  const rangoInvalido = desde && hasta && desde > hasta;

  return (
    <div className="space-y-6">
      <SectionCard
        title="Por cliente"
        subtitle={`${clientes.length} empresa${clientes.length !== 1 ? "s" : ""} con pedidos activos`}
        action={
          <div className="flex flex-wrap items-end gap-2">
            <Input type="date" label="Liquidar desde" value={desde} max={hasta || undefined} onChange={(e) => setDesde(e.target.value)} />
            <Input type="date" label="Hasta" value={hasta} min={desde || undefined} onChange={(e) => setHasta(e.target.value)} />
          </div>
        }
      >
        <p className="mb-4 text-xs text-slate-500">
          {desde || hasta
            ? `La liquidación incluirá los pedidos entregados o fallidos ${desde ? `desde el ${dia(desde)}` : ""} ${hasta ? `hasta el ${dia(hasta)}` : ""}.`
            : "Sin fechas, la liquidación incluye todo el histórico del cliente."}
          {rangoInvalido && <span className="ml-1 font-semibold text-danger-strong">La fecha inicial es posterior a la final.</span>}
        </p>
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {clientes.map((c, i) => (
            <div key={c.cliente} style={{ animationDelay: `${i * 40}ms` }} className="animate-fade-up">
              <ClienteCard c={c} desde={desde} hasta={hasta} bloqueado={rangoInvalido} onGenerada={cargarHistorial} />
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard title="Liquidaciones generadas" subtitle="Vuelve a descargar las anteriores">
        {historial.length === 0 ? (
          <EmptyState icon={History} title="Sin liquidaciones" description="Las que generes aparecerán aquí." />
        ) : (
          <ul className="divide-y divide-slate-100">
            {historial.map((l) => (
              <li key={l.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-slate-800">{l.cliente}</p>
                  <p className="text-xs text-slate-500 nums">
                    {l.periodo_inicio || l.periodo_fin ? `${dia(l.periodo_inicio)} – ${dia(l.periodo_fin)}` : "Todo el histórico"}
                    {l.total_pedidos != null && ` · ${l.total_pedidos} pedidos`} · generada {new Date(l.generada_en).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" })}
                  </p>
                </div>
                {l.disponible ? (
                  <Button size="sm" variant="secondary" icon={Download} onClick={() => descargarLiquidacion(l.descarga_url, `liquidacion_${l.id}.xlsx`)}>
                    Descargar
                  </Button>
                ) : (
                  <span className="text-xs text-slate-400">Archivo no disponible</span>
                )}
              </li>
            ))}
          </ul>
        )}
      </SectionCard>
    </div>
  );
}

const MINI_DOT = { success: "bg-success", info: "bg-info", warning: "bg-warning", danger: "bg-danger", neutral: "bg-slate-400" };

// Indicador de conteo con punto de color. Recibe tono, valor y etiqueta.
function Mini({ tono, valor, etiqueta }) {
  return (
    <div className="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 transition-colors hover:bg-brand-50">
      <span className={`h-2 w-2 shrink-0 rounded-full ${MINI_DOT[tono]}`} />
      <span className="text-lg font-bold text-slate-800 nums">{valor}</span>
      <span className="text-xs text-slate-400">{etiqueta}</span>
    </div>
  );
}

// Tarjeta de empresa con barra de progreso y desglose de estados. Recibe el cliente c, el rango
// de fechas de la liquidación (C36-01), si está bloqueada y onGenerada (refresca el historial).
function ClienteCard({ c, desde, hasta, bloqueado, onGenerada }) {
  const avance = c.total ? Math.round((c.entregados / c.total) * 100) : 0;
  const [generando, setGenerando] = useState(false);
  const [error, setError] = useState(null);

  // Genera la liquidacion del cliente y descarga el Excel.
  const descargar = () => {
    setGenerando(true);
    setError(null);
    generarLiquidacion({ cliente: c.cliente, periodo_inicio: desde || null, periodo_fin: hasta || null })
      .then((res) => descargarLiquidacion(res.descarga_url, res.archivo).then(() => onGenerada && onGenerada()))
      .catch((err) => setError(err.message))
      .finally(() => setGenerando(false));
  };

  return (
    <Card hover>
      <div className="mb-4 flex items-start justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <span className="shrink-0 rounded-xl bg-brand-50 p-2 text-brand-600">
            <Building2 size={18} />
          </span>
          <h3 className="truncate font-semibold text-slate-900" title={c.cliente}>
            {c.cliente}
          </h3>
        </div>
        <span className="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-500 nums">
          {c.total}
        </span>
      </div>

      <div className="mb-4">
        <div className="mb-1 flex justify-between text-sm">
          <span className="text-slate-500">Entregado</span>
          <span className="font-semibold text-slate-700 nums">{avance}%</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-success transition-all"
            style={{ width: `${avance}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Mini tono="success" valor={c.entregados} etiqueta="Entregados" />
        <Mini tono="info" valor={c.en_proceso} etiqueta="En proceso" />
        <Mini tono="warning" valor={c.pendientes} etiqueta="Pendientes" />
        <Mini tono="danger" valor={c.fallidos} etiqueta="Fallidos" />
        {c.cancelados > 0 && <Mini tono="neutral" valor={c.cancelados} etiqueta="Cancelados" />}
      </div>

      <Button
        variant="secondary"
        size="sm"
        block
        className="mt-4"
        icon={generando ? Loader2 : FileSpreadsheet}
        onClick={descargar}
        disabled={generando || bloqueado}
      >
        {generando ? "Generando…" : "Descargar liquidación (Excel)"}
      </Button>
      {error && <p className="mt-2 text-xs text-danger-strong">{error}</p>}
    </Card>
  );
}
