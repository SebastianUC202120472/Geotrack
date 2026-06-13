import { CheckCircle2 } from "lucide-react";

export default function EstadoSistema() {
  const estados = [
    "Servidor Operativo",
    "Base de Datos Conectada",
    "Servicio Excel Disponible",
  ];

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
      <h2 className="text-xl font-bold mb-4">
        Estado del Sistema
      </h2>

      <div className="space-y-3">
        {estados.map((item) => (
          <div
            key={item}
            className="flex items-center gap-3 bg-green-50 p-3 rounded-xl"
          >
            <CheckCircle2 className="text-green-600" />
            <span>{item}</span>
          </div>
        ))}
      </div>
    </div>
  );
}