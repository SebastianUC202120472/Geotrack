const variantes = {
  primary:
    "bg-brand-600 text-white shadow-[0_6px_16px_rgba(37,99,235,0.25)] hover:bg-brand-700 hover:shadow-[0_8px_20px_rgba(37,99,235,0.32)] focus-visible:ring-brand-600",
  secondary:
    "bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 focus-visible:ring-brand-600",
  ghost:
    "bg-transparent text-slate-600 hover:bg-slate-100 focus-visible:ring-brand-600",
  danger:
    "bg-danger text-white hover:bg-danger-strong focus-visible:ring-danger",
};

const tamanos = {
  sm: "text-sm px-3 py-2 gap-1.5",
  md: "text-sm px-4 py-2.5 gap-2",
  lg: "text-base px-5 py-3 gap-2",
};

// Boton reutilizable. Recibe variant, size, icon, block, className y props HTML de button.
export default function Button({
  variant = "primary",
  size = "md",
  icon: Icon,
  block = false,
  className = "",
  children,
  ...props
}) {
  return (
    <button
      className={`inline-flex items-center justify-center font-semibold rounded-xl transition-colors outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-60 disabled:cursor-not-allowed ${variantes[variant]} ${tamanos[size]} ${block ? "w-full" : ""} ${className}`}
      {...props}
    >
      {Icon && <Icon size={size === "lg" ? 20 : 18} />}
      {children}
    </button>
  );
}
