import { useEffect, useState } from "react";
import { Truck, Plus, CheckCircle2, AlertCircle } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import { EstadoBadge } from "../components/ui/Badge";
import { listarVehiculos, crearVehiculo, listarConductores } from "../services/api";

// Registro de vehículos y su asignación a un conductor. El alta de conductores
// vive en su propia sección (Conductores).
export default function Flota() {
  const [vehiculos, setVehiculos] = useState([]);
  const [conductores, setConductores] = useState([]);
  const [cargando, setCargando] = useState(true);

  const [placa, setPlaca] = useState("");
  const [marca, setMarca] = useState("");
  const [capacidad, setCapacidad] = useState("");
  const [conductorId, setConductorId] = useState("");
  const [aviso, setAviso] = useState(null);

  const cargar = async () => {
    setCargando(true);
    try {
      const [v, c] = await Promise.all([listarVehiculos(), listarConductores()]);
      setVehiculos(v);
      setConductores(c);
    } catch (err) {
      console.error("No se pudo cargar la flota:", err.message);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargar();
  }, []);

  // Mapa id de conductor -> nombre, para mostrarlo en la tabla.
  const nombrePorId = Object.fromEntries(conductores.map((c) => [c.usuario_id, c.nombre || c.codigo]));

  const altaVehiculo = async (e) => {
    e.preventDefault();
    setAviso(null);
    try {
      await crearVehiculo({
        placa,
        marca: marca || null,
        capacidad_volumetrica: capacidad ? Number(capacidad) : null,
        conductor_id: conductorId ? Number(conductorId) : null,
      });
      setAviso({ ok: true, texto: "Vehículo registrado correctamente." });
      setPlaca(""); setMarca(""); setCapacidad(""); setConductorId("");
      cargar();
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
    }
  };

  return (
    <div className="space-y-6 p-6 lg:p-8">
      <PageHeader titulo="Flota de Vehículos" subtitulo="Registra los vehículos y asígnalos a un conductor." />

      <div className="grid gap-6 lg:grid-cols-3">
        <Card title="Registrar vehículo" subtitle="El conductor es opcional (vacío = de la empresa)." className="lg:col-span-1">
          <form onSubmit={altaVehiculo} className="space-y-4">
            <Input label="Placa" required value={placa} onChange={(e) => setPlaca(e.target.value)} placeholder="ABC-123" />
            <div className="grid grid-cols-2 gap-4">
              <Input label="Marca" value={marca} onChange={(e) => setMarca(e.target.value)} placeholder="Toyota" />
              <Input label="Capacidad (m³)" type="number" value={capacidad} onChange={(e) => setCapacidad(e.target.value)} placeholder="12" />
            </div>
            <Input as="select" label="Conductor asignado" value={conductorId} onChange={(e) => setConductorId(e.target.value)}>
              <option value="">Sin conductor (de la empresa)</option>
              {conductores.map((c) => (
                <option key={c.usuario_id} value={c.usuario_id}>
                  {c.nombre || c.correo} {c.codigo ? `· ${c.codigo}` : ""}
                </option>
              ))}
            </Input>
            <Button type="submit" icon={Plus} block>Registrar vehículo</Button>
            {aviso && (
              <div className={`flex items-center gap-2 rounded-xl px-3.5 py-3 text-sm ${aviso.ok ? "bg-success-soft text-success-strong" : "bg-danger-soft text-danger-strong"}`}>
                {aviso.ok ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
                <span>{aviso.texto}</span>
              </div>
            )}
          </form>
        </Card>

        <Card
          title="Flota registrada"
          className="lg:col-span-2"
          action={<span className="text-sm text-slate-400 nums">{vehiculos.length} vehículos</span>}
        >
          {cargando ? (
            <p className="py-10 text-center text-sm text-slate-500">Cargando flota…</p>
          ) : vehiculos.length === 0 ? (
            <div className="py-12 text-center text-sm text-slate-400">
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
                      <td className="py-3 text-slate-600">{v.conductor_id ? (nombrePorId[v.conductor_id] || `id ${v.conductor_id}`) : "Empresa"}</td>
                      <td className="py-3"><EstadoBadge estado={v.estado} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
