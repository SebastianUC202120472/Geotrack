import { useEffect, useState } from "react";
import { RefreshCw, Truck, CircleCheck, CircleX, Clock } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import { EstadoBadge } from "../components/ui/Badge";
import { obtenerFlota } from "../services/api";

// Seguimiento de la flota (CUS-33): avance de cada ruta desde /dashboard/flota.
// El backend aún no expone WebSocket, así que el refresco es con el botón
// "Actualizar" (todavía no hay tracking en vivo).
export default function Seguimiento() {
  const [rutas, setRutas] = useState([]);
  const [cargando, setCargando] = useState(true);

  const cargar = async () => {
    setCargando(true);
    try {
      const data = await obtenerFlota();
      setRutas(data.rutas || []);
    } catch (err) {
      console.error("No se pudo cargar el seguimiento:", err.message);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargar();
  }, []);

  return (
    <div className="space-y-6 p-6 lg:p-8">
      <PageHeader titulo="Seguimiento de Flota" subtitulo="Avance de las rutas en operación (CUS-33).">
        <Button variant="secondary" icon={RefreshCw} onClick={cargar}>Actualizar</Button>
      </PageHeader>

      {cargando ? (
        <Card><p className="py-10 text-center text-sm text-slate-500">Cargando rutas…</p></Card>
      ) : rutas.length === 0 ? (
        <Card>
          <div className="py-12 text-center text-sm text-slate-400">
            <Truck className="mx-auto mb-3 opacity-40" size={36} />
            <p>No hay rutas en operación todavía. Asigna un bloque de pedidos para verlas aquí.</p>
          </div>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {rutas.map((r) => (
            <Card key={r.ruta_id}>
              <div className="mb-4 flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-slate-900">{r.nombre}</h3>
                  <p className="text-sm text-slate-500">{r.vehiculo_placa || "Sin vehículo"}</p>
                </div>
                <EstadoBadge estado={r.estado} />
              </div>

              <div className="mb-4">
                <div className="mb-1 flex justify-between text-sm">
                  <span className="text-slate-500">Avance</span>
                  <span className="font-semibold text-slate-700 nums">{Math.round(r.avance_porcentaje)}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full rounded-full bg-brand-600 transition-all" style={{ width: `${r.avance_porcentaje}%` }} />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center">
                <Contador icon={CircleCheck} color="text-success" valor={r.entregadas} etiqueta="Entregadas" />
                <Contador icon={CircleX} color="text-danger" valor={r.fallidas} etiqueta="Fallidas" />
                <Contador icon={Clock} color="text-warning" valor={r.pendientes} etiqueta="Pendientes" />
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function Contador({ icon: Icon, color, valor, etiqueta }) {
  return (
    <div className="rounded-xl bg-slate-50 py-3">
      <Icon className={`mx-auto ${color}`} size={18} />
      <p className="mt-1 text-lg font-bold text-slate-800 nums">{valor}</p>
      <p className="text-xs text-slate-400">{etiqueta}</p>
    </div>
  );
}
