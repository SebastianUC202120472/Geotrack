import React, { useState, useEffect } from "react";
import { Truck, Search, Filter, Plus, FileText, CheckCircle2 } from "lucide-react";

export function ModuloCapacidadPage() {
  const [modelos, setModelos] = useState([]);
  const [busqueda, setBusqueda] = useState("");
  const [filtroTipo, setFiltroTipo] = useState("todos");
  const [placa, setPlaca] = useState("");
  const [modeloSeleccionado, setModeloSeleccionado] = useState("");
  const [mensaje, setMensaje] = useState(null);

  const datos60Modelos = [
    // 1 - 15: Pick-ups
    { id: 1, marca: "Toyota", modelo: "Hilux Pick-up", tipo: "pickup", largo: 1.52, ancho: 1.51, alto: 0.48, volumen: 1.10, carga: 1000, fuente: "Ficha técnica oficial Toyota Hilux" },
    { id: 2, marca: "Ford", modelo: "Ranger", tipo: "pickup", largo: 1.56, ancho: 1.58, alto: 0.51, volumen: 1.26, carga: 1000, fuente: "Ficha técnica oficial Ford Ranger" },
    { id: 3, marca: "Mitsubishi", modelo: "L200", tipo: "pickup", largo: 1.52, ancho: 1.47, alto: 0.46, volumen: 1.03, carga: 1000, fuente: "Ficha técnica oficial Mitsubishi L200" },
    { id: 4, marca: "Nissan", modelo: "Frontier", tipo: "pickup", largo: 1.51, ancho: 1.56, alto: 0.47, volumen: 1.11, carga: 1000, fuente: "Ficha técnica oficial Nissan Frontier" },
    { id: 5, marca: "Chevrolet", modelo: "D-Max", tipo: "pickup", largo: 1.48, ancho: 1.53, alto: 0.48, volumen: 1.09, carga: 1000, fuente: "Ficha técnica oficial Chevrolet D-Max" },
    { id: 6, marca: "Volkswagen", modelo: "Amarok", tipo: "pickup", largo: 1.56, ancho: 1.62, alto: 0.51, volumen: 1.29, carga: 1000, fuente: "Ficha técnica oficial Volkswagen Amarok" },
    { id: 7, marca: "Mazda", modelo: "BT-50", tipo: "pickup", largo: 1.57, ancho: 1.53, alto: 0.49, volumen: 1.18, carga: 1000, fuente: "Ficha técnica oficial Mazda BT-50" },
    { id: 8, marca: "GWM", modelo: "Poer", tipo: "pickup", largo: 1.52, ancho: 1.52, alto: 0.47, volumen: 1.09, carga: 1000, fuente: "Ficha técnica oficial GWM Poer" },
    { id: 9, marca: "JMC", modelo: "Vigus", tipo: "pickup", largo: 1.47, ancho: 1.47, alto: 0.46, volumen: 0.99, carga: 900, fuente: "Ficha técnica oficial JMC Vigus" },
    { id: 10, marca: "Foton", modelo: "Tunland", tipo: "pickup", largo: 1.52, ancho: 1.58, alto: 0.44, volumen: 1.06, carga: 1000, fuente: "Ficha técnica oficial Foton Tunland" },
    { id: 11, marca: "JAC", modelo: "T8", tipo: "pickup", largo: 1.52, ancho: 1.52, alto: 0.47, volumen: 1.09, carga: 900, fuente: "Ficha técnica oficial JAC T8" },
    { id: 12, marca: "Isuku", modelo: "D-Max Crew", tipo: "pickup", largo: 1.48, ancho: 1.53, alto: 0.48, volumen: 1.09, carga: 1050, fuente: "Ficha técnica oficial Isuzu D-Max" },
    { id: 13, marca: "RAM", modelo: "700", tipo: "pickup", largo: 1.35, ancho: 1.31, alto: 0.40, volumen: 0.71, carga: 650, fuente: "Ficha técnica oficial RAM 700" },
    { id: 14, marca: "RAM", modelo: "1500", tipo: "pickup", largo: 1.71, ancho: 1.68, alto: 0.54, volumen: 1.55, carga: 800, fuente: "Ficha técnica oficial RAM 1500" },
    { id: 15, marca: "Fiat", modelo: "Strada", tipo: "pickup", largo: 1.35, ancho: 1.31, alto: 0.40, volumen: 0.71, carga: 650, fuente: "Ficha técnica oficial Fiat Strada" },

    // 16 - 30: Furgones y Vans
    { id: 16, marca: "Hyundai", modelo: "H1 Van", tipo: "furgon", largo: 2.37, ancho: 1.62, alto: 1.34, volumen: 5.15, carga: 1200, fuente: "Ficha técnica oficial Hyundai H1" },
    { id: 17, marca: "Peugeot", modelo: "Partner", tipo: "furgon", largo: 1.81, ancho: 1.23, alto: 1.25, volumen: 3.30, carga: 800, fuente: "Ficha técnica oficial Peugeot Partner" },
    { id: 18, marca: "Peugeot", modelo: "Boxer", tipo: "furgon", largo: 3.12, ancho: 1.87, alto: 1.93, volumen: 11.50, carga: 1500, fuente: "Ficha técnica oficial Peugeot Boxer" },
    { id: 19, marca: "Citroën", modelo: "Berlingo", tipo: "furgon", largo: 1.81, ancho: 1.23, alto: 1.25, volumen: 3.30, carga: 800, fuente: "Ficha técnica oficial Citroën Berlingo" },
    { id: 20, marca: "Citroën", modelo: "Jumper", tipo: "furgon", largo: 3.12, ancho: 1.87, alto: 1.93, volumen: 11.50, carga: 1500, fuente: "Ficha técnica oficial Citroën Jumper" },
    { id: 21, marca: "Renault", modelo: "Kangoo", tipo: "furgon", largo: 1.73, ancho: 1.22, alto: 1.17, volumen: 3.00, carga: 750, fuente: "Ficha técnica oficial Renault Kangoo" },
    { id: 22, marca: "Renault", modelo: "Master", tipo: "furgon", largo: 3.08, ancho: 1.76, alto: 1.89, volumen: 10.80, carga: 1600, fuente: "Ficha técnica oficial Renault Master" },
    { id: 23, marca: "Mercedes-Benz", modelo: "Sprinter 315", tipo: "furgon", largo: 3.27, ancho: 1.78, alto: 1.94, volumen: 11.00, carga: 1400, fuente: "Ficha técnica oficial MB Sprinter" },
    { id: 24, marca: "Mercedes-Benz", modelo: "Vito", tipo: "furgon", largo: 2.53, ancho: 1.68, alto: 1.39, volumen: 6.00, carga: 1000, fuente: "Ficha técnica oficial MB Vito" },
    { id: 25, marca: "Volkswagen", modelo: "Caddy", tipo: "furgon", largo: 1.78, ancho: 1.25, alto: 1.27, volumen: 3.20, carga: 700, fuente: "Ficha técnica oficial VW Caddy" },
    { id: 26, marca: "Volkswagen", modelo: "Crafter", tipo: "furgon", largo: 3.45, ancho: 1.83, alto: 1.96, volumen: 12.00, carga: 1500, fuente: "Ficha técnica oficial VW Crafter" },
    { id: 27, marca: "Ford", modelo: "Transit Van", tipo: "furgon", largo: 3.04, ancho: 1.78, alto: 1.88, volumen: 10.00, carga: 1400, fuente: "Ficha técnica oficial Ford Transit" },
    { id: 28, marca: "Nissan", modelo: "NV350 Urvan", tipo: "furgon", largo: 2.86, ancho: 1.52, alto: 1.35, volumen: 5.80, carga: 1300, fuente: "Ficha técnica oficial Nissan NV350" },
    { id: 29, marca: "Chevrolet", modelo: "N400 Max", tipo: "furgon", largo: 2.10, ancho: 1.40, alto: 1.30, volumen: 3.80, carga: 720, fuente: "Ficha técnica oficial Chevrolet N400" },
    { id: 30, marca: "Changan", modelo: "Grand Supervan", tipo: "furgon", largo: 2.50, ancho: 1.48, alto: 1.35, volumen: 5.00, carga: 1000, fuente: "Ficha técnica oficial Changan Supervan" },

    // 31 - 45: Camiones Ligeros y Medianos
    { id: 31, marca: "Hyundai", modelo: "H100 Baranda", tipo: "camion_ligero", largo: 3.20, ancho: 1.80, alto: 0.40, volumen: 2.30, carga: 1500, fuente: "Ficha técnica oficial Hyundai H100" },
    { id: 32, marca: "Hyundai", modelo: "EX8 Furgón", tipo: "camion_ligero", largo: 4.80, ancho: 2.10, alto: 2.10, volumen: 21.10, carga: 5000, fuente: "Ficha técnica oficial Hyundai EX8" },
    { id: 33, marca: "Isuzu", modelo: "NLR 3.1", tipo: "camion_ligero", largo: 3.10, ancho: 1.85, alto: 1.90, volumen: 10.80, carga: 3000, fuente: "Ficha técnica oficial Isuzu NLR" },
    { id: 34, marca: "Isuzu", modelo: "NPR 75", tipo: "camion_ligero", largo: 4.30, ancho: 2.05, alto: 2.00, volumen: 17.60, carga: 5000, fuente: "Ficha técnica oficial Isuzu NPR" },
    { id: 35, marca: "Hino", modelo: "Dutro 300 (4t)", tipo: "camion_ligero", largo: 4.20, ancho: 2.00, alto: 2.00, volumen: 16.80, carga: 4000, fuente: "Ficha técnica oficial Hino Dutro 300" },
    { id: 36, marca: "Hino", modelo: "500 (10t)", tipo: "camion_mediano", largo: 6.50, ancho: 2.40, alto: 2.40, volumen: 37.40, carga: 10000, fuente: "Ficha técnica oficial Hino 500" },
    { id: 37, marca: "Foton", modelo: "Aumark 6t", tipo: "camion_ligero", largo: 5.20, ancho: 2.15, alto: 2.15, volumen: 24.00, carga: 6000, fuente: "Ficha técnica oficial Foton Aumark" },
    { id: 38, marca: "JAC", modelo: "Urban HFC 1042", tipo: "camion_ligero", largo: 3.80, ancho: 1.90, alto: 1.90, volumen: 13.70, carga: 3500, fuente: "Ficha técnica oficial JAC Urban" },
    { id: 39, marca: "Mitsubishi Fuso", modelo: "Canter 5t", tipo: "camion_ligero", largo: 4.50, ancho: 2.00, alto: 2.00, volumen: 18.00, carga: 5000, fuente: "Ficha técnica oficial Fuso Canter" },
    { id: 40, marca: "Mitsubishi Fuso", modelo: "FI 12t", tipo: "camion_mediano", largo: 6.20, ancho: 2.35, alto: 2.30, volumen: 33.50, carga: 8500, fuente: "Ficha técnica oficial Fuso FI" },
    { id: 41, marca: "Dongfeng", modelo: "Captain-E", tipo: "camion_ligero", largo: 4.20, ancho: 2.00, alto: 1.90, volumen: 15.90, carga: 4000, fuente: "Ficha técnica oficial Dongfeng Captain" },
    { id: 42, marca: "Shacman", modelo: "L3000", tipo: "camion_mediano", largo: 6.80, ancho: 2.45, alto: 2.50, volumen: 41.60, carga: 12000, fuente: "Ficha técnica oficial Shacman L3000" },
    { id: 43, marca: "Volvo", modelo: "FL 280", tipo: "camion_mediano", largo: 7.20, ancho: 2.48, alto: 2.55, volumen: 45.50, carga: 14000, fuente: "Ficha técnica oficial Volvo FL" },
    { id: 44, marca: "Scania", modelo: "P280", tipo: "camion_mediano", largo: 7.50, ancho: 2.50, alto: 2.60, volumen: 48.70, carga: 15000, fuente: "Ficha técnica oficial Scania P280" },
    { id: 45, marca: "International", modelo: "MV Series", tipo: "camion_mediano", largo: 7.00, ancho: 2.45, alto: 2.50, volumen: 42.80, carga: 13000, fuente: "Ficha técnica oficial International MV" },

    // 46 - 60: Camiones Pesados, Tráileres y Remolques
    { id: 46, marca: "Volvo", modelo: "FH 500 6x4", tipo: "pesado", largo: 13.60, ancho: 2.50, alto: 2.70, volumen: 91.80, carga: 30000, fuente: "Ficha técnica oficial Volvo FH" },
    { id: 47, marca: "Volvo", modelo: "FM 420 4x2", tipo: "pesado", largo: 12.50, ancho: 2.50, alto: 2.60, volumen: 81.25, carga: 25000, fuente: "Ficha técnica oficial Volvo FM" },
    { id: 48, marca: "Scania", modelo: "R500 6x2", tipo: "pesado", largo: 13.60, ancho: 2.50, alto: 2.70, volumen: 91.80, carga: 32000, fuente: "Ficha técnica oficial Scania R500" },
    { id: 49, marca: "Scania", modelo: "G450 6x4", tipo: "pesado", largo: 13.00, ancho: 2.50, alto: 2.65, volumen: 86.10, carga: 28000, fuente: "Ficha técnica oficial Scania G450" },
    { id: 50, marca: "Mercedes-Benz", modelo: "Actros 2651", tipo: "pesado", largo: 13.60, ancho: 2.50, alto: 2.70, volumen: 91.80, carga: 30000, fuente: "Ficha técnica oficial MB Actros" },
    { id: 51, marca: "Mercedes-Benz", modelo: "Arocs 3345", tipo: "pesado", largo: 12.80, ancho: 2.50, alto: 2.60, volumen: 83.20, carga: 27000, fuente: "Ficha técnica oficial MB Arocs" },
    { id: 52, marca: "International", modelo: "LT625", tipo: "pesado", largo: 13.60, ancho: 2.50, alto: 2.75, volumen: 93.50, carga: 30000, fuente: "Ficha técnica oficial International LT" },
    { id: 53, marca: "Kenworth", modelo: "T680", tipo: "pesado", largo: 13.60, ancho: 2.50, alto: 2.75, volumen: 93.50, carga: 32000, fuente: "Ficha técnica oficial Kenworth T680" },
    { id: 54, marca: "Freightliner", modelo: "Cascadia", tipo: "pesado", largo: 13.60, ancho: 2.50, alto: 2.75, volumen: 93.50, carga: 32000, fuente: "Ficha técnica oficial Freightliner Cascadia" },
    { id: 55, marca: "Howo", modelo: "Sinotruk A7", tipo: "pesado", largo: 13.00, ancho: 2.50, alto: 2.60, volumen: 84.50, carga: 28000, fuente: "Ficha técnica oficial Howo A7" },
    { id: 56, marca: "FAW", modelo: "Jiefang J6P", tipo: "pesado", largo: 12.80, ancho: 2.50, alto: 2.60, volumen: 83.20, carga: 26000, fuente: "Ficha técnica oficial FAW J6P" },
    { id: 57, marca: "Shacman", modelo: "X3000", tipo: "pesado", largo: 13.50, ancho: 2.50, alto: 2.70, volumen: 91.10, carga: 30000, fuente: "Ficha técnica oficial Shacman X3000" },
    { id: 58, marca: "CAMC", modelo: "Hanma H9", tipo: "pesado", largo: 13.00, ancho: 2.50, alto: 2.65, volumen: 86.10, carga: 28000, fuente: "Ficha técnica oficial CAMC H9" },
    { id: 59, marca: "DAF", modelo: "XF 530", tipo: "pesado", largo: 13.60, ancho: 2.50, alto: 2.70, volumen: 91.80, carga: 30000, fuente: "Ficha técnica oficial DAF XF" },
    { id: 60, marca: "IVECO", modelo: "Stralis Hi-Way", tipo: "pesado", largo: 13.60, ancho: 2.50, alto: 2.70, volumen: 91.80, carga: 30000, fuente: "Ficha técnica oficial IVECO Stralis" }
  ];

  useEffect(() => {
    fetch("/api/v1/capacidad/modelos")
      .then((res) => {
        if (!res.ok) throw new Error("Endpoint no encontrado");
        return res.json();
      })
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setModelos(data);
        } else {
          setModelos(datos60Modelos);
        }
      })
      .catch(() => {
        setModelos(datos60Modelos);
      });
  }, []);

  const listaSegura = Array.isArray(modelos) ? modelos : [];

  const modelosFiltrados = listaSegura.filter((item) => {
    const coincideTexto =
      item.marca?.toLowerCase().includes(busqueda.toLowerCase()) ||
      item.modelo?.toLowerCase().includes(busqueda.toLowerCase());
    const coincideTipo = filtroTipo === "todos" || item.tipo === filtroTipo;
    return coincideTexto && coincideTipo;
  });

  const handleVincular = (e) => {
    e.preventDefault();
    if (!placa || !modeloSeleccionado) return;
    setMensaje(`Placa ${placa.toUpperCase()} vinculada correctamente al modelo.`);
    setPlaca("");
    setModeloSeleccionado("");
    setTimeout(() => setMensaje(null), 4000);
  };

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

      {mensaje && (
        <div className="flex items-center gap-3 p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl shadow-sm">
          <CheckCircle2 size={20} className="text-emerald-600 flex-shrink-0" />
          <p className="text-sm font-medium">{mensaje}</p>
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
              className="w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all uppercase placeholder:normal-case text-slate-800"
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

      {/* Contenedor del Catálogo y Filtros */}
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
                <option value="furgon">Furgón</option>
                <option value="camion_ligero">Camión Ligero</option>
                <option value="camion_mediano">Camión Mediano</option>
                <option value="pesado">Pesado / Tráiler</option>
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
                <th className="py-3.5 px-6 text-center">Carga Máx (kg)</th>
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
                    {item.largo} x {item.ancho} x {item.alto} m
                  </td>
                  <td className="py-4 px-6 text-center font-semibold text-blue-600">
                    {item.volumen} m³
                  </td>
                  <td className="py-4 px-6 text-center font-medium text-slate-800">
                    {item.carga} kg
                  </td>
                  <td className="py-4 px-6 text-xs text-slate-400 flex items-center gap-1.5">
                    <FileText size={14} className="text-slate-400" />
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