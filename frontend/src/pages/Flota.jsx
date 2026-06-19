import { useEffect, useMemo, useState } from "react";
import { Truck, Plus, CheckCircle2, AlertCircle } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import DataTable from "../components/ui/DataTable";
import SectionCard from "../components/ui/SectionCard";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import { EstadoBadge } from "../components/ui/Badge";
import { listarVehiculos, crearVehiculo, listarConductores } from "../services/api";
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
  const [conductorId, setConductorId] = useState("");
  const [errores, setErrores] = useState({});
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
        conductor_id: conductorId ? Number(conductorId) : null,
      });
      setAviso({ ok: true, texto: "Vehículo registrado correctamente." });
      setPlaca(""); setMarca(""); setCapacidad(""); setConductorId("");
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
      header: "Capacidad (m³)",
      render: (v) => <span className="text-slate-600 nums">{v.capacidad_volumetrica ?? "—"}</span>,
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
    </div>
  );
}
