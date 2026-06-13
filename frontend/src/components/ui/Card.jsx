// Tarjeta blanca estándar (superficie del panel). Borde y sombra suaves desde
// los tokens del sistema. Opcionalmente acepta título y acción en la cabecera.
export default function Card({ title, subtitle, action, className = "", children }) {
  return (
    <section
      className={`bg-white border border-slate-200 rounded-card shadow-card ${className}`}
    >
      {(title || action) && (
        <header className="flex items-center justify-between gap-4 px-6 py-4 border-b border-slate-100">
          <div>
            {title && <h2 className="text-base font-semibold text-slate-900">{title}</h2>}
            {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
          </div>
          {action}
        </header>
      )}
      <div className="p-6">{children}</div>
    </section>
  );
}
