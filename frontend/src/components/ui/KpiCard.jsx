import useCountUp from "../../hooks/useCountUp";

// Tarjeta KPI con icono, valor animado y tendencia opcional. Recibe label, value, icon, tone, trend y live.
const tonos = {
  brand: { chip: "bg-brand-50 text-brand-600", dot: "text-brand-600" },
  info: { chip: "bg-info-soft text-info-strong", dot: "text-info" },
  success: { chip: "bg-success-soft text-success-strong", dot: "text-success" },
  warning: { chip: "bg-warning-soft text-warning-strong", dot: "text-warning" },
  danger: { chip: "bg-danger-soft text-danger-strong", dot: "text-danger" },
};

export default function KpiCard({ label, value, icon: Icon, tone = "brand", trend, live = false }) {
  const animado = useCountUp(value);
  const t = tonos[tone] || tonos.brand;

  return (
    <div className="rounded-card border border-slate-200 bg-white p-5 shadow-card transition-all duration-200 hover:-translate-y-0.5 hover:shadow-card-hover">
      <div className="flex items-start justify-between">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          {label}
        </span>
        {Icon && (
          <span className={`rounded-chip p-2 ${t.chip}`}>
            <Icon size={18} />
          </span>
        )}
      </div>
      <p className="mt-3 text-3xl font-bold text-slate-900 nums">{animado}</p>
      <div className="mt-2 flex items-center gap-2">
        {live && (
          <span className={`live-dot h-2 w-2 rounded-full bg-current ${t.dot}`} aria-hidden="true" />
        )}
        {trend && (
          <span className={`text-xs font-semibold ${trend.dir === "down" ? "text-danger-strong" : "text-success-strong"}`}>
            {trend.dir === "down" ? "▼" : "▲"} {trend.text}
          </span>
        )}
      </div>
    </div>
  );
}
