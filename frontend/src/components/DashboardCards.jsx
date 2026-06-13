import { useEffect, useState } from "react";
import {
  Package,
  Truck,
  CheckCircle
} from "lucide-react";

import { obtenerResumen } from "../services/api";

export default function DashboardCards() {

  const [resumen, setResumen] = useState(null);

  useEffect(() => {
    cargarResumen();
  }, []);

  const cargarResumen = async () => {
    try {
      const data = await obtenerResumen();
      setResumen(data);
    } catch (error) {
      console.log(error);
    }
  };

  if (!resumen) {
    return (
      <div className="grid md:grid-cols-3 gap-5">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="bg-white rounded-2xl border border-slate-200 p-6 animate-pulse h-28"
          />
        ))}
      </div>
    );
  }

  const porcentajeRutas =
    resumen.total_rutas === 0
      ? 0
      : Math.round(
          (resumen.rutas_finalizadas /
            resumen.total_rutas) *
            100
        );

  const cards = [
    {
      titulo: "Pedidos Totales",
      valor: resumen.total_pedidos,
      icono: Package,
    },
    {
      titulo: "Rutas Activas",
      valor: resumen.rutas_activas,
      icono: Truck,
    },
    {
      titulo: "Rutas Finalizadas",
      valor: `${porcentajeRutas}%`,
      icono: CheckCircle,
    },
  ];

  return (
    <div className="grid md:grid-cols-3 gap-5">

      {cards.map((card) => {

        const Icon = card.icono;

        return (
          <div
            key={card.titulo}
            className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition"
          >

            <div className="flex justify-between items-center">

              <div>

                <p className="text-slate-500">
                  {card.titulo}
                </p>

                <h2 className="text-4xl font-bold mt-2 text-slate-800">
                  {card.valor}
                </h2>

              </div>

              <div className="bg-blue-100 p-4 rounded-xl">
                <Icon
                  size={30}
                  className="text-blue-600"
                />
              </div>

            </div>

          </div>
        );

      })}

    </div>
  );
}