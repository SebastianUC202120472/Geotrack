
import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import {
  AlertCircle, AlertTriangle, BookOpen, Boxes, Calculator, CalendarRange,
  CheckCircle2, ClipboardList, Gauge, Link2, Pencil, Plus, Settings,
  Trash2, Truck, Unlink,
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
import { ESTADOS_PLANIFICABLES, ETIQUETA_TIPO, TIPOS_VEHICULO } from "../components/capacidad/constantes";
import { useAuth } from "../context/AuthContext";
import {
  actualizarConfiguracionCapacidad, actualizarModeloCapacidad,
  calcularCapacidad, crearModeloCapacidad, desvincularPlacaCapacidad,
  eliminarModeloCapacidad, listarAuditoriaCapacidad, listarCatalogoCapacidad,
  listarFlotaCapacidad, listarVinculacionesCapacidad,
  obtenerConfiguracionCapacidad, obtenerPlanificacionCapacidad,
  vincularPlacaCapacidad,
} from "../services/api";

// El visor 3D se descarga solo cuando el usuario abre un resultado.
const VisorCarga3D = lazy(() => import("../components/capacidad/VisorCarga3D"));
const CAMPOS = ["factor_aprovechamiento", "max_paradas_por_viaje", "max_paradas_por_jornada", "max_viajes_por_dia",
  "s_peso_kg", "s_volumen_m3", "m_peso_kg", "m_volumen_m3", "l_peso_kg", "l_volumen_m3"];
const etiquetas = {
  factor_aprovechamiento: "Factor de aprovechamiento (0.5 a 1)",
  max_paradas_por_viaje: "Paradas máximas por viaje",
  max_paradas_por_jornada: "Paradas máximas por jornada",
  max_viajes_por_dia: "Viajes máximos por día",
  s_peso_kg: "Peso S (kg)", s_volumen_m3: "Volumen S (m³)",
  m_peso_kg: "Peso M (kg)", m_volumen_m3: "Volumen M (m³)",
  l_peso_kg: "Peso L (kg)", l_volumen_m3: "Volumen L (m³)",
};
const tabs = [
  ["catalogo", "Catálogo", BookOpen], ["flota", "Flota y vinculaciones", Link2],
  ["calculadora", "Calculadora", Calculator], ["planificacion", "Planificación", CalendarRange],
  ["configuracion", "Configuración", Settings],
];
const formularioConfig = (config) => Object.fromEntries(CAMPOS.map((campo) => [campo, String(config?.[campo] ?? "")]));
const natural = (n) => Number(n ?? 0).toLocaleString("es-PE");

function Alertas({ alertas = [] }) {
  return alertas.length ? (
    <div className="space-y-2" role="status">
      {alertas.map((a, i) => (
        <div key={`${a.codigo}-${i}`} className={`flex gap-2 rounded-xl border p-3 text-sm ${a.nivel === "danger"
          ? "border-red-200 bg-red-50 text-red-800" : a.nivel === "warning"
            ? "border-amber-200 bg-amber-50 text-amber-800" : "border-blue-200 bg-blue-50 text-blue-800"}`}>
          <AlertTriangle size={18} className="shrink-0" />
          <span><strong>{String(a.codigo || "Aviso").replaceAll("_", " ")}: </strong>{a.mensaje}</span>
        </div>
      ))}
    </div>
  ) : null;
}

function TablaResultado({ plan, indice, cambiarIndice, modelos }) {
  const viajes = plan?.viajes || [];
  const viaje = viajes[indice] || null;
  const ficha = modelos.find((m) => m.id === viaje?.modelo_id);
  const modelo = ficha || (viaje ? {
    marca: viaje.marca || "Vehículo", modelo: viaje.modelo || "Referencial",
    largo_m: 2.6, ancho_m: 1.6, alto_m: 1.0, referencial: true,
  } : null);
  const resumen = plan.resumen;
  const nombreVehiculo = (v) => {
    if (!v) return "Sin identificar";

    const fichaVehiculo = modelos.find((m) => m.id === v.modelo_id);

    const nombre = fichaVehiculo
      ? `${fichaVehiculo.marca} ${fichaVehiculo.modelo}`
      : [v.marca, v.modelo].filter(Boolean).join(" ");

    const placa = v.vehiculo_placa || "";

    if (placa && placa.toUpperCase() !== "CATALOGO") {
      return nombre ? `${placa} - ${nombre}` : placa;
    }

    return nombre || placa || "Sin identificar";
  };

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <KpiCard label="Pedidos" value={resumen.total_pedidos} icon={Boxes} tone="brand" />
        <KpiCard label="Viajes" value={resumen.viajes_necesarios} icon={Truck} tone="info" />
        <KpiCard label="Sin asignar" value={resumen.pedidos_sin_asignar} icon={AlertCircle}
          tone={resumen.pedidos_sin_asignar ? "danger" : "success"} />
        <KpiCard label="Vehículos necesarios (estimación)"
          value={resumen.vehiculos_necesarios ?? "Sin datos"} icon={Gauge} tone="warning" />
      </div>
      <Alertas alertas={plan.alertas} />
      <SectionCard title="Viajes calculados" subtitle="Una recomendación que no altera las rutas del núcleo.">
        <DataTable rows={viajes} rowKey={(v) => `${v.numero}-${v.vehiculo_placa}`}
          empty={{ icon: ClipboardList, title: "No se generaron viajes", description: "Revisa la flota y los límites." }}
          columns={[
            { key: "numero", header: "Viaje", render: (v) => `#${v.numero}` },
            { key: "vehiculo_placa",header: "Vehículo",render: (v) => nombreVehiculo(v) },
            { key: "paradas", header: "Paradas", render: (v) => v.paradas },
            { key: "peso_kg", header: "Peso (kg)", render: (v) => natural(v.peso_kg) },
            { key: "volumen_m3", header: "Volumen (m³)", render: (v) => v.volumen_m3 },
            { key: "utilizacion_pct", header: "Uso (%)", render: (v) => `${v.utilizacion_pct}%` },
            { key: "ver", header: "Detalle", render: (v) => (
              <Button size="sm" variant={viajes.indexOf(v) === indice ? "primary" : "secondary"}
                onClick={() => cambiarIndice(viajes.indexOf(v))}>Ver 3D</Button>
            ) },
          ]} />
      </SectionCard>
      <div className="grid gap-5 lg:grid-cols-2">
        <SectionCard title="Vista de carga 3D" subtitle="Visualización referencial del viaje elegido.">
          <Suspense fallback={<Skeleton className="h-72 w-full" />}>
              <VisorCarga3D
              modelo={modelo}
              utilizacionPct={viaje?.utilizacion_pct || 0}
              placa={
              viaje?.vehiculo_placa?.toUpperCase() === "CATALOGO"
                ? nombreVehiculo(viaje)
                : (viaje?.vehiculo_placa || "")
                    }
              pedidos={viaje?.paradas || 0}
            />

          </Suspense>
        </SectionCard>
        <SectionCard title="Resumen del viaje">
          {viaje ? <dl className="space-y-2 text-sm">
            <div>Vehículo: <strong>{nombreVehiculo(viaje)}</strong></div>
            <div>Pedidos: <strong>{viaje.paradas}</strong></div>
            <div>Peso: <strong>{natural(viaje.peso_kg)} / {natural(viaje.capacidad_kg)} kg</strong></div>
            <div>Volumen: <strong>{viaje.volumen_m3} / {viaje.capacidad_m3} m³</strong></div>
            <div>Uso por peso: <strong>{viaje.utilizacion_peso_pct}%</strong></div>
            <div>Uso por volumen: <strong>{viaje.utilizacion_pct}%</strong></div>
            <p className="text-xs text-slate-500">Los pesos o volúmenes estimados se indican en las alertas.</p>
          </dl> : <p className="text-sm text-slate-500">No hay un viaje seleccionado.</p>}
        </SectionCard>
      </div>
    </div>
  );
}

export function ModuloCapacidadPage() {
  const { rol } = useAuth();
  const esAdmin = rol === "admin";
  const [tab, setTab] = useState("catalogo");
  const [cargando, setCargando] = useState(true);
  const [aviso, setAviso] = useState(null);
  const [modelos, setModelos] = useState([]);
  const [flota, setFlota] = useState([]);
  const [vinculaciones, setVinculaciones] = useState([]);
  const [config, setConfig] = useState(null);
  const [formConfig, setFormConfig] = useState({});
  const [auditoria, setAuditoria] = useState([]);
  const [busqueda, setBusqueda] = useState("");
  const [filtroMarca, setFiltroMarca] = useState("");
  const [filtroTipo, setFiltroTipo] = useState("");
  const [soloVerificados, setSoloVerificados] = useState(false);
  const [modalModelo, setModalModelo] = useState(null);
  const [modeloEliminar, setModeloEliminar] = useState(null);
  const [vinculoEliminar, setVinculoEliminar] = useState(null);
  const [guardando, setGuardando] = useState(false);
  const [placaNueva, setPlacaNueva] = useState("");
  const [modeloNuevo, setModeloNuevo] = useState("");
  const [fuente, setFuente] = useState("modelo");
  const [calcModelo, setCalcModelo] = useState("");
  const [calcPlaca, setCalcPlaca] = useState("");
  const [carga, setCarga] = useState("cajas");
  const [cajas, setCajas] = useState({ S: 20, M: 10, L: 4 });
  const [filtrosCalc, setFiltrosCalc] = useState({ estado: "", distrito: "", limite: 200 });
  const [demoCalc, setDemoCalc] = useState(100);
  const [factorCalc, setFactorCalc] = useState("");
  const [paradasCalc, setParadasCalc] = useState("");
  const [viajesCalc, setViajesCalc] = useState("");
  const [resultado, setResultado] = useState(null);
  const [viajeCalc, setViajeCalc] = useState(0);
  const [filtrosPlan, setFiltrosPlan] = useState({ estado: "", distrito: "", fecha: "", limite: 500 });
  const [demoPedidos, setDemoPedidos] = useState(700);
  const [demoVehiculos, setDemoVehiculos] = useState(6);
  const [factorPlan, setFactorPlan] = useState("");
  const [planResultado, setPlanResultado] = useState(null);
  const [viajePlan, setViajePlan] = useState(0);

  const notificar = (ok, texto) => setAviso({ ok, texto });
  const manejarError = (error) => notificar(false, error?.message || "Se produjo un error en el módulo.");
  const recargarCatalogo = async () => setModelos(await listarCatalogoCapacidad());
  const recargarFlota = async () => {
    const [a, b] = await Promise.all([listarFlotaCapacidad(), listarVinculacionesCapacidad()]);
    setFlota(a); setVinculaciones(b);
  };

  useEffect(() => {
    let activo = true;
    Promise.all([listarCatalogoCapacidad(), listarFlotaCapacidad(), listarVinculacionesCapacidad(), obtenerConfiguracionCapacidad()])
      .then(([m, f, v, c]) => {
        if (!activo) return;
        setModelos(m); setFlota(f); setVinculaciones(v); setConfig(c); setFormConfig(formularioConfig(c));
      })
.catch((e) => {
  if (activo) {
    setAviso({
      ok: false,
      texto: e?.message || "Error al cargar el módulo de capacidad.",
    });
  }
})

      .finally(() => { if (activo) setCargando(false); });
    return () => { activo = false; };
  }, []);

  useEffect(() => {
    if (!esAdmin || tab !== "configuracion") return;
    let activo = true;
    listarAuditoriaCapacidad(50).then((a) => { if (activo) setAuditoria(a); })
      .catch(() => { if (activo) setAuditoria([]); });
    return () => { activo = false; };
  }, [esAdmin, tab]);

  const marcas = useMemo(() => [...new Set(modelos.map((m) => m.marca))].sort(), [modelos]);
  const catalogo = useMemo(() => modelos.filter((m) => (
    (!busqueda || `${m.marca} ${m.modelo} ${m.id}`.toLowerCase().includes(busqueda.toLowerCase())) &&
    (!filtroMarca || m.marca === filtroMarca) && (!filtroTipo || m.tipo === filtroTipo) &&
    (!soloVerificados || m.verificado)
  )), [modelos, busqueda, filtroMarca, filtroTipo, soloVerificados]);
  const vinculadas = useMemo(() => new Set(vinculaciones.map((v) => v.placa)), [vinculaciones]);

  async function guardarModelo(datos) {
    setGuardando(true);
    try {
      if (modalModelo?.modo === "editar") await actualizarModeloCapacidad(modalModelo.modelo.id, datos);
      else await crearModeloCapacidad(datos);
      await recargarCatalogo(); setModalModelo(null); notificar(true, "Modelo guardado correctamente.");
    } catch (e) { manejarError(e); } finally { setGuardando(false); }
  }

  async function eliminarModelo() {
    if (!modeloEliminar) return;
    setGuardando(true);
    try {
      await eliminarModeloCapacidad(modeloEliminar.id); await recargarCatalogo();
      setModeloEliminar(null); notificar(true, "Modelo eliminado.");
    } catch (e) { manejarError(e); } finally { setGuardando(false); }
  }

  async function vincular(evento) {
    evento.preventDefault();
    if (!placaNueva || !modeloNuevo) return notificar(false, "Selecciona placa y modelo.");
    setGuardando(true);
    try {
      await vincularPlacaCapacidad({ placa: placaNueva, modelo_id: modeloNuevo });
      await recargarFlota(); setPlacaNueva(""); setModeloNuevo("");
      notificar(true, "Vinculación registrada y guardada.");
    } catch (e) { manejarError(e); } finally { setGuardando(false); }
  }

  async function desvincular() {
    if (!vinculoEliminar) return;
    setGuardando(true);
    try {
      await desvincularPlacaCapacidad(vinculoEliminar.id); await recargarFlota();
      setVinculoEliminar(null); notificar(true, "Placa desvinculada.");
    } catch (e) { manejarError(e); } finally { setGuardando(false); }
  }

  async function calcular() {
    const datos = {};
    if (fuente === "modelo") {
      if (!calcModelo) return notificar(false, "Selecciona un modelo.");
      datos.modelo_id = calcModelo;
    } else {
      if (!calcPlaca) return notificar(false, "Selecciona una placa vinculada.");
      datos.placa = calcPlaca;
    }
    if (carga === "cajas") {
      const cantidades = Object.fromEntries(["S", "M", "L"].map((s) => [s, Number(cajas[s])]));
      if (Object.values(cantidades).some((n) => !Number.isInteger(n) || n < 0)
          || Object.values(cantidades).reduce((s, n) => s + n, 0) < 1
          || Object.values(cantidades).reduce((s, n) => s + n, 0) > 5000) {
        return notificar(false, "Ingresa entre 1 y 5000 cajas en total.");
      }
      datos.cantidades = cantidades;
    } else if (carga === "demo") {
      datos.demo_pedidos = Number(demoCalc);
    } else {
      datos.filtros = { estado: filtrosCalc.estado || null,
        distrito: filtrosCalc.distrito || null, limite: Number(filtrosCalc.limite) };
    }
    if (factorCalc !== "") datos.factor_aprovechamiento = Number(factorCalc);
    if (paradasCalc !== "") datos.max_paradas_por_viaje = Number(paradasCalc);
    if (viajesCalc !== "") datos.max_viajes_por_dia = Number(viajesCalc);
    setGuardando(true);
    try {
      const respuesta = await calcularCapacidad(datos);
      setResultado(respuesta); setViajeCalc(0);
      notificar(true, `Calculados ${respuesta.resumen.viajes_necesarios} viajes.`);
    } catch (e) { manejarError(e); } finally { setGuardando(false); }
  }

  async function planificar(demo) {
    const datos = demo
      ? { demo_pedidos: Number(demoPedidos), demo_vehiculos: Number(demoVehiculos) }
      : { estado: filtrosPlan.estado || undefined, distrito: filtrosPlan.distrito || undefined,
          fecha: filtrosPlan.fecha || undefined, limite: Number(filtrosPlan.limite) };
    if (factorPlan !== "") datos.factor_aprovechamiento = Number(factorPlan);
    setGuardando(true);
    try {
      const respuesta = await obtenerPlanificacionCapacidad(datos);
      setPlanResultado(respuesta); setViajePlan(0);
      notificar(true, `Plan: ${respuesta.resumen.viajes_necesarios} viajes, ${respuesta.resumen.pedidos_sin_asignar} pendientes.`);
    } catch (e) { manejarError(e); } finally { setGuardando(false); }
  }

  async function guardarConfiguracion(evento) {
    evento.preventDefault();
    const datos = Object.fromEntries(CAMPOS.map((campo) => [campo, Number(formConfig[campo])]));
    if (CAMPOS.some((c) => !formConfig[c] || !Number.isFinite(datos[c]))) {
      return notificar(false, "Todos los parámetros deben estar completos.");
    }
    const enteros = ["max_paradas_por_viaje", "max_paradas_por_jornada", "max_viajes_por_dia"];
    if (datos.factor_aprovechamiento < 0.5 || datos.factor_aprovechamiento > 1 ||
        enteros.some((c) => !Number.isInteger(datos[c]) || datos[c] < 1) ||
        CAMPOS.slice(4).some((c) => datos[c] <= 0)) {
      return notificar(false, "Revisa factor, límites y medidas positivas.");
    }
    setGuardando(true);
    try {
      const actualizada = await actualizarConfiguracionCapacidad(datos);
      setConfig(actualizada); setFormConfig(formularioConfig(actualizada));
      setAuditoria(await listarAuditoriaCapacidad(50));
      notificar(true, "Configuración S/M/L guardada.");
    } catch (e) { manejarError(e); } finally { setGuardando(false); }
  }

  if (cargando) return <div className="p-8"><Skeleton className="h-72 w-full" /></div>;

  return (
    <div className="space-y-6 p-6 lg:p-8">
      <PageHeader titulo="Catálogo de vehículos y capacidad"
        subtitulo="Idea 3: catálogo, flota, cálculo, planificación y configuración.">
        <Badge tono={esAdmin ? "brand" : "neutral"}>{esAdmin ? "Administrador" : "Solo lectura"}</Badge>
      </PageHeader>
      {aviso && <div role="alert" className={`flex items-center justify-between rounded-xl border p-3 text-sm ${aviso.ok
        ? "border-green-200 bg-green-50 text-green-800" : "border-red-200 bg-red-50 text-red-800"}`}>
        <span className="flex items-center gap-2">{aviso.ok ? <CheckCircle2 size={17} /> : <AlertCircle size={17} />}{aviso.texto}</span>
        <button type="button" onClick={() => setAviso(null)} aria-label="Cerrar aviso">Cerrar</button>
      </div>}
      <nav className="flex flex-wrap gap-2" aria-label="Secciones del módulo">
        {tabs.map(([id, nombre, Icono]) => <button type="button" key={id} onClick={() => setTab(id)}
          aria-current={tab === id ? "page" : undefined}
          className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium ${tab === id
            ? "bg-brand-600 text-white" : "border border-slate-200 bg-white text-slate-700"}`}>
          <Icono size={16} />{nombre}</button>)}
      </nav>

      {tab === "catalogo" && <div className="space-y-5">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <KpiCard label="Modelos" value={modelos.length} icon={Boxes} tone="brand" />
          <KpiCard label="Marcas" value={marcas.length} icon={Truck} tone="info" />
          <KpiCard label="Verificados" value={modelos.filter((m) => m.verificado).length} icon={CheckCircle2} tone="success" />
          <KpiCard label="Tipos" value={new Set(modelos.map((m) => m.tipo)).size} icon={Gauge} tone="warning" />
        </div>
        <SectionCard title="Catálogo" subtitle={`${catalogo.length} de ${modelos.length} modelos`}
          action={esAdmin ? <Button size="sm" icon={Plus} onClick={() => setModalModelo({ modo: "crear" })}>Agregar modelo</Button> : null}>
          <div className="grid gap-3 sm:grid-cols-4">
            <Input label="Buscar" value={busqueda} onChange={(e) => setBusqueda(e.target.value)} placeholder="Marca o modelo" />
            <Input as="select" label="Marca" value={filtroMarca} onChange={(e) => setFiltroMarca(e.target.value)}>
              <option value="">Todas</option>{marcas.map((m) => <option key={m}>{m}</option>)}
            </Input>
            <Input as="select" label="Tipo" value={filtroTipo} onChange={(e) => setFiltroTipo(e.target.value)}>
              <option value="">Todos</option>{TIPOS_VEHICULO.map((t) => <option key={t.valor} value={t.valor}>{t.etiqueta}</option>)}
            </Input>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={soloVerificados}
              onChange={(e) => setSoloVerificados(e.target.checked)} />Solo verificados</label>
          </div>
          <div className="mt-4"><DataTable rows={catalogo} rowKey={(m) => m.id}
            empty={{ icon: Boxes, title: "Sin resultados", description: "Cambia los filtros." }} columns={[
              { key: "marca", header: "Marca", render: (m) => m.marca },
              { key: "modelo", header: "Modelo", render: (m) => m.modelo },
              { key: "tipo", header: "Tipo", render: (m) => ETIQUETA_TIPO[m.tipo] || m.tipo },
              { key: "volumen", header: "Volumen (m³)", render: (m) => m.volumen_util_m3 },
              { key: "carga", header: "Carga (kg)", render: (m) => natural(m.carga_util_kg) },
              { key: "fuente", header: "Ficha", render: (m) => m.fuente_url
                ? <a className="text-brand-700 underline" href={m.fuente_url} target="_blank" rel="noopener noreferrer">Fuente</a> : "Sin fuente" },
              { key: "estado", header: "Estado", render: (m) => m.verificado ? "Verificado" : "Referencial" },
              ...(esAdmin ? [{ key: "acciones", header: "", render: (m) => <div className="flex gap-2">
                <Button size="sm" variant="ghost" icon={Pencil} onClick={() => setModalModelo({ modo: "editar", modelo: m })}>Editar</Button>
                {m.es_personalizado && <Button size="sm" variant="ghost" icon={Trash2}
                  onClick={() => setModeloEliminar(m)}>Borrar</Button>}
              </div> }] : []),
            ]} /></div>
        </SectionCard>
      </div>}

      {tab === "flota" && <div className="space-y-5">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <KpiCard label="Vehículos" value={flota.length} icon={Truck} tone="brand" />
          <KpiCard label="Vinculados" value={vinculaciones.length} icon={Link2} tone="success" />
          <KpiCard label="Sin vínculo" value={flota.filter((v) => !vinculadas.has(v.placa)).length} icon={Unlink} tone="warning" />
        </div>
        {esAdmin && <SectionCard title="Vincular placa y modelo">
          <form className="grid gap-3 sm:grid-cols-3" onSubmit={vincular}>
            <Input as="select" label="Placa disponible" value={placaNueva} onChange={(e) => setPlacaNueva(e.target.value)}>
              <option value="">Seleccionar</option>{flota.filter((v) => !vinculadas.has(v.placa)).map((v) =>
                <option key={v.id} value={v.placa}>{v.placa}</option>)}
            </Input>
            <Input as="select" label="Modelo" value={modeloNuevo} onChange={(e) => setModeloNuevo(e.target.value)}>
              <option value="">Seleccionar</option>{modelos.map((m) =>
                <option key={m.id} value={m.id}>{m.marca} {m.modelo}</option>)}
            </Input>
            <div className="flex items-end"><Button icon={Link2} type="submit" disabled={guardando}>Vincular</Button></div>
          </form>
        </SectionCard>}
        <SectionCard title="Flota de vehículos">
          <DataTable rows={flota} rowKey={(v) => v.id}
            empty={{ icon: Truck, title: "Sin vehículos", description: "Registra vehículos en Flota." }} columns={[
              { key: "placa", header: "Placa", render: (v) => v.placa },
              { key: "estado", header: "Estado", render: (v) => <EstadoBadge estado={v.estado} /> },
              { key: "conductor", header: "Conductor", render: (v) => v.conductor || "Sin conductor" },
              { key: "modelo", header: "Modelo", render: (v) => v.vinculacion
                ? `${v.vinculacion.marca} ${v.vinculacion.nombre_modelo}` : "No vinculado" },
              ...(esAdmin ? [{ key: "acciones", header: "", render: (v) => v.vinculacion
                ? <Button variant="ghost" icon={Unlink} size="sm" onClick={() => setVinculoEliminar(v.vinculacion)}>Desvincular</Button> : null }] : []),
            ]} />
        </SectionCard>
        <SectionCard title="Historial de vinculaciones">
          <DataTable rows={vinculaciones} rowKey={(v) => v.id}
            empty={{ icon: Link2, title: "Sin vinculaciones", description: "Vincula una placa para comenzar." }} columns={[
              { key: "placa", header: "Placa", render: (v) => v.placa },
              { key: "modelo", header: "Modelo", render: (v) => `${v.marca} ${v.nombre_modelo}` },
              { key: "creado_por", header: "Usuario", render: (v) => v.creado_por },
              { key: "creado_en", header: "Fecha", render: (v) => new Date(v.creado_en).toLocaleString("es-PE") },
            ]} />
        </SectionCard>
      </div>}

      {tab === "calculadora" && <div className="space-y-5">
        <SectionCard title="Calculadora de capacidad" subtitle="Compara peso y volumen; se aplica el límite que se alcanza primero.">
          <div className="grid gap-4 sm:grid-cols-2">
            <Input as="select" label="Tipo de vehículo" value={fuente} onChange={(e) => setFuente(e.target.value)}>
              <option value="modelo">Modelo del catálogo</option><option value="placa">Placa vinculada</option>
            </Input>
            {fuente === "modelo" ? <Input as="select" label="Modelo" value={calcModelo} onChange={(e) => setCalcModelo(e.target.value)}>
              <option value="">Selecciona modelo</option>{modelos.map((m) =>
                <option key={m.id} value={m.id}>{m.marca} {m.modelo} — {m.volumen_util_m3} m³</option>)}
            </Input> : <Input as="select" label="Placa" value={calcPlaca} onChange={(e) => setCalcPlaca(e.target.value)}>
              <option value="">Selecciona placa</option>{vinculaciones.map((v) =>
                <option key={v.id} value={v.placa}>{v.placa} — {v.marca} {v.nombre_modelo}</option>)}
            </Input>}
            <Input as="select" label="Origen de pedidos" value={carga} onChange={(e) => setCarga(e.target.value)}>
              <option value="cajas">Cajas S/M/L</option><option value="pedidos">Pedidos reales</option><option value="demo">Demostración</option>
            </Input>
          </div>
          {carga === "cajas" && <div className="mt-4 grid grid-cols-3 gap-3">
            {["S", "M", "L"].map((s) => <Input key={s} label={`Cajas ${s}`} type="number" min="0" max="5000" step="1"
              value={cajas[s]} onChange={(e) => setCajas((c) => ({ ...c, [s]: e.target.value }))} />)}
          </div>}
          {carga === "pedidos" && <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <Input as="select" label="Estado" value={filtrosCalc.estado}
              onChange={(e) => setFiltrosCalc((f) => ({ ...f, estado: e.target.value }))}>
              {ESTADOS_PLANIFICABLES.map((e) => <option key={e.valor} value={e.valor}>{e.etiqueta}</option>)}
            </Input>
            <Input label="Distrito" value={filtrosCalc.distrito}
              onChange={(e) => setFiltrosCalc((f) => ({ ...f, distrito: e.target.value }))} />
            <Input label="Límite" type="number" min="1" max="5000" value={filtrosCalc.limite}
              onChange={(e) => setFiltrosCalc((f) => ({ ...f, limite: e.target.value }))} />
          </div>}
          {carga === "demo" && <div className="mt-4"><Input label="Pedidos de demostración" type="number" min="1" max="5000"
            value={demoCalc} onChange={(e) => setDemoCalc(e.target.value)} /></div>}
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <Input label="Factor (opcional)" type="number" min="0.5" max="1" step="0.05"
              value={factorCalc} onChange={(e) => setFactorCalc(e.target.value)} />
            <Input label="Paradas por viaje (opcional)" type="number" min="1" max="100" step="1"
              value={paradasCalc} onChange={(e) => setParadasCalc(e.target.value)} />
            <Input label="Viajes diarios (opcional)" type="number" min="1" max="20" step="1"
              value={viajesCalc} onChange={(e) => setViajesCalc(e.target.value)} />
          </div>
          <div className="mt-4"><Button icon={Calculator} disabled={guardando} onClick={calcular}>Calcular capacidad</Button></div>
        </SectionCard>
        {resultado && <TablaResultado plan={resultado} indice={viajeCalc} cambiarIndice={setViajeCalc} modelos={modelos} />}
      </div>}

      {tab === "planificacion" && <div className="space-y-5">
        <SectionCard title="Planificación del día" subtitle="Utiliza la flota disponible; no crea rutas en el sistema principal.">
          <div className="grid gap-3 sm:grid-cols-4">
            <Input as="select" label="Estado" value={filtrosPlan.estado}
              onChange={(e) => setFiltrosPlan((f) => ({ ...f, estado: e.target.value }))}>
              {ESTADOS_PLANIFICABLES.map((e) => <option key={e.valor} value={e.valor}>{e.etiqueta}</option>)}
            </Input>
            <Input label="Distrito" value={filtrosPlan.distrito}
              onChange={(e) => setFiltrosPlan((f) => ({ ...f, distrito: e.target.value }))} />
            <Input label="Fecha de creación" type="date" value={filtrosPlan.fecha}
              onChange={(e) => setFiltrosPlan((f) => ({ ...f, fecha: e.target.value }))} />
            <Input label="Límite" type="number" min="1" max="5000" value={filtrosPlan.limite}
              onChange={(e) => setFiltrosPlan((f) => ({ ...f, limite: e.target.value }))} />
          </div>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <Input label="Pedidos demo" type="number" min="1" max="5000" value={demoPedidos}
              onChange={(e) => setDemoPedidos(e.target.value)} />
            <Input label="Vehículos demo" type="number" min="1" max="50" value={demoVehiculos}
              onChange={(e) => setDemoVehiculos(e.target.value)} />
            <Input label="Factor (opcional)" type="number" min="0.5" max="1" step="0.05" value={factorPlan}
              onChange={(e) => setFactorPlan(e.target.value)} />
          </div>
          <div className="mt-4 flex flex-wrap gap-3">
            <Button icon={CalendarRange} disabled={guardando} onClick={() => planificar(false)}>Planificar pedidos reales</Button>
            <Button icon={Boxes} variant="secondary" disabled={guardando} onClick={() => planificar(true)}>Probar 700 pedidos</Button>
          </div>
        </SectionCard>
        {planResultado && <>
          <TablaResultado plan={planResultado} indice={viajePlan} cambiarIndice={setViajePlan} modelos={modelos} />
          <SectionCard title="Resumen por vehículo">
            <DataTable rows={planResultado.vehiculos || []} rowKey={(v) => v.placa}
              empty={{ icon: Truck, title: "No se utilizaron vehículos", description: "Revisa la disponibilidad." }} columns={[
                { key: "placa", header: "Placa", render: (v) => v.placa },
                { key: "modelo", header: "Modelo", render: (v) => `${v.marca} ${v.modelo}` },
                { key: "viajes", header: "Viajes", render: (v) => v.viajes },
                { key: "pedidos", header: "Pedidos", render: (v) => v.pedidos },
                { key: "peso_kg", header: "Peso (kg)", render: (v) => natural(v.peso_kg) },
                { key: "paradas", header: "Paradas", render: (v) => v.paradas },
              ]} />
          </SectionCard>
        </>}
      </div>}

      {tab === "configuracion" && <div className="space-y-5">
        <SectionCard title="Parámetros de planificación" subtitle="El administrador configura límites, pesos y volúmenes de S/M/L.">
          {esAdmin ? <form onSubmit={guardarConfiguracion} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              {CAMPOS.map((campo) => <Input key={campo} label={etiquetas[campo]} type="number"
                min={campo === "factor_aprovechamiento" ? "0.5" : campo.startsWith("max_") ? "1" : "0.0001"}
                max={campo === "factor_aprovechamiento" ? "1" : undefined}
                step={campo.startsWith("max_") ? "1" : "any"}
                value={formConfig[campo] ?? ""}
                onChange={(e) => setFormConfig((f) => ({ ...f, [campo]: e.target.value }))} />)}
            </div>
            <Button type="submit" icon={Settings} disabled={guardando}>Guardar configuración</Button>
          </form> : <dl className="grid gap-3 sm:grid-cols-2 text-sm">
            {CAMPOS.map((c) => <div key={c}><dt className="text-slate-500">{etiquetas[c]}</dt>
              <dd className="font-semibold">{config?.[c]}</dd></div>)}
          </dl>}
        </SectionCard>
        {esAdmin && <SectionCard title="Auditoría" subtitle="Últimos 50 cambios del módulo.">
          <DataTable rows={auditoria} rowKey={(a) => a.id}
            empty={{ icon: ClipboardList, title: "Sin movimientos", description: "No hay cambios registrados." }} columns={[
              { key: "fecha", header: "Fecha", render: (a) => new Date(a.creado_en).toLocaleString("es-PE") },
              { key: "usuario", header: "Usuario", render: (a) => a.usuario },
              { key: "accion", header: "Acción", render: (a) => a.accion },
              { key: "entidad", header: "Entidad", render: (a) => a.entidad },
              { key: "detalle", header: "Detalle", render: (a) => a.detalle || "—" },
            ]} />
        </SectionCard>}
      </div>}

      <Modal open={Boolean(modalModelo)} onClose={() => !guardando && setModalModelo(null)} className="max-w-2xl">
        {modalModelo && <FormularioModelo key={modalModelo.modelo?.id || "nuevo"} modelo={modalModelo.modelo}
          guardando={guardando} onGuardar={guardarModelo} onCancelar={() => setModalModelo(null)} />}
      </Modal>
      <ConfirmDialog open={Boolean(modeloEliminar)} titulo="Eliminar modelo"
        mensaje={modeloEliminar ? `¿Eliminar ${modeloEliminar.marca} ${modeloEliminar.modelo}?` : ""}
        textoConfirmar="Eliminar" tono="danger" cargando={guardando}
        onConfirmar={eliminarModelo} onCancelar={() => setModeloEliminar(null)} />
      <ConfirmDialog open={Boolean(vinculoEliminar)} titulo="Desvincular placa"
        mensaje={vinculoEliminar ? `¿Quitar el modelo de ${vinculoEliminar.placa}?` : ""}
        textoConfirmar="Desvincular" tono="danger" cargando={guardando}
        onConfirmar={desvincular} onCancelar={() => setVinculoEliminar(null)} />
    </div>
  );
}
