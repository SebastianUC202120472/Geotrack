// Pestaña "Métricas": cuántas conversaciones hubo, qué porcentaje se resolvió sin una persona,
// temas más consultados, empresas captadas y alertas de seguridad. Primero las básicas (tarjetas
// y temas); la serie diaria es una métrica avanzada y es lo primero que se recorta si falta tiempo.
import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Tooltip, XAxis, YAxis } from "recharts";
import { Building2, MessagesSquare, ShieldAlert, UserCheck } from "lucide-react";
import KpiCard from "../../../components/ui/KpiCard";
import SectionCard from "../../../components/ui/SectionCard";
import ChartCard from "../../../components/ui/ChartCard";
import Input from "../../../components/ui/Input";
import { obtenerMetricas } from "./servicioAdminAtencion";

const MODOS = { ia: "Con IA", sin_ia: "Sin IA (respaldo)", bloqueado: "Bloqueadas por seguridad", accion: "Confirmaciones" };

// Pestaña de métricas. Sin props.
export default function TabMetricas() {
  const [dias, setDias] = useState(30);
  const [m, setM] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let vivo = true;
    obtenerMetricas(dias).then((d) => { if (vivo) { setM(d); setError(""); } }).catch((e) => vivo && setError(e.message));
    return () => { vivo = false; };
  }, [dias]);

  if (error) return <p role="alert" className="rounded-xl border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger-strong">{error}</p>;
  if (!m) return <p className="text-sm text-slate-500">Cargando…</p>;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-end">
        <Input as="select" value={dias} onChange={(e) => setDias(Number(e.target.value))} aria-label="Periodo">
          <option value={7}>Últimos 7 días</option>
          <option value={30}>Últimos 30 días</option>
          <option value={90}>Últimos 90 días</option>
        </Input>
      </div>
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KpiCard label="Conversaciones" value={m.conversaciones} icon={MessagesSquare} tone="brand" />
        <KpiCard label="Resueltas sin una persona" value={m.porcentaje_sin_persona == null ? "—" : `${m.porcentaje_sin_persona} %`} icon={UserCheck} tone="success" />
        <KpiCard label="Empresas captadas" value={m.empresas_captadas} icon={Building2} tone="info" />
        <KpiCard label="Alertas de seguridad" value={m.alertas_seguridad} icon={ShieldAlert} tone="warning" />
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <SectionCard title="Temas más consultados" subtitle="Artículos de la base de conocimiento usados en las respuestas">
          {m.temas.length === 0 ? <p className="text-sm text-slate-500">Todavía no hay consultas en este periodo.</p> : (
            <ol className="space-y-1.5 text-sm">
              {m.temas.map((t) => (
                <li key={t.clave} className="flex items-center justify-between gap-3 rounded-xl bg-warm-50 px-3 py-2">
                  <span className="text-slate-700">{t.titulo}</span>
                  <span className="font-semibold text-slate-800 nums">{t.veces}</span>
                </li>
              ))}
            </ol>
          )}
        </SectionCard>
        <SectionCard title="Gestiones" subtitle={`Periodo: ${m.dias} días`}>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-xl bg-warm-50 px-3 py-2"><dt className="text-slate-500">Derivadas a una persona</dt><dd className="text-lg font-semibold text-slate-800 nums">{m.derivadas}</dd></div>
            <div className="rounded-xl bg-warm-50 px-3 py-2"><dt className="text-slate-500">Pendientes en la bandeja</dt><dd className="text-lg font-semibold text-slate-800 nums">{m.derivaciones_pendientes}</dd></div>
            <div className="rounded-xl bg-warm-50 px-3 py-2"><dt className="text-slate-500">Reprogramaciones confirmadas</dt><dd className="text-lg font-semibold text-slate-800 nums">{m.reprogramaciones}</dd></div>
            <div className="rounded-xl bg-warm-50 px-3 py-2"><dt className="text-slate-500">Mensajes por voz</dt><dd className="text-lg font-semibold text-slate-800 nums">{m.mensajes_por_voz}</dd></div>
          </dl>
          <ul className="mt-3 space-y-1 text-xs text-slate-500">
            {Object.entries(m.respuestas_por_modo).map(([modo, n]) => <li key={modo}>{MODOS[modo] || modo}: <b className="text-slate-700">{n}</b></li>)}
          </ul>
        </SectionCard>
      </div>

      {m.por_dia.length > 0 && (
        <ChartCard title="Conversaciones por día" subtitle="Hora de Lima" height={220}>
          <BarChart data={m.por_dia} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
            <XAxis dataKey="dia" tick={{ fontSize: 11, fill: "#64748b" }} tickFormatter={(d) => d.slice(5)} />
            <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "#64748b" }} />
            <Tooltip />
            <Bar dataKey="conversaciones" name="Conversaciones" fill="#2563eb" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ChartCard>
      )}
    </div>
  );
}
