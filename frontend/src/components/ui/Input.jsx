// Campo de formulario con label, error y soporte para input/select/textarea via prop "as".
import { useId } from "react";

export default function Input({
  label,
  as = "input",
  className = "",
  hint,
  error,
  children,
  ...props
}) {
  const id = useId();
  const Tag = as;

  const borde = error
    ? "border-danger focus:border-danger focus:ring-danger/30"
    : "border-slate-200 focus:border-brand-500 focus:ring-brand-500/30";

  return (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-slate-700">
          {label}
        </label>
      )}
      <Tag
        id={id}
        aria-invalid={error ? "true" : undefined}
        className={`w-full rounded-xl border bg-white px-3.5 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 outline-none transition focus:ring-2 ${borde} ${className}`}
        {...props}
      >
        {children}
      </Tag>
      {error ? (
        <p className="text-xs font-medium text-danger-strong">{error}</p>
      ) : hint ? (
        <p className="text-xs text-slate-400">{hint}</p>
      ) : null}
    </div>
  );
}
