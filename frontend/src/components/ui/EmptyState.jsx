// Estado vacío reutilizable: ilustración SVG + título + descripción + acción.
// Evita pantallas en blanco cuando no hay datos.
// Entrada: icon (componente lucide opcional), title, description, action (nodo).
export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-14 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-50 text-brand-600">
        {Icon ? <Icon size={28} /> : <span className="text-2xl font-bold">∅</span>}
      </div>
      <h3 className="text-base font-semibold text-slate-900">{title}</h3>
      {description && (
        <p className="mt-1 max-w-sm text-sm text-slate-500">{description}</p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
