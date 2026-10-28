import { useEffect, useState } from "react";
import { Truck, MapPin, User, Loader2, AlertCircle, CheckCircle2, Route, Package } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import SectionCard from "../components/ui/SectionCard";
import StatCard from "../components/ui/StatCard";
import EmptyState from "../components/ui/EmptyState";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import { asignarBloque, listarZonas, listarVehiculos, listarConductores } from "../services/api";

// Largo máximo del nombre de la ruta (columna rutas.nombre).
const MAX_NOMBRE = 100;

// Asigna un bloque de pedidos de una zona a un conductor. Envía conductor_id (no vehiculo_id).
export default function AsignacionBloque() {
  const [zonas, setZonas] = useState([]);
  const [vehiculos, setVehiculos] = useState([]);
  const [nombrePorId, setNombrePorId] = useState({});
  const [distrito, setDistrito] = useState("");
  const [vehiculoId, setVehiculoId] = useState("");
  const [nombreRuta, setNombreRuta] = useState("");
  const [cargando, setCargando] = useState(false);
  const [aviso, setAviso] = useState(null);

  // Carga zonas, vehículos y conductores al montar.
  useEffect(() => {
    let activo = true;
    Promise.all([listarZonas(), listarVehiculos(), listarConductores()])
      .then(([z, v, c]) => {
        if (!activo) return;
        setZonas(z.zonas_operativas || []);
        setVehiculos(v || []);
        setNombrePorId(Object.fromEntries((c || []).map((x) => [x.usuario_id, x.nombre || x.codigo])));
      })
      .catch((err) => console.error("Error al cargar datos:", err.message));
    return () => { activo = false; };
  }, []);

  const vehiculosConConductor = vehiculos.filter((v) => v.conductor_id);
  const zonaSel = zonas.find((z) => z.distrito === distrito);
  const vehiculoSel = vehiculos.find((v) => String(v.id) === String(vehiculoId));
  const nombreAuto = distrito ? `Ruta ${distrito}` : "";
  const nombreFinal = nombreRuta.trim() || nombreAuto;

  // Vuelve a pedir las zonas para que la recién despachada ya no aparezca con pedidos.
  const recargarZonas = () =>
    listarZonas()
      .then((z) => setZonas(z.zonas_operativas || []))
      .catch((err) => console.error("Error al recargar zonas:", err.message));

  const asignar = async () => {
    if (!distrito || !vehiculoId) {
      setAviso({ ok: false, texto: "Selecciona la zona y el vehículo." });
      return;
    }
    setCargando(true);
    setAviso(null);
    try {
      const res = await asignarBloque({
        nombre_ruta: nombreRuta.trim() || null,
        distrito,
        conductor_id: vehiculoSel.conductor_id,
      });
      setAviso({ ok: true, texto: `${res.mensaje} (ruta ${res.codigo || res.ruta_id}).` });
      setDistrito(""); setVehiculoId(""); setNombreRuta("");
      recargarZonas();
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
      recargarZonas();
    } finally {
      setCargando(false);
    }
  };

  const totalZonas = zonas.length;
  const totalVehiculos = vehiculosConConductor.length;
  const totalPedidos = zonaSel ? zonaSel.total_pedidos : zonas.reduce((acc, z) => acc + (z.total_pedidos || 0), 0);

  return (
    <div className="space-y-6 p-6 lg:p-8 bg-canvas min-h-full">
      <div className="animate-fade-up">
        <PageHeader
          titulo="Asignación de Rutas"
          subtitulo="Arma un bloque logístico y asígnalo a un conductor."
        />
      </div>

      {vehiculosConConductor.length === 0 && (
        <div className="animate-fade-up" style={{ animationDelay: "60ms" }}>
          <SectionCard>
            <div className="flex items-start gap-3 text-warning-strong">
              <AlertCircle size={22} className="shrink-0 mt-0.5" />
              <span className="text-sm leading-relaxed">
                No hay vehículos con conductor asignado. Ve a <b>Flota y Conductores</b> para registrar un
                conductor y vincularlo a un vehículo antes de asignar rutas.
              </span>
            </div>
          </SectionCard>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-3 animate-fade-up" style={{ animationDelay: "80ms" }}>
        <StatCard
          label="Zonas disponibles"
          value={totalZonas}
          icon={MapPin}
          tone="brand"
          hint="Zonas con pedidos en cola"
        />
        <StatCard
          label="Vehículos con conductor"
          value={totalVehiculos}
          icon={Truck}
          tone="info"
          hint="Listos para asignación"
        />
        <StatCard
          label={zonaSel ? `Pedidos · ${zonaSel.distrito}` : "Pedidos (todas las zonas)"}
          value={totalPedidos}
          icon={Package}
          tone="warning"
          hint={zonaSel ? "En la zona seleccionada" : "Total en todas las zonas"}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">

        <div className="animate-fade-up" style={{ animationDelay: "120ms" }}>
          <SectionCard
            title="Configurar ruta"
            subtitle="Elige la zona operativa y el vehículo conductor."
          >
            <div className="space-y-5">
              <Input
                as="select"
                label="Zona operativa"
                value={distrito}
                onChange={(e) => setDistrito(e.target.value)}
              >
                <option value="">Selecciona una zona</option>
                {zonas.map((z, i) => (
                  <option key={i} value={z.distrito}>
                    {z.distrito} ({z.total_pedidos} pedidos)
                  </option>
                ))}
              </Input>

              <Input
                label="Nombre de la ruta (opcional)"
                value={nombreRuta}
                maxLength={MAX_NOMBRE}
                onChange={(e) => setNombreRuta(e.target.value)}
                placeholder={nombreAuto || "Ruta Miraflores mañana"}
                hint={nombreAuto ? `Si lo dejas vacío se llamará «${nombreAuto}».` : "Si lo dejas vacío se usa el nombre de la zona."}
              />

              <Input
                as="select"
                label="Vehículo (con conductor)"
                value={vehiculoId}
                onChange={(e) => setVehiculoId(e.target.value)}
              >
                <option value="">Selecciona un vehículo</option>
                {vehiculosConConductor.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.placa} · {nombrePorId[v.conductor_id] || `conductor id ${v.conductor_id}`}
                  </option>
                ))}
              </Input>

              <Button onClick={asignar} disabled={cargando} block size="lg">
                {cargando ? <Loader2 className="animate-spin" size={20} /> : "Confirmar asignación"}
              </Button>

              {aviso && (
                <div
                  className={`flex items-start gap-3 rounded-xl px-4 py-3 text-sm ${
                    aviso.ok
                      ? "bg-success-soft text-success-strong border border-success/20"
                      : "bg-danger-soft text-danger-strong border border-danger/20"
                  }`}
                >
                  {aviso.ok ? (
                    <CheckCircle2 size={18} className="shrink-0 mt-0.5" />
                  ) : (
                    <AlertCircle size={18} className="shrink-0 mt-0.5" />
                  )}
                  <span>{aviso.texto}</span>
                </div>
              )}
            </div>
          </SectionCard>
        </div>

        <div className="animate-fade-up" style={{ animationDelay: "160ms" }}>
          <SectionCard
            title="Impacto logístico"
            subtitle="Resumen de la asignación antes de confirmar."
          >
            {zonaSel && vehiculoSel ? (
              <div className="space-y-3">
                <div className="flex items-center gap-3 rounded-xl bg-slate-50 border border-warm-200 px-4 py-3 text-sm text-slate-700">
                  <Route className="text-brand-600 shrink-0" size={18} />
                  <span className="min-w-0 truncate">Ruta:&nbsp;<b>{nombreFinal}</b></span>
                </div>

                <div className="flex items-center gap-3 rounded-xl bg-slate-50 border border-warm-200 px-4 py-3 text-sm text-slate-700">
                  <MapPin className="text-brand-600 shrink-0" size={18} />
                  <span>Zona:&nbsp;<b>{zonaSel.distrito}</b></span>
                </div>

                <div className="flex items-center gap-3 rounded-xl bg-slate-50 border border-warm-200 px-4 py-3 text-sm text-slate-700">
                  <Truck className="text-brand-600 shrink-0" size={18} />
                  <span>Vehículo:&nbsp;<b>{vehiculoSel.placa}</b></span>
                </div>

                {vehiculoSel.conductor_id && (
                  <div className="flex items-center gap-3 rounded-xl bg-slate-50 border border-warm-200 px-4 py-3 text-sm text-slate-700">
                    <User className="text-brand-600 shrink-0" size={18} />
                    <span>
                      Conductor:&nbsp;
                      <b>{nombrePorId[vehiculoSel.conductor_id] || `id ${vehiculoSel.conductor_id}`}</b>
                    </span>
                  </div>
                )}

                <div className="mt-2 rounded-xl border-2 border-dashed border-brand-200 bg-brand-50/50 py-8 text-center">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Pedidos a despachar
                  </p>
                  <p className="my-2 text-6xl font-bold text-brand-600 nums">
                    {zonaSel.total_pedidos}
                  </p>
                  <p className="text-xs text-slate-400">en {zonaSel.distrito}</p>
                </div>
              </div>
            ) : (
              <EmptyState
                icon={Truck}
                title="Sin selección aún"
                description="Selecciona una zona y un vehículo para ver el resumen del bloque logístico."
              />
            )}
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
