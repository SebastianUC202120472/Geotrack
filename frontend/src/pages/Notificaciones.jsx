import { useEffect, useMemo, useState } from "react";
import {
  Bell,
  BellRing,
  Send,
  Wrench,
  Sliders,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  Plus,
  Trash2,
  KeyRound,
  ShieldCheck,
  AlertTriangle,
  Users,
  Copy,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import SectionCard from "../components/ui/SectionCard";
import EmptyState from "../components/ui/EmptyState";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import Modal from "../components/ui/Modal";
import Badge from "../components/ui/Badge";
import {
  obtenerNotificaciones,
  listarEnviosNotificaciones,
  reintentarEnvio,
  listarMecanicos,
  crearMecanico,
  eliminarMecanico,
  enviarCodigoMecanico,
  verificarCodigoMecanico,
  listarPlantillas,
  actualizarPlantilla,
  listarConductores,
  listarConductoresTelegram,
  obtenerEnlaceTelegramConductor,
} from "../services/api";
import { haciaPanel } from "../utils/rutasPanel";

const fmt = (f) => (f ? new Date(f).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" }) : "—");

function tiempoRelativo(fechaIso) {
  if (!fechaIso) return "—";
  const diff = Date.now() - new Date(fechaIso).getTime();
  const min = Math.floor(diff / 60000);
  if (min < 1) return "ahora mismo";
  if (min < 60) return `hace ${min} min`;
  const hrs = Math.floor(min / 60);
  if (hrs < 24) return `hace ${hrs} h`;
  const dias = Math.floor(hrs / 24);
  return `hace ${dias} día${dias > 1 ? "s" : ""}`;
}

export default function Notificaciones() {
  const navigate = useNavigate();
  const [tab, setTab] = useState("internas"); // internas | envios | mecanicos | plantillas

  // 1. Internas (Campana)
  const [internas, setInternas] = useState([]);
  const [noVistas, setNoVistas] = useState(0);
  const [filtroInterno, setFiltroInterno] = useState("todas");
  const [cargandoInternas, setCargandoInternas] = useState(true);

  // 2. Envíos (Bitácora Outbox)
  const [envios, setEnvios] = useState([]);
  const [totalEnvios, setTotalEnvios] = useState(0);
  const [cargandoEnvios, setCargandoEnvios] = useState(true);
  const [filtroEstado, setFiltroEstado] = useState("");
  const [filtroCanal, setFiltroCanal] = useState("");

  // 3. Mecánicos
  const [mecanicos, setMecanicos] = useState([]);
  const [cargandoMec, setCargandoMec] = useState(true);
  const [modalMec, setModalMec] = useState(false);
  const [modalOtp, setModalOtp] = useState(null);
  const [codigoOtp, setCodigoOtp] = useState("");
  const [nuevoMec, setNuevoMec] = useState({
    nombre: "",
    empresa_taller: "",
    tipo_servicio: "Mecánico",
    distritos: "Miraflores, Surquillo, San Isidro",
    direccion: "",
    telefono_whatsapp: "",
    telegram_chat_id: "",
    horario_inicio: "08:00",
    horario_fin: "20:00",
  });
  const [guardandoMec, setGuardandoMec] = useState(false);
  const [errorMec, setErrorMec] = useState("");

  // 4. Plantillas y Configuración
  const [plantillas, setPlantillas] = useState([]);
  const [cargandoPlan, setCargandoPlan] = useState(true);
  const [modalEditPlan, setModalEditPlan] = useState(null);
  const [planCuerpo, setPlanCuerpo] = useState("");
  const [planAsunto, setPlanAsunto] = useState("");
  const [planActivo, setPlanActivo] = useState(true);

  // 5. Conductores en Telegram
  const [conductores, setConductores] = useState([]);
  const [vinculados, setVinculados] = useState([]);
  const [cargandoCond, setCargandoCond] = useState(true);
  const [avisoCond, setAvisoCond] = useState("");

  // Carga la campana al abrir la pantalla.
  useEffect(() => {
    let activo = true;
    obtenerNotificaciones(200)
      .then((d) => {
        if (!activo) return;
        setInternas(Array.isArray(d?.items) ? d.items : []);
        setNoVistas(d?.no_vistas ?? 0);
      })
      .catch(() => {})
      .finally(() => activo && setCargandoInternas(false));
    return () => { activo = false; };
  }, []);

  // Carga los datos de la pestaña abierta (y vuelve a pedir la bitácora si cambian sus filtros).
  useEffect(() => {
    let activo = true;
    if (tab === "envios") {
      listarEnviosNotificaciones({ estado: filtroEstado, canal: filtroCanal, limite: 50 })
        .then((d) => {
          if (!activo) return;
          setEnvios(Array.isArray(d?.items) ? d.items : []);
          setTotalEnvios(d?.total ?? 0);
        })
        .catch(() => {})
        .finally(() => activo && setCargandoEnvios(false));
    } else if (tab === "mecanicos") {
      listarMecanicos()
        .then((d) => activo && setMecanicos(Array.isArray(d) ? d : []))
        .catch(() => {})
        .finally(() => activo && setCargandoMec(false));
    } else if (tab === "plantillas") {
      listarPlantillas()
        .then((d) => activo && setPlantillas(Array.isArray(d) ? d : []))
        .catch(() => {})
        .finally(() => activo && setCargandoPlan(false));
    } else if (tab === "conductores") {
      Promise.all([listarConductores(), listarConductoresTelegram()])
        .then(([lista, vinc]) => {
          if (!activo) return;
          setConductores(Array.isArray(lista) ? lista.filter((c) => c.estado !== false) : []);
          setVinculados(Array.isArray(vinc?.conductores) ? vinc.conductores : []);
        })
        .catch(() => {})
        .finally(() => activo && setCargandoCond(false));
    }
    return () => { activo = false; };
  }, [tab, filtroEstado, filtroCanal]);

  // Copia el enlace firmado de Telegram de un conductor para enviárselo. Recibe el conductor.
  const copiarEnlaceConductor = (c) => {
    setAvisoCond("");
    obtenerEnlaceTelegramConductor(c.usuario_id)
      .then((d) => navigator.clipboard.writeText(d.url).then(() => d.url))
      .then(() => setAvisoCond(`Enlace de ${c.nombre} copiado: envíaselo para que pulse "Iniciar" en Telegram (vence en 24 h).`))
      .catch((err) => setAvisoCond(err.message));
  };

  // Vuelve a pedir la bitácora de envíos (tras un reintento o con el botón Actualizar). Sin parámetros.
  const cargarEnvios = () => {
    setCargandoEnvios(true);
    listarEnviosNotificaciones({ estado: filtroEstado, canal: filtroCanal, limite: 50 })
      .then((d) => {
        setEnvios(Array.isArray(d?.items) ? d.items : []);
        setTotalEnvios(d?.total ?? 0);
      })
      .finally(() => setCargandoEnvios(false));
  };

  // Vuelve a pedir el directorio de mecánicos (tras crear, verificar o eliminar). Sin parámetros.
  const cargarMecanicos = () => {
    setCargandoMec(true);
    listarMecanicos()
      .then((d) => setMecanicos(Array.isArray(d) ? d : []))
      .finally(() => setCargandoMec(false));
  };

  // Vuelve a pedir las plantillas (tras editar o encender/apagar una). Sin parámetros.
  const cargarPlantillas = () => {
    setCargandoPlan(true);
    listarPlantillas()
      .then((d) => setPlantillas(Array.isArray(d) ? d : []))
      .finally(() => setCargandoPlan(false));
  };

  // Da de alta un mecánico desde el formulario. Recibe el evento del formulario.
  const handleCrearMecanico = (e) => {
    e.preventDefault();
    if (!nuevoMec.nombre || !nuevoMec.telefono_whatsapp) {
      setErrorMec("Nombre y teléfono de WhatsApp son requeridos.");
      return;
    }
    setGuardandoMec(true);
    setErrorMec("");
    crearMecanico(nuevoMec)
      .then(() => {
        setModalMec(false);
        setNuevoMec({
          nombre: "",
          empresa_taller: "",
          tipo_servicio: "Mecánico",
          distritos: "Miraflores, Surquillo, San Isidro",
          direccion: "",
          telefono_whatsapp: "",
          telegram_chat_id: "",
          horario_inicio: "08:00",
          horario_fin: "20:00",
        });
        cargarMecanicos();
      })
      .catch((err) => setErrorMec(err.message))
      .finally(() => setGuardandoMec(false));
  };

  // Envía el código de verificación y abre el modal para ingresarlo. Recibe el mecánico.
  const handleEnviarOtp = (mec) => {
    enviarCodigoMecanico(mec.id)
      .then(() => {
        setModalOtp(mec);
        setCodigoOtp("");
      })
      .catch((err) => alert(err.message));
  };

  // Verifica el código ingresado del mecánico. Sin parámetros.
  const handleVerificarOtp = () => {
    if (!codigoOtp.trim()) return;
    verificarCodigoMecanico(modalOtp.id, codigoOtp.trim())
      .then(() => {
        setModalOtp(null);
        cargarMecanicos();
      })
      .catch((err) => alert(err.message));
  };

  // Vuelve a poner en cola un envío fallido. Recibe el id.
  const handleReintentar = (id) => {
    reintentarEnvio(id)
      .then(() => cargarEnvios())
      .catch((err) => alert(err.message));
  };

  // Enciende o apaga el aviso de una plantilla. Recibe la plantilla.
  const handleTogglePlantilla = (p) => {
    actualizarPlantilla(p.id, { cuerpo: p.cuerpo, asunto: p.asunto, activo: !p.activo })
      .then(() => cargarPlantillas())
      .catch((err) => alert(err.message));
  };

  // Guarda el texto editado de la plantilla. Recibe el evento del formulario.
  const handleGuardarPlantilla = (e) => {
    e.preventDefault();
    if (!modalEditPlan) return;
    actualizarPlantilla(modalEditPlan.id, { cuerpo: planCuerpo, asunto: planAsunto, activo: planActivo })
      .then(() => {
        setModalEditPlan(null);
        cargarPlantillas();
      })
      .catch((err) => alert(err.message));
  };

  const filtradosInternos = useMemo(
    () => (filtroInterno === "no_vistas" ? internas.filter((i) => i.visto_en === null) : internas),
    [internas, filtroInterno],
  );

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader
        titulo="Centro de Notificaciones"
        subtitulo="Gestión de avisos automáticos multicanal (WhatsApp, Telegram y Correo), bitácora y proveedores de auxilio."
      />

      {/* Navegación por Pestañas */}
      <div className="flex border-b border-slate-200 gap-6 overflow-x-auto whitespace-nowrap">
        <button
          onClick={() => setTab("internas")}
          className={`flex items-center gap-2 pb-3 font-semibold text-sm transition-colors border-b-2 -mb-px ${
            tab === "internas" ? "border-brand-600 text-brand-600" : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <Bell size={18} />
          Alertas del Panel ({noVistas > 0 ? `${noVistas} nuevas` : internas.length})
        </button>

        <button
          onClick={() => setTab("envios")}
          className={`flex items-center gap-2 pb-3 font-semibold text-sm transition-colors border-b-2 -mb-px ${
            tab === "envios" ? "border-brand-600 text-brand-600" : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <Send size={18} />
          Bitácora de Envíos Externos
        </button>

        <button
          onClick={() => setTab("mecanicos")}
          className={`flex items-center gap-2 pb-3 font-semibold text-sm transition-colors border-b-2 -mb-px ${
            tab === "mecanicos" ? "border-brand-600 text-brand-600" : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <Wrench size={18} />
          Directorio de Mecánicos
        </button>

        <button
          onClick={() => setTab("plantillas")}
          className={`flex items-center gap-2 pb-3 font-semibold text-sm transition-colors border-b-2 -mb-px ${
            tab === "plantillas" ? "border-brand-600 text-brand-600" : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <Sliders size={18} />
          Plantillas y Canales
        </button>

        <button
          onClick={() => setTab("conductores")}
          className={`flex items-center gap-2 pb-3 font-semibold text-sm transition-colors border-b-2 -mb-px ${
            tab === "conductores" ? "border-brand-600 text-brand-600" : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <Users size={18} />
          Conductores en Telegram
        </button>
      </div>

      {/* 1. Alertas internas */}
      {tab === "internas" && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 sm:max-w-md">
            <KpiCard label="Total" value={internas.length} icon={Bell} tone="brand" />
            <KpiCard label="No vistas" value={noVistas} icon={BellRing} tone={noVistas > 0 ? "warning" : "info"} />
          </div>

          <SectionCard
            title="Avisos para Administración"
            action={
              <div className="flex gap-2">
                <button
                  onClick={() => setFiltroInterno("todas")}
                  className={`px-3 py-1 text-xs font-semibold rounded-lg ${
                    filtroInterno === "todas" ? "bg-brand-600 text-white" : "border text-slate-600"
                  }`}
                >
                  Todas
                </button>
                <button
                  onClick={() => setFiltroInterno("no_vistas")}
                  className={`px-3 py-1 text-xs font-semibold rounded-lg ${
                    filtroInterno === "no_vistas" ? "bg-brand-600 text-white" : "border text-slate-600"
                  }`}
                >
                  No vistas
                </button>
              </div>
            }
          >
            {cargandoInternas ? (
              <p className="py-8 text-center text-sm text-slate-500">Cargando...</p>
            ) : filtradosInternos.length === 0 ? (
              <EmptyState icon={Bell} title="Sin notificaciones" description="No hay alertas administrativas." />
            ) : (
              <ul className="-mx-5 divide-y divide-slate-100">
                {filtradosInternos.map((item) => (
                  <li key={item.id} className={item.visto_en === null ? "bg-brand-50/40" : ""}>
                    <button
                      onClick={() => item.ruta && navigate(haciaPanel(item.ruta))}
                      className="flex w-full items-start gap-3 px-5 py-3.5 text-left hover:bg-slate-50 cursor-pointer"
                    >
                      <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${item.visto_en === null ? "bg-brand-600" : "bg-slate-300"}`} />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-semibold text-slate-900">{item.titulo}</p>
                        <p className="text-sm text-slate-600">{item.mensaje}</p>
                        <p className="mt-0.5 text-xs text-slate-400">{tiempoRelativo(item.creado_en)} · {fmt(item.creado_en)}</p>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>
        </div>
      )}

      {/* 2. Bitácora de Envíos */}
      {tab === "envios" && (
        <div className="space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <select
                value={filtroEstado}
                onChange={(e) => setFiltroEstado(e.target.value)}
                className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700"
              >
                <option value="">Todos los estados</option>
                <option value="PENDIENTE">Pendientes</option>
                <option value="ENVIADO">Enviados</option>
                <option value="FALLIDO">Fallidos</option>
              </select>

              <select
                value={filtroCanal}
                onChange={(e) => setFiltroCanal(e.target.value)}
                className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700"
              >
                <option value="">Todos los canales</option>
                <option value="whatsapp">WhatsApp</option>
                <option value="telegram">Telegram</option>
                <option value="correo">Correo</option>
              </select>
            </div>

            <Button variant="secondary" onClick={cargarEnvios} disabled={cargandoEnvios}>
              <RefreshCw size={16} /> Actualizar
            </Button>
          </div>

          <SectionCard title={`Cola de Envíos (${totalEnvios})`}>
            {cargandoEnvios ? (
              <p className="py-8 text-center text-sm text-slate-500">Cargando bitácora...</p>
            ) : envios.length === 0 ? (
              <EmptyState icon={Send} title="Sin mensajes registrados" description="No hay mensajes en la bitácora con los filtros aplicados." />
            ) : (
              <div className="overflow-x-auto -mx-5">
                <table className="w-full text-left text-sm text-slate-600">
                  <thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-500">
                    <tr>
                      <th className="px-5 py-3">Evento</th>
                      <th className="px-5 py-3">Canal</th>
                      <th className="px-5 py-3">Destinatario</th>
                      <th className="px-5 py-3">Mensaje</th>
                      <th className="px-5 py-3">Estado</th>
                      <th className="px-5 py-3">Fecha</th>
                      <th className="px-5 py-3 text-right">Acción</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {envios.map((env) => (
                      <tr key={env.id} className="hover:bg-slate-50/60">
                        <td className="px-5 py-3 font-semibold text-slate-900">
                          {env.evento}
                          {env.prioridad === "urgente" && (
                            <span className="ml-2 inline-flex items-center text-[10px] bg-red-100 text-red-700 px-1.5 py-0.5 rounded font-bold">
                              URGENTE
                            </span>
                          )}
                        </td>
                        <td className="px-5 py-3">
                          <span className="capitalize font-medium">{env.canal}</span>
                        </td>
                        <td className="px-5 py-3 font-mono text-xs">
                          {env.destinatario_valor}
                          {env.destinatario_nombre && <div className="text-slate-400 font-sans">{env.destinatario_nombre}</div>}
                        </td>
                        <td className="px-5 py-3 max-w-xs truncate text-xs" title={env.cuerpo}>
                          {env.asunto && <span className="font-semibold">{env.asunto} - </span>}
                          {env.cuerpo}
                        </td>
                        <td className="px-5 py-3">
                          {env.estado === "ENVIADO" && <Badge tono="success"><CheckCircle2 size={12} className="mr-1 inline" /> Enviado</Badge>}
                          {env.estado === "PENDIENTE" && <Badge tono="warning"><Clock size={12} className="mr-1 inline" /> Pendiente ({env.intentos})</Badge>}
                          {env.estado === "FALLIDO" && <Badge tono="danger"><XCircle size={12} className="mr-1 inline" /> Fallido</Badge>}
                        </td>
                        <td className="px-5 py-3 text-xs text-slate-400 whitespace-nowrap">
                          {fmt(env.enviado_en || env.creado_en)}
                        </td>
                        <td className="px-5 py-3 text-right">
                          {env.estado === "FALLIDO" && (
                            <button
                              onClick={() => handleReintentar(env.id)}
                              className="text-brand-600 hover:text-brand-800 text-xs font-semibold flex items-center gap-1 ml-auto"
                            >
                              <RefreshCw size={12} /> Reintentar
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </SectionCard>
        </div>
      )}

      {/* 3. Directorio de Mecánicos */}
      {tab === "mecanicos" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-500">
              Proveedores de auxilio: en Auxilio mecánico se propone al más cercano y el administrador confirma el envío.
            </p>
            <Button onClick={() => setModalMec(true)}>
              <Plus size={16} /> Nuevo Proveedor
            </Button>
          </div>

          <SectionCard title={`Directorio Activo (${mecanicos.length})`}>
            {cargandoMec ? (
              <p className="py-8 text-center text-sm text-slate-500">Cargando mecánicos...</p>
            ) : mecanicos.length === 0 ? (
              <EmptyState icon={Wrench} title="Sin mecánicos" description="No hay proveedores de auxilio en el directorio." />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {mecanicos.map((m) => (
                  <div key={m.id} className="border border-slate-200 rounded-xl p-4 bg-white shadow-sm space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-bold text-slate-900">{m.nombre}</h4>
                        <p className="text-xs text-slate-500">{m.empresa_taller || "Independiente"}</p>
                      </div>
                      <Badge tono={m.telefono_verificado ? "success" : "warning"}>
                        {m.telefono_verificado ? "Verificado" : "No verificado"}
                      </Badge>
                    </div>

                    <div className="text-xs text-slate-600 space-y-1">
                      <p><span className="font-semibold">Servicio:</span> {m.tipo_servicio}</p>
                      <p><span className="font-semibold">Teléfono:</span> {m.telefono_whatsapp}</p>
                      {m.telegram_chat_id && <p><span className="font-semibold">Telegram:</span> {m.telegram_chat_id}</p>}
                      <p><span className="font-semibold">Distritos:</span> {m.distritos}</p>
                      <p><span className="font-semibold">Horario:</span> {m.horario_inicio} - {m.horario_fin}</p>
                    </div>

                    <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
                      {!m.telefono_verificado ? (
                        <Button variant="secondary" size="sm" onClick={() => handleEnviarOtp(m)}>
                          <KeyRound size={14} className="mr-1" /> Verificar número
                        </Button>
                      ) : (
                        <span className="text-xs font-semibold text-emerald-600 flex items-center gap-1">
                          <ShieldCheck size={14} /> Listo para auxilio
                        </span>
                      )}

                      <button
                        onClick={() => eliminarMecanico(m.id).then(() => cargarMecanicos())}
                        className="text-slate-400 hover:text-danger p-1 rounded"
                        title="Eliminar mecánico"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>
        </div>
      )}

      {/* 5. Conductores en Telegram */}
      {tab === "conductores" && (
        <div className="space-y-6">
          <p className="text-sm text-slate-500">
            El conductor recibe por Telegram el aviso de que su auxilio va en camino. Copia su enlace y envíaselo:
            al pulsar «Iniciar» en el bot su chat queda vinculado. El enlace es personal y vence en 24 horas.
          </p>
          {avisoCond && (
            <p className="rounded-xl border border-brand-200 bg-brand-50/60 px-4 py-3 text-sm text-brand-800" role="status">{avisoCond}</p>
          )}
          <SectionCard title={`Conductores (${conductores.length})`}>
            {cargandoCond ? (
              <p className="py-8 text-center text-sm text-slate-500">Cargando conductores...</p>
            ) : conductores.length === 0 ? (
              <EmptyState icon={Users} title="Sin conductores" description="No hay conductores registrados." />
            ) : (
              <ul className="-mx-5 divide-y divide-slate-100">
                {conductores.map((c) => (
                  <li key={c.usuario_id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-slate-900">{c.nombre}</p>
                      <p className="text-xs text-slate-500">{c.correo}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge tono={vinculados.includes(c.usuario_id) ? "success" : "neutral"}>
                        {vinculados.includes(c.usuario_id) ? "Telegram vinculado" : "Sin vincular"}
                      </Badge>
                      <Button variant="secondary" size="sm" onClick={() => copiarEnlaceConductor(c)}>
                        <Copy size={14} className="mr-1" /> Copiar enlace
                      </Button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>
        </div>
      )}

      {/* 4. Plantillas y Canales */}
      {tab === "plantillas" && (
        <div className="space-y-6">
          <p className="text-sm text-slate-500">
            Activa o desactiva avisos sin programar y edita las plantillas de mensaje en cualquier momento.
          </p>

          <SectionCard title={`Plantillas del Módulo (${plantillas.length})`}>
            {cargandoPlan ? (
              <p className="py-8 text-center text-sm text-slate-500">Cargando plantillas...</p>
            ) : plantillas.length === 0 ? (
              <EmptyState icon={Sliders} title="Sin plantillas" description="No hay plantillas registradas." />
            ) : (
              <div className="overflow-x-auto -mx-5">
                <table className="w-full text-left text-sm text-slate-600">
                  <thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-500">
                    <tr>
                      <th className="px-5 py-3">Evento</th>
                      <th className="px-5 py-3">Canal</th>
                      <th className="px-5 py-3">Texto / Plantilla</th>
                      <th className="px-5 py-3 text-center">Estado</th>
                      <th className="px-5 py-3 text-right">Acción</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {plantillas.map((p) => (
                      <tr key={p.id} className="hover:bg-slate-50/60">
                        <td className="px-5 py-3 font-semibold text-slate-900">{p.evento}</td>
                        <td className="px-5 py-3 capitalize">{p.canal}</td>
                        <td className="px-5 py-3 max-w-md text-xs">
                          {p.asunto && <div className="font-semibold text-slate-800">Asunto: {p.asunto}</div>}
                          <div className="text-slate-500 truncate" title={p.cuerpo}>{p.cuerpo}</div>
                        </td>
                        <td className="px-5 py-3 text-center">
                          <button
                            onClick={() => handleTogglePlantilla(p)}
                            className={`px-2.5 py-1 text-xs font-semibold rounded-full transition-colors ${
                              p.activo ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-500"
                            }`}
                          >
                            {p.activo ? "Activo" : "Inactivo"}
                          </button>
                        </td>
                        <td className="px-5 py-3 text-right">
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => {
                              setModalEditPlan(p);
                              setPlanCuerpo(p.cuerpo);
                              setPlanAsunto(p.asunto || "");
                              setPlanActivo(p.activo);
                            }}
                          >
                            Editar
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </SectionCard>
        </div>
      )}

      {/* Modal Nuevo Mecánico */}
      <Modal open={modalMec} onClose={() => setModalMec(false)} className="max-h-[90vh] overflow-y-auto">
        <h3 className="mb-4 text-lg font-semibold text-slate-900">Registrar Proveedor de Auxilio</h3>
        <form onSubmit={handleCrearMecanico} className="space-y-4">
          {errorMec && (
            <div className="p-3 bg-red-50 text-red-700 text-xs rounded-lg flex items-center gap-2">
              <AlertTriangle size={16} /> {errorMec}
            </div>
          )}

          <Input
            label="Nombre completo *"
            value={nuevoMec.nombre}
            onChange={(e) => setNuevoMec({ ...nuevoMec, nombre: e.target.value })}
            placeholder="Ej. Carlos Mendoza"
            required
          />

          <Input
            label="Empresa o Taller"
            value={nuevoMec.empresa_taller}
            onChange={(e) => setNuevoMec({ ...nuevoMec, empresa_taller: e.target.value })}
            placeholder="Ej. Taller Mecánico San Isidro"
          />

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Tipo de Servicio *</label>
            <select
              value={nuevoMec.tipo_servicio}
              onChange={(e) => setNuevoMec({ ...nuevoMec, tipo_servicio: e.target.value })}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800"
            >
              <option value="Mecánico">Mecánico</option>
              <option value="Grúa">Grúa</option>
              <option value="Combustible">Combustible</option>
              <option value="Vehículo de reemplazo">Vehículo de reemplazo</option>
              <option value="Otro">Otro</option>
            </select>
          </div>

          <Input
            label="Teléfono WhatsApp (E.164) *"
            value={nuevoMec.telefono_whatsapp}
            onChange={(e) => setNuevoMec({ ...nuevoMec, telefono_whatsapp: e.target.value })}
            placeholder="+51999888777"
            required
          />

          <Input
            label="Chat ID de Telegram (Opcional demo)"
            value={nuevoMec.telegram_chat_id}
            onChange={(e) => setNuevoMec({ ...nuevoMec, telegram_chat_id: e.target.value })}
            placeholder="Ej. 123456789"
          />

          <Input
            label="Dirección del Taller (para cálculo de cercanía)"
            value={nuevoMec.direccion}
            onChange={(e) => setNuevoMec({ ...nuevoMec, direccion: e.target.value })}
            placeholder="Ej. Av. República de Panamá 3500, San Isidro"
          />

          <Input
            label="Distritos de Cobertura (separados por coma)"
            value={nuevoMec.distritos}
            onChange={(e) => setNuevoMec({ ...nuevoMec, distritos: e.target.value })}
          />

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="secondary" onClick={() => setModalMec(false)}>Cancelar</Button>
            <Button type="submit" disabled={guardandoMec}>Registrar Mecánico</Button>
          </div>
        </form>
      </Modal>

      {/* Modal Verificación OTP */}
      <Modal open={!!modalOtp} onClose={() => setModalOtp(null)}>
        <h3 className="mb-4 text-lg font-semibold text-slate-900">Verificar Número de Teléfono</h3>
        <div className="space-y-4">
          <p className="text-sm text-slate-600">
            Se envió un código de 6 dígitos{" "}
            {modalOtp?.telegram_chat_id ? (
              <>por Telegram al chat <span className="font-semibold">{modalOtp.telegram_chat_id}</span></>
            ) : (
              <>por WhatsApp a <span className="font-semibold">{modalOtp?.telefono_whatsapp}</span></>
            )}
            . Ingrésalo para que el mecánico pueda recibir pedidos de auxilio.
          </p>

          <Input
            label="Código de 6 dígitos"
            value={codigoOtp}
            onChange={(e) => setCodigoOtp(e.target.value)}
            placeholder="123456"
            autoFocus
          />

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setModalOtp(null)}>Cancelar</Button>
            <Button onClick={handleVerificarOtp}>Confirmar Verificación</Button>
          </div>
        </div>
      </Modal>

      {/* Modal Editar Plantilla */}
      <Modal open={!!modalEditPlan} onClose={() => setModalEditPlan(null)}>
        <h3 className="mb-4 text-lg font-semibold text-slate-900">Editar plantilla: {modalEditPlan?.evento}</h3>
        <form onSubmit={handleGuardarPlantilla} className="space-y-4">
          {modalEditPlan?.canal === "correo" && (
            <Input
              label="Asunto del Correo"
              value={planAsunto}
              onChange={(e) => setPlanAsunto(e.target.value)}
              placeholder="Asunto..."
            />
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Cuerpo del mensaje *</label>
            <textarea
              rows={4}
              value={planCuerpo}
              onChange={(e) => setPlanCuerpo(e.target.value)}
              className="w-full rounded-xl border border-slate-200 p-3 text-sm text-slate-800 outline-none focus:border-brand-500"
              required
            />
            <p className="mt-1 text-xs text-slate-400">
              Usa las mismas variables entre llaves que trae el texto original (por ejemplo, &#123;codigo&#125;).
            </p>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="planActivo"
              checked={planActivo}
              onChange={(e) => setPlanActivo(e.target.checked)}
              className="rounded text-brand-600 focus:ring-brand-500"
            />
            <label htmlFor="planActivo" className="text-sm font-medium text-slate-700">Aviso activo</label>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={() => setModalEditPlan(null)}>Cancelar</Button>
            <Button type="submit">Guardar Cambios</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
