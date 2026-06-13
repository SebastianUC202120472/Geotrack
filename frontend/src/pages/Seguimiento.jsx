import { useEffect, useState } from "react";
import { RefreshCw, Truck, CheckCircle2, XCircle, Clock } from "lucide-react";
import Header from "../components/Header";
import { obtenerFlota } from "../services/api";

// Seguimiento de la flota (CUS-33). Muestra el avance de cada ruta a partir de
// /api/dashboard/flota. Como el backend aún no expone WebSocket, el refresco es
// bajo demanda con el botón "Actualizar" (no hay tracking en vivo todavía).
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

  const colorEstado = (estado) =>
    ({
      CREADA: "bg-slate-100 text-slate-600",
      EN_PROGRESO: "bg-blue-100 text-blue-700",
      FINALIZADA: "bg-green-100 text-green-700",
    }[estado] || "bg-slate-100 text-slate-600");

  return (
    <div className="min-h-screen flex flex-col">
      <Header titulo="Seguimiento de Flota" subtitulo="Avance de las rutas en operación (CUS-33)" />

      <main className="flex-grow p-8 space-y-6">
        <div className="flex justify-end">
          <button
            onClick={cargar}
            className="flex items-center gap-2 bg-indigo-600 text-white px-5 py-3 rounded-xl hover:bg-indigo-700 transition"
          >
            <RefreshCw size={18} /> Actualizar
          </button>
        </div>

        {cargando ? (
          <p className="text-center py-16 text-slate-500">Cargando rutas...</p>
        ) : rutas.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-16 text-center text-slate-400 shadow-sm">
            <Truck className="mx-auto mb-3 opacity-40" size={40} />
            <p>No hay rutas en operación todavía. Asigna un bloque de pedidos para verlas aquí.</p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
            {rutas.map((r) => (
              <div key={r.ruta_id} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="font-bold text-slate-800">{r.nombre}</h3>
                    <p className="text-sm text-slate-500">{r.vehiculo_placa || "Sin vehículo"}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${colorEstado(r.estado)}`}>
                    {r.estado}
                  </span>
                </div>

                {/* Barra de avance */}
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-slate-500 mb-1">
                    <span>Avance</span>
                    <span className="font-semibold text-slate-700">{Math.round(r.avance_porcentaje)}%</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-600 rounded-full transition-all"
                      style={{ width: `${r.avance_porcentaje}%` }}
                    />
                  </div>
                </div>

                {/* Contadores */}
                <div className="grid grid-cols-3 gap-2 text-center text-sm">
                  <Contador icon={CheckCircle2} color="text-green-600" valor={r.entregadas} etiqueta="Entregadas" />
                  <Contador icon={XCircle} color="text-red-500" valor={r.fallidas} etiqueta="Fallidas" />
                  <Contador icon={Clock} color="text-amber-500" valor={r.pendientes} etiqueta="Pendientes" />
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

function Contador({ icon: Icon, color, valor, etiqueta }) {
  return (
    <div className="bg-slate-50 rounded-xl py-3">
      <Icon className={`mx-auto ${color}`} size={18} />
      <p className="text-lg font-bold text-slate-800 mt-1">{valor}</p>
      <p className="text-xs text-slate-400">{etiqueta}</p>
    </div>
  );
}
