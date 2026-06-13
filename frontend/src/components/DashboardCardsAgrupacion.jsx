import {
  Map,
  Package,
  Truck
} from "lucide-react";

export default function DashboardCardsAgrupacion() {

  const cards = [
    {
      titulo: "Distritos",
      valor: 8,
      icon: Map
    },
    {
      titulo: "Pedidos",
      valor: 1245,
      icon: Package
    },
    {
      titulo: "Rutas",
      valor: 12,
      icon: Truck
    }
  ];

  return (
    <div className="grid md:grid-cols-3 gap-5">

      {cards.map((card) => {

        const Icon = card.icon;

        return (
          <div
            key={card.titulo}
            className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm"
          >

            <div className="flex justify-between">

              <div>
                <p className="text-slate-500">
                  {card.titulo}
                </p>

                <h2 className="text-3xl font-bold mt-2">
                  {card.valor}
                </h2>
              </div>

              <div className="bg-indigo-100 p-4 rounded-xl">
                <Icon className="text-indigo-600" />
              </div>

            </div>

          </div>
        );

      })}

    </div>
  );
}