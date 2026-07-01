import { useEffect, useState } from "react";
import { CircleCheck, CircleX, Loader2 } from "lucide-react";
import Card from "./ui/Card";
import { obtenerResumen } from "../services/api";

// Muestra el estado de la API y la BD consultando el resumen del dashboard.
export default function EstadoSistema() {
  const [estado, setEstado] = useState("verificando"); // verificando | ok | error

  useEffect(() => {
    obtenerResumen().then(() => setEstado("ok")).catch(() => setEstado("error"));
  }, []);

  const items = [
    { etiqueta: "API del servidor", ok: estado === "ok" },
    { etiqueta: "Base de datos conectada", ok: estado === "ok" },
  ];

  return (
    <Card title="Estado del sistema">
      {estado === "verificando" ? (
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Loader2 className="animate-spin" size={18} /> Verificando conexión…
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <div
              key={item.etiqueta}
              className={`flex items-center gap-3 rounded-xl px-3.5 py-3 text-sm font-medium ${
                item.ok ? "bg-success-soft text-success-strong" : "bg-danger-soft text-danger-strong"
              }`}
            >
              {item.ok ? <CircleCheck size={18} /> : <CircleX size={18} />}
              <span>{item.etiqueta}</span>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
