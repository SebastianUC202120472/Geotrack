import { TrendingUp, TrendingDown } from "lucide-react";

// Tarjeta de KPI: etiqueta, número grande, icono y, opcionalmente, una
// variación (delta) o un texto de apoyo (hint).
export default function StatCard({ label, value, icon: Icon, delta, hint }) {
  const subeObaja = typeof delta === "number" ? (delta >= 0 ? "up" : "down") : null;

  return (
    <div className="bg-white border border-slate-200 rounded-card shadow-card p-5 transition-shadow hover:shadow-card-hover">
      <div className="flex items-start justify-between">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          {label}
        </span>
        {Icon && (
          <span className="rounded-lg bg-brand-50 p-2 text-brand-600">
            <Icon size={18} />
          </span>
        )}
      </div>

      <p className="mt-3 text-3xl font-bold text-slate-900 nums">{value}</p>

      {subeObaja && (
        <p
          className={`mt-1 flex items-center gap-1 text-xs font-semibold ${
            subeObaja === "up" ? "text-success-strong" : "text-danger-strong"
          }`}
        >
          {subeObaja === "up" ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
          {Math.abs(delta)}% vs. ayer
        </p>
      )}
      {!subeObaja && hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
    </div>
  );
}
