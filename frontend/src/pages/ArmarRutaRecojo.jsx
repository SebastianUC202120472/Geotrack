import { useEffect, useState } from "react";
import { Route as RouteIcon, CheckCircle2, AlertCircle } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import {
  listarSolicitudesAlmacen,
  asignarRutaRecojoAlmacen,
  listarConductores,
  listarVehiculos,
} from "../services/api";

// Página para armar ruta de recojo: selecciona solicitudes y asigna conductor y vehículo.
export default function ArmarRutaRecojo() {
  const [solicitudes, setSolicitudes] = useState([]);
  const [conductores, setConductores] = useState([]);
  const [vehiculos, setVehiculos] = useState([]);
  const [cargando, setCargando] = useState(true);

  const [seleccion, setSeleccion] = useState([]);
  const [conductorId, setConductorId] = useState("");
  const [placa, setPlaca] = useState("");
  const [nombre, setNombre] = useState("");
  const [aviso, setAviso] = useState(null);
  const [guardando, setGuardando] = useState(false);

  // Recarga solicitudes y catálogos desde el backend.
  const cargar = () => {
    setCargando(true);
    listarSolicitudesAlmacen()
      .then((d) => setSolicitudes(d))
      .catch(() => {})
      .finally(() => setCargando(false));
  };

  useEffect(() => {
    let activo = true;
    listarSolicitudesAlmacen()
      .then((d) => activo && setSolicitudes(d))
      .catch(() => {})
      .finally(() => activo && setCargando(false));
    listarConductores().then((d) => activo && setConductores(d)).catch(() => {});
    listarVehiculos().then((d) => activo && setVehiculos(d)).catch(() => {});
    return () => { activo = false; };
  }, []);

  // Alterna selección de una solicitud por id.
  const alternar = (id) =>
    setSeleccion((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

  // Valida la selección y envía la asignación de ruta al backend.
  const enviar = async () => {
    if (!seleccion.length) {
      setAviso({ ok: false, texto: "Selecciona al menos una solicitud." });
      return;
    }
    if (!conductorId) {
      setAviso({ ok: false, texto: "Elige un conductor." });
      return;
    }
    if (!placa) {
      setAviso({ ok: false, texto: "Elige un vehículo." });
      return;
    }
    setGuardando(true);
    setAviso(null);
    asignarRutaRecojoAlmacen({
      recojo_ids: seleccion,
      conductor_id: Number(conductorId),
      vehiculo_placa: placa,
      nombre_ruta: nombre.trim() || null,
    })
      .then((r) => {
        setAviso({ ok: true, texto: r.mensaje });
        setSeleccion([]);
        setConductorId("");
        setPlaca("");
        setNombre("");
        cargar();
      })
      .catch((err) => {
        setAviso({ ok: false, texto: err.message });
      })
      .finally(() => setGuardando(false));
  };

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader
        titulo="Armar ruta de recojo"
        subtitulo="Selecciona las solicitudes aceptadas y asigna conductor y vehículo para crear la ruta."
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-5 py-4">
            <h2 className="font-semibold text-slate-800">Solicitudes disponibles</h2>
            <p className="mt-0.5 text-xs text-slate-400">
              Solo se muestran las solicitudes aceptadas pendientes de asignar.
            </p>
          </div>

          {cargando ? (
            <div className="flex items-center justify-center py-16 text-slate-400 text-sm">
              Cargando solicitudes…
            </div>
          ) : solicitudes.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-16 text-slate-400">
              <RouteIcon size={32} className="opacity-30" />
              <p className="text-sm">No hay solicitudes pendientes de asignar.</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {solicitudes.map((s) => (
                <label
                  key={s.id}
                  className="flex cursor-pointer items-start gap-3 px-5 py-3.5 hover:bg-slate-50 transition-colors"
                >
                  <input
                    type="checkbox"
                    className="mt-0.5 accent-brand-600"
                    checked={seleccion.includes(s.id)}
                    onChange={() => alternar(s.id)}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-slate-800 truncate">
                      {s.cliente_origen}
                    </p>
                    <p className="text-xs text-slate-500 truncate">
                      {s.direccion_origen}
                      {s.distrito ? ` · ${s.distrito}` : ""}
                    </p>
                  </div>
                  <span className="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                    {s.num_pedidos ?? "—"} pedido{s.num_pedidos !== 1 ? "s" : ""}
                  </span>
                </label>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm self-start">
          <div className="border-b border-slate-100 px-5 py-4">
            <h2 className="font-semibold text-slate-800">Asignar ruta</h2>
            <p className="mt-0.5 text-xs text-slate-400">
              {seleccion.length === 0
                ? "Selecciona al menos una solicitud."
                : `${seleccion.length} solicitud${seleccion.length !== 1 ? "es" : ""} seleccionada${seleccion.length !== 1 ? "s" : ""}.`}
            </p>
          </div>

          <div className="space-y-4 p-5">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">
                Conductor
              </label>
              <select
                value={conductorId}
                onChange={(e) => setConductorId(e.target.value)}
                className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="">— Selecciona —</option>
                {conductores.map((c) => {
                  const id = c.usuario_id ?? c.id;
                  return (
                    <option key={id} value={id}>
                      {c.nombre ?? c.correo ?? `Conductor ${id}`}
                    </option>
                  );
                })}
              </select>
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">
                Vehículo
              </label>
              <select
                value={placa}
                onChange={(e) => setPlaca(e.target.value)}
                className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="">— Selecciona —</option>
                {vehiculos.map((v) => (
                  <option key={v.id ?? v.placa} value={v.placa}>
                    {v.placa}
                    {v.codigo ? ` · ${v.codigo}` : ""}
                  </option>
                ))}
              </select>
            </div>

            <Input
              label="Nombre de la ruta"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              hint='Opcional (p. ej. "Recojo Miraflores")'
            />

            <Button
              icon={RouteIcon}
              block
              disabled={guardando || seleccion.length === 0}
              onClick={enviar}
            >
              {guardando ? "Creando…" : "Crear ruta de recojo"}
            </Button>

            {aviso && (
              <div
                className={`flex items-center gap-2 rounded-xl px-3.5 py-3 text-sm ${
                  aviso.ok
                    ? "bg-success-soft text-success-strong"
                    : "bg-danger-soft text-danger-strong"
                }`}
              >
                {aviso.ok ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
                <span>{aviso.texto}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
