import { MapPinned, Package } from "lucide-react";

export default function DistrictCard({
  distrito,
  pedidos,
}) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:shadow-lg transition-all">

      <div className="flex items-center gap-4">

        <div className="bg-indigo-100 p-4 rounded-xl">
          <MapPinned className="text-indigo-600" />
        </div>

        <div>
          <h3 className="text-lg font-bold text-slate-800">
            {distrito || "Sin distrito"}
          </h3>

          <div className="flex items-center gap-2 mt-2 text-slate-500">
            <Package size={16} />
            <span>{pedidos} pedidos</span>
          </div>
        </div>

      </div>

    </div>
  );
}