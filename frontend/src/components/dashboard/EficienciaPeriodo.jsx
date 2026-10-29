// Eficiencia del periodo en el tablero (C34-01, C34-02) e indicadores del proyecto In.OE.1-4 (C34-03).
import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { Target, CircleCheck, CircleX, Clock, PiggyBank, Download } from "lucide-react";
import Card from "../ui/Card";
import Button from "../ui/Button";
import { obtenerKpis, obtenerIndicadores, descargarIndicadores } from "../../services/api";

const PERIODOS = [
  { id: "dia", label: "Hoy" },
  { id: "semana", label: "Esta semana" },
  { id: "mes", label: "Este mes" },
];

const TONOS = {
  brand: "bg-brand-50 text-brand-600",
  success: "bg-success-soft text-success-strong",
  danger: "bg-danger-soft text-danger-strong",
  warning: "bg-warning-soft text-warning-strong",
  info: "bg-info-soft text-info-strong",
};

const soles = (n) => `S/ ${Number(n || 0).toLocaleString("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
// Valor o guion si no hay datos. Recibe el valor y un sufijo.
const o = (v, sufijo = "") => (v == null ? "—" : `${v}${sufijo}`);
// Día corto dd/mm de una fecha AAAA-MM-DD. Recibe la fecha.
const diaCorto = (f) => new Date(`${f}T12:00:00`).toLocaleDateString("es-PE", { day: "2-digit", month: "2-digit" });

// Mosaico de un KPI. Recibe etiqueta, valor, detalle, icono y tono.
function Kpi({ etiqueta, valor, detalle, icono: Icono, tono }) {
  return (
    <div className="rounded-2xl border border-slate-100 bg-white p-4">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-medium text-slate-500">{etiqueta}</p>
        <span className={`rounded-lg p-1.5 ${TONOS[tono]}`}><Icono size={15} /></span>
      </div>
      <p className="mt-2 text-2xl font-bold text-slate-900 nums">{valor}</p>
      {detalle && <p className="mt-0.5 text-xs text-slate-400">{detalle}</p>}
    </div>
  );
}

// Fila de un indicador del proyecto. Recibe código, nombre, valor y cómo se calcula.
function Indicador({ codigo, nombre, valor, detalle }) {
  return (
    <div className="flex items-start justify-between gap-4 py-2.5">
      <div className="min-w-0">
        <p className="text-sm font-medium text-slate-800"><span className="mr-1.5 text-xs font-semibold text-brand-600">{codigo}</span>{nombre}</p>
        <p className="text-xs text-slate-500">{detalle}</p>
      </div>
      <p className="shrink-0 text-base font-bold text-slate-900 nums">{valor}</p>
    </div>
  );
}

// Panel de eficiencia con selector de periodo; se refresca con `version` (el tablero lo sube cada 20 s).
// Recibe version.
export default function EficienciaPeriodo({ version = 0 }) {
  const [periodo, setPeriodo] = useState("dia");
  const [kpis, setKpis] = useState(null);
  const [ind, setInd] = useState(null);
  const [descargando, setDescargando] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let activo = true;
    Promise.all([obtenerKpis(periodo), obtenerIndicadores(periodo)])
      .then(([k, i]) => { if (activo) { setKpis(k); setInd(i); setError(""); } })
      .catch((e) => activo && setError(e.message));
    return () => { activo = false; };
  }, [periodo, version]);

  // Descarga el reporte de indicadores del periodo en Excel. Sin parámetros.
  const exportar = () => {
    setDescargando(true);
    descargarIndicadores(periodo).catch((e) => setError(e.message)).finally(() => setDescargando(false));
  };

  const serie = (kpis?.serie || []).map((f) => ({ ...f, dia: diaCorto(f.dia) }));

  return (
    <Card
      title="Eficiencia del período"
      subtitle={kpis ? `Del ${new Date(`${kpis.desde}T12:00:00`).toLocaleDateString("es-PE")} al ${new Date(`${kpis.hasta}T12:00:00`).toLocaleDateString("es-PE")}` : "Cargando…"}
      action={
        <div role="tablist" aria-label="Período" className="flex rounded-xl bg-slate-100 p-1">
          {PERIODOS.map((p) => (
            <button key={p.id} type="button" role="tab" aria-selected={periodo === p.id} onClick={() => setPeriodo(p.id)}
              className={`whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-semibold transition ${periodo === p.id ? "bg-white text-brand-700 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}>
              {p.label}
            </button>
          ))}
        </div>
      }
    >
      {error && <p className="mb-3 rounded-xl bg-danger-soft px-3 py-2 text-sm text-danger-strong">{error}</p>}
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <Kpi etiqueta="Cumplimiento" valor={o(kpis?.cumplimiento, " %")} icono={Target} tono="brand"
          detalle={kpis ? `${kpis.entregados} de ${kpis.gestionados} gestionados` : ""} />
        <Kpi etiqueta="Entregados" valor={o(kpis?.entregados)} icono={CircleCheck} tono="success" />
        <Kpi etiqueta="Fallidos" valor={o(kpis?.fallidos)} icono={CircleX} tono="danger" detalle="Intentos sin entregar" />
        <Kpi etiqueta="Pendientes" valor={o(kpis?.pendientes)} icono={Clock} tono="warning" detalle="Aún por entregar (hoy)" />
        <Kpi etiqueta="Ahorro de la flota" valor={kpis ? soles(kpis.ahorro_soles) : "—"} icono={PiggyBank} tono="info"
          detalle={kpis ? `${kpis.km_ahorrados} km ahorrados · ${kpis.rutas_cerradas} rutas` : ""} />
      </div>

      {serie.length > 1 && (
        <div className="mt-5">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={serie} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" vertical={false} />
              <XAxis dataKey="dia" tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} axisLine={{ stroke: "#e2e8f0" }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 13 }} />
              <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="entregados" name="Entregados" stackId="a" fill="#16a34a" maxBarSize={36} />
              <Bar dataKey="fallidos" name="Fallidos" stackId="a" fill="#dc2626" radius={[6, 6, 0, 0]} maxBarSize={36} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="mt-5 border-t border-slate-100 pt-4">
        <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
          <p className="text-sm font-semibold text-slate-700">Indicadores del proyecto</p>
          <Button size="sm" variant="secondary" icon={Download} className="whitespace-nowrap" onClick={exportar} disabled={descargando || !ind}>
            {descargando ? "Descargando…" : "Exportar a Excel"}
          </Button>
        </div>
        {ind && (
          <div className="divide-y divide-slate-100">
            <Indicador codigo="In.OE.1" nombre="Tiempo de registro de un lote" valor={o(ind.in_oe_1.minutos_promedio, " min")}
              detalle={`Del correo de solicitud al registro · ${ind.in_oe_1.lotes_por_correo} de ${ind.in_oe_1.lotes} lotes llegaron por correo`} />
            <Indicador codigo="In.OE.2" nombre="Distancia por ruta" valor={o(ind.in_oe_2.km_promedio_por_ruta, " km")}
              detalle={`${ind.in_oe_2.rutas} rutas cerradas · ahorro ${o(ind.in_oe_2.ahorro_porcentaje, " %")}`} />
            <Indicador codigo="In.OE.3" nombre="Pedidos perdidos · entregas con foto" valor={`${ind.in_oe_3.pedidos_perdidos} · ${o(ind.in_oe_3.entregas_con_foto_porcentaje, " %")}`}
              detalle={`${ind.in_oe_3.observados_en_almacen} faltantes en almacén y ${ind.in_oe_3.cancelados} cancelados · con GPS ${o(ind.in_oe_3.entregas_con_gps_porcentaje, " %")}`} />
            <Indicador codigo="In.OE.4" nombre="Pérdidas" valor={soles(ind.in_oe_4.perdidas_soles)}
              detalle={`${ind.in_oe_4.reintentos} reintentos (${soles(ind.in_oe_4.costo_reintentos_soles)}) + reclamado ${soles(ind.in_oe_4.monto_reclamado_soles)}`} />
          </div>
        )}
      </div>
    </Card>
  );
}
