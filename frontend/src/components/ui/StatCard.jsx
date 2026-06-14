import useCountUp from "../../hooks/useCountUp";

// Tono -> clases (chip de icono + relleno de barra). Por defecto, marca (azul).
const tonos = {
  brand: { chip: "bg-brand-50 text-brand-600", barra: "bg-brand-600" },
  info: { chip: "bg-info-soft text-info-strong", barra: "bg-info" },
  success: { chip: "bg-success-soft text-success-strong", barra: "bg-success" },
  warning: { chip: "bg-warning-soft text-warning-strong", barra: "bg-warning" },
  danger: { chip: "bg-danger-soft text-danger-strong", barra: "bg-danger" },
};

// Tarjeta de KPI: etiqueta, número grande (animado), icono en chip y, opcional,
// una barra de progreso real (progress 0–100) o un texto de apoyo (hint).
// Entrada:
//   label (string), value (number | string), icon (componente lucide),
//   tone ("brand"|"info"|"success"|"warning"|"danger"), progress (0–100, opcional),
//   progressLabel (string bajo la barra, opcional), hint (string, opcional).
export default function StatCard({
  label,
  value,
  icon: Icon,
  tone = "brand",
  progress,
  progressLabel,
  hint,
}) {
  const animado = useCountUp(value);
  const t = tonos[tone] || tonos.brand;
  const tieneBarra = typeof progress === "number";
  const ancho = Math.max(0, Math.min(100, progress ?? 0));

  return (
    <div className="bg-white border border-slate-200 rounded-card shadow-card p-5 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-card-hover">
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

      {tieneBarra ? (
        <div className="mt-3">
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className={`h-full rounded-full transition-[width] duration-700 ${t.barra}`}
              style={{ width: `${ancho}%` }}
            />
          </div>
          {progressLabel && <p className="mt-1.5 text-xs text-slate-400">{progressLabel}</p>}
        </div>
      ) : (
        hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>
      )}
    </div>
  );
}
