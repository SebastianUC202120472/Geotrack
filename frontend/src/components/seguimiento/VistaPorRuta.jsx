import { useEffect, useState } from "react";
import { Truck, CircleCheck, CircleX, Clock, FileSpreadsheet, Loader2 } from "lucide-react";
import Card from "../ui/Card";
import SectionCard from "../ui/SectionCard";
import EmptyState from "../ui/EmptyState";
import Button from "../ui/Button";
import { EstadoBadge } from "../ui/Badge";
import { obtenerFlota, descargarManifiesto } from "../../services/api";

// Carga y muestra el avance de cada ruta activa (CUS-33).
// Sin props: autocontenido; carga datos con obtenerFlota() al montar.
export default function VistaPorRuta() {
  const [rutas, setRutas] = useState(null);
  const [cargando, setCargando] = useState(true);

  // Solicita la lista de rutas activas al montar; setState solo dentro de callbacks.
  useEffect(() => {
    let activo = true;
    obtenerFlota()
      .then((data) => { if (activo) setRutas(data.rutas || []); })
      .catch((err) => {
        console.error("No se pudo cargar las rutas:", err.message);
        if (activo) setRutas([]);
      })
      .finally(() => { if (activo) setCargando(false); });
    return () => { activo = false; };
  }, []);

  if (cargando) {
    return (
      <SectionCard>
        <div className="flex justify-center py-12 text-slate-400">
          <Loader2 className="animate-spin" size={24} />
        </div>
      </SectionCard>
    );
  }

  if (!rutas || rutas.length === 0) {
    return (
      <SectionCard title="Rutas en operación">
        <EmptyState
          icon={Truck}
          title="Sin rutas activas"
          description="Asigna un bloque de pedidos para ver el avance de cada ruta aquí."
        />
      </SectionCard>
    );
  }

  return (
    <SectionCard
      title="Rutas en operación"
      subtitle={`${rutas.length} ruta${rutas.length !== 1 ? "s" : ""} activa${rutas.length !== 1 ? "s" : ""}`}
    >
      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {rutas.map((r, i) => (
          <div key={r.ruta_id} style={{ animationDelay: `${i * 40}ms` }} className="animate-fade-up">
            <Card hover>
              <div className="mb-4 flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-slate-900">{r.nombre}</h3>
                  <p className="text-sm text-slate-500">{r.conductor_nombre || "Sin conductor"}</p>
                </div>
                <EstadoBadge estado={r.estado} />
              </div>

              {/* Barra de progreso de la ruta */}
              <div className="mb-4">
                <div className="mb-1 flex justify-between text-sm">
                  <span className="text-slate-500">Avance</span>
                  <span className="font-semibold text-slate-700 nums">
                    {Math.round(r.avance_porcentaje)}%
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-brand-600 transition-all"
                    style={{ width: `${r.avance_porcentaje}%` }}
                  />
                </div>
              </div>

              {/* Contadores de entregadas / fallidas / pendientes */}
              <div className="grid grid-cols-3 gap-2 text-center">
                <Contador icon={CircleCheck} color="text-success" valor={r.entregadas} etiqueta="Entregadas" />
                <Contador icon={CircleX} color="text-danger" valor={r.fallidas} etiqueta="Fallidas" />
                <Contador icon={Clock} color="text-warning" valor={r.pendientes} etiqueta="Pendientes" />
              </div>

              {/* CUS-21: descargar manifiesto de carga en Excel */}
              <div className="mt-4 flex gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  icon={FileSpreadsheet}
                  onClick={() => descargarManifiesto(r.ruta_id, `manifiesto_${r.nombre}.xlsx`)}
                >
                  Manifiesto
                </Button>
              </div>
            </Card>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}

// Minibloque de conteo dentro de la tarjeta de ruta (icono + número + etiqueta).
// Entrada: icon (componente lucide), color (clase css), valor (number), etiqueta (string).
function Contador({ icon: Icon, color, valor, etiqueta }) {
  return (
    <div className="rounded-xl bg-slate-50 py-3 transition-colors hover:bg-brand-50">
      <Icon className={`mx-auto ${color}`} size={18} />
      <p className="mt-1 text-lg font-bold text-slate-800 nums">{valor}</p>
      <p className="text-xs text-slate-400">{etiqueta}</p>
    </div>
  );
}
