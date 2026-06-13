import { useEffect, useState } from "react";
import { Truck, UserPlus, Plus, CheckCircle2, AlertCircle } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import { EstadoBadge } from "../components/ui/Badge";
import { listarVehiculos, crearVehiculo, registrarConductor } from "../services/api";

// Gestión de la flota: registrar conductores (cuentas para la app móvil) y
// vehículos, vinculándolos. Ese vínculo es lo que luego permite asignar rutas.
export default function Flota() {
  const [vehiculos, setVehiculos] = useState([]);
  const [cargando, setCargando] = useState(true);

  const [correo, setCorreo] = useState("");
  const [clave, setClave] = useState("");
  const [conductorMsg, setConductorMsg] = useState(null);

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
      const u = await registrarConductor(correo, clave);
      setConductorMsg({ ok: true, texto: `Conductor creado: ${u.codigo || ""} (id ${u.id}). Úsalo al registrar su vehículo.` });
      setCorreo(""); setClave("");
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
      setPlaca(""); setMarca(""); setCapacidad(""); setConductorId("");
      cargarVehiculos();
    } catch (err) {
      setVehiculoMsg({ ok: false, texto: err.message });
    }
  };

  return (
    <div className="space-y-6 p-6 lg:p-8">
      <PageHeader titulo="Flota y Conductores" subtitulo="Registro de vehículos y conductores de reparto." />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Registrar conductor" subtitle="Crea la cuenta que usará en la app móvil.">
          <form onSubmit={altaConductor} className="space-y-4">
            <Input label="Correo del conductor" type="email" required value={correo}
              onChange={(e) => setCorreo(e.target.value)} placeholder="conductor@siol.com" />
            <Input label="Contraseña inicial" type="password" required value={clave}
              onChange={(e) => setClave(e.target.value)} placeholder="••••••••" />
            <Button type="submit" icon={UserPlus} block>Crear conductor</Button>
            {conductorMsg && <Aviso {...conductorMsg} />}
          </form>
        </Card>

        <Card title="Registrar vehículo" subtitle="El id de conductor es opcional (vacío = de la empresa).">
          <form onSubmit={altaVehiculo} className="space-y-4">
            <Input label="Placa" required value={placa} onChange={(e) => setPlaca(e.target.value)} placeholder="ABC-123" />
            <div className="grid grid-cols-2 gap-4">
              <Input label="Marca" value={marca} onChange={(e) => setMarca(e.target.value)} placeholder="Toyota" />
              <Input label="Capacidad (m³)" type="number" value={capacidad} onChange={(e) => setCapacidad(e.target.value)} placeholder="12" />
            </div>
            <Input label="Id del conductor (opcional)" type="number" value={conductorId}
              onChange={(e) => setConductorId(e.target.value)} placeholder="2" />
            <Button type="submit" icon={Plus} block>Registrar vehículo</Button>
            {vehiculoMsg && <Aviso {...vehiculoMsg} />}
          </form>
        </Card>
      </div>

      <Card
        title="Flota registrada"
        action={<span className="text-sm text-slate-400 nums">{vehiculos.length} vehículos</span>}
      >
        {cargando ? (
          <p className="py-10 text-center text-sm text-slate-500">Cargando flota…</p>
        ) : vehiculos.length === 0 ? (
          <div className="py-10 text-center text-sm text-slate-400">
            <Truck className="mx-auto mb-2 opacity-40" size={28} />
            <p>Aún no hay vehículos registrados.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-400">
                  <th className="pb-3 font-semibold">Código</th>
                  <th className="pb-3 font-semibold">Placa</th>
                  <th className="pb-3 font-semibold">Marca</th>
                  <th className="pb-3 font-semibold">Capacidad (m³)</th>
                  <th className="pb-3 font-semibold">Conductor</th>
                  <th className="pb-3 font-semibold">Estado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {vehiculos.map((v) => (
                  <tr key={v.id} className="hover:bg-slate-50">
                    <td className="py-3 font-medium text-slate-800 nums">{v.codigo || "—"}</td>
                    <td className="py-3 text-slate-700">{v.placa}</td>
                    <td className="py-3 text-slate-600">{v.marca || "—"}</td>
                    <td className="py-3 text-slate-600 nums">{v.capacidad_volumetrica ?? "—"}</td>
                    <td className="py-3 text-slate-600">{v.conductor_id ? `id ${v.conductor_id}` : "Empresa"}</td>
                    <td className="py-3"><EstadoBadge estado={v.estado} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

function Aviso({ ok, texto }) {
  return (
    <div className={`flex items-center gap-2 rounded-xl px-3.5 py-3 text-sm ${ok ? "bg-success-soft text-success-strong" : "bg-danger-soft text-danger-strong"}`}>
      {ok ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
      <span>{texto}</span>
    </div>
  );
}
