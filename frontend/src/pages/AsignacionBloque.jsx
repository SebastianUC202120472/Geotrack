import { useEffect, useState } from "react";
import { Truck, MapPin, User, Loader2, AlertCircle, CheckCircle } from "lucide-react";
import Header from "../components/Header";
import { asignarBloque, listarZonas, listarVehiculos } from "../services/api";

// Asignación de un bloque de pedidos a un conductor (CUS-18).
// IMPORTANTE: el backend asigna la ruta al USUARIO conductor (conductor_id),
// no al vehículo. Por eso aquí solo se ofrecen los vehículos que tienen un
// conductor vinculado, y se envía ese conductor_id (no el id del vehículo).
export default function AsignacionBloque() {
  const [zonas, setZonas] = useState([]);
  const [vehiculos, setVehiculos] = useState([]);

  const [distrito, setDistrito] = useState("");
  const [vehiculoId, setVehiculoId] = useState("");
  const [nombreRuta, setNombreRuta] = useState("");

  const [cargando, setCargando] = useState(false);
  const [aviso, setAviso] = useState(null);

  useEffect(() => {
    const cargar = async () => {
      try {
        const [zonasRes, vehiculosRes] = await Promise.all([listarZonas(), listarVehiculos()]);
        setZonas(zonasRes.zonas_operativas || []);
        setVehiculos(vehiculosRes || []);
      } catch (err) {
        console.error("Error al cargar datos:", err.message);
      }
    };
    cargar();
  }, []);

  // Solo los vehículos con conductor asignado pueden recibir una ruta.
  const vehiculosConConductor = vehiculos.filter((v) => v.conductor_id);

  const zonaSeleccionada = zonas.find((z) => z.distrito === distrito);
  const vehiculoSeleccionado = vehiculos.find((v) => String(v.id) === String(vehiculoId));

  const asignar = async () => {
    if (!distrito || !vehiculoId || !nombreRuta.trim()) {
      setAviso({ ok: false, texto: "Completa el nombre de la ruta, la zona y el vehículo." });
      return;
    }
    setCargando(true);
    setAviso(null);
    try {
      const res = await asignarBloque({
        nombre_ruta: nombreRuta.trim(),
        distrito,
        conductor_id: vehiculoSeleccionado.conductor_id,
      });
      setAviso({ ok: true, texto: `${res.mensaje} (ruta ${res.codigo || res.ruta_id}).` });
      setNombreRuta("");
      setDistrito("");
      setVehiculoId("");
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex flex-col">
      <Header titulo="Asignación de Rutas" subtitulo="Arma un bloque logístico y asígnalo a un conductor (CUS-18)" />

      <main className="flex-grow w-full p-8">
        <div className="max-w-6xl mx-auto w-full space-y-8">
          {vehiculosConConductor.length === 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 flex items-center gap-3 text-amber-800">
              <AlertCircle size={22} />
              <span>
                No hay vehículos con conductor asignado. Ve a <b>Flota y Conductores</b> para registrar un
                conductor y vincularlo a un vehículo antes de asignar rutas.
              </span>
            </div>
          )}

          <div className="grid md:grid-cols-2 gap-8">
            {/* Formulario */}
            <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm space-y-6">
              <input
                className="w-full p-4 bg-slate-50 border border-slate-200 rounded-2xl outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Nombre de la nueva ruta"
                value={nombreRuta}
                onChange={(e) => setNombreRuta(e.target.value)}
              />

              <select
                className="w-full p-4 bg-slate-50 border border-slate-200 rounded-2xl outline-none"
                value={distrito}
                onChange={(e) => setDistrito(e.target.value)}
              >
                <option value="">Selecciona zona operativa</option>
                {zonas.map((z, i) => (
                  <option key={i} value={z.distrito}>
                    {z.distrito} ({z.total_pedidos} pedidos)
                  </option>
                ))}
              </select>

              <select
                className="w-full p-4 bg-slate-50 border border-slate-200 rounded-2xl outline-none"
                value={vehiculoId}
                onChange={(e) => setVehiculoId(e.target.value)}
              >
                <option value="">Selecciona vehículo (con conductor)</option>
                {vehiculosConConductor.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.placa} · conductor id {v.conductor_id}
                  </option>
                ))}
              </select>

              <button
                onClick={asignar}
                disabled={cargando}
                className="w-full bg-blue-600 text-white p-4 rounded-2xl font-bold hover:bg-blue-700 transition shadow-lg shadow-blue-200 flex justify-center items-center gap-2 disabled:opacity-60"
              >
                {cargando ? <Loader2 className="animate-spin" /> : "Confirmar Asignación"}
              </button>

              {aviso && (
                <div
                  className={`flex items-center gap-2 p-3 rounded-xl text-sm ${
                    aviso.ok ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
                  }`}
                >
                  {aviso.ok ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
                  <span>{aviso.texto}</span>
                </div>
              )}
            </div>

            {/* Vista previa del impacto */}
            <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm flex flex-col">
              <h2 className="font-bold text-lg mb-6 flex items-center gap-2">
                <Truck className="text-blue-600" /> Impacto Logístico
              </h2>

              {zonaSeleccionada && vehiculoSeleccionado ? (
                <div className="space-y-5 flex-grow">
                  <div className="flex items-center gap-3 p-4 bg-slate-50 rounded-2xl">
                    <MapPin className="text-blue-600" />
                    <span>Zona: <b>{zonaSeleccionada.distrito}</b></span>
                  </div>
                  <div className="flex items-center gap-3 p-4 bg-slate-50 rounded-2xl">
                    <User className="text-blue-600" />
                    <span>Vehículo: <b>{vehiculoSeleccionado.placa}</b></span>
                  </div>
                  <div className="text-center py-6 border-t border-dashed mt-auto">
                    <p className="text-sm text-slate-400">Pedidos a despachar</p>
                    <p className="text-6xl font-extrabold text-blue-600 my-2">
                      {zonaSeleccionada.total_pedidos}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex-grow flex flex-col items-center justify-center text-slate-400 border-2 border-dashed rounded-2xl">
                  <AlertCircle className="mb-2 opacity-50" />
                  <p>Selecciona zona y vehículo para ver el resumen.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
