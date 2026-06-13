import { useEffect, useState } from "react";
import { Truck, UserPlus, Plus, CheckCircle, AlertCircle } from "lucide-react";
import Header from "../components/Header";
import {
  listarVehiculos,
  crearVehiculo,
  registrarConductor,
} from "../services/api";

// Gestión de la flota desde el panel del admin:
//  - Registrar conductores (usuarios que luego usan la app móvil).
//  - Registrar vehículos y, opcionalmente, vincularlos a un conductor.
//  - Ver la flota registrada.
// El vínculo vehículo ↔ conductor es lo que después permite asignarle rutas
// (la asignación necesita el id del usuario conductor, no el del vehículo).
export default function Flota() {
  const [vehiculos, setVehiculos] = useState([]);
  const [cargando, setCargando] = useState(true);

  // Formulario de alta de conductor
  const [correo, setCorreo] = useState("");
  const [clave, setClave] = useState("");
  const [conductorMsg, setConductorMsg] = useState(null);

  // Formulario de alta de vehículo
  const [placa, setPlaca] = useState("");
  const [marca, setMarca] = useState("");
  const [capacidad, setCapacidad] = useState("");
  const [conductorId, setConductorId] = useState("");
  const [vehiculoMsg, setVehiculoMsg] = useState(null);

  const cargarVehiculos = async () => {
    setCargando(true);
    try {
      setVehiculos(await listarVehiculos());
    } catch (err) {
      console.error("No se pudo cargar la flota:", err.message);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarVehiculos();
  }, []);

  const altaConductor = async (e) => {
    e.preventDefault();
    setConductorMsg(null);
    try {
      const usuario = await registrarConductor(correo, clave);
      setConductorMsg({
        ok: true,
        texto: `Conductor creado: ${usuario.codigo || ""} (id ${usuario.id}). Úsalo al registrar su vehículo.`,
      });
      setCorreo("");
      setClave("");
    } catch (err) {
      setConductorMsg({ ok: false, texto: err.message });
    }
  };

  const altaVehiculo = async (e) => {
    e.preventDefault();
    setVehiculoMsg(null);
    try {
      await crearVehiculo({
        placa,
        marca: marca || null,
        capacidad_volumetrica: capacidad ? Number(capacidad) : null,
        conductor_id: conductorId ? Number(conductorId) : null,
      });
      setVehiculoMsg({ ok: true, texto: "Vehículo registrado correctamente." });
      setPlaca("");
      setMarca("");
      setCapacidad("");
      setConductorId("");
      cargarVehiculos();
    } catch (err) {
      setVehiculoMsg({ ok: false, texto: err.message });
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header titulo="Flota y Conductores" subtitulo="Registro de vehículos y conductores de reparto" />

      <main className="flex-grow p-8 space-y-8">
        {/* Formularios de alta */}
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Alta de conductor */}
          <form onSubmit={altaConductor} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-indigo-600 text-white rounded-xl"><UserPlus size={22} /></div>
              <div>
                <h2 className="text-lg font-bold text-slate-800">Registrar Conductor</h2>
                <p className="text-sm text-slate-500">Crea la cuenta que el conductor usará en la app móvil.</p>
              </div>
            </div>

            <input
              type="email"
              required
              value={correo}
              onChange={(e) => setCorreo(e.target.value)}
              placeholder="correo del conductor"
              className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <input
              type="password"
              required
              value={clave}
              onChange={(e) => setClave(e.target.value)}
              placeholder="contraseña inicial"
              className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button className="w-full bg-indigo-600 text-white font-semibold p-3 rounded-xl hover:bg-indigo-700 transition">
              Crear conductor
            </button>

            {conductorMsg && <Aviso ok={conductorMsg.ok} texto={conductorMsg.texto} />}
          </form>

          {/* Alta de vehículo */}
          <form onSubmit={altaVehiculo} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-blue-600 text-white rounded-xl"><Plus size={22} /></div>
              <div>
                <h2 className="text-lg font-bold text-slate-800">Registrar Vehículo</h2>
                <p className="text-sm text-slate-500">El id de conductor es opcional (déjalo vacío si es de la empresa).</p>
              </div>
            </div>

            <input
              required
              value={placa}
              onChange={(e) => setPlaca(e.target.value)}
              placeholder="Placa (ej. ABC-123)"
              className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="grid grid-cols-2 gap-3">
              <input
                value={marca}
                onChange={(e) => setMarca(e.target.value)}
                placeholder="Marca"
                className="p-3 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500"
              />
              <input
                type="number"
                value={capacidad}
                onChange={(e) => setCapacidad(e.target.value)}
                placeholder="Capacidad (m³)"
                className="p-3 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <input
              type="number"
              value={conductorId}
              onChange={(e) => setConductorId(e.target.value)}
              placeholder="Id del conductor (opcional)"
              className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button className="w-full bg-blue-600 text-white font-semibold p-3 rounded-xl hover:bg-blue-700 transition">
              Registrar vehículo
            </button>

            {vehiculoMsg && <Aviso ok={vehiculoMsg.ok} texto={vehiculoMsg.texto} />}
          </form>
        </div>

        {/* Listado de la flota */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-5">
            <Truck className="text-blue-600" />
            <h2 className="text-xl font-bold text-slate-800">Flota Registrada</h2>
            <span className="ml-auto text-sm text-slate-400">{vehiculos.length} vehículos</span>
          </div>

          {cargando ? (
            <p className="text-center py-10 text-slate-500">Cargando flota...</p>
          ) : vehiculos.length === 0 ? (
            <p className="text-center py-10 text-slate-400">Aún no hay vehículos registrados.</p>
          ) : (
            <table className="w-full text-left">
              <thead>
                <tr className="border-b text-slate-500 text-sm">
                  <th className="py-3">Código</th>
                  <th>Placa</th>
                  <th>Marca</th>
                  <th>Capacidad (m³)</th>
                  <th>Conductor</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {vehiculos.map((v) => (
                  <tr key={v.id} className="border-b hover:bg-slate-50">
                    <td className="py-3 font-medium">{v.codigo || "-"}</td>
                    <td>{v.placa}</td>
                    <td>{v.marca || "-"}</td>
                    <td>{v.capacidad_volumetrica ?? "-"}</td>
                    <td>{v.conductor_id ? `id ${v.conductor_id}` : "Empresa"}</td>
                    <td>
                      <span className="px-3 py-1 rounded-full text-xs bg-green-100 text-green-700">
                        {v.estado}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>
    </div>
  );
}

// Pequeño aviso de éxito/error reutilizable dentro de esta pantalla.
function Aviso({ ok, texto }) {
  return (
    <div
      className={`flex items-center gap-2 p-3 rounded-xl text-sm ${
        ok ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
      }`}
    >
      {ok ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
      <span>{texto}</span>
    </div>
  );
}
