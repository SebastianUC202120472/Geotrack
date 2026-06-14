import { MapPin, ChevronRight } from "lucide-react";

// Carta de una zona (distrito): muestra el desglose de pedidos PENDIENTES y
// ASIGNADOS con su color, visible sin hacer clic. Cada conteo es clicable y
// lleva al listado de pedidos ya filtrado por ese estado en el distrito; la
// cabecera abre el distrito completo.
// Entrada:
//   distrito (string), pendientes (number), asignados (number),
//   onVerPendientes (fn), onVerAsignados (fn), onAbrir (fn: abre la zona completa).
const tonos = {
  warning: { caja: "bg-warning-soft hover:bg-warning/20", punto: "bg-warning", texto: "text-warning-strong" },
  info: { caja: "bg-info-soft hover:bg-info/20", punto: "bg-info", texto: "text-info-strong" },
};

// Conteo clicable de un estado dentro de la zona (color + número + etiqueta).
// Se deshabilita cuando el valor es 0 (no hay nada que listar).
function ConteoEstado({ tono, label, valor, onClick }) {
  const t = tonos[tono];
  return (
    <button
      onClick={onClick}
      disabled={!valor}
      className={`flex items-center gap-2 rounded-xl px-3 py-2 text-left transition-colors disabled:cursor-default disabled:opacity-50 ${t.caja}`}
    >
      <span className={`h-2 w-2 rounded-full ${t.punto}`} />
      <span className={`text-lg font-bold nums ${t.texto}`}>{valor}</span>
      <span className="text-xs font-medium text-slate-500">{label}</span>
    </button>
  );
}

export default function DistrictCard({ distrito, pendientes, asignados, onVerPendientes, onVerAsignados, onAbrir }) {
  return (
    <div className="rounded-card border border-slate-200 bg-white p-4 shadow-card transition-all duration-200 hover:-translate-y-0.5 hover:shadow-card-hover">
      <button onClick={onAbrir} className="flex w-full items-center gap-3 text-left">
        <span className="rounded-xl bg-brand-50 p-2.5 text-brand-600">
          <MapPin size={20} />
        </span>
        <h3 className="flex-1 font-semibold text-slate-800">{distrito || "Sin distrito"}</h3>
        <ChevronRight size={18} className="text-slate-300" />
      </button>

      <div className="mt-3 grid grid-cols-2 gap-2">
        <ConteoEstado tono="warning" label="Pendientes" valor={pendientes} onClick={onVerPendientes} />
        <ConteoEstado tono="info" label="Asignados" valor={asignados} onClick={onVerAsignados} />
      </div>
    </div>
  );
}
