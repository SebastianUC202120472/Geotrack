// Tarjeta blanca estándar (superficie del panel). Borde y sombra suaves desde
// los tokens del sistema. Opcionalmente acepta título y acción en la cabecera.
// Entrada: title, subtitle, action (nodo a la derecha de la cabecera),
//   hover (bool: eleva al pasar el mouse), className, children.
export default function Card({ title, subtitle, action, hover = false, className = "", children }) {
  const interaccion = hover
    ? "transition-all duration-200 hover:-translate-y-0.5 hover:shadow-card-hover"
    : "";
  return (
    <section
      className={`bg-white border border-warm-200 rounded-card shadow-card ${interaccion} ${className}`}
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
