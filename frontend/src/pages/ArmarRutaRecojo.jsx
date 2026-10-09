import { useEffect, useMemo, useState } from "react";
import { Route as RouteIcon, CheckCircle2, AlertCircle, Truck, Package, Boxes, Download, RotateCcw, CalendarDays, AlertTriangle } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import SectionCard from "../components/ui/SectionCard";
import DataTable from "../components/ui/DataTable";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import Badge, { EstadoBadge } from "../components/ui/Badge";
import MapaSolicitudesRecojo from "../components/MapaSolicitudesRecojo";
import {
  listarSolicitudesAlmacen,
  asignarRutaRecojoAlmacen,
  listarConductores,
  listarVehiculos,
  listarRutasRecojoAlmacen,
  descargarManifiesto,
} from "../services/api";

// Fecha local de hoy en formato "AAAA-MM-DD".
const hoyISO = () => new Date().toLocaleDateString("en-CA");

// Etiqueta de la fecha pedida para el recojo: hoy, atrasada o el dia. Recibe la fecha y hoy.
function EtiquetaFecha({ fecha, hoy }) {
  if (!fecha) return null;
  if (fecha < hoy) return <Badge tono="danger"><CalendarDays size={12} />Atrasada · {fecha.split("-").reverse().slice(0, 2).join("/")}</Badge>;
  if (fecha === hoy) return <Badge tono="info"><CalendarDays size={12} />Hoy</Badge>;
  return <Badge tono="neutral"><CalendarDays size={12} />{fecha.split("-").reverse().slice(0, 2).join("/")}</Badge>;
}

// Página para armar la ruta de recojo: mapa de puntos pendientes, volumen total y conductor;
// la placa sale del vehículo del conductor (C12-01, C12-03). Abajo, las rutas de recojo
// con su manifiesto descargable (C22-02).
export default function ArmarRutaRecojo() {
  const [solicitudes, setSolicitudes] = useState([]);
  const [conductores, setConductores] = useState([]);
  const [vehiculos, setVehiculos] = useState([]);
  const [rutas, setRutas] = useState([]);
  const [cargando, setCargando] = useState(true);

  const [seleccion, setSeleccion] = useState([]);
  const [conductorId, setConductorId] = useState("");
  const [nombre, setNombre] = useState("");
  const [aviso, setAviso] = useState(null);
  const [guardando, setGuardando] = useState(false);
  const [version, setVersion] = useState(0); // fuerza la recarga tras crear una ruta

  // Carga solicitudes, conductores, vehiculos y rutas de recojo (el setState va en los .then).
  useEffect(() => {
    let activo = true;
    listarSolicitudesAlmacen()
      .then((d) => activo && setSolicitudes(d))
      .catch(() => {})
      .finally(() => activo && setCargando(false));
    listarConductores().then((d) => activo && setConductores(d)).catch(() => {});
    listarVehiculos().then((d) => activo && setVehiculos(d)).catch(() => {});
    listarRutasRecojoAlmacen().then((d) => activo && setRutas(d)).catch(() => {});
    return () => { activo = false; };
  }, [version]);

  const hoy = hoyISO();
  const capacidadPorVehiculo = useMemo(
    () => Object.fromEntries(vehiculos.map((v) => [v.id, v.capacidad_volumetrica])),
    [vehiculos]
  );
  const conductor = conductores.find((c) => String(c.usuario_id) === conductorId);
  const capacidad = conductor?.vehiculo ? capacidadPorVehiculo[conductor.vehiculo.id] : null;

  // Totales de lo seleccionado: solicitudes, pedidos, volumen y peso (C12-03).
  const totales = useMemo(() => {
    const elegidas = solicitudes.filter((s) => seleccion.includes(s.id));
    return {
      solicitudes: elegidas.length,
      pedidos: elegidas.reduce((a, s) => a + (s.num_pedidos || 0), 0),
      volumen: elegidas.reduce((a, s) => a + (s.volumen_m3 || 0), 0),
      peso: elegidas.reduce((a, s) => a + (s.peso_kg || 0), 0),
    };
  }, [solicitudes, seleccion]);
  const excedeCapacidad = capacidad != null && totales.volumen > capacidad;

  // Alterna selección de una solicitud por id.
  const alternar = (id) =>
    setSeleccion((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

  // Marca todas las solicitudes con fecha de hoy o atrasadas (o todas si ninguna tiene fecha).
  const elegirDeHoy = () => {
    const deHoy = solicitudes.filter((s) => s.fecha_programada && s.fecha_programada <= hoy).map((s) => s.id);
    setSeleccion(deHoy.length ? deHoy : solicitudes.map((s) => s.id));
  };

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
    setGuardando(true);
    setAviso(null);
    asignarRutaRecojoAlmacen({
      recojo_ids: seleccion,
      conductor_id: Number(conductorId),
      nombre_ruta: nombre.trim() || null,
    })
      .then((r) => {
        setAviso({ ok: true, texto: r.mensaje });
        setSeleccion([]);
        setConductorId("");
        setNombre("");
        setVersion((v) => v + 1);
      })
      .catch((err) => setAviso({ ok: false, texto: err.message }))
      .finally(() => setGuardando(false));
  };

  // Descarga el manifiesto Excel de una ruta de recojo. Recibe la fila de la ruta.
  const bajarManifiesto = (r) =>
    descargarManifiesto(r.ruta_id, `manifiesto_${r.codigo || r.ruta_id}.xlsx`)
      .catch((err) => setAviso({ ok: false, texto: err.message }));

  const columnasRutas = [
    { key: "codigo", header: "Ruta", render: (r) => (
      <div>
        <p className="font-medium text-slate-800">{r.nombre}</p>
        <p className="text-xs text-slate-400 nums">{r.codigo}</p>
      </div>
    ) },
    { key: "conductor", header: "Conductor", render: (r) => (
      <div>
        <p className="text-slate-700">{r.conductor || "—"}</p>
        <p className="text-xs text-slate-400">{r.vehiculo_placa || "—"}</p>
      </div>
    ) },
    { key: "avance", header: "Avance", render: (r) => (
      <span className="nums text-sm text-slate-600">
        {r.recogidas}/{r.total_paradas} recogidos
        {r.no_realizadas > 0 && <span className="text-danger-strong"> · {r.no_realizadas} sin éxito</span>}
      </span>
    ) },
    { key: "estado", header: "Estado", render: (r) => <EstadoBadge estado={r.estado} /> },
    { key: "acciones", header: "", render: (r) => (
      <Button variant="ghost" size="sm" icon={Download} onClick={(e) => { e.stopPropagation(); bajarManifiesto(r); }}>Manifiesto</Button>
    ) },
  ];

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader
        titulo="Armar ruta de recojo"
        subtitulo="Elige en el mapa o en la lista los puntos por recoger y asígnalos a un conductor."
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
        <SectionCard
          title="Solicitudes por recoger"
          subtitle="Haz clic en un punto del mapa para agregarlo o quitarlo de la ruta."
          action={solicitudes.length > 0 && (
            <Button variant="secondary" size="sm" onClick={elegirDeHoy}>Elegir las de hoy</Button>
          )}
        >
          {cargando ? (
            <div className="flex items-center justify-center py-16 text-sm text-slate-400">Cargando solicitudes…</div>
          ) : solicitudes.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-16 text-slate-400">
              <RouteIcon size={32} className="opacity-30" />
              <p className="text-sm">No hay solicitudes pendientes de asignar.</p>
            </div>
          ) : (
            <>
              <MapaSolicitudesRecojo solicitudes={solicitudes} seleccion={seleccion} onAlternar={alternar} />
              <div className="mt-4 divide-y divide-slate-100 rounded-xl border border-slate-100">
                {solicitudes.map((s) => (
                  <label key={s.id} className="flex cursor-pointer items-start gap-3 px-4 py-3 transition-colors hover:bg-slate-50">
                    <input
                      type="checkbox"
                      className="mt-1 accent-brand-600"
                      checked={seleccion.includes(s.id)}
                      onChange={() => alternar(s.id)}
                    />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-1.5">
                        <p className="truncate text-sm font-semibold text-slate-800">{s.cliente_origen}</p>
                        <span className="text-xs text-slate-400 nums">{s.codigo}</span>
                        <EtiquetaFecha fecha={s.fecha_programada} hoy={hoy} />
                        {s.intentos_no_realizados > 0 && (
                          <span title={s.motivo_no_realizado || ""}>
                            <Badge tono="warning"><RotateCcw size={12} />Reintento</Badge>
                          </span>
                        )}
                      </div>
                      <p className="truncate text-xs text-slate-500">
                        {s.direccion_origen}{s.distrito ? ` · ${s.distrito}` : ""}
                      </p>
                      {s.motivo_no_realizado && (
                        <p className="mt-0.5 text-xs text-warning-strong">Última visita: {s.motivo_no_realizado}</p>
                      )}
                    </div>
                    <div className="shrink-0 text-right text-xs text-slate-500 nums">
                      <p className="font-semibold text-slate-700">{s.num_pedidos} pedido{s.num_pedidos !== 1 ? "s" : ""}</p>
                      <p>{Number(s.volumen_m3 || 0).toFixed(2)} m³</p>
                    </div>
                  </label>
                ))}
              </div>
            </>
          )}
        </SectionCard>

        <div className="self-start rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-5 py-4">
            <h2 className="font-semibold text-slate-800">Asignar ruta</h2>
            <p className="mt-0.5 text-xs text-slate-400">
              {seleccion.length === 0
                ? "Selecciona al menos una solicitud."
                : `${seleccion.length} solicitud${seleccion.length !== 1 ? "es" : ""} seleccionada${seleccion.length !== 1 ? "s" : ""}.`}
            </p>
          </div>

          <div className="space-y-4 p-5">
            <div className="grid grid-cols-3 gap-2 text-center">
              <Resumen icono={Package} valor={totales.pedidos} etiqueta="Pedidos" />
              <Resumen icono={Boxes} valor={totales.volumen.toFixed(2)} etiqueta="m³" />
              <Resumen icono={Truck} valor={totales.peso.toFixed(0)} etiqueta="kg" />
            </div>

            <Input as="select" label="Conductor" value={conductorId} onChange={(e) => setConductorId(e.target.value)}>
              <option value="">— Selecciona —</option>
              {conductores.map((c) => (
                <option key={c.usuario_id} value={c.usuario_id} disabled={!c.vehiculo}>
                  {c.nombre ?? c.correo}{c.vehiculo ? ` · ${c.vehiculo.placa}` : " · sin vehículo"}{c.en_ruta ? " (en ruta)" : ""}
                </option>
              ))}
            </Input>

            {conductor?.vehiculo && (
              <div className={`flex items-start gap-2 rounded-xl px-3.5 py-3 text-sm ${excedeCapacidad ? "bg-warning-soft text-warning-strong" : "bg-slate-50 text-slate-600"}`}>
                {excedeCapacidad ? <AlertTriangle size={18} className="mt-0.5 shrink-0" /> : <Truck size={18} className="mt-0.5 shrink-0 text-slate-400" />}
                <span>
                  Vehículo <b>{conductor.vehiculo.placa}</b>
                  {capacidad != null ? ` · capacidad ${capacidad} m³` : ""}
                  {excedeCapacidad && ". La carga elegida supera su capacidad: considera dividirla en dos rutas."}
                </span>
              </div>
            )}

            <Input
              label="Nombre de la ruta"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              hint='Opcional (p. ej. "Recojo Miraflores")'
            />

            <Button icon={RouteIcon} block disabled={guardando || seleccion.length === 0} onClick={enviar}>
              {guardando ? "Creando…" : "Crear ruta de recojo"}
            </Button>

            {aviso && (
              <div className={`flex items-center gap-2 rounded-xl px-3.5 py-3 text-sm ${aviso.ok ? "bg-success-soft text-success-strong" : "bg-danger-soft text-danger-strong"}`}>
                {aviso.ok ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
                <span>{aviso.texto}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      <SectionCard title="Rutas de recojo" subtitle="Activas y de los últimos 7 días. Descarga su manifiesto para el despacho.">
        <DataTable
          columns={columnasRutas}
          rows={rutas}
          rowKey={(r) => r.ruta_id}
          empty={{ icon: RouteIcon, title: "Aún no hay rutas de recojo", description: "Las rutas que armes aparecerán aquí." }}
        />
      </SectionCard>
    </div>
  );
}

// Cifra resumida con icono para la tarjeta de asignacion. Recibe icono, valor y etiqueta.
function Resumen({ icono: Icono, valor, etiqueta }) {
  return (
    <div className="rounded-xl bg-slate-50 px-2 py-3">
      <Icono size={16} className="mx-auto text-slate-400" />
      <p className="mt-1 text-lg font-bold text-slate-800 nums">{valor}</p>
      <p className="text-[11px] text-slate-500">{etiqueta}</p>
    </div>
  );
}
