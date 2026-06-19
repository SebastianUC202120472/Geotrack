// Tarjeta de sección: cabecera (título + subtítulo + acción) + cuerpo.
// Más flexible que Card para secciones de dashboard/reportes.
// Entrada: title, subtitle, action (nodo a la derecha), className, children.
export default function SectionCard({ title, subtitle, action, className = "", children }) {
  return (
    <section className={`rounded-card border border-slate-200 bg-white shadow-card ${className}`}>
      {(title || action) && (
        <header className="flex items-center justify-between gap-4 px-5 py-4 border-b border-slate-100">
          <div>
            {title && <h2 className="text-sm font-bold text-slate-900">{title}</h2>}
            {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
          </div>
          {action}
        </header>
      )}
      <div className="p-5">{children}</div>
    </section>
  );
}
