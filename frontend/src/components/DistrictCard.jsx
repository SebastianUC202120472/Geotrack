import { MapPin, Package, ChevronRight } from "lucide-react";

// Tarjeta de un distrito con su conteo de pedidos. Si recibe onClick, se vuelve
// un botón (para ir a los pedidos de esa zona).
export default function DistrictCard({ distrito, pedidos, onClick }) {
  const contenido = (
    <>
      <span className="rounded-xl bg-brand-50 p-3 text-brand-600">
        <MapPin size={22} />
      </span>
      <div className="flex-1">
        <h3 className="font-semibold text-slate-800">{distrito || "Sin distrito"}</h3>
        <p className="mt-0.5 flex items-center gap-1.5 text-sm text-slate-500">
          <Package size={15} /> <span className="nums">{pedidos}</span> pedidos
        </p>
      </div>
      {onClick && <ChevronRight size={18} className="text-slate-300" />}
    </>
  );

  const clases =
    "flex w-full items-center gap-4 rounded-card border border-slate-200 bg-white p-4 text-left shadow-card transition-shadow hover:shadow-card-hover";

  if (onClick) {
    return <button onClick={onClick} className={`${clases} hover:border-brand-300`}>{contenido}</button>;
  }
  return <div className={clases}>{contenido}</div>;
}
