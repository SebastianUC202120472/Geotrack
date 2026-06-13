import { useState } from "react";
import { Map, Navigation, Loader2, CheckCircle, AlertCircle, MapPin, Truck } from "lucide-react";
import { optimizarRutaConductor } from "../services/api";

export default function EjecucionEnrutamiento() {
  const [rutaId, setRutaId] = useState("");
  const [latitud, setLatitud] = useState("");
  const [longitud, setLongitud] = useState("");
  const [loading, setLoading] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState("");

  const obtenerUbicacion = () => {
    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLatitud(pos.coords.latitude.toFixed(6));
        setLongitud(pos.coords.longitude.toFixed(6));
        setLoading(false);
      },
      () => {
        setError("No se pudo obtener la ubicación. Por favor, activa el GPS.");
        setLoading(false);
      }
    );
  };

  const ejecutarVRP = async () => {
    if (!rutaId || !latitud || !longitud) {
      setError("Por favor, completa el ID de ruta y tu ubicación actual.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await optimizarRutaConductor({
        ruta_id: Number(rutaId),
        latitud_actual_conductor: Number(latitud),
        longitud_actual_conductor: Number(longitud),
      });
      setResultado(response);
    } catch (err) {
      setError(err.message || "Error al optimizar la ruta.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <main className="max-w-6xl mx-auto space-y-6">
        
        {/* HEADER */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="p-4 bg-indigo-600 text-white rounded-2xl">
            <Map size={28} />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Optimización de Ruta (VRP)</h1>
            <p className="text-slate-500">Reordena tu secuencia de entregas basándose en tu posición actual.</p>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {/* PANEL DE CONTROL */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h2 className="font-bold text-lg text-slate-800 mb-2">Configuración</h2>
            
            <input
              className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none"
              placeholder="ID de ruta activa"
              value={rutaId}
              onChange={(e) => setRutaId(e.target.value)}
            />

            <div className="grid grid-cols-2 gap-3">
              <input className="p-3 bg-slate-50 border border-slate-200 rounded-xl" placeholder="Latitud" value={latitud} readOnly />
              <input className="p-3 bg-slate-50 border border-slate-200 rounded-xl" placeholder="Longitud" value={longitud} readOnly />
            </div>

            <button
              onClick={obtenerUbicacion}
              className="w-full flex items-center justify-center gap-2 bg-slate-100 text-slate-700 font-semibold p-3 rounded-xl hover:bg-slate-200 transition"
            >
              <MapPin size={18} /> Obtener ubicación GPS
            </button>

            <button
              onClick={ejecutarVRP}
              disabled={loading}
              className="w-full bg-indigo-600 text-white font-bold p-4 rounded-xl flex items-center justify-center gap-2 hover:bg-indigo-700 transition shadow-lg shadow-indigo-200"
            >
              {loading ? <Loader2 className="animate-spin" /> : <Navigation size={20} />}
              {loading ? "Calculando..." : "Optimizar Ruta ahora"}
            </button>
          </div>

          {/* PANEL DE RESULTADOS */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h2 className="font-bold text-lg text-slate-800 mb-4">Secuencia Optimizada</h2>

            {error && (
              <div className="flex items-center gap-3 p-4 bg-red-50 text-red-700 rounded-xl border border-red-100">
                <AlertCircle size={20} /> {error}
              </div>
            )}

            {resultado ? (
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-green-600 font-bold bg-green-50 p-3 rounded-lg">
                  <CheckCircle size={20} /> Optimización exitosa
                </div>
                <div className="text-slate-600">
                  <p>La nueva ruta cuenta con <b>{resultado.total_paradas}</b> paradas.</p>
                </div>
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 max-h-80 overflow-y-auto font-mono text-xs">
                  {JSON.stringify(resultado.ruta_optimizada || resultado, null, 2)}
                </div>
              </div>
            ) : (
              <div className="h-64 flex flex-col items-center justify-center text-slate-400 border-2 border-dashed border-slate-100 rounded-xl">
                <Truck size={40} className="mb-2 opacity-50" />
                <p>Esperando datos de optimización...</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}