import React, { useState, useEffect } from "react";
import { Truck, Search, Filter, Plus, FileText, CheckCircle2, AlertCircle, History } from "lucide-react";

export function ModuloCapacidadPage() {
  const [modelos, setModelos] = useState([]);
  const [vinculaciones, setVinculaciones] = useState([]); // Guardará la lista de placas en BD
  const [busqueda, setBusqueda] = useState("");
  const [filtroTipo, setFiltroTipo] = useState("todos");
  const [placa, setPlaca] = useState("");
  const [modeloSeleccionado, setModeloSeleccionado] = useState("");
  const [mensaje, setMensaje] = useState(null);

  // 1. Cargar catálogo y vinculaciones al montar el componente
  useEffect(() => {
    cargarCatalogo();
    cargarVinculaciones();
  }, []);

  const cargarCatalogo = () => {
    fetch("http://localhost:8000/api/modulo-capacidad/catalogo")
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) setModelos(data);
      })
      .catch((err) => console.error("Error al cargar catálogo:", err));
  };

  const cargarVinculaciones = () => {
    fetch("http://localhost:8000/api/modulo-capacidad/vincular")
      .then((res) => {
        if (res.ok) return res.json();
        return [];
      })
      .then((data) => {
        if (Array.isArray(data)) setVinculaciones(data);
      })
      .catch((err) => console.error("Error al obtener vinculaciones:", err));
  };

  const handleVincular = async (e) => {
    e.preventDefault();
    setMensaje(null);

    if (!placa.trim() || !modeloSeleccionado) {
      setMensaje({
        tipo: "error",
        texto: "Por favor, ingrese la placa y seleccione un modelo del catálogo.",
      });
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/api/modulo-capacidad/vincular", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          placa: placa.toUpperCase(),
          modelo_id: modeloSeleccionado,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Error en la vinculación con el backend.");
      }

      const data = await response.json();

      setMensaje({
        tipo: "exito",
        texto: `¡Vinculación exitosa! Placa ${data.placa} asociada a ${data.modelo.marca} ${data.modelo.modelo}.`,
      });

      // Agregar la nueva vinculación a la lista persistente local
      setVinculaciones((prev) => [data, ...prev]);

      setPlaca("");
      setModeloSeleccionado("");
    } catch (err) {
      setMensaje({
        tipo: "error",
        texto: err.message || "Error al conectar con el servidor.",
      });
    }
  };

  const listaSegura = Array.isArray(modelos) ? modelos : [];

  const modelosFiltrados = listaSegura.filter((item) => {
    const coincideTexto =
      item.marca?.toLowerCase().includes(busqueda.toLowerCase()) ||
      item.modelo?.toLowerCase().includes(busqueda.toLowerCase());
    const coincideTipo = filtroTipo === "todos" || item.tipo === filtroTipo;
    return coincideTexto && coincideTipo;
  });

  return (
    <div className="p-6 md:p-8 space-y-8 bg-slate-50 min-h-screen">
      {/* Encabezado Principal */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 text-xs font-semibold bg-blue-50 text-blue-700 rounded-md border border-blue-200">
              Semana 9
            </span>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              Catálogo de Vehículos y Capacidad
            </h1>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Gestión de especificaciones volumétricas, carga útil y asignación de placas a la flota GeoTrack.
          </p>
        </div>
      </div>

      {/* Alerta de Respuesta */}
      {mensaje && (
        <div
          className={`flex items-center gap-3 p-4 rounded-xl shadow-sm border ${
            mensaje.tipo === "exito"
              ? "bg-emerald-50 border-emerald-200 text-emerald-800"
              : "bg-rose-50 border-rose-200 text-rose-800"
          }`}
        >
          {mensaje.tipo === "exito" ? (
            <CheckCircle2 size={20} className="text-emerald-600 flex-shrink-0" />
          ) : (
            <AlertCircle size={20} className="text-rose-600 flex-shrink-0" />
          )}
          <p className="text-sm font-medium">{mensaje.texto}</p>
        </div>
      )}

      {/* Tarjeta de Vinculación de Placa */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-100">
          <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
            <Plus size={18} />
          </div>
          <h2 className="text-base font-semibold text-slate-800">
            Vinculación de Placa a Modelo del Catálogo
          </h2>
        </div>

        <form onSubmit={handleVincular} className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">
              Placa del Vehículo
            </label>
            <input
              type="text"
              value={placa}
              onChange={(e) => setPlaca(e.target.value)}
              placeholder="Ej. ABC-123"
              className="w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all uppercase text-slate-800"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">
              Modelo de Catálogo
            </label>
            <select
              value={modeloSeleccionado}
              onChange={(e) => setModeloSeleccionado(e.target.value)}
              className="w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-slate-800"
            >
              <option value="">-- Seleccionar Modelo --</option>
              {listaSegura.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.marca} {m.modelo} ({m.tipo})
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold py-2.5 px-5 rounded-xl shadow-sm hover:shadow transition-all flex items-center justify-center gap-2 text-sm"
          >
            <Truck size={18} />
            Vincular Placa
          </button>
        </form>
      </div>

      {/* NUEVA SECCIÓN: HISTORIAL DE PLACAS VINCULADAS EN BD */}
      {vinculaciones.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
            <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
              <History size={18} />
            </div>
            <h2 className="text-base font-semibold text-slate-800">
              Placas Vinculadas Registradas ({vinculaciones.length})
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {vinculaciones.map((v, i) => (
              <div key={v.id || i} className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900 text-lg tracking-wider">{v.placa}</span>
                  <span className="px-2 py-0.5 text-xs bg-emerald-100 text-emerald-800 font-semibold rounded-full">
                    Activo
                  </span>
                </div>
                <p className="text-sm font-medium text-slate-700">
                  {v.modelo?.marca} {v.modelo?.modelo}
                </p>
                <p className="text-xs text-slate-500">
                  Carga Útil: <strong className="text-slate-700">{v.modelo?.carga_util_kg} kg</strong> | Vol:{" "}
                  <strong className="text-slate-700">{v.modelo?.volumen_util_m3} m³</strong>
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tabla del Catálogo Oficial */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-semibold text-slate-800">
              Catálogo Oficial ({modelosFiltrados.length} modelos)
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Dimensiones expresadas en metros y volumen útil en metros cúbicos.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3">
            <div className="relative w-full sm:w-64">
              <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
                placeholder="Buscar por marca o modelo..."
                className="w-full pl-10 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-slate-800"
              />
            </div>

            <div className="relative w-full sm:w-48">
              <Filter size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <select
                value={filtroTipo}
                onChange={(e) => setFiltroTipo(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-slate-800 appearance-none"
              >
                <option value="todos">Todos los tipos</option>
                <option value="pickup">Pick-up</option>
                <option value="furgoneta">Furgoneta / Furgón</option>
                <option value="camion_ligero">Camión Ligero</option>
                <option value="camion_mediano">Camión Mediano</option>
              </select>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm border-collapse">
            <thead>
              <tr className="bg-slate-800 text-slate-200 text-xs font-semibold uppercase tracking-wider">
                <th className="py-3.5 px-6">Marca</th>
                <th className="py-3.5 px-6">Modelo</th>
                <th className="py-3.5 px-6">Tipo</th>
                <th className="py-3.5 px-6">Dimensiones (L x A x H)</th>
                <th className="py-3.5 px-6 text-center">Volumen (m³)</th>
                <th className="py-3.5 px-6 text-center">Carga Útil (kg)</th>
                <th className="py-3.5 px-6">Fuente</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {modelosFiltrados.map((item, idx) => (
                <tr key={item.id || idx} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-4 px-6 font-semibold text-slate-900">{item.marca}</td>
                  <td className="py-4 px-6 font-medium text-slate-800">{item.modelo}</td>
                  <td className="py-4 px-6">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700 capitalize border border-slate-200">
                      {item.tipo?.replace("_", " ")}
                    </span>
                  </td>
                  <td className="py-4 px-6 font-mono text-xs text-slate-600">
                    {item.largo_m ?? item.largo} x {item.ancho_m ?? item.ancho} x {item.alto_m ?? item.alto} m
                  </td>
                  <td className="py-4 px-6 text-center font-semibold text-blue-600">
                    {item.volumen_util_m3 ?? item.volumen} m³
                  </td>
                  <td className="py-4 px-6 text-center font-medium text-slate-800">
                    {item.carga_util_kg ?? item.carga} kg
                  </td>
                  <td className="py-4 px-6 text-xs text-slate-400 flex items-center gap-1.5">
                    <FileText size={14} className="text-slate-400 flex-shrink-0" />
                    {item.fuente}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}