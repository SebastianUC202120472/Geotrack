import { useState } from "react";
import { Truck, Building2 } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import LiveBadge from "../components/ui/LiveBadge";
import VistaPorRuta from "../components/seguimiento/VistaPorRuta";
import VistaPorCliente from "../components/seguimiento/VistaPorCliente";

// Seguimiento de PEDIDOS con dos vistas (pestañas):
//  - "Por ruta": avance de cada ruta (CUS-33, /dashboard/flota).
//  - "Por cliente": repartos agregados por empresa (/dashboard/clientes).
// (El mapa con la ubicación de los conductores vive en "Seguimiento de Conductores".)
const PESTANAS = [
  { id: "ruta", label: "Por ruta", icon: Truck },
  { id: "cliente", label: "Por cliente", icon: Building2 },
];

export default function Seguimiento() {
  const [tab, setTab] = useState("ruta");

  return (
    <div className="space-y-6 p-6 lg:p-8">
      {/* Cabecera */}
      <div className="animate-fade-up">
        <PageHeader
          titulo="Seguimiento"
          subtitulo="Avance de las operaciones de reparto por ruta y por cliente."
        >
          <LiveBadge tone="success" pulse>
            En vivo
          </LiveBadge>
        </PageHeader>
      </div>

      {/* Selector de pestañas moderno */}
      <div className="animate-fade-up" style={{ animationDelay: "60ms" }}>
        <div className="inline-flex items-center gap-1 rounded-2xl border border-warm-200 bg-white p-1 shadow-card">
          {PESTANAS.map((p) => {
            const Ico = p.icon;
            const activo = tab === p.id;
            return (
              <button
                key={p.id}
                onClick={() => setTab(p.id)}
                className={`inline-flex items-center gap-2 rounded-xl px-5 py-2 text-sm font-semibold transition-all duration-200 ${
                  activo
                    ? "bg-brand-600 text-white shadow-sm"
                    : "text-slate-500 hover:bg-slate-50 hover:text-slate-800"
                }`}
              >
                <Ico size={15} />
                {p.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Contenido principal — delegado a los componentes autocontenidos */}
      <div className="animate-fade-up" style={{ animationDelay: "120ms" }}>
        {tab === "ruta" ? <VistaPorRuta /> : <VistaPorCliente />}
      </div>
    </div>
  );
}
