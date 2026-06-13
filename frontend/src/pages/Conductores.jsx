import { useEffect, useState } from "react";
import { UserPlus, Users, Truck, X, Phone, IdCard, Mail, CheckCircle2, AlertCircle } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import Badge, { EstadoBadge } from "../components/ui/Badge";
import { listarConductores, crearConductor } from "../services/api";

// Apartado de conductores: ficha completa (nombre, teléfono, DNI), vehículo
// asignado y detalle en un modal. La cuenta (correo/contraseña) es la que el
// conductor usa en la app móvil.
export default function Conductores() {
  const [conductores, setConductores] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [seleccionado, setSeleccionado] = useState(null);

  const [form, setForm] = useState({ nombre: "", correo: "", contrasena: "", telefono: "", dni: "" });
  const [aviso, setAviso] = useState(null);
  const [guardando, setGuardando] = useState(false);

  const cargar = async () => {
    setCargando(true);
    try {
      setConductores(await listarConductores());
    } catch (err) {
      console.error("No se pudo cargar conductores:", err.message);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargar();
  }, []);

  const set = (campo) => (e) => setForm({ ...form, [campo]: e.target.value });

  const registrar = async (e) => {
    e.preventDefault();
    setAviso(null);
    setGuardando(true);
    try {
      const c = await crearConductor({
        nombre: form.nombre,
        correo: form.correo,
        contrasena: form.contrasena,
        telefono: form.telefono || null,
        dni: form.dni || null,
      });
      setAviso({ ok: true, texto: `Conductor ${c.nombre} registrado (${c.codigo}).` });
      setForm({ nombre: "", correo: "", contrasena: "", telefono: "", dni: "" });
      cargar();
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
    } finally {
      setGuardando(false);
    }
  };

  return (
    <div className="space-y-6 p-6 lg:p-8">
      <PageHeader titulo="Conductores" subtitulo="Registra y consulta a los conductores de reparto." />

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Formulario de alta */}
        <Card title="Registrar conductor" className="lg:col-span-1">
          <form onSubmit={registrar} className="space-y-4">
            <Input label="Nombre completo" required value={form.nombre} onChange={set("nombre")} placeholder="Ej. Juan Pérez" />
            <Input label="Correo (acceso a la app)" type="email" required value={form.correo} onChange={set("correo")} placeholder="conductor@siol.com" />
            <Input label="Contraseña inicial" type="password" required value={form.contrasena} onChange={set("contrasena")} placeholder="••••••••" />
            <div className="grid grid-cols-2 gap-4">
              <Input label="Teléfono" value={form.telefono} onChange={set("telefono")} placeholder="999 888 777" />
              <Input label="DNI" value={form.dni} onChange={set("dni")} placeholder="12345678" />
            </div>
            <Button type="submit" icon={UserPlus} block disabled={guardando}>
              {guardando ? "Registrando…" : "Registrar conductor"}
            </Button>
            {aviso && (
              <div className={`flex items-center gap-2 rounded-xl px-3.5 py-3 text-sm ${aviso.ok ? "bg-success-soft text-success-strong" : "bg-danger-soft text-danger-strong"}`}>
                {aviso.ok ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
                <span>{aviso.texto}</span>
              </div>
            )}
          </form>
        </Card>

        {/* Lista */}
        <Card
          title="Conductores registrados"
          className="lg:col-span-2"
          action={<span className="text-sm text-slate-400 nums">{conductores.length}</span>}
        >
          {cargando ? (
            <p className="py-10 text-center text-sm text-slate-500">Cargando…</p>
          ) : conductores.length === 0 ? (
            <div className="py-12 text-center text-sm text-slate-400">
              <Users className="mx-auto mb-2 opacity-40" size={32} />
              <p>Aún no hay conductores registrados.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-400">
                    <th className="pb-3 font-semibold">Código</th>
                    <th className="pb-3 font-semibold">Nombre</th>
                    <th className="pb-3 font-semibold">Teléfono</th>
                    <th className="pb-3 font-semibold">Vehículo</th>
                    <th className="pb-3 font-semibold">Estado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {conductores.map((c) => (
                    <tr key={c.usuario_id} className="cursor-pointer hover:bg-slate-50" onClick={() => setSeleccionado(c)}>
                      <td className="py-3 font-medium text-slate-800 nums">{c.codigo || "—"}</td>
                      <td className="py-3 text-slate-700">{c.nombre || "—"}</td>
                      <td className="py-3 text-slate-600 nums">{c.telefono || "—"}</td>
                      <td className="py-3">
                        {c.vehiculo
                          ? <Badge tono="info"><Truck size={13} /> {c.vehiculo.placa}</Badge>
                          : <span className="text-slate-400">Sin vehículo</span>}
                      </td>
                      <td className="py-3"><EstadoBadge estado={c.estado ? "DISPONIBLE" : "INACTIVO"} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>

      {seleccionado && <DetalleConductor conductor={seleccionado} onCerrar={() => setSeleccionado(null)} />}
    </div>
  );
}

function DetalleConductor({ conductor: c, onCerrar }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-slate-900/50" onClick={onCerrar} />
      <div className="relative w-full max-w-md rounded-card bg-white p-6 shadow-xl">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <span className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-600 text-lg font-bold text-white">
              {(c.nombre || "?").charAt(0).toUpperCase()}
            </span>
            <div>
              <h2 className="font-bold text-slate-900">{c.nombre || "Conductor"}</h2>
              <p className="text-sm text-slate-500 nums">{c.codigo}</p>
            </div>
          </div>
          <button onClick={onCerrar} aria-label="Cerrar" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100">
            <X size={20} />
          </button>
        </div>

        <div className="mt-6 space-y-3">
          <Dato icono={Mail} etiqueta="Correo" valor={c.correo} />
          <Dato icono={Phone} etiqueta="Teléfono" valor={c.telefono || "—"} />
          <Dato icono={IdCard} etiqueta="DNI" valor={c.dni || "—"} />
          <Dato icono={Truck} etiqueta="Vehículo asignado"
            valor={c.vehiculo ? `${c.vehiculo.placa}${c.vehiculo.codigo ? ` (${c.vehiculo.codigo})` : ""}` : "Sin vehículo asignado"} />
        </div>
      </div>
    </div>
  );
}

function Dato({ etiqueta, valor, icono: Icono }) {
  return (
    <div className="flex items-center gap-3 rounded-xl bg-slate-50 px-4 py-3 text-sm">
      <Icono size={18} className="text-slate-400" />
      <div>
        <p className="text-xs text-slate-400">{etiqueta}</p>
        <p className="font-medium text-slate-700">{valor}</p>
      </div>
    </div>
  );
}
