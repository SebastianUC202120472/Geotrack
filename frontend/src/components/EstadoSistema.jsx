import { useEffect, useState } from "react";
import { CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { obtenerResumen } from "../services/api";

// Refleja el estado real de la conexión con el backend. Si el resumen del
// dashboard responde, la API y la base de datos están operativas.
export default function EstadoSistema() {
  const [estado, setEstado] = useState("verificando"); // verificando | ok | error

  useEffect(() => {
    obtenerResumen()
      .then(() => setEstado("ok"))
      .catch(() => setEstado("error"));
  }, []);

  const items = [
    { etiqueta: "API del servidor", ok: estado === "ok" },
    { etiqueta: "Base de datos conectada", ok: estado === "ok" },
  ];

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
      <h2 className="text-xl font-bold mb-4">Estado del Sistema</h2>

      {estado === "verificando" ? (
        <div className="flex items-center gap-3 text-slate-500">
          <Loader2 className="animate-spin" size={18} /> Verificando conexión...
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <div
              key={item.etiqueta}
              className={`flex items-center gap-3 p-3 rounded-xl ${
                item.ok ? "bg-green-50" : "bg-red-50"
              }`}
            >
              {item.ok ? (
                <CheckCircle2 className="text-green-600" />
              ) : (
                <XCircle className="text-red-500" />
              )}
              <span>{item.etiqueta}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
