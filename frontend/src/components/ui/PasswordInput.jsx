// Campo de contraseña con toggle de visibilidad y soporte de error/hint.
import { useId, useState } from "react";
import { Eye, EyeOff } from "lucide-react";

export default function PasswordInput({ label, error, hint, className = "", ...props }) {
  const id = useId();
  const [visible, setVisible] = useState(false);

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
      <div className="relative">
        <input
          id={id}
          type={visible ? "text" : "password"}
          aria-invalid={error ? "true" : undefined}
          className={`w-full rounded-xl border bg-white py-2.5 pl-3.5 pr-11 text-sm text-slate-800 placeholder:text-slate-400 outline-none transition focus:ring-2 ${borde} ${className}`}
          {...props}
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? "Ocultar contraseña" : "Mostrar contraseña"}
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
        >
          {visible ? <EyeOff size={18} /> : <Eye size={18} />}
        </button>
      </div>
      {error ? (
        <p className="text-xs font-medium text-danger-strong">{error}</p>
      ) : hint ? (
        <p className="text-xs text-slate-400">{hint}</p>
      ) : null}
    </div>
  );
}
