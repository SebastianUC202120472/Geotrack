import React, { useState, useEffect } from 'react';
import { getConductores, getDistritos } from '../services/api';

const AdminManifiesto = () => {
  const [data, setData] = useState({ zonas: [], vehiculos: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const cargarDatos = async () => {
      try {
        const [zonasRes, vehiculosRes] = await Promise.all([getDistritos(), getConductores()]);
        setData({ 
          zonas: zonasRes.zonas_operativas || [], 
          vehiculos: vehiculosRes || [] 
        });
      } catch (error) {
        console.error("Error al cargar:", error);
      } finally {
        setLoading(false);
      }
    };
    cargarDatos();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      {/* Encabezado */}
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-gray-900">Emisión de Manifiestos</h1>
        <p className="text-gray-500">Gestión de rutas y asignación de conductores (CUS-21)</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Panel Zonas */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-white">
            <h2 className="text-lg font-bold text-gray-800">Zonas Operativas</h2>
            <span className="bg-blue-100 text-blue-600 py-1 px-3 rounded-full text-xs font-bold uppercase">{data.zonas.length} activas</span>
          </div>
          <ul className="divide-y divide-gray-100">
            {data.zonas.map((zona, i) => (
  <li key={i} className="p-4 hover:bg-gray-50 transition-colors cursor-pointer flex items-center gap-3">
    <div className="w-2 h-2 rounded-full bg-blue-500"></div>
    {/* CAMBIA ESTA LÍNEA */}
    <span className="text-gray-700 font-medium">
      {zona.distrito || "Zona sin nombre"}
    </span>
    <span className="ml-auto text-xs text-gray-400">{zona.total_pedidos} pedidos</span>
  </li>
))}
          </ul>
        </div>

        {/* Panel Vehículos */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-white">
            <h2 className="text-lg font-bold text-gray-800">Flota Disponible</h2>
            <span className="bg-green-100 text-green-600 py-1 px-3 rounded-full text-xs font-bold uppercase">{data.vehiculos.length} vehículos</span>
          </div>
          
          {data.vehiculos.length === 0 ? (
            <div className="p-12 text-center text-gray-400">
              <p>No hay vehículos registrados.</p>
              <button className="mt-4 text-blue-600 font-semibold hover:underline">Ir a configuración de flota</button>
            </div>
          ) : (
            <ul className="divide-y divide-gray-100">
              {data.vehiculos.map((v) => (
                <li key={v.id} className="p-4 hover:bg-gray-50 flex justify-between items-center">
                  <div>
                    <p className="font-bold text-gray-800">{v.placa}</p>
                    <p className="text-sm text-gray-500">{v.modelo}</p>
                  </div>
                  <button className="bg-gray-900 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-gray-700 transition-all">
                    Asignar Ruta
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminManifiesto;