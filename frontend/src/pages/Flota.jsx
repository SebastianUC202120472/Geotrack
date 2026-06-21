import { useEffect, useMemo, useState } from "react";
import { Truck, Plus, CheckCircle2, AlertCircle, Pencil, Trash2, Check, X } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import DataTable from "../components/ui/DataTable";
import SectionCard from "../components/ui/SectionCard";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import Modal from "../components/ui/Modal";
import { EstadoBadge } from "../components/ui/Badge";
import { listarVehiculos, crearVehiculo, listarConductores, actualizarVehiculo, eliminarVehiculo } from "../services/api";
import { validarPlaca, validarCapacidad } from "../utils/validaciones";

// Registro de vehículos y su asignación a un conductor. El alta de conductores
// vive en su propia sección (Conductores).
export default function Flota() {
  const [vehiculos, setVehiculos] = useState([]);
  const [conductores, setConductores] = useState([]);
  const [cargando, setCargando] = useState(true);

  const [placa, setPlaca] = useState("");
  const [marca, setMarca] = useState("");
  const [capacidad, setCapacidad] = useState("");
  const [cajas, setCajas] = useState("");
  const [conductorId, setConductorId] = useState("");
  const [errores, setErrores] = useState({});
  const [aviso, setAviso] = useState(null);
  const [editando, setEditando] = useState(null);  // vehículo que se edita/elimina (CUS-08/09)

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

  // KPIs calculados desde los vehículos cargados (sin petición extra).
  const kpis = useMemo(() => {
    const total = vehiculos.length;
    const conConductor = vehiculos.filter((v) => v.conductor_id).length;
    const disponibles = vehiculos.filter((v) => v.estado === "DISPONIBLE").length;
    const enRuta = vehiculos.filter((v) => v.estado === "EN_RUTA").length;
    return { total, conConductor, disponibles, enRuta };
  }, [vehiculos]);

  const altaVehiculo = async (e) => {
    e.preventDefault();
    setAviso(null);

    const errs = { placa: validarPlaca(placa), capacidad: validarCapacidad(capacidad) };
    if (errs.placa || errs.capacidad) {
      setErrores(errs);
      return;
    }
    setErrores({});

    try {
      await crearVehiculo({
        placa,
        marca: marca || null,
        capacidad_volumetrica: capacidad ? Number(capacidad) : null,
        capacidad_cajas: cajas ? Number(cajas) : null,
        conductor_id: conductorId ? Number(conductorId) : null,
      });
      setAviso({ ok: true, texto: "Vehículo registrado correctamente." });
      setPlaca(""); setMarca(""); setCapacidad(""); setCajas(""); setConductorId("");
      cargar();
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
    }
  };

  // Columnas para DataTable
  const columnas = [
    {
      key: "codigo",
      header: "Código",
      render: (v) => <span className="font-medium text-slate-800 nums">{v.codigo || "—"}</span>,
    },
    {
      key: "placa",
      header: "Placa",
      render: (v) => <span className="font-semibold text-slate-700">{v.placa}</span>,
    },
    {
      key: "marca",
      header: "Marca",
      render: (v) => <span className="text-slate-600">{v.marca || "—"}</span>,
    },
    {
      key: "capacidad_volumetrica",
      header: "Cap. (m³)",
      render: (v) => <span className="text-slate-600 nums">{v.capacidad_volumetrica ?? "—"}</span>,
    },
    {
      key: "capacidad_cajas",
      header: "Cajas",
      render: (v) => <span className="text-slate-600 nums">{v.capacidad_cajas ?? "—"}</span>,
    },
    {
      key: "conductor",
      header: "Conductor",
      render: (v) => (
        <span className="text-slate-600">
          {v.conductor_id ? (nombrePorId[v.conductor_id] || `id ${v.conductor_id}`) : "Empresa"}
        </span>
      ),
    },
    {
      key: "estado",
      header: "Estado",
      render: (v) => <EstadoBadge estado={v.estado} />,
    },
    {
      key: "acciones",
      header: "",
      render: (v) => (
        <Button variant="ghost" size="sm" icon={Pencil} onClick={() => { setAviso(null); setEditando(v); }}>
          Editar
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader
        titulo="Flota de Vehículos"
        subtitulo="Registra los vehículos y asígnalos a un conductor."
      />

      {/* KPIs derivados de los vehículos cargados */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 animate-fade-up">
        <KpiCard label="Total" value={kpis.total} icon={Truck} tone="brand" />
        <KpiCard label="Con conductor" value={kpis.conConductor} icon={Truck} tone="info" />
        <KpiCard label="Disponibles" value={kpis.disponibles} icon={Truck} tone="success" />
        <KpiCard label="En ruta" value={kpis.enRuta} icon={Truck} tone="warning" />
      </div>

      <div className="grid gap-6 lg:grid-cols-3 animate-fade-up" style={{ animationDelay: "60ms" }}>
        {/* Formulario de alta */}
        <SectionCard title="Registrar vehículo" subtitle="El conductor es opcional (vacío = de la empresa)." className="lg:col-span-1">
          <form onSubmit={altaVehiculo} noValidate className="space-y-4">
            <Input label="Placa" required value={placa}
              onChange={(e) => { setPlaca(e.target.value.toUpperCase()); setErrores((er) => ({ ...er, placa: "" })); }}
              placeholder="ABC-123" error={errores.placa} hint="3 letras y 3 dígitos (Perú)" />
            <div className="grid grid-cols-2 gap-4">
              <Input label="Marca" value={marca} onChange={(e) => setMarca(e.target.value)} placeholder="Toyota" />
              <Input label="Capacidad (m³)" type="number" min="0" step="0.1" value={capacidad}
                onChange={(e) => { setCapacidad(e.target.value); setErrores((er) => ({ ...er, capacidad: "" })); }}
                placeholder="12" error={errores.capacidad} hint="Mayor a 0 (máx. 100)" />
            </div>
            <Input label="Capacidad (cajas)" type="number" min="0" step="1" value={cajas}
              onChange={(e) => setCajas(e.target.value)} placeholder="200" hint="Cuántas cajas soporta (opcional)" />
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
        </SectionCard>

        {/* Tabla de vehículos */}
        <div className="lg:col-span-2">
          <DataTable
            columns={columnas}
            rows={vehiculos}
            rowKey={(v) => v.id}
            loading={cargando}
            empty={{
              icon: Truck,
              title: "Aún no hay vehículos registrados",
              description: "Usa el formulario de la izquierda para dar de alta el primer vehículo.",
            }}
          />
        </div>
      </div>

      {/* CUS-08/09: editar (marca/capacidades/conductor) o dar de baja un vehículo */}
      <Modal open={!!editando} onClose={() => setEditando(null)} variant="center">
        {editando && (
          <EditarVehiculo
            vehiculo={editando}
            conductores={conductores}
            onCerrar={() => setEditando(null)}
            onCambios={() => { setEditando(null); cargar(); }}
          />
        )}
      </Modal>
    </div>
  );
}

// Edición de un vehículo (CUS-08): marca, capacidades, conductor (CUS-09) y baja.
// Recibe: el vehículo, la lista de conductores y los callbacks de cierre/recarga.
function EditarVehiculo({ vehiculo, conductores, onCerrar, onCambios }) {
  const [modo, setModo] = useState("editar"); // "editar" | "confirmar"
  const [marca, setMarca] = useState(vehiculo.marca || "");
  const [capacidad, setCapacidad] = useState(vehiculo.capacidad_volumetrica ?? "");
  const [cajas, setCajas] = useState(vehiculo.capacidad_cajas ?? "");
  const [conductorId, setConductorId] = useState(vehiculo.conductor_id ? String(vehiculo.conductor_id) : "");
  const [trabajando, setTrabajando] = useState(false);
  const [error, setError] = useState(null);

  const guardar = async () => {
    setTrabajando(true);
    setError(null);
    try {
      await actualizarVehiculo(vehiculo.id, {
        marca: marca.trim() || null,
        capacidad_volumetrica: capacidad === "" ? null : Number(capacidad),
        capacidad_cajas: cajas === "" ? null : Number(cajas),
        conductor_id: conductorId ? Number(conductorId) : null,
      });
      onCambios();
    } catch (err) {
      setError(err.message);
      setTrabajando(false);
    }
  };

  const eliminar = async () => {
    setTrabajando(true);
    setError(null);
    try {
      await eliminarVehiculo(vehiculo.id);
      onCambios();
    } catch (err) {
      setError(err.message);
      setTrabajando(false);
      setModo("editar");
    }
  };

  return (
    <>
      <div className="flex items-start justify-between">
        <div>
          <h2 className="font-bold text-slate-900">Editar vehículo</h2>
          <p className="text-sm text-slate-500 nums">{vehiculo.placa}{vehiculo.codigo ? ` · ${vehiculo.codigo}` : ""}</p>
        </div>
        <button onClick={onCerrar} aria-label="Cerrar" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100">
          <X size={20} />
        </button>
      </div>

      {error && (
        <div className="mt-4 flex items-center gap-2 rounded-xl bg-danger-soft px-3.5 py-3 text-sm text-danger-strong">
          <AlertCircle size={18} /> <span>{error}</span>
        </div>
      )}

      {modo === "editar" ? (
        <div className="mt-6 space-y-4">
          <Input label="Marca" value={marca} onChange={(e) => setMarca(e.target.value)} placeholder="Toyota" />
          <div className="grid grid-cols-2 gap-4">
            <Input label="Capacidad (m³)" type="number" min="0" step="0.1" value={capacidad}
              onChange={(e) => setCapacidad(e.target.value)} placeholder="12" />
            <Input label="Capacidad (cajas)" type="number" min="0" step="1" value={cajas}
              onChange={(e) => setCajas(e.target.value)} placeholder="200" />
          </div>
          <Input as="select" label="Conductor asignado" value={conductorId} onChange={(e) => setConductorId(e.target.value)}>
            <option value="">Sin conductor (de la empresa)</option>
            {conductores.map((c) => (
              <option key={c.usuario_id} value={c.usuario_id}>
                {c.nombre || c.correo} {c.codigo ? `· ${c.codigo}` : ""}
              </option>
            ))}
          </Input>
          <div className="flex gap-2">
            <Button variant="secondary" icon={Trash2} block onClick={() => { setError(null); setModo("confirmar"); }} disabled={trabajando}>Eliminar</Button>
            <Button icon={Check} block onClick={guardar} disabled={trabajando}>{trabajando ? "Guardando…" : "Guardar"}</Button>
          </div>
        </div>
      ) : (
        <div className="mt-6 space-y-4">
          <div className="flex items-start gap-3 rounded-xl bg-danger-soft px-4 py-3 text-sm text-danger-strong">
            <AlertCircle size={20} className="shrink-0" />
            <span>¿Dar de baja el vehículo <b>{vehiculo.placa}</b>? Se quitará de la flota y se liberará su conductor.</span>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" block onClick={() => setModo("editar")} disabled={trabajando}>Cancelar</Button>
            <Button variant="danger" icon={Trash2} block onClick={eliminar} disabled={trabajando}>{trabajando ? "Eliminando…" : "Sí, eliminar"}</Button>
          </div>
        </div>
      )}
    </>
  );
}
