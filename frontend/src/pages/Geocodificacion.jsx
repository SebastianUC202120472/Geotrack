import { useState } from "react";
import Header from "../components/Header";
import { 
  MapPinned, 
  LocateFixed, 
  Loader2, 
  CheckCircle, 
  AlertCircle
} from "lucide-react";
import { procesarGeocodificacion } from "../services/api";

export default function Geocodificacion() {
  const [loading, setLoading] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState("");

  const ejecutar = async () => {
    setLoading(true);
    setError("");
    setResultado(null);

    try {
      const response = await procesarGeocodificacion();
      setResultado(response);
    } catch (err) {
      setError(err.message || "Error al procesar la geocodificación");
    } finally {
      setLoading(false);
    }
  };

  return (
    // min-h-screen y flex flex-col para ocupar toda la altura
    <div className="min-h-screen w-full bg-slate-50 flex flex-col">
      <Header />

      {/* main con flex-grow para expandirse */}
      <main className="flex-grow w-full p-8 flex flex-col space-y-6">
        
        {/* Título */}
        <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
          <h1 className="text-3xl font-extrabold text-slate-900">Geocodificación Automática</h1>
          <p className="text-slate-500 mt-2">
            Convierte direcciones de clientes en coordenadas precisas para la optimización logística.
          </p>
        </div>

        {/* Panel de Acción: flex-grow para ocupar el resto de la pantalla */}
        <div className="bg-white rounded-2xl border border-slate-200 p-10 flex-grow flex flex-col items-center justify-center shadow-sm">
          <div className="w-24 h-24 bg-indigo-50 flex items-center justify-center rounded-full mb-6">
            <MapPinned size={40} className="text-indigo-600" />
          </div>

          <h2 className="text-2xl font-bold text-slate-800">¿Listo para procesar?</h2>
          <p className="text-slate-500 mt-2 text-center max-w-lg">
            Este proceso tomará todas las direcciones importadas y buscará sus coordenadas geográficas automáticamente.
          </p>

          <button
            onClick={ejecutar}
            disabled={loading}
            className="mt-8 bg-indigo-600 hover:bg-indigo-700 text-white px-10 py-5 rounded-xl font-bold flex items-center gap-3 transition-all shadow-lg shadow-indigo-200 text-lg"
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin" /> Procesando datos...
              </>
            ) : (
              <>
                <LocateFixed size={22} /> Iniciar geocodificación
              </>
            )}
          </button>
        </div>

        {/* Resultados y errores se mostrarán debajo */}
        {(resultado || error) && (
          <div className="w-full">
            {resultado && (
              <div className="bg-green-50 border border-green-200 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-green-100 text-green-700 rounded-full"> <CheckCircle size={24} /> </div>
                  <div>
                    <h2 className="font-bold text-green-800 text-lg">Proceso exitoso</h2>
                    <p className="text-green-600">Las direcciones han sido convertidas correctamente.</p>
                  </div>
                </div>
                <div className="mt-4 bg-white p-4 rounded-xl border border-green-100 font-mono text-xs overflow-auto max-h-40">
                  <pre>{JSON.stringify(resultado, null, 2)}</pre>
                </div>
              </div>
            )}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-2xl p-6 flex items-center gap-4 shadow-sm">
                <AlertCircle className="text-red-600" size={30} />
                <span className="text-red-700 font-medium text-lg">{error}</span>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}