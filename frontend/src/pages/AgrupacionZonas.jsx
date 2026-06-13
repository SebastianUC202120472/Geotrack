import { useEffect, useState } from "react";
import {
  Layers3,
  RefreshCw,
  MapPinned,
  Package
} from "lucide-react";

import Header from "../components/Header";
import DistrictCard from "../components/DistrictCard";
// Importamos la función correcta que definimos en api.js
import { getDistritos } from "../services/api";

export default function AgrupacionZonas() {

  const [zonas, setZonas] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    cargarZonas();
  }, []);

  const cargarZonas = async () => {
    setLoading(true);
    try {
      const response = await getDistritos();
      // Ajustamos según la estructura que devuelva tu API. 
      // Si response es un objeto { zonas_operativas: [...] }, úsalo así:
      // Si response es un array directo, usa: setZonas(response);
      setZonas(response.zonas_operativas || response || []);
    } catch (error) {
      console.error("Error al cargar zonas:", error);
      alert("No se pudieron cargar las zonas");
    } finally {
      setLoading(false);
    }
  };

  // Verificación de seguridad por si zonas está vacío
  const totalPedidos = zonas.reduce(
    (acc, zona) => acc + (zona.total_pedidos || 0),
    0
  );

  return (
    <div className="flex h-full bg-slate-100">
      <main className="flex-1 overflow-y-auto p-6 space-y-6">
        <Header />

        {loading ? (
          <div className="bg-white rounded-2xl p-10 text-center shadow-sm">
            Cargando agrupación automática...
          </div>
        ) : (
          <>
            {/* Encabezado */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
              <div className="flex justify-between items-center">
                <div>
                  <h1 className="text-3xl font-bold text-slate-800">
                    Agrupación Automática por Distritos
                  </h1>
                  <p className="text-slate-500 mt-2">
                    Los pedidos importados han sido organizados automáticamente por distrito.
                  </p>
                </div>
                <button
                  onClick={cargarZonas}
                  className="flex items-center gap-2 bg-indigo-600 text-white px-5 py-3 rounded-xl hover:bg-indigo-700"
                >
                  <RefreshCw size={18} />
                  Actualizar
                </button>
              </div>
            </div>

            {/* Cards de métricas */}
            <div className="grid md:grid-cols-3 gap-5">
              <div className="bg-white rounded-2xl p-6 border shadow-sm">
                <div className="flex justify-between">
                  <div>
                    <p className="text-slate-500">Distritos</p>
                    <h2 className="text-4xl font-bold">{zonas.length}</h2>
                  </div>
                  <MapPinned className="text-indigo-600" size={40} />
                </div>
              </div>

              <div className="bg-white rounded-2xl p-6 border shadow-sm">
                <div className="flex justify-between">
                  <div>
                    <p className="text-slate-500">Pedidos</p>
                    <h2 className="text-4xl font-bold">{totalPedidos}</h2>
                  </div>
                  <Package className="text-green-600" size={40} />
                </div>
              </div>

              <div className="bg-white rounded-2xl p-6 border shadow-sm">
                <div className="flex justify-between">
                  <div>
                    <p className="text-slate-500">Estado</p>
                    <h2 className="text-2xl font-bold text-green-600">Agrupado</h2>
                  </div>
                  <Layers3 className="text-blue-600" size={40} />
                </div>
              </div>
            </div>

            {/* Lista de Distritos */}
            <div className="bg-white rounded-2xl border p-6 shadow-sm">
              <h2 className="text-xl font-bold mb-5">Zonas Operativas Detectadas</h2>
              <div className="grid lg:grid-cols-2 xl:grid-cols-3 gap-5">
                {zonas.map((zona) => (
                  <DistrictCard
                    key={zona.distrito}
                    distrito={zona.distrito}
                    pedidos={zona.total_pedidos}
                  />
                ))}
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}