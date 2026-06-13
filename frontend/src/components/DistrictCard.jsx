import { MapPin, Package } from "lucide-react";

// Tarjeta de un distrito con su conteo de pedidos.
export default function DistrictCard({ distrito, pedidos }) {
  return (
    <div className="flex items-center gap-4 rounded-card border border-slate-200 bg-white p-4 shadow-card transition-shadow hover:shadow-card-hover">
      <span className="rounded-xl bg-brand-50 p-3 text-brand-600">
        <MapPin size={22} />
      </span>
      <div>
        <h3 className="font-semibold text-slate-800">{distrito || "Sin distrito"}</h3>
        <p className="mt-0.5 flex items-center gap-1.5 text-sm text-slate-500">
          <Package size={15} /> <span className="nums">{pedidos}</span> pedidos
        </p>
      </div>
    </div>
  );
}
