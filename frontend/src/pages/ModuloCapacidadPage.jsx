import { Suspense, lazy, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  BarChart3,
  BookOpen,
  Boxes,
  CalendarRange,
  Calculator,
  CheckCircle2,
  ClipboardList,
  FileText,
  Gauge,
  Link2,
  Pencil,
  Plus,
  Search,
  Settings,
  Trash2,
  Truck,
  Unlink,
  X,
} from "lucide-react";

import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import DataTable from "../components/ui/DataTable";
import SectionCard from "../components/ui/SectionCard";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import Modal from "../components/ui/Modal";
import ConfirmDialog from "../components/ui/ConfirmDialog";
import Badge, { EstadoBadge } from "../components/ui/Badge";
import Skeleton from "../components/ui/Skeleton";
import FormularioModelo from "../components/capacidad/FormularioModelo";
import {
  ESTADOS_PLANIFICABLES,
  ETIQUETA_TIPO,
  TIPOS_VEHICULO,
} from "../components/capacidad/constantes";
import { useAuth } from "../context/AuthContext";
import {
  actualizarConfiguracionCapacidad,
  actualizarModeloCapacidad,
  calcularCapacidad,
  crearModeloCapacidad,
  desvincularPlacaCapacidad,
  eliminarModeloCapacidad,
  listarAuditoriaCapacidad,
  listarCatalogoCapacidad,
  listarFlotaCapacidad,
  listarVinculacionesCapacidad,
  obtenerConfiguracionCapacidad,
  obtenerPlanificacionCapacidad,
  vincularPlacaCapacidad,
} from "../services/api";

// El visor 3D se carga bajo demanda: Three.js queda en un chunk aparte.
const VisorCarga3D = lazy(() => import("../components/capacidad/VisorCarga3D"));

const TABS = [
  { id: "catalogo", etiqueta: "Catalogo", icono: BookOpen },
  { id: "flota", etiqueta: "Flota y vinculaciones", icono: Link2 },
  { id: "calculadora", etiqueta: "Calculadora", icono: Calculator },
  { id: "planificacion", etiqueta: "Planificacion", icono: CalendarRange },
  { id: "configuracion", etiqueta: "Configuracion", icono: Settings },
];

const ETIQUETA_MODO = {
  cajas: "Cajas S/M/L",
  pedidos: "Pedidos reales",
  demo: "Demostracion",
};

// Convierte un valor de input en numero o undefined (para no enviar campos vacios).
const aNumero = (valor) => (valor === "" || valor === null ? undefined : Number(valor));

// Mensaje de exito o error con boton para cerrarlo.
function Aviso({ aviso, onCerrar }) {
  if (!aviso) return null;
  const ok = aviso.ok;
  return (
    <div
      className={`flex items-start gap-3 rounded-xl border px-4 py-3 text-sm ${
        ok
          ? "border-success/30 bg-success-soft text-success-strong"
          : "border-danger/30 bg-danger-soft text-danger-strong"
      }`}
    >
      {ok ? (
        <CheckCircle2 size={18} className="mt-0.5 shrink-0" />
      ) : (
        <AlertCircle size={18} className="mt-0.5 shrink-0" />
      )}
      <p className="flex-1 font-medium">{aviso.texto}</p>
      <button type="button" onClick={onCerrar} aria-label="Cerrar aviso" className="rounded p-0.5 hover:bg-black/5">
        <X size={16} />
      </button>
    </div>
  );
}

// Barra compacta de utilizacion (volumen usado / capacidad).
function BarraUso({ valor }) {
  const pct = Math.max(0, Math.min(100, Number(valor) || 0));
  const color = pct >= 90 ? "bg-success" : pct >= 60 ? "bg-brand-600" : "bg-warning";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="nums text-xs font-semibold text-slate-600">{pct.toFixed(0)}%</span>
    </div>
  );
}

// Lista de alertas del plan con color segun el nivel.
function ListaAlertas({ alertas }) {
  if (!alertas?.length) return null;
  return (
    <div className="space-y-2">
      {alertas.map((alerta, indice) => {
        const peligro = alerta.nivel === "danger";
        const advertencia = alerta.nivel === "warning";
        const Icono = peligro ? AlertCircle : advertencia ? AlertTriangle : CheckCircle2;
        const clases = peligro
          ? "border-danger/30 bg-danger-soft text-danger-strong"
          : advertencia
            ? "border-warning/30 bg-warning-soft text-warning-strong"
            : "border-info/30 bg-info-soft text-info-strong";
        return (
          <div
            key={`${alerta.codigo}-${indice}`}
            className={`flex items-start gap-3 rounded-xl border px-4 py-3 text-sm ${clases}`}
          >
            <Icono size={18} className="mt-0.5 shrink-0" />
            <div>
              <p className="font-semibold capitalize">{alerta.codigo.replaceAll("_", " ")}</p>
              <p className="text-xs opacity-90">{alerta.mensaje}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// Tabla de viajes reutilizada por la calculadora y la planificacion.
function TablaViajes({ viajes, maxParadas, seleccionado, onSeleccionar }) {
  const columnas = [
    {
      key: "numero",
      header: "Viaje",
      render: (v) => <span className="nums font-semibold text-slate-800">#{v.numero}</span>,
    },
    {
      key: "vehiculo_placa",
      header: "Vehiculo",
      render: (v) => (
        <div>
          <p className="font-semibold text-slate-800">
            {v.vehiculo_placa === "CATALOGO" ? "Modelo del catalogo" : v.vehiculo_placa}
          </p>
          <p className="text-xs text-slate-400">
            {v.marca} {v.modelo}
          </p>
        </div>
      ),
    },
    {
      key: "paradas",
      header: "Paradas",
      render: (v) => (
        <span className={v.paradas > maxParadas ? "font-semibold text-warning-strong" : "text-slate-700"}>
          {v.paradas}
          {v.paradas > maxParadas && " ⚠"}
        </span>
      ),
    },
    {
      key: "peso_kg",
      header: "Peso",
      render: (v) => <span className="nums text-slate-600">{v.peso_kg.toLocaleString("es-PE")} kg</span>,
    },
    {
      key: "volumen_m3",
      header: "Volumen",
      render: (v) => <span className="nums text-slate-600">{v.volumen_m3} m3</span>,
    },
    {
      key: "utilizacion_pct",
      header: "Uso",
      render: (v) => <BarraUso valor={v.utilizacion_pct} />,
    },
    {
      key: "acciones",
      header: "",
      render: (v) => (
        <Button
          size="sm"
          variant={seleccionado === viajes.indexOf(v) ? "primary" : "secondary"}
          onClick={() => onSeleccionar(viajes.indexOf(v))}
        >
          Ver 3D
        </Button>
      ),
    },
  ];

  return (
    <DataTable
      columns={columnas}
      rows={viajes}
      rowKey={(v) => `${v.numero}-${v.vehiculo_placa}`}
      empty={{
        icon: ClipboardList,
        title: "Sin viajes calculados",
        description: "Ajusta la carga, el vehiculo o los topes para volver a calcular.",
      }}
    />
  );
}

// Pagina del modulo de catalogo y capacidad (Idea 3, semanas 9 a 11).
export function ModuloCapacidadPage() {
  const { rol } = useAuth();
  const esAdmin = rol === "admin";

  const [tab, setTab] = useState("catalogo");
  const [cargando, setCargando] = useState(true);
  const [moduloActivo, setModuloActivo] = useState(true);
  const [aviso, setAviso] = useState(null);

  const [modelos, setModelos] = useState([]);
  const [flota, setFlota] = useState([]);
  const [vinculaciones, setVinculaciones] = useState([]);
  const [config, setConfig] = useState(null);

  // --- Catalogo ---
  const [busqueda, setBusqueda] = useState("");
  const [filtroTipo, setFiltroTipo] = useState("");
  const [filtroMarca, setFiltroMarca] = useState("");
  const [soloVerificados, setSoloVerificados] = useState(false);
  const [modalModelo, setModalModelo] = useState(null);
  const [guardandoModelo, setGuardandoModelo] = useState(false);
  const [modeloAEliminar, setModeloAEliminar] = useState(null);
  const [eliminandoModelo, setEliminandoModelo] = useState(false);

  // --- Flota y vinculaciones ---
  const [placaNueva, setPlacaNueva] = useState("");
  const [modeloNuevo, setModeloNuevo] = useState("");
  const [guardandoVinculo, setGuardandoVinculo] = useState(false);
  const [vinculacionAEliminar, setVinculacionAEliminar] = useState(null);
  const [eliminandoVinculo, setEliminandoVinculo] = useState(false);

  // --- Calculadora ---
  const [calcFuente, setCalcFuente] = useState("modelo");
  const [calcModelo, setCalcModelo] = useState("");
  const [calcPlaca, setCalcPlaca] = useState("");
  const [calcCarga, setCalcCarga] = useState("cajas");
  const [cajas, setCajas] = useState({ S: 20, M: 10, L: 4 });
  const [calcFiltros, setCalcFiltros] = useState({ estado: "", distrito: "", limite: 200 });
  const [calcDemo, setCalcDemo] = useState(100);
  const [calcFactor, setCalcFactor] = useState("");
  const [calcParadas, setCalcParadas] = useState("");
  const [calcViajes, setCalcViajes] = useState("");
  const [calculando, setCalculando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [viajeSeleccionado, setViajeSeleccionado] = useState(0);

  // --- Planificacion ---
  const [planFiltros, setPlanFiltros] = useState({ estado: "", distrito: "", fecha: "", limite: 500 });
  const [planDemoPedidos, setPlanDemoPedidos] = useState(700);
  const [planDemoVehiculos, setPlanDemoVehiculos] = useState(6);
  const [planFactor, setPlanFactor] = useState("");
  const [planificando, setPlanificando] = useState(false);
  const [planResultado, setPlanResultado] = useState(null);

  // --- Configuracion y auditoria ---
  const [formConfig, setFormConfig] = useState(null);
  const [guardandoConfig, setGuardandoConfig] = useState(false);
  const [auditoria, setAuditoria] = useState([]);

  useEffect(() => {
    let activo = true;

    Promise.all([
      listarCatalogoCapacidad(),
      listarFlotaCapacidad(),
      listarVinculacionesCapacidad(),
      obtenerConfiguracionCapacidad(),
    ])
      .then(([catalogo, flotaApi, vinculos, configApi]) => {
        if (!activo) return;
        setModelos(catalogo);
        setFlota(flotaApi);
        setVinculaciones(vinculos);
        setConfig(configApi);
        setFormConfig({
          factor_aprovechamiento: String(configApi.factor_aprovechamiento),
          max_paradas_por_viaje: String(configApi.max_paradas_por_viaje),
          max_paradas_por_jornada: String(configApi.max_paradas_por_jornada),
          max_viajes_por_dia: String(configApi.max_viajes_por_dia),
        });
      })
      .catch((error) => {
        if (!activo) return;
        if (error.status === 404) {
          setModuloActivo(false);
          setAviso({
            ok: false,
            texto:
              "El modulo de capacidad esta desactivado en este servidor (MODULO_CAPACIDAD_ENABLED=false).",
          });
        } else {
          setAviso({ ok: false, texto: error.message || "No se pudo cargar el modulo." });
        }
      })
      .finally(() => {
        if (activo) setCargando(false);
      });

    return () => {
      activo = false;
    };
  }, []);

  // La auditoria solo se pide cuando un administrador abre la pestana de configuracion.
  useEffect(() => {
    if (!esAdmin || tab !== "configuracion") return undefined;
    let activo = true;

    listarAuditoriaCapacidad(50)
      .then((datos) => {
        if (activo) setAuditoria(datos);
      })
      .catch(() => {
        if (activo) setAuditoria([]);
      });

    return () => {
      activo = false;
    };
  }, [tab, esAdmin]);

  const marcas = useMemo(
    () => [...new Set(modelos.map((m) => m.marca))].sort((a, b) => a.localeCompare(b, "es")),
    [modelos],
  );

  const modelosFiltrados = useMemo(() => {
    const texto = busqueda.trim().toLowerCase();
    return modelos.filter((modelo) => {
      const coincideTexto =
        !texto ||
        `${modelo.marca} ${modelo.modelo} ${modelo.id}`.toLowerCase().includes(texto);
      const coincideTipo = !filtroTipo || modelo.tipo === filtroTipo;
      const coincideMarca = !filtroMarca || modelo.marca === filtroMarca;
      const coincideVerificado = !soloVerificados || modelo.verificado;
      return coincideTexto && coincideTipo && coincideMarca && coincideVerificado;
    });
  }, [modelos, busqueda, filtroTipo, filtroMarca, soloVerificados]);

  const modelosPorId = useMemo(
    () => Object.fromEntries(modelos.map((m) => [m.id, m])),
    [modelos],
  );

  const vinculacionPorPlaca = useMemo(
    () => Object.fromEntries(vinculaciones.map((v) => [v.placa, v])),
    [vinculaciones],
  );

  const placasDisponibles = useMemo(
    () => flota.filter((vehiculo) => !vinculacionPorPlaca[vehiculo.placa]),
    [flota, vinculacionPorPlaca],
  );

  const modelosVerificados = useMemo(
    () => modelos.filter((m) => m.verificado).length,
    [modelos],
  );

  const tiposDistintos = useMemo(() => new Set(modelos.map((m) => m.tipo)).size, [modelos]);

  const flotaConModelo = useMemo(
    () => flota.filter((vehiculo) => vehiculo.vinculacion).length,
    [flota],
  );

  const modeloCalculado = calcModelo ? modelosPorId[calcModelo] : null;
  const viajeActual = resultado?.viajes?.[viajeSeleccionado] || null;
  const modeloViaje = viajeActual ? modelosPorId[viajeActual.modelo_id] : null;

  const mostrarAviso = (ok, texto) => setAviso({ ok, texto });

  // Traduce un error de la API a un mensaje entendible (y detecta el modulo apagado).
  const manejarError = (error) => {
    if (error.status === 404) {
      setModuloActivo(false);
      mostrarAviso(false, "El modulo de capacidad esta desactivado en este servidor.");
      return;
    }
    mostrarAviso(false, error.message || "Ocurrio un error inesperado.");
  };

  const recargarCatalogo = async () => {
    const catalogo = await listarCatalogoCapacidad();
    setModelos(catalogo);
  };

  const recargarFlota = async () => {
    const [flotaApi, vinculos] = await Promise.all([
      listarFlotaCapacidad(),
      listarVinculacionesCapacidad(),
    ]);
    setFlota(flotaApi);
    setVinculaciones(vinculos);
  };

  // --------------------------- Acciones del catalogo ---------------------------

  const guardarModelo = async (datos) => {
    setGuardandoModelo(true);
    try {
      if (modalModelo?.modo === "editar") {
        await actualizarModeloCapacidad(modalModelo.modelo.id, datos);
        mostrarAviso(true, "Modelo actualizado en el catalogo.");
      } else {
        const creado = await crearModeloCapacidad(datos);
        mostrarAviso(true, `Modelo ${creado.marca} ${creado.modelo} agregado al catalogo.`);
      }
      await recargarCatalogo();
      setModalModelo(null);
    } catch (error) {
      manejarError(error);
    } finally {
      setGuardandoModelo(false);
    }
  };

  const confirmarEliminarModelo = async () => {
    if (!modeloAEliminar) return;
    setEliminandoModelo(true);
    try {
      await eliminarModeloCapacidad(modeloAEliminar.id);
      await recargarCatalogo();
      mostrarAviso(true, "Modelo eliminado del catalogo.");
      setModeloAEliminar(null);
    } catch (error) {
      manejarError(error);
    } finally {
      setEliminandoModelo(false);
    }
  };

  // --------------------------- Acciones de la flota ---------------------------

  const vincular = async (evento) => {
    evento.preventDefault();
    if (!placaNueva || !modeloNuevo) {
      mostrarAviso(false, "Selecciona la placa y el modelo del catalogo.");
      return;
    }

    setGuardandoVinculo(true);
    try {
      const datos = await vincularPlacaCapacidad({ placa: placaNueva, modelo_id: modeloNuevo });
      await recargarFlota();
      setPlacaNueva("");
      setModeloNuevo("");
      mostrarAviso(true, `Placa ${datos.placa} vinculada a ${datos.marca} ${datos.nombre_modelo}.`);
    } catch (error) {
      manejarError(error);
    } finally {
      setGuardandoVinculo(false);
    }
  };

  const confirmarDesvincular = async () => {
    if (!vinculacionAEliminar) return;
    setEliminandoVinculo(true);
    try {
      await desvincularPlacaCapacidad(vinculacionAEliminar.id);
      await recargarFlota();
      mostrarAviso(true, `Se quito el modelo de la placa ${vinculacionAEliminar.placa}.`);
      setVinculacionAEliminar(null);
    } catch (error) {
      manejarError(error);
    } finally {
      setEliminandoVinculo(false);
    }
  };

  // --------------------------- Calculadora ---------------------------

  const calcular = async () => {
    const datos = {};

    if (calcFuente === "placa") {
      if (!calcPlaca) {
        mostrarAviso(false, "Selecciona una placa vinculada.");
        return;
      }
      datos.placa = calcPlaca;
    } else {
      if (!calcModelo) {
        mostrarAviso(false, "Selecciona un modelo del catalogo.");
        return;
      }
      datos.modelo_id = calcModelo;
    }

    if (calcCarga === "cajas") {
      const cantidades = {
        S: Math.max(0, Math.trunc(Number(cajas.S) || 0)),
        M: Math.max(0, Math.trunc(Number(cajas.M) || 0)),
        L: Math.max(0, Math.trunc(Number(cajas.L) || 0)),
      };
      if (cantidades.S + cantidades.M + cantidades.L === 0) {
        mostrarAviso(false, "Indica al menos una caja S, M o L.");
        return;
      }
      datos.cantidades = cantidades;
    } else if (calcCarga === "demo") {
      datos.demo_pedidos = Math.max(1, Math.trunc(Number(calcDemo) || 1));
    } else {
      datos.filtros = {
        estado: calcFiltros.estado || null,
        distrito: calcFiltros.distrito || null,
        limite: Math.max(1, Math.trunc(Number(calcFiltros.limite) || 200)),
      };
    }

    if (calcFactor) datos.factor_aprovechamiento = Number(calcFactor);
    if (calcParadas) datos.max_paradas_por_viaje = Number(calcParadas);
    if (calcViajes) datos.max_viajes_por_dia = Number(calcViajes);

    setCalculando(true);
    try {
      const plan = await calcularCapacidad(datos);
      setResultado(plan);
      setViajeSeleccionado(0);
      mostrarAviso(true, `Calculo listo: ${plan.resumen.viajes_necesarios} viajes para ${plan.resumen.total_pedidos} pedidos.`);
    } catch (error) {
      manejarError(error);
    } finally {
      setCalculando(false);
    }
  };

  const limpiarCalculo = () => {
    setResultado(null);
    setViajeSeleccionado(0);
    setAviso(null);
  };

  // --------------------------- Planificacion ---------------------------

  const planificar = async (demo) => {
    const datos = demo
      ? {
          demo_pedidos: Math.max(1, Math.trunc(Number(planDemoPedidos) || 700)),
          demo_vehiculos: Math.max(1, Math.trunc(Number(planDemoVehiculos) || 6)),
        }
      : {
          estado: planFiltros.estado || undefined,
          distrito: planFiltros.distrito || undefined,
          fecha: planFiltros.fecha || undefined,
          limite: aNumero(planFiltros.limite),
        };

    if (planFactor) datos.factor_aprovechamiento = Number(planFactor);

    setPlanificando(true);
    try {
      const plan = await obtenerPlanificacionCapacidad(datos);
      setPlanResultado(plan);
      mostrarAviso(
        true,
        `${demo ? "Demo" : "Plan real"}: ${plan.resumen.total_pedidos} pedidos en ${plan.resumen.viajes_necesarios} viajes.`,
      );
    } catch (error) {
      manejarError(error);
    } finally {
      setPlanificando(false);
    }
  };

  // --------------------------- Configuracion ---------------------------

  const guardarConfiguracion = async (evento) => {
    evento.preventDefault();
    if (!formConfig) return;

    const datos = {
      factor_aprovechamiento: Number(formConfig.factor_aprovechamiento),
      max_paradas_por_viaje: Number(formConfig.max_paradas_por_viaje),
      max_paradas_por_jornada: Number(formConfig.max_paradas_por_jornada),
      max_viajes_por_dia: Number(formConfig.max_viajes_por_dia),
    };

    if (datos.factor_aprovechamiento < 0.5 || datos.factor_aprovechamiento > 1) {
      mostrarAviso(false, "El factor debe estar entre 0.50 y 1.00.");
      return;
    }

    setGuardandoConfig(true);
    try {
      const actualizada = await actualizarConfiguracionCapacidad(datos);
      setConfig(actualizada);
      setFormConfig({
        factor_aprovechamiento: String(actualizada.factor_aprovechamiento),
        max_paradas_por_viaje: String(actualizada.max_paradas_por_viaje),
        max_paradas_por_jornada: String(actualizada.max_paradas_por_jornada),
        max_viajes_por_dia: String(actualizada.max_viajes_por_dia),
      });
      const historial = await listarAuditoriaCapacidad(50);
      setAuditoria(historial);
      mostrarAviso(true, "Parametros de planificacion actualizados.");
    } catch (error) {
      manejarError(error);
    } finally {
      setGuardandoConfig(false);
    }
  };

  // --------------------------- Columnas ---------------------------

  const columnasCatalogo = [
    {
      key: "marca",
      header: "Marca",
      render: (m) => <span className="font-semibold text-slate-800">{m.marca}</span>,
    },
    {
      key: "modelo",
      header: "Modelo",
      render: (m) => <span className="text-slate-700">{m.modelo}</span>,
    },
    {
      key: "tipo",
      header: "Tipo",
      render: (m) => <Badge tono="brand">{ETIQUETA_TIPO[m.tipo] || m.tipo}</Badge>,
    },
    {
      key: "dimensiones",
      header: "L x A x H",
      render: (m) => (
        <span className="nums text-xs text-slate-600">
          {m.largo_m} x {m.ancho_m} x {m.alto_m} m
        </span>
      ),
    },
    {
      key: "volumen_util_m3",
      header: "Vol. util",
      render: (m) => <span className="nums font-semibold text-brand-700">{m.volumen_util_m3} m3</span>,
    },
    {
      key: "carga_util_kg",
      header: "Carga util",
      render: (m) => <span className="nums text-slate-700">{m.carga_util_kg.toLocaleString("es-PE")} kg</span>,
    },
    {
      key: "fuente",
      header: "Fuente",
      render: (m) =>
        m.fuente_url ? (
          <a
            href={m.fuente_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs font-medium text-brand-600 hover:underline"
          >
            <FileText size={13} />
            {m.fuente || "Ver ficha"}
          </a>
        ) : (
          <span className="text-xs text-slate-400">{m.fuente || "Sin fuente"}</span>
        ),
    },
    {
      key: "estado",
      header: "Estado",
      render: (m) =>
        m.verificado ? (
          <Badge tono="success">Verificado</Badge>
        ) : m.es_personalizado ? (
          <Badge tono="warning">Editado</Badge>
        ) : (
          <Badge tono="neutral">Referencia</Badge>
        ),
    },
  ];

  if (esAdmin) {
    columnasCatalogo.push({
      key: "acciones",
      header: "",
      render: (m) => (
        <div className="flex justify-end gap-1">
          <Button
            variant="ghost"
            size="sm"
            icon={Pencil}
            onClick={() => setModalModelo({ modo: "editar", modelo: m })}
          >
            Editar
          </Button>
          {m.es_personalizado && (
            <Button
              variant="ghost"
              size="sm"
              icon={Trash2}
              className="text-danger-strong"
              onClick={() => setModeloAEliminar(m)}
            >
              Borrar
            </Button>
          )}
        </div>
      ),
    });
  }

  const columnasFlota = [
    {
      key: "placa",
      header: "Placa",
      render: (v) => <span className="font-semibold text-slate-800">{v.placa}</span>,
    },
    {
      key: "estado",
      header: "Estado",
      render: (v) => <EstadoBadge estado={v.estado} />,
    },
    {
      key: "conductor",
      header: "Conductor",
      render: (v) => <span className="text-slate-600">{v.conductor || "Empresa"}</span>,
    },
    {
      key: "modelo",
      header: "Modelo vinculado",
      render: (v) =>
        v.vinculacion ? (
          <div>
            <p className="font-medium text-slate-700">
              {v.vinculacion.marca} {v.vinculacion.nombre_modelo}
            </p>
            <p className="text-xs text-slate-400">{ETIQUETA_TIPO[v.vinculacion.tipo] || v.vinculacion.tipo}</p>
          </div>
        ) : (
          <Badge tono="warning">Sin modelo</Badge>
        ),
    },
    {
      key: "capacidad",
      header: "Vol. / carga",
      render: (v) =>
        v.vinculacion ? (
          <span className="nums text-xs text-slate-600">
            {v.vinculacion.capacidad_m3} m3 · {v.vinculacion.carga_kg?.toLocaleString("es-PE")} kg
          </span>
        ) : (
          <span className="text-xs text-slate-400">—</span>
        ),
    },
  ];

  if (esAdmin) {
    columnasFlota.push({
      key: "acciones",
      header: "",
      render: (v) =>
        v.vinculacion ? (
          <Button
            variant="ghost"
            size="sm"
            icon={Unlink}
            className="text-danger-strong"
            onClick={() => setVinculacionAEliminar(v.vinculacion)}
          >
            Desvincular
          </Button>
        ) : null,
    });
  }

  const columnasVinculaciones = [
    {
      key: "placa",
      header: "Placa",
      render: (v) => <span className="font-semibold text-slate-800">{v.placa}</span>,
    },
    {
      key: "modelo",
      header: "Modelo",
      render: (v) => (
        <span className="text-slate-700">
          {v.marca} {v.nombre_modelo}
        </span>
      ),
    },
    {
      key: "capacidad_m3",
      header: "Volumen",
      render: (v) => <span className="nums text-slate-600">{v.capacidad_m3} m3</span>,
    },
    {
      key: "carga_kg",
      header: "Carga",
      render: (v) => <span className="nums text-slate-600">{v.carga_kg?.toLocaleString("es-PE")} kg</span>,
    },
    {
      key: "creado_por",
      header: "Registrado por",
      render: (v) => <span className="text-xs text-slate-500">{v.creado_por}</span>,
    },
    {
      key: "creado_en",
      header: "Fecha",
      render: (v) => (
        <span className="text-xs text-slate-500">
          {new Date(v.creado_en).toLocaleString("es-PE")}
        </span>
      ),
    },
  ];

  const columnasVehiculosPlan = [
    {
      key: "placa",
      header: "Vehiculo",
      render: (v) => <span className="font-semibold text-slate-800">{v.placa}</span>,
    },
    {
      key: "modelo",
      header: "Modelo",
      render: (v) => <span className="text-slate-600">{v.marca} {v.modelo}</span>,
    },
    {
      key: "viajes",
      header: "Viajes",
      render: (v) => <span className="nums text-slate-700">{v.viajes}</span>,
    },
    {
      key: "pedidos",
      header: "Pedidos",
      render: (v) => <span className="nums text-slate-700">{v.pedidos}</span>,
    },
    {
      key: "volumen_m3",
      header: "Volumen",
      render: (v) => <span className="nums text-slate-600">{v.volumen_m3} m3</span>,
    },
    {
      key: "paradas",
      header: "Paradas",
      render: (v) => <span className="nums text-slate-600">{v.paradas}</span>,
    },
    {
      key: "utilizacion_pct",
      header: "Uso",
      render: (v) => <BarraUso valor={v.utilizacion_pct} />,
    },
  ];

  const columnasAuditoria = [
    {
      key: "creado_en",
      header: "Fecha",
      render: (fila) => (
        <span className="text-xs text-slate-500">{new Date(fila.creado_en).toLocaleString("es-PE")}</span>
      ),
    },
    {
      key: "usuario",
      header: "Usuario",
      render: (fila) => <span className="text-slate-700">{fila.usuario}</span>,
    },
    {
      key: "accion",
      header: "Accion",
      render: (fila) => <Badge tono="brand">{fila.accion}</Badge>,
    },
    {
      key: "entidad",
      header: "Entidad",
      render: (fila) => <span className="text-slate-600">{fila.entidad}</span>,
    },
    {
      key: "entidad_id",
      header: "Referencia",
      render: (fila) => <span className="text-xs text-slate-500">{fila.entidad_id || "—"}</span>,
    },
    {
      key: "detalle",
      header: "Detalle",
      render: (fila) => <span className="text-xs text-slate-500">{fila.detalle || "—"}</span>,
    },
  ];

  // --------------------------- Render ---------------------------

  if (cargando) {
    return (
      <div className="space-y-6 p-6 lg:p-8">
        <PageHeader
          titulo="Catalogo de vehiculos y capacidad"
          subtitulo="Cargando catalogo, flota y configuracion..."
        />
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[0, 1, 2, 3].map((indice) => (
            <Skeleton key={indice} className="h-28 w-full" rounded="rounded-card" />
          ))}
        </div>
        <Skeleton className="h-72 w-full" rounded="rounded-card" />
      </div>
    );
  }

  if (!moduloActivo) {
    return (
      <div className="space-y-6 p-6 lg:p-8">
        <PageHeader
          titulo="Catalogo de vehiculos y capacidad"
          subtitulo="Modulo de la Idea 3 (semanas 9 a 11)."
        />
        <div className="flex items-start gap-3 rounded-card border border-warning/30 bg-warning-soft p-5 text-sm text-warning-strong">
          <AlertTriangle size={20} className="mt-0.5 shrink-0" />
          <div>
            <p className="font-semibold">Modulo desactivado</p>
            <p className="mt-1">
              {aviso?.texto ||
                "El backend tiene MODULO_CAPACIDAD_ENABLED=false. Activa la bandera y vuelve a cargar la pagina."}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6 lg:p-8">
      <PageHeader
        titulo="Catalogo de vehiculos y capacidad"
        subtitulo="Fichas tecnicas, vinculacion de placas, calculadora de carga y planificacion diaria."
      >
        <Badge tono={esAdmin ? "brand" : "neutral"}>{esAdmin ? "Administrador" : "Solo lectura"}</Badge>
      </PageHeader>

      <Aviso aviso={aviso} onCerrar={() => setAviso(null)} />

      <div className="flex flex-wrap gap-1 rounded-xl border border-slate-200 bg-white p-1 shadow-card">
        {TABS.map((opcion) => {
          const Icono = opcion.icono;
          const activa = tab === opcion.id;
          return (
            <button
              key={opcion.id}
              type="button"
              onClick={() => setTab(opcion.id)}
              className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition-colors ${
                activa ? "bg-brand-600 text-white" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              <Icono size={16} />
              {opcion.etiqueta}
            </button>
          );
        })}
      </div>

      {/* ------------------------------ Catalogo ------------------------------ */}
      {tab === "catalogo" && (
        <div className="space-y-6 animate-fade-in">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <KpiCard label="Modelos" value={modelos.length} icon={Boxes} tone="brand" />
            <KpiCard label="Marcas" value={marcas.length} icon={Truck} tone="info" />
            <KpiCard label="Verificados" value={modelosVerificados} icon={CheckCircle2} tone="success" />
            <KpiCard label="Tipos" value={tiposDistintos} icon={Gauge} tone="warning" />
          </div>

          <SectionCard
            title="Catalogo de vehiculos"
            subtitle="Fichas del JSON base y modelos agregados o editados desde el panel."
            action={
              esAdmin ? (
                <Button size="sm" icon={Plus} onClick={() => setModalModelo({ modo: "crear", modelo: null })}>
                  Agregar modelo
                </Button>
              ) : null
            }
          >
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <div className="relative">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  value={busqueda}
                  onChange={(evento) => setBusqueda(evento.target.value)}
                  placeholder="Buscar marca, modelo o ID..."
                  className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-9 pr-3 text-sm text-slate-800 outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
                />
              </div>
              <Input as="select" value={filtroTipo} onChange={(evento) => setFiltroTipo(evento.target.value)}>
                <option value="">Todos los tipos</option>
                {TIPOS_VEHICULO.map((tipo) => (
                  <option key={tipo.valor} value={tipo.valor}>
                    {tipo.etiqueta}
                  </option>
                ))}
              </Input>
              <Input as="select" value={filtroMarca} onChange={(evento) => setFiltroMarca(evento.target.value)}>
                <option value="">Todas las marcas</option>
                {marcas.map((marca) => (
                  <option key={marca} value={marca}>
                    {marca}
                  </option>
                ))}
              </Input>
              <label className="flex items-center gap-2 rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm text-slate-600">
                <input
                  type="checkbox"
                  checked={soloVerificados}
                  onChange={(evento) => setSoloVerificados(evento.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                />
                Solo verificados
              </label>
            </div>

            <p className="mt-3 text-xs text-slate-500">
              {modelosFiltrados.length} de {modelos.length} modelos · volumen util y carga declarados por el fabricante.
            </p>

            <div className="mt-4">
              <DataTable
                columns={columnasCatalogo}
                rows={modelosFiltrados}
                rowKey={(m) => m.id}
                empty={{
                  icon: Boxes,
                  title: "Sin modelos",
                  description: "Prueba con otra busqueda, marca o tipo de vehiculo.",
                }}
              />
            </div>
          </SectionCard>
        </div>
      )}

      {/* --------------------------- Flota y vinculos --------------------------- */}
      {tab === "flota" && (
        <div className="space-y-6 animate-fade-in">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <KpiCard label="Vehiculos" value={flota.length} icon={Truck} tone="brand" />
            <KpiCard label="Con modelo" value={flotaConModelo} icon={Link2} tone="success" />
            <KpiCard label="Sin modelo" value={flota.length - flotaConModelo} icon={Unlink} tone="warning" />
            <KpiCard label="Vinculaciones" value={vinculaciones.length} icon={ClipboardList} tone="info" />
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            <SectionCard
              title="Vincular placa"
              subtitle="Solo aparecen placas de la flota que aun no tienen modelo."
              className="lg:col-span-1"
            >
              {esAdmin ? (
                <form onSubmit={vincular} className="space-y-4">
                  <Input
                    as="select"
                    label="Placa de la flota"
                    value={placaNueva}
                    onChange={(evento) => setPlacaNueva(evento.target.value)}
                    hint={placasDisponibles.length ? undefined : "Todas las placas ya tienen modelo."}
                  >
                    <option value="">Selecciona una placa...</option>
                    {placasDisponibles.map((vehiculo) => (
                      <option key={vehiculo.id} value={vehiculo.placa}>
                        {vehiculo.placa}
                        {vehiculo.marca ? ` · ${vehiculo.marca}` : ""}
                      </option>
                    ))}
                  </Input>
                  <Input
                    as="select"
                    label="Modelo del catalogo"
                    value={modeloNuevo}
                    onChange={(evento) => setModeloNuevo(evento.target.value)}
                  >
                    <option value="">Selecciona un modelo...</option>
                    {modelos.map((modelo) => (
                      <option key={modelo.id} value={modelo.id}>
                        {modelo.marca} {modelo.modelo} · {modelo.volumen_util_m3} m3
                      </option>
                    ))}
                  </Input>
                  <Button type="submit" icon={Link2} block disabled={guardandoVinculo}>
                    {guardandoVinculo ? "Vinculando..." : "Vincular placa"}
                  </Button>
                  <p className="text-xs text-slate-400">
                    Vincular no modifica la flota del nucleo: la relacion se guarda en las tablas propias del modulo.
                  </p>
                </form>
              ) : (
                <div className="flex items-start gap-2 text-sm text-slate-500">
                  <AlertCircle size={18} className="mt-0.5 shrink-0" />
                  Solo un administrador puede vincular o desvincular placas.
                </div>
              )}
            </SectionCard>

            <SectionCard
              title="Flota"
              subtitle="Vehiculos activos y su modelo vinculado."
              className="lg:col-span-2"
            >
              <DataTable
                columns={columnasFlota}
                rows={flota}
                rowKey={(v) => v.id}
                empty={{
                  icon: Truck,
                  title: "No hay vehiculos",
                  description: "Registra vehiculos en Flota para poder vincularlos a un modelo.",
                }}
              />
            </SectionCard>
          </div>

          <SectionCard
            title="Historial de vinculaciones"
            subtitle="Cada placa conserva quien la vinculo y cuando."
          >
            <DataTable
              columns={columnasVinculaciones}
              rows={vinculaciones}
              rowKey={(v) => v.id}
              empty={{
                icon: Link2,
                title: "Sin vinculaciones",
                description: "Usa el formulario de arriba para asociar una placa a un modelo.",
              }}
            />
          </SectionCard>
        </div>
      )}

      {/* ----------------------------- Calculadora ----------------------------- */}
      {tab === "calculadora" && (
        <div className="space-y-6 animate-fade-in">
          <div className="grid gap-6 lg:grid-cols-2">
            <SectionCard title="Vehiculo" subtitle="Elige un modelo del catalogo o una placa ya vinculada.">
              <div className="grid grid-cols-2 gap-1 rounded-xl bg-slate-100 p-1">
                {[
                  { valor: "modelo", etiqueta: "Modelo del catalogo" },
                  { valor: "placa", etiqueta: "Placa de la flota" },
                ].map((opcion) => (
                  <button
                    key={opcion.valor}
                    type="button"
                    onClick={() => setCalcFuente(opcion.valor)}
                    className={`rounded-lg px-3 py-2 text-sm font-semibold transition-colors ${
                      calcFuente === opcion.valor
                        ? "bg-white text-brand-700 shadow-sm"
                        : "text-slate-500 hover:text-slate-700"
                    }`}
                  >
                    {opcion.etiqueta}
                  </button>
                ))}
              </div>

              <div className="mt-4">
                {calcFuente === "modelo" ? (
                  <Input
                    as="select"
                    label="Modelo"
                    value={calcModelo}
                    onChange={(evento) => setCalcModelo(evento.target.value)}
                    hint="El calculo usa la capacidad del modelo y no toca la flota."
                  >
                    <option value="">Selecciona un modelo...</option>
                    {modelos.map((modelo) => (
                      <option key={modelo.id} value={modelo.id}>
                        {modelo.marca} {modelo.modelo} · {modelo.volumen_util_m3} m3 /{" "}
                        {modelo.carga_util_kg} kg
                      </option>
                    ))}
                  </Input>
                ) : (
                  <Input
                    as="select"
                    label="Placa vinculada"
                    value={calcPlaca}
                    onChange={(evento) => setCalcPlaca(evento.target.value)}
                    hint={vinculaciones.length ? undefined : "Primero vincula una placa en la pestana Flota."}
                  >
                    <option value="">Selecciona una placa...</option>
                    {vinculaciones.map((vinculo) => (
                      <option key={vinculo.id} value={vinculo.placa}>
                        {vinculo.placa} · {vinculo.marca} {vinculo.nombre_modelo}
                      </option>
                    ))}
                  </Input>
                )}
              </div>

              {modeloCalculado && (
                <div className="mt-4 rounded-xl bg-slate-50 p-3 text-xs text-slate-600">
                  <p className="font-semibold text-slate-700">
                    {modeloCalculado.marca} {modeloCalculado.modelo}
                  </p>
                  <p className="mt-1">
                    {modeloCalculado.largo_m} x {modeloCalculado.ancho_m} x {modeloCalculado.alto_m} m ·{" "}
                    {modeloCalculado.volumen_util_m3} m3 · {modeloCalculado.carga_util_kg} kg
                  </p>
                </div>
              )}
            </SectionCard>

            <SectionCard title="Carga a transportar" subtitle="Cajas de prueba, pedidos reales o el escenario demo.">
              <div className="grid grid-cols-3 gap-1 rounded-xl bg-slate-100 p-1">
                {[
                  { valor: "cajas", etiqueta: "Cajas S/M/L" },
                  { valor: "pedidos", etiqueta: "Pedidos" },
                  { valor: "demo", etiqueta: "Demo" },
                ].map((opcion) => (
                  <button
                    key={opcion.valor}
                    type="button"
                    onClick={() => setCalcCarga(opcion.valor)}
                    className={`rounded-lg px-3 py-2 text-sm font-semibold transition-colors ${
                      calcCarga === opcion.valor
                        ? "bg-white text-brand-700 shadow-sm"
                        : "text-slate-500 hover:text-slate-700"
                    }`}
                  >
                    {opcion.etiqueta}
                  </button>
                ))}
              </div>

              {calcCarga === "cajas" && (
                <div className="mt-4 grid grid-cols-3 gap-3">
                  {[
                    { clave: "S", etiqueta: "Cajas S", ayuda: "5 kg · 0.03 m3" },
                    { clave: "M", etiqueta: "Cajas M", ayuda: "15 kg · 0.09 m3" },
                    { clave: "L", etiqueta: "Cajas L", ayuda: "40 kg · 0.25 m3" },
                  ].map((caja) => (
                    <Input
                      key={caja.clave}
                      label={caja.etiqueta}
                      type="number"
                      min="0"
                      step="1"
                      value={cajas[caja.clave]}
                      onChange={(evento) =>
                        setCajas((actual) => ({ ...actual, [caja.clave]: evento.target.value }))
                      }
                      hint={caja.ayuda}
                    />
                  ))}
                </div>
              )}

              {calcCarga === "pedidos" && (
                <div className="mt-4 space-y-3">
                  <Input
                    as="select"
                    label="Estado"
                    value={calcFiltros.estado}
                    onChange={(evento) =>
                      setCalcFiltros((actual) => ({ ...actual, estado: evento.target.value }))
                    }
                  >
                    {ESTADOS_PLANIFICABLES.map((estado) => (
                      <option key={estado.valor} value={estado.valor}>
                        {estado.etiqueta}
                      </option>
                    ))}
                  </Input>
                  <div className="grid grid-cols-2 gap-3">
                    <Input
                      label="Distrito"
                      value={calcFiltros.distrito}
                      onChange={(evento) =>
                        setCalcFiltros((actual) => ({ ...actual, distrito: evento.target.value }))
                      }
                      placeholder="Opcional"
                    />
                    <Input
                      label="Limite"
                      type="number"
                      min="1"
                      max="5000"
                      value={calcFiltros.limite}
                      onChange={(evento) =>
                        setCalcFiltros((actual) => ({ ...actual, limite: evento.target.value }))
                      }
                      hint="Maximo 5000"
                    />
                  </div>
                  <p className="text-xs text-slate-400">
                    Se usan el peso y volumen reales del pedido. Si faltan, se estima S/M/L y el plan lo advierte.
                  </p>
                </div>
              )}

              {calcCarga === "demo" && (
                <div className="mt-4 space-y-3">
                  <Input
                    label="Pedidos sinteticos"
                    type="number"
                    min="1"
                    max="5000"
                    value={calcDemo}
                    onChange={(evento) => setCalcDemo(evento.target.value)}
                    hint="Escenario de la semana 11: 700 pedidos."
                  />
                  <div className="flex flex-wrap gap-2">
                    {[100, 300, 700].map((cantidad) => (
                      <Button
                        key={cantidad}
                        variant="secondary"
                        size="sm"
                        onClick={() => setCalcDemo(cantidad)}
                      >
                        {cantidad} pedidos
                      </Button>
                    ))}
                  </div>
                </div>
              )}
            </SectionCard>
          </div>

          <SectionCard
            title="Parametros del calculo"
            subtitle="Vacio usa el valor guardado en Configuracion."
          >
            <div className="grid gap-4 sm:grid-cols-3">
              <Input
                label="Factor de aprovechamiento"
                type="number"
                min="0.5"
                max="1"
                step="0.05"
                value={calcFactor}
                onChange={(evento) => setCalcFactor(evento.target.value)}
                placeholder={config ? String(config.factor_aprovechamiento) : "0.85"}
                hint="0.50 a 1.00 · 0.85 = 15% de holgura"
              />
              <Input
                label="Maximo de paradas por viaje"
                type="number"
                min="1"
                max="100"
                value={calcParadas}
                onChange={(evento) => setCalcParadas(evento.target.value)}
                placeholder={config ? String(config.max_paradas_por_viaje) : "25"}
                hint="Se avisa si un viaje lo supera"
              />
              <Input
                label="Maximo de viajes por dia"
                type="number"
                min="1"
                max="20"
                value={calcViajes}
                onChange={(evento) => setCalcViajes(evento.target.value)}
                placeholder={config ? String(config.max_viajes_por_dia) : "3"}
                hint="Limite duro por vehiculo"
              />
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              <Button icon={Calculator} onClick={calcular} disabled={calculando}>
                {calculando ? "Calculando..." : "Calcular capacidad"}
              </Button>
              <Button variant="secondary" icon={Trash2} onClick={limpiarCalculo}>
                Limpiar resultado
              </Button>
            </div>
          </SectionCard>

          {resultado && (
            <div className="space-y-6 animate-fade-up">
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <KpiCard
                  label="Pedidos"
                  value={resultado.resumen.total_pedidos}
                  icon={Boxes}
                  tone="brand"
                />
                <KpiCard
                  label="Viajes"
                  value={resultado.resumen.viajes_necesarios}
                  icon={Truck}
                  tone="info"
                />
                <KpiCard
                  label="Uso promedio"
                  value={Math.round(resultado.resumen.utilizacion_promedio_pct)}
                  icon={Gauge}
                  tone="success"
                />
                <KpiCard
                  label="Sin asignar"
                  value={resultado.resumen.pedidos_sin_asignar}
                  icon={AlertCircle}
                  tone={resultado.resumen.pedidos_sin_asignar ? "danger" : "success"}
                />
              </div>

              <ListaAlertas alertas={resultado.alertas} />

              <div className="grid gap-6 xl:grid-cols-[1.4fr,1fr]">
                <SectionCard
                  title="Viajes calculados"
                  subtitle={`Modo: ${ETIQUETA_MODO[resultado.modo] || resultado.modo}. Tope de paradas por viaje: ${resultado.configuracion.max_paradas_por_viaje}.`}
                >
                  <TablaViajes
                    viajes={resultado.viajes}
                    maxParadas={resultado.configuracion.max_paradas_por_viaje}
                    seleccionado={viajeSeleccionado}
                    onSeleccionar={setViajeSeleccionado}
                  />
                  <p className="mt-3 text-xs text-slate-400">
                    {resultado.resumen.pedidos_estimados
                      ? `${resultado.resumen.pedidos_estimados} pedidos sin peso/volumen usaron una talla estimada.`
                      : "Todos los pedidos tenian peso y volumen reales."}
                  </p>
                </SectionCard>

                <SectionCard title="Vista de carga 3D" subtitle="Representacion referencial del volumen ocupado.">
                  <Suspense fallback={<Skeleton className="h-[280px] w-full" />}>
                    <VisorCarga3D
                      modelo={modeloViaje}
                      utilizacionPct={viajeActual?.utilizacion_pct || 0}
                      placa={
                        viajeActual?.vehiculo_placa === "CATALOGO"
                          ? ""
                          : viajeActual?.vehiculo_placa || ""
                      }
                      pedidos={viajeActual?.paradas || 0}
                    />
                  </Suspense>
                  {viajeActual && (
                    <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                      <div className="rounded-xl bg-slate-50 p-3">
                        <p className="text-xs uppercase tracking-wide text-slate-400">Peso</p>
                        <p className="nums mt-1 font-semibold text-slate-700">
                          {viajeActual.peso_kg.toLocaleString("es-PE")} /{" "}
                          {viajeActual.capacidad_kg.toLocaleString("es-PE")} kg
                        </p>
                      </div>
                      <div className="rounded-xl bg-slate-50 p-3">
                        <p className="text-xs uppercase tracking-wide text-slate-400">Volumen</p>
                        <p className="nums mt-1 font-semibold text-slate-700">
                          {viajeActual.volumen_m3} / {viajeActual.capacidad_m3} m3
                        </p>
                      </div>
                    </div>
                  )}
                </SectionCard>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ---------------------------- Planificacion ---------------------------- */}
      {tab === "planificacion" && (
        <div className="space-y-6 animate-fade-in">
          <SectionCard
            title="Planificacion del dia"
            subtitle="Reparte los pedidos reales entre los vehiculos con modelo vinculado."
          >
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Input
                as="select"
                label="Estado de pedido"
                value={planFiltros.estado}
                onChange={(evento) =>
                  setPlanFiltros((actual) => ({ ...actual, estado: evento.target.value }))
                }
              >
                {ESTADOS_PLANIFICABLES.map((estado) => (
                  <option key={estado.valor} value={estado.valor}>
                    {estado.etiqueta}
                  </option>
                ))}
              </Input>
              <Input
                label="Distrito"
                value={planFiltros.distrito}
                onChange={(evento) =>
                  setPlanFiltros((actual) => ({ ...actual, distrito: evento.target.value }))
                }
                placeholder="Opcional"
              />
              <Input
                label="Fecha de creacion"
                type="date"
                value={planFiltros.fecha}
                onChange={(evento) =>
                  setPlanFiltros((actual) => ({ ...actual, fecha: evento.target.value }))
                }
              />
              <Input
                label="Limite de pedidos"
                type="number"
                min="1"
                max="5000"
                value={planFiltros.limite}
                onChange={(evento) =>
                  setPlanFiltros((actual) => ({ ...actual, limite: evento.target.value }))
                }
              />
            </div>

            <div className="mt-4 grid gap-4 sm:grid-cols-3">
              <Input
                label="Demo: pedidos"
                type="number"
                min="1"
                max="5000"
                value={planDemoPedidos}
                onChange={(evento) => setPlanDemoPedidos(evento.target.value)}
                hint="El caso de la semana 11 es 700."
              />
              <Input
                label="Demo: vehiculos"
                type="number"
                min="1"
                max="50"
                value={planDemoVehiculos}
                onChange={(evento) => setPlanDemoVehiculos(evento.target.value)}
                hint="Completa la flota con camiones tipicos."
              />
              <Input
                label="Factor de aprovechamiento"
                type="number"
                min="0.5"
                max="1"
                step="0.05"
                value={planFactor}
                onChange={(evento) => setPlanFactor(evento.target.value)}
                placeholder={config ? String(config.factor_aprovechamiento) : "0.85"}
              />
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              <Button icon={CalendarRange} onClick={() => planificar(false)} disabled={planificando}>
                {planificando ? "Planificando..." : "Planificar pedidos reales"}
              </Button>
              <Button
                variant="secondary"
                icon={Boxes}
                onClick={() => planificar(true)}
                disabled={planificando}
              >
                Probar demo 700 pedidos
              </Button>
            </div>
          </SectionCard>

          {planResultado && (
            <div className="space-y-6 animate-fade-up">
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
                <KpiCard
                  label="Pedidos"
                  value={planResultado.resumen.total_pedidos}
                  icon={Boxes}
                  tone="brand"
                />
                <KpiCard
                  label="Viajes"
                  value={planResultado.resumen.viajes_necesarios}
                  icon={Truck}
                  tone="info"
                />
                <KpiCard
                  label="Vehiculos"
                  value={planResultado.resumen.vehiculos_necesarios}
                  icon={BarChart3}
                  tone="success"
                />
                <KpiCard
                  label="Uso promedio"
                  value={Math.round(planResultado.resumen.utilizacion_promedio_pct)}
                  icon={Gauge}
                  tone="success"
                />
                <KpiCard
                  label="Sin asignar"
                  value={planResultado.resumen.pedidos_sin_asignar}
                  icon={AlertCircle}
                  tone={planResultado.resumen.pedidos_sin_asignar ? "danger" : "success"}
                />
                <KpiCard
                  label="Estimados"
                  value={planResultado.resumen.pedidos_estimados}
                  icon={AlertTriangle}
                  tone="warning"
                />
              </div>

              <ListaAlertas alertas={planResultado.alertas} />

              <SectionCard
                title="Resumen por vehiculo"
                subtitle="Viajes, pedidos, volumen y utilizacion de cada vehiculo del plan."
              >
                <DataTable
                  columns={columnasVehiculosPlan}
                  rows={planResultado.vehiculos}
                  rowKey={(v) => v.placa}
                  empty={{
                    icon: Truck,
                    title: "Sin vehiculos en el plan",
                    description: "Vincula placas a modelos o usa la demo para ver un escenario completo.",
                  }}
                />
              </SectionCard>

              <SectionCard
                title="Detalle de viajes"
                subtitle={`Plan generado en modo ${ETIQUETA_MODO[planResultado.modo] || planResultado.modo}.`}
              >
                <TablaViajes
                  viajes={planResultado.viajes}
                  maxParadas={planResultado.configuracion.max_paradas_por_viaje}
                  seleccionado={-1}
                  onSeleccionar={() => {}}
                />
              </SectionCard>
            </div>
          )}
        </div>
      )}

      {/* ----------------------------- Configuracion ----------------------------- */}
      {tab === "configuracion" && (
        <div className="space-y-6 animate-fade-in">
          <div className="grid gap-6 lg:grid-cols-2">
            <SectionCard
              title="Parametros de planificacion"
              subtitle="Se aplican a la calculadora y a la planificacion del dia."
            >
              {formConfig ? (
                esAdmin ? (
                  <form onSubmit={guardarConfiguracion} className="space-y-4">
                    <Input
                      label="Factor de aprovechamiento"
                      type="number"
                      min="0.5"
                      max="1"
                      step="0.05"
                      value={formConfig.factor_aprovechamiento}
                      onChange={(evento) =>
                        setFormConfig((actual) => ({
                          ...actual,
                          factor_aprovechamiento: evento.target.value,
                        }))
                      }
                      hint="0.85 significa usar el 85% del volumen y del peso."
                    />
                    <div className="grid gap-4 sm:grid-cols-2">
                      <Input
                        label="Paradas por viaje"
                        type="number"
                        min="1"
                        max="100"
                        value={formConfig.max_paradas_por_viaje}
                        onChange={(evento) =>
                          setFormConfig((actual) => ({
                            ...actual,
                            max_paradas_por_viaje: evento.target.value,
                          }))
                        }
                        hint="Umbral de alerta por viaje."
                      />
                      <Input
                        label="Paradas por jornada"
                        type="number"
                        min="1"
                        max="500"
                        value={formConfig.max_paradas_por_jornada}
                        onChange={(evento) =>
                          setFormConfig((actual) => ({
                            ...actual,
                            max_paradas_por_jornada: evento.target.value,
                          }))
                        }
                        hint="Alerta si un vehiculo acumula mas."
                      />
                    </div>
                    <Input
                      label="Viajes por dia y vehiculo"
                      type="number"
                      min="1"
                      max="20"
                      value={formConfig.max_viajes_por_dia}
                      onChange={(evento) =>
                        setFormConfig((actual) => ({
                          ...actual,
                          max_viajes_por_dia: evento.target.value,
                        }))
                      }
                      hint="Este si es un limite duro del plan."
                    />
                    <Button type="submit" icon={Settings} block disabled={guardandoConfig}>
                      {guardandoConfig ? "Guardando..." : "Guardar parametros"}
                    </Button>
                  </form>
                ) : (
                  <dl className="space-y-3 text-sm">
                    <div className="flex justify-between border-b border-slate-100 pb-2">
                      <dt className="text-slate-500">Factor de aprovechamiento</dt>
                      <dd className="font-semibold text-slate-800">{config?.factor_aprovechamiento}</dd>
                    </div>
                    <div className="flex justify-between border-b border-slate-100 pb-2">
                      <dt className="text-slate-500">Paradas por viaje</dt>
                      <dd className="font-semibold text-slate-800">{config?.max_paradas_por_viaje}</dd>
                    </div>
                    <div className="flex justify-between border-b border-slate-100 pb-2">
                      <dt className="text-slate-500">Paradas por jornada</dt>
                      <dd className="font-semibold text-slate-800">{config?.max_paradas_por_jornada}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-slate-500">Viajes por dia</dt>
                      <dd className="font-semibold text-slate-800">{config?.max_viajes_por_dia}</dd>
                    </div>
                  </dl>
                )
              ) : (
                <Skeleton className="h-48 w-full" />
              )}
            </SectionCard>

            <SectionCard title="Como se calcula" subtitle="Reglas del modulo de capacidad.">
              <ul className="space-y-3 text-sm text-slate-600">
                <li className="flex gap-2">
                  <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-success" />
                  La capacidad efectiva es volumen y peso del modelo multiplicados por el factor de aprovechamiento.
                </li>
                <li className="flex gap-2">
                  <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-success" />
                  Los pedidos reales usan peso y volumen de la tabla de pedidos; si faltan, se estima S/M/L y se avisa.
                </li>
                <li className="flex gap-2">
                  <AlertTriangle size={16} className="mt-0.5 shrink-0 text-warning" />
                  El tope de paradas por viaje es una alerta: el plan puede superarlo y avisarte para sumar otro vehiculo.
                </li>
                <li className="flex gap-2">
                  <AlertCircle size={16} className="mt-0.5 shrink-0 text-danger" />
                  El maximo de viajes por dia si es un limite duro. Si sobra carga, aparece la alerta de capacidad insuficiente.
                </li>
                <li className="flex gap-2">
                  <Link2 size={16} className="mt-0.5 shrink-0 text-brand-600" />
                  El modulo solo lee pedidos y vehiculos del nucleo; sus tablas viven en el esquema del propio modulo.
                </li>
              </ul>
            </SectionCard>
          </div>

          {esAdmin && (
            <SectionCard title="Auditoria" subtitle="Ultimos 50 cambios hechos en el modulo.">
              <DataTable
                columns={columnasAuditoria}
                rows={auditoria}
                rowKey={(fila) => fila.id}
                empty={{
                  icon: ClipboardList,
                  title: "Sin movimientos",
                  description: "Los cambios de catalogo, vinculaciones y configuracion se registran aqui.",
                }}
              />
            </SectionCard>
          )}
        </div>
      )}

      {/* ------------------------------- Modales ------------------------------- */}
      <Modal
        open={Boolean(modalModelo)}
        onClose={() => {
          if (!guardandoModelo) setModalModelo(null);
        }}
        className="max-w-2xl"
      >
        {modalModelo && (
          <FormularioModelo
            key={modalModelo.modelo?.id || "nuevo"}
            modelo={modalModelo.modelo}
            guardando={guardandoModelo}
            onGuardar={guardarModelo}
            onCancelar={() => setModalModelo(null)}
          />
        )}
      </Modal>

      <ConfirmDialog
        open={Boolean(modeloAEliminar)}
        titulo="Eliminar modelo del catalogo"
        mensaje={
          modeloAEliminar
            ? `Se borrara ${modeloAEliminar.marca} ${modeloAEliminar.modelo}. Solo se pueden eliminar modelos creados desde el panel.`
            : ""
        }
        textoConfirmar="Eliminar modelo"
        tono="danger"
        cargando={eliminandoModelo}
        onConfirmar={confirmarEliminarModelo}
        onCancelar={() => setModeloAEliminar(null)}
      />

      <ConfirmDialog
        open={Boolean(vinculacionAEliminar)}
        titulo="Desvincular placa"
        mensaje={
          vinculacionAEliminar
            ? `La placa ${vinculacionAEliminar.placa} quedara sin modelo y saldra de la planificacion hasta que la vincules de nuevo.`
            : ""
        }
        textoConfirmar="Desvincular"
        tono="danger"
        cargando={eliminandoVinculo}
        onConfirmar={confirmarDesvincular}
        onCancelar={() => setVinculacionAEliminar(null)}
      />
    </div>
  );
}
