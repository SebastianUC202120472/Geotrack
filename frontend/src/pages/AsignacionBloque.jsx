import { useEffect, useState } from "react";
import { Truck, MapPin, User, Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import { asignarBloque, listarZonas, listarVehiculos, listarConductores } from "../services/api";

// Asignación de un bloque de pedidos a un conductor (CUS-18).
// El backend asigna la ruta al USUARIO conductor (conductor_id), no al vehículo;
// por eso solo se ofrecen vehículos con conductor vinculado y se envía ese id.
export default function AsignacionBloque() {
  const [zonas, setZonas] = useState([]);
  const [vehiculos, setVehiculos] = useState([]);
  const [nombrePorId, setNombrePorId] = useState({});
  const [distrito, setDistrito] = useState("");
  const [vehiculoId, setVehiculoId] = useState("");
  const [nombreRuta, setNombreRuta] = useState("");
  const [cargando, setCargando] = useState(false);
  const [aviso, setAviso] = useState(null);

  useEffect(() => {
    const cargar = async () => {
      try {
        const [z, v, c] = await Promise.all([listarZonas(), listarVehiculos(), listarConductores()]);
        setZonas(z.zonas_operativas || []);
        setVehiculos(v || []);
        setNombrePorId(Object.fromEntries((c || []).map((x) => [x.usuario_id, x.nombre || x.codigo])));
      } catch (err) {
        console.error("Error al cargar datos:", err.message);
      }
    };
    cargar();
  }, []);

  const vehiculosConConductor = vehiculos.filter((v) => v.conductor_id);
  const zonaSel = zonas.find((z) => z.distrito === distrito);
  const vehiculoSel = vehiculos.find((v) => String(v.id) === String(vehiculoId));

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
        conductor_id: vehiculoSel.conductor_id,
      });
      setAviso({ ok: true, texto: `${res.mensaje} (ruta ${res.codigo || res.ruta_id}).` });
      setNombreRuta(""); setDistrito(""); setVehiculoId("");
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="space-y-6 p-6 lg:p-8">
      <PageHeader titulo="Asignación de Rutas" subtitulo="Arma un bloque logístico y asígnalo a un conductor (CUS-18)." />

      {vehiculosConConductor.length === 0 && (
        <Card className="border-warning/30">
          <div className="flex items-start gap-3 text-warning-strong">
            <AlertCircle size={22} className="shrink-0" />
            <span className="text-sm">
              No hay vehículos con conductor asignado. Ve a <b>Flota y Conductores</b> para registrar un
              conductor y vincularlo a un vehículo antes de asignar rutas.
            </span>
          </div>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Configurar ruta">
          <div className="space-y-5">
            <Input label="Nombre de la ruta" placeholder="Ej. Ruta Norte — Miraflores"
              value={nombreRuta} onChange={(e) => setNombreRuta(e.target.value)} />

            <Input as="select" label="Zona operativa" value={distrito} onChange={(e) => setDistrito(e.target.value)}>
              <option value="">Selecciona una zona</option>
              {zonas.map((z, i) => (
                <option key={i} value={z.distrito}>{z.distrito} ({z.total_pedidos} pedidos)</option>
              ))}
            </Input>

            <Input as="select" label="Vehículo (con conductor)" value={vehiculoId} onChange={(e) => setVehiculoId(e.target.value)}>
              <option value="">Selecciona un vehículo</option>
              {vehiculosConConductor.map((v) => (
                <option key={v.id} value={v.id}>{v.placa} · {nombrePorId[v.conductor_id] || `conductor id ${v.conductor_id}`}</option>
              ))}
            </Input>

            <Button onClick={asignar} disabled={cargando} block size="lg">
              {cargando ? <Loader2 className="animate-spin" size={20} /> : "Confirmar asignación"}
            </Button>

            {aviso && (
              <div className={`flex items-center gap-2 rounded-xl px-3.5 py-3 text-sm ${aviso.ok ? "bg-success-soft text-success-strong" : "bg-danger-soft text-danger-strong"}`}>
                {aviso.ok ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
                <span>{aviso.texto}</span>
              </div>
            )}
          </div>
        </Card>

        <Card title="Impacto logístico">
          {zonaSel && vehiculoSel ? (
            <div className="space-y-4">
              <div className="flex items-center gap-3 rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
                <MapPin className="text-brand-600" size={18} /> Zona: <b>{zonaSel.distrito}</b>
              </div>
              <div className="flex items-center gap-3 rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
                <User className="text-brand-600" size={18} /> Vehículo: <b>{vehiculoSel.placa}</b>
              </div>
              <div className="border-t border-dashed border-slate-200 pt-6 text-center">
                <p className="text-sm text-slate-400">Pedidos a despachar</p>
                <p className="my-1 text-5xl font-bold text-brand-600 nums">{zonaSel.total_pedidos}</p>
              </div>
            </div>
          ) : (
            <div className="flex h-56 flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-200 text-sm text-slate-400">
              <Truck className="mb-2 opacity-40" size={28} />
              <p>Selecciona zona y vehículo para ver el resumen.</p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
