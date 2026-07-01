// Chip de estado con punto pulsante. Recibe tone, pulse y children.
const tonos = {
  brand: { chip: "bg-brand-50 text-brand-700", dot: "bg-brand-500 text-brand-500" },
  success: { chip: "bg-success-soft text-success-strong", dot: "bg-success text-success" },
  info: { chip: "bg-info-soft text-info-strong", dot: "bg-info text-info" },
  warning: { chip: "bg-warning-soft text-warning-strong", dot: "bg-warning text-warning" },
  danger: { chip: "bg-danger-soft text-danger-strong", dot: "bg-danger text-danger" },
  neutral: { chip: "bg-slate-100 text-slate-600", dot: "bg-slate-400 text-slate-400" },
};

export default function LiveBadge({ tone = "success", pulse = true, children }) {
  const t = tonos[tone] || tonos.success;
  return (
    <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${t.chip}`}>
      <span className={`h-2 w-2 rounded-full ${t.dot} ${pulse ? "live-dot" : ""}`} aria-hidden="true" />
      {children}
    </span>
  );
}
