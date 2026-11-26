import { useCallback, useEffect, useState } from "react";
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Search,
  ZoomIn,
  ZoomOut,
  Users,
  MapPin,
  Cpu,
  Sparkles,
  X,
  ExternalLink,
  Copy,
  Sun,
} from "lucide-react";
import PageHeader from "../../components/ui/PageHeader";
import KpiCard from "../../components/ui/KpiCard";
import SectionCard from "../../components/ui/SectionCard";
import DataTable from "../../components/ui/DataTable";
import Input from "../../components/ui/Input";
import Button from "../../components/ui/Button";
import Badge from "../../components/ui/Badge";
import Modal from "../../components/ui/Modal";
import { usePestanasPagina } from "../../components/ui/PestanasPagina";
import { useAuth } from "../../hooks/useAuth";
import {
  listarEvidencias,
  obtenerDetalleEvidencia,
  obtenerMetricasAuditoria,
  obtenerUrlImagenEvidencia,
  registrarDictamen,
  sembrarDemoAuditoria,
  sincronizarAuditoriaAhora,
} from "./servicioAuditoria";

const VISTAS_AUDITORIA = [
  ["cola", "Cola de revisión", ShieldCheck],
  ["conductores", "Reincidencia por conductor", Users],
];

const MOTIVOS_RAPIDOS = [
  "No se distingue paquete",
  "Foto borrosa u oscura",
  "Ubicación GPS no coincide",
  "Foto reciclada de otro pedido",
];

const fmt = (f) =>
  f ? new Date(f).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" }) : "—";

function BadgeSemaforo({ semaforo }) {
  if (semaforo === "rojo") {
    return (
      <Badge tono="danger">
        <span className="h-1.5 w-1.5 rounded-full bg-danger" />
        Rojo · Alerta
      </Badge>
    );
  }
  if (semaforo === "ambar") {
    return (
      <Badge tono="warning">
        <span className="h-1.5 w-1.5 rounded-full bg-warning" />
        Ámbar · Revisar
      </Badge>
    );
  }
  return (
    <Badge tono="success">
      <span className="h-1.5 w-1.5 rounded-full bg-success" />
      Verde · Confiable
    </Badge>
  );
}

function BadgeDictamen({ estado }) {
  if (estado === "VALIDA") return <Badge tono="success">Válida</Badge>;
  if (estado === "OBSERVADA") return <Badge tono="danger">Observada</Badge>;
  return <Badge tono="neutral">Pendiente</Badge>;
}

export default function PaginaAuditoria() {
  const { rol } = useAuth();
  const [vista, pestanas] = usePestanasPagina(VISTAS_AUDITORIA, "Vistas de auditoría");
  const [evidencias, setEvidencias] = useState([]);
  const [metricas, setMetricas] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [sincronizando, setSincronizando] = useState(false);
  const [cargandoDemo, setCargandoDemo] = useState(false);
  const [error, setError] = useState("");

  // Filtros de la cola
  const [semaforo, setSemaforo] = useState("");
  const [estadoRevision, setEstadoRevision] = useState("");
  const [pedidoCodigo, setPedidoCodigo] = useState("");
  const [soloConReclamo, setSoloConReclamo] = useState(false);

  // Drawer lateral de detalle
  const [seleccionada, setSeleccionada] = useState(null);
  const [urlImagen, setUrlImagen] = useState(null);
  const [zoom, setZoom] = useState(false);
  const [motivoDictamen, setMotivoDictamen] = useState("");
  const [guardandoDictamen, setGuardandoDictamen] = useState(false);
  const [errorDetalle, setErrorDetalle] = useState("");

  const recargar = useCallback(async () => {
    setError("");
    try {
      const [lista, kpis] = await Promise.all([
        listarEvidencias({
          semaforo: semaforo || undefined,
          estadoRevision: estadoRevision || undefined,
          pedidoCodigo: pedidoCodigo || undefined,
          soloConReclamo,
        }),
        obtenerMetricasAuditoria(),
      ]);
      setEvidencias(Array.isArray(lista) ? lista : []);
      setMetricas(kpis);
    } catch (e) {
      setError(e.message || "No se pudo cargar la auditoría de evidencias");
    } finally {
      setCargando(false);
    }
  }, [semaforo, estadoRevision, pedidoCodigo, soloConReclamo]);

  useEffect(() => {
    if (rol !== "admin") return;
    let cancelado = false;
    Promise.all([
      listarEvidencias({
        semaforo: semaforo || undefined,
        estadoRevision: estadoRevision || undefined,
        pedidoCodigo: pedidoCodigo || undefined,
        soloConReclamo,
      }),
      obtenerMetricasAuditoria(),
    ])
      .then(([lista, kpis]) => {
        if (cancelado) return;
        setEvidencias(Array.isArray(lista) ? lista : []);
        setMetricas(kpis);
        setError("");
      })
      .catch((e) => {
        if (!cancelado) setError(e.message || "No se pudo cargar la auditoría de evidencias");
      })
      .finally(() => {
        if (!cancelado) setCargando(false);
      });
    return () => {
      cancelado = true;
    };
  }, [rol, semaforo, estadoRevision, pedidoCodigo, soloConReclamo]);

  useEffect(() => {
    return () => {
      if (urlImagen) URL.revokeObjectURL(urlImagen);
    };
  }, [urlImagen]);

  if (rol !== "admin") {
    return (
      <div className="space-y-5 px-6 pb-6 pt-4 lg:px-8 lg:pb-8 lg:pt-5 animate-fade-in">
        <div className="rounded-card border border-warning/40 bg-warning-soft p-6 text-warning-strong">
          Esta pantalla de auditoría de evidencias está restringida a administradores.
        </div>
      </div>
    );
  }

  const abrirDetalle = async (fila) => {
    const id = typeof fila === "object" ? fila.id : fila;
    setErrorDetalle("");
    setMotivoDictamen("");
    setZoom(false);
    if (urlImagen) {
      URL.revokeObjectURL(urlImagen);
      setUrlImagen(null);
    }
    try {
      const [detalle, imgUrl] = await Promise.all([
        obtenerDetalleEvidencia(id),
        obtenerUrlImagenEvidencia(id).catch(() => null),
      ]);
      setSeleccionada(detalle);
      setUrlImagen(imgUrl);
    } catch (e) {
      setError(e.message || "No se pudo abrir el detalle de la evidencia");
    }
  };

  const cerrarDetalle = () => {
    setSeleccionada(null);
    if (urlImagen) {
      URL.revokeObjectURL(urlImagen);
      setUrlImagen(null);
    }
  };

  const manejarDictamen = async (dictamen) => {
    if (!seleccionada) return;
    if (dictamen === "OBSERVADA" && !motivoDictamen.trim()) {
      setErrorDetalle("Selecciona o escribe el motivo por el cual observas esta evidencia.");
      return;
    }
    setGuardandoDictamen(true);
    setErrorDetalle("");
    try {
      await registrarDictamen(seleccionada.id, dictamen, motivoDictamen.trim());
      await abrirDetalle(seleccionada.id);
      await recargar();
    } catch (e) {
      setErrorDetalle(e.message || "No se pudo registrar el dictamen");
    } finally {
      setGuardandoDictamen(false);
    }
  };

  const manejarSincronizacion = async () => {
    setSincronizando(true);
    setError("");
    try {
      await sincronizarAuditoriaAhora();
      await recargar();
    } catch (e) {
      setError(e.message || "Error al sincronizar evidencias");
    } finally {
      setSincronizando(false);
    }
  };

  const manejarCargarDemo = async () => {
    setCargandoDemo(true);
    setError("");
    try {
      await sembrarDemoAuditoria();
      await recargar();
    } catch (e) {
      setError(e.message || "Error al cargar evidencias de demostración");
    } finally {
      setCargandoDemo(false);
    }
  };

  const columnasCola = [
    {
      key: "pedido_codigo",
      header: "Pedido",
      render: (ev) => (
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <p className="font-semibold text-slate-800 nums">{ev.pedido_codigo || `#${ev.pedido_id}`}</p>
            {ev.tiene_reclamo && (
              <Badge tono="danger">Reclamo ({ev.reclamos_count})</Badge>
            )}
          </div>
          <p className="text-xs text-slate-500 line-clamp-1">
            {ev.pedido_distrito ? `${ev.pedido_distrito} · ` : ""}
            {ev.direccion_destino || "Sin dirección"}
          </p>
        </div>
      ),
    },
    {
      key: "conductor_nombre",
      header: "Conductor",
      render: (ev) => (
        <div>
          <p className="font-medium text-slate-700">
            {ev.conductor_nombre || (ev.conductor_id ? `Conductor #${ev.conductor_id}` : "Sin asignar")}
          </p>
          <p className="text-xs text-slate-400 nums">{fmt(ev.fecha_entrega || ev.creado_en)}</p>
        </div>
      ),
    },
    {
      key: "semaforo",
      header: "Semáforo",
      render: (ev) => <BadgeSemaforo semaforo={ev.semaforo} />,
    },
    {
      key: "motivo_alerta",
      header: "Diagnóstico (Python + IA)",
      render: (ev) => (
        <div className="max-w-md space-y-1">
          <p className="text-xs font-medium text-slate-700 line-clamp-2">
            {ev.motivo_alerta || ev.vision_explicacion || "Evidencia nítida y consistente"}
          </p>
          <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-slate-400">
            <span className="nums">Calidad {Math.round((ev.calidad_score || 0) * 100)}%</span>
            {ev.es_duplicada && <span className="font-semibold text-danger-strong">· Reciclada</span>}
            {ev.vision_analizada && <span className="text-brand-600 font-medium">· Visión IA</span>}
          </div>
        </div>
      ),
    },
    {
      key: "estado_revision",
      header: "Dictamen humano",
      render: (ev) => <BadgeDictamen estado={ev.estado_revision} />,
    },
  ];

  const columnasConductores = [
    {
      key: "conductor_nombre",
      header: "Conductor",
      render: (c) => <span className="font-semibold text-slate-800">{c.conductor_nombre}</span>,
    },
    {
      key: "total_analizadas",
      header: "Evidencias analizadas",
      className: "nums",
      render: (c) => <span className="nums">{c.total_analizadas}</span>,
    },
    {
      key: "total_alertas_rojas",
      header: "Alertas rojas (sistema)",
      className: "nums",
      render: (c) => (
        c.total_alertas_rojas > 0
          ? <Badge tono="danger" className="nums">{c.total_alertas_rojas}</Badge>
          : <span className="text-slate-400 nums">0</span>
      ),
    },
    {
      key: "total_observadas",
      header: "Confirmadas observadas (humano)",
      className: "nums",
      render: (c) => <span className="font-semibold text-slate-800 nums">{c.total_observadas}</span>,
    },
    {
      key: "porcentaje_observadas",
      header: "% Reincidencia",
      className: "nums",
      render: (c) => (
        <Badge tono={c.porcentaje_observadas >= 25 ? "danger" : c.porcentaje_observadas > 0 ? "warning" : "success"} className="nums">
          {c.porcentaje_observadas}%
        </Badge>
      ),
    },
  ];

  return (
    <div className="space-y-5 px-6 pb-6 pt-4 lg:px-8 lg:pb-8 lg:pt-5 animate-fade-in">
      <PageHeader
        titulo="Auditoría de evidencias"
        subtitulo="Control de calidad y detección de anomalías asistido por IA. La decisión final siempre es humana."
      >
        <Button
          variant="secondary"
          size="sm"
          icon={Sparkles}
          disabled={cargandoDemo}
          onClick={manejarCargarDemo}
        >
          {cargandoDemo ? "Generando demo..." : "Cargar evidencias demo"}
        </Button>
        <Button
          variant="primary"
          size="sm"
          icon={RefreshCw}
          disabled={sincronizando}
          onClick={manejarSincronizacion}
        >
          {sincronizando ? "Analizando..." : "Sincronizar"}
        </Button>
      </PageHeader>

      {error && (
        <p className="rounded-xl bg-danger-soft px-4 py-3 text-sm font-medium text-danger-strong">
          {error}
        </p>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 animate-fade-up">
        <KpiCard
          label="Evidencias analizadas"
          value={metricas?.total_analizadas ?? 0}
          icon={ShieldCheck}
          tone="brand"
          trend={
            metricas
              ? { dir: "up", text: `${metricas.total_verde} verde · ${metricas.total_ambar} ámbar · ${metricas.total_rojo} rojo` }
              : undefined
          }
        />
        <KpiCard
          label="Pendientes de revisión"
          value={metricas?.pendientes_revision ?? 0}
          icon={AlertTriangle}
          tone="warning"
        />
        <KpiCard
          label="Observadas (humano)"
          value={metricas?.total_observadas ?? 0}
          icon={XCircle}
          tone="danger"
          trend={
            metricas
              ? { dir: metricas.porcentaje_observadas > 0 ? "down" : "up", text: `${metricas.porcentaje_observadas}% del total` }
              : undefined
          }
        />
        <KpiCard
          label="Falsas alarmas"
          value={metricas?.falsas_alarmas ?? 0}
          icon={CheckCircle2}
          tone="success"
          trend={
            metricas
              ? { dir: "up", text: `${metricas.tasa_falsas_alarmas}% de alertas revisadas` }
              : undefined
          }
        />
      </div>

      {pestanas}

      {vista === "cola" && (
        <SectionCard
          className="animate-fade-up"
          title="Cola de evidencias"
          subtitle={`${evidencias.length} registros (haz clic en una fila para revisar la foto y dictaminar)`}
          action={
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative">
                <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <Input
                  value={pedidoCodigo}
                  onChange={(e) => setPedidoCodigo(e.target.value)}
                  placeholder="Buscar pedido (ej. PD-001)"
                  className="pl-9"
                />
              </div>

              <Input as="select" value={semaforo} onChange={(e) => setSemaforo(e.target.value)}>
                <option value="">Todos los semáforos</option>
                <option value="rojo">Solo Rojo (Alerta alta)</option>
                <option value="ambar">Solo Ámbar (Revisar)</option>
                <option value="verde">Solo Verde (Confiable)</option>
              </Input>

              <Input as="select" value={estadoRevision} onChange={(e) => setEstadoRevision(e.target.value)}>
                <option value="">Todos los dictámenes</option>
                <option value="PENDIENTE">Pendientes</option>
                <option value="VALIDA">Válidas</option>
                <option value="OBSERVADA">Observadas</option>
              </Input>

              <Button
                variant={soloConReclamo ? "danger" : "secondary"}
                size="sm"
                icon={AlertTriangle}
                onClick={() => setSoloConReclamo((v) => !v)}
              >
                Con reclamo
              </Button>
            </div>
          }
        >
          <DataTable
            columns={columnasCola}
            rows={evidencias}
            rowKey={(ev) => ev.id}
            loading={cargando}
            onRowClick={abrirDetalle}
            empty={{
              icon: ShieldCheck,
              title: "Sin evidencias auditadas para este filtro",
              description:
                "Si aún no hay fotos locales en este servidor, usa el botón «Cargar evidencias demo» arriba a la derecha para probar el flujo con IA.",
            }}
          />
        </SectionCard>
      )}

      {vista === "conductores" && (
        <SectionCard
          className="animate-fade-up"
          title="Reincidencia por conductor"
          subtitle="Consolidado de alertas del sistema y evidencias confirmadas como observadas por un administrador"
        >
          <DataTable
            columns={columnasConductores}
            rows={metricas?.reincidencia_conductores || []}
            rowKey={(c) => c.conductor_id ?? c.conductor_nombre}
            loading={cargando}
            empty={{
              icon: Users,
              title: "Sin datos de conductores",
              description: "Los indicadores por conductor aparecerán en cuanto se auditen evidencias.",
            }}
          />
        </SectionCard>
      )}

      <Modal open={!!seleccionada} onClose={cerrarDetalle} variant="right" className="max-w-lg">
        {seleccionada && (
          <>
            <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
              <div className="flex items-center gap-2.5">
                <ShieldCheck size={20} className="text-brand-600 shrink-0" />
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="font-bold text-slate-900 nums">
                      {seleccionada.pedido_codigo || `Pedido #${seleccionada.pedido_id}`}
                    </h2>
                    <BadgeSemaforo semaforo={seleccionada.semaforo} />
                  </div>
                  <p className="text-xs text-slate-500">
                    {seleccionada.conductor_nombre || "Conductor"} · {fmt(seleccionada.fecha_entrega || seleccionada.creado_en)}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={cerrarDetalle}
                aria-label="Cerrar"
                className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-4 px-6 py-5">
              {/* Fotografía con zoom */}
              <div>
                <div className="relative overflow-hidden rounded-xl border border-slate-200 bg-slate-100">
                  {urlImagen ? (
                    <img
                      src={urlImagen}
                      alt="Evidencia fotográfica de entrega"
                      onClick={() => setZoom(!zoom)}
                      className={`w-full cursor-pointer object-contain transition-transform duration-200 ${
                        zoom ? "scale-150" : "max-h-64"
                      }`}
                    />
                  ) : (
                    <div className="flex h-48 items-center justify-center text-xs text-slate-400">
                      Fotografía no disponible localmente
                    </div>
                  )}
                  {urlImagen && (
                    <button
                      type="button"
                      onClick={() => setZoom(!zoom)}
                      className="absolute bottom-2.5 right-2.5 inline-flex items-center gap-1 rounded-lg bg-slate-900/75 px-2.5 py-1 text-xs font-medium text-white"
                    >
                      {zoom ? <ZoomOut size={14} /> : <ZoomIn size={14} />}
                      {zoom ? "Reducir" : "Ampliar"}
                    </button>
                  )}
                </div>

                <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
                  <span>{seleccionada.direccion_destino || "Sin dirección registrada"}</span>
                  {seleccionada.latitud_longitud_captura && (
                    <a
                      href={`https://www.google.com/maps?q=${seleccionada.latitud_longitud_captura}`}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 font-semibold text-brand-600 hover:underline"
                    >
                      Ver GPS en mapa <ExternalLink size={12} />
                    </a>
                  )}
                </div>
              </div>

              {/* Reclamos activos del pedido */}
              {seleccionada.reclamos?.length > 0 && (
                <div className="rounded-xl border border-danger/30 bg-danger-soft p-3.5 text-xs text-danger-strong space-y-1">
                  <p className="font-bold flex items-center gap-1.5">
                    <AlertTriangle size={15} /> Reclamo registrado por el cliente:
                  </p>
                  {seleccionada.reclamos.map((rec) => (
                    <p key={rec.id}>
                      • <strong>{rec.codigo || rec.tipo}:</strong> {rec.detalle}
                    </p>
                  ))}
                </div>
              )}

              {/* Motivo de alerta principal */}
              {seleccionada.motivo_alerta && (
                <div className="rounded-xl border border-warning/40 bg-warning-soft p-3.5 text-xs text-warning-strong">
                  <span className="font-bold">Motivo de alerta: </span>
                  {seleccionada.motivo_alerta}
                </div>
              )}

              {/* Checklist Determinístico en Grilla 2x2 */}
              <div className="grid grid-cols-2 gap-2.5 text-xs">
                <div className="rounded-xl border border-slate-200 bg-warm-50 p-3">
                  <div className="flex items-center justify-between text-slate-500">
                    <span>Calidad visual</span>
                    <Sun size={14} />
                  </div>
                  <p className="mt-1 text-base font-bold text-slate-900 nums">
                    {Math.round((seleccionada.calidad_score || 0) * 100)}%
                  </p>
                  <p className="text-[11px] text-slate-500">
                    {seleccionada.es_borrosa
                      ? "Desenfocada"
                      : seleccionada.es_oscura
                      ? "Subexpuesta / oscura"
                      : `${seleccionada.resolucion_ancho || 0}×${seleccionada.resolucion_alto || 0} px`}
                  </p>
                </div>

                <div className="rounded-xl border border-slate-200 bg-warm-50 p-3">
                  <div className="flex items-center justify-between text-slate-500">
                    <span>Huella ImageHash</span>
                    <Copy size={14} />
                  </div>
                  <p className={`mt-1 text-base font-bold ${seleccionada.es_duplicada ? "text-danger-strong" : "text-slate-900"}`}>
                    {seleccionada.es_duplicada ? "Reciclada" : "Única"}
                  </p>
                  <p className="text-[11px] text-slate-500">
                    {seleccionada.es_duplicada
                      ? `Coincide con #${seleccionada.duplicada_con_evidencia_id}`
                      : "Sin duplicidad previa"}
                  </p>
                </div>

                <div className="rounded-xl border border-slate-200 bg-warm-50 p-3">
                  <div className="flex items-center justify-between text-slate-500">
                    <span>Distancia GPS</span>
                    <MapPin size={14} />
                  </div>
                  <p className={`mt-1 text-base font-bold nums ${seleccionada.alerta_gps ? "text-warning-strong" : "text-slate-900"}`}>
                    {seleccionada.distancia_gps_metros != null ? `${seleccionada.distancia_gps_metros} m` : "—"}
                  </p>
                  <p className="text-[11px] text-slate-500">
                    {seleccionada.alerta_gps ? "Lejos del destino (>350 m)" : "Dentro del radio esperado"}
                  </p>
                </div>

                <div className="rounded-xl border border-slate-200 bg-warm-50 p-3">
                  <div className="flex items-center justify-between text-slate-500">
                    <span>Receptor POD</span>
                    <Users size={14} />
                  </div>
                  <p className="mt-1 truncate text-sm font-bold text-slate-900">
                    {seleccionada.receptor_nombre || "No registrado"}
                  </p>
                  <p className="text-[11px] text-slate-500 nums">
                    {seleccionada.receptor_documento ? `Doc: ${seleccionada.receptor_documento}` : "Sin documento"}
                  </p>
                </div>
              </div>

              {/* Bloque Visión IA */}
              <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                    <Cpu size={15} className="text-brand-600" />
                    Análisis de Visión IA
                  </span>
                  {seleccionada.vision_proveedor && (
                    <Badge tono="brand">{seleccionada.vision_proveedor}</Badge>
                  )}
                </div>

                {seleccionada.vision_analizada ? (
                  <>
                    <div className="flex flex-wrap gap-1.5">
                      <Badge tono={seleccionada.vision_paquete ? "success" : "warning"}>
                        Paquete: {seleccionada.vision_paquete ? "Sí" : "No"}
                      </Badge>
                      <Badge tono={seleccionada.vision_fachada ? "success" : "neutral"}>
                        Puerta/Fachada: {seleccionada.vision_fachada ? "Sí" : "No"}
                      </Badge>
                      <Badge tono={seleccionada.vision_persona ? "success" : "neutral"}>
                        Persona: {seleccionada.vision_persona ? "Sí" : "No"}
                      </Badge>
                    </div>
                    <p className="text-xs leading-relaxed text-slate-600">
                      {seleccionada.vision_explicacion}
                    </p>
                  </>
                ) : (
                  <p className="text-xs text-slate-500">
                    Omitido por cortocircuito determinístico (ahorro de cuota en fotos oscuras o recicladas).
                  </p>
                )}
              </div>

              {/* Bloque de Dictamen Humano */}
              <div className="space-y-3 rounded-xl border border-slate-200 bg-warm-50 p-4">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-bold text-slate-800">Dictamen del administrador</p>
                  <BadgeDictamen estado={seleccionada.estado_revision} />
                </div>

                <div className="flex flex-wrap gap-1.5">
                  {MOTIVOS_RAPIDOS.map((m) => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => setMotivoDictamen(m)}
                      className={`rounded-full border px-2.5 py-1 text-[11px] font-medium transition-colors ${
                        motivoDictamen === m
                          ? "border-brand-600 bg-brand-50 text-brand-700"
                          : "border-slate-200 bg-white text-slate-600 hover:bg-slate-100"
                      }`}
                    >
                      {m}
                    </button>
                  ))}
                </div>

                <Input
                  as="textarea"
                  rows={2}
                  value={motivoDictamen}
                  onChange={(e) => setMotivoDictamen(e.target.value)}
                  placeholder="Observación o motivo (obligatorio al marcar como Observada)..."
                  error={errorDetalle}
                />

                <div className="grid grid-cols-2 gap-2.5">
                  <Button
                    variant="primary"
                    size="sm"
                    icon={CheckCircle2}
                    disabled={guardandoDictamen}
                    onClick={() => manejarDictamen("VALIDA")}
                  >
                    Confirmar Válida
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    icon={XCircle}
                    disabled={guardandoDictamen}
                    onClick={() => manejarDictamen("OBSERVADA")}
                  >
                    Marcar Observada
                  </Button>
                </div>
              </div>

              {/* Historial de Auditoría */}
              {seleccionada.revisiones?.length > 0 && (
                <div className="space-y-2 border-t border-slate-100 pt-3">
                  <p className="text-xs font-bold text-slate-700">Historial de revisiones humanas</p>
                  {seleccionada.revisiones.map((rev) => (
                    <div key={rev.id} className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs">
                      <div className="flex items-center justify-between">
                        <BadgeDictamen estado={rev.dictamen} />
                        <span className="text-slate-400 nums">{fmt(rev.registrado_en)}</span>
                      </div>
                      <p className="mt-1 text-slate-600">
                        Por <span className="font-medium text-slate-800">{rev.admin_email}</span>
                        {rev.motivo ? ` — "${rev.motivo}"` : ""}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </Modal>
    </div>
  );
}
