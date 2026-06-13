// Campo de formulario con etiqueta asociada (accesibilidad: el label apunta al
// input por id) y foco visible. Sirve para <input> y, con "as", para <select>.
import { useId } from "react";

export default function Input({
  label,
  as = "input",
  className = "",
  hint,
  children,
  ...props
}) {
  const id = useId();
  const Tag = as;

  return (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-slate-700">
          {label}
        </label>
      )}
      <Tag
        id={id}
        className={`w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30 ${className}`}
        {...props}
      >
        {children}
      </Tag>
      {hint && <p className="text-xs text-slate-400">{hint}</p>}
    </div>
  );
}
